from fastapi import FastAPI, Query, Response
# Demo Functions Server – Sutherland endpoints v3
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

# ---------------------------
# Sutherland Healthcare Demo
# ---------------------------

class VerifyIdentityRequest(BaseModel):
    method: str
    factors: dict

class VerifyIdentityResponse(BaseModel):
    status: str

def _unwrap(payload: dict) -> dict:
    """Accept bodies shaped as {..}, {args:{..}}, or {body:{..}} (and tolerate extra keys)."""
    if not isinstance(payload, dict):
        return {}
    if isinstance(payload.get("args"), dict):
        return payload.get("args")
    if isinstance(payload.get("body"), dict):
        return payload.get("body")
    return payload


@app.post("/functions/verify-identity")
async def verify_identity(payload: dict) -> VerifyIdentityResponse:
    # Be tolerant to different wrappers used by various tool runners
    args = _unwrap(payload)
    method = args.get("method") if isinstance(args, dict) else None
    factors = args.get("factors") if isinstance(args, dict) else None
    if isinstance(factors, str):
        try:
            import json as _json
            factors = _json.loads(factors)
        except Exception:
            factors = {}
    if not isinstance(factors, dict):
        factors = {}

    last_name = str(factors.get("last_name", "")).strip().lower()
    dob = str(factors.get("dob", "")).strip()
    zip_code = str(factors.get("zip", "")).strip()
    account_id = str(factors.get("account_id", "")).strip()
    statement_id = str(factors.get("statement_id", "")).strip()

    if last_name in {"mismatch", "wrong"}:
        return VerifyIdentityResponse(status="failed")
    if not last_name or not dob:
        return VerifyIdentityResponse(status="failed")
    # Accept multiple verification methods used in demos
    if method not in {"hipaa_minimum", "proxy_auth", "knowledge", "statement_id", "member_id"}:
        return VerifyIdentityResponse(status="failed")
    # One more factor required for success
    if not (zip_code or account_id or statement_id):
        return VerifyIdentityResponse(status="failed")
    return VerifyIdentityResponse(status="verified")


class LookupPatientAccountRequest(BaseModel):
    last_name: str | None = None
    dob: str | None = None
    zip: str | None = None
    patient_id: str | None = None
    account_id: str | None = None
    statement_id: str | None = None
    phone: str | None = None

@app.post("/functions/lookup-patient-account")
async def lookup_patient_account(payload: dict):
    args = _unwrap(payload)
    payload = LookupPatientAccountRequest(**{k: args.get(k) for k in [
        "last_name","dob","zip","patient_id","account_id","statement_id","phone"
    ]})
    # Error path: not found
    if (payload.last_name or "").lower() in {"unknown", "notfound"}:
        return {"account_id": None, "error": "not_found"}
    # Deterministic account id
    account_id = payload.account_id or "ACCT-100200"
    total_due = 425.75
    min_due = 75.00
    result = {
        "account_id": account_id,
        "balances": {"total_due": total_due, "min_due": min_due},
        "statements": [
            {"statement_id": "STMT-778899", "date": "2025-07-15"},
            {"statement_id": "STMT-889900", "date": "2025-08-01"},
        ],
        "provider": "Sutherland Health Partners",
        "service_dates": ["2025-06-22", "2025-06-24"],
    }
    return result


@app.get("/functions/get-statement-details")
async def get_statement_details(statement_id: str):
    if statement_id.lower() in {"bad", "error"}:
        return {"error": "statement_unavailable"}
    return {
        "line_items": [
            {"desc": "Office visit", "cpt": "99213", "amount": 180.00},
            {"desc": "Lab work", "cpt": "80050", "amount": 220.00},
        ],
        "adjustments": [
            {"type": "contractual", "amount": -120.00},
        ],
        "insurance_payments": [
            {"payer": "Acme Health", "amount": 100.00, "date": "2025-07-01"},
        ],
    }

class GetStatementDetailsRequest(BaseModel):
    statement_id: str

@app.post("/functions/get-statement-details")
async def get_statement_details_post(payload: dict):
    args = _unwrap(payload)
    sid = args.get("statement_id")
    return await get_statement_details(sid)


@app.get("/functions/get-payment-options")
async def get_payment_options(account_id: str):
    if account_id.lower() in {"blocked", "hold"}:
        return {"error": "account_on_hold"}
    return {
        "min_due": 75.00,
        "total_due": 425.75,
        "plans": [
            {"installments": 3, "frequency": "monthly", "down_payment": 50.00},
            {"installments": 6, "frequency": "biweekly", "down_payment": 25.00},
        ],
    }

class GetPaymentOptionsRequest(BaseModel):
    account_id: str

@app.post("/functions/get-payment-options")
async def get_payment_options_post(payload: dict):
    args = _unwrap(payload)
    aid = args.get("account_id")
    return await get_payment_options(aid)


class OpenPaymentPortalRequest(BaseModel):
    account_id: str
    amount: float

@app.post("/functions/open-secure-payment-portal")
async def open_secure_payment_portal(payload: dict):
    args = _unwrap(payload)
    account_id = args.get("account_id")
    amount = float(args.get("amount", 0) or 0)
    if amount <= 0:
        return {"error": "invalid_amount"}
    token_suffix = secrets.token_hex(8)
    return {
        "payment_token_url": f"https://secure.pay.example.com/token/{token_suffix}"
    }


