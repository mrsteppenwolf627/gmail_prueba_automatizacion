# Gmail Auto-Reply Setup Guide

Complete step-by-step guide to deploy the Gmail auto-reply webhook.

## Prerequisites
- Google Cloud Platform (GCP) account
- Gmail account
- Python 3.11+
- Vercel account
- `gcloud` CLI installed

## Step 1: Create GCP Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Click "Select a Project" → "New Project"
3. Name it "Gmail Auto-Reply" (or your preference)
4. Click "Create"
5. Wait for project creation to complete

## Step 2: Enable Required APIs

1. In the GCP Console, go to "APIs & Services" → "Library"
2. Search for **Gmail API**
   - Click on it
   - Click "Enable"
3. Search for **Cloud Pub/Sub API**
   - Click on it
   - Click "Enable"

## Step 3: Create OAuth 2.0 Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. If prompted, click "Configure Consent Screen"
   - Choose "External" → "Create"
   - Fill in App Name: "Gmail Auto-Reply"
   - Add your email as test user
   - Click "Save and Continue" through all screens
4. Back to Credentials:
   - Click "Create Credentials" → "OAuth client ID"
   - Choose "Desktop application"
   - Click "Create"
5. Click the download icon (↓) to download `credentials.json`
6. Save `credentials.json` in your project root

## Step 4: Get Refresh Token

1. Copy `credentials.json` to your project root
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run OAuth setup:
   ```bash
   python scripts/setup_oauth.py
   ```
4. Browser will open → authorize the app
5. Copy the `Refresh Token` printed in terminal
6. Copy `client_id` and `client_secret` from `credentials.json`

## Step 5: Create Pub/Sub Topic & Subscription

1. Go to "Pub/Sub" in GCP Console
2. Click "Create Topic"
   - Name: `gmail-notifications`
   - Click "Create Topic"
3. Open the topic → go to "Subscriptions" tab
4. Click "Create Subscription"
   - Name: `gmail-webhook-sub`
   - Delivery type: **Push**
   - Webhook URL: `https://your-vercel-app.vercel.app/api/webhooks/gmail`
   - Click "Create"
5. Go back to topic "gmail-notifications"
6. Click "Permissions" (top right)
7. Add new principal: `gmail-api-push@system.gserviceaccount.com`
8. Give role: **Pub/Sub Publisher**
9. Click "Save"

## Step 6: Set Environment Variables

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with:
   ```
   GOOGLE_CLIENT_ID=your_client_id_from_credentials.json
   GOOGLE_CLIENT_SECRET=your_client_secret_from_credentials.json
   GOOGLE_REFRESH_TOKEN=refresh_token_from_setup_oauth.py
   GMAIL_USER_ID=aitor@aitoralmu.xyz
   AUTO_REPLY_BODY=Te he recibido, te contesto en breves.
   ```

## Step 7: Test Locally

```bash
uvicorn api.index:app --reload
```

Should show:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

Test endpoint:
```bash
curl http://localhost:8000/api/health
# {"status":"ok"}
```

## Step 8: Deploy to Vercel

1. Install Vercel CLI:
   ```bash
   npm install -g vercel
   ```

2. Login and deploy:
   ```bash
   vercel login
   vercel --prod
   ```

3. When prompted:
   - "Link to existing project?" → No
   - "Project name?" → gmail-auto-reply (or your choice)
   - Vercel will show deployment URL

4. Add environment variables in Vercel dashboard:
   - Go to Project Settings → Environment Variables
   - Add all variables from .env:
     - `GOOGLE_CLIENT_ID`
     - `GOOGLE_CLIENT_SECRET`
     - `GOOGLE_REFRESH_TOKEN`
     - `GMAIL_USER_ID`
     - `AUTO_REPLY_BODY`

## Step 9: Configure Gmail Watch

1. Update your Pub/Sub subscription with correct webhook URL:
   - Go to Pub/Sub → `gmail-webhook-sub`
   - Click "Edit"
   - Update "Webhook URL" to your Vercel URL:
     ```
     https://your-vercel-app.vercel.app/api/webhooks/gmail
     ```
   - Click "Update"

2. Run Gmail watch setup:
   ```bash
   python scripts/setup_gmail_watch.py https://your-vercel-app.vercel.app
   ```

## Step 10: Test End-to-End

1. From another email account, send an email to your Gmail account
2. Check Vercel logs:
   ```bash
   vercel logs --prod
   ```
3. You should see a response from the webhook
4. Check your inbox → you should have received the auto-reply

## Troubleshooting

### "Permission denied" error
- Make sure `gmail-api-push@system.gserviceaccount.com` has Publisher role on the Pub/Sub topic

### "historyId not found" error
- The watch may not be active. Re-run `python scripts/setup_gmail_watch.py`

### No auto-reply sent
- Check Vercel logs for errors
- Verify environment variables are set in Vercel
- Make sure refresh token is valid

### "Invalid request" on webhook
- Verify the webhook URL in Pub/Sub subscription matches your Vercel deployment
- Check that the subscription is type "Push", not "Pull"

## Monitoring

View logs in real-time:
```bash
vercel logs -f --prod
```

Check auto-reply history:
```bash
vercel env pull  # If needed
# Logs stored in /tmp/LOGS_DE_MEMORIA.txt on Vercel function
```

## Architecture Diagram

```
Gmail Inbox
    ↓
[New email arrives]
    ↓
Gmail API detects change
    ↓
Gmail API → Pub/Sub topic (gmail-notifications)
    ↓
Pub/Sub subscription (Push)
    ↓
POST → https://your-vercel-app.vercel.app/api/webhooks/gmail
    ↓
[FastAPI webhook processes]
    ↓
Gmail API sends auto-reply
    ↓
[Log saved to /tmp/LOGS_DE_MEMORIA.txt]
    ↓
200 OK response
```

## File Structure

```
gmail-auto-reply/
├── api/
│   └── index.py              # FastAPI webhook
├── scripts/
│   ├── setup_oauth.py        # Get refresh token
│   └── setup_gmail_watch.py  # Configure Gmail watch
├── requirements.txt          # Python dependencies
├── vercel.json              # Vercel config
├── .env.example             # Environment template
├── .env                     # Your local env (don't commit)
└── setup_guide.md           # This file
```

## Security Notes

- Never commit `.env` to git
- Keep `credentials.json` local (don't commit)
- Refresh tokens don't expire but rotate periodically (Gmail API handles this)
- The webhook accepts POST from Pub/Sub only
- All logs go to Vercel function storage (ephemeral)

## Next Steps

- Customize `AUTO_REPLY_BODY` with your message
- Add reply delay with a task queue (for future enhancement)
- Monitor email volume in Vercel analytics
- Set up alerts for webhook errors
