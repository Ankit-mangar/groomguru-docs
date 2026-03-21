#!/usr/bin/env python3
"""
Upload .docx files to a Google Drive folder as native Google Docs.

Converts .docx → Google Docs on upload so they don't count against
the service account's storage quota (which is zero).

Usage:
  python upload_to_drive.py --folder-id FOLDER_ID --docs-dir ./docs

Environment:
  GOOGLE_SERVICE_ACCOUNT_KEY  — JSON key contents (not a file path)
"""

import argparse
import json
import os
import sys

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/drive']
MIME_DOCX = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
MIME_GDOC = 'application/vnd.google-apps.document'


def get_drive_service():
    key_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_KEY')
    if not key_json:
        print("ERROR: GOOGLE_SERVICE_ACCOUNT_KEY environment variable not set")
        sys.exit(1)

    info = json.loads(key_json)
    creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    return build('drive', 'v3', credentials=creds)


def find_existing_file(service, folder_id, name):
    """Find an existing Google Doc by name in the folder."""
    query = (
        f"name='{name}' and '{folder_id}' in parents "
        f"and mimeType='{MIME_GDOC}' and trashed=false"
    )
    results = service.files().list(
        q=query, fields="files(id, name)",
        supportsAllDrives=True, includeItemsFromAllDrives=True,
    ).execute()
    files = results.get('files', [])
    return files[0]['id'] if files else None


def upload_or_update(service, folder_id, local_path):
    """Upload a new file or replace an existing one as a Google Doc."""
    raw_name = os.path.basename(local_path)
    doc_name = raw_name.replace('.docx', '')
    media = MediaFileUpload(local_path, mimetype=MIME_DOCX, resumable=True)

    existing_id = find_existing_file(service, folder_id, doc_name)

    if existing_id:
        # Delete old and re-create (Google Docs can't be updated with media in-place easily)
        service.files().delete(
            fileId=existing_id, supportsAllDrives=True,
        ).execute()
        print(f"  Deleted old: {doc_name} (id: {existing_id})")

    file_metadata = {
        'name': doc_name,
        'parents': [folder_id],
        'mimeType': MIME_GDOC,  # Convert to Google Docs on upload
    }
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, webViewLink',
        supportsAllDrives=True,
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
