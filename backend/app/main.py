from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from .db import observations_collection
from .models import ObservationDay

app = FastAPI(title="Meteo Log API")

# Для дев-режима: разрешим фронту ходить на API
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

@app.get("/api/observations", response_model=List[ObservationDay])
async def list_days(
    from_: Optional[str] = Query(None, alias="from"),
    to: Optional[str] = Query(None)
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
async def get_day(date: str):
    col = observations_collection()
    doc = await col.find_one({"date": date})
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    return ObservationDay(**doc)

@app.put("/api/observations/{date}", response_model=ObservationDay)
async def upsert_day(date: str, payload: ObservationDay):
    if payload.date != date:
        raise HTTPException(status_code=400, detail="date in path and body must match")

    col = observations_collection()
    data = payload.model_dump()
    await col.update_one({"date": date}, {"$set": data}, upsert=True)
    doc = await col.find_one({"date": date})
    return ObservationDay(**doc)
