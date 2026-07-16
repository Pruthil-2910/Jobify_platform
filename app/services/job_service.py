import uuid
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.job import Job


async def get_all_jobs(db: AsyncSession, offset: int = 0, limit: int = 20):
    result = await db.execute(
        select(Job).order_by(Job.posted_at.desc()).offset(offset).limit(limit)
    )
    jobs = result.scalars().all()

    total_result = await db.execute(select(func.count()).select_from(Job))
    total = total_result.scalar_one()

    return jobs, total

async def get_job_by_id(db: AsyncSession, job_id: uuid.UUID):
    result = await db.execute(select(Job).where(Job.id == job_id))
    return result.scalar_one_or_none()