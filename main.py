import os
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import Column, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from fastapi.staticfiles import StaticFiles


# -----------------------
# Database configuration
# -----------------------

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "pastebin")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")

DATABASE_URL = (
    f"postgresql+psycopg://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False)
Base = declarative_base()

# -----------------------
# FastAPI app
# -----------------------

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


from fastapi.responses import FileResponse

@app.get("/")
def index():
    return FileResponse("static/index.html")

class Paste(Base):
    __tablename__ = "pastes"

    slug = Column(String(255), primary_key=True)
    content = Column(Text, nullable=False)


Base.metadata.create_all(bind=engine)

# -----------------------
# Routes
# -----------------------

@app.get("/{slug}")
def read_paste(request: Request, slug: str):
    if slug in {"static", "favicon.ico"}:
        raise HTTPException(status_code=404)
    
    slug_lowercase = slug.lower()

    if slug != slug_lowercase:
        return RedirectResponse(f"/{slug_lowercase}")
        


    with SessionLocal() as db:
        paste = db.get(Paste, slug_lowercase)

    if paste:
        return templates.TemplateResponse(
            "view.html",
            {
                "request": request,
                "slug": slug_lowercase,
                "content": paste.content,
            },
        )

    return templates.TemplateResponse(
        "edit.html",
        {
            "request": request,
            "slug": slug_lowercase,
        },
    )


@app.post("/{slug}")
def create_paste(slug: str, content: str = Form(...)):
    with SessionLocal() as db:
        if db.get(Paste, slug):
            raise HTTPException(status_code=409, detail="Paste already exists")

        db.add(Paste(slug=slug, content=content))
        db.commit()

    return RedirectResponse(f"/{slug}", status_code=303)
