from sqlmodel import SQLModel, create_engine, Session

# SQLite file in your project root
DATABASE_URL = "sqlite:///./database.db"

# check_same_thread=False lets FastAPI use the same connection across threads
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)

def get_session():
    """FastAPI dependency that yields a DB session per request."""
    with Session(engine) as session:
        yield session
