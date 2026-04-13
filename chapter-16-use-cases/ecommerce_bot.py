"""
E-Commerce Shopping Assistant
Chapter 16: Industry Use-Cases — E-Commerce

A conversational shopping assistant demonstrating:
  - Product search and recommendations
  - Cart management
  - Order tracking
  - Personalised upsell suggestions
"""

import re
from dataclasses import dataclass, field
from typing import Optional, List, Dict


# ─────────────────────────────────────────────
# Product catalogue
# ─────────────────────────────────────────────

PRODUCTS = [
    {"id": "P001", "name": "Wireless Earbuds Pro",    "category": "electronics",
     "price": 2499,  "rating": 4.5, "stock": True,
     "tags": ["wireless", "audio", "earbuds", "music", "bluetooth"]},
    {"id": "P002", "name": "Running Shoes Air Max",   "category": "footwear",
     "price": 3999,  "rating": 4.7, "stock": True,
     "tags": ["shoes", "running", "sports", "footwear", "gym"]},
    {"id": "P003", "name": "Laptop Stand (Adjustable)","category": "accessories",
     "price": 899,   "rating": 4.3, "stock": True,
     "tags": ["laptop", "stand", "desk", "work from home", "ergonomic"]},
    {"id": "P004", "name": "Smart Watch Series 5",    "category": "electronics",
     "price": 8999,  "rating": 4.6, "stock": True,
     "tags": ["watch", "smartwatch", "fitness", "health", "wearable"]},
    {"id": "P005", "name": "Yoga Mat Premium",        "category": "fitness",
     "price": 1299,  "rating": 4.4, "stock": True,
     "tags": ["yoga", "mat", "fitness", "exercise", "gym"]},
    {"id": "P006", "name": "Stainless Steel Bottle",  "category": "lifestyle",
     "price": 599,   "rating": 4.2, "stock": True,
     "tags": ["bottle", "water", "steel", "eco", "gym", "travel"]},
    {"id": "P007", "name": "Mechanical Keyboard TKL", "category": "electronics",
     "price": 4299,  "rating": 4.8, "stock": False,
     "tags": ["keyboard", "mechanical", "typing", "gaming", "computer"]},
    {"id": "P008", "name": "Noise-Cancelling Headphones","category": "electronics",
     "price": 6499,  "rating": 4.6, "stock": True,
     "tags": ["headphones", "noise cancelling", "audio", "music", "wireless"]},
]

UPSELL_MAP = {
    "P001": ["P008"],   # Earbuds → Headphones
    "P002": ["P005", "P006"],  # Shoes → Yoga Mat, Bottle
    "P003": ["P007"],   # Laptop Stand → Keyboard
    "P004": ["P006"],   # Smart Watch → Bottle
}


# ─────────────────────────────────────────────
# Cart
# ─────────────────────────────────────────────

@dataclass
class Cart:
    items: List[Dict] = field(default_factory=list)

    def add(self, product: Dict):
        for item in self.items:
            if item["id"] == product["id"]:
                item["qty"] += 1
                return
        self.items.append({**product, "qty": 1})

    def remove(self, product_id: str):
        self.items = [i for i in self.items if i["id"] != product_id]

    def total(self) -> int:
        return sum(i["price"] * i["qty"] for i in self.items)

    def is_empty(self) -> bool:
        return len(self.items) == 0

    def display(self) -> str:
        if self.is_empty():
            return "Your cart is empty."
        lines = ["🛒 Your cart:\n"]
        for item in self.items:
            lines.append(f"  • {item['name']} x{item['qty']} — ₹{item['price'] * item['qty']:,}")
        lines.append(f"\n  Total: ₹{self.total():,}")
        return "\n".join(lines)


# ─────────────────────────────────────────────
# E-Commerce Bot
# ─────────────────────────────────────────────