class CreatePaymentRequest(BaseModel):
    account_id: str
    amount: float
    token: str
    method: str
    last4: str

@app.post("/functions/create-payment")
async def create_payment(payload: dict):
    args = _unwrap(payload)
    token = str(args.get("token", ""))
    if not token.startswith("tok_"):
        return {"error": "invalid_token"}
    receipt_id = f"RCT-{secrets.token_hex(4).upper()}"
    return {"receipt_id": receipt_id, "timestamp": "2025-08-15T12:00:00Z"}


class CreatePaymentPlanRequest(BaseModel):
    account_id: str
    amount: float
    installments: int
    frequency: str
    start_date: str

@app.post("/functions/create-payment-plan")
async def create_payment_plan(payload: dict):
    args = _unwrap(payload)
    installments = int(args.get("installments", 0) or 0)
    amount = float(args.get("amount", 0) or 0)
    start_date = str(args.get("start_date", "") or "")
    if installments < 2:
        return {"error": "installments_too_low"}
    plan_id = f"PLAN-{secrets.token_hex(3).upper()}"
    # Simplified schedule
    schedule = [
        {"due_date": start_date, "amount": round(amount / installments, 2)}
        for _ in range(installments)
    ]
    return {"plan_id": plan_id, "schedule": schedule}


class SendSMSRequest(BaseModel):
    phone: str
    text: str | None = None
    link: str | None = None

@app.post("/functions/send-sms")
async def send_sms(payload: dict):
    args = _unwrap(payload)
    phone = str(args.get("phone", "") or "")
    text = args.get("text")
    link = args.get("link")
    if not (text or link):
        return {"status": "failed", "error": "missing_content"}
    if phone.endswith("0000"):
        return {"status": "failed", "error": "carrier_reject"}
    return {"status": "sent"}


class SendEmailRequest(BaseModel):
    email: str
    subject: str
    body: str | None = None
    link: str | None = None

@app.post("/functions/send-email")
async def send_email(payload: dict):
    args = _unwrap(payload)
    email = str(args.get("email", "") or "")
    subject = str(args.get("subject", "") or "")
    body = args.get("body")
    link = args.get("link")
    if not (body or link):
        return {"status": "failed", "error": "missing_content"}
    if email.lower().endswith("@invalid.test"):
        return {"status": "failed", "error": "bounce"}
    return {"status": "sent"}


class LookupBenefitsRequest(BaseModel):
    member_id: str | None = None
    payer: str | None = None
    dob: str | None = None
    last_name: str | None = None
    provider_npi: str | None = None
    service_type: str | None = None
    cpt_code: str | None = None

@app.post("/functions/lookup-benefits")
async def lookup_benefits(payload: dict):
    args = _unwrap(payload)
    member_id = args.get("member_id")
    provider_npi = args.get("provider_npi")
    if (member_id or "").lower() in {"unknown", "notfound"}:
        return {"error": "member_not_found"}
    coverage_active = not ((member_id or "").endswith("X"))
    result = {
        "coverage_active": coverage_active,
        "plan_name": "Acme PPO 2000",
        "effective_dates": {"start": "2025-01-01", "end": "2025-12-31"},
        "copay": 40.0,
        "coinsurance": 0.2,
        "deductible_remaining": 350.0,
        "oop_remaining": 1200.0,
        "visit_limits": {"pt": 20, "ot": 20},
        "network_status": "in_network" if (provider_npi or "").endswith("7") else "unknown",
    }
    return result


class CheckPriorAuthRequest(BaseModel):
    payer: str
    plan_id: str | None = None
    cpt_code: str
    provider_npi: str | None = None

@app.post("/functions/check-prior-auth")
async def check_prior_auth(payload: dict):
    args = _unwrap(payload)
    cpt_code = str(args.get("cpt_code", "") or "")
    required = cpt_code in {"70551", "73721", "72148"}
    notes = "MRI/CT often require prior auth" if required else "Not typically required"
    return {"required": required, "notes": notes}


class EstimatePatientResponsibilityRequest(BaseModel):
    member_id: str
    plan_id: str | None = None
    cpt_code: str
    in_network: bool

@app.post("/functions/estimate-patient-responsibility")
async def estimate_patient_responsibility(payload: dict):
    args = _unwrap(payload)
    in_network = bool(args.get("in_network", True))
    base = 500.0 if in_network else 900.0
    estimate = base * 0.3
    return {"estimate": round(estimate, 2), "assumptions": "In-network unless noted; excludes facility fees"}


class CreateTicketRequest(BaseModel):
    category: str
    summary: str
    details: dict

@app.post("/functions/create-ticket")
async def create_ticket(payload: dict):
    # Ticket number is spoken as "123 — 456"; store with dash
    return {"ticket_number": "123-456"}


class TransferCallRequest(BaseModel):
    queue: str
    reason: str

@app.post("/functions/transfer-call")
async def transfer_call(payload: dict):
    return {"status": "transferred"}
