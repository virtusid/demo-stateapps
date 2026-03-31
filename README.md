# Demo Stateful App

Notes app sederhana dengan arsitektur stateful + stateless.

## Arsitektur

```
Internet
   ↓
Route (HTTPS)
   ↓
Frontend / Nginx  ← stateless (DeploymentConfig, 2 replicas)
   ↓ /api/*
Flask API         ← stateless (DeploymentConfig, 2 replicas)
   ↓         ↓
PostgreSQL   Redis  ← stateful (StatefulSet + PVC)
```

## Struktur

```
demo-stateful/
├── api/
│   ├── app.py
│   ├── requirements.txt
│   └── .s2i/bin/
│       ├── assemble
│       └── run
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf
│   └── html/
│       └── index.html
└── k8s/
    ├── stateful/
    │   └── stateful.yaml     # Secret, PVC, StatefulSet, Service (postgres + redis)
    └── stateless/
        └── stateless.yaml    # ImageStream, BuildConfig, DeploymentConfig, Service, Route
```

## Deploy

```bash
# 1. Login & project
oc login --token=<token> --server=https://<ocp-api>:6443
oc new-project demo-project

# 2. Beri izin pull image
oc policy add-role-to-user system:image-puller system:serviceaccount:demo-project:default -n demo-project

# 3. Deploy stateful components dulu
oc apply -f k8s/stateful/stateful.yaml

# 4. Tunggu postgres & redis running
oc get pods -w -n demo-project

# 5. Update git URI di stateless.yaml, lalu deploy
oc apply -f k8s/stateless/stateless.yaml

# 6. Trigger build
oc start-build demo-api --follow -n demo-project
oc start-build demo-frontend --follow -n demo-project

# 7. Cek URL
oc get route demo-frontend -n demo-project
```
