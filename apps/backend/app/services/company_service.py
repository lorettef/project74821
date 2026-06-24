import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models import Company, User
from app.schemas import CompanyCreate, CompanyRead, CompanyUpdate

logger = structlog.get_logger(__name__)


async def create_company(
    db: AsyncSession, user: User, request: CompanyCreate
) -> CompanyRead:
    """Create a company for the authenticated user. Rejects duplicate name per user."""
    existing = await db.execute(
        select(Company).where(
            Company.owner_id == user.id,
            Company.name == request.name,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise ConflictError("Company with this name already exists")

    company = Company(
        owner_id=user.id,
        name=request.name,
        stage=request.stage,
    )
    db.add(company)
    await db.commit()
    await db.refresh(company)

    logger.info("company_created", company_id=str(company.id), user_id=str(user.id))

    return CompanyRead.model_validate(company)


async def get_company(
    db: AsyncSession, company_id: uuid.UUID, user: User
) -> CompanyRead:
    """Get company by ID. Verifies the company belongs to the authenticated user."""
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()

    if company is None or company.owner_id != user.id:
        raise NotFoundError("Company not found")

    return CompanyRead.model_validate(company)


async def list_companies(
    db: AsyncSession, user: User
) -> list[CompanyRead]:
    """List all companies owned by the authenticated user."""
    result = await db.execute(
        select(Company).where(Company.owner_id == user.id)
    )
    companies = result.scalars().all()
    return [CompanyRead.model_validate(c) for c in companies]


async def update_company(
    db: AsyncSession, company_id: uuid.UUID, user: User, request: CompanyUpdate
) -> CompanyRead:
    """Update a company. Only sets provided (non-None) fields. Verifies ownership."""
    company = await _get_owned_company(db, company_id, user)

    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(company, field, value)

    await db.commit()
    await db.refresh(company)

    logger.info("company_updated", company_id=str(company.id), user_id=str(user.id))

    return CompanyRead.model_validate(company)


async def delete_company(
    db: AsyncSession, company_id: uuid.UUID, user: User
) -> None:
    """Delete a company. Verifies ownership. Hard delete (CASCADE handles FKs)."""
    company = await _get_owned_company(db, company_id, user)
    await db.delete(company)
    await db.commit()

    logger.info("company_deleted", company_id=str(company_id), user_id=str(user.id))


async def _get_owned_company(
    db: AsyncSession, company_id: uuid.UUID, user: User
) -> Company:
    """Fetch company and verify ownership. Raises NotFoundError if not found or not owned."""
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()

    if company is None or company.owner_id != user.id:
        raise NotFoundError("Company not found")

    return company
