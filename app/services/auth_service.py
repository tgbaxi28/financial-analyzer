"""Authentication service for user management and magic links."""
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.models import User, MagicLinkToken, Session as SessionModel
from app.schemas import UserCreate
from app.utils.security import generate_magic_link_token, create_access_token
from app.services.email_service import email_service
from app.config import settings
from app.utils.logger import logger


class AuthService:
    """Service for authentication operations."""

    def get_or_create_user(self, db: Session, user_data: UserCreate) -> User:
        """
        Get existing user or create new one.

        Args:
            db: Database session
            user_data: User creation data

        Returns:
            User object
        """
        # Check if user exists
        user = db.query(User).filter(User.email == user_data.email).first()

        if user:
            logger.info(f"Existing user found: {user_data.email}")
            return user

        # Create new user
        user = User(
            email=user_data.email,
            first_name=user_data.first_name,
            last_name=user_data.last_name
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        logger.info(f"New user created: {user_data.email}")

        # Send welcome email
        email_service.send_welcome_email(user.email, user.first_name)

        return user

    def create_magic_link(self, db: Session, email: str) -> Optional[str]:
        """
        Create magic link for user authentication.

        Args:
            db: Database session
            email: User's email address

        Returns:
            Magic link URL or None if failed
        """
        # Generate token
        token = generate_magic_link_token()

        # Calculate expiration
        expires_at = datetime.utcnow() + timedelta(minutes=settings.MAGIC_LINK_EXPIRE_MINUTES)

        # Create magic link token
        magic_link_token = MagicLinkToken(
            email=email,
            token=token,
            expires_at=expires_at
        )

        db.add(magic_link_token)
        db.commit()

        # Construct magic link URL
        magic_link = f"{settings.APP_URL}/auth/verify?token={token}"

        logger.info(f"Magic link created for {email}")

        return magic_link

    def send_magic_link(self, db: Session, email: str) -> bool:
        """
        Send magic link email to user.

        Args:
            db: Database session
            email: User's email address

        Returns:
            True if sent successfully, False otherwise
        """
        magic_link = self.create_magic_link(db, email)

        if not magic_link:
            return False

        # Send email
        success = email_service.send_magic_link(email, magic_link)

        if success:
            logger.info(f"Magic link sent to {email}")
        else:
            logger.error(f"Failed to send magic link to {email}")

        return success

    def verify_magic_link(self, db: Session, token: str) -> Optional[User]:
        """
        Verify magic link token and return user.

        Args:
            db: Database session
            token: Magic link token

        Returns:
            User object if valid, None otherwise
        """
        # Find magic link token
        magic_link = db.query(MagicLinkToken).filter(
            MagicLinkToken.token == token,
            MagicLinkToken.is_used == False
        ).first()

        if not magic_link:
            logger.warning(f"Invalid or already used magic link token")
            return None

        # Check if expired
        if magic_link.expires_at < datetime.utcnow():
            logger.warning(f"Expired magic link token for {magic_link.email}")
            return None

        # Mark as used
        magic_link.is_used = True
        magic_link.used_at = datetime.utcnow()
        db.commit()

        # Get or create user
        user = db.query(User).filter(User.email == magic_link.email).first()

        if not user:
            logger.error(f"User not found for email {magic_link.email}")
            return None

        logger.info(f"Magic link verified for {user.email}")

        return user

    def create_session(self, db: Session, user_id: UUID) -> str:
        """
        Create session for user and return access token.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            JWT access token
        """
        # Create JWT token
        token_data = {"sub": str(user_id)}
        access_token = create_access_token(token_data)

        # Calculate expiration
        expires_at = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        # Create session
        session = SessionModel(
            user_id=user_id,
            token=access_token,
            expires_at=expires_at
        )

        db.add(session)
        db.commit()

        logger.info(f"Session created for user {user_id}")

        return access_token

    def get_user_from_token(self, db: Session, token: str) -> Optional[User]:
        """
        Get user from access token.

        Args:
            db: Database session
            token: JWT access token

        Returns:
            User object if valid, None otherwise
        """
        from app.utils.security import decode_access_token

        # Decode token
        payload = decode_access_token(token)

        if not payload:
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        # Check if session exists and is active
        session = db.query(SessionModel).filter(
            SessionModel.token == token,
            SessionModel.is_active == True
        ).first()

        if not session:
            return None

        # Check if expired
        if session.expires_at < datetime.utcnow():
            session.is_active = False
            db.commit()
            logger.warning(f"Expired session for user {user_id}")
            return None

        # Update last activity
        session.last_activity = datetime.utcnow()
        db.commit()

        # Get user
        user = db.query(User).filter(User.id == user_id).first()

        return user

    def invalidate_session(self, db: Session, token: str) -> bool:
        """
        Invalidate user session.

        Args:
            db: Database session
            token: JWT access token

        Returns:
            True if invalidated, False otherwise
        """
        session = db.query(SessionModel).filter(
            SessionModel.token == token
        ).first()

        if not session:
            return False

        session.is_active = False
        db.commit()

        logger.info(f"Session invalidated for user {session.user_id}")

        return True


# Global auth service instance
auth_service = AuthService()
