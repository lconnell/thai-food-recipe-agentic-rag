from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
import uvicorn
import os

# Initialize FastAPI app
app = FastAPI(title="Camping Gear RAG API")

# Define the path to the CSV file
CSV_FILE_PATH = os.path.join("data", "gear.csv")

# Load and process CSV file
def load_csv_data(file_path: str):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"CSV file not found at: {file_path}")
    try:
        df = pd.read_csv(file_path)
        # Convert rows to Document objects for LangChain
        documents = [
            Document(
                page_content=f"{row['name']}: {row['description']}",
                metadata={"category": row["category"], "price": row["price"]}
            )
            for _, row in df.iterrows()
        ]
        return documents
    except Exception as e:
        raise Exception(f"Error loading CSV: {str(e)}")

# Initialize embeddings and vector store
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
documents = load_csv_data(CSV_FILE_PATH)
vector_store = FAISS.from_documents(documents, embeddings)

# Pydantic model for request body
class QueryRequest(BaseModel):
    query: str
    top_k: int = 2  # Number of results to return

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Query endpoint
@app.post("/query")
async def query_gear(request: QueryRequest):
    try:
        # Perform similarity search
        results = vector_store.similarity_search(request.query, k=request.top_k)
        
        # Format the response
        response = [
            {
                "name": result.page_content.split(":")[0].strip(),
                "description": result.page_content.split(":")[1].strip(),
                "category": result.metadata["category"],
                "price": result.metadata["price"]
            }
            for result in results
        ]
        return {"results": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

# Run the app
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)