import httpx


async def fetch_greenhouse_jobs(company_slug: str) -> list[dict]:
    """
    Fetches raw job postings from a company's Greenhouse board.
    Returns the RAW, untouched job dicts — no cleaning happens here.
    """
    url = f"https://boards-api.greenhouse.io/v1/boards/{company_slug}/jobs"
    params = {"content": "true"}  # include full job description

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()  # throws if 404/500 etc
        data = response.json()

    return data.get("jobs", [])