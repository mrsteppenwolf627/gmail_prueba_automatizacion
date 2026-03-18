#!/usr/bin/env python3
"""
OAuth 2.0 setup script to obtain and store refresh token.

Run this once locally:
  1. Download credentials.json from GCP Console
  2. Place in project root
  3. python scripts/setup_oauth.py
  4. Copy refresh_token to .env as GOOGLE_REFRESH_TOKEN
"""

import json
import os
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
CREDENTIALS_FILE = 'credentials.json'


def setup_oauth():
    """Obtain refresh token via OAuth 2.0 browser flow."""
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"Error: {CREDENTIALS_FILE} not found in project root")
        print("1. Go to https://console.cloud.google.com")
        print("2. Create OAuth 2.0 Client (Desktop app)")
        print("3. Download as credentials.json")
        return

    flow = InstalledAppFlow.from_client_secrets_file(
        CREDENTIALS_FILE,
        scopes=SCOPES,
        redirect_uri='http://localhost:8080/'
    )

    creds = flow.run_local_server(port=8080, open_browser=True)

    print("\n" + "=" * 60)
    print("SUCCESS: OAuth setup complete!")
    print("=" * 60)
    print(f"\nRefresh Token: {creds.refresh_token}")
    print("\nAdd this to your .env file:")
    print(f"GOOGLE_REFRESH_TOKEN={creds.refresh_token}")
    print("\nAlso add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET from credentials.json")


if __name__ == '__main__':
    setup_oauth()
