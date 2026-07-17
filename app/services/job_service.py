import uuid
from sqlalchemy import select, func
from app.models.job import Job
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession


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


async def upsert_job(db: AsyncSession, job_data: dict) -> Job:
    """
    job_data must contain at least: external_id, company_name, title,
    location, description, application_link, employment_type,
    is_remote, source, posted_at
    """
    stmt = pg_insert(Job).values(**job_data)

    update_columns = {
        col: stmt.excluded[col]
        for col in job_data.keys()
        if col != "external_id"  # never overwrite the conflict key itself
    }

    stmt = stmt.on_conflict_do_update(
        index_elements=["external_id"],
        set_=update_columns,
        where=(
            (Job.title != stmt.excluded.title)
            | (Job.description != stmt.excluded.description)
            | (Job.location != stmt.excluded.location)
            | (Job.is_active != stmt.excluded.is_active)
        ),
    ).returning(Job)

    result = await db.execute(stmt)
    await db.commit()

    row = result.first()
    if row is not None:
        return row[0]

    # WHERE clause skipped the update (nothing changed) — fetch existing row
    existing = await db.scalar(select(Job).where(Job.external_id == job_data["external_id"]))
    return existing


async def upsert_jobs_batch(db: AsyncSession, jobs_data: list[dict]) -> dict:
    """
    Runs upsert_job for a list of jobs. Returns counts for visibility.
    """
    inserted_or_updated = 0
    skipped = 0

    for job_data in jobs_data:
        before = await db.scalar(
            select(func.count()).select_from(Job).where(Job.external_id == job_data["external_id"])
        )
        await upsert_job(db, job_data)
        if before == 0:
            inserted_or_updated += 1
        else:
            skipped += 1  # existed already, may or may not have changed

    return {"processed": len(jobs_data), "new_or_updated": inserted_or_updated, "already_existed": skipped}