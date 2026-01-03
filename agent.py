"""
AI Customer Support Agent using OpenAI Function Calling.

This is the core of our agent. It:
1. Takes user messages
2. Decides which action to take (using OpenAI's function calling)
3. Executes the action
4. Returns a conversational response
"""

import json
from openai import OpenAI
from database import lookup_order, process_refund, get_faq


class CustomerSupportAgent:
    """
    An AI agent that handles customer support queries.
    
    How it works:
    1. User sends a message (e.g., "Where's my order #12345?")
    2. OpenAI analyzes the message and decides which function to call
    3. We execute that function with the parameters OpenAI extracted
    4. We send the result back to OpenAI to generate a human response
    """
    
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.conversation_history = []
        
        # System prompt: This tells the AI how to behave
        self.system_prompt = """You are a friendly and helpful customer support agent for an online store.

Your job is to:
- Help customers track their orders
- Process refund requests
- Answer common questions about shipping, returns, and payments

Guidelines:
- Be warm, professional, and empathetic
- Keep responses concise but helpful
- If you can't help with something, offer to connect them with a human agent
- Always confirm actions before taking them (like processing refunds)

Available order IDs for testing: 12345, 67890, 11111"""
        
        # Define the tools (functions) the agent can use
        # This is the key part that makes it an "agent" - it can take actions!
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "lookup_order",
                    "description": "Look up the status and details of a customer's order by order ID",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "order_id": {
                                "type": "string",
                                "description": "The order ID to look up (e.g., '12345')"
                            }
                        },
                        "required": ["order_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "process_refund",
                    "description": "Process a refund request for an order. Only call this after confirming with the customer.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "order_id": {
                                "type": "string",
                                "description": "The order ID to refund"
                            },
                            "reason": {
                                "type": "string",
                                "description": "The reason for the refund"
                            }
                        },
                        "required": ["order_id", "reason"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_faq",
                    "description": "Get information about common topics like shipping, returns, payment methods, or contacting support",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "topic": {
                                "type": "string",
                                "description": "The topic to get information about (e.g., 'shipping', 'returns', 'payment')"
                            }
                        },
                        "required": ["topic"]
                    }
                }
            }
        ]
    
    def _execute_function(self, function_name: str, arguments: dict) -> str:
        """
        Execute a function and return the result as a string.
        
        This is where the agent actually DOES things, not just talks.
        """
        if function_name == "lookup_order":
            result = lookup_order(arguments["order_id"])
        elif function_name == "process_refund":
            result = process_refund(arguments["order_id"], arguments["reason"])
        elif function_name == "get_faq":
            result = get_faq(arguments["topic"])
        else:
            result = {"error": f"Unknown function: {function_name}"}
        
        return json.dumps(result)
    
    def chat(self, user_message: str) -> str:
        """
        Process a user message and return the agent's response.
        
        This is the main method - it orchestrates the whole conversation.
        """
        # Add the user's message to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # Prepare messages for OpenAI (system prompt + conversation history)
        messages = [
            {"role": "system", "content": self.system_prompt}
        ] + self.conversation_history
        
        # Call OpenAI API
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",  # Fast and cheap, good for demos
            messages=messages,
            tools=self.tools,
            tool_choice="auto"  # Let the model decide whether to use a tool
        )
        
        # Get the assistant's response
        assistant_message = response.choices[0].message
        
        # Check if the model wants to call a function
        if assistant_message.tool_calls:
            # The model decided to use a tool - let's execute it!
            
            # Add the assistant's message (with tool calls) to history
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in assistant_message.tool_calls
                ]
            })
            
            # Execute each tool call and collect results
            for tool_call in assistant_message.tool_calls:
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                
                print(f"  🔧 Agent calling: {function_name}({arguments})")
                
                # Execute the function
                result = self._execute_function(function_name, arguments)
                
                # Add the tool result to conversation history
                self.conversation_history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })
            
            # Now call OpenAI again to generate a response based on the tool results
            messages = [
                {"role": "system", "content": self.system_prompt}
            ] + self.conversation_history
            
            final_response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages
            )
            
            final_message = final_response.choices[0].message.content
            
            # Add the final response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": final_message
            })
            
            return final_message
        
        else:
            # No tool call needed - just a regular response
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message.content
            })
            
            return assistant_message.content
    
    def reset_conversation(self):
        """Clear the conversation history to start fresh."""
        self.conversation_history = []

