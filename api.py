"""
Web API for the AI Customer Support Agent.

This file creates a web server that exposes our AI agent as an API.
Anyone can send HTTP requests to talk to the agent.

HOW IT WORKS:
1. We start a web server on http://localhost:8000
2. Clients send POST requests to /chat with their message
3. Our agent processes the message and returns a response
4. The response is sent back as JSON

WHY THIS MATTERS:
- This is how real AI products work (ChatGPT, Sierra, etc.)
- Any app (web, mobile, desktop) can now use our agent
- It's production-ready architecture
"""

import os
import uuid
from datetime import datetime
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from agent import CustomerSupportAgent

# Load environment variables (like our API key)
load_dotenv()


# ============================================================================
# DATA MODELS (Pydantic)
# ============================================================================
# These define the shape of data going in and out of our API.
# Think of them as contracts: "requests must look like THIS, responses like THAT"

class ChatRequest(BaseModel):
    """
    What the client sends to us.
    
    Example:
    {
        "message": "Where is my order #12345?",
        "conversation_id": "abc-123"  (optional - for continuing conversations)
    }
    """
    message: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    """
    What we send back to the client.
    
    Example:
    {
        "response": "Your order #12345 has shipped...",
        "conversation_id": "abc-123",
        "tools_used": ["lookup_order"]
    }
    """
    response: str
    conversation_id: str
    tools_used: list[str] = []
    timestamp: str


class ConversationInfo(BaseModel):
    """Information about a conversation."""
    conversation_id: str
    message_count: int
    created_at: str
    last_message_at: str


# ============================================================================
# CONVERSATION STORAGE
# ============================================================================
# This stores conversations in memory so users can have multi-turn chats.
# In production, you'd use a database (Redis, PostgreSQL, etc.)

class ConversationStore:
    """
    Stores active conversations.
    
    WHY WE NEED THIS:
    - Users might send multiple messages in one conversation
    - We need to remember what was said before
    - Each conversation gets a unique ID
    
    HOW IT WORKS:
    - conversation_id -> {agent, created_at, last_used}
    - When a user sends a message with a conversation_id, we use their existing agent
    - When they don't, we create a new conversation
    """
    
    def __init__(self):
        self.conversations: dict = {}
        self.api_key = os.getenv("OPENAI_API_KEY")
    
    def get_or_create(self, conversation_id: Optional[str] = None) -> tuple[str, CustomerSupportAgent]:
        """
        Get an existing conversation or create a new one.
        
        Returns: (conversation_id, agent)
        """
        # If no ID provided, create a new conversation
        if conversation_id is None or conversation_id not in self.conversations:
            new_id = str(uuid.uuid4())[:8]  # Short unique ID like "a1b2c3d4"
            agent = CustomerSupportAgent(self.api_key)
            self.conversations[new_id] = {
                "agent": agent,
                "created_at": datetime.now().isoformat(),
                "last_used": datetime.now().isoformat(),
                "message_count": 0
            }
            return new_id, agent
        
        # Use existing conversation
        conv = self.conversations[conversation_id]
        conv["last_used"] = datetime.now().isoformat()
        return conversation_id, conv["agent"]
    
    def increment_message_count(self, conversation_id: str):
        """Track how many messages in this conversation."""
        if conversation_id in self.conversations:
            self.conversations[conversation_id]["message_count"] += 1
    
    def get_info(self, conversation_id: str) -> Optional[dict]:
        """Get info about a conversation."""
        if conversation_id in self.conversations:
            conv = self.conversations[conversation_id]
            return {
                "conversation_id": conversation_id,
                "message_count": conv["message_count"],
                "created_at": conv["created_at"],
                "last_message_at": conv["last_used"]
            }
        return None
    
    def delete(self, conversation_id: str) -> bool:
        """Delete a conversation."""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            return True
        return False
    
    def list_all(self) -> list[dict]:
        """List all active conversations."""
        return [
            {
                "conversation_id": cid,
                "message_count": data["message_count"],
                "created_at": data["created_at"],
                "last_message_at": data["last_used"]
            }
            for cid, data in self.conversations.items()
        ]


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

