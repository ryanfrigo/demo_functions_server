from fastapi import FastAPI, Query
from pydantic import BaseModel
import secrets

app = FastAPI(title="Demo Functions Server")

class RandomNumberRequest(BaseModel):
    digits: int = 6

@app.get("/healthz")
async def healthz():
    return {"ok": True}

@app.get("/functions/random-number")
async def get_random_number_get(digits: int = Query(6, ge=1, le=30)):
    value = secrets.randbelow(10 ** digits)
    number_str = f"{value:0{digits}d}"
    return {"ok": True, "digits": digits, "number": number_str}

@app.post("/functions/random-number")
async def get_random_number_post(payload: RandomNumberRequest | None = None):
    digits = (payload.digits if payload else 6)
    if digits < 1 or digits > 30:
        return {"ok": False, "error": "digits must be between 1 and 30"}
    value = secrets.randbelow(10 ** digits)
    number_str = f"{value:0{digits}d}"
    return {"ok": True, "digits": digits, "number": number_str}
