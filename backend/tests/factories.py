"""Model factories for test data generation."""
import factory
from uuid_utils import uuid7

from app.models import (
    User, AdAccount, Campaign, SpendSnapshot, BudgetRule,
    RuleEvaluation, PauseLog, AlertLog, SimulationState,
    AccountMode, CampaignStatus, SpendSource, RuleType, RuleAction,
    EvaluationResult, AlertType, AlertChannel,
)


class UserFactory(factory.Factory):
    class Meta:
        model = User

    id = factory.LazyFunction(uuid7)
    facebook_id = factory.Sequence(lambda n: f"fb_{n}")
    name = factory.Faker("name")
    email = factory.Faker("email")
    access_token = None
    token_expires_at = None
    needs_reauth = False


class AdAccountFactory(factory.Factory):
    class Meta:
        model = AdAccount

    id = factory.LazyFunction(uuid7)
    meta_account_id = factory.Sequence(lambda n: f"act_{n}")
    name = factory.Sequence(lambda n: f"Account {n}")
    mode = AccountMode.simulation
    currency = "USD"
    timezone = "UTC"
    is_active = True


class CampaignFactory(factory.Factory):
    class Meta:
        model = Campaign

    id = factory.LazyFunction(uuid7)
    account_id = factory.LazyFunction(uuid7)
    meta_campaign_id = factory.Sequence(lambda n: f"camp_{n}")
    name = factory.Sequence(lambda n: f"Campaign {n}")
    status = CampaignStatus.ACTIVE
    daily_budget = None
    lifetime_budget = None


class SpendSnapshotFactory(factory.Factory):
    class Meta:
        model = SpendSnapshot

    id = factory.LazyFunction(uuid7)
    campaign_id = factory.LazyFunction(uuid7)
    spend = factory.Faker("pydecimal", left_digits=3, right_digits=2, positive=True)
    source = SpendSource.simulator


class BudgetRuleFactory(factory.Factory):
    class Meta:
        model = BudgetRule

    id = factory.LazyFunction(uuid7)
    account_id = factory.LazyFunction(uuid7)
    campaign_id = None
    rule_type = RuleType.daily_limit
    threshold = factory.Faker("pydecimal", left_digits=3, right_digits=2, positive=True)
    action = RuleAction.soft_pause
    is_active = True


class RuleEvaluationFactory(factory.Factory):
    class Meta:
        model = RuleEvaluation

    id = factory.LazyFunction(uuid7)
    rule_id = factory.LazyFunction(uuid7)
    result = EvaluationResult.ok
    current_value = factory.Faker("pydecimal", left_digits=3, right_digits=2, positive=True)
    threshold_value = factory.Faker("pydecimal", left_digits=3, right_digits=2, positive=True)


class PauseLogFactory(factory.Factory):
    class Meta:
        model = PauseLog

    id = factory.LazyFunction(uuid7)
    campaign_id = factory.LazyFunction(uuid7)
    rule_id = None
    reason = "Budget exceeded"


class AlertLogFactory(factory.Factory):
    class Meta:
        model = AlertLog

    id = factory.LazyFunction(uuid7)
    account_id = factory.LazyFunction(uuid7)
    alert_type = AlertType.budget_warning
    channel = AlertChannel.telegram
    message = "Test alert"
    acknowledged = False


class SimulationStateFactory(factory.Factory):
    class Meta:
        model = SimulationState

    id = factory.LazyFunction(uuid7)
    account_id = factory.LazyFunction(uuid7)
    state_data = factory.LazyFunction(dict)
    is_running = False
    last_tick = None
