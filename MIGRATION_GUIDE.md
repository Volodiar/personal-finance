# Complete Migration Guide (Updated)

## Overview

This guide walks you through setting up Google OAuth and migrating your data to Google Sheets.

---

## Part 1: Google OAuth Setup (10 min)

### 1.1 Create OAuth Client ID

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project: **personalfinance** 
3. Go to **APIs & Services** → **Credentials**
4. Click **Create Credentials** → **OAuth client ID**

### 1.2 Configure OAuth Client

```
Application type: Web application
Name: Personal Finance OAuth

Authorized redirect URIs:
  - http://localhost:8501
  - https://YOUR-APP-NAME.streamlit.app
```

5. Click **Create**
6. **Save** Client ID and Client Secret

### 1.3 Configure Consent Screen

1. Go to **OAuth consent screen**
2. App name: `Personal Finance`
3. Add scopes: `email`, `profile`, `openid`
4. Add **test users**: your email addresses
5. Save

---

## Part 2: Update Streamlit Cloud Secrets (5 min)

Go to [share.streamlit.io](https://share.streamlit.io) → Your app → **Settings** → **Secrets**

```toml
# Cookie encryption
cookie_key = "your-random-secret-key-32-chars-or-more"

# Google OAuth
[google_oauth]
client_id = "YOUR_CLIENT_ID.apps.googleusercontent.com"
client_secret = "YOUR_CLIENT_SECRET"
redirect_uri = "https://YOUR-APP.streamlit.app"

# Keep existing secrets
spreadsheet_url = "https://docs.google.com/spreadsheets/d/YOUR_ID/edit"

[gcp_service_account]
# ... your existing service account ...
```

---

## Part 3: Migrate Your Data (10 min)

### Run Migration Script Locally

```bash
cd /Users/pabloparrenolaporta/Documents/GitHub/personal-finance

# Run migration tool
streamlit run src/migrate_data.py
```

### Migration Steps:

1. Enter your Google email (the one you'll use to log in)
2. Review detected local data (from /data/ folders)
3. Configure names and emojis for each profile
4. Click "Start Migration"
5. Verify data was transferred correctly

---

## Part 4: Push and Deploy (5 min)

```bash
git add .
git commit -m "Multi-tenant with OAuth and Google Sheets"
git push origin main
```

Wait for Streamlit Cloud to redeploy (~2-3 min).

---

## Part 5: Test

1. Open your app URL
2. Click "Sign in with Google"
3. Select your Google account
4. You should see your profiles (Pablo, Masha, etc.)
5. Click a profile → verify your transactions are there

---

## Architecture Summary

```
Account User: pablo@gmail.com
  └── hash: "a1b2c3d4"
  └── Data Users:
      ├── Pablo → worksheet: a1b2c3d4_pablo
      └── Masha → worksheet: a1b2c3d4_masha

Account User: john@gmail.com (separate)
  └── hash: "x7y8z9w0"
  └── Data Users:
      └── Family → worksheet: x7y8z9w0_family
```

Each account sees ONLY their own data users!
