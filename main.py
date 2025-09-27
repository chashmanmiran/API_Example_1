from random import randint
from fastapi import FastAPI, HTTPException, Request, Response
from typing import Any
from sqlalchemy import create_engine

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

app = FastAPI(root_path="/api/v1")

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

@app.get("/games") # Get of the games
async def Root():
    return {"games": data}

@app.get("/games/{id}")
async def read_games(id: int):
    for games in data:
        if games.get("games_id") == id:
            return {"game": games}
    raise HTTPException(status_code=404)
    
@app.post("/games", status_code=201)
async def create_games(body: dict[str, Any]):
    new = {
        "games_id": randint(1, 1000),
        "title": body.get("title"),
        "genre": body.get ("genre"),
        "platform": body.get("platform"),
        "release_date": body.get("release_date"),
        "developer": body.get("developer"),
        "publisher": body.get("publisher"),
        "rating": body.get("rating"),
        "description": body.get("description"),
        "cover_image_url": body.get("cover_image_url")
    }

    data.append(new)
    return {"games": new}

@app.put("/games/{id}")
async def update_games(id: int, body: dict[str, Any]):
    for index, games in enumerate(data):
        if games.get("games_id") == id:
                updated: Any = {
                    "games_id": randint(100, 1000),
                    "title": body.get("title"),
                    "genre": body.get("genre"),
                    "platform": body.get("platform"),
                    "release_date": body.get("release_date"),
                    "developer": body.get("developer"),
                    "publisher": body.get("publisher"),
                    "rating": body.get("rating"),
                    "description": body.get("description"),
                    "cover_image_url": body.get("cover_image_url")
                }
                data[index] = updated
                return {"games": updated}
    raise HTTPException(status_code=404)

@app.delete("/games/{id}")
async def delete_games(id: int, body: dict[str, Any]):
    for index, games in enumerate(data):
       if games.get("games_id") == id:
           data.pop(index)
           return Response(status_code=204)
    raise HTTPException(status_code=404)