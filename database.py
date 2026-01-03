"""
Mock database for our customer support agent.
In a real app, this would connect to a real database.

This file contains:
1. Orders - customer purchase history
2. Products - items available for sale
3. FAQs - common questions and answers
4. Store info - business hours, locations
5. Callback slots - available times for support calls
"""

# ============================================================================
# ORDERS DATABASE
# ============================================================================
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


# ============================================================================
# PRODUCTS DATABASE (NEW!)
# ============================================================================
PRODUCTS = [
    {
        "id": "PROD001",
        "name": "Classic Blue T-Shirt",
        "category": "clothing",
        "price": 29.99,
        "description": "Comfortable cotton t-shirt in classic blue",
        "in_stock": True,
        "sizes": ["S", "M", "L", "XL"]
    },
    {
        "id": "PROD002",
        "name": "Running Shoes Pro",
        "category": "footwear",
        "price": 129.99,
        "description": "Professional running shoes with advanced cushioning",
        "in_stock": True,
        "sizes": ["8", "9", "10", "11", "12"]
    },
    {
        "id": "PROD003",
        "name": "Wireless Headphones",
        "category": "electronics",
        "price": 199.99,
        "description": "Noise-canceling wireless headphones with 30-hour battery",
        "in_stock": True,
        "colors": ["black", "white", "blue"]
    },
    {
        "id": "PROD004",
        "name": "Laptop Stand",
        "category": "accessories",
        "price": 49.99,
        "description": "Ergonomic aluminum laptop stand",
        "in_stock": False,
        "restock_date": "January 10, 2026"
    },
    {
        "id": "PROD005",
        "name": "Winter Jacket",
        "category": "clothing",
        "price": 189.99,
        "description": "Warm waterproof winter jacket with hood",
        "in_stock": True,
        "sizes": ["S", "M", "L", "XL"]
    },
    {
        "id": "PROD006",
        "name": "Smart Watch",
        "category": "electronics",
        "price": 299.99,
        "description": "Fitness tracking smartwatch with heart rate monitor",
        "in_stock": True,
        "colors": ["black", "silver", "rose gold"]
    }
]


def search_products(query: str, category: str = None, max_price: float = None) -> dict:
    """
    Search for products by keyword, category, or price.
    
    This is a more complex function that shows how agents can handle
    multiple optional parameters.
    """
    results = []
    query_lower = query.lower() if query else ""
    
    for product in PRODUCTS:
        # Check if query matches name or description
        matches_query = (
            not query or 
            query_lower in product["name"].lower() or 
            query_lower in product["description"].lower()
        )
        
        # Check category filter
        matches_category = (
            not category or 
            product["category"].lower() == category.lower()
        )
        
        # Check price filter
        matches_price = (
            max_price is None or 
            product["price"] <= max_price
        )
        
        if matches_query and matches_category and matches_price:
            results.append(product)
    
    if results:
        return {
            "success": True,
            "count": len(results),
            "products": results
        }
    return {
        "success": False,
        "message": "No products found matching your criteria"
    }


# ============================================================================
# CALLBACK SCHEDULING (NEW!)
# ============================================================================
AVAILABLE_SLOTS = [
    {"date": "2026-01-06", "time": "10:00 AM", "available": True},
    {"date": "2026-01-06", "time": "2:00 PM", "available": True},
    {"date": "2026-01-07", "time": "9:00 AM", "available": True},
    {"date": "2026-01-07", "time": "11:00 AM", "available": False},
    {"date": "2026-01-07", "time": "3:00 PM", "available": True},
    {"date": "2026-01-08", "time": "10:00 AM", "available": True},
]

SCHEDULED_CALLBACKS = []


def get_available_callback_slots() -> dict:
    """Get available time slots for a callback."""
    available = [slot for slot in AVAILABLE_SLOTS if slot["available"]]
    return {
        "success": True,
        "slots": available,
        "message": f"We have {len(available)} available time slots"
    }


def schedule_callback(date: str, time: str, phone_number: str, reason: str) -> dict:
    """
    Schedule a callback with customer support.
    
    This demonstrates how agents can handle actions with multiple
    required parameters and validation.
    """
    # Find the slot
    slot_found = None
    for slot in AVAILABLE_SLOTS:
        if slot["date"] == date and slot["time"] == time:
            slot_found = slot
            break
    
    if not slot_found:
        return {"success": False, "error": f"No slot found for {date} at {time}"}
    
    if not slot_found["available"]:
        return {"success": False, "error": f"Sorry, {date} at {time} is no longer available"}
    
    # Validate phone number (simple check)
    if len(phone_number.replace("-", "").replace(" ", "")) < 10:
        return {"success": False, "error": "Please provide a valid phone number"}
    
    # Schedule the callback
    callback_id = f"CB-{len(SCHEDULED_CALLBACKS) + 1001}"
    callback = {
        "id": callback_id,
        "date": date,
        "time": time,
        "phone": phone_number,
        "reason": reason
    }
    SCHEDULED_CALLBACKS.append(callback)
    
    # Mark slot as unavailable
    slot_found["available"] = False
    
    return {
        "success": True,
        "callback_id": callback_id,
        "message": f"Callback scheduled for {date} at {time}. We'll call {phone_number}.",
        "confirmation": callback
    }


# ============================================================================
# STORE INFORMATION (NEW!)
# ============================================================================
STORE_INFO = {
    "name": "TechStyle Store",
    "hours": {
        "monday": "9:00 AM - 9:00 PM",
        "tuesday": "9:00 AM - 9:00 PM",
        "wednesday": "9:00 AM - 9:00 PM",
        "thursday": "9:00 AM - 9:00 PM",
        "friday": "9:00 AM - 10:00 PM",
        "saturday": "10:00 AM - 10:00 PM",
        "sunday": "11:00 AM - 7:00 PM"
    },
    "locations": [
        {
            "name": "San Francisco - Downtown",
            "address": "123 Market St, San Francisco, CA 94105",
            "phone": "(415) 555-0100"
        },
        {
            "name": "Palo Alto",
            "address": "456 University Ave, Palo Alto, CA 94301",
            "phone": "(650) 555-0200"
        }
    ],
    "contact": {
        "email": "support@techstyle.com",
        "phone": "1-800-TECHSTYLE",
        "chat": "Available 24/7"
    }
}


def get_store_info(info_type: str) -> dict:
    """
    Get store information like hours, locations, or contact details.
    """
    info_type_lower = info_type.lower()
    
    if "hour" in info_type_lower or "open" in info_type_lower or "close" in info_type_lower:
        return {
            "success": True,
            "type": "hours",
            "data": STORE_INFO["hours"]
        }
    elif "location" in info_type_lower or "address" in info_type_lower or "store" in info_type_lower:
        return {
            "success": True,
            "type": "locations",
            "data": STORE_INFO["locations"]
        }
    elif "contact" in info_type_lower or "email" in info_type_lower or "phone" in info_type_lower:
        return {
            "success": True,
            "type": "contact",
            "data": STORE_INFO["contact"]
        }
    else:
        return {
            "success": True,
            "type": "all",
            "data": STORE_INFO
        }

