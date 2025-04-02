import json
import re
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

# Parse recipes from tools data, returning dicts for serialization
def parse_recipes_from_tools(run_response) -> List[Dict[str, str]]:
    """Parse recipes from RunResponse tools data (LanceDb or DuckDuckGo) into dicts."""
    recipes = []
    for tool_result in getattr(run_response, 'tools', []):
        tool_name = tool_result.get("tool_name")
        content = tool_result.get("content")
        if not content:
            continue
        
        logger.info(f"Tool: {tool_name}, Raw content: {repr(content)}")
        
        if tool_name == "duckduckgo_search":
            try:
                results = json.loads(content)
                for item in results:
                    recipes.append({
                        "name": item.get("title", "Unknown Recipe"),
                        "description": item.get("body", ""),
                        "url": item.get("href", "")
                    })
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse DuckDuckGo content: {content}")
        
        elif tool_name == "search_knowledge_base":
            if content == "No documents found":
                logger.info("No recipes found in knowledge base.")
                continue
            try:
                # Parse JSON from LanceDb
                tool_data = json.loads(content)
                for entry in tool_data:
                    inner_content = entry.get("content", "")
                    if "recipe_name, recipe_text" not in inner_content:
                        logger.warning(f"Unexpected LanceDb content format: {inner_content}")
                        continue
                    
                    # Remove header and split by recipe boundaries (before "Ingredients:")
                    recipe_section = inner_content.split("recipe_name, recipe_text", 1)[1].strip()
                    # Split on recipe names followed by "Ingredients:"
                    recipe_texts = re.split(r'(\b(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*,\s*Ingredients:)', recipe_section)
                    for i in range(1, len(recipe_texts), 2):  # Step by 2: name, then description
                        name = recipe_texts[i].strip()
                        description = recipe_texts[i + 1].strip() if i + 1 < len(recipe_texts) else ""
                        if name and description:
                            recipes.append({
                                "name": name,
                                "description": f"Ingredients: {description}",
                                "url": ""  # No URL in current CSV
                            })
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse knowledge base JSON: {content}")
            except Exception as e:
                logger.warning(f"Error processing knowledge base content: {str(e)}")

    return recipes