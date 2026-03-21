#!/usr/bin/env python3
"""
One-time script to generate a Google OAuth2 refresh token.
Run this locally once, then store the refresh token as a GitHub secret.

Usage:
  1. Go to Google Cloud Console -> APIs & Services -> Credentials
  2. Create an OAuth 2.0 Client ID (Desktop app type)
  3. Download the JSON or note the Client ID and Client Secret
  4. Run: python get_refresh_token.py --client-id YOUR_ID --client-secret YOUR_SECRET
  5. It opens a browser, you log in and authorize
  6. Copy the printed refresh token into GitHub secret GOOGLE_REFRESH_TOKEN
"""

import argparse
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/drive']


def main():
    parser = argparse.ArgumentParser(description="Get Google OAuth2 refresh token")
    parser.add_argument("--client-id", required=True)
    parser.add_argument("--client-secret", required=True)
    args = parser.parse_args()

    client_config = {
        "installed": {
            "client_id": args.client_id,
            "client_secret": args.client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }

    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    creds = flow.run_local_server(port=0, access_type='offline', prompt='consent')

    print("\n" + "=" * 60)
    print("SUCCESS! Copy this refresh token to GitHub secrets:")
    print("=" * 60)
    print(f"\nGOOGLE_REFRESH_TOKEN={creds.refresh_token}")
    print(f"\n(Also store GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)")
    print("=" * 60)


if __name__ == "__main__":
    main()
