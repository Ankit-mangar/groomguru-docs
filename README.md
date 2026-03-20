# GroomGuru Documentation Generator

Automatically generates 8 comprehensive `.docx` documentation files from the GroomGuru codebase and uploads them to Google Drive.

## Documents Generated

| # | Document | Description |
|---|----------|-------------|
| 1 | Project Overview & Features | What GroomGuru is, features, user flow |
| 2 | Tech Stack & Architecture | All technologies, system diagram |
| 3 | Database Design | Tables, columns, relationships, Flyway |
| 4 | API Reference | All REST endpoints with examples |
| 5 | Frontend Guide | Components, hooks, routing, state |
| 6 | Backend Guide | Packages, services, security, AI |
| 7 | Local Setup & Run Guide | Prerequisites, setup, troubleshooting |
| 8 | Deployment Guide | Railway setup, CI/CD, production config |

## How It Works

1. Push code to `groomguru-service` or `groomguru-ui`
2. A trigger workflow dispatches to this repo
3. GitHub Action clones both repos, generates docs, uploads to Google Drive

## Setup

### 1. Google Cloud (one-time)

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Select your existing project (the one with OAuth)
3. Enable **Google Drive API**: APIs & Services → Library → search "Google Drive API" → Enable
4. Create **Service Account**: IAM & Admin → Service Accounts → Create
   - Name: `groomguru-docs-bot`
   - Role: none needed (we share the folder directly)
5. Click the service account → Keys → Add Key → Create new key → JSON
6. Download the JSON key file — you'll need its **contents** as a secret

### 2. Google Drive (one-time)

1. Go to [Google Drive](https://drive.google.com)
2. Create a folder: "GroomGuru Documentation"
3. Right-click → Share → add the service account email (e.g., `groomguru-docs-bot@project-id.iam.gserviceaccount.com`) as **Editor**
4. Copy the folder ID from the URL: `https://drive.google.com/drive/folders/THIS_IS_THE_ID`

### 3. GitHub Secrets

**On this repo (groomguru-docs):**
- `GOOGLE_SERVICE_ACCOUNT_KEY` — paste the **entire JSON key file contents**
- `GOOGLE_DRIVE_FOLDER_ID` — the folder ID from step 2.4

**On groomguru-service AND groomguru-ui:**
- `DOCS_REPO_TOKEN` — a GitHub Personal Access Token (PAT) with `repo` scope
  - Create at: Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate
  - Scope: `repo` (full)

### 4. Test

Go to this repo's Actions tab → "Generate & Upload Documentation" → Run workflow

## Local Usage

```bash
pip install -r requirements.txt

python generate_docs.py \
  --be-path ../groomguru-service \
  --fe-path ../groomguru-ui \
  --output ./docs
```
