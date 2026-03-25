"""Tests for AdDataProvider abstraction."""
import pytest

from app.models.ad_account import AccountMode
from app.providers.base import AdDataProvider, SyncAdDataProvider


class TestAdDataProviderABC:
    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            AdDataProvider()

    def test_subclass_must_implement_all_methods(self):
        class Incomplete(AdDataProvider):
            pass
        with pytest.raises(TypeError):
            Incomplete()

    def test_sync_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            SyncAdDataProvider()


class TestProviderSelection:
    def test_meta_sandbox_returns_meta_provider(self):
        from tests.factories import AdAccountFactory, UserFactory
        from app.api.deps import get_provider_for_account
        from app.providers.meta_api_provider import MetaApiProvider

        account = AdAccountFactory.build(mode=AccountMode.sandbox)
        user = UserFactory.build(access_token="tok_test")
        provider = get_provider_for_account(account, user)
        assert isinstance(provider, MetaApiProvider)

    def test_production_returns_meta_provider(self):
        from tests.factories import AdAccountFactory, UserFactory
        from app.api.deps import get_provider_for_account
        from app.providers.meta_api_provider import MetaApiProvider

        account = AdAccountFactory.build(mode=AccountMode.production)
        user = UserFactory.build(access_token="tok_test")
        provider = get_provider_for_account(account, user)
        assert isinstance(provider, MetaApiProvider)

    def test_simulation_raises_not_implemented(self):
        from tests.factories import AdAccountFactory, UserFactory
        from app.api.deps import get_provider_for_account

        account = AdAccountFactory.build(mode=AccountMode.simulation)
        user = UserFactory.build()
        with pytest.raises(NotImplementedError):
            get_provider_for_account(account, user)

    def test_meta_provider_receives_token(self):
        from app.providers.meta_api_provider import MetaApiProvider
        provider = MetaApiProvider(access_token="my_token")
        assert provider._access_token == "my_token"
