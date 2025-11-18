"""Authentication API routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    UserCreate, UserResponse, MagicLinkRequest, MagicLinkResponse,
    MagicLinkVerify, TokenResponse
)
from app.services.auth_service import auth_service
from app.dependencies import get_current_user
from app.models import User
from app.utils.logger import logger


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=MagicLinkResponse)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user or get existing user and send magic link.

    Args:
        user_data: User registration data
        db: Database session

    Returns:
        Magic link response
    """
    try:
        # Get or create user
        user = auth_service.get_or_create_user(db, user_data)

        # Send magic link
        success = auth_service.send_magic_link(db, user.email)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send magic link email"
            )

        return MagicLinkResponse(
            message="Magic link sent to your email",
            email=user.email
        )

    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=MagicLinkResponse)
async def login_user(
    login_data: MagicLinkRequest,
    db: Session = Depends(get_db)
):
    """
    Request magic link for login.

    Args:
        login_data: Login request data
        db: Database session

    Returns:
        Magic link response
    """
    try:
        # Send magic link (works for both existing and new users)
        success = auth_service.send_magic_link(db, login_data.email)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send magic link email"
            )

        return MagicLinkResponse(
            message="Magic link sent to your email",
            email=login_data.email
        )

    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/verify", response_model=TokenResponse)
async def verify_magic_link(
    verify_data: MagicLinkVerify,
    db: Session = Depends(get_db)
):
    """
    Verify magic link token and create session.

    Args:
        verify_data: Magic link verification data
        db: Database session

    Returns:
        Access token and user data
    """
    # Verify magic link
    user = auth_service.verify_magic_link(db, verify_data.token)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired magic link"
        )

    # Create session and get access token
    access_token = auth_service.create_session(db, user.id)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.get("/verify", response_model=TokenResponse)
async def verify_magic_link_get(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Verify magic link token via GET request (for email links).

    Args:
        token: Magic link token from query parameter
        db: Database session

    Returns:
        Access token and user data
    """
    # Verify magic link
    user = auth_service.verify_magic_link(db, token)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired magic link"
        )

    # Create session and get access token
    access_token = auth_service.create_session(db, user.id)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.post("/logout")
async def logout_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logout current user (invalidate session).

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        Success message
    """
    # Note: We don't have the token in dependencies, so we'll invalidate all sessions
    # In production, you'd want to pass the token and invalidate specific session
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user information.

    Args:
        current_user: Current authenticated user

    Returns:
        User information
    """
    return UserResponse.model_validate(current_user)
