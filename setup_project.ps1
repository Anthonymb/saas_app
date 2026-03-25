# ============================================================
#  FastAPI SaaS Project Setup Script
#  Paste this entire script into your VS Code terminal
# ============================================================

Write-Host "Creating project structure..." -ForegroundColor Cyan

# ── Folders ──────────────────────────────────────────────────
New-Item -ItemType Directory -Force -Path "app/api/v1/endpoints" | Out-Null
New-Item -ItemType Directory -Force -Path "app/core"             | Out-Null
New-Item -ItemType Directory -Force -Path "app/db"               | Out-Null
New-Item -ItemType Directory -Force -Path "app/models"           | Out-Null
New-Item -ItemType Directory -Force -Path "app/schemas"          | Out-Null
New-Item -ItemType Directory -Force -Path "app/services"         | Out-Null
New-Item -ItemType Directory -Force -Path "app/utils"            | Out-Null
New-Item -ItemType Directory -Force -Path "alembic/versions"     | Out-Null
New-Item -ItemType Directory -Force -Path "tests/unit"           | Out-Null
New-Item -ItemType Directory -Force -Path "tests/integration"    | Out-Null
New-Item -ItemType Directory -Force -Path ".vscode"              | Out-Null

Write-Host "Creating files..." -ForegroundColor Cyan

# ── requirements.txt ─────────────────────────────────────────
@'
fastapi==0.111.0
uvicorn[standard]==0.29.0
sqlalchemy==2.0.30
alembic==1.13.1
asyncpg==0.29.0
psycopg2-binary==2.9.9
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.9
pydantic==2.7.1
pydantic-settings==2.2.1
python-dotenv==1.0.1
httpx==0.27.0
email-validator==2.1.1
pytest==8.2.0
pytest-asyncio==0.23.6
'@ | Set-Content "requirements.txt"

# ── .env.example ─────────────────────────────────────────────
@'
APP_NAME="My SaaS App"
APP_ENV=development
DEBUG=true
SECRET_KEY=change-me-to-a-long-random-secret-at-least-32-chars

POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=saas_user
POSTGRES_PASSWORD=yourpassword
POSTGRES_DB=saas_db

ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
ALGORITHM=HS256

ALLOWED_ORIGINS=http://localhost:3000
'@ | Set-Content ".env.example"

# ── .gitignore ────────────────────────────────────────────────
@'
.env
.env.*
!.env.example
__pycache__/
*.py[cod]
.venv/
venv/
.pytest_cache/
.coverage
'@ | Set-Content ".gitignore"

# ── main.py (entry point) ─────────────────────────────────────
@'
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
'@ | Set-Content "main.py"

# ── app/__init__.py ───────────────────────────────────────────
"" | Set-Content "app/__init__.py"

# ── app/main.py ───────────────────────────────────────────────
@'
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.v1.router import api_router
from app.core.config import settings
from app.db.session import engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"Starting {settings.app_name} [{settings.app_env}]")
    yield
    await engine.dispose()
    print("Shutdown complete")

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )
    app.include_router(api_router)
    return app

app = create_app()
'@ | Set-Content "app/main.py"

# ── app/core/config.py ────────────────────────────────────────
@'
from functools import lru_cache
from typing import List
from pydantic import computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    app_name: str = "My SaaS App"
    app_env: str = "development"
    debug: bool = False
    secret_key: str = "default-secret-key"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_db: str = "saas_db"

    @computed_field
    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    @computed_field
    @property
    def sync_database_url(self) -> str:
        return f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    allowed_origins: List[str] = ["http://localhost:3000"]

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_origins(cls, v):
        if isinstance(v, str):
            return [o.strip() for o in v.split(",")]
        return v

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
'@ | Set-Content "app/core/config.py"

# ── app/core/security.py ──────────────────────────────────────
@'
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from jose import jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def _create_token(data: dict, expires_delta: timedelta) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + expires_delta
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)

def create_access_token(subject: str) -> str:
    return _create_token({"sub": str(subject), "type": "access"},
                         timedelta(minutes=settings.access_token_expire_minutes))

