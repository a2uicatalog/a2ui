#!/bin/bash
# Push and deploy the GAS renderer to the stable deployment URL.
# Usage: ./deploy.sh [optional description]

DESC="${1:-update}"
# Set your own deployment ID after running: clasp deploy (first time creates a new deployment)
DEPLOYMENT_ID="${GAS_DEPLOYMENT_ID:-}"
if [ -z "$DEPLOYMENT_ID" ]; then
  echo "Error: set GAS_DEPLOYMENT_ID env var to your deployment ID"
  exit 1
fi

cd "$(dirname "$0")"

echo "Pushing files..."
clasp push || { echo "Push failed"; exit 1; }

echo "Deploying..."
clasp deploy --deploymentId "$DEPLOYMENT_ID" --description "$DESC"
