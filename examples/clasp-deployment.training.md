---
id: clasp-deployment
domain: training
subtype: tool-kt
name: "CLASP Deployment Runbook"
audience: "developers deploying Google Workspace add-ons"
source: "internal KT session + github.com/google/clasp README, July 2026"
license: "Apache-2.0"
est_minutes: 25
---

Step-by-step guide to installing CLASP and deploying Google Workspace Add-ons from a shared git repository using a dedicated deployment account. Tick each step as you complete it.

# Steps

## 0 · Prerequisites
**You will need**
- Dedicated account :: The shared deployment Google account — not your personal account
- Git access :: Clone/pull permissions on the add-on repository
- Node 18+ :: Managed via nvs (see steps below)
- GCP project :: With Apps Script API enabled and OAuth consent screen configured

### 1. Install nvs (Node Version Switcher) {#command_step}
cmd: export NVS_HOME="$HOME/.nvs" && git clone https://github.com/jasongin/nvs "$NVS_HOME" && . "$NVS_HOME/nvs.sh" install
note: Skip if nvs is already installed — verify with: nvs --version

### 2. Set Node version to LTS {#command_step}
cmd: nvs add lts && nvs use lts
note: Verify with: node --version (expect v18 or higher)

### 3. Install CLASP globally {#command_step}
cmd: npm install -g @google/clasp && clasp --version
note: Expect output like: 2.4.x

## 1 · GCP Project Setup {nav="1 · GCP Setup"}
> GCP setup must be done before first deploy. These are one-time steps
> per project.

**GCP Checklist**
- 1. Enable API :: GCP Console → APIs & Services → Enable Apps Script API
- 2. OAuth screen :: APIs & Services → OAuth consent screen → set app name, support email, scopes
- 3. Add test users :: OAuth consent screen → Test users → add the dedicated account email
- 4. Link to project :: Apps Script editor → Project Settings → Google Cloud Platform Project → enter GCP project number
- 5. Shared Drive :: Create or confirm the shared drive where the script project lives — dedicated account must have Contributor access

## 2 · Clone & Authenticate {nav="2 · Clone & Auth"}

### 1. Pull latest code from repository {#command_step}
cmd: git pull origin main
note: First time? Use: git clone <repo-url> && cd <repo-folder>

> Login with the dedicated deployment account — not your personal Google
> account. A browser window will open for OAuth.

### 2. Authenticate CLASP with dedicated account {#command_step}
cmd: clasp login
note: To check who is logged in: clasp login --status

## 3 · Push & Deploy
**Deployment modes**
- New add-on :: Run clasp create first to link this folder to a new Apps Script project on the shared drive
- Update existing :: Confirm .clasp.json contains the correct scriptId before pushing — no clasp create needed
- CI-style :: Same flow, but run from a scheduled job using the dedicated account credentials; scriptId in .clasp.json must match the production deployment

### 1. Push files to Apps Script {#command_step}
cmd: clasp push --force
note: –force overwrites remote without prompting. Check .claspignore to confirm only intended files are pushed.

### 2. Create a new versioned deployment {#command_step}
cmd: clasp deploy --description "deploy-$(date +%Y%m%d)"
note: Note the deployment ID in the output — needed for update deploys and Workspace admin install

**Updating an existing deployment**
- List deployments :: clasp deployments  — copy the target deployment ID
- Update in place :: clasp deploy --deploymentId <id> --description "deploy-YYYYMMDD"
- Deployment limit :: Apps Script enforces a 20-version limit per project. Run clasp undeploy <oldest-id> before deploying when at the limit.

## Done
Share the deployment URL with the Workspace admin for installation, or install directly via Google Workspace Marketplace if published. For internal tools, the admin installs via Admin Console → Apps → Google Workspace Marketplace apps → install by URL.
