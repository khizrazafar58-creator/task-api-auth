"""
Task API — now with Auth.
FlyRank AI Internship — Backend AI Engineering — BE-03: Auth · Login & protect

Stage 0: setup server + Supabase client
Stage 1: signup / login routes
Stage 2: public + (unverified) protected routes
Stage 3: token verification on /protected/profile
Stage 4: auth middleware (dependency) + logout, reused on a second protected route
Stage 5: Swagger UI with Bearer auth (HTTPBearer) — built in at /docs
"""
_
import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from dotenv import load_dotenv
from supabase import create_client, Client

# ---------------------------------------------------------------------------
# Stage 0: load environment variables + connect to Supabase
# ---------------------------------------------------------------------------
load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "Missing SUPABASE_URL or SUPABASE_KEY. Copy .env.example to .env "
        "and fill in your own Supabase project values."
    )

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(
    title="Task API — with Auth",
    version="2.0",
    description=(
        "A CRUD Task API secured with Supabase Auth. Sign up, log in, log out, "
        "and access a protected profile route with a Bearer token."
    ),
)

print("Server running and connected to Supabase")


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------
class AuthPayload(BaseModel):
    email: str
    password: str


# ---------------------------------------------------------------------------
# Stage 4: reusable auth guard (FastAPI "dependency" = middleware equivalent)
# ---------------------------------------------------------------------------
bearer_scheme = HTTPBearer()


def require_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    """
    Reusable guard: extracts the Bearer token, verifies it with Supabase,
    and returns the authenticated user. Any route can depend on this to
    become protected — this is the single guard used by every locked door.
    """
    token = credentials.credentials
    if not token:
        raise HTTPException(status_code=401, detail="Access token required")

    try:
        response = supabase.auth.get_user(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if not response or not response.user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return response.user


# ---------------------------------------------------------------------------
# Stage 1: Sign up & Log in (open auth — no token required yet)
# ---------------------------------------------------------------------------
@app.post("/auth/signup", status_code=201, tags=["auth"], summary="Create a new account")
def signup(payload: AuthPayload):
    """Registers a new user with Supabase Auth. Returns the created user object."""
    if not payload.email or not payload.password:
        raise HTTPException(status_code=400, detail="Email and password are required")

    try:
        result = supabase.auth.sign_up({"email": payload.email, "password": payload.password})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not result.user:
        raise HTTPException(status_code=400, detail="Signup failed")

    return {"id": result.user.id, "email": result.user.email}


@app.post("/auth/login", tags=["auth"], summary="Log in and receive a JWT")
def login(payload: AuthPayload):
    """Authenticates the user and returns an access token + refresh token."""
    if not payload.email or not payload.password:
        raise HTTPException(status_code=400, detail="Email and password are required")

    try:
        result = supabase.auth.sign_in_with_password(
            {"email": payload.email, "password": payload.password}
        )
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid login credentials")

    if not result.session:
        raise HTTPException(status_code=401, detail="Invalid login credentials")

    return {
        "access_token": result.session.access_token,
        "refresh_token": result.session.refresh_token,
        "token_type": "bearer",
    }


# ---------------------------------------------------------------------------
# Stage 2 + 3: public + protected routes
# ---------------------------------------------------------------------------
@app.get("/public/info", tags=["public"], summary="Public, unprotected data")
def public_info():
    """No auth required — anyone can call this."""
    return {"message": "Welcome stranger! This info is public."}


@app.get("/protected/profile", tags=["protected"], summary="Read private profile data")
def protected_profile(user=Depends(require_user)):
    """
    Protected route — only reachable with a valid Bearer token.
    The require_user guard already verified the token before this code runs.
    """
    return {
        "id": user.id,
        "email": user.email,
        "created_at": user.created_at,
    }


# ---------------------------------------------------------------------------
# Stage 4 (continued): a second protected route, reusing the same guard,
# plus logout
# ---------------------------------------------------------------------------
@app.get("/protected/dashboard", tags=["protected"], summary="Another protected route")
def protected_dashboard(user=Depends(require_user)):
    """Proves the same guard (require_user) protects more than one route."""
    return {"message": f"Welcome back, {user.email}. This is your dashboard."}


@app.post("/auth/logout", status_code=204, tags=["auth"], summary="Log out")
def logout(user=Depends(require_user)):
    """Protected route — ends the current session via Supabase."""
    try:
        supabase.auth.sign_out()
    except Exception:
        pass  # sign_out is best-effort; still return 204
    return


# ---------------------------------------------------------------------------
# Optional extra: 403 case — an authenticated user who still isn't allowed
# ---------------------------------------------------------------------------
ADMIN_EMAILS = {"admin@example.com"}  # swap in a real admin email to test


@app.get("/protected/admin-only", tags=["protected"], summary="Admin-only route (403 example)")
def admin_only(user=Depends(require_user)):
    """
    401 = 'I don't know you' (handled by require_user already).
    403 = 'I know exactly who you are, and you still may not.'
    """
    if user.email not in ADMIN_EMAILS:
        raise HTTPException(status_code=403, detail="Admins only")
    return {"message": f"Welcome, admin {user.email}."}
