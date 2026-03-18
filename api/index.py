import json
import base64
import os
from datetime import datetime
from email.mime.text import MIMEText
import google.auth
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from google.api_core.exceptions import GoogleAPIError
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Gmail API scope
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']


def get_gmail_service():
    """Build Gmail service with refresh token from environment."""
    refresh_token = os.getenv('GOOGLE_REFRESH_TOKEN')
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET')

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri='https://oauth2.googleapis.com/token',
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES
    )
    creds.refresh(GoogleRequest())
    return build('gmail', 'v1', credentials=creds)


def log_event(message: str):
    """Append log to /tmp/LOGS_DE_MEMORIA.txt"""
    try:
        with open('/tmp/LOGS_DE_MEMORIA.txt', 'a') as f:
            f.write(f"[{datetime.now().isoformat()}] {message}\n")
    except Exception as e:
        print(f"Error logging: {e}")


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/api/webhooks/gmail")
async def gmail_webhook(request: Request):
    """Receive Gmail Pub/Sub notification and send auto-reply."""
    try:
        body = await request.json()
        print(f"RAW BODY RECEIVED: {json.dumps(body)}")

        if 'message' not in body or 'data' not in body['message']:
            print("ERROR: Invalid payload structure")
            return JSONResponse({"error": "Invalid payload"}, status_code=400)

        message_data = base64.b64decode(body['message']['data']).decode('utf-8')
        payload = json.loads(message_data)
        history_id = int(payload.get('historyId'))

        print(f"--- START PROCESSING historyId: {history_id} ---")

        gmail = get_gmail_service()
        user_id = os.getenv('GMAIL_USER_ID', 'me')

        # Get new messages from history
        print(f"Fetching history for user {user_id} starting from {history_id - 1}")
        history = gmail.users().history().list(
            userId=user_id,
            startHistoryId=max(0, history_id - 1)
        ).execute()

        print(f"FULL HISTORY RESPONSE: {json.dumps(history)}")

        messages = []
        if 'history' in history:
            for h in history['history']:
                if 'messagesAdded' in h:
                    for m_added in h['messagesAdded']:
                        msg_id = m_added['message']['id']
                        messages.append(msg_id)
        
        # Fallback: If history doesn't show added messages, get the latest from INBOX
        if not messages:
            print("History was empty, falling back to latest message in INBOX...")
            list_res = gmail.users().messages().list(userId=user_id, q="label:INBOX", maxResults=1).execute()
            if 'messages' in list_res:
                messages = [list_res['messages'][0]['id']]

        if not messages:
            print("CRITICAL: No messages found even in fallback.")
            return JSONResponse({"status": "no_messages"}, status_code=200)

        msg_id = messages[0]
        print(f"Processing message ID: {msg_id}")
        message = gmail.users().messages().get(userId=user_id, id=msg_id, format='full').execute()
        
        # Get headers for reply
        headers = message['payload']['headers']
        from_addr = next((h['value'] for h in headers if h['name'] == 'From'), "")
        
        # CHECK IF ALREADY REPLIED OR IF IT IS FROM US
        if user_id in from_addr or "me" in from_addr:
            print(f"Skipping self-sent message from: {from_addr}")
            return JSONResponse({"status": "skipped_self"}, status_code=200)

        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), None)
        msg_id_header = next((h['value'] for h in headers if h['name'] == 'Message-ID'), None)

        log_event(f"Processing message from {from_addr} with subject: {subject}")

        # Build reply
        reply_body = os.getenv('AUTO_REPLY_BODY', 'Te he recibido, te contesto en breves.')

        reply_msg = MIMEText(reply_body)
        reply_msg['To'] = from_addr
        reply_msg['Subject'] = f"Re: {subject}"
        if msg_id_header:
            reply_msg['In-Reply-To'] = msg_id_header
            reply_msg['References'] = msg_id_header

        raw = base64.urlsafe_b64encode(reply_msg.as_bytes()).decode()

        # Send reply
        sent = gmail.users().messages().send(
            userId=user_id,
            body={'raw': raw}
        ).execute()

        log_event(f"Auto-reply sent to {from_addr}, message id: {sent['id']}")

        return JSONResponse({"status": "success", "message_id": sent['id']}, status_code=200)

    except GoogleAPIError as e:
        log_event(f"Gmail API error: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=500)
    except Exception as e:
        log_event(f"Error: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=500)
