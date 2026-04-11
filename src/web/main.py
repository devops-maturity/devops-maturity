import os
from fastapi import FastAPI
from fastapi import HTTPException
from starlette.middleware.sessions import SessionMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi import Request
from fastapi import Form
from fastapi.responses import FileResponse, RedirectResponse
from core.model import UserResponse, Assessment, SessionLocal, init_db, User
from core.scorer import calculate_score, score_to_level, calculate_category_scores
from core.badge import get_badge_url
from core import __version__
from config.loader import load_criteria_config

# Handle bcrypt version compatibility issue
try:
    from passlib.hash import bcrypt
except (ImportError, AttributeError):
    # Fallback for bcrypt version compatibility issues
    import passlib.hash

    # Force bcrypt to use the correct backend
    bcrypt = passlib.hash.bcrypt.using(rounds=12)

from sqlalchemy.exc import IntegrityError
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from dotenv import load_dotenv


app = FastAPI(
    title="DevOps Maturity Assessment",
    description="Assess DevOps, DevSecOps, and supply chain maturity from the web or CLI.",
    version=__version__,
)


@app.get("/edit-assessment/{assessment_id}", response_class=HTMLResponse)
def edit_assessment_form(request: Request, assessment_id: int):
    user = get_current_user(request)
    db = SessionLocal()
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    db.close()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if not user or assessment.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not allowed")
    return templates.TemplateResponse(
        request,
        "edit_assessment.html",
        {
            "assessment": assessment,
            "criteria": criteria,
            "categories": categories,
            "user": user,
        },
    )


@app.post("/edit-assessment/{assessment_id}", response_class=HTMLResponse)
async def edit_assessment_submit(request: Request, assessment_id: int):
    user = get_current_user(request)
    db = SessionLocal()
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        db.close()
        raise HTTPException(status_code=404, detail="Assessment not found")
    if not user or assessment.user_id != user.id:
        db.close()
        raise HTTPException(status_code=403, detail="Not allowed")
    form = await request.form()
    project_name = form.get("project_name")
    if not project_name:
        db.close()
        return templates.TemplateResponse(
            request,
            "edit_assessment.html",
            {
                "assessment": assessment,
                "criteria": criteria,
                "categories": categories,
                "user": user,
                "error": "Project Name is required.",
            },
        )
    project_url = form.get("project_url") or None
    responses_dict = {}
    for k, v in form.items():
        if k in ("project_name", "project_url"):
            continue
        responses_dict[k] = v == "yes"
    assessment.project_name = project_name
    assessment.project_url = project_url
    assessment.responses = responses_dict
    db.commit()
    db.close()
    return RedirectResponse("/assessments", status_code=302)


load_dotenv()
config = Config(".env") if os.path.exists(".env") else Config(environ=os.environ)
oauth = OAuth(config)

# Only register OAuth providers if credentials are provided
google_client_id = os.environ.get("GOOGLE_CLIENT_ID")
google_client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
if google_client_id and google_client_secret:
    oauth.register(
        name="google",
        client_id=google_client_id,
        client_secret=google_client_secret,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )

github_client_id = os.environ.get("GITHUB_CLIENT_ID")
github_client_secret = os.environ.get("GITHUB_CLIENT_SECRET")
if github_client_id and github_client_secret:
    oauth.register(
        name="github",
        client_id=github_client_id,
        client_secret=github_client_secret,
        access_token_url="https://github.com/login/oauth/access_token",
        access_token_params=None,
        authorize_url="https://github.com/login/oauth/authorize",
        authorize_params=None,
        api_base_url="https://api.github.com/",
        client_kwargs={"scope": "user:email"},
    )

app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("SESSION_SECRET_KEY", "devops-maturity-secret"),
)
templates = Jinja2Templates(directory="src/web/templates")
app.mount("/static", StaticFiles(directory="src/web/static"), name="static")

# Load criteria and categories from config
categories, criteria = load_criteria_config()

init_db()


