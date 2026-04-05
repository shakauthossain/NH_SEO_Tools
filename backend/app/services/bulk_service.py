import os
import asyncio
import pandas as pd
from sqlalchemy.orm import Session
from app.models import Audit, BulkJob, JobStatus
from app.services.seo_service import scrape_rankmath_async
from app.services.speed_service import fetch_pagespeed_data_sync, parse_pagespeed_data
from app.services.pdf_service import generate_pdf
import uuid

# Helper to import original HTML generators
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.getcwd())))
try:
    from singlesite_seo import generate_report as gen_seo_html
    from singlesite_speed import generate_report as gen_speed_html
except ImportError:
    gen_seo_html = None
    gen_speed_html = None

REPORTS_DIR = os.path.join(os.getcwd(), "reports")
PAGESPEED_API_KEY = os.getenv("PAGESPEED_API_KEY", "AIzaSyCItGGWJ4uWXr2EzRwgscKD81N9cislDIw")

async def process_bulk_audit(db: Session, job_id: int, file_path: str, user_id: int):
    job = db.query(BulkJob).filter(BulkJob.id == job_id).first()
    job.status = "running"
    db.commit()
    
    try:
        # Load file
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        
        # Identify URL column
        url_col = None
        for col in df.columns:
            if col.lower() in ['url', 'website', 'link', 'site']:
                url_col = col
                break
        
        if not url_col:
            url_col = df.columns[0] # Fallback to first column
            
        results = []
        
        for index, row in df.iterrows():
            url = str(row[url_col]).strip()
            if not url.startswith('http'):
                url = 'https://' + url
            
            print(f"Processing ({index+1}/{len(df)}): {url}")
            
            report_id = str(uuid.uuid4())
            result_row = row.to_dict()
            
            # 1. SEO
            seo_data = await scrape_rankmath_async(url)
            seo_score = seo_data.get("seo_score", "N/A")
            result_row["SEO Score"] = seo_score
            
            if gen_seo_html:
                html = gen_seo_html(seo_data)
                h_path = os.path.join(REPORTS_DIR, f"{report_id}_seo.html")
                with open(h_path, "w", encoding="utf-8") as f:
                    f.write(html)
                result_row["SEO Report Link"] = f"http://localhost:8000/reports/{report_id}_seo.html"
            
            # 2. Speed
            raw_speed = fetch_pagespeed_data_sync(url, PAGESPEED_API_KEY)
            speed_score = "N/A"
            if raw_speed:
                speed_data = parse_pagespeed_data(raw_speed, url, "mobile")
                speed_score = speed_data.get("perf_score", "N/A")
                if gen_speed_html:
                    html = gen_speed_html(speed_data)
                    h_path = os.path.join(REPORTS_DIR, f"{report_id}_speed.html")
                    with open(h_path, "w", encoding="utf-8") as f:
                        f.write(html)
                    result_row["Speed Report Link"] = f"http://localhost:8000/reports/{report_id}_speed.html"
            
            result_row["Speed Score"] = speed_score
            results.append(result_row)
            
            # Save to Database
            db_audit = Audit(
                user_id=user_id,
                url=url,
                seo_score=str(seo_score),
                speed_score=str(speed_score),
                report_id=report_id,
                full_results={"seo": seo_data, "speed": speed_data if raw_speed else {}}
            )
            db.add(db_audit)
            db.commit()
            
            # Rate limiting / Sleep to avoid blocking/bans
            await asyncio.sleep(5)
            
        # Generate output file
        output_df = pd.DataFrame(results)
        output_filename = f"bulk_result_{job_id}.csv"
        output_path = os.path.join(REPORTS_DIR, output_filename)
        output_df.to_csv(output_path, index=False)
        
        job.status = "completed"
        job.output_filename = output_filename
        db.commit()
        
    except Exception as e:
        print(f"Bulk Error: {e}")
        job.status = "failed"
        db.commit()
