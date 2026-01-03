# 🤖 AI Customer Support Agent

An intelligent customer support agent built with OpenAI's function calling capabilities. The agent can understand natural language queries, decide which actions to take, execute those actions, and respond conversationally.

**This project demonstrates core AI agent concepts used in production systems at companies like Sierra, Intercom, and others.**

## Features

### Core Capabilities
- **Order Tracking**: Look up order status, items, and delivery estimates
- **Refund Processing**: Handle refund requests with confirmation flows
- **FAQ Handling**: Answer common questions about shipping, returns, and payments
- **Product Search**: Find products by keyword, category, or price
- **Callback Scheduling**: Book calls with human support agents
- **Store Information**: Get business hours, locations, and contact details

### Technical Features
- **Multi-turn Conversations**: Maintains context across multiple messages
- **Function Calling**: Uses OpenAI's function calling for reliable action execution
- **RESTful API**: FastAPI-based web server with auto-generated docs
- **Conversation Persistence**: Track and manage multiple concurrent conversations
- **Tool Tracking**: See which functions the agent called for each response

## How It Works

```
User: "Where's my order #12345?"
     ↓
Agent analyzes intent
     ↓
Agent calls: lookup_order("12345")
     ↓
Database returns order details
     ↓
Agent: "Your order #12345 has shipped and will arrive by January 5th!"
```

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   User      │────▶│   Agent     │────▶│  OpenAI API │
│   Input     │     │  (agent.py) │◀────│  (GPT-4o)   │
└─────────────┘     └──────┬──────┘     └─────────────┘
                          │
                          ▼
                   ┌─────────────┐
                   │  Functions  │
                   │ - lookup    │
                   │ - refund    │
                   │ - faq       │
                   └─────────────┘
```

## Quick Start

### 1. Clone and setup
```bash
cd ai-support-agent
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure API key
Create a `.env` file in the project root:
```
OPENAI_API_KEY=your-api-key-here
```

Get your API key from: https://platform.openai.com/api-keys

### 3. Run the agent
```bash
python main.py
```

## Example Conversations

**Order Tracking:**
```
You: Where is my order #12345?
Agent: Your order #12345 has shipped! It contains a Blue T-Shirt and Black Jeans, 
       totaling $79.99. Expected delivery is January 5, 2026.
```

**Refund Request:**
```
You: I want to return order #67890
Agent: I can help with that. Before I process the refund for order #67890 
       (Running Shoes - $129.99), may I ask the reason for the return?

You: They don't fit
Agent: I've initiated your refund of $129.99. You'll receive the funds in 
       3-5 business days. Your refund ID is REF-67890.
```

**FAQ:**
```
You: What's your return policy?
Agent: You can return any item within 30 days of delivery for a full refund. 
       Items must be unused and in original packaging.
```

## Project Structure

```
ai-support-agent/
├── agent.py         # Core agent logic with OpenAI function calling
├── api.py           # FastAPI web server with REST endpoints
├── database.py      # Mock database for orders, products, FAQs
├── main.py          # Interactive CLI interface
├── requirements.txt # Python dependencies
└── README.md        # Documentation
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| POST | `/chat` | Send message to agent |
| GET | `/conversations` | List all conversations |
| GET | `/conversations/{id}` | Get conversation details |
| DELETE | `/conversations/{id}` | Delete a conversation |

### Example API Request

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me running shoes under $150"}'
```

### Example Response

```json
{
  "response": "I found Running Shoes Pro for $129.99...",
  "conversation_id": "abc123",
  "tools_used": ["search_products"],
  "timestamp": "2026-01-03T12:00:00"
}
```

## Technical Details

### Function Calling
The agent uses OpenAI's function calling feature to reliably extract structured data from natural language:

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "lookup_order",
            "description": "Look up order status by ID",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string"}
                }
            }
        }
    }
]
```

### Conversation Flow
1. User sends message
2. OpenAI analyzes message and decides if a function call is needed
3. If yes: Agent executes function → sends result back to OpenAI → generates response
4. If no: OpenAI generates direct response
5. Response returned to user

## Built With

- **Python 3.10+**
- **OpenAI API** - GPT-4o-mini with function calling
- **python-dotenv** - Environment variable management

## Future Enhancements

- [ ] Add real database integration (PostgreSQL/MongoDB)
- [ ] Implement streaming responses
- [ ] Add web interface (FastAPI + React)
- [ ] Multi-language support
- [ ] Analytics and conversation logging

## License

MIT

---

Built by [Caleb Kwakye](https://github.com/calebkwakye)

