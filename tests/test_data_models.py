"""The persistence models create and round-trip on SQLite (portable groundwork)."""

from __future__ import annotations

from canopy.data import Case, Module, Observation, TestRun
from canopy.data.db import create_all, make_engine, make_session_factory


def test_schema_creates_and_round_trips() -> None:
    engine = make_engine("sqlite+pysqlite:///:memory:")
    create_all(engine)
    Session = make_session_factory(engine)

    with Session() as s:
        module = Module(make="Ford", model="F-250 6.7L PCM", part_number="GC3A-12B684")
        run = TestRun(module=module, profile_version="0.1", result="fail")
        run.observations.append(Observation(type="missing_can_id", value={"id": "0x100"}))
        run.case = Case(root_cause="U3 5V LDO open", component_ref="U3", confidence=0.82)
        s.add(module)
        s.commit()
        run_id = run.id

    with Session() as s:
        loaded = s.get(TestRun, run_id)
        assert loaded is not None
        assert loaded.module.make == "Ford"
        assert loaded.result == "fail"
        assert loaded.observations[0].value == {"id": "0x100"}
        assert loaded.case.root_cause == "U3 5V LDO open"
