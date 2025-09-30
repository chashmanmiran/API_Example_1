from typing import Optional, Generic, TypeVar, List
from typing_extensions import Annotated
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from contextlib import asynccontextmanager
from pydantic import BaseModel
from sqlmodel import SQLModel, Field, Session, select
from fastapi import APIRouter, Depends
from authentificate import router as auth_router, get_current_active_user

app = FastAPI()

from fastapi import APIRouter
games_router = APIRouter(
    prefix="/api/v1",
    tags=["games"],
    dependencies=[Depends(get_current_active_user)]  # <-- protects all games endpoints
)

# import the db helpers
from database import engine, get_session, create_db_and_tables

# ---------- Models ----------
class Game(SQLModel, table=True):
    games_id: int | None = Field(default=None, primary_key=True)
    title: Optional[str] = Field(default=None, index=True, nullable=True)
    genre: Optional[str] = Field(default=None, index=True, nullable=True)
    platform: Optional[str] = Field(default=None, index=True, nullable=True)
    release_date: Optional[str] = Field(default=None, index=True, nullable=True)
    developer: Optional[str] = Field(default=None, index=True, nullable=True)
    publisher: Optional[str] = Field(default=None, index=True, nullable=True)
    rating: Optional[str] = Field(default=None, index=True, nullable=True)
    description: Optional[str] = Field(default=None, index=True, nullable=True)
    cover_image_url: Optional[str] = Field(default=None, index=True, nullable=True)

class GameCreate(SQLModel):
    title: str
    genre: str
    platform: str
    release_date: str
    developer: str
    publisher: str
    rating: str
    description: str
    cover_image_url: str

T = TypeVar("T")

class ApiResponse(BaseModel, Generic[T]):
    data: T

class PaginatedResponse(BaseModel, Generic[T]):
    data: T
    next: Optional[str] = None
    previous: Optional[str] = None

# ---------- Dependencies ----------
SessionDep = Annotated[Session, Depends(get_session)]

# ---------- Startup (creates tables + seeds data) ----------
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    # seed only if table is empty
    with Session(engine) as session:
        if not session.exec(select(Game)).first():
            session.add_all(
                [
                    Game(
                        title="Halo Infinite",
                        genre="FPS",
                        platform="Xbox, PC",
                        release_date="2021-12-08",
                        developer="343 Industries",
                        publisher="Xbox Game Studios",
                        rating="M",
                        description="The legendary Halo series returns with the most expansive Master Chief campaign yet.",
                        cover_image_url="https://upload.wikimedia.org/wikipedia/en/1/14/Halo_Infinite.png",
                    ),
                    Game(
                        title="Mass Effect",
                        genre="Action RPG",
                        platform="Xbox 360, PC, PlayStation 3",
                        release_date="2007-11-20",
                        developer="BioWare",
                        publisher="Microsoft Game Studios, Electronic Arts",
                        rating="M",
                        description="Mass Effect is a sci-fi action role-playing game where players assume the role of Commander Shepard.",
                        cover_image_url="https://upload.wikimedia.org/wikipedia/en/8/80/MassEffectCover.png",
                    ),
                    Game(
                        title="The Witcher 3: Wild Hunt",
                        genre="Action RPG",
                        platform="PC, PlayStation 4, Xbox One, Nintendo Switch",
                        release_date="2015-05-19",
                        developer="CD Projekt Red",
                        publisher="CD Projekt",
                        rating="M",
                        description="An open-world action RPG following Geralt of Rivia.",
                        cover_image_url="https://upload.wikimedia.org/wikipedia/en/0/0c/Witcher_3_cover_art.jpg",
                    ),
                ]
            )
            session.commit()
    yield

# ⬇️ Minimal change: attach lifespan instead of recreating the app
app.router.lifespan_context = lifespan

# ---------- Routes (moved onto the protected games_router) ----------
@games_router.get("/games", response_model=PaginatedResponse[List[Game]])
def read_games(
    request: Request,
    session: SessionDep,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1),
):
    items = session.exec(
        select(Game).order_by(Game.games_id).offset(offset).limit(limit)
    ).all()

    base = str(request.url).split("?", 1)[0]
    next_url = f"{base}?offset={offset + limit}&limit={limit}" if len(items) == limit else None
    prev_url = f"{base}?offset={max(0, offset - limit)}&limit={limit}" if offset > 0 else None

    return {"data": items, "next": next_url, "previous": prev_url}

@games_router.get("/games/{id}", response_model=ApiResponse[Game])
def read_game(id: int, session: SessionDep):
    row = session.get(Game, id)
    if not row:
        raise HTTPException(status_code=404, detail="Game not found")
    return {"data": row}

@games_router.post("/games", response_model=ApiResponse[Game], status_code=201)
def create_game(game: GameCreate, session: SessionDep):
    db_game = Game.model_validate(game)  # pydantic v2
    session.add(db_game)
    session.commit()
    session.refresh(db_game)
    return {"data": db_game}

@games_router.put("/games/{id}", response_model=ApiResponse[Game])
def update_game(id: int, game: GameCreate, session: SessionDep):
    row = session.get(Game, id)
    if not row:
        raise HTTPException(status_code=404, detail="Game not found")
    for k, v in game.model_dump().items():  # pydantic v2
        setattr(row, k, v)
    session.commit()
    session.refresh(row)
    return {"data": row}

@games_router.delete("/games/{id}", status_code=204)
def delete_game(id: int, session: SessionDep):
    row = session.get(Game, id)
    if not row:
        raise HTTPException(status_code=404, detail="Game not found")
    session.delete(row)
    session.commit()

app.include_router(auth_router)     # <-- adds /register, /token, /users/me
app.include_router(games_router)    # <-- adds /api/v1/games/* (protected)
