import uuid
from datetime import datetime, timezone
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.job import Job


@pytest_asyncio.fixture(scope="function")
async def sample_jobs(db_session: AsyncSession) -> list[Job]:
    """Fixture to seed sample jobs into the test database."""
    jobs = [
        Job(
            id=uuid.uuid4(),
            external_id=f"gh-job-{i}",
            company_name=f"Company {i}",
            title=f"Software Engineer {i}",
            location="Remote" if i % 2 == 0 else "San Francisco, CA",
            description=f"Job description for position {i}",
            application_link=f"https://careers.example.com/job/{i}",
            employment_type="Full-time",
            is_remote=(i % 2 == 0),
            source="greenhouse",
            posted_at=datetime.now(timezone.utc),
            is_active=True,
        )
        for i in range(1, 6)
    ]
    db_session.add_all(jobs)
    await db_session.commit()
    for job in jobs:
        await db_session.refresh(job)
    return jobs


@pytest.mark.asyncio
async def test_get_all_jobs_empty(client: AsyncClient):
    """Test GET /jobs when database has no jobs."""
    response = await client.get("/jobs")
    assert response.status_code == 200
    data = response.json()
    assert data["jobs"] == []
    assert data["total"] == 0
    assert data["offset"] == 0
    assert data["limit"] == 20


@pytest.mark.asyncio
async def test_get_all_jobs_populated(client: AsyncClient, sample_jobs: list[Job]):
    """Test GET /jobs when database has seeded jobs."""
    response = await client.get("/jobs")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["jobs"]) == 5


@pytest.mark.asyncio
async def test_get_all_jobs_pagination(client: AsyncClient, sample_jobs: list[Job]):
    """Test GET /jobs with limit and offset query parameters."""
    response = await client.get("/jobs?offset=0&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["jobs"]) == 2
    assert data["offset"] == 0
    assert data["limit"] == 2

    response_page2 = await client.get("/jobs?offset=2&limit=2")
    assert response_page2.status_code == 200
    data_page2 = response_page2.json()
    assert len(data_page2["jobs"]) == 2
    assert data_page2["offset"] == 2


@pytest.mark.asyncio
async def test_get_job_by_id_success(client: AsyncClient, sample_jobs: list[Job]):
    """Test GET /jobs/{job_id} with an existing job ID."""
    target_job = sample_jobs[0]
    response = await client.get(f"/jobs/{target_job.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(target_job.id)
    assert data["title"] == target_job.title
    assert data["company_name"] == target_job.company_name


@pytest.mark.asyncio
async def test_get_job_by_id_not_found(client: AsyncClient):
    """Test GET /jobs/{job_id} with a random non-existent UUID returns 404."""
    random_id = uuid.uuid4()
    response = await client.get(f"/jobs/{random_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"


@pytest.mark.asyncio
async def test_get_job_by_invalid_uuid(client: AsyncClient):
    """Test GET /jobs/{job_id} with invalid UUID format returns 422."""
    response = await client.get("/jobs/not-a-valid-uuid")
    assert response.status_code == 422
