# app/api/routes/job.py
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.job import JobResponse, JobListResponse
from app.services import job_service

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=JobListResponse)
async def get_all_jobs(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db), 
):
    jobs, total = await job_service.get_all_jobs(db, offset=offset, limit=limit)
    return JobListResponse(jobs=jobs, total=total, offset=offset, limit=limit)

@router.get("/{job_id}", response_model=JobResponse)
async def get_job_by_id(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    job = await job_service.get_job_by_id(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job