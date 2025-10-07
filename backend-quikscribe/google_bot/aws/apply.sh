#!/usr/bin/env bash
set -euo pipefail
SCRIPTPATH="$(cd "$(dirname "$0")" && pwd)"

kubectl apply -f "$SCRIPTPATH/namespace.yaml"

echo "Apply or edit secret templates before continuing:"
read -p "Press Enter to apply secrets from templates..." _

kubectl apply -f "$SCRIPTPATH/backend-secret.yaml.template"
kubectl apply -f "$SCRIPTPATH/../google_bot/k8s/aws-secret.yaml.template"
kubectl apply -f "$SCRIPTPATH/redis-secret.yaml.template"

kubectl apply -f "$SCRIPTPATH/backend-configmap.yaml"

kubectl apply -f "$SCRIPTPATH/backend-deployment.yaml"
kubectl apply -f "$SCRIPTPATH/backend-service.yaml"
kubectl apply -f "$SCRIPTPATH/backend-hpa.yaml"

kubectl apply -f "$SCRIPTPATH/../google_bot/k8s/deployment.yaml"

# Coordinator (API to orchestrate bots)
kubectl apply -f "$SCRIPTPATH/../google_bot/k8s/coordinator.yaml"

# Optional: Backend Ingress (requires AWS Load Balancer Controller)
if [[ -f "$SCRIPTPATH/backend-ingress.yaml.template" ]]; then
  read -p "Apply backend ingress (requires ALB controller)? [y/N] " choice
  if [[ "${choice:-N}" == "y" || "${choice:-N}" == "Y" ]]; then
    kubectl apply -f "$SCRIPTPATH/backend-ingress.yaml.template"
  fi
fi

echo "All manifests applied."
