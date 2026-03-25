"""Tests for Docker Compose configuration and entrypoint scripts."""
import os

import yaml

REPO_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)


class TestDockerCompose:
    def setup_method(self):
        compose_path = os.path.join(REPO_ROOT, "docker-compose.yml")
        with open(compose_path) as f:
            self.config = yaml.safe_load(f)

    def test_compose_config_valid_yaml(self):
        assert self.config is not None
        assert "services" in self.config

    def test_all_services_defined(self):
        expected = {
            "web",
            "celery-worker",
            "celery-beat",
            "redis",
            "postgres",
            "frontend",
        }
        assert expected == set(self.config["services"].keys())

    def test_web_depends_on_postgres_and_redis_healthy(self):
        deps = self.config["services"]["web"]["depends_on"]
        assert deps["postgres"]["condition"] == "service_healthy"
        assert deps["redis"]["condition"] == "service_healthy"

    def test_celery_worker_depends_on_web_healthy(self):
        deps = self.config["services"]["celery-worker"]["depends_on"]
        assert deps["web"]["condition"] == "service_healthy"

    def test_celery_beat_depends_on_redis_and_web(self):
        deps = self.config["services"]["celery-beat"]["depends_on"]
        assert "redis" in deps
        assert "web" in deps


class TestEntrypointScripts:
    def test_entrypoint_runs_alembic(self):
        path = os.path.join(REPO_ROOT, "backend", "entrypoint.sh")
        with open(path) as f:
            content = f.read()
        assert "alembic upgrade head" in content

    def test_worker_entrypoint_does_not_run_alembic(self):
        path = os.path.join(REPO_ROOT, "backend", "entrypoint-worker.sh")
        with open(path) as f:
            content = f.read()
        assert "alembic" not in content
