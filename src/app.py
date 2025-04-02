import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
from parser import parse_recipes_from_tools

# Agno imports
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.embedder.openai import OpenAIEmbedder
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.knowledge.csv import CSVKnowledgeBase
from agno.vectordb.lancedb import LanceDb, SearchType

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# Response models
class Recipe(BaseModel):
    name: str
    description: str
    url: str

class QueryResponse(BaseModel):
    content: str
    recipes: list[Recipe]

# Debug lance
import lance
logger.info(f"Lance version: {lance.__version__}")

# Initialize Agent
try:
    agent = Agent(
        model=OpenAIChat(id="gpt-4o"),
        description="You are a Thai cuisine expert!",
        instructions=[
            "Search your knowledge base for Thai recipes.",
            "If the question is better suited for the web, search the web to fill in gaps.",
            "Prefer the information in your knowledge base over the web results."
        ],
        knowledge=CSVKnowledgeBase(
            path="data/ThaiRecipes.csv",
            vector_db=LanceDb(
                uri="data/lancedb",
                table_name="recipes",
                search_type=SearchType.hybrid,
                embedder=OpenAIEmbedder(id="text-embedding-3-small"),
            ),
        ),
        tools=[DuckDuckGoTools()],
        show_tool_calls=True,
        markdown=True
    )
    if agent.knowledge is not None:
        agent.knowledge.load()
except Exception as e:
    logger.error(f"Agent initialization failed: {str(e)}", exc_info=True)
    raise

app = FastAPI()

class QueryRequest(BaseModel):
    query: str

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/query", response_model=QueryResponse)
async def query_agent(request: QueryRequest):
    try:
        if not request.query.strip():
            raise ValueError("Query cannot be empty")
        
        logger.info(f"Processing query: {request.query}")
        run_response = await asyncio.to_thread(agent.run, request.query, stream=False)
        logger.info(f"Full RunResponse tools: {run_response.tools}")
        
        # Parse recipes from tools data (returns dicts)
        recipes = parse_recipes_from_tools(run_response)
        response_data = QueryResponse(
            content=run_response.content,
            recipes=recipes  # Pydantic will handle dict-to-model conversion
        )
        
        logger.info("Query processed successfully")
        return response_data
    
    except ValueError as ve:
        logger.error(f"Invalid query: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process query: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)