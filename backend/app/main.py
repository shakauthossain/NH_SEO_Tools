import asyncio
import os
import uuid
from datetime import timedelta
from typing import List, Optional

from app.auth import (
    create_access_token,
    get_current_user,
    get_optional_user,
    get_password_hash,
    get_super_admin,
    verify_password,
)
from app.database import Base, engine, get_db
from app.models import Audit, BulkJob, User
from app.schemas import AnalysisRequest, AnalysisResponse, ReportType
from app.services.bulk_service import process_bulk_audit
from app.services.pdf_service import generate_pdf
from app.services.seo_service import generate_html as gen_seo_html
from app.services.seo_service import scrape_rankmath_async
from app.services.speed_service import fetch_pagespeed_data_sync, parse_pagespeed_data
from app.services.speed_service import generate_html as gen_speed_html
from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    File,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session

# Initialize Database
Base.metadata.create_all(bind=engine)

app = FastAPI(title="SEO & Speed Analysis API (Enterprise)")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

REPORTS_DIR = os.path.join(os.getcwd(), "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)
PAGESPEED_API_KEY = os.getenv("PAGESPEED_API_KEY", "")

# --- AUTH ROUTES ---

# --- ADMIN ROUTES ---


@app.post("/admin/create-user", status_code=status.HTTP_201_CREATED)
def admin_create_user(
    email: str,
    password: str,
    db: Session = Depends(get_db),
    admin_username: str = Depends(get_super_admin),
):
    db_user = db.query(User).filter(User.email == email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(email=email, hashed_password=get_password_hash(password))
    db.add(new_user)
    db.commit()
    return {"message": f"User {email} created successfully by admin {admin_username}"}


@app.get("/admin/users")
def admin_list_users(
    db: Session = Depends(get_db), admin_username: str = Depends(get_super_admin)
):
    users = db.query(User).all()
    result = []
    for u in users:
        audit_count = db.query(Audit).filter(Audit.user_id == u.id).count()
        result.append(
            {
                "id": u.id,
                "email": u.email,
                "audit_count": audit_count,
            }
        )
    return result


@app.delete("/admin/users/{user_id}")
def admin_delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin_username: str = Depends(get_super_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Delete user's audits first
    db.query(Audit).filter(Audit.user_id == user_id).delete()
    db.query(BulkJob).filter(BulkJob.user_id == user_id).delete()
    db.delete(user)
    db.commit()
    return {"message": f"User {user.email} deleted successfully"}


@app.get("/admin/stats")
def admin_stats(
    db: Session = Depends(get_db), admin_username: str = Depends(get_super_admin)
):
    total_users = db.query(User).count()
    total_audits = db.query(Audit).count()
    total_jobs = db.query(BulkJob).count()
    return {
        "total_users": total_users,
        "total_audits": total_audits,
        "total_bulk_jobs": total_jobs,
    }


@app.post("/token")
def login(email: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


# --- AUDIT ROUTES ---


@app.get("/me/audits")
def get_user_audits(current_user: User = Depends(get_current_user)):
    audits = []
    for a in current_user.audits:
        if a.report_id:
            audits.append(
                {
                    "report_id": a.report_id,
                    "url": a.url,
                    "seo_score": a.seo_score,
                    "speed_score": a.speed_score,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                }
            )
    return sorted(audits, key=lambda x: x["created_at"] or "", reverse=True)


@app.post("/analyze/bulk")
async def bulk_analyze(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Save uploaded file
    file_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1]
    file_path = os.path.join(REPORTS_DIR, f"upload_{file_id}{ext}")

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    # Create Job
    job = BulkJob(
        user_id=current_user.id, input_filename=file.filename, status="pending"
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(
        process_bulk_audit, db, job.id, file_path, current_user.id
    )

    return {"job_id": job.id, "status": "queued"}


@app.get("/bulk/status/{job_id}")
def get_bulk_status(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = (
        db.query(BulkJob)
        .filter(BulkJob.id == job_id, BulkJob.user_id == current_user.id)
        .first()
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


# --- LEGACY / SINGLE ROUTES (Updated to save to DB) ---


def normalize_url(url: str):
    """Ensures the URL has a protocol (http/https). Defaults to https."""
    if url.startswith(("http://", "https://")):
        return url
    return f"https://{url}"


@app.post("/analyze")
async def analyze_website(
    request: AnalysisRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    url = normalize_url(request.url)
    print(f"--- INFO: Starting analysis for {url} ---")
    report_type = request.report_type
    report_id = str(uuid.uuid4())

    # 1. SEO Analysis
    seo_data = {}
    if report_type in [ReportType.SEO, ReportType.BOTH]:
        seo_data = await scrape_rankmath_async(url)
        if gen_seo_html:
            html = gen_seo_html(seo_data)
            with open(
                os.path.join(REPORTS_DIR, f"{report_id}_seo.html"),
                "w",
                encoding="utf-8",
            ) as f:
                f.write(html)
            await generate_pdf(html, os.path.join(REPORTS_DIR, f"{report_id}_seo.pdf"))

    # 2. Speed Analysis
    speed_data = {}
    if report_type in [ReportType.SPEED, ReportType.BOTH]:
        print(f"--- INFO: Fetching Speed data for {url} ---")
        raw_speed = fetch_pagespeed_data_sync(url, PAGESPEED_API_KEY)
        if raw_speed:
            print(f"--- SUCCESS: Speed data fetched for {url} ---")
            speed_data = parse_pagespeed_data(raw_speed, url, "mobile")
            html = gen_speed_html(speed_data)
            with open(
                os.path.join(REPORTS_DIR, f"{report_id}_speed.html"),
                "w",
                encoding="utf-8",
            ) as f:
                f.write(html)
            await generate_pdf(
                html, os.path.join(REPORTS_DIR, f"{report_id}_speed.pdf")
            )
        else:
            print(f"--- WARNING: Speed data FETCH FAILED for {url} ---")

    # Save to DB (Defensive)
    try:
        full_results = {"seo": seo_data, "speed": speed_data}
        new_audit = Audit(
            url=url,
            seo_score=str(seo_data.get("seo_score", "N/A")),
            speed_score=str(speed_data.get("perf_score", "N/A")),
            report_id=report_id,
            full_results=full_results,
            user_id=current_user.id if current_user else None,
        )
        db.add(new_audit)
        db.commit()
        print(f"--- SUCCESS: Audit saved to history for {url} ---")
    except Exception as db_err:
        db.rollback()
        print(f"--- WARNING: Could not save audit to history: {db_err} ---")

    # Flatten for frontend dashboard
    seo_tests = []
    for cat in seo_data.get("categories", []):
        seo_tests.extend(cat.get("items", []))

    speed_tests = []
    for cat in speed_data.get("categories", []):
        speed_tests.extend(cat.get("items", []))

    return {
        "id": report_id,
        "seo": {
            **seo_data,
            "seo_score": seo_data.get("seo_score", "N/A"),
            "seo_tests": seo_tests,
        },
        "speed": {
            **speed_data,
            "perf_score": speed_data.get("perf_score", "N/A"),
            "metrics": {
                "fcp": speed_data.get("fcp", "N/A"),
                "lcp": speed_data.get("lcp", "N/A"),
                "cls": speed_data.get("cls", "N/A"),
                "tbt": speed_data.get("tbt", "N/A"),
                "si": speed_data.get("si", "N/A"),
                "tti": speed_data.get("tti", "N/A"),
            },
            "speed_tests": speed_tests,
        },
        "seo_report_url": f"/reports/{report_id}_seo.html",
        "speed_report_url": f"/reports/{report_id}_speed.html",
    }


@app.get("/reports/{filename}")
async def get_report_file(filename: str):
    file_path = os.path.join(REPORTS_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)


@app.get("/audits/{report_id}")
def get_audit(report_id: str, db: Session = Depends(get_db)):
    audit = db.query(Audit).filter(Audit.report_id == report_id).first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    seo_data = audit.full_results.get("seo", {}) if audit.full_results else {}
    speed_data = audit.full_results.get("speed", {}) if audit.full_results else {}

    seo_tests = []
    for cat in seo_data.get("categories", []):
        seo_tests.extend(cat.get("items", []))

    speed_tests = []
    for cat in speed_data.get("categories", []):
        speed_tests.extend(cat.get("items", []))

    speed_metrics = {
        "fcp": speed_data.get("fcp", "N/A"),
        "lcp": speed_data.get("lcp", "N/A"),
        "cls": speed_data.get("cls", "N/A"),
        "tbt": speed_data.get("tbt", "N/A"),
        "si": speed_data.get("si", "N/A"),
        "tti": speed_data.get("tti", "N/A"),
    }

    return {
        "id": report_id,
        "url": audit.url,
        "seo": {**seo_data, "seo_score": audit.seo_score, "seo_tests": seo_tests},
        "speed": {
            **speed_data,
            "perf_score": audit.speed_score,
            "metrics": speed_metrics,
            "speed_tests": speed_tests,
        },
        "seo_report_url": f"/reports/{report_id}_seo.html",
        "speed_report_url": f"/reports/{report_id}_speed.html",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
