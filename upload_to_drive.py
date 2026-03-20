#!/usr/bin/env python3
"""
Upload .docx files to a Google Drive folder using a service account.

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

SCOPES = ['https://www.googleapis.com/auth/drive.file']
MIME_DOCX = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'


def get_drive_service():
    key_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_KEY')
    if not key_json:
        print("ERROR: GOOGLE_SERVICE_ACCOUNT_KEY environment variable not set")
        sys.exit(1)

    info = json.loads(key_json)
    creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    return build('drive', 'v3', credentials=creds)


def find_existing_file(service, folder_id, name):
    """Find an existing file by name in the folder."""
    query = f"name='{name}' and '{folder_id}' in parents and trashed=false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get('files', [])
    return files[0]['id'] if files else None


def upload_or_update(service, folder_id, local_path):
    """Upload a new file or update an existing one."""
    name = os.path.basename(local_path)
    media = MediaFileUpload(local_path, mimetype=MIME_DOCX, resumable=True)

    existing_id = find_existing_file(service, folder_id, name)

    if existing_id:
        file = service.files().update(
            fileId=existing_id,
            media_body=media,
        ).execute()
        print(f"  Updated: {name} (id: {file['id']})")
    else:
        file_metadata = {
            'name': name,
            'parents': [folder_id],
        }
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id',
        ).execute()
        print(f"  Created: {name} (id: {file['id']})")

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

    print(f"Found {len(docx_files)} .docx files to upload")
    service = get_drive_service()

    for filename in docx_files:
        filepath = os.path.join(args.docs_dir, filename)
        upload_or_update(service, args.folder_id, filepath)

    print(f"\nDone! {len(docx_files)} files uploaded to Google Drive folder: {args.folder_id}")


if __name__ == "__main__":
    main()
