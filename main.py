"""
Customer Support AI Agent - Interactive Demo

This is the entry point for the application.
Run this file to chat with the AI agent.
"""

import os
from dotenv import load_dotenv
from agent import CustomerSupportAgent

# Load environment variables from .env file
load_dotenv()


def main():
    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found!")
        print("\nTo fix this:")
        print("1. Create a file called '.env' in this folder")
        print("2. Add this line: OPENAI_API_KEY=your-api-key-here")
        print("3. Get your API key from: https://platform.openai.com/api-keys")
        return
    
    # Create the agent
    agent = CustomerSupportAgent(api_key)
    
    # Welcome message
    print("=" * 60)
    print("🤖 Customer Support AI Agent")
    print("=" * 60)
    print("\nHi! I'm your AI customer support assistant.")
    print("I can help you with:")
    print("  • Track orders (try: 'Where is my order #12345?')")
    print("  • Process refunds (try: 'I want to return order #67890')")
    print("  • Answer questions (try: 'What's your return policy?')")
    print("\nType 'quit' to exit, 'reset' to start a new conversation.")
    print("-" * 60)
    
    # Main conversation loop
    while True:
        # Get user input
        try:
            user_input = input("\n👤 You: ").strip()
        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋")
            break
        
        # Handle special commands
        if not user_input:
            continue
        if user_input.lower() == "quit":
            print("\nGoodbye! Thanks for chatting. 👋")
            break
        if user_input.lower() == "reset":
            agent.reset_conversation()
            print("\n🔄 Conversation reset. Starting fresh!")
            continue
        
        # Get agent response
        try:
            response = agent.chat(user_input)
            print(f"\n🤖 Agent: {response}")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Please check your API key and try again.")


if __name__ == "__main__":
    main()

