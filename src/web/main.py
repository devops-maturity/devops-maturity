from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from core.model import Criteria, UserResponse
from core.scorer import calculate_score, score_to_level
from badges.generator import generate_badge

app = FastAPI()
templates = Jinja2Templates(directory="devops_maturity/web/templates")
app.mount("/static", StaticFiles(directory="devops_maturity/web/static"), name="static")

criteria = [
    Criteria(id="ci", question="Do you use continuous integration?", weight=1.0),
    Criteria(id="cd", question="Do you have continuous delivery?", weight=1.0),
    Criteria(id="iac", question="Do you use infrastructure as code?", weight=1.0),
]


@app.get("/", response_class=HTMLResponse)
def read_form(request: Request):
    return templates.TemplateResponse(
        "form.html", {"request": request, "criteria": criteria}
    )


@app.post("/submit", response_class=HTMLResponse)
def submit_form(
    request: Request, ci: str = Form("no"), cd: str = Form("no"), iac: str = Form("no")
):
    responses = [
        UserResponse(id="ci", answer=ci == "yes"),
        UserResponse(id="cd", answer=cd == "yes"),
        UserResponse(id="iac", answer=iac == "yes"),
    ]
    score = calculate_score(criteria, responses)
    level = score_to_level(score)
    generate_badge(score, level, "devops_maturity/web/static/badge.svg")
    return templates.TemplateResponse(
        "result.html", {"request": request, "score": score, "level": level}
    )


@app.get("/badge.svg")
def get_badge():
    return FileResponse(
        "devops_maturity/web/static/badge.svg", media_type="image/svg+xml"
    )
