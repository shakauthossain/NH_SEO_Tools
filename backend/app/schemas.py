from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from enum import Enum

class ReportType(str, Enum):
    SEO = "seo"
    SPEED = "speed"
    BOTH = "both"

class AnalysisRequest(BaseModel):
    url: str
    report_type: ReportType = ReportType.BOTH

class AnalysisResponse(BaseModel):
    id: str
    url: str
    status: str
    seo_report_url: Optional[str] = None
    speed_report_url: Optional[str] = None
    seo_pdf_url: Optional[str] = None
    speed_pdf_url: Optional[str] = None
