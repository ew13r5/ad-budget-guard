"""Celery task: daily token health check and refresh."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import httpx

from app.services.crypto import decrypt_token, encrypt_token
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.token_health.check_token_health")
def check_token_health():
    """Check all user tokens, refresh expiring ones, alert on issues."""
    from app.config import get_settings

    settings = get_settings()

    if not settings.meta_app_id or not settings.meta_app_secret:
        logger.info("token_health_skipped: meta credentials not configured")
        return {"status": "skipped", "reason": "simulation_mode"}

    from app.database import get_sync_session_factory
    from app.models.user import User

    session_factory = get_sync_session_factory()
    session = session_factory()

    checked = 0
    healthy = 0
    refreshed = 0
    needs_reauth_count = 0

    try:
        users = session.query(User).filter(User.access_token.isnot(None)).all()

        for user in users:
            checked += 1
            try:
                # Decrypt token
                try:
                    token = decrypt_token(user.access_token, settings.encryption_key)
                except ValueError:
                    logger.error("token_decrypt_failed", extra={"user_id": str(user.id)})
                    user.needs_reauth = True
                    needs_reauth_count += 1
                    _dispatch_alert(session, user, "token_expired", "critical",
                                    f"Token for {user.name} could not be decrypted.")
                    continue

                # Call debug_token
                app_token = f"{settings.meta_app_id}|{settings.meta_app_secret}"
                graph_url = f"https://graph.facebook.com/{settings.meta_api_version}"

                try:
                    with httpx.Client(timeout=10.0) as client:
                        resp = client.get(
                            f"{graph_url}/debug_token",
                            params={
                                "input_token": token,
                                "access_token": app_token,
                            },
                        )
                        resp.raise_for_status()
                        data = resp.json().get("data", {})
                except Exception:
                    logger.warning("debug_token_failed", extra={"user_id": str(user.id)})
                    continue  # Skip, retry next run

                is_valid = data.get("is_valid", False)

                if not is_valid:
                    user.needs_reauth = True
                    needs_reauth_count += 1
                    _dispatch_alert(session, user, "token_expired", "critical",
                                    f"Token for {user.name} is invalid and needs re-authentication.")
                    continue

                expires_at = data.get("expires_at", 0)
                if expires_at == 0:
                    healthy += 1
                    continue

                expiry = datetime.fromtimestamp(expires_at, tz=timezone.utc)
                remaining = expiry - datetime.now(timezone.utc)

                if remaining > timedelta(days=7):
                    healthy += 1
                    continue

                # Attempt refresh
                try:
                    with httpx.Client(timeout=10.0) as client:
                        refresh_resp = client.get(
                            f"{graph_url}/oauth/access_token",
                            params={
                                "grant_type": "fb_exchange_token",
                                "client_id": settings.meta_app_id,
                                "client_secret": settings.meta_app_secret,
                                "fb_exchange_token": token,
                            },
                        )
                        refresh_resp.raise_for_status()
                        refresh_data = refresh_resp.json()
                except Exception:
                    logger.warning("token_refresh_failed", extra={"user_id": str(user.id)})
                    user.needs_reauth = True
                    needs_reauth_count += 1
                    _dispatch_alert(session, user, "token_expiring", "warning",
                                    f"Token for {user.name} is expiring and could not be refreshed.")
                    continue

                new_token = refresh_data.get("access_token")
                expires_in = refresh_data.get("expires_in")

                if new_token:
                    user.access_token = encrypt_token(new_token, settings.encryption_key)
                    if expires_in:
                        user.token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))
                    refreshed += 1
                    logger.info("token_refreshed", extra={"user_id": str(user.id)})
                else:
                    user.needs_reauth = True
                    needs_reauth_count += 1
                    _dispatch_alert(session, user, "token_expiring", "warning",
                                    f"Token for {user.name} is expiring and refresh returned no token.")

            except Exception:
                logger.exception("token_health_user_error", extra={"user_id": str(user.id)})

        session.commit()

    except Exception:
        logger.exception("token_health_task_error")
        session.rollback()
        return {"status": "error"}
    finally:
        session.close()

    logger.info("token_health_complete", extra={
        "checked": checked,
        "healthy": healthy,
        "refreshed": refreshed,
        "needs_reauth": needs_reauth_count,
    })
    return {
        "status": "ok",
        "checked": checked,
        "healthy": healthy,
        "refreshed": refreshed,
        "needs_reauth": needs_reauth_count,
    }


def _dispatch_alert(session, user, alert_type: str, severity: str, message: str):
    """Dispatch alert for user via first associated account."""
    try:
        from app.alerts.alert_manager import AlertManager

        if not user.accounts:
            return

        alert_manager = AlertManager()
        alert_manager.dispatch(
            db=session,
            account_id=user.accounts[0].id,
            alert_type=alert_type,
            severity=severity,
            message=message,
        )
    except Exception:
        logger.exception("token_health_alert_failed")
