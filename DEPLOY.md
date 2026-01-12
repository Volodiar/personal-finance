# Streamlit Cloud Deployment Guide

## Quick Setup (15 minutes)

### Step 1: Create Google Cloud Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable **Google Sheets API** and **Google Drive API**:
   - Go to "APIs & Services" → "Enable APIs"
   - Search and enable both APIs
4. Create Service Account:
   - Go to "IAM & Admin" → "Service Accounts"
   - Click "Create Service Account"
   - Name: `personal-finance-app`
   - Click "Create and Continue"
   - Skip the optional steps, click "Done"
5. Create Key:
   - Click on the service account you just created
   - Go to "Keys" tab
   - Click "Add Key" → "Create new key" → "JSON"
   - Download the JSON file (keep it safe!)

### Step 2: Create Google Sheet

1. Go to [Google Sheets](https://sheets.google.com)
2. Create a new blank spreadsheet
3. Name it: `Personal Finance Data`
4. **Share the sheet** with your service account email:
   - Click "Share" button
   - Paste the service account email (from the JSON file, looks like: `xxx@xxx.iam.gserviceaccount.com`)
   - Give "Editor" access
5. Copy the spreadsheet URL

### Step 3: Push Code to GitHub

```bash
# In your project directory
git add .
git commit -m "Add cloud deployment support"
git push origin main
```

### Step 4: Deploy to Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click "New app"
4. Select your repository and `src/app.py`
5. Click "Deploy"

### Step 5: Configure Secrets

In Streamlit Cloud dashboard:

1. Go to your app → "Settings" → "Secrets"
2. Add the following (replace with your values):

```toml
# Password hash (generate with command below)
password_hash = "YOUR_HASH_HERE"

# Google Sheet URL
spreadsheet_url = "https://docs.google.com/spreadsheets/d/YOUR_ID/edit"

# Paste your entire service account JSON here:
[gcp_service_account]
type = "service_account"
project_id = "your-project"
private_key_id = "abc123"
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "personal-finance@your-project.iam.gserviceaccount.com"
client_id = "123456789"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
```

### Generate Password Hash

Run this command to generate your password hash:

```bash
python3 -c "import hashlib; print(hashlib.sha256(b'YOUR_PASSWORD').hexdigest())"
```

Replace `YOUR_PASSWORD` with your desired password.

---

## Testing Locally

For local development without Google Sheets:

1. The app will use local CSV storage
2. Default password: `finance123`

To test with Google Sheets locally:

1. Create `.streamlit/secrets.toml` (copy from `.streamlit/secrets.toml.template`)
2. Fill in your credentials
3. Run: `streamlit run src/app.py`

---

## Access Your App

After deployment, your app will be available at:
```
https://your-app-name.streamlit.app
```

Access from any device (phone, tablet, computer)!
