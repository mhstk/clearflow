from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect
import logging

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.db.session import engine, SessionLocal
from app.db.base import Base
from app.api.v1 import accounts, transactions, ai, dashboard, recurring, auth, categories
from app.models.user import User

# Setup logging first
setup_logging()

# Create database tables
Base.metadata.create_all(bind=engine)


def run_migrations():
    """Run any needed database migrations on startup."""
    logger = logging.getLogger(__name__)

    with engine.connect() as conn:
        inspector = inspect(engine)

        # Check if is_expense column exists in transactions table
        tx_columns = [col['name'] for col in inspector.get_columns('transactions')]

        if 'is_expense' not in tx_columns:
            logger.info("Adding is_expense column to transactions table...")

            # Add the column with default value
            conn.execute(text(
                "ALTER TABLE transactions ADD COLUMN is_expense BOOLEAN DEFAULT 1 NOT NULL"
            ))

            # Update existing rows based on amount
            conn.execute(text(
                "UPDATE transactions SET is_expense = (amount < 0)"
            ))

            # Create index for faster queries
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_transactions_is_expense ON transactions(is_expense)"
            ))

            # Create composite index
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_transactions_user_expense_date "
                "ON transactions(user_id, is_expense, date)"
            ))

            conn.commit()
            logger.info("Migration complete: is_expense column added and populated")

        # Auth columns migration for users table
        user_columns = [col['name'] for col in inspector.get_columns('users')]

        if 'hashed_password' not in user_columns:
            logger.info("Adding authentication columns to users table...")

            # Add auth columns
            conn.execute(text("ALTER TABLE users ADD COLUMN hashed_password VARCHAR"))
            conn.execute(text("ALTER TABLE users ADD COLUMN name VARCHAR"))
            conn.execute(text("ALTER TABLE users ADD COLUMN avatar_url VARCHAR"))
            conn.execute(text("ALTER TABLE users ADD COLUMN google_id VARCHAR"))
            conn.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1"))
            conn.execute(text("ALTER TABLE users ADD COLUMN is_demo BOOLEAN DEFAULT 0"))
            conn.execute(text("ALTER TABLE users ADD COLUMN updated_at DATETIME"))

            # Mark user 1 as demo account
            conn.execute(text("UPDATE users SET is_demo = 1 WHERE id = 1"))

            # Create index for google_id
            conn.execute(text(
                "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_google_id ON users(google_id)"
            ))

            conn.commit()
            logger.info("Migration complete: authentication columns added to users table")


# Run migrations after table creation
run_migrations()

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS - hardcode production URLs + env var origins
cors_origins = [
    "https://clearflow-front.vercel.app",  # Production frontend
    "http://localhost:5173",                # Local development
    "http://localhost:3000",
]
# Add any additional origins from env var
cors_origins.extend(settings.cors_origins_list)
# Remove duplicates
cors_origins = list(set(cors_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    accounts.router,
    prefix=f"{settings.API_V1_PREFIX}/accounts",
    tags=["accounts"]
)
app.include_router(
    transactions.router,
    prefix=f"{settings.API_V1_PREFIX}/transactions",
    tags=["transactions"]
)
app.include_router(
    ai.router,
    prefix=f"{settings.API_V1_PREFIX}/ai",
    tags=["ai"]
)
app.include_router(
    dashboard.router,
    prefix=f"{settings.API_V1_PREFIX}/dashboard",
    tags=["dashboard"]
)
app.include_router(
    recurring.router,
    prefix=f"{settings.API_V1_PREFIX}/recurring",
    tags=["recurring"]
)
app.include_router(
    auth.router,
    prefix=f"{settings.API_V1_PREFIX}/auth",
    tags=["authentication"]
)
app.include_router(
    categories.router,
    prefix=f"{settings.API_V1_PREFIX}/categories",
    tags=["categories"]
)


@app.on_event("startup")
def startup_event():
    """Initialize demo user on startup"""
    logger = logging.getLogger(__name__)
    db = SessionLocal()
    try:
        # Check if demo user exists
        user = db.query(User).filter(User.id == settings.DEMO_USER_ID).first()
        if not user:
            # Create demo user
            user = User(
                id=settings.DEMO_USER_ID,
                email="demo@example.com",
                name="Demo User",
                is_demo=True,
                is_active=True
            )
            db.add(user)
            db.commit()
            logger.info(f"Created demo user with ID {settings.DEMO_USER_ID}")
        elif not user.is_demo:
            # Mark existing user as demo
            user.is_demo = True
            if not user.email:
                user.email = "demo@example.com"
            if not user.name:
                user.name = "Demo User"
            db.commit()
            logger.info(f"Marked user {settings.DEMO_USER_ID} as demo user")
    finally:
        db.close()


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "Personal Finance Intelligence API",
        "docs": "/docs",
        "version": "1.0.0"
    }


@app.get("/health")
def health():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
