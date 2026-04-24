from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import CaseMember, Document, Message, PatientCase, User
from app.schemas import (
    CaseCreate,
    CaseMemberCreate,
    CaseMemberOut,
    CaseMemberUserOut,
    CaseOut,
    CaseSummaryOut,
)
from app.security import get_current_user

router = APIRouter(prefix="/cases", tags=["Cases"])


async def _get_case_or_404(case_id: int, db: AsyncSession) -> PatientCase:
    case_result = await db.execute(select(PatientCase).where(PatientCase.id == case_id))
    case_obj = case_result.scalar_one_or_none()

    if not case_obj:
        raise HTTPException(status_code=404, detail="Case not found")

    return case_obj


async def _ensure_case_member(case_id: int, user_id: int, db: AsyncSession) -> None:
    current_member = await db.execute(
        select(CaseMember).where(
            CaseMember.case_id == case_id,
            CaseMember.user_id == user_id,
        )
    )

    if not current_member.scalar_one_or_none():
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to access this case",
        )


@router.post("/", response_model=CaseOut, status_code=status.HTTP_201_CREATED)
async def create_case(
    payload: CaseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = await db.execute(
        select(PatientCase).where(PatientCase.patient_code == payload.patient_code)
    )

    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Patient code already exists")
    
    new_case = PatientCase(
        patient_code=payload.patient_code,
        case_title=payload.case_title,
        created_by=current_user.id,
    )

    db.add(new_case)
    await db.commit()
    await db.refresh(new_case)

    #add creator as member of the case
    creator_member = CaseMember(
        case_id=new_case.id,
        user_id=current_user.id,
        member_role="admin",
    )

    db.add(creator_member)
    await db.commit()

    return new_case


@router.get("/", response_model=list[CaseOut])
async def get_my_cases(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    result = await db.execute(
        select(PatientCase)
        .join(CaseMember, CaseMember.case_id == PatientCase.id)
        .where(CaseMember.user_id == current_user.id)
    )

    cases = result.scalars().all()

    return cases


@router.get("/summary", response_model=list[CaseSummaryOut])
async def get_case_summaries(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(PatientCase)
        .join(CaseMember, CaseMember.case_id == PatientCase.id)
        .where(CaseMember.user_id == current_user.id)
    )

    cases = result.scalars().all()
    if not cases:
        return []

    case_ids = [case.id for case in cases]

    latest_ids_result = await db.execute(
        select(
            Message.case_id,
            func.max(Message.id).label("latest_message_id"),
        )
        .where(Message.case_id.in_(case_ids))
        .group_by(Message.case_id)
    )
    latest_ids_by_case = {
        row.case_id: row.latest_message_id
        for row in latest_ids_result.all()
        if row.latest_message_id is not None
    }

    latest_messages_by_case: dict[int, Message] = {}
    if latest_ids_by_case:
        latest_messages_result = await db.execute(
            select(Message).where(Message.id.in_(list(latest_ids_by_case.values())))
        )
        latest_messages_by_case = {
            message.case_id: message for message in latest_messages_result.scalars().all()
        }

    member_counts_result = await db.execute(
        select(
            CaseMember.case_id,
            func.count(CaseMember.id).label("member_count"),
        )
        .where(CaseMember.case_id.in_(case_ids))
        .group_by(CaseMember.case_id)
    )
    member_counts = {
        row.case_id: row.member_count
        for row in member_counts_result.all()
    }

    document_counts_result = await db.execute(
        select(
            Document.case_id,
            func.count(Document.id).label("document_count"),
        )
        .where(Document.case_id.in_(case_ids))
        .group_by(Document.case_id)
    )
    document_counts = {
        row.case_id: row.document_count
        for row in document_counts_result.all()
    }

    summaries: list[CaseSummaryOut] = []
    for case in cases:
        latest_message = latest_messages_by_case.get(case.id)
        summaries.append(
            CaseSummaryOut(
                id=case.id,
                patient_code=case.patient_code,
                case_title=case.case_title,
                status=case.status,
                member_count=member_counts.get(case.id, 0),
                document_count=document_counts.get(case.id, 0),
                created_at=case.created_at,
                updated_at=case.updated_at,
                last_message=latest_message.content if latest_message else None,
                last_message_at=latest_message.sent_at if latest_message else None,
                last_message_sender_id=latest_message.sender_id if latest_message else None,
                last_message_type=latest_message.message_type if latest_message else None,
            )
        )

    return sorted(
        summaries,
        key=lambda item: item.last_message_at or item.updated_at or item.created_at or datetime.min,
        reverse=True,
    )


@router.get("/{case_id}/members", response_model=list[CaseMemberUserOut])
async def get_case_members(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_case_or_404(case_id, db)
    await _ensure_case_member(case_id, current_user.id, db)

    result = await db.execute(
        select(CaseMember, User)
        .join(User, User.id == CaseMember.user_id)
        .where(CaseMember.case_id == case_id)
        .order_by(CaseMember.joined_at.asc())
    )

    return [
        CaseMemberUserOut(
            user_id=user.id,
            full_name=user.full_name,
            email=user.email,
            role=user.role,
            member_role=member.member_role,
            joined_at=member.joined_at,
        )
        for member, user in result.all()
    ]


@router.post("/{case_id}/members", response_model=CaseMemberOut, status_code=status.HTTP_201_CREATED)
async def add_members_to_case(
    case_id: int,
    payload: CaseMemberCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_case_or_404(case_id, db)
    await _ensure_case_member(case_id, current_user.id, db)

    user_result = await db.execute(select(User)
                                .where(User.id == payload.user_id))
    user_obj = user_result.scalar_one_or_none()

    if not user_obj:
        raise HTTPException(status_code=404, detail="User not found")
    
    existing_member = await db.execute(
        select(CaseMember).where(
            CaseMember.case_id == case_id,
            CaseMember.user_id == payload.user_id,
        )
    )

    if existing_member.scalar_one_or_none():
        raise HTTPException(status_code=400, detail = "User already added to this case")

    member = CaseMember(case_id = case_id,
                        user_id = payload.user_id,
                        member_role = payload.member_role)
    
    db.add(member)
    await db.commit()
    await db.refresh(member)

    return member