def get_assessment_template_context(request: Request, **extra):
    """Build shared context for the assessment form."""
    category_counts = {
        category: len([c for c in criteria if c.category == category])
        for category in categories
    }
    context = {
        "__version__": __version__,
        "criteria": criteria,
        "criteria_count": len(criteria),
        "categories": categories,
        "category_counts": category_counts,
        "user": get_current_user(request),
    }
    context.update(extra)
    return context


def is_oauth_provider_enabled(provider: str) -> bool:
    """Check if OAuth provider is configured and enabled"""
    if provider == "google":
        return bool(
            os.environ.get("GOOGLE_CLIENT_ID")
            and os.environ.get("GOOGLE_CLIENT_SECRET")
        )
    elif provider == "github":
        return bool(
            os.environ.get("GITHUB_CLIENT_ID")
            and os.environ.get("GITHUB_CLIENT_SECRET")
        )
    return False


def get_current_user(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    db.close()
    return user


@app.get("/register", response_class=HTMLResponse)
def register_form(request: Request):
    user = get_current_user(request)
    if user:
        return RedirectResponse("/", status_code=302)

    # Check which OAuth providers are available
    oauth_providers = {
        "google": is_oauth_provider_enabled("google"),
        "github": is_oauth_provider_enabled("github"),
    }

    return templates.TemplateResponse(
        request, "register.html", {"oauth_providers": oauth_providers}
    )


@app.post("/register", response_class=HTMLResponse)
async def register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
):
    db = SessionLocal()
    hashed_password = bcrypt.hash(password)
    user = User(username=username, email=email, password_hash=hashed_password)
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
        request.session["user_id"] = user.id
        db.close()
        return RedirectResponse("/", status_code=302)
    except IntegrityError:
        db.rollback()
        db.close()
        # Check which OAuth providers are available for error response
        oauth_providers = {
            "google": is_oauth_provider_enabled("google"),
            "github": is_oauth_provider_enabled("github"),
        }
        return templates.TemplateResponse(
            request,
            "register.html",
            {
                "error": "Username or email already exists.",
                "oauth_providers": oauth_providers,
            },
        )


@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    user = get_current_user(request)
    if user:
        return RedirectResponse("/", status_code=302)

    # Check for OAuth error
    error = request.query_params.get("error")
    if error == "oauth_not_configured":
        error = "OAuth login is not configured. Please contact the administrator."

    # Check which OAuth providers are available
    oauth_providers = {
        "google": is_oauth_provider_enabled("google"),
        "github": is_oauth_provider_enabled("github"),
    }

    return templates.TemplateResponse(
        request,
        "login.html",
        {"error": error, "oauth_providers": oauth_providers},
    )


@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    db = SessionLocal()
    user = (
        db.query(User)
        .filter((User.username == username) | (User.email == username))
        .first()
    )
    db.close()
    if (
        not user
        or not user.password_hash
        or not bcrypt.verify(password, user.password_hash)
    ):
        oauth_providers = {
            "google": is_oauth_provider_enabled("google"),
            "github": is_oauth_provider_enabled("github"),
        }
        return templates.TemplateResponse(
            request,
            "login.html",
            {"error": "Invalid credentials.", "oauth_providers": oauth_providers},
        )
    request.session["user_id"] = user.id
    return RedirectResponse("/", status_code=302)


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=302)


@app.get("/auth/{provider}")
async def oauth_login(request: Request, provider: str):
    if provider not in ("google", "github"):
        return RedirectResponse("/login")

    # Check if the OAuth provider is configured
    if not is_oauth_provider_enabled(provider):
        return RedirectResponse("/login?error=oauth_not_configured")

    redirect_uri = request.url_for("oauth_callback", provider=provider)
    return await oauth.create_client(provider).authorize_redirect(request, redirect_uri)


