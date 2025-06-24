from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from core.model import Criteria, UserResponse, Assessment, SessionLocal, init_db
from core.scorer import calculate_score, score_to_level
from core.badge import get_badge_url

app = FastAPI()
templates = Jinja2Templates(directory="src/web/templates")
app.mount("/static", StaticFiles(directory="src/web/static"), name="static")

# categories of criteria
categories = [
    "Basics",
    "Quality",
    "Security",
    "Supply Chain Security",
    "Analysis",
    "Reporting",
]

criteria = [
    # Basics
    Criteria(id="D101", category="Basics", criteria="Branch Builds (🟢)", weight=1.0),
    Criteria(
        id="D102", category="Basics", criteria="Pull Request Builds (🟢)", weight=1.0
    ),
    Criteria(
        id="D103",
        category="Basics",
        criteria="Clean Build Environments (🟡)",
        weight=0.5,
    ),
    # Quality
    Criteria(id="D201", category="Quality", criteria="Unit Testing (🟢)", weight=1.0),
    Criteria(
        id="D202", category="Quality", criteria="Functional Testing (🟢)", weight=1.0
    ),
    Criteria(
        id="D203", category="Quality", criteria="Performance Testing (🟡)", weight=0.5
    ),
    Criteria(id="D204", category="Quality", criteria="Code Coverage (🟡)", weight=0.5),
    Criteria(
        id="D205", category="Quality", criteria="Accessibility Testing (🟡)", weight=0.5
    ),
    # Security
    Criteria(
        id="D301", category="Security", criteria="Security Scanning (🟢)", weight=1.0
    ),
    Criteria(
        id="D302", category="Security", criteria="License Scanning (🟡)", weight=0.5
    ),
    # Supply Chain Security
    Criteria(
        id="D401",
        category="Supply Chain Security",
        criteria="Documented Build Process (🟢)",
        weight=1.0,
    ),
    Criteria(
        id="D402",
        category="Supply Chain Security",
        criteria="CI/CD as Code (🟢)",
        weight=1.0,
    ),
    Criteria(
        id="D403",
        category="Supply Chain Security",
        criteria="Artifact Signing (🟡)",
        weight=0.5,
    ),
    Criteria(
        id="D404",
        category="Supply Chain Security",
        criteria="Dependency Pinning (🟡)",
        weight=0.5,
    ),
    # Analysis
    Criteria(
        id="D501", category="Analysis", criteria="Static Code Analysis (🟡)", weight=0.5
    ),
    Criteria(
        id="D502",
        category="Analysis",
        criteria="Dynamic Code Analysis (🟡)",
        weight=0.5,
    ),
    Criteria(id="D503", category="Analysis", criteria="Code Linting (🟡)", weight=0.5),
    # Reporting
    Criteria(
        id="D601",
        category="Reporting",
        criteria="Notifications & Alerts (🟢)",
        weight=1.0,
    ),
    Criteria(
        id="D602", category="Reporting", criteria="Attached Reports (🟢)", weight=1.0
    ),
]

init_db()


@app.get("/", response_class=HTMLResponse)
def read_form(request: Request):
    return templates.TemplateResponse(
        "form.html",
        {"request": request, "criteria": criteria, "categories": categories},
    )


@app.post("/submit")
async def submit(request: Request):
    form = await request.form()
    responses = []
    responses_dict = {}
    for k, v in form.items():
        answer = v == "yes"
        responses.append(UserResponse(id=k, answer=answer))
        responses_dict[k] = answer  # store as dict for database

    # Save to database
    db = SessionLocal()
    assessment = Assessment(responses=responses_dict)
    db.add(assessment)
    db.commit()
    db.close()

    score = calculate_score(criteria, responses)
    level = score_to_level(score)
    badge_url = get_badge_url(level)
    return templates.TemplateResponse(
        "result.html",
        {
            "request": request,
            "score": score,
            "level": level,
            "badge_url": badge_url,
        },
    )


@app.get("/badge.svg")
def get_badge():
    return FileResponse("src/web/static/badge.svg", media_type="image/svg+xml")


@app.get("/assessments", response_class=HTMLResponse)
def list_assessments(request: Request):
    db = SessionLocal()
    assessments = db.query(Assessment).all()
    db.close()
    assessment_data = []
    for a in assessments:
        # Convert responses from dict to UserResponse objects
        responses = [UserResponse(id=k, answer=v) for k, v in a.responses.items()]
        point = calculate_score(criteria, responses)
        assessment_data.append({"id": a.id, "responses": a.responses, "point": point})
    return templates.TemplateResponse(
        "assessments.html",
        {
            "request": request,
            "assessments": assessment_data,
            "criteria_list": criteria,
        },
    )
