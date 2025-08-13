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
    value = secrets.randbelow(10 ** digits)
    number_str = f"{value:0{digits}d}"
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
    value = secrets.randbelow(10 ** digits)
    number_str = f"{value:0{digits}d}"
    if format == "json":
        return {"ok": True, "digits": digits, "number": number_str}
    return Response(content=number_str, media_type="text/plain")
