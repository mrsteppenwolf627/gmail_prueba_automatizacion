#!/usr/bin/env python3
"""
Test the webhook locally with a mock Pub/Sub message.

Run this while the app is running locally:
  uvicorn api.index:app --reload

In another terminal:
  python test_webhook.py
"""

import json
import base64
import requests

# Local webhook URL
WEBHOOK_URL = "https://gmail-auto-reply-webhook.vercel.app/api/webhooks/gmail"


def test_webhook():
    """Send a test Pub/Sub message to the webhook."""
    # Create a mock Pub/Sub payload
    message_data = {
        "historyId": "1234567890"
    }

    # Encode as base64 (Pub/Sub format)
    encoded = base64.b64encode(
        json.dumps(message_data).encode()
    ).decode()

    # Create Pub/Sub message format
    payload = {
        "message": {
            "data": encoded,
            "messageId": "test-message-123"
        }
    }

    print(f"Testing webhook at {WEBHOOK_URL}")
    print(f"Payload: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(WEBHOOK_URL, json=payload)
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Body: {response.json()}")

        if response.status_code == 200:
            print("\n✓ Webhook received the test message successfully!")
        else:
            print(f"\n✗ Webhook returned status {response.status_code}")

    except requests.exceptions.ConnectionError:
        print("\n✗ Could not connect to webhook.")
        print("Make sure the app is running: uvicorn api.index:app --reload")
    except Exception as e:
        print(f"\n✗ Error: {e}")


def test_health():
    """Test the health endpoint."""
    health_url = "http://localhost:8000/api/health"

    print(f"Testing health endpoint at {health_url}")

    try:
        response = requests.get(health_url)
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {response.json()}")

        if response.status_code == 200:
            print("✓ Health check passed!")
        else:
            print(f"✗ Health check failed with status {response.status_code}")

    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to server.")
        print("Make sure the app is running: uvicorn api.index:app --reload")
    except Exception as e:
        print(f"✗ Error: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("Gmail Webhook Test")
    print("=" * 60)
    print()

    test_health()
    print()
    print("-" * 60)
    print()
    test_webhook()
