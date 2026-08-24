# Task API — with Auth

A secured version of the Task API, using **Supabase Auth** as the Identity Provider. Built for the FlyRank AI Internship — Backend AI Engineering track — BE-03: *Auth · Login & protect*.

## What this is

A FastAPI backend that handles Sign Up, Log In, and Log Out through Supabase, issues JWTs, and protects specific routes so they only answer for logged-in users — verified via a reusable auth guard (FastAPI dependency).
_
## How to set up your environment variables

1. Create a free project at [supabase.com](https://supabase.com) (call it anything, e.g. `Auth-Practice`).
2. In your Supabase Dashboard, go to **Project Settings → API** and copy your **Project URL** and **anon key**.
3. In **Authentication → Sign In / Providers → Email**, turn **off** "Confirm email" (so a fresh signup can log in immediately, for practice purposes).
4. Copy `.env.example` to a new file named `.env`, and fill in your values:
   ```
   SUPABASE_URL=your_project_url
   SUPABASE_KEY=your_anon_key
   PORT=8000
   ```
5. **Never commit `.env`** — it's already listed in `.gitignore`.

## How to run it

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

The API runs at `http://localhost:8000`. Interactive Swagger docs (with a Bearer-token "Authorize" padlock) are at `http://localhost:8000/docs`.

## API reference

| Method | Path | Auth required? | Description |
|---|---|---|---|
| POST | `/auth/signup` | No | Create a new account |
| POST | `/auth/login` | No | Log in, returns access + refresh token |
| POST | `/auth/logout` | **Yes** | End the session |
| GET | `/public/info` | No | Public, open data |
| GET | `/protected/profile` | **Yes** | Private profile data |
| GET | `/protected/dashboard` | **Yes** | Second protected route (proves the guard is reusable) |
| GET | `/protected/admin-only` | **Yes** + admin email | 403 example — authenticated but not authorized |

## Example: curl flow

```bash
# 1. Sign up
curl -i -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
# -> 201

# 2. Log in
curl -i -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
# -> 200, returns access_token

# 3. Call a protected route with the token
curl -i http://localhost:8000/protected/profile \
  -H "Authorization: Bearer <PASTE_YOUR_ACCESS_TOKEN_HERE>"
# -> 200, your user details

# 4. Tamper with the token (change one character) and try again
# -> 401 Invalid or expired token
```

## Swagger UI screenshot

The screenshots below show the Auth API's Swagger docs (title, Authorize button, and the `/auth/signup` route), and a successful authenticated call to `GET /protected/profile` returning 200 with the verified user's data — confirming the full signup → login → protected-route flow works end-to-end with a real Supabase project.

![Swagger UI — API overview](swagger_top.png)
![Successful protected route call](swagger_result.png)

## Testing checklist (all verified working with a real Supabase project)

- [x] Server starts and logs "Server running and connected to Supabase"
- [x] `GET /public/info` → 200, no auth needed
- [x] `GET /protected/profile` with no token → 401, `{"detail":"Access token required"}`
- [x] `GET /docs` and `/openapi.json` load correctly
- [x] `securitySchemes` correctly registers `HTTPBearer` in the OpenAPI spec
- [x] `POST /auth/signup` with a real email/password → 201, real Supabase user created
- [x] `POST /auth/login` → 200, returns a real `access_token`
- [x] `GET /protected/profile` with that token → 200, returns the authenticated user's id, email, and created_at
- [x] All 4 protected routes (`/protected/profile`, `/protected/dashboard`, `/auth/logout`, `/protected/admin-only`) have security applied — confirmed via the OpenAPI spec
- [x] Swagger `/docs` shows the Authorize padlock, and "Authorize" + "Try it out" works end-to-end



## 401 vs 403

- **401 Unauthorized** — "I don't know who you are." Returned when no token, a malformed token, or an invalid/expired token is presented. Handled automatically by the `require_user` guard before any route logic runs.
- **403 Forbidden** — "I know exactly who you are, and you still may not." Demonstrated on `/protected/admin-only`: a logged-in user is correctly identified (no 401), but is rejected because their email isn't in the admin list.

## Notes

- **Identity Provider:** Supabase handles password hashing and JWT signing — this project never touches passwords or writes cryptography itself, as required.
- **Auth guard:** `require_user` (a FastAPI dependency built on `HTTPBearer`) is the single reusable guard — it's applied to four different routes with zero duplicated logic, exactly as Stage 4 asks.
- **Secrets:** `SUPABASE_URL` and `SUPABASE_KEY` live only in `.env`, which is git-ignored. `.env.example` documents the required keys without exposing real values.
