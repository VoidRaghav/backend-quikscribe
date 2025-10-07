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

## Repository Cleanup and Optional Components

This repository contains optional components and large artifacts that you may not need in your workflow. Use this checklist to minimize disk usage while keeping your deployment path intact.

### Optional components
- Google Meeting Bot (`google_bot/`)
  - Used by Docker Compose services (`google_bot`, `meeting_coordinator`) and Kubernetes manifests referenced by `k8s/apply.sh`.
  - If you do not run the Node-based meeting bot, you can remove `google_bot/` and related wiring:
    - Remove `docker-compose.concurrency.yml` or the `google_bot` service from `docker-compose.yml`.
    - Remove Google Bot references from `k8s/apply.sh` and skip applying `../google_bot/k8s/*.yaml`.
  - If you keep it, do NOT commit `google_bot/node_modules/` to version control. Regenerate via your package manager.

- Nginx load balancer (`nginx.conf`)
  - Only used by `docker-compose.concurrency.yml` to load-balance dynamic bot ports.
  - If you do not use that stack, you can remove `nginx.conf`.

### Large root artifacts (safe to remove from repo)
- `awscliv2.zip`, `eksctl`, `eksctl_Linux_amd64.tar.gz`, and the bundled AWS CLI distribution under `aws/`
  - These are not used by the backend at runtime. Prefer installing AWS CLI and eksctl via your OS/CI environment instead of committing them.

### Static HTML pages
- `static/login.html`, `static/oauth-success.html`, `static/oauth-error.html`
  - Current OAuth flow redirects to `settings.frontend_url` (see `app/modules/auth/routes.py`). If your frontend handles these routes, the static HTML files are unnecessary and can be removed.

### Local/dev artifacts
- `.venv_quikscribe/`
  - Local Python virtual environment. Do not commit; add to `.gitignore`.
- `.env.bak.*` and `*.pem`
  - Environment backups and private keys should not be committed. Store securely and ignore in VCS.

### Suggested .gitignore additions
Add these patterns to `backend-quikscribe/.gitignore` to prevent large or sensitive files from being committed:

```
node_modules/
.venv_quikscribe/
*.pem
*.bak
```

### Compose and K8s quick notes
- `init.sql` is mounted by both Compose files; keep it if you use Compose.
- If you do not deploy to Kubernetes, the entire `k8s/` directory is optional and can be archived outside the repo.
