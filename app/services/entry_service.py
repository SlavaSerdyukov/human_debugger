from sqlalchemy.orm import Session

from app import crud, models, schemas


def create_entry(session: Session, entry: schemas.EntryCreate) -> models.Entry:
    return crud.create_entry(session, entry)


def list_entries(session: Session) -> list[models.Entry]:
    return crud.list_entries(session)
