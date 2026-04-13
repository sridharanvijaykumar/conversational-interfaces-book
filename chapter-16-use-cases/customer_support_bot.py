"""
Customer Support Bot
Chapter 16: Industry Use-Cases — Customer Support & Contact Centres

A functional customer support chatbot demonstrating:
  - FAQ answering with fuzzy keyword matching
  - Order status lookup (mock database)
  - Human escalation trigger
  - Context-aware follow-up handling
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List
import re, random


# ─────────────────────────────────────────────
# Mock order database
# ─────────────────────────────────────────────

ORDERS: Dict[str, Dict] = {
    "ORD-1001": {"status": "Delivered",   "date": "2026-03-28", "item": "Wireless Headphones"},
    "ORD-1002": {"status": "In Transit",  "date": "2026-04-14", "item": "Running Shoes"},
    "ORD-1003": {"status": "Processing",  "date": "2026-04-16", "item": "Laptop Stand"},
    "ORD-1004": {"status": "Cancelled",   "date": "2026-04-01", "item": "Phone Case"},
    "ORD-1005": {"status": "Out for Delivery", "date": "2026-04-12", "item": "Smart Watch"},
}


# ─────────────────────────────────────────────
# FAQ knowledge base
# ─────────────────────────────────────────────

FAQS = [
    {
        "keywords": ["return", "refund", "send back", "exchange"],
        "answer": (
            "Our return policy:\n"
            "  • Items can be returned within 30 days of delivery.\n"
            "  • Refunds are processed within 5–7 business days.\n"
            "  • Items must be in original, unused condition.\n"
            "To initiate a return, visit support.example.com/returns."
        ),
    },
    {
        "keywords": ["shipping", "delivery", "ship", "how long", "arrive", "dispatch"],
        "answer": (
            "Shipping options:\n"
            "  • Standard shipping: 3–5 business days (free over ₹499)\n"
            "  • Express shipping: 1–2 business days (₹99)\n"
            "  • Same-day delivery available in select cities."
        ),
    },
    {
        "keywords": ["payment", "pay", "credit card", "upi", "wallet", "method"],
        "answer": (
            "We accept:\n"
            "  • Credit & Debit cards (Visa, Mastercard, RuPay)\n"
            "  • UPI (GPay, PhonePe, Paytm)\n"
            "  • Net Banking\n"
            "  • Cash on Delivery (COD) for orders under ₹5,000"
        ),
    },
    {
        "keywords": ["cancel", "cancellation", "cancel order"],
        "answer": (
            "You can cancel an order within 12 hours of placing it.\n"
            "If the order has already shipped, you'll need to refuse delivery "
            "or use our return process.\n"
            "To cancel, visit My Orders → Select Order → Cancel."
        ),
    },
    {
        "keywords": ["contact", "phone", "email", "call", "speak", "agent", "human"],
        "answer": (
            "Reach our support team:\n"
            "  📧 support@example.com\n"
            "  📞 1800-123-4567 (toll-free, Mon–Fri 9 AM–6 PM)\n"
            "  💬 Live chat on our website\n"
            "Would you like me to connect you with a live agent?"
        ),
    },
    {
        "keywords": ["warranty", "guarantee", "defective", "broken", "damaged"],
        "answer": (
            "All products come with a minimum 6-month warranty.\n"
            "Electronics carry a 1-year manufacturer's warranty.\n"
            "If you received a damaged item, please send photos to "
            "support@example.com within 48 hours of delivery."
        ),
    },
    {
        "keywords": ["coupon", "discount", "promo", "offer", "code", "deal"],
        "answer": (
            "Apply coupon codes at checkout in the 'Promo Code' field.\n"
            "Current offers:\n"
            "  • WELCOME10 — 10% off your first order\n"
            "  • FREESHIP — Free shipping on any order\n"
            "  • SAVE20 — ₹200 off orders above ₹1,000"
        ),
    },
]


# ─────────────────────────────────────────────
# Customer Support Bot
# ─────────────────────────────────────────────

@dataclass
class SupportContext:
    order_id:     Optional[str] = None
    last_topic:   Optional[str] = None
    escalated:    bool = False
    turn_count:   int = 0


class CustomerSupportBot:
    """
    A customer support chatbot that handles FAQs, order lookups,
    and escalation to human agents.
    """

    def __init__(self):
        self.context = SupportContext()

    def respond(self, user_input: str) -> str:
        self.context.turn_count += 1
        text = user_input.lower().strip()

        # Escalation request
        if any(w in text for w in ["human", "agent", "representative", "person", "speak to someone"]):
            return self._escalate()

        # Order ID lookup
        order_id = self._extract_order_id(user_input)
        if order_id:
            return self._lookup_order(order_id)

        # "my order" with context
        if "my order" in text and self.context.order_id:
            return self._lookup_order(self.context.order_id)

        # FAQ matching
        faq_answer = self._match_faq(text)
        if faq_answer:
            self.context.last_topic = "faq"
            return faq_answer

        # Greeting
        if re.search(r'\b(hi|hello|hey|good\s+\w+)\b', text):
            return (
                "Hello! Welcome to customer support. 😊\n"
                "How can I help you today? You can ask about:\n"
                "  • Your order status (share your order ID, e.g. ORD-1001)\n"
                "  • Returns & refunds\n"
                "  • Shipping & delivery\n"
                "  • Payments & coupons"
            )

        # Gratitude
        if re.search(r'\b(thank|thanks|great|perfect|awesome)\b', text):
            return "You're welcome! 😊 Is there anything else I can help with?"

        # Goodbye
        if re.search(r'\b(bye|goodbye|done|that\'s all)\b', text):
            return (
                "Thank you for contacting us! Have a great day. 👋\n"
                "Don't forget to rate this conversation."
            )

        # Fallback
        return (
            "I'm sorry, I didn't quite catch that. 🤔\n"
            "You can ask about order status, returns, shipping, or payments.\n"
            "Or type 'agent' to speak with a human."
        )

    def _extract_order_id(self, text: str) -> Optional[str]:
        m = re.search(r'ORD[-\s]?\d{4}', text.upper())
        return m.group(0).replace(" ", "-") if m else None

    def _lookup_order(self, order_id: str) -> str:
        order = ORDERS.get(order_id)
        if not order:
            return (
                f"I couldn't find order {order_id}. Please double-check the ID.\n"
                "Your order ID is in your confirmation email (format: ORD-XXXX)."
            )
        self.context.order_id = order_id
        status_icons = {
            "Delivered": "✅", "In Transit": "🚚",
            "Processing": "⏳", "Cancelled": "❌",
            "Out for Delivery": "🛵",
        }
        icon = status_icons.get(order["status"], "📦")
        return (
            f"{icon} Order {order_id}:\n"
            f"   Item:     {order['item']}\n"
            f"   Status:   {order['status']}\n"
            f"   Date:     {order['date']}\n\n"
            "Is there anything else I can help you with?"
        )

    def _match_faq(self, text: str) -> Optional[str]:
        for faq in FAQS:
            if any(kw in text for kw in faq["keywords"]):
                return faq["answer"]
        return None

    def _escalate(self) -> str:
        self.context.escalated = True
        return (
            "Of course — let me connect you with a human agent.\n"
            "⏳ Current wait time: approximately 3–5 minutes.\n"
            "You can also reach us directly:\n"
            "  📧 support@example.com\n"
            "  📞 1800-123-4567 (Mon–Fri, 9 AM–6 PM)"
        )


def main():
    print("=== Customer Support Bot Demo ===")
    print("(Type 'quit' to exit)\n")

    bot = CustomerSupportBot()
    print(f"Bot: {bot.respond('hello')}\n")

    while True:
        user_input = input("You: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("Bot: Goodbye! 👋")
            break
        print(f"Bot: {bot.respond(user_input)}\n")


if __name__ == "__main__":
    main()
