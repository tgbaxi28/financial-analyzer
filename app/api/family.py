"""Family member management API routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database import get_db
from app.schemas import FamilyMemberCreate, FamilyMemberUpdate, FamilyMemberResponse
from app.models import User, FamilyMember
from app.dependencies import get_current_user
from app.utils.logger import logger


router = APIRouter(prefix="/family", tags=["Family Members"])


@router.post("", response_model=FamilyMemberResponse, status_code=status.HTTP_201_CREATED)
async def create_family_member(
    family_member_data: FamilyMemberCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new family member for the current user.

    Args:
        family_member_data: Family member creation data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Created family member
    """
    try:
        family_member = FamilyMember(
            user_id=current_user.id,
            first_name=family_member_data.first_name,
            last_name=family_member_data.last_name,
            relationship=family_member_data.relationship
        )

        db.add(family_member)
        db.commit()
        db.refresh(family_member)

        logger.info(f"Family member created: {family_member.id} for user {current_user.id}")

        return FamilyMemberResponse.model_validate(family_member)

    except Exception as e:
        logger.error(f"Error creating family member: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create family member"
        )


@router.get("", response_model=List[FamilyMemberResponse])
async def list_family_members(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    include_inactive: bool = False
):
    """
    List all family members for the current user.

    Args:
        current_user: Current authenticated user
        db: Database session
        include_inactive: Include inactive family members

    Returns:
        List of family members
    """
    query = db.query(FamilyMember).filter(FamilyMember.user_id == current_user.id)

    if not include_inactive:
        query = query.filter(FamilyMember.is_active == True)

    family_members = query.all()

    return [FamilyMemberResponse.model_validate(fm) for fm in family_members]


@router.get("/{family_member_id}", response_model=FamilyMemberResponse)
async def get_family_member(
    family_member_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific family member by ID.

    Args:
        family_member_id: Family member ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Family member data

    Raises:
        HTTPException: If family member not found or unauthorized
    """
    family_member = db.query(FamilyMember).filter(
        FamilyMember.id == family_member_id,
        FamilyMember.user_id == current_user.id
    ).first()

    if not family_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Family member not found"
        )

    return FamilyMemberResponse.model_validate(family_member)


@router.patch("/{family_member_id}", response_model=FamilyMemberResponse)
async def update_family_member(
    family_member_id: UUID,
    update_data: FamilyMemberUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a family member.

    Args:
        family_member_id: Family member ID
        update_data: Update data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated family member

    Raises:
        HTTPException: If family member not found or unauthorized
    """
    family_member = db.query(FamilyMember).filter(
        FamilyMember.id == family_member_id,
        FamilyMember.user_id == current_user.id
    ).first()

    if not family_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Family member not found"
        )

    try:
        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(family_member, field, value)

        db.commit()
        db.refresh(family_member)

        logger.info(f"Family member updated: {family_member_id}")

        return FamilyMemberResponse.model_validate(family_member)

    except Exception as e:
        logger.error(f"Error updating family member: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update family member"
        )


@router.delete("/{family_member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_family_member(
    family_member_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    hard_delete: bool = False
):
    """
    Delete a family member (soft delete by default).

    Args:
        family_member_id: Family member ID
        current_user: Current authenticated user
        db: Database session
        hard_delete: If True, permanently delete; otherwise soft delete

    Raises:
        HTTPException: If family member not found or unauthorized
    """
    family_member = db.query(FamilyMember).filter(
        FamilyMember.id == family_member_id,
        FamilyMember.user_id == current_user.id
    ).first()

    if not family_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Family member not found"
        )

    try:
        if hard_delete:
            db.delete(family_member)
            logger.info(f"Family member permanently deleted: {family_member_id}")
        else:
            family_member.is_active = False
            logger.info(f"Family member soft deleted: {family_member_id}")

        db.commit()

    except Exception as e:
        logger.error(f"Error deleting family member: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete family member"
        )
