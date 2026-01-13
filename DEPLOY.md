# Streamlit Cloud Deployment Guide

## Quick Setup (20 minutes)

---

## Step 1: Google OAuth Credentials (NEW!)

### Create OAuth Client ID

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project (or create one)
3. Go to **APIs & Services** → **Credentials**
4. Click **Create Credentials** → **OAuth client ID**
5. Application type: **Web application**
6. Name: `Personal Finance App`
7. Authorized redirect URIs:
   - For local: `http://localhost:8501`
   - For production: `https://your-app-name.streamlit.app`
8. Click **Create**
9. Copy the **Client ID** and **Client Secret**

### Configure OAuth Consent Screen

1. Go to **OAuth consent screen**
2. User type: **External**
3. Fill in App name, User support email
4. Add scopes: `email`, `profile`, `openid`
5. Add test users (your email addresses)
6. Save

---

## Step 2: Create Google Cloud Service Account

*(Same as before - for Sheets storage)*

1. Go to "IAM & Admin" → "Service Accounts"
2. Click "Create Service Account"
3. Name: `personal-finance-app`
4. Create Key → JSON → Download

---

## Step 3: Create Google Sheet

1. Create new spreadsheet: "Personal Finance Data"
2. Share with service account email (Editor access)
3. Copy the spreadsheet URL

---

## Step 4: Deploy to Streamlit Cloud

```bash
git add .
git commit -m "Add Google OAuth support"
git push origin main
```

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Deploy your repo with `src/app.py`

---

## Step 5: Configure Secrets

In Streamlit Cloud: **Settings** → **Secrets**

```toml
# Cookie encryption key
cookie_key = "your-random-secret-key-here-make-it-long-and-random"

# Google OAuth
[google_oauth]
client_id = "123456789.apps.googleusercontent.com"
client_secret = "GOCSPX-your-secret"
redirect_uri = "https://your-app-name.streamlit.app"

# Authorized for joint view
[authorized_users]
joint_view = ["pablo@gmail.com", "masha@gmail.com"]

# Fallback password (optional)
password_hash = "your-hash-here"

# Google Sheet URL
spreadsheet_url = "https://docs.google.com/spreadsheets/d/YOUR_ID/edit"

# Service account (paste entire JSON content)
[gcp_service_account]
type = "service_account"
project_id = "..."
# ... rest of JSON fields
```

---

## How It Works

### User Flow
```
1. User opens app → sees "Sign in with Google" button
2. User clicks → Google OAuth popup
3. User logs in → app gets email + name
4. App creates user folder: pablo_parreno (from email)
5. User sees ONLY their data
6. Cookie saved → no re-login for 30 days
```

### Data Isolation
- Each user's data in separate worksheet: `{user}_transactions`
- User can only access their own worksheet
- Joint view only for authorized emails

---

## Local Testing

### Without OAuth (password mode)
```bash
./run.sh
# Use password: finance123
```

### With OAuth
Create `.streamlit/secrets.toml` with your credentials, then:
```bash
./run.sh
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| OAuth redirect error | Check redirect_uri matches exactly |
| "Access blocked" | Add yourself as test user in OAuth consent |
| Cookie not saving | Check cookie_key is set |
| Can't see data | Check spreadsheet sharing with service account |
