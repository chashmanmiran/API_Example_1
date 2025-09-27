from annotated_types import T
from fastapi.concurrency import asynccontextmanager
from pydantic import BaseModel
from sqlmodel import SQLModel, Field, func
from typing_extensions import Annotated
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from typing import Any, Generic, TypeVar
from sqlmodel import SQLModel, create_engine
from sqlmodel import SQLModel, Session, select
from typing import Optional

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

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
    
SessionDep = Annotated[Session, Depends(get_session)]

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    with Session(engine) as session:
        if not session.exec(select(Game)).first():
            session.add_all([
                Game(title = "Halo Infinite", genre = "FPS", platform = "Xbox, PC", release_date = "2021-12-08", developer = "343 Industries", publisher = "Xbox Game Studios", rating = "M", description = "The legendary Halo series returns with the most expansive Master Chief campaign yet.", cover_image_url = "https://upload.wikimedia.org/wikipedia/en/1/14/Halo_Infinite.png"),
                Game(title = "Mass Effect", genre = "Action RPG", platform = "Xbox 360, PC, PlayStation 3", release_date = "2007-11-20", developer = "BioWare", publisher = "Microsoft Game Studios, Electronic Arts", rating = "M", description = "Mass Effect is a sci-fi action role-playing game where players assume the role of Commander Shepard, leading a team across the galaxy to stop an ancient threat known as the Reapers.", cover_image_url = "https://upload.wikimedia.org/wikipedia/en/8/80/MassEffectCover.png"),
                Game(title = "The Witcher 3: Wild Hunt", genre = "Action RPG", platform = "PC, PlayStation 4, Xbox One, Nintendo Switch", release_date = "2015-05-19", developer = "CD Projekt Red", publisher = "CD Projekt", rating = "M", description = "The Witcher 3: Wild Hunt is an open-world action RPG that follows Geralt of Rivia, a monster hunter, as he searches for his adopted daughter in a war-torn world filled with dangerous creatures and political intrigue.", cover_image_url = "https://upload.wikimedia.org/wikipedia/en/0/0c/Witcher_3_cover_art.jpg")
          ])
            session.commit()
    yield

app = FastAPI(root_path="/api/v1", lifespan=lifespan)

data : Any = [  # List of the games
    {
        "games_id": 1,
        "title": "Halo Infitinite",
        "genre": "FPS",
        "platform": "Xbox, PC",
        "release_date": "2021-12-08",
        "developer": "343 Industries",
        "publisher": "Xbox Game Studios",
        "rating": "M",
        "description": "The legendary Halo series returns with the most expansive Master Chief campaign yet.",
        "cover_image_url": "https://upload.wikimedia.org/wikipedia/en/1/14/Halo_Infinite.png"

    },
    {
        "games_id": 2,
        "title": "Mass Effect",
        "genre": "Action RPG",
        "platform": "Xbox 360, PC, PlayStation 3",
        "release_date": "2007-11-20",
        "developer": "BioWare",
        "publisher": "Microsoft Game Studios, Electronic Arts",
        "rating": "M",
        "description": "Mass Effect is a sci-fi action role-playing game where players assume the role of Commander Shepard, leading a team across the galaxy to stop an ancient threat known as the Reapers.",
        "cover_image_url": "https://upload.wikimedia.org/wikipedia/en/8/80/MassEffectCover.png"
    },
    {
        "games_id": 3,
        "title": "The Witcher 3: Wild Hunt",
        "genre": "Action RPG",
        "platform": "PC, PlayStation 4, Xbox One, Nintendo Switch",
        "release_date": "2015-05-19",
        "developer": "CD Projekt Red",
        "publisher": "CD Projekt",
        "rating": "M",
        "description": "The Witcher 3: Wild Hunt is an open-world action RPG that follows Geralt of Rivia, a monster hunter, as he searches for his adopted daughter in a war-torn world filled with dangerous creatures and political intrigue.",
        "cover_image_url": "https://upload.wikimedia.org/wikipedia/en/0/0c/Witcher_3_cover_art.jpg"
    },
]

"""
Games
- game_id
- title
- genre
- platform
- release_date
- developer
- publisher
- rating
- description
- cover_image_url
"""

T = TypeVar("T")

class ApiResponse(BaseModel, Generic[T]):
    data: T

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


class PaginatedResponse(BaseModel, Generic[T]):
    data: T
    next: Optional[str]
    previous: Optional[str]
    
@app.get("/games", response_model = PaginatedResponse[list[Game]])
async def read_games(request: Request, session: SessionDep, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1)):
    limit = page_size
    offset = (page-1)*limit
    data = session.exec(select(Game).order_by(Game.games_id).offset(offset).limit(limit)).all()

    base_url = str(request.url).split('?')[0]

    next_url = f"{base_url}?page={page+1}&page_size={limit}"

    if page > 1:
        prev_url = f"{base_url}?page={page-1}&page_size={limit}"
    else:
        prev_url = None

    return {
        "next": next_url,
        "previous": prev_url,
        "data": data
    }

@app.get("/games/{id}", response_model=ApiResponse[Game])
async def read_game(id: int, session: SessionDep):
    data = session.get(Game, id)
    if not data:
        raise HTTPException(status_code=404, detail="Game not found")
    return {"data": data}

@app.post("/games", response_model=ApiResponse[Game], status_code=201)
async def create_game(game: GameCreate, session: SessionDep):
    db_game = Game.model_validate(game)
    session.add(db_game)
    session.commit()
    session.refresh(db_game)
    return {"data": db_game}
                      
@app.put("/games/{id}", response_model=ApiResponse[Game])
async def update_game(id: int, game: GameCreate, session: SessionDep):
    data = session.get(Game, id)
    if not data:
        raise HTTPException(status_code=404, detail="Game not found")
    for field, value in game.dict().items():
        setattr(data, field, value)

    session.commit()
    session.refresh(data)
    return {"data": data}

@app.delete("/games/{id}", status_code=204)
async def delete_game(id: int, session: SessionDep):
    data = session.get(Game, id)
    if not data:
        raise HTTPException(status_code=404, detail="Game not found")
    session.delete(data)
    session.commit()
