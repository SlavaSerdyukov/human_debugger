from datetime import date
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app import schemas
from app.database import create_db_and_tables, get_session
from app.services import analytics_service, entry_service, project_service

BASE_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    create_db_and_tables()
    yield


app = FastAPI(title="Human Debugger", version="0.1.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

FAVICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
<rect width="64" height="64" rx="12" fill="#0d1117"/>
<path d="M14 20h36M14 32h26M14 44h18" stroke="#3fb950" stroke-width="6" stroke-linecap="round"/>
<circle cx="48" cy="44" r="5" fill="#58a6ff"/>
</svg>"""


def redirect(path: str) -> RedirectResponse:
    return RedirectResponse(path, status_code=303)


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    return Response(content=FAVICON_SVG, media_type="image/svg+xml")


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, session: Annotated[Session, Depends(get_session)]) -> HTMLResponse:
    entries = entry_service.list_entries(session)
    projects = project_service.list_projects(session)
    report = analytics_service.build_report(session)
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {"request": request, "entries": entries[:5], "projects": projects, "report": report, "today": date.today()},
    )


@app.get("/entries", response_class=HTMLResponse)
def entries_page(request: Request, session: Annotated[Session, Depends(get_session)]) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "entries.html",
        {"request": request, "entries": entry_service.list_entries(session), "today": date.today()},
    )


@app.post("/entries")
def create_entry(
    session: Annotated[Session, Depends(get_session)],
    date_value: Annotated[date, Form(alias="date")],
    text: Annotated[str, Form()],
    mood: Annotated[int, Form()],
    energy: Annotated[int, Form()],
    focus: Annotated[int, Form()],
    stress: Annotated[int, Form()],
    sleep_hours: Annotated[float, Form()],
    tags: Annotated[str, Form()] = "",
) -> RedirectResponse:
    entry = schemas.EntryCreate(
        date=date_value,
        text=text,
        mood=mood,
        energy=energy,
        focus=focus,
        stress=stress,
        sleep_hours=sleep_hours,
        tags=tags,
    )
    entry_service.create_entry(session, entry)
    return redirect("/entries")


@app.get("/projects", response_class=HTMLResponse)
def projects_page(request: Request, session: Annotated[Session, Depends(get_session)]) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "projects.html",
        {"request": request, "projects": project_service.list_projects(session)},
    )


@app.post("/projects")
def create_project(
    session: Annotated[Session, Depends(get_session)],
    name: Annotated[str, Form()],
    description: Annotated[str, Form()] = "",
    status: Annotated[schemas.ProjectStatus, Form()] = "active",
) -> RedirectResponse:
    project_service.create_project(session, schemas.ProjectCreate(name=name, description=description, status=status))
    return redirect("/projects")


@app.get("/projects/{project_id}", response_class=HTMLResponse)
def project_detail(
    project_id: int,
    request: Request,
    session: Annotated[Session, Depends(get_session)],
) -> HTMLResponse:
    project = project_service.get_project(session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return templates.TemplateResponse(
        request,
        "project_detail.html",
        {"request": request, "project": project, "today": date.today()},
    )


@app.post("/projects/{project_id}/logs")
def create_log(
    project_id: int,
    session: Annotated[Session, Depends(get_session)],
    date_value: Annotated[date, Form(alias="date")],
    progress_score: Annotated[int, Form()],
    friction_score: Annotated[int, Form()],
    note: Annotated[str, Form()] = "",
) -> RedirectResponse:
    if not project_service.get_project(session, project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    project_service.create_project_log(
        session,
        project_id,
        schemas.ProjectLogCreate(
            date=date_value,
            progress_score=progress_score,
            friction_score=friction_score,
            note=note,
        ),
    )
    return redirect(f"/projects/{project_id}")


@app.get("/debug-report", response_class=HTMLResponse)
def debug_report(request: Request, session: Annotated[Session, Depends(get_session)]) -> HTMLResponse:
    report, llm_summary = analytics_service.build_report_with_llm_summary(session)
    return templates.TemplateResponse(
        request,
        "debug_report.html",
        {"request": request, "report": report, "llm_summary": llm_summary},
    )


@app.get("/api/debug-report")
def api_debug_report(session: Annotated[Session, Depends(get_session)]) -> dict:
    return analytics_service.build_report(session)


@app.get("/api/llm-status")
def api_llm_status() -> dict:
    return analytics_service.llm_status()


@app.api_route("/seed-demo", methods=["GET", "POST"])
def seed_demo(session: Annotated[Session, Depends(get_session)]) -> RedirectResponse:
    project_service.seed_demo_data(session)
    return redirect("/debug-report")
