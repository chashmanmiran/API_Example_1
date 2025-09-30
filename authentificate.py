# security.py
from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel
from passlib.context import CryptContext
from sqlmodel import SQLModel, Field, Session, select
from database import get_session



# --- Config (keep same values you used before) ---
SECRET_KEY = "1ff29d59b8dd1e0fa514767b6d78432631a90d6c1ac2a86185a8232fc474e25f"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# bcrypt_sha256 avoids bcrypt's 72-byte limit
pwd_context = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")

# Keep the token URL exactly "/token" so you don't have to change clients
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

# --- In-memory user store: start empty to force registration ---
db_users = {} 

# --- Pydantic models ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None

class UserInDB(User):
    hashed_password: str


#Indexed usernames
class UserAccount(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: Optional[str] = Field(index=True, unique=True, nullable=True)
    full_name: Optional[str] = Field(default=None, nullable=True)
    hashed_password: str
    disabled: bool = False

# --- Hash helpers ---
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# --- User lookup/auth ---
def get_user(username: str) -> Optional[UserInDB]:
    data = db_users.get(username)
    return UserInDB(**data) if data else None

def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

# --- JWT helpers & dependencies ---
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()  # IMPORTANT: call copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise credentials_exc
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exc

    user = get_user(token_data.username)  # type: ignore[arg-type]
    if user is None:
        raise credentials_exc
    return user

async def get_current_active_user(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# --- Auth router (/register, /token, /users/me) ---
router = APIRouter(tags=["auth"])

# ⬇️ minimal addition: registration endpoint (create profile first)
class RegisterForm(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    full_name: Optional[str] = None

@router.post("/register", status_code=201)
def register_user(form: RegisterForm):
    if form.username in db_users:
        raise HTTPException(status_code=409, detail="Username already exists")
    if len(form.password) < 6:
        raise HTTPException(status_code=400, detail="Password too short (min 6)")
    db_users[form.username] = {
        "username": form.username,
        "full_name": form.full_name,
        "email": form.email,
        "hashed_password": get_password_hash(form.password),
        "disabled": False,
    }
    return {"message": "User created. Please log in at /token."}

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

