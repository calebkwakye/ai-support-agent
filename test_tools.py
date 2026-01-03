"""Quick test to verify tools are working."""
import os
from dotenv import load_dotenv
load_dotenv()

from agent import CustomerSupportAgent

agent = CustomerSupportAgent(os.getenv("OPENAI_API_KEY"))
print("Number of tools:", len(agent.tools))
print("Tool names:", [t["function"]["name"] for t in agent.tools])

# Test a product query
print("\n--- Testing product search ---")
response = agent.chat("Search your products for running shoes")
print("Response:", response)

