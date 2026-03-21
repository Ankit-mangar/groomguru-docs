#!/usr/bin/env python3
"""
Upload .docx files to a Google Drive folder as native Google Docs.

Uses OAuth2 refresh token (your personal Google account) instead of
a service account, avoiding the zero-quota limitation.

Usage:
  python upload_to_drive.py --folder-id FOLDER_ID --docs-dir ./docs

Environment:
  GOOGLE_CLIENT_ID      — OAuth2 client ID
  GOOGLE_CLIENT_SECRET  — OAuth2 client secret
  GOOGLE_REFRESH_TOKEN  — Refresh token from get_refresh_token.py
"""

import argparse
import os
import sys

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/drive']
MIME_DOCX = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
MIME_GDOC = 'application/vnd.google-apps.document'


def get_drive_service():
    client_id = os.environ.get('GOOGLE_CLIENT_ID')
    client_secret = os.environ.get('GOOGLE_CLIENT_SECRET')
    refresh_token = os.environ.get('GOOGLE_REFRESH_TOKEN')

    if not all([client_id, client_secret, refresh_token]):
        print("ERROR: Missing GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, or GOOGLE_REFRESH_TOKEN")
        sys.exit(1)

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri='https://oauth2.googleapis.com/token',
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES,
    )
    creds.refresh(Request())
    return build('drive', 'v3', credentials=creds)


def find_existing_file(service, folder_id, name):
    """Find an existing Google Doc by name in the folder."""
    query = (
        f"name='{name}' and '{folder_id}' in parents "
        f"and mimeType='{MIME_GDOC}' and trashed=false"
    )
    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get('files', [])
    return files[0]['id'] if files else None


def upload_or_update(service, folder_id, local_path):
    """Upload a new file or replace an existing one as a Google Doc."""
    raw_name = os.path.basename(local_path)
    doc_name = raw_name.replace('.docx', '')
    media = MediaFileUpload(local_path, mimetype=MIME_DOCX, resumable=True)

    existing_id = find_existing_file(service, folder_id, doc_name)

    if existing_id:
        service.files().delete(fileId=existing_id).execute()
        print(f"  Deleted old: {doc_name} (id: {existing_id})")

    file_metadata = {
        'name': doc_name,
        'parents': [folder_id],
        'mimeType': MIME_GDOC,
    }
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, webViewLink',
    ).execute()
    link = file.get('webViewLink', '')
    print(f"  Created: {doc_name} (id: {file['id']}) {link}")
    return file['id']


def main():
    parser = argparse.ArgumentParser(description="Upload docs to Google Drive")
    parser.add_argument("--folder-id", required=True, help="Google Drive folder ID")
    parser.add_argument("--docs-dir", default="./docs", help="Directory containing .docx files")
    args = parser.parse_args()

    if not os.path.isdir(args.docs_dir):
        print(f"ERROR: docs directory not found: {args.docs_dir}")
        sys.exit(1)

    docx_files = sorted([
        f for f in os.listdir(args.docs_dir)
        if f.endswith('.docx')
    ])

    if not docx_files:
        print("ERROR: No .docx files found in docs directory")
        sys.exit(1)

    print(f"Found {len(docx_files)} .docx files to upload as Google Docs")
    service = get_drive_service()

    for filename in docx_files:
        filepath = os.path.join(args.docs_dir, filename)
        upload_or_update(service, args.folder_id, filepath)

    print(f"\nDone! {len(docx_files)} files uploaded to Google Drive folder: {args.folder_id}")


if __name__ == "__main__":
    main()
