from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ProjectStatus = Literal["active", "paused", "abandoned", "completed"]


class EntryBase(BaseModel):
    date: date
    text: str = Field(min_length=1)
    mood: int = Field(ge=1, le=10)
    energy: int = Field(ge=1, le=10)
    focus: int = Field(ge=1, le=10)
    stress: int = Field(ge=1, le=10)
    sleep_hours: float = Field(ge=0, le=24)
    tags: str = ""


class EntryCreate(EntryBase):
    pass


class EntryRead(EntryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class ProjectBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = ""
    status: ProjectStatus = "active"


class ProjectCreate(ProjectBase):
    pass


class ProjectRead(ProjectBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class ProjectLogBase(BaseModel):
    date: date
    progress_score: int = Field(ge=0, le=10)
    friction_score: int = Field(ge=0, le=10)
    note: str = ""


class ProjectLogCreate(ProjectLogBase):
    pass


class ProjectLogRead(ProjectLogBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    created_at: datetime
