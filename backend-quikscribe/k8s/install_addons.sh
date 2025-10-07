#!/usr/bin/env bash
set -euo pipefail

# Usage: ./install_addons.sh <CLUSTER_NAME> <AWS_REGION>
# Example: ./install_addons.sh quikscribe-eks us-east-1

CLUSTER_NAME=${1:-}
AWS_REGION=${2:-}

if [[ -z "$CLUSTER_NAME" || -z "$AWS_REGION" ]]; then
  echo "Usage: $0 <CLUSTER_NAME> <AWS_REGION>"
  exit 1
fi

# Pre-reqs
if ! command -v helm >/dev/null 2>&1; then
  echo "Helm not found. Install Helm first: https://helm.sh/docs/intro/install/"
  exit 1
fi

kubectl get ns kube-system >/dev/null 2>&1 || { echo "kubeconfig not configured or cluster unreachable"; exit 1; }

helm repo add metrics-server https://kubernetes-sigs.github.io/metrics-server/ || true
helm repo add kedacore https://kedacore.github.io/charts || true
helm repo add jetstack https://charts.jetstack.io || true
helm repo add eks https://aws.github.io/eks-charts || true
helm repo update

# 1) metrics-server
helm upgrade --install metrics-server metrics-server/metrics-server \
  --namespace kube-system \
  --set args={--kubelet-insecure-tls} \
  --wait

# 2) KEDA
kubectl create ns keda --dry-run=client -o yaml | kubectl apply -f -
helm upgrade --install keda kedacore/keda \
  --namespace keda \
  --wait

# 3) cert-manager (optional, for TLS certs)
kubectl create ns cert-manager --dry-run=client -o yaml | kubectl apply -f -
helm upgrade --install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --set installCRDs=true \
  --wait

# 4) AWS Load Balancer Controller
kubectl create ns aws-load-balancer-controller --dry-run=client -o yaml | kubectl apply -f - || true
helm upgrade --install aws-load-balancer-controller eks/aws-load-balancer-controller \
  --namespace kube-system \
  --set clusterName="$CLUSTER_NAME" \
  --set region="$AWS_REGION" \
  --set serviceAccount.create=true \
  --wait

# 5) Cluster Autoscaler
# NOTE: Ensure your node groups have the required tags and IAM permissions.
CA_VERSION=v1.29.0
kubectl apply -f https://raw.githubusercontent.com/kubernetes/autoscaler/${CA_VERSION}/cluster-autoscaler/cloudprovider/aws/examples/cluster-autoscaler-autodiscover.yaml

# Patch deployment with your cluster name
kubectl -n kube-system patch deployment.apps/cluster-autoscaler -p \
  "{\"spec\":{\"template\":{\"spec\":{\"containers\":[{\"name\":\"cluster-autoscaler\",\"command\":[\"./cluster-autoscaler\",\"--v=4\",\"--stderrthreshold=info\",\"--cloud-provider=aws\",\"--skip-nodes-with-local-storage=false\",\"--expander=least-waste\",\"--balance-similar-node-groups\",\"--skip-nodes-with-system-pods=false\",\"--cluster-name=${CLUSTER_NAME}\"]}]}}}}"

# Recommended: set the cluster-autoscaler image tag compatible with your cluster version
kubectl -n kube-system set image deployment/cluster-autoscaler cluster-autoscaler=k8s.gcr.io/autoscaling/cluster-autoscaler:${CA_VERSION}

echo "All addons installed or updated."
