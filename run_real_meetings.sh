#!/usr/bin/env bash
set -euo pipefail

# =============================
# Concurrent real-meeting trigger script
# - Discovers ELB of backend Service
# - Gets OAuth token (sed-only, no jq/python)
# - Triggers 3 Jobs concurrently via FastAPI /k8s/meeting
# - Shows Jobs/Pods, describes Pending pods, tails recent logs
# Configurable via env: NS, AWS_REGION, USERNAME, PASSWORD
# Optional: DELETE_OLD_JOBS=true to delete previous job objects first
# =============================

NS=${NS:-quikscribe}
AWS_REGION=${AWS_REGION:-us-east-1}
USERNAME=${USERNAME:-voidraghav}
PASSWORD=${PASSWORD:-StrongPass123}
DELETE_OLD_JOBS=${DELETE_OLD_JOBS:-false}

# Real meeting URLs (override by exporting MEETING_1/2/3)
MEETING_1=${MEETING_1:-"https://meet.google.com/hhk-zhkg-osq"}
MEETING_2=${MEETING_2:-"https://meet.google.com/rrg-gkdt-qsb"}
MEETING_3=${MEETING_3:-"https://meet.google.com/cdk-sjyp-bbs"}
MEETINGS=("$MEETING_1" "$MEETING_2" "$MEETING_3")

# 0) Ensure kube access
aws eks update-kubeconfig --name quikscribe-eks --region "$AWS_REGION" >/dev/null 2>&1 || true

# Optional: clean old Jobs to avoid confusion
if [ "$DELETE_OLD_JOBS" = "true" ]; then
  echo "[cleanup] Deleting old Jobs (label app=quikscribe-job-bot)"
  kubectl -n "$NS" delete job -l app=quikscribe-job-bot --ignore-not-found || true
fi

# 1) Resolve ELB and base URL
ELB=$(kubectl -n "$NS" get svc quikscribe-backend-svc -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
BASE="http://${ELB}:8000"
echo "[ELB] $BASE"

# 2) Health check
curl -sS "$BASE/health" | sed 's/^/[health] /'

# 3) Acquire token via sed-only parser
RAW=$(curl -s -X POST "$BASE/api/v1/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=${USERNAME}&password=${PASSWORD}")
ACCESS=$(echo "$RAW" | sed -n 's/.*"access_token":"\([^"]*\)".*/\1/p')
if [ -z "$ACCESS" ]; then
  echo "[auth] Failed to parse token; raw: $RAW" >&2
  exit 1
fi
TKN="$ACCESS"
echo "[auth] token (trunc): ${TKN:0:25}..."

# Helper: POST JSON safely (uses --json if supported, otherwise --data-binary)
post_json() {
  local url="$1" json="$2" label="$3"
  if curl -h 2>&1 | grep -q -- "--json"; then
    curl -sS -w "\n[label:${label}][code:%{http_code}]\n" -X POST "$url" \
      -H "Authorization: Bearer $TKN" \
      --json "$json"
  else
    curl -sS -w "\n[label:${label}][code:%{http_code}]\n" -X POST "$url" \
      -H "Authorization: Bearer $TKN" \
      -H "Content-Type: application/json" \
      --data-binary "$json"
  fi
}

# 4) Trigger meetings concurrently
echo "[trigger] Posting ${#MEETINGS[@]} jobs concurrently"
i=0
for m in "${MEETINGS[@]}"; do
  i=$((i+1))
  body=$(printf '{"meetingId":"%s","duration":1,"recordType":"VIDEO"}' "$m")
  echo "  -> ($i) $m"
  post_json "$BASE/api/v1/meeting-bot/k8s/meeting" "$body" "$i" &
done
wait
echo "[trigger] All jobs posted."

# 5) Show Jobs/Pods
echo "[k8s] jobs/pods (app=quikscribe-job-bot)"
kubectl -n "$NS" get jobs,pods -l app=quikscribe-job-bot -o wide || true

# 6) Describe Pending pods and show recent events
PENDING=$(kubectl -n "$NS" get pods -l app=quikscribe-job-bot --no-headers 2>/dev/null | awk '$3=="Pending"{print $1}' || true)
if [ -n "$PENDING" ]; then
  echo "[debug] Pending pods: $PENDING"
  for p in $PENDING; do
    echo "--- describe $p ---"
    kubectl -n "$NS" describe pod "$p" | tail -n +1
  done
  echo "[events] recent (last 50)"
  kubectl -n "$NS" get events --sort-by=.lastTimestamp | tail -n 50 || true
fi

# 7) Tail logs for up to 3 jobs
JOBS=$(kubectl -n "$NS" get jobs -l app=quikscribe-job-bot -o jsonpath='{.items[*].metadata.name}' 2>/dev/null || true)
if [ -n "$JOBS" ]; then
  echo "$JOBS" | tr ' ' '\n' | head -n 3 | while read -r j; do
    [ -z "$j" ] && continue
    echo "---- logs $j (worker) ----";   kubectl -n "$NS" logs job/$j -c worker --tail=120 || true
    echo "---- logs $j (selenium) ----"; kubectl -n "$NS" logs job/$j -c selenium --tail=60 || true
  done
fi