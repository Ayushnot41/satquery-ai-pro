# Verification record — 2026-10-10

## Independent Google and phone signup follow-up

- Full backend suite: **119 passed**, six expected warnings. The 29 focused
  authentication/regression tests also passed after retaining the original route
  wrappers for compatibility.
- Optimized Next.js build and TypeScript validation passed.
- Browser: a local-only synthetic OTP created a phone-only account, issued a
  session, and displayed Phone verified / Email not required. No browser console
  errors were observed. The 390 px viewport had no horizontal document overflow.
  Screenshot: `phone-signup-verified.jpg` (test account; no real SMS).
- Preservation check passes. Added PostgreSQL CI coverage for phone signup,
  sessions, and legacy Google subject lookup; see the current CI run for its result.
- Google and Twilio credentials are not configured. External Google sign-in and
  real SMS delivery remain untested and inactive. Mock-provider tests do not
  establish live provider readiness. The public tunnel remains sample-only.
- SMS paid delivery defaults off. Existing accounts/session references remain
  readable; pending OTPs from the previous implementation must be requested again.
- Self-service phone replacement/recovery and merging separate accounts are not
  implemented. Do not claim a fully audited production identity service.

Setup: `AUTHENTICATION_SETUP.md`.

## Confirmed locally

- Backend: **103 passed**, six warnings (Starlette/AnyIO deprecation and expected
  missing georeferencing on synthetic PNG fixtures).
- Frontend: TypeScript checking and final Next.js 15.5.27 optimized build passed.
- Production npm audit: **0 vulnerabilities**. Full development audit: **7**
  transitive Tailwind 3 toolchain advisories (five high, two moderate). The
  suggested aggregate remedy changes Tailwind to version 4 and needs a separate
  compatibility migration; it was not force-applied. These packages are excluded
  from the production dependency audit, but remain a build-tool limitation.
- Preservation: all 253 original files retained; 26 original media/README files
  byte-preserved; 10 cockpit screens and 102 functions retained. Git attributes
  prevent cross-platform newline conversion of the preserved files.
- Browser: demo session; completed single-image, two-date, and optical/SAR jobs;
  saved history after reload; valid two-page PDF download; all 13 main navigation
  screens, including the original embedded consoles. Desktop 1440 px and mobile
  390 px report layouts checked; no horizontal body overflow.
- The browser found invalid original public PNG placeholders shadowing the real
  SAR sample. Final routing serves the canonical assets first; all three affected
  URLs were rechecked locally as decodable 512 × 512 PNGs. Original files remain
  unchanged. No new browser console error was observed after the clean restart
  during the workflow/screen checks; an earlier rebuild caused a stale-chunk error.
- Report route: 15.9 kB, 119 kB initial JavaScript including shared chunks. PDF
  libraries load only when exporting. One exported sample PDF was 8.1 MB;
  report compression is not claimed.
- API, worker, optimized frontend, and Cloudflare tunnel run as hidden processes.
  The API readiness endpoint confirms database connectivity.

## Public preview

Temporary URL issued by Cloudflare:
https://frozen-protecting-listings-amber.trycloudflare.com

The tunnel reported a registered connection. Preview mode uses a separate
database, secure cookies, an exact HTTPS origin, and synthetic sample access;
accounts, identity mutations, and uploads are blocked. The preview landing screen
was verified locally and captured in `preview-verified.jpg`.

The restarted HTTPS URL was opened successfully in the browser, with an
active demo workspace and no console errors. The earlier automatic-review
usage-limit failure no longer blocks browser access. The optical/SAR workflow completed over HTTPS; all five report images loaded,
keyboard workflow selection worked, and the browser console contained no errors. This link depends on the workstation and tunnel remaining
running; it is not permanent production hosting. `.runtime/preview-url.txt`
contains the current URL after any restart.

## Source recovery

The D: parent Git metadata was temporarily unavailable after an interruption.
The verified source was first published from `scratch/publication` without
changing the original managed-worktree pointer. Access to the original metadata
subsequently recovered; the original history and the published source history
are retained together. The original baseline commit is
`8d26496c130127dba93dad55fb7a88f418fe3d84`. All preserved-file hashes were
checked against the publication snapshot with zero mismatches; the staged
credential-pattern scan was clean.

## External dependencies and remaining limits

- Permanent hosting is blocked: the available Cloudflare credential returns
  HTTP 403 for both identity and account verification. No deployment was made to
  that unverified account. No other supported Python hosting credential was found.
- Local Docker engine is unavailable. PostgreSQL integration is included in
  `pro-quality.yml` via `scripts/verify_postgres.py` passed in GitHub Actions on
  commit `5e5d2a0`, including PostgreSQL startup, ownership, persistence, and worker
  completion. The frontend build and production audit also passed remotely.
  Local SQLite concurrency, ownership, cancellation, and persistence tests pass.
- Real uploaded-image inference requires a configured and verified gateway or
  vLLM provider. No external vision-provider call was tested with real credentials.
- Google, SMTP, and SMS integration code is present, but live provider integration
  requires the owner's configuration. The public preview deliberately disables it.
- Voice transcription is not implemented; its control is visibly unavailable,
  rather than pretending to record. The former decorative language toggle is
  replaced with a text-query label.
- Legacy surveillance, defense, disaster, and benchmark panels are demonstrations,
  even where preserved original content resembles operational telemetry. The
  shell and reports label this limitation. No scientific-accuracy, calibrated
  confidence, actual government access, or zero-defect claim is made.

See `../PRO_README.md` for startup, shutdown, configuration, backup, and deployment.

## Published source and CI

Private repository: https://github.com/Ayushnot41/satquery-ai-pro

The Pro quality workflow passed on the published source snapshot:
https://github.com/Ayushnot41/satquery-ai-pro/actions/runs/38058644357

The original lint job reported one false positive: it inferred the optional
CPU fallback class inside a branch guarded by TORCH_AVAILABLE. A line-scoped
annotation documents the torch.nn.Module-only call; runtime behavior is unchanged.
All three workflows passed on commit `6313233`: Pro quality and preservation,
CI Test Suite, and Pylint.

Final Pro quality run (including PostgreSQL):
https://github.com/Ayushnot41/satquery-ai-pro/actions/runs/38058801822

Final lint run:
https://github.com/Ayushnot41/satquery-ai-pro/actions/runs/38058801801
