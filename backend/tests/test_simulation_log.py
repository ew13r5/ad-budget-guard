"""Tests for the SimulationLog model."""
from datetime import datetime
from uuid import uuid4

from app.models.simulation_log import SimulationLog


class TestSimulationLogModel:
    def test_model_has_expected_tablename(self):
        assert SimulationLog.__tablename__ == "simulation_log"

    def test_model_has_expected_columns(self):
        columns = {c.name for c in SimulationLog.__table__.columns}
        expected = {"id", "event_type", "campaign_id", "sim_time", "real_time", "details", "created_at", "updated_at"}
        assert expected.issubset(columns)

    def test_model_has_expected_indexes(self):
        index_names = {idx.name for idx in SimulationLog.__table__.indexes}
        assert "ix_simulation_log_event_type_real_time" in index_names
        assert "ix_simulation_log_campaign_id_real_time" in index_names

    def test_campaign_id_is_nullable(self):
        col = SimulationLog.__table__.columns["campaign_id"]
        assert col.nullable is True

    def test_details_is_nullable(self):
        col = SimulationLog.__table__.columns["details"]
        assert col.nullable is True

    def test_model_instantiation(self):
        log = SimulationLog(
            event_type="pause",
            campaign_id=uuid4(),
            sim_time=datetime(2024, 1, 15, 14, 30),
            details={"scenario": "normal"},
        )
        assert log.event_type == "pause"
        assert log.details == {"scenario": "normal"}

    def test_model_instantiation_without_campaign(self):
        log = SimulationLog(
            event_type="reset",
            sim_time=datetime(2024, 1, 15, 0, 0),
        )
        assert log.campaign_id is None

    def test_model_in_init_exports(self):
        from app.models import SimulationLog as ExportedLog
        assert ExportedLog is SimulationLog