@app.get("/auth/callback/{provider}")
async def oauth_callback(request: Request, provider: str):
    if provider not in ("google", "github"):
        return RedirectResponse("/login")

    # Check if the OAuth provider is configured
    if not is_oauth_provider_enabled(provider):
        return RedirectResponse("/login?error=oauth_not_configured")

    client = oauth.create_client(provider)
    token = await client.authorize_access_token(request)
    if provider == "google":
        user_info = await client.parse_id_token(request, token)
        email = user_info.get("email")
        username = user_info.get("name") or email.split("@")[0]
        oauth_id = user_info.get("sub")
    elif provider == "github":
        resp = await client.get("user", token=token)
        profile = resp.json()
        email = profile.get("email")
        if not email:
            # fetch primary email
            emails_resp = await client.get("user/emails", token=token)
            emails = emails_resp.json()
            email = next((e["email"] for e in emails if e.get("primary")), None)
        username = profile.get("login")
        oauth_id = str(profile.get("id"))
    else:
        return RedirectResponse("/login")
    db = SessionLocal()
    user = (
        db.query(User)
        .filter((User.oauth_provider == provider) & (User.oauth_id == oauth_id))
        .first()
    )
    if not user:
        # If user with this email exists, link accounts
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.oauth_provider = provider
            user.oauth_id = oauth_id
        else:
            user = User(
                username=username,
                email=email,
                oauth_provider=provider,
                oauth_id=oauth_id,
            )
            db.add(user)
        db.commit()
        db.refresh(user)
    request.session["user_id"] = user.id
    db.close()
    return RedirectResponse("/", status_code=302)


@app.get("/", response_class=HTMLResponse)
def read_form(request: Request):
    return templates.TemplateResponse(
        request,
        "form.html",
        get_assessment_template_context(request),
    )


@app.post("/submit")
async def submit(request: Request):
    form = await request.form()
    project_name = form.get("project_name")
    if not project_name:
        return templates.TemplateResponse(
            request,
            "form.html",
            get_assessment_template_context(request, error="Project Name is required."),
        )
    project_url = form.get("project_url") or None
    responses = []
    responses_dict = {}
    for k, v in form.items():
        if k in ("project_name", "project_url"):
            continue
        answer = v == "yes"
        responses.append(UserResponse(id=k, answer=answer))
        responses_dict[k] = answer  # store as dict for database

    user = get_current_user(request)
    user_id = user.id if user else None

    # Save to database
    db = SessionLocal()
    assessment = Assessment(
        project_name=project_name,
        project_url=project_url,
        user_id=user_id,
        responses=responses_dict,
    )
    db.add(assessment)
    db.commit()
    db.close()

    score = calculate_score(criteria, responses)
    level = score_to_level(score)
    badge_url = get_badge_url(level)
    category_scores = calculate_category_scores(criteria, responses)
    # Build per-criterion result: include answer and description for recommendations
    criteria_results = [
        {
            "id": c.id,
            "category": c.category,
            "criteria": c.criteria,
            "description": c.description,
            "answer": responses_dict.get(c.id, False),
        }
        for c in criteria
    ]
    return templates.TemplateResponse(
        request,
        "result.html",
        {
            "score": score,
            "level": level,
            "badge_url": badge_url,
            "project_name": project_name,
            "project_url": project_url,
            "user": user,
            "category_scores": category_scores,
            "criteria_results": criteria_results,
            "categories": categories,
        },
    )


@app.get("/badge.svg")
def get_badge():
    return FileResponse("src/web/static/badge.svg", media_type="image/svg+xml")


@app.get("/assessments", response_class=HTMLResponse)
def list_assessments(request: Request):
    user = get_current_user(request)
    db = SessionLocal()
    assessments = db.query(Assessment).all()
    users = {u.id: u for u in db.query(User).all()}
    db.close()
    assessment_data = []
    for a in assessments:
        responses = [UserResponse(id=k, answer=v) for k, v in a.responses.items()]
        point = calculate_score(criteria, responses)
        level = score_to_level(point)
        badge_url = get_badge_url(level)
        assessment_data.append(
            {
                "id": a.id,
                "project_name": getattr(a, "project_name", ""),
                "project_url": getattr(a, "project_url", None),
                "user": users.get(a.user_id),
                "responses": a.responses,
                "point": point,
                "level": level,
                "badge_url": badge_url,
            }
        )
    return templates.TemplateResponse(
        request,
        "assessments.html",
        {
            "assessments": assessment_data,
            "criteria_list": criteria,
            "user": user,
        },
    )
