from .auth import LoginIn, Token, authenticate, create_access_token, get_current_user
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import date as dt_date, timedelta
from .db import observations_collection
from .models import ObservationDay
from .scraper import fetch_day

app = FastAPI(title="Meteo Log API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health():
    return {"ok": True}

@app.post("/api/login", response_model=Token)
async def login(payload: LoginIn):
    if not authenticate(payload.username, payload.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(payload.username)
    return {"access_token": token, "token_type": "bearer"}


@app.get("/api/observations", response_model=List[ObservationDay])
async def list_days(
    from_: Optional[str] = Query(None, alias="from"),
    to: Optional[str] = Query(None),
    user: str = Depends(get_current_user),
):
    col = observations_collection()
    q = {}
    if from_ or to:
        q["date"] = {}
        if from_:
            q["date"]["$gte"] = from_
        if to:
            q["date"]["$lte"] = to

    cursor = col.find(q).sort("date", 1)
    docs = await cursor.to_list(length=1000)
    return [ObservationDay(**doc) for doc in docs]

@app.get("/api/observations/{date}", response_model=ObservationDay)
async def get_day(date: str, user: str = Depends(get_current_user)):
    col = observations_collection()
    doc = await col.find_one({"date": date})
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    return ObservationDay(**doc)

class SyncResponse(BaseModel):
    synced: List[str]
    skipped: List[str]
    errors: Dict[str, str]


@app.post("/api/sync", response_model=SyncResponse)
async def sync(user: str = Depends(get_current_user)):
    col = observations_collection()

    # Найти последний заполненный день
    last_doc = await col.find_one({}, sort=[("date", -1)])
    if not last_doc:
        raise HTTPException(status_code=404, detail="No observations in DB to sync from")

    last_date = dt_date.fromisoformat(last_doc["date"])
    today = dt_date.today()

    synced: List[str] = []
    skipped: List[str] = []
    errors: Dict[str, str] = {}

    cur = last_date + timedelta(days=1)
    while cur < today:
        date_str = cur.isoformat()
        existing = await col.find_one({"date": date_str})
        if existing:
            skipped.append(date_str)
        else:
            try:
                day = await fetch_day(date_str)
                data = day.model_dump()
                await col.update_one({"date": date_str}, {"$set": data}, upsert=True)
                synced.append(date_str)
            except Exception as e:
                errors[date_str] = str(e)
        cur += timedelta(days=1)

    return SyncResponse(synced=synced, skipped=skipped, errors=errors)


@app.put("/api/observations/{date}", response_model=ObservationDay)
async def upsert_day(date: str, payload: ObservationDay, user: str = Depends(get_current_user)):
    if payload.date != date:
        raise HTTPException(status_code=400, detail="date in path and body must match")

    col = observations_collection()
    data = payload.model_dump()
    await col.update_one({"date": date}, {"$set": data}, upsert=True)
    doc = await col.find_one({"date": date})
    return ObservationDay(**doc)
