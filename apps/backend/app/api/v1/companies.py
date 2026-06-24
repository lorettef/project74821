import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user
from app.core.database import get_session
from app.models import User
from app.schemas import CompanyCreate, CompanyRead, CompanyUpdate
from app.services import company_service

router = APIRouter(prefix="/companies", tags=["companies"])


@router.post("", response_model=CompanyRead, status_code=201)
async def create_company(
    request: CompanyCreate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> CompanyRead:
    return await company_service.create_company(db, current_user, request)


@router.get("", response_model=list[CompanyRead])
async def list_companies(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[CompanyRead]:
    return await company_service.list_companies(db, current_user)


@router.get("/{company_id}", response_model=CompanyRead)
async def get_company(
    company_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> CompanyRead:
    return await company_service.get_company(db, company_id, current_user)


@router.put("/{company_id}", response_model=CompanyRead)
async def update_company(
    company_id: uuid.UUID,
    request: CompanyUpdate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> CompanyRead:
    return await company_service.update_company(db, company_id, current_user, request)


@router.delete("/{company_id}", status_code=204)
async def delete_company(
    company_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    await company_service.delete_company(db, company_id, current_user)
