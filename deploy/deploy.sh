#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# deploy.sh – Deploy Voice AI Orchestrator to GCP Cloud Run
# Usage: ./deploy/deploy.sh
# Prerequisites: gcloud CLI installed, authenticated, project configured
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────────────────
PROJECT_ID="${GCP_PROJECT_ID:-$(gcloud config get-value project)}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="voice-ai-orchestrator"
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Voice AI Orchestrator – GCP Deploy"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Project:  ${PROJECT_ID}"
echo "  Region:   ${REGION}"
echo "  Service:  ${SERVICE_NAME}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── Step 1: Enable required APIs ───────────────────────────────────────────────
echo "[1/5] Enabling GCP APIs..."
gcloud services enable \
  run.googleapis.com \
  containerregistry.googleapis.com \
  secretmanager.googleapis.com \
  cloudbuild.googleapis.com \
  --project="${PROJECT_ID}" \
  --quiet

echo "  ↳ Granting Secret Manager Accessor role to Compute service account..."
PROJECT_NUMBER=$(gcloud projects describe "${PROJECT_ID}" --format="value(projectNumber)")
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --quiet &>/dev/null || true

# ── Step 2: Create Secrets in Secret Manager ───────────────────────────────────
echo "[2/5] Creating secrets in Secret Manager..."

create_secret() {
  local SECRET_NAME=$1
  local SECRET_VALUE=$2
  if gcloud secrets describe "${SECRET_NAME}" --project="${PROJECT_ID}" &>/dev/null; then
    echo "  ↳ Secret ${SECRET_NAME} already exists, updating..."
    echo -n "${SECRET_VALUE}" | gcloud secrets versions add "${SECRET_NAME}" --data-file=- --project="${PROJECT_ID}"
  else
    echo "  ↳ Creating secret ${SECRET_NAME}..."
    echo -n "${SECRET_VALUE}" | gcloud secrets create "${SECRET_NAME}" --data-file=- --project="${PROJECT_ID}"
  fi
}

# Load from local .env if present
if [ -f "backend/.env" ]; then
  export $(grep -v '^#' backend/.env | xargs)
fi

create_secret "MONGODB_URI" "${MONGODB_URI:-}"
create_secret "VAPI_API_KEY" "${VAPI_API_KEY:-}"
create_secret "OPENAI_API_KEY" "${OPENAI_API_KEY:-}"
create_secret "GEMINI_API_KEY" "${GEMINI_API_KEY:-}"
create_secret "VAPI_PHONE_NUMBER_ID" "${VAPI_PHONE_NUMBER_ID:-}"

# ── Step 3: Build Docker Image ─────────────────────────────────────────────────
echo "[3/5] Building Docker image..."
gcloud builds submit \
  --tag "${IMAGE}" \
  --project="${PROJECT_ID}" \
  --timeout=20m \
  .

# ── Step 4: Deploy to Cloud Run ────────────────────────────────────────────────
echo "[4/5] Deploying to Cloud Run..."

# Phase 1: Deploy with a temporary placeholder for VAPI_WEBHOOK_URL
# (We can only know the real URL AFTER the service is first created)
gcloud run deploy "${SERVICE_NAME}" \
  --image="${IMAGE}" \
  --region="${REGION}" \
  --platform=managed \
  --allow-unauthenticated \
  --min-instances=0 \
  --max-instances=5 \
  --memory=1Gi \
  --cpu=1 \
  --port=8000 \
  --timeout=300 \
  --set-secrets="MONGODB_URI=MONGODB_URI:latest,VAPI_API_KEY=VAPI_API_KEY:latest,OPENAI_API_KEY=OPENAI_API_KEY:latest,GEMINI_API_KEY=GEMINI_API_KEY:latest,VAPI_PHONE_NUMBER_ID=VAPI_PHONE_NUMBER_ID:latest" \
  --set-env-vars="MONGODB_DB_NAME=voice_saas,OPENAI_MODEL=gpt-4o,GEMINI_MODEL=gemini-1.5-flash,APP_ENV=production,VAPI_WEBHOOK_URL=placeholder,SECRET_KEY=${SECRET_KEY:-dev-secret-key},BACKEND_CORS_ORIGINS=*" \
  --project="${PROJECT_ID}"

# Phase 2: Fetch the REAL service URL (Cloud Run generates a hash-based URL, not project-id based)
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" \
  --region="${REGION}" \
  --project="${PROJECT_ID}" \
  --format="value(status.url)")

WEBHOOK_URL="${SERVICE_URL}/api/webhooks/vapi"
echo "  ↳ Real service URL: ${SERVICE_URL}"
echo "  ↳ Setting VAPI_WEBHOOK_URL to: ${WEBHOOK_URL}"

# Phase 3: Update ONLY the VAPI_WEBHOOK_URL env var with the correct URL
# This triggers a new revision but reuses the already-deployed image (very fast)
gcloud run services update "${SERVICE_NAME}" \
  --region="${REGION}" \
  --update-env-vars="VAPI_WEBHOOK_URL=${WEBHOOK_URL}" \
  --project="${PROJECT_ID}" \
  --quiet

# ── Step 5: Get Service URL ────────────────────────────────────────────────────
echo "[5/5] Fetching service URL..."
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" \
  --region="${REGION}" \
  --project="${PROJECT_ID}" \
  --format="value(status.url)")

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ Deployment Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Frontend URL:    ${SERVICE_URL}"
echo "  API Docs:        ${SERVICE_URL}/docs"
echo "  Webhook URL:     ${SERVICE_URL}/api/webhooks/vapi"
echo "  Health Check:    ${SERVICE_URL}/health"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  📌 Next steps:"
echo "  1. Update VAPI_WEBHOOK_URL to: ${SERVICE_URL}/api/webhooks/vapi"
echo "  2. Run seed script: cd backend && python scripts/seed_db.py"
echo "  3. Open frontend: ${SERVICE_URL}"
