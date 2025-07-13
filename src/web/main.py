from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from core.model import UserResponse, Assessment, SessionLocal, init_db
from core.scorer import calculate_score, score_to_level
from core.badge import get_badge_url
from core import __version__
from config.loader import load_criteria_config

app = FastAPI()
templates = Jinja2Templates(directory="src/web/templates")
app.mount("/static", StaticFiles(directory="src/web/static"), name="static")

# Load criteria and categories from config
categories, criteria = load_criteria_config()

init_db()


@app.get("/", response_class=HTMLResponse)
def read_form(request: Request):
    return templates.TemplateResponse(
        "form.html",
        {
            "request": request,
            "__version__": __version__,
            "criteria": criteria,
            "categories": categories,
        },
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
