# Google, phone signup, and free hosting

Hosting can have no hosting fee while SMS still uses a paid provider. These are separate choices.

## What is implemented

- Google: first successful sign-in creates an account; later sign-ins return to it.
- Phone: enter a number with its country code, request SMS, enter the six-digit code. A new verified number creates an account without email or password. A returning number signs into its existing account.
- Google login uses a browser-bound, single-use nonce and Google's verified subject ID.
- SMS uses Twilio Verify. Challenges are tied to browser, number, purpose, and account. They expire after five minutes, allow five checks, enforce a 30-second resend interval, and limit requests to five per number/account per hour and 100 per workspace per day.
- Existing accounts and sessions remain readable. Phone accounts have a permanent user ID and an opaque internal record key; email is null, not an invented address.
- Verified phone accounts can use the production workspace. Google/email users can attach an unclaimed phone in Account settings.
- Already separate accounts are not automatically merged. Replacing a verified phone and self-service phone-account recovery are not implemented. Do not remove another person's phone binding to resolve a conflict.

## 1. Turn on Google sign-in

1. Sign into https://console.cloud.google.com/ using your own account.
2. Create/select a project. Open Google Auth Platform and complete Branding and Audience.
3. Under Clients, create a Web application client.
4. Add Authorized JavaScript origins `http://localhost` and `http://localhost:3010` for local testing. Add your exact HTTPS site origin when deployed. Do not add paths or `#settings`.
5. Copy the Client ID ending in `.apps.googleusercontent.com`.
6. Add it to `backend/.env` for the Windows launcher:

```dotenv
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
```

7. Restart the normal application and open http://localhost:3010. Click Continue with Google. For an external audience, follow the console's testing/publishing requirements. A public launch also needs appropriate homepage/privacy-policy links and any verification Google requires.

This integration uses a JavaScript callback and backend token verification. It does not need a Client Secret or Gmail inbox access. Basic identity scopes are enough. The temporary sample-only preview disables identity mutations deliberately.

Google accounts with Gmail or a verified hosted Workspace domain can establish email ownership. A third-party email attached to Google is not automatically treated as currently verified for workspace access; verify that email separately or attach a verified phone.

Official guide: https://developers.google.com/identity/gsi/web/guides/get-google-api-clientid

## 2. Turn on Twilio SMS

1. Create/sign into your own Twilio account at https://console.twilio.com/.
2. Open Verify and create one service named Satquery. Set six-digit codes.
3. Configure the destination countries, sender requirements, and fraud protection. Complete the provider's account/trial/billing requirements for real recipients.
4. Copy the Verify Service SID (`VA...`) and create server-side API credentials (`SK...` and secret).
5. Put these only in `backend/.env`:

```dotenv
SMS_ENABLED=true
TWILIO_ACCOUNT_SID=AC...
TWILIO_API_KEY=SK...
TWILIO_API_SECRET=your-secret
TWILIO_VERIFY_SERVICE_SID=VA...
DEVELOPMENT_VERIFICATION_CODES=false
```

6. Restart the normal application. Choose Continue with phone, enter a number such as `+919876543210`, click Send SMS code, and enter the received code.

API key/secret are preferred. Account SID/Auth Token are also supported by the adapter for testing. `TWILIO_FROM` is a legacy setting and is not used by Verify. Never put provider secrets in frontend variables, screenshots, GitHub, or chat.

SMS is billable. Configure provider spending alerts and fraud controls before enabling it. The app's request caps reduce abuse but are not a guaranteed billing cap. Indian domestic messaging may need DLT registration; confirm the route with Twilio.

Official guides: https://www.twilio.com/docs/verify/api and https://www.twilio.com/en-us/guidelines/in/sms

## 3. Run locally

For local HTTP development, keep these in `backend/.env`:

```dotenv
ENVIRONMENT=development
COOKIE_SECURE=false
CORS_ORIGINS=http://localhost:3010,http://127.0.0.1:3010
ALLOW_DEMO_GUEST=false
DEVELOPMENT_VERIFICATION_CODES=false
```

From the project folder in PowerShell 7, run:

```powershell
./scripts/stop-pro.ps1
./scripts/start-pro.ps1 -Production
```

`-Production` selects the optimized frontend build. The `ENVIRONMENT` setting separately controls backend security. Use `http://localhost:3010` for the registered Google origin. Do not run the preview launcher when testing these real identity providers.

Docker deployments read the root `.env`, not `backend/.env`. The Compose file now passes the Verify variables to the backend.

## 4. Share a free preview

Your computer can host the app while Cloudflare supplies a temporary public HTTPS link. There is no hosting or domain purchase, but your existing internet and electricity still have costs.

1. Keep the computer on and connected to the internet.
2. From the project folder, run `./scripts/start-preview.ps1` in PowerShell 7.
3. Copy the printed `https://...trycloudflare.com` link and share it.

The script starts the frontend, API, database access, worker, and tunnel in the background. Read the current link from `.runtime/preview-url.txt`. Stop with `./scripts/stop-pro.ps1`.

The default command is a sample-only demonstration. To test your configured Google/phone registration over a free HTTPS link, use this instead:

```powershell
./scripts/start-preview.ps1 -Accounts
```

This requires the Google or Twilio configuration above. It uses secure production authentication settings, disables guests and local test codes, and stores real test accounts separately in `.runtime/public-accounts`. Add the printed HTTPS origin to your Google client's Authorized JavaScript origins before signing in. Re-add the new origin after any tunnel restart. Follow Google's domain/consent requirements; registration of an arbitrary temporary origin is not guaranteed by this launcher. Twilio is billed normally. Image analysis remains demo mode until you separately configure a real provider.

Cloudflare Quick Tunnels have no uptime guarantee and their address changes after a tunnel restart. The `-Accounts` option is for integration testing; it does not turn Quick Tunnels into supported production hosting. Official documentation: https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/

For real accounts on a public website, use a stable HTTPS origin with your provider registrations and production settings (`ENVIRONMENT=production`, secure cookies, a strong persistent AUTH_PEPPER, explicit HTTPS CORS origin, no guest sessions, no development codes). A free hosting plan must support this project's Python backend, persistent database, shared image storage, and background worker; static website hosting alone cannot host the complete project. No permanent free account-enabled host is configured here.

## Verification boundary

Automated tests use fake provider responses and isolated databases. They cannot confirm that your Google project is published or that a real SMS reaches your phone. Those checks require your configured accounts. No real verification message is sent by the test suite.

No ChatGPT plugin is required for the implementation. An optional provider plugin can help with account setup after you connect it, but cannot waive service charges or perform your personal account verification for you.
