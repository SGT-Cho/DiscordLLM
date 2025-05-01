import os
import json
import requests
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain import hub
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import BaseTool, Tool
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Qdrant
from langchain_community.llms.openai import OpenAI
import qdrant_client

# Load environment variables
load_dotenv()
MCP_API = os.getenv('MCP_API', 'http://localhost:5601')
QDRANT_URL = os.getenv('QDRANT_URL', 'http://localhost:5600')
SEARXNG_URL = os.getenv('SEARXNG_URL', 'http://localhost:5578')

# Define model for search results
class WebSearchResult(BaseModel):
    title: str
    excerpt: str
    url: str

class MCPChatModel(BaseChatModel):
    """LangChain chat model wrapper for MCP API"""
    
    def __init__(self, api_url: str):
        super().__init__()
        self.api_url = api_url
    
    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        """Generate text based on messages"""
        # Extract the most recent message
        if messages and isinstance(messages[-1], HumanMessage):
            query = messages[-1].content
        else:
            query = "Hello"
        
        # Send to MCP API
        try:
            response = requests.post(
                f"{self.api_url}/query",
                json={"question": query}
            )
            response.raise_for_status()
            answer = response.json().get("answer", "Sorry, I couldn't generate a response.")
            
            return {"generations": [[{"text": answer}]]}
        except Exception as e:
            return {"generations": [[{"text": f"Error: {str(e)}"}]]}
    
    @property
    def _llm_type(self) -> str:
        return "mcp-chat"

def create_rag_search_tool() -> BaseTool:
    """Create a tool for searching the vector database"""
    
    def rag_search(query: str) -> str:
        """Search for documents in the vector database"""
        try:
            response = requests.post(
                f"{MCP_API}/mcp/v1/tools/rag_search/run",
                json={"arguments": {"query": query, "limit": 3}}
            )
            response.raise_for_status()
            
            results = response.json().get("results", [])
            if not results:
                return "No relevant documents found."
            
            formatted_results = []
            for i, result in enumerate(results):
                content = result.get("content", "")
                source = result.get("metadata", {}).get("source", "Unknown")
                formatted_results.append(f"Document {i+1} (Source: {source}):\n{content[:300]}...\n")
            
            return "\n".join(formatted_results)
        except Exception as e:
            return f"Error searching documents: {str(e)}"
    
    return Tool(
        name="rag_search",
        func=rag_search,
        description="Searches the document database for relevant information. Use this when you need to lookup specific information from documents."
    )

def create_web_search_tool() -> BaseTool:
    """Create a tool for web search using SearxNG"""
    
    def web_search(query: str) -> str:
        """Search the web for information"""
        try:
            response = requests.post(
                f"{MCP_API}/search_web",
                json={"query": query}
            )
            response.raise_for_status()
            
            results = response.json()
            if not results:
                return "No search results found."
            
            formatted_results = []
            for i, result in enumerate(results):
                title = result.get("title", "No title")
                excerpt = result.get("excerpt", "No excerpt")
                url = result.get("url", "#")
                formatted_results.append(f"Result {i+1}:\nTitle: {title}\nExcerpt: {excerpt}\nURL: {url}\n")
            
            return "\n".join(formatted_results)
        except Exception as e:
            return f"Error during web search: {str(e)}"
    
    return Tool(
        name="web_search",
        func=web_search,
        description="Searches the web for current information. Use this for questions about current events, general knowledge, or when you need up-to-date information."
    )

def create_direct_query_tool() -> BaseTool:
    """Create a tool for directly querying the LLM"""
    
    def direct_query(query: str) -> str:
        """Query the LLM directly"""
        try:
            response = requests.post(
                f"{MCP_API}/query",
                json={"question": query}
            )
            response.raise_for_status()
            return response.json().get("answer", "No answer generated.")
        except Exception as e:
            return f"Error querying the model: {str(e)}"
    
    return Tool(
        name="direct_query",
        func=direct_query,
        description="Queries the language model directly with a question. Use this for general questions, reasoning, or creative tasks."
    )

def create_agent():
    """Create a LangChain agent with all the tools"""
    
    # Create tools
    rag_tool = create_rag_search_tool()
    web_search_tool = create_web_search_tool()
    direct_query_tool = create_direct_query_tool()
    
    tools = [rag_tool, web_search_tool, direct_query_tool]
    
    # Create a wrapper for the MCP API
    llm = MCPChatModel(api_url=MCP_API)
    
    # Load the agent prompt
    prompt = hub.pull("hwchase17/react")
    
    # Create the agent
    agent = create_react_agent(llm, tools, prompt)
    
    # Create an agent executor
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
    )
    
    return agent_executor

def main():
    """Run the agent with a sample query"""
    agent_executor = create_agent()
    
    # Sample query
    query = "What can you tell me about artificial intelligence and its applications?"
    
    print(f"Query: {query}")
    print("-" * 50)
    
    # Run the agent
    result = agent_executor.invoke({"input": query})
    
    print("-" * 50)
    print(f"Result: {result['output']}")

if __name__ == "__main__":
    main()