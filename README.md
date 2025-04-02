##### Build
``` bash
docker build -t agentic_rag_app --no-cache .
```

##### Run
``` bash
docker run --env-file .env -p 8000:8000 -v $(pwd)/data:/app/data agentic_rag_app
```

##### Health Check
``` bash
curl http://localhost:8000/health
docker inspect --format='{{.State.Health.Status}}' $(docker ps -q --filter ancestor=agentic_rag_app)
```

##### Kubernetes
``` bash
kubectl create pv thai-recipes-pv \
  --capacity=storage=1Gi \
  --access-modes=ReadWriteMany \
  --nfs-server=nfs-server.example.com \
  --nfs-path=/exports/thai-recipes
  ```