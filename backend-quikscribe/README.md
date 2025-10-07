# Quikscribe Kubernetes Manifests

## Apply order
1. Namespace
2. Secrets (backend, aws for bot, redis)
3. ConfigMap (backend)
4. Backend (Deployment, Service, HPA)
5. Meeting Bot (Deployment + Service)
6. Coordinator (Deployment + Service)
7. Optional: Backend Ingress (if ALB controller installed)

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

# 5) Bot (selenium sidecar)
kubectl apply -f ../google_bot/k8s/deployment.yaml

# 6) Coordinator (orchestrates bot processes)
kubectl apply -f ../google_bot/k8s/coordinator.yaml

# 7) Optional: Backend Ingress (AWS ALB)
kubectl apply -f backend-ingress.yaml.template
```

## Notes
- Backend probes use `/health` as defined in `main.py`.
- Meeting bot runs with a Selenium sidecar and exposes port 3000 inside the pod. Selenium is accessible at `http://localhost:4444/wd/hub` from the bot container.
- Replace `your-registry/...:latest` images with actual registry/image:tag.
- Use RDS/ElastiCache endpoints in secrets/configs for production.
- Consider IRSA for S3 (instead of static keys) in production.
