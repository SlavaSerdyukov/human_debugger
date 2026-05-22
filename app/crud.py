from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app import models, schemas


def create_entry(session: Session, entry: schemas.EntryCreate) -> models.Entry:
    db_entry = models.Entry(**entry.model_dump())
    session.add(db_entry)
    session.commit()
    session.refresh(db_entry)
    return db_entry


def list_entries(session: Session) -> list[models.Entry]:
    return list(session.scalars(select(models.Entry).order_by(models.Entry.date.desc(), models.Entry.id.desc())))


def create_project(session: Session, project: schemas.ProjectCreate) -> models.Project:
    db_project = models.Project(**project.model_dump())
    session.add(db_project)
    session.commit()
    session.refresh(db_project)
    return db_project


def list_projects(session: Session) -> list[models.Project]:
    return list(
        session.scalars(
            select(models.Project)
            .options(selectinload(models.Project.logs))
            .order_by(models.Project.created_at.desc(), models.Project.id.desc())
        )
    )


def get_project(session: Session, project_id: int) -> models.Project | None:
    return session.scalar(
        select(models.Project)
        .where(models.Project.id == project_id)
        .options(selectinload(models.Project.logs))
    )


def create_project_log(
    session: Session,
    project_id: int,
    log: schemas.ProjectLogCreate,
) -> models.ProjectLog:
    db_log = models.ProjectLog(project_id=project_id, **log.model_dump())
    session.add(db_log)
    session.commit()
    session.refresh(db_log)
    return db_log


def seed_demo_data(session: Session) -> None:
    if session.scalar(select(models.Entry.id).limit(1)):
        return

    today = date.today()
    demo_entries = [
        schemas.EntryCreate(
            date=today - timedelta(days=i),
            text=f"Demo log {i}: shipped small pieces, noticed focus drift around context switches.",
            mood=max(3, 8 - i // 3),
            energy=max(2, 8 - i // 2),
            focus=max(2, 8 - i),
            stress=min(9, 3 + i // 2),
            sleep_hours=7.5 if i < 4 else 5.5,
            tags="deep-work" if i < 3 else "procrastination, stuck",
        )
        for i in range(10)
    ]
    for entry in demo_entries:
        create_entry(session, entry)

    project = create_project(
        session,
        schemas.ProjectCreate(
            name="Neon Notebook",
            description="A demo project with an early burst and later friction.",
            status="active",
        ),
    )
    scores = [(9, 2), (8, 3), (7, 4), (4, 7), (3, 8)]
    for offset, (progress, friction) in enumerate(scores):
        create_project_log(
            session,
            project.id,
            schemas.ProjectLogCreate(
                date=today - timedelta(days=12 - offset),
                progress_score=progress,
                friction_score=friction,
                note="Demo project signal.",
            ),
        )
