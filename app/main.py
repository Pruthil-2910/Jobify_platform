from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.auth import router as auth_router
from app.api.routes.job import router as job_router

app = FastAPI(title="Jobify")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True, # Access-Control-Allow-Credentials like cookies
    allow_methods=["*"], # GET, POST, PUT, DELETE, OPTIONS
    allow_headers=["*"], # Access-Control-Allow-Headers like Content-Type, Authorization
)

app.add_middleware(GZipMiddleware, minimum_size=1000) # Compress responses larger than 1000 bytes
app.include_router(auth_router)
app.include_router(job_router)

@app.get("/health") # health check endpoint
def health():
    return {"status": "ok"}