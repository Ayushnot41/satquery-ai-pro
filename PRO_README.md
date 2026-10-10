# Satquery AI Pro

The enhanced BHUVISION workspace preserves the original interface, media, and
README. It adds a Next.js workspace, durable account-owned investigations,
background jobs, authenticated uploads, and clearly labelled demonstrations.

## Run locally (Windows, PowerShell 7)

Requires Python 3.12 or 3.13 and Node.js 22 or newer.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-core.txt -c backend/requirements-lock.txt
npm.cmd ci --prefix frontend
npm.cmd run build --prefix frontend
.\scripts\start-pro.ps1 -Production
```

Open http://127.0.0.1:3010 and choose **Explore the demo workspace**. The API
runs on loopback port 8010 and a separate worker executes queued investigations.
`-Production` selects the optimized frontend build; it does not configure
production authentication. Run `scripts/stop-pro.ps1` before rebuilding or
restarting. Logs and verified process IDs are in `.runtime/`.

For persistent accounts, register locally instead of using a demo session.
Guest sessions expire after one hour; keep the same session to revisit its
history. Local SQLite data lives in `backend/data/satquery-pro.db`; uploaded
imagery is in `backend/data/uploads`. Back up both while the services are stopped.
Keep the same `AUTH_PEPPER` across restarts; changing it invalidates sessions.

Copy `.env.pro.example` to `backend/.env` for local configuration and replace
placeholder secrets. Do not commit environment files, databases, or uploads.
Backend settings read `backend/.env` because the launcher sets that working
directory. The Docker Compose workflow reads the root `.env` instead.

## Temporary public demo

With the official Cloudflare `cloudflared` CLI already installed:

```powershell
.\scripts\start-preview.ps1
Get-Content .runtime/preview-url.txt
```

This stops the saved local service instances, starts a temporary HTTPS tunnel,
and launches the optimized app in explicit **preview** mode. The preview uses
a separate SQLite database and random authentication secret under
`.runtime/public-preview`. It accepts guest sessions and sample investigations
only; account creation, sign-in, verification, and uploads are blocked. CORS
allows only the exact HTTPS preview origin, cookies are secure, development
codes are disabled, and real vision providers cannot run in preview mode.

The URL changes when the tunnel restarts. The computer, application, worker,
and tunnel must remain running. This is a demonstration link, not durable
production hosting. Cloudflare Quick Tunnels have no uptime guarantee and a
200 concurrent-request limit; see the [official limitations](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/).
Stop all saved services and the tunnel with `scripts/stop-pro.ps1`.

## Full-service deployment

Use `compose.pro.yml` and the `.pro` Dockerfiles. They deploy PostgreSQL, the
Python API, a separate worker, and the standalone frontend. Preserve the
`database` and `imagery` volumes. Only the frontend is exposed, on loopback
3010; place an HTTPS reverse proxy in front of it. Do not expose PostgreSQL or
the API directly. Use a hosting account owned by **Ayushnot41** and a free plan
that actually supports Python/rasterio, persistent storage, and a worker.
Cloudflare Workers/Sites alone cannot run this Python raster stack.

```powershell
# Set real secrets and provider settings in the ignored root .env first.
docker compose --env-file .env -f compose.pro.yml config --quiet
docker compose --env-file .env -f compose.pro.yml up -d --build
```

Required public configuration: `ENVIRONMENT=production`, a random
`AUTH_PEPPER` of at least 32 characters, `COOKIE_SECURE=true`,
`ALLOW_DEMO_GUEST=false`, `DEVELOPMENT_VERIFICATION_CODES=false`, and exact
HTTPS `CORS_ORIGINS`. Startup rejects insecure public settings. Configure
SMTP for email verification/password reset, or a valid Google client ID for
Google sign-in. Optional phone verification requires Twilio. Production
investigations require a verified account.

Google and phone are independent signup/sign-in choices. Phone-only accounts do
not need email. SMS uses Twilio Verify and stays disabled until `SMS_ENABLED=true`
and a Verify service plus credentials are configured. See
[the step-by-step authentication and free preview guide](docs/AUTHENTICATION_SETUP.md).

For analysis of uploaded imagery, set `VLM_BACKEND=gateway` and a valid
`OPENROUTER_API_KEY`, or configure the supported vLLM endpoint. Provider
failures return an error instead of a fabricated successful answer. Demo
mode uses synthetic scenarios; its confidence values and conclusions are
illustrative, not scientific validation. Unreferenced images do not acquire
invented geographic coordinates. Pixel-change comparisons require aligned
imagery and are not a substitute for validated remote-sensing measurements.

Do not run schema-changing upgrades without backing up the database and
imagery. The current schema is initialized on first boot, with a process lock
for simultaneous API/worker startup. Future schema changes need explicit
migrations; `create_all` does not migrate existing columns.

## Verification

```powershell
Push-Location backend
..\.venv\Scripts\python.exe -m pytest tests -q
Pop-Location
npm.cmd run typecheck --prefix frontend
npm.cmd run build --prefix frontend
npm.cmd audit --prefix frontend --omit=dev
.\.venv\Scripts\python.exe scripts/verify_preservation.py
```

See `docs/VERIFICATION.md` for the actual checks, remaining external
dependencies, and deployment status. Passing checks do not guarantee the
absence of all defects or establish the scientific accuracy of model output.
