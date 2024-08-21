from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware  # Add this import
from fastapi.responses import RedirectResponse
from app.api import auth
from app.core.config import settings
from app.db.database import get_db
from app.models.user import User


from gpt_researcher_master.backend.server import app as gpt_researcher_app

app = FastAPI(title=settings.PROJECT_NAME)
app.add_middleware(SessionMiddleware, secret_key="mlsense.api")  # Replace with a secure secret key

templates = Jinja2Templates(directory="app/templates")

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])

app.mount("/gpt-researcher", gpt_researcher_app)
@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    user = await auth.get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=302, headers={"Location": "/login"})
    return RedirectResponse(url="/gpt-researcher", status_code=302)
    # return templates.TemplateResponse("home.html", {"request": request, "user": user})

@app.get("/accounts/google/login/callback/", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)