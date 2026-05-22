from sqlalchemy.orm import Session

from app import crud, models, schemas


def create_project(session: Session, project: schemas.ProjectCreate) -> models.Project:
    return crud.create_project(session, project)


def list_projects(session: Session) -> list[models.Project]:
    return crud.list_projects(session)


def get_project(session: Session, project_id: int) -> models.Project | None:
    return crud.get_project(session, project_id)


def create_project_log(
    session: Session,
    project_id: int,
    log: schemas.ProjectLogCreate,
) -> models.ProjectLog:
    return crud.create_project_log(session, project_id, log)


def seed_demo_data(session: Session) -> None:
    crud.seed_demo_data(session)
