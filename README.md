[![Codacy Badge](https://app.codacy.com/project/badge/Grade/7e04b9743f2b4eba9d3a48e53f8e6391)](https://app.codacy.com/gh/lconnell/langchain-rag/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade)

##### Build
``` bash
docker build -t langchain_rag_app --no-cache .
```

##### Run
``` bash
docker run --name langchain_rag --rm --env-file .env -p 8000:8000 -v $(pwd)/data:/app/data langchain_rag_app
```

##### Health Check
``` bash
curl -X GET "http://localhost:8000/health"
```

##### Camping Gear Query
``` bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "best camping gear"}'
```

##### Kubernetes
``` bash
kubectl create pv langchain-rag-pv \
  --capacity=storage=1Gi \
  --access-modes=ReadWriteOnce \
  --host-path=/Users/lconnell/Development/langchain-rag/data \
  --dry-run=client -o yaml > langchain-rag-pv.yaml
kubectl apply -f langchain-rag-pv.yaml
```