class EcommerceBot:

    def __init__(self):
        self.cart          = Cart()
        self.last_results: List[Dict] = []
        self.user_name:    Optional[str] = None

    def respond(self, user_input: str) -> str:
        text = user_input.lower().strip()

        # Greetings
        if re.search(r'\b(hi|hello|hey|good\s+\w+)\b', text):
            return (
                "Hi there! Welcome to ShopBot. 🛍️\n"
                "I can help you:\n"
                "  • Search for products\n"
                "  • Manage your cart\n"
                "  • Track your order\n\n"
                "What are you looking for today?"
            )

        # Cart viewing
        if re.search(r'\b(cart|basket|my items?)\b', text) and \
           not re.search(r'\b(add|remove|clear)\b', text):
            return self.cart.display()

        # Clear cart
        if re.search(r'\b(clear|empty)\s+(cart|basket)\b', text):
            self.cart = Cart()
            return "Cart cleared. Ready to start fresh! 🛒"

        # Add to cart (by number from last results)
        add_match = re.search(r'add\s+(\d+|first|second|third)', text)
        if add_match and self.last_results:
            return self._add_to_cart(add_match.group(1))

        # Remove from cart
        remove_match = re.search(r'remove\s+(\d+)', text)
        if remove_match and not self.cart.is_empty():
            return self._remove_from_cart(remove_match.group(1))

        # Order tracking
        order_id = re.search(r'ORD[-\s]?\d{4}', user_input.upper())
        if order_id or re.search(r'\b(track|order status|where is my)\b', text):
            return self._track_order(order_id.group(0) if order_id else None)

        # Checkout
        if re.search(r'\b(checkout|buy|purchase|pay|order now)\b', text):
            return self._checkout()

        # Product search
        if re.search(r'\b(search|find|show|looking for|want|need|buy|shop)\b', text) or \
           self._has_product_keywords(text):
            return self._search_products(text)

        # Price range filter
        if re.search(r'under ₹?\d+|below ₹?\d+|budget', text):
            return self._filter_by_budget(text)

        # Recommendations
        if re.search(r'\b(recommend|suggest|popular|best|top)\b', text):
            return self._recommend()

        # Thanks / Goodbye
        if re.search(r'\b(thank|bye|goodbye|done)\b', text):
            return (
                "Thank you for shopping with us! 🎉\n"
                "Happy shopping and come back soon!"
            )

        return (
            "I can help you find products, manage your cart, or track an order.\n"
            "Try: 'Show me wireless headphones' or 'What's in my cart?'"
        )

    def _search_products(self, query: str) -> str:
        results = [
            p for p in PRODUCTS
            if any(tag in query for tag in p["tags"])
            or p["category"] in query
            or p["name"].lower() in query
        ]
        if not results:
            results = [p for p in PRODUCTS if p["stock"]][:4]
            intro = "I didn't find an exact match, but here are some popular items:\n\n"
        else:
            intro = f"Found {len(results)} product(s):\n\n"

        self.last_results = results
        lines = [intro]
        for i, p in enumerate(results, 1):
            stock = "✅ In stock" if p["stock"] else "❌ Out of stock"
            lines.append(
                f"  {i}. {p['name']}\n"
                f"     ₹{p['price']:,}  |  ⭐ {p['rating']}  |  {stock}"
            )
        lines.append("\nSay 'add 1' to add item 1 to your cart, or ask for more details.")
        return "\n".join(lines)

    def _add_to_cart(self, selector: str) -> str:
        ordinals = {"first": 1, "second": 2, "third": 3}
        idx = ordinals.get(selector, int(selector) if selector.isdigit() else 1) - 1

        if idx < 0 or idx >= len(self.last_results):
            return "Please choose a valid item number from the search results."

        product = self.last_results[idx]
        if not product["stock"]:
            return f"Sorry, **{product['name']}** is currently out of stock."

        self.cart.add(product)
        response = f"✅ Added **{product['name']}** to your cart!\n"

        # Upsell suggestion
        upsell_ids = UPSELL_MAP.get(product["id"], [])
        if upsell_ids:
            upsell = next((p for p in PRODUCTS if p["id"] == upsell_ids[0]), None)
            if upsell:
                response += (
                    f"\n💡 Customers also bought: **{upsell['name']}** (₹{upsell['price']:,})\n"
                    "Say 'add' to add it too, or 'cart' to view your cart."
                )
                self.last_results = [upsell]

        return response

    def _remove_from_cart(self, selector: str) -> str:
        items = self.cart.items
        idx   = int(selector) - 1
        if idx < 0 or idx >= len(items):
            return "Please choose a valid item number from your cart."
        name = items[idx]["name"]
        self.cart.remove(items[idx]["id"])
        return f"Removed **{name}** from your cart."

    def _track_order(self, order_id: Optional[str]) -> str:
        from customer_support_bot import ORDERS
        if order_id:
            order_id = order_id.replace(" ", "-")
            order = ORDERS.get(order_id)
            if order:
                icons = {"Delivered": "✅", "In Transit": "🚚",
                         "Processing": "⏳", "Cancelled": "❌",
                         "Out for Delivery": "🛵"}
                return (
                    f"{icons.get(order['status'],'📦')} Order {order_id}:\n"
                    f"  Item:   {order['item']}\n"
                    f"  Status: {order['status']}\n"
                    f"  Date:   {order['date']}"
                )
            return f"Order {order_id} not found. Please check your order ID."
        return (
            "Please share your order ID (format: ORD-XXXX) to track your order.\n"
            "You can find it in your confirmation email."
        )

    def _checkout(self) -> str:
        if self.cart.is_empty():
            return "Your cart is empty! Add some items first. 🛒"
        return (
            f"{self.cart.display()}\n\n"
            "To complete your purchase, please visit our website:\n"
            "  🌐 shop.example.com/checkout\n\n"
            "Payment methods: Cards, UPI, Net Banking, COD"
        )

    def _recommend(self) -> str:
        top = sorted(PRODUCTS, key=lambda p: p["rating"], reverse=True)[:4]
        self.last_results = top
        lines = ["⭐ Top-rated products right now:\n"]
        for i, p in enumerate(top, 1):
            lines.append(f"  {i}. {p['name']} — ₹{p['price']:,}  (⭐ {p['rating']})")
        lines.append("\nSay 'add 1' to add any item to your cart.")
        return "\n".join(lines)

    def _filter_by_budget(self, text: str) -> str:
        match = re.search(r'₹?(\d+)', text)
        if not match:
            return "Please specify a budget, e.g. 'under ₹2000'."
        budget  = int(match.group(1))
        results = [p for p in PRODUCTS if p["price"] <= budget and p["stock"]]
        if not results:
            return f"No products found under ₹{budget:,}. Try a higher budget."
        self.last_results = results
        lines = [f"Products under ₹{budget:,}:\n"]
        for i, p in enumerate(results, 1):
            lines.append(f"  {i}. {p['name']} — ₹{p['price']:,}  (⭐ {p['rating']})")
        return "\n".join(lines)

    def _has_product_keywords(self, text: str) -> bool:
        all_tags = [tag for p in PRODUCTS for tag in p["tags"]]
        return any(tag in text for tag in all_tags)


def main():
    print("=== E-Commerce Shopping Assistant ===")
    print("(Type 'quit' to exit)\n")
    bot = EcommerceBot()
    print(f"Bot: {bot.respond('hello')}\n")

    while True:
        user_input = input("You: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit"):
            print("Bot: Happy shopping! 👋")
            break
        print(f"Bot: {bot.respond(user_input)}\n")


if __name__ == "__main__":
    main()