def create_refresh_token(subject: str) -> str:
    return _create_token({"sub": str(subject), "type": "refresh"},
                         timedelta(days=settings.refresh_token_expire_days))

def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
'@ | Set-Content "app/core/security.py"

# ── app/core/dependencies.py ──────────────────────────────────
@'
from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import decode_token
from app.db.session import AsyncSessionLocal
from app.schemas.token import TokenPayload

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> int:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise credentials_exc
        token_data = TokenPayload(**payload)
    except (JWTError, ValueError):
        raise credentials_exc
    return int(token_data.sub)
'@ | Set-Content "app/core/dependencies.py"

"" | Set-Content "app/core/__init__.py"

# ── app/db/session.py ─────────────────────────────────────────
@'
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.config import settings

engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.debug,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)
'@ | Set-Content "app/db/session.py"

# ── app/db/base.py ────────────────────────────────────────────
@'
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

from app.models.user import User  # noqa
'@ | Set-Content "app/db/base.py"

"" | Set-Content "app/db/__init__.py"

# ── app/models/base.py ────────────────────────────────────────
@'
from datetime import datetime
from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
'@ | Set-Content "app/models/base.py"

# ── app/models/user.py ────────────────────────────────────────
@'
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.models.base import TimestampMixin

class User(TimestampMixin, Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
'@ | Set-Content "app/models/user.py"

"" | Set-Content "app/models/__init__.py"

# ── app/schemas/user.py ───────────────────────────────────────
@'
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    email: EmailStr
    full_name: str

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None

class UserRead(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    model_config = {"from_attributes": True}
'@ | Set-Content "app/schemas/user.py"

# ── app/schemas/token.py ──────────────────────────────────────
@'
from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: str
    type: str
'@ | Set-Content "app/schemas/token.py"

# ── app/schemas/common.py ─────────────────────────────────────
@'
from typing import Generic, List, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class MessageResponse(BaseModel):
    message: str

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int
'@ | Set-Content "app/schemas/common.py"

"" | Set-Content "app/schemas/__init__.py"

# ── app/services/user.py ──────────────────────────────────────
@'
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

class UserService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def create(self, data: UserCreate) -> User:
        user = User(
            email=data.email,
            full_name=data.full_name,
            hashed_password=hash_password(data.password),
        )
        self.db.add(user)
        await self.db.flush()
        return user

    async def update(self, user: User, data: UserUpdate) -> User:
        update_data = data.model_dump(exclude_unset=True)
        if "password" in update_data:
            update_data["hashed_password"] = hash_password(update_data.pop("password"))
        for field, value in update_data.items():
            setattr(user, field, value)
        await self.db.flush()
        return user

    async def delete(self, user: User) -> None:
        await self.db.delete(user)
        await self.db.flush()
'@ | Set-Content "app/services/user.py"

# ── app/services/auth.py ──────────────────────────────────────
@'
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import create_access_token, create_refresh_token, verify_password
from app.models.user import User
from app.schemas.token import Token
from app.services.user import UserService

class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.user_svc = UserService(db)

    async def authenticate(self, email: str, password: str) -> Optional[User]:
        user = await self.user_svc.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        return user

    @staticmethod
    def issue_tokens(user: User) -> Token:
        return Token(
            access_token=create_access_token(subject=user.id),
            refresh_token=create_refresh_token(subject=user.id),
        )
'@ | Set-Content "app/services/auth.py"

"" | Set-Content "app/services/__init__.py"

# ── app/api/v1/endpoints/auth.py ──────────────────────────────
@'
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserRead
from app.services.auth import AuthService
from app.services.user import UserService

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    svc = UserService(db)
    if await svc.get_by_email(payload.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    return await svc.create(payload)

@router.post("/login", response_model=Token)
async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    auth_svc = AuthService(db)
    user = await auth_svc.authenticate(email=form.username, password=form.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return auth_svc.issue_tokens(user)
'@ | Set-Content "app/api/v1/endpoints/auth.py"

# ── app/api/v1/endpoints/users.py ────────────────────────────
@'
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_user_id, get_db
from app.schemas.user import UserRead, UserUpdate
from app.services.user import UserService

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=UserRead)
async def get_me(user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    svc = UserService(db)
    user = await svc.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.patch("/me", response_model=UserRead)
async def update_me(payload: UserUpdate, user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    svc = UserService(db)
    user = await svc.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.email and payload.email != user.email:
        if await svc.get_by_email(payload.email):
            raise HTTPException(status_code=400, detail="Email already in use")
    return await svc.update(user, payload)

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    svc = UserService(db)
    user = await svc.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await svc.delete(user)
'@ | Set-Content "app/api/v1/endpoints/users.py"

# ── app/api/v1/endpoints/health.py ───────────────────────────
@'
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("")
async def health_check():
    return {"status": "ok"}

@router.get("/db")
async def db_health(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": str(e)}
'@ | Set-Content "app/api/v1/endpoints/health.py"

"" | Set-Content "app/api/v1/endpoints/__init__.py"

# ── app/api/v1/router.py ─────────────────────────────────────
@'
from fastapi import APIRouter
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.users import router as users_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(users_router)
'@ | Set-Content "app/api/v1/router.py"

"" | Set-Content "app/api/v1/__init__.py"
"" | Set-Content "app/api/__init__.py"

# ── app/utils/pagination.py ───────────────────────────────────
@'
import math
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

async def paginate(db: AsyncSession, query: Select, page: int = 1, page_size: int = 20, response_schema=None) -> dict:
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()
    offset = (page - 1) * page_size
    rows = (await db.execute(query.offset(offset).limit(page_size))).scalars().all()
    items = [response_schema.model_validate(r) for r in rows] if response_schema else rows
    return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": math.ceil(total / page_size) if total else 1}
'@ | Set-Content "app/utils/pagination.py"

"" | Set-Content "app/utils/__init__.py"

# ── alembic/env.py ────────────────────────────────────────────
@'
import asyncio
from logging.config import fileConfig
from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from app.core.config import settings
from app.db.base import Base

target_metadata = Base.metadata
config.set_main_option("sqlalchemy.url", settings.sync_database_url)

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    connectable = async_engine_from_config(config.get_section(config.config_ini_section, {}), prefix="sqlalchemy.", poolclass=pool.NullPool)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()

def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
'@ | Set-Content "alembic/env.py"

# ── alembic/script.py.mako ────────────────────────────────────
@'
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}

def upgrade() -> None:
    ${upgrades if upgrades else "pass"}

def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
'@ | Set-Content "alembic/script.py.mako"

"" | Set-Content "alembic/__init__.py"
"" | Set-Content "alembic/versions/.gitkeep"

# ── alembic.ini ───────────────────────────────────────────────
@'
[alembic]
script_location = alembic
prepend_sys_path = .

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
'@ | Set-Content "alembic.ini"

# ── tests ─────────────────────────────────────────────────────
"" | Set-Content "tests/__init__.py"
"" | Set-Content "tests/unit/__init__.py"
"" | Set-Content "tests/integration/__init__.py"

# ── .vscode/launch.json ───────────────────────────────────────
@'
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Run FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["app.main:app", "--reload", "--port", "8000"],
      "env": { "PYTHONPATH": "${workspaceFolder}" }
    }
  ]
}
'@ | Set-Content ".vscode/launch.json"

Write-Host ""
Write-Host "Project created successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Files created:" -ForegroundColor Yellow
Get-ChildItem -Recurse -File | Where-Object { $_.FullName -notlike "*\.venv\*" } | ForEach-Object { Write-Host "  $($_.FullName.Replace((Get-Location).Path + '\', ''))" }
Write-Host ""
Write-Host "Next step: run the following commands one by one:" -ForegroundColor Cyan
Write-Host "  1. python -m venv .venv"
Write-Host "  2. .venv\Scripts\Activate.ps1"
Write-Host "  3. pip install -r requirements.txt"
