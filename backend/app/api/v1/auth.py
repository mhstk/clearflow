"""
Authentication endpoints for user signup, login, and Google OAuth.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.core.security import verify_password, get_password_hash, create_access_token
from app.models.user import User
from app.schemas.auth import (
    SignupRequest,
    LoginRequest,
    GoogleAuthRequest,
    AuthResponse,
    UserAuthResponse,
    Token,
    GoogleAuthUrlResponse
)
from app.services.google_oauth import (
    get_google_auth_url,
    exchange_code_for_tokens,
    get_google_user_info
)

router = APIRouter()


@router.post("/signup", response_model=AuthResponse)
async def signup(
    data: SignupRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new user with email and password.

    - **email**: Valid email address (must be unique)
    - **password**: User password
    - **name**: Optional display name
    """
    # Check if email already exists
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    user = User(
        email=data.email,
        hashed_password=get_password_hash(data.password),
        name=data.name,
        is_active=True,
        is_demo=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Generate JWT token
    token = create_access_token(user.id)

    return AuthResponse(
        user=UserAuthResponse.model_validate(user),
        token=Token(access_token=token)
    )


@router.post("/login", response_model=AuthResponse)
async def login(
    data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login with email and password.

    Returns JWT token on success.
    """
    # Find user by email
    user = db.query(User).filter(User.email == data.email).first()

    if not user or not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Verify password
    if not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is disabled"
        )

    # Generate JWT token
    token = create_access_token(user.id)

    return AuthResponse(
        user=UserAuthResponse.model_validate(user),
        token=Token(access_token=token)
    )


@router.post("/google", response_model=AuthResponse)
async def google_auth(
    data: GoogleAuthRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate with Google OAuth.

    - **code**: Authorization code from Google OAuth redirect
    """
    # Exchange code for tokens
    tokens = await exchange_code_for_tokens(data.code)
    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to exchange authorization code"
        )

    # Get user info from Google
    google_user = await get_google_user_info(tokens["access_token"])
    if not google_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to get user info from Google"
        )

    google_id = google_user["id"]
    email = google_user["email"]

    # Find existing user by Google ID
    user = db.query(User).filter(User.google_id == google_id).first()

    if not user:
        # Check if email exists (link accounts)
        user = db.query(User).filter(User.email == email).first()

        if user:
            # Link Google account to existing user
            user.google_id = google_id
            if not user.name and google_user.get("name"):
                user.name = google_user["name"]
            if not user.avatar_url and google_user.get("picture"):
                user.avatar_url = google_user["picture"]
        else:
            # Create new user
            user = User(
                email=email,
                google_id=google_id,
                name=google_user.get("name"),
                avatar_url=google_user.get("picture"),
                is_active=True,
                is_demo=False
            )
            db.add(user)

        db.commit()
        db.refresh(user)

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is disabled"
        )

    # Generate JWT token
    token = create_access_token(user.id)

    return AuthResponse(
        user=UserAuthResponse.model_validate(user),
        token=Token(access_token=token)
    )


@router.get("/google/url", response_model=GoogleAuthUrlResponse)
async def get_google_oauth_url():
    """
    Get Google OAuth authorization URL.

    Redirect user to this URL to initiate Google login.
    """
    url = get_google_auth_url()

    if not url:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth not configured"
        )

    return GoogleAuthUrlResponse(url=url)


@router.get("/me", response_model=UserAuthResponse)
async def get_me(
    user: User = Depends(get_current_user)
):
    """
    Get current authenticated user's profile.

    Requires valid JWT token in Authorization header.
    """
    return UserAuthResponse.model_validate(user)
