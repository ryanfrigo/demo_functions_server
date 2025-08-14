from fastapi import FastAPI, Query, Response
from pydantic import BaseModel
import secrets

app = FastAPI(title="Demo Functions Server")

class RandomNumberRequest(BaseModel):
    digits: int = 6

@app.get("/healthz")
async def healthz():
    return {"ok": True}

@app.get("/functions/random-number")
async def get_random_number_get(
    digits: int = Query(6, ge=1, le=30),
    format: str = Query("text", pattern="^(text|json)$"),
):
    # Ensure the first digit is never 0 by sampling from
    # [10^(digits-1), 10^digits - 1]
    start = 10 ** (digits - 1)
    range_size = 9 * start
    value = secrets.randbelow(range_size) + start
    number_str = str(value)
    if format == "json":
        return {"ok": True, "digits": digits, "number": number_str}
    return Response(content=number_str, media_type="text/plain")

@app.post("/functions/random-number")
async def get_random_number_post(payload: RandomNumberRequest | None = None, format: str = Query("json", pattern="^(text|json)$")):
    digits = (payload.digits if payload else 6)
    if digits < 1 or digits > 30:
        if format == "json":
            return {"ok": False, "error": "digits must be between 1 and 30"}
        return Response(content="digits must be between 1 and 30", status_code=400, media_type="text/plain")
    # Ensure the first digit is never 0 by sampling from
    # [10^(digits-1), 10^digits - 1]
    start = 10 ** (digits - 1)
    range_size = 9 * start
    value = secrets.randbelow(range_size) + start
    number_str = str(value)
    if format == "json":
        return {"ok": True, "digits": digits, "number": number_str}
    return Response(content=number_str, media_type="text/plain")
