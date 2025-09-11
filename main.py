from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

def gads_client():
    # Build client from environment vars; no local yaml needed
    return GoogleAdsClient.load_from_dict({
        "developer_token": os.getenv("GADS_DEV_TOKEN"),
        "client_id": os.getenv("GADS_CLIENT_ID"),
        "client_secret": os.getenv("GADS_CLIENT_SECRET"),
        "refresh_token": os.getenv("GADS_REFRESH_TOKEN"),
        "login_customer_id": os.getenv("GADS_LOGIN_CUSTOMER_ID", None),
    })

CUSTOMER_ID   = os.getenv("GOOGLE_ADS_CUSTOMER_ID")   # no dashes
DEFAULT_LANG  = os.getenv("DEFAULT_LANGUAGE_ID", "1000")  # English
DEFAULT_GEO   = os.getenv("DEFAULT_GEO_ID", "2840")       # United States
SEO_KEY       = os.getenv("SEO_KEY")                      # shared secret with WordPress

app = FastAPI(title="SEO Value Calculator API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class EstimateRequest(BaseModel):
    services: str
    location_geo_id: Optional[str] = None
    language_id: Optional[str] = None

class Idea(BaseModel):
    keyword: str
    avgMonthlySearches: int
    cpc: float

class EstimateResponse(BaseModel):
    ideas: List[Idea]
    totalVolume: int
    weightedCpc: float

def keyword_ideas(services: str, geo_id: str, language_id: str) -> List[Idea]:
    client = gads_client()
    service = client.get_service("KeywordPlanIdeaService")
    req = client.get_type("GenerateKeywordIdeasRequest")
    req.customer_id = CUSTOMER_ID
    req.language = f"languageConstants/{language_id}"
    req.geo_target_constants.append(f"geoTargetConstants/{geo_id}")
    req.keyword_seed.keywords.extend([s.strip() for s in services.split(",") if s.strip()])
    req.include_adult_keywords = False

    out: List[Idea] = []
    try:
        for r in service.generate_keyword_ideas(request=req):
            m = r.keyword_idea_metrics
            low  = (m.low_top_of_page_bid_micros  or 0)/1_000_000
            high = (m.high_top_of_page_bid_micros or 0)/1_000_000
            cpc = round(high or low or 0.0, 2)
            out.append(Idea(keyword=r.text, avgMonthlySearches=m.avg_monthly_searches or 0, cpc=cpc))
    except GoogleAdsException as ex:
        print(ex)
        raise HTTPException(status_code=500, detail="Google Ads error")
    return out

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.post("/estimate", response_model=EstimateResponse)
def estimate(req: EstimateRequest, x_seo_key: str = Header(default=None)):
    if not SEO_KEY or x_seo_key != SEO_KEY:
        raise HTTPException(403, "Forbidden")
    geo = req.location_geo_id or DEFAULT_GEO
    lang = req.language_id or DEFAULT_LANG
    ideas = sorted(keyword_ideas(req.services, geo, lang), key=lambda i: i.avgMonthlySearches, reverse=True)[:25]
    total = sum(i.avgMonthlySearches for i in ideas)
    w_cpc = round((sum(i.cpc * i.avgMonthlySearches for i in ideas) / total) if total else 0.0, 2)
    return EstimateResponse(ideas=ideas, totalVolume=total, weightedCpc=w_cpc)
