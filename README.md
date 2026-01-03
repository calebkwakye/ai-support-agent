# AI Customer Support Agent

A conversational AI agent built with OpenAI's function calling, deployed as a serverless application on AWS Lambda. The agent can understand natural language, decide which actions to take, execute those actions, and respond conversationally.

## Live Endpoint

```bash
curl -X POST https://8foml1e4r9.execute-api.us-east-1.amazonaws.com \
  -H 'Content-Type: application/json' \
  -d '{"message": "What are your store hours?"}'
```

## Features

**Agent Capabilities**
- Order tracking with status and delivery estimates
- Refund processing with confirmation flows
- Product search by keyword, category, or price
- FAQ handling for shipping, returns, and policies
- Callback scheduling with human agents
- Store information (hours, locations, contact)

**Technical Features**
- Multi-turn conversation with context retention
- OpenAI function calling for reliable action execution
- RESTful API with FastAPI
- Serverless deployment on AWS Lambda
- Conversation persistence with DynamoDB

## How It Works

```
User: "Where's my order #12345?"
     │
     ▼
Agent analyzes intent → decides to call lookup_order("12345")
     │
     ▼
Function returns order details from database
     │
     ▼
Agent: "Your order has shipped and will arrive January 5th."
```

The agent uses OpenAI's function calling to determine which action to take:

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

When a user asks about an order, OpenAI returns a structured function call. The agent executes it, sends the result back to OpenAI, and generates a natural response.

## Quick Start

```bash
# Setup
git clone https://github.com/calebkwakye/ai-support-agent.git
cd ai-support-agent
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Configure API key
echo "OPENAI_API_KEY=your-key" > .env

# Run locally
python main.py
```

## Example Conversations

**Order Tracking:**
```
You: Where is my order #12345?
Agent: Your order #12345 has shipped. It contains a Blue T-Shirt and Black Jeans,
       totaling $79.99. Expected delivery is January 5, 2026.
```

**Refund Request:**
```
You: I want to return order #67890
Agent: I can help with that. Before I process the refund for order #67890
       (Running Shoes - $129.99), may I ask the reason?

You: They don't fit
Agent: I've initiated your refund of $129.99. You'll receive the funds in
       3-5 business days. Refund ID: REF-67890.
```

## Architecture

```
┌─────────────────┐
│   API Gateway   │  ← Public HTTP endpoint
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   AWS Lambda    │  ← Serverless compute (Python 3.11)
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌──────────┐
│ OpenAI │ │ DynamoDB │
│  API   │ │ (state)  │
└────────┘ └──────────┘
```

## Project Structure

```
ai-support-agent/
├── agent.py           # Core agent with function calling
├── api.py             # FastAPI server (local development)
├── lambda_handler.py  # AWS Lambda handler (production)
├── database.py        # Mock database for orders, products, FAQs
├── main.py            # CLI interface
├── deploy.sh          # AWS deployment script
└── requirements.txt
```

## AWS Deployment

Deploy with a single command:

```bash
export OPENAI_API_KEY=your-key
./deploy.sh
```

Creates:
- Lambda function: `ai-support-agent`
- DynamoDB table: `ai-support-conversations`
- API Gateway: HTTP endpoint with CORS
- IAM role: Least-privilege permissions

## API Reference

| Method | Endpoint               | Description              |
| ------ | ---------------------- | ------------------------ |
| GET    | `/`                    | Health check             |
| POST   | `/chat`                | Send message to agent    |
| GET    | `/conversations`       | List all conversations   |
| GET    | `/conversations/{id}`  | Get conversation details |
| DELETE | `/conversations/{id}`  | Delete a conversation    |

**Request:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me running shoes under $150"}'
```

**Response:**
```json
{
  "response": "I found Running Shoes Pro for $129.99...",
  "conversation_id": "abc123",
  "tools_used": ["search_products"],
  "timestamp": "2026-01-03T12:00:00"
}
```

## Tech Stack

| Component   | Technology                            |
| ----------- | ------------------------------------- |
| Runtime     | Python 3.11                           |
| LLM         | OpenAI GPT-4o-mini with function calling |
| API         | FastAPI                               |
| Compute     | AWS Lambda                            |
| Database    | AWS DynamoDB                          |
| Gateway     | AWS API Gateway                       |

## License

MIT
