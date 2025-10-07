# Quikscribe Kubernetes Manifests

## Apply order
1. Namespace
2. Secrets (backend, aws for bot, redis)
3. ConfigMap (backend)
4. Backend (Deployment, Service, HPA)
5. Worker (Deployment + KEDA ScaledObject) [requires KEDA]
6. Coordinator (Deployment + Service)
7. Optional: Legacy Bot (Deployment + Service) if not using queue/worker
8. Optional: Backend Ingress (if ALB controller installed)

## Commands
```bash
# 1) Create namespace
kubectl apply -f namespace.yaml

# 2) Create secrets from templates (edit first)
kubectl apply -f backend-secret.yaml.template
kubectl apply -f ../google_bot/k8s/aws-secret.yaml.template
kubectl apply -f redis-secret.yaml.template

# 3) ConfigMap
kubectl apply -f backend-configmap.yaml

# 4) Backend
kubectl apply -f backend-deployment.yaml
kubectl apply -f backend-service.yaml
kubectl apply -f backend-hpa.yaml

# 5) Worker (KEDA will scale replicas based on Redis queue length)
# Requires KEDA CRDs to be installed first. See Add-ons section below.
kubectl apply -f ../google_bot/k8s/worker.yaml

# 6) Coordinator (orchestrates bot processes or enqueues jobs in queue mode)
kubectl apply -f ../google_bot/k8s/coordinator.yaml

# 7) Optional: Legacy Bot (only if not using Worker/KEDA)
kubectl apply -f ../google_bot/k8s/deployment.yaml

# 8) Optional: Backend Ingress (AWS ALB)
kubectl apply -f backend-ingress.yaml.template
```

## Notes
- Backend probes use `/health` as defined in `main.py`.
- Worker pattern: a lightweight `worker` container pulls jobs from Redis and uses a Selenium sidecar in the same Pod. Selenium is accessible at `http://localhost:4444/wd/hub` from the worker container.
- Coordinator runs in `COORDINATOR_MODE=queue` by default, pushing jobs into `meeting:queue`. KEDA scales `quikscribe-worker` replicas based on queue depth.
- Replace `your-registry/...:latest` images with actual registry/image:tag.
- Use RDS/ElastiCache endpoints in secrets/configs for production.
- Consider IRSA for S3 (instead of static keys) in production.

## EKS Quickstart

### 1) Create Cluster with eksctl

An example config is included at `k8s/eksctl-cluster.yaml`. Edit as needed (region, node types) then run:

```bash
eksctl create cluster -f eksctl-cluster.yaml
```

### 2) Install Add-ons

Install metrics-server, KEDA, cert-manager, AWS Load Balancer Controller, and Cluster Autoscaler:

```bash
./install_addons.sh <CLUSTER_NAME> <AWS_REGION>
# example
./install_addons.sh quikscribe-eks us-east-1
```

Once KEDA is installed, (re)apply the worker manifest if you skipped earlier:

```bash
kubectl apply -f ../google_bot/k8s/worker.yaml
```

### 3) Apply Quikscribe Manifests

Use the convenience script:

```bash
./apply.sh
```

The script applies namespace, secrets, backend, optional legacy bot, worker (only if KEDA CRD is present), and coordinator. It will prompt for optional backend ingress.
