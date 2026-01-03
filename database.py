"""
Mock database for our customer support agent.
In a real app, this would connect to a real database.
"""

# Fake order database
ORDERS = {
    "12345": {
        "id": "12345",
        "customer": "John Doe",
        "status": "shipped",
        "items": ["Blue T-Shirt", "Black Jeans"],
        "total": 79.99,
        "eta": "January 5, 2026"
    },
    "67890": {
        "id": "67890",
        "customer": "Jane Smith",
        "status": "processing",
        "items": ["Running Shoes"],
        "total": 129.99,
        "eta": "January 8, 2026"
    },
    "11111": {
        "id": "11111",
        "customer": "Bob Wilson",
        "status": "delivered",
        "items": ["Laptop Stand", "USB Cable"],
        "total": 49.99,
        "delivered_date": "December 20, 2025"
    }
}

# Fake FAQ database
FAQS = {
    "return_policy": "You can return any item within 30 days of delivery for a full refund. Items must be unused and in original packaging.",
    "shipping_time": "Standard shipping takes 5-7 business days. Express shipping (additional $9.99) takes 2-3 business days.",
    "contact": "You can reach our human support team at support@store.com or call 1-800-SUPPORT (Mon-Fri 9am-5pm EST).",
    "payment_methods": "We accept Visa, Mastercard, American Express, PayPal, and Apple Pay.",
}


def lookup_order(order_id: str) -> dict:
    """Look up an order by ID."""
    if order_id in ORDERS:
        return {"success": True, "order": ORDERS[order_id]}
    return {"success": False, "error": f"Order {order_id} not found"}


def process_refund(order_id: str, reason: str) -> dict:
    """Process a refund request for an order."""
    if order_id not in ORDERS:
        return {"success": False, "error": f"Order {order_id} not found"}
    
    order = ORDERS[order_id]
    if order["status"] == "refunded":
        return {"success": False, "error": "This order has already been refunded"}
    
    # In a real app, this would actually process the refund
    return {
        "success": True,
        "message": f"Refund of ${order['total']} initiated for order {order_id}",
        "refund_id": f"REF-{order_id}",
        "estimated_days": "3-5 business days"
    }


def get_faq(topic: str) -> dict:
    """Get FAQ information about a topic."""
    # Try to match the topic to our FAQ
    topic_lower = topic.lower()
    
    if "return" in topic_lower or "refund" in topic_lower:
        return {"success": True, "answer": FAQS["return_policy"]}
    elif "ship" in topic_lower or "delivery" in topic_lower or "long" in topic_lower:
        return {"success": True, "answer": FAQS["shipping_time"]}
    elif "contact" in topic_lower or "human" in topic_lower or "speak" in topic_lower:
        return {"success": True, "answer": FAQS["contact"]}
    elif "pay" in topic_lower or "card" in topic_lower:
        return {"success": True, "answer": FAQS["payment_methods"]}
    else:
        return {"success": False, "error": "I don't have information about that topic. Would you like to speak with a human agent?"}

