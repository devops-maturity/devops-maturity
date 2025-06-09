from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from ..core.model import Criteria, UserResponse, Assessment, SessionLocal
from ..core.scorer import calculate_score, score_to_level
from ..badges.generator import generate_badge

app = FastAPI()
templates = Jinja2Templates(directory="src/web/templates")
app.mount("/static", StaticFiles(directory="src/web/static"), name="static")

# categories of criteria
categories = {
    "CI/CD Basics": "CI/CD Basics",
    "Quality": "Quality",
    "Security": "Security",
    "Secure Supply Chain": "Secure Supply Chain",
    "Reporting": "Reporting",
    "Analysis": "Analysis",
}

criteria = [
    # CI/CD Basics
    Criteria(
        id="build_branch",
        question="Build a specific branch (CI/CD Basics, must have)",
        weight=1.0,
    ),
    Criteria(
        id="build_pr",
        question="Build upon pull request (CI/CD Basics, must have)",
        weight=1.0,
    ),
    Criteria(id="docker", question="Docker (CI/CD Basics, nice to have)", weight=0.5),
    # Quality
    Criteria(
        id="func_test",
        question="Automated Testing: Functional testing (Quality, must have)",
        weight=1.0,
    ),
    Criteria(
        id="perf_test",
        question="Automated Testing: Performance testing (Quality, must have)",
        weight=1.0,
    ),
    Criteria(
        id="code_coverage", question="Code Coverage (Quality, nice to have)", weight=0.5
    ),
    Criteria(
        id="accessibility",
        question="Accessibility Testing (Quality, nice to have)",
        weight=0.5,
    ),
    # Security
    Criteria(
        id="security_scan", question="Security scan (Security, must have)", weight=1.0
    ),
    Criteria(
        id="license_scan", question="License scan (Security, nice to have)", weight=0.5
    ),
    # Secure Supply Chain
    Criteria(
        id="doc_build_chain",
        question="Documented Build Chain (Secure Supply Chain, must have)",
        weight=1.0,
    ),
    Criteria(
        id="cicd_as_code",
        question="CICD as coded (Secure Supply Chain, must have)",
        weight=1.0,
    ),
    Criteria(
        id="signed_artifacts",
        question="Artifacts are signed (Secure Supply Chain, nice to have)",
        weight=0.5,
    ),
    Criteria(
        id="artifactory_download",
        question="Artifactory download for Package Managers (Secure Supply Chain, nice to have)",
        weight=0.5,
    ),
    # Reporting
    Criteria(
        id="reporting",
        question="Email/Slack reporting functionality (Reporting, must have)",
        weight=1.0,
    ),
    # Analysis
    Criteria(
        id="quality_gate", question="Quality Gate (Analysis, nice to have)", weight=0.5
    ),
    Criteria(id="code_lint", question="Code Lint (Analysis, nice to have)", weight=0.5),
    Criteria(
        id="static_analysis",
        question="Static code analysis (Analysis, nice to have)",
        weight=0.5,
    ),
    Criteria(
        id="dynamic_analysis",
        question="Dynamic code analysis (Analysis, nice to have)",
        weight=0.5,
    ),
]


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
    badge_filename = "devops-maturity.svg"
    badge_path = f"src/web/static/{badge_filename}"
    badge_url = f"/static/{badge_filename}"
    generate_badge(score, level, badge_path)
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
        {"request": request, "assessments": assessment_data},
    )