# Create the conversation store (shared across all requests)
store = ConversationStore()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown logic for the app.
    This runs when the server starts and stops.
    """
    # Startup: Check that we have an API key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY not set!")
    else:
        print("✅ OpenAI API key loaded")
    print("🚀 AI Support Agent API is ready!")
    
    yield  # Server runs here
    
    # Shutdown: Clean up
    print("👋 Shutting down...")


# Create the FastAPI app
app = FastAPI(
    title="AI Customer Support Agent",
    description="""
    An intelligent customer support agent powered by OpenAI.
    
    ## Features
    - 🔍 Order tracking
    - 💰 Refund processing  
    - ❓ FAQ handling
    - 💬 Multi-turn conversations
    
    ## How to use
    1. Send a POST request to `/chat` with your message
    2. Include `conversation_id` to continue a conversation
    3. The agent will respond with helpful information
    """,
    version="1.0.0",
    lifespan=lifespan
)


# CORS middleware - allows web browsers to talk to our API
# (Without this, browsers block requests for security reasons)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# API ENDPOINTS (Routes)
# ============================================================================
# These are the URLs that clients can call

@app.get("/")
async def root():
    """
    Health check endpoint.
    
    When someone visits http://localhost:8000/, they see this.
    Useful for checking if the server is running.
    """
    return {
        "status": "online",
        "message": "AI Customer Support Agent is running!",
        "docs": "Visit /docs for interactive API documentation"
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint - talk to the AI agent.
    
    HOW TO USE:
    
    curl -X POST http://localhost:8000/chat \\
         -H "Content-Type: application/json" \\
         -d '{"message": "Where is my order #12345?"}'
    
    WHAT HAPPENS:
    1. We get the user's message
    2. We find or create their conversation
    3. We send the message to the AI agent
    4. The agent decides what to do (maybe call a function)
    5. We return the response
    """
    try:
        # Get or create conversation
        conversation_id, agent = store.get_or_create(request.conversation_id)
        
        # Track tools used (we'll capture this from the agent)
        tools_used = []
        
        # Send message to agent and get response
        response = agent.chat(request.message)
        
        # Update message count
        store.increment_message_count(conversation_id)
        
        # Check what tools were used (look at last entries in history)
        for msg in agent.conversation_history[-5:]:
            if msg.get("role") == "assistant" and msg.get("tool_calls"):
                for tc in msg["tool_calls"]:
                    tools_used.append(tc["function"]["name"])
        
        return ChatResponse(
            response=response,
            conversation_id=conversation_id,
            tools_used=list(set(tools_used)),  # Remove duplicates
            timestamp=datetime.now().isoformat()
        )
    
    except Exception as e:
        # Something went wrong - return a helpful error
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )


@app.get("/conversations")
async def list_conversations():
    """
    List all active conversations.
    
    Useful for debugging or admin dashboards.
    """
    return {"conversations": store.list_all()}


@app.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """
    Get info about a specific conversation.
    """
    info = store.get_info(conversation_id)
    if info is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return info


@app.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """
    Delete a conversation (clear its history).
    """
    if store.delete(conversation_id):
        return {"message": f"Conversation {conversation_id} deleted"}
    raise HTTPException(status_code=404, detail="Conversation not found")


@app.post("/conversations/{conversation_id}/reset")
async def reset_conversation(conversation_id: str):
    """
    Reset a conversation (clear history but keep the ID).
    """
    info = store.get_info(conversation_id)
    if info is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Delete and recreate
    store.delete(conversation_id)
    return {"message": f"Conversation {conversation_id} reset", "new_conversation_id": conversation_id}


# ============================================================================
# RUN THE SERVER
# ============================================================================
# This only runs if you execute this file directly (python api.py)

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("🤖 Starting AI Customer Support Agent API")
    print("=" * 60)
    print("\n📍 Server will be available at: http://localhost:8000")
    print("📚 API docs available at: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop the server\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)

