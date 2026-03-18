#!/usr/bin/env python3
"""
Gmail watch setup script.

Run this once after deploying to Vercel:
  1. Deploy to Vercel: vercel --prod
  2. Copy your Vercel URL
  3. python scripts/setup_gmail_watch.py <vercel_url>

This configures Gmail to push notifications to your webhook via Pub/Sub.
"""

import sys
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv(override=True)

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']


def get_gmail_service():
    """Build Gmail service with refresh token from .env"""
    refresh_token = os.getenv('GOOGLE_REFRESH_TOKEN')
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET')

    if not all([refresh_token, client_id, client_secret]):
        raise ValueError("Missing GOOGLE_REFRESH_TOKEN, GOOGLE_CLIENT_ID, or GOOGLE_CLIENT_SECRET in .env")

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri='https://oauth2.googleapis.com/token',
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES
    )
    creds.refresh(Request())
    return build('gmail', 'v1', credentials=creds)


def setup_gmail_watch(webhook_url):
    """Configure Gmail to watch inbox and push to Pub/Sub"""
    gmail = get_gmail_service()
    user_id = os.getenv('GMAIL_USER_ID', 'me')

    # Topic name must match your Pub/Sub setup
    project_id = os.getenv('GOOGLE_PROJECT_ID')
    if not project_id:
        raise ValueError("Missing GOOGLE_PROJECT_ID in .env")

    topic_name = f'projects/{project_id}/topics/gmail-notifications'
    print(f"DEBUG: Using project_id: {project_id}")
    print(f"DEBUG: Using topic_name: {topic_name}")
    print(f"DEBUG: Using client_id: {os.getenv('GOOGLE_CLIENT_ID')}")

    try:
        result = gmail.users().watch(
            userId=user_id,
            body={
                'topicName': topic_name,
                'labelIds': ['INBOX']
            }
        ).execute()

        print("\n" + "=" * 60)
        print("SUCCESS: Gmail watch configured!")
        print("=" * 60)
        print(f"\nWatch ID: {result.get('historyId')}")
        print(f"Gmail will now push inbox changes to Pub/Sub topic: {topic_name}")
        print(f"\nMake sure your Pub/Sub subscription points to:")
        print(f"  {webhook_url}/api/webhooks/gmail")

    except Exception as e:
        print(f"Error setting up watch: {e}")
        print("\nMake sure:")
        print("1. .env file has valid GOOGLE_REFRESH_TOKEN, CLIENT_ID, CLIENT_SECRET")
        print("2. Pub/Sub topic 'gmail-notifications' exists in your GCP project")
        print("3. gmail-api-push@system.gserviceaccount.com has Publisher role on topic")


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python scripts/setup_gmail_watch.py <vercel_url>")
        print("Example: python scripts/setup_gmail_watch.py https://my-app.vercel.app")
        sys.exit(1)

    webhook_url = sys.argv[1].rstrip('/')
    setup_gmail_watch(webhook_url)
