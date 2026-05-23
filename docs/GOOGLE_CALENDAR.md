# Google Calendar integration — setup

AI Planner reads and writes events in your Google Calendar. Setup
takes ~5 minutes and is done once.

## 1. Create the OAuth client

1. Open <https://console.cloud.google.com/> and create (or pick) a
   project.
2. **APIs & Services → Library** → search for **Google Calendar API**
   → click **Enable**.
3. **APIs & Services → OAuth consent screen** →
   - User type: **External**
   - Fill in App name, support email, developer email.
   - Scopes: skip (we request them at runtime).
   - **Test users**: add your own Google email (required while the app
     is in "Testing" mode).
4. **APIs & Services → Credentials → Create credentials → OAuth client ID**:
   - Application type: **Web application**
   - Name: `AI Planner` (anything).
   - **Authorized redirect URIs** — add **exactly**:
     ```
     http://localhost:8000/api/v1/google/callback
     ```
   - Click **Create**. Copy the **Client ID** and **Client Secret**.

## 2. Wire it into `.env`

```env
GOOGLE_CLIENT_ID=<your client id>.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=<your client secret>
# leave the rest at the defaults
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/google/callback
GOOGLE_POST_AUTH_REDIRECT=http://localhost:3000/settings?google=connected
```

Restart the stack:

```bash
docker compose -f infra/docker/docker-compose.yml restart api
```

## 3. Connect your account

1. Open <http://localhost:3000/settings>.
2. The **Google Calendar** section should show "Не подключено" with
   the **Connect Google Calendar** button enabled.
3. Click it — you'll be redirected to Google's consent screen, grant
   access, and end up back on Settings with status "Подключено".

## 4. Use it

- **Calendar** tab — shows events from your Google Calendar in
  Day/Week views.
- **AI план → Google** button on `/calendar` — schedules your open
  tasks with the local greedy planner (uses urgency/importance from
  the Eisenhower matrix; run **Sort with AI** on `/matrix` first to
  involve Ollama / OpenAI) and creates the resulting time blocks as
  events in your Google Calendar.

## Troubleshooting

- **`redirect_uri_mismatch`** — the redirect URI in the Google
  console must match `GOOGLE_REDIRECT_URI` byte-for-byte
  (including `http`/`https`, port, trailing slash).
- **`access_denied`** — your Google account must be in the **Test
  users** list while the OAuth consent screen is in "Testing" mode.
- **Tokens stop working** — click **Disconnect** in Settings and
  reconnect. The refresh token is only issued the first time; we
  always send `prompt=consent` so reconnecting will provide a new one.
