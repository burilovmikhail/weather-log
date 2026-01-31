from .auth import LoginIn, Token, authenticate, create_access_token, get_current_user
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from .db import observations_collection
from .models import ObservationDay

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

@app.put("/api/observations/{date}", response_model=ObservationDay)
async def upsert_day(date: str, payload: ObservationDay, user: str = Depends(get_current_user)):
    if payload.date != date:
        raise HTTPException(status_code=400, detail="date in path and body must match")

    col = observations_collection()
    data = payload.model_dump()
    await col.update_one({"date": date}, {"$set": data}, upsert=True)
    doc = await col.find_one({"date": date})
    return ObservationDay(**doc)
