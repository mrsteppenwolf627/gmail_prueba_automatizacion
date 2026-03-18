# Gmail Auto-Reply Webhook

Minimal MVP: FastAPI webhook that receives Gmail notifications via Google Cloud Pub/Sub and automatically sends replies using the Gmail API.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Setup OAuth (get refresh token)
python scripts/setup_oauth.py

# 3. Copy .env.example → .env and fill in values
cp .env.example .env

# 4. Test locally
uvicorn api.index:app --reload

# 5. Deploy to Vercel
vercel --prod

# 6. Configure Gmail watch
python scripts/setup_gmail_watch.py https://your-vercel-app.vercel.app
```

## Architecture

```
Gmail inbox → Pub/Sub → FastAPI /api/webhooks/gmail → Gmail API reply
```

**Flow:**
1. Gmail detects new message
2. Gmail API pushes notification to Pub/Sub topic
3. Pub/Sub delivers payload to Vercel webhook
4. Webhook extracts sender, subject, message ID
5. Webhook sends auto-reply via Gmail API
6. Log saved to `/tmp/LOGS_DE_MEMORIA.txt`

## Files

| File | Purpose |
|------|---------|
| `api/index.py` | FastAPI webhook (~120 lines) |
| `scripts/setup_oauth.py` | Get OAuth refresh token |
| `scripts/setup_gmail_watch.py` | Configure Gmail → Pub/Sub |
| `setup_guide.md` | **Complete setup instructions** |
| `requirements.txt` | Python dependencies |
| `vercel.json` | Vercel configuration |
| `.env.example` | Environment variables template |

## Environment Variables

```env
GOOGLE_CLIENT_ID=xxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=xxxx
GOOGLE_REFRESH_TOKEN=xxxx
GMAIL_USER_ID=aitor@aitoralmu.xyz
AUTO_REPLY_BODY=Te he recibido, te contesto en breves.
```

## API Endpoints

### GET /api/health
Health check.
```bash
curl https://your-vercel-app.vercel.app/api/health
# {"status":"ok"}
```

### POST /api/webhooks/gmail
Receive Pub/Sub notifications (auto-called by Pub/Sub).

**Request (from Pub/Sub):**
```json
{
  "message": {
    "data": "eyJoaXN0b3J5SWQiOiAiMTIzNDU2Nzg5MCJ9",
    "messageId": "abc123"
  }
}
```

**Response:**
```json
{"status": "success", "message_id": "xyz789"}
```

## Setup Instructions

See [setup_guide.md](setup_guide.md) for complete step-by-step instructions.

**TL;DR:**
1. Create GCP project + OAuth credentials
2. Enable Gmail API + Pub/Sub API
3. Create Pub/Sub topic + subscription (Push)
4. Run `setup_oauth.py` to get refresh token
5. Set environment variables
6. Deploy to Vercel
7. Run `setup_gmail_watch.py` to activate Gmail watch

## Verification

After setup:
1. Send email to your Gmail account
2. Check Vercel logs: `vercel logs --prod`
3. Verify auto-reply received in sender's inbox

## Logs

Webhook logs to `/tmp/LOGS_DE_MEMORIA.txt` on Vercel:
```
[2024-03-17T10:30:45.123456] Received notification with historyId: 12345
[2024-03-17T10:30:46.234567] Processing message from user@example.com with subject: Hello
[2024-03-17T10:30:47.345678] Auto-reply sent to user@example.com, message id: abc123
```

View in Vercel logs or SSH into function storage.

## Customization

- Change `AUTO_REPLY_BODY` env var to customize reply message
- Modify webhook logic in `api/index.py`
- Add filtering by subject, sender, labels

## Cost

- **Gmail API**: Free (first 1M free calls/month)
- **Pub/Sub**: ~$0.40/GB (first 10GB free/month)
- **Vercel**: Free tier included

## Security

- OAuth 2.0 with refresh tokens (no password storage)
- Credentials stored only in environment variables
- No persistent database (stateless)
- HTTPS only

## Limitations (MVP)

- Single account only (can extend for multi-user)
- No complex rules or conditions
- No retry mechanism (Pub/Sub retries built-in)
- Simple logging only

## License

MIT
