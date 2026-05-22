from collections.abc import Generator
from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app import crud, schemas
from app.database import Base


@pytest.fixture()
def session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    local_session = sessionmaker(bind=engine)
    db = local_session()
    try:
        yield db
    finally:
        db.close()


def test_create_entry(session: Session) -> None:
    created = crud.create_entry(
        session,
        schemas.EntryCreate(
            date=date(2026, 5, 17),
            text="Shipped a tiny patch.",
            mood=7,
            energy=6,
            focus=8,
            stress=3,
            sleep_hours=7.5,
            tags="deep-work",
        ),
    )

    assert created.id is not None
    assert crud.list_entries(session)[0].text == "Shipped a tiny patch."


def test_create_project_and_log(session: Session) -> None:
    project = crud.create_project(
        session,
        schemas.ProjectCreate(name="Human Debugger", description="Local MVP", status="active"),
    )
    log = crud.create_project_log(
        session,
        project.id,
        schemas.ProjectLogCreate(date=date(2026, 5, 17), progress_score=8, friction_score=2, note="Started."),
    )
    loaded = crud.get_project(session, project.id)

    assert project.id is not None
    assert log.project_id == project.id
    assert loaded is not None
    assert len(loaded.logs) == 1
