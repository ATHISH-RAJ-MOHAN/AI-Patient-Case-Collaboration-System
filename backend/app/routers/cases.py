from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import CaseMember, PatientCase, User
from app.schemas import CaseCreate, CaseMemberCreate, CaseMemberOut, CaseOut
from app.security import get_current_user

router = APIRouter(prefix = "/cases", tags = ["Cases"])

@router.post("/", response_model=CaseOut, status_code=status.HTTP_201_CREATED)
async def create_case(
    payload:CaseCreate,
    db:AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
    ) :
    
    existing = await db.execute(
        select(PatientCase).where(PatientCase.patient_code == payload.patient_code)
    )

    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Patient code already exists")
    
    new_case = PatientCase(
        patient_code = payload.patient_code,
        case_title = payload.case_title,
        created_by = current_user.id
    )

    db.add(new_case)
    await db.commit()
    await db.refresh(new_case)

    #add creator as member of the case
    creator_member = CaseMember(
        case_id = new_case.id,
        user_id = current_user.id,
        member_role = "admin"
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

@router.post("/{case_id}/members", response_model=CaseMemberOut, status_code=status.HTTP_201_CREATED)
async def add_members_to_case(case_id: int, payload: CaseMemberCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):

    case_result = await db.execute(select(PatientCase).where(PatientCase.id == case_id))
    case_obj = case_result.scalar_one_or_none()

    if not case_obj:
        raise HTTPException(status_code=404, detail="Case not found")

    user_result = await db.execute(select(User)
                                .where(User.id == payload.user_id))
    user_obj = user_result.scalar_one_or_none()

    if not user_obj:
        raise HTTPException(status_code=404, detail="User not found")
    
    existing = await db.execute(
        select(CaseMember).where(
            CaseMember.case_id == case_id,
            CaseMember.user_id == payload.user_id,
        )
    )

    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail = "User already added to this case")
    
    current_member = await db.execute(select(CaseMember).where(CaseMember.case_id == case_id,
                                                               CaseMember.user_id == current_user.id,))

    if not current_member.scalar_one_or_none():
        raise HTTPException(
            status_code=403,
            detail = "You are not allowed to modify this case"
        )

    member = CaseMember(case_id = case_id,
                        user_id = payload.user_id,
                        member_role = payload.member_role)
    
    db.add(member)
    await db.commit()
    await db.refresh(member)

    return member


