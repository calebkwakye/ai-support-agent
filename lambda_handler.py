"""
AWS Lambda handler for the AI Support Agent.

This file adapts our agent to run as a serverless function on AWS Lambda.
API Gateway sends HTTP requests here, and we return responses.

Architecture:
    User → API Gateway → Lambda (this file) → OpenAI API
                              ↓
                         DynamoDB (conversations)
"""

import json
import os
import boto3
from decimal import Decimal

# Import our agent
from agent import CustomerSupportAgent

# DynamoDB setup for conversation persistence
dynamodb = boto3.resource('dynamodb')
TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'ai-support-conversations')

# Cache for agent instances (Lambda containers can be reused)
agents_cache = {}


def get_or_create_agent(conversation_id: str, api_key: str) -> CustomerSupportAgent:
    """
    Get an existing agent or create a new one.
    
    Lambda containers can be reused, so we cache agents in memory.
    For new containers, we reload conversation history from DynamoDB.
    """
    if conversation_id in agents_cache:
        return agents_cache[conversation_id]
    
    # Create new agent
    agent = CustomerSupportAgent(api_key)
    
    # Try to load existing conversation from DynamoDB
    try:
        table = dynamodb.Table(TABLE_NAME)
        response = table.get_item(Key={'conversation_id': conversation_id})
        
        if 'Item' in response:
            # Restore conversation history
            agent.conversation_history = response['Item'].get('messages', [])
    except Exception as e:
        print(f"Could not load conversation: {e}")
    
    agents_cache[conversation_id] = agent
    return agent


def save_conversation(conversation_id: str, agent: CustomerSupportAgent):
    """Save conversation history to DynamoDB."""
    try:
        table = dynamodb.Table(TABLE_NAME)
        
        # Convert any float values to Decimal (DynamoDB requirement)
        messages = json.loads(json.dumps(agent.conversation_history), parse_float=Decimal)
        
        table.put_item(Item={
            'conversation_id': conversation_id,
            'messages': messages,
            'message_count': len(agent.conversation_history)
        })
    except Exception as e:
        print(f"Could not save conversation: {e}")


def lambda_handler(event, context):
    """
    Main Lambda handler.
    
    This function is called by API Gateway for every HTTP request.
    
    Args:
        event: Contains the HTTP request data (body, headers, etc.)
        context: Lambda runtime information (not used here)
    
    Returns:
        dict: HTTP response with statusCode, headers, and body
    """
    # CORS headers for browser requests
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'POST, GET, OPTIONS'
    }
    
    # Handle CORS preflight requests
    http_method = event.get('httpMethod', event.get('requestContext', {}).get('http', {}).get('method', 'POST'))
    if http_method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }
    
    # Health check endpoint (only for GET requests)
    path = event.get('path', event.get('rawPath', '/'))
    if http_method == 'GET' and (path == '/' or path == '/health'):
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'status': 'healthy',
                'service': 'AI Support Agent',
                'version': '1.0.0'
            })
        }
    
    try:
        # Parse request body
        body = event.get('body', '{}')
        if isinstance(body, str):
            body = json.loads(body)
        
        message = body.get('message', '')
        conversation_id = body.get('conversation_id', context.aws_request_id if context else 'default')
        
        if not message:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Message is required'})
            }
        
        # Get OpenAI API key from environment
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            return {
                'statusCode': 500,
                'headers': headers,
                'body': json.dumps({'error': 'OpenAI API key not configured'})
            }
        
        # Get or create agent
        agent = get_or_create_agent(conversation_id, api_key)
        
        # Process message
        response = agent.chat(message)
        
        # Save conversation to DynamoDB
        save_conversation(conversation_id, agent)
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'response': response,
                'conversation_id': conversation_id
            })
        }
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }


# For local testing
if __name__ == '__main__':
    # Simulate a Lambda event
    test_event = {
        'body': json.dumps({'message': 'What are your store hours?'}),
        'httpMethod': 'POST',
        'path': '/chat'
    }
    
    # Mock context
    class MockContext:
        aws_request_id = 'test-123'
    
    result = lambda_handler(test_event, MockContext())
    print(json.dumps(json.loads(result['body']), indent=2))

