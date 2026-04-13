"""
Conversation Flow Builder
Chapter 8: Conversational Flows & Prototyping

This script demonstrates how to define, visualise, and execute
conversation flows using a declarative graph structure.
Each node represents a bot turn; edges represent user responses.

Run this script to see a visual representation of the flow
and to walk through it interactively.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
import json


# ─────────────────────────────────────────────
# Data structures
# ─────────────────────────────────────────────

@dataclass
class FlowNode:
    """A single turn/step in the conversation flow."""
    id:           str
    bot_message:  str
    transitions:  Dict[str, str] = field(default_factory=dict)
    # Optional: a function to run when entering this node
    on_enter:     Optional[Callable] = field(default=None, repr=False)
    is_terminal:  bool = False

    def add_transition(self, user_response_key: str, next_node_id: str):
        """Add a transition: when user says <key>, go to <next_node_id>."""
        self.transitions[user_response_key.lower()] = next_node_id
        return self  # fluent interface


@dataclass
class ConversationFlow:
    """A directed graph of FlowNodes representing a full conversation."""
    name:         str
    start_node_id: str
    nodes:        Dict[str, FlowNode] = field(default_factory=dict)

    def add_node(self, node: FlowNode) -> "ConversationFlow":
        self.nodes[node.id] = node
        return self

    def get_node(self, node_id: str) -> Optional[FlowNode]:
        return self.nodes.get(node_id)

    def validate(self) -> List[str]:
        """Check the flow for common problems. Returns a list of warnings."""
        warnings = []
        if self.start_node_id not in self.nodes:
            warnings.append(f"Start node '{self.start_node_id}' not found.")
        for node_id, node in self.nodes.items():
            for key, target in node.transitions.items():
                if target not in self.nodes:
                    warnings.append(
                        f"Node '{node_id}': transition '{key}' points to "
                        f"unknown node '{target}'."
                    )
            if not node.transitions and not node.is_terminal:
                warnings.append(
                    f"Node '{node_id}' has no transitions and is not marked terminal."
                )
        return warnings

    def visualise(self):
        """Print a simple ASCII diagram of the flow."""
        print(f"\n=== Flow: {self.name} ===")
        print(f"Start: {self.start_node_id}\n")
        for node_id, node in self.nodes.items():
            marker = "🔚" if node.is_terminal else "📍"
            start  = "▶ " if node_id == self.start_node_id else "  "
            print(f"{start}{marker} [{node_id}]")
            # Truncate long messages for readability
            msg = node.bot_message.replace("\n", " ")
            if len(msg) > 60:
                msg = msg[:57] + "..."
            print(f"      Bot: \"{msg}\"")
            for key, target in node.transitions.items():
                print(f"      ─ user: '{key}' ──→ [{target}]")
            print()

    def to_dict(self) -> dict:
        """Serialise the flow to a plain dict (JSON-compatible)."""
        return {
            "name": self.name,
            "start": self.start_node_id,
            "nodes": {
                nid: {
                    "bot_message":  n.bot_message,
                    "transitions":  n.transitions,
                    "is_terminal":  n.is_terminal,
                }
                for nid, n in self.nodes.items()
            }
        }

    def save(self, filepath: str):
        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
        print(f"Flow saved to {filepath}")

    @classmethod
    def load(cls, filepath: str) -> "ConversationFlow":
        with open(filepath) as f:
            data = json.load(f)
        flow = cls(name=data["name"], start_node_id=data["start"])
        for nid, nd in data["nodes"].items():
            node = FlowNode(
                id=nid,
                bot_message=nd["bot_message"],
                transitions=nd["transitions"],
                is_terminal=nd.get("is_terminal", False),
            )
            flow.add_node(node)
        return flow


# ─────────────────────────────────────────────
# Flow executor
# ─────────────────────────────────────────────

class FlowExecutor:
    """Walks through a ConversationFlow interactively."""

    FALLBACK_KEYS = ["other", "default", "*"]

    def __init__(self, flow: ConversationFlow):
        self.flow         = flow
        self.current_node = flow.get_node(flow.start_node_id)
        self.context: Dict = {}  # shared state / slot storage

    def _match_transition(self, user_input: str) -> Optional[str]:
        """Find which transition key best matches the user input."""
        text = user_input.lower().strip()
        node = self.current_node

        # Exact match
        if text in node.transitions:
            return node.transitions[text]

        # Substring match
        for key, target in node.transitions.items():
            if key in text or text in key:
                return target

        # Fallback transition
        for fb_key in self.FALLBACK_KEYS:
            if fb_key in node.transitions:
                return node.transitions[fb_key]

        return None

    def run(self):
        """Execute the flow interactively in the terminal."""
        print(f"\n=== Running flow: {self.flow.name} ===\n")

        while self.current_node:
            # Trigger on_enter hook
            if self.current_node.on_enter:
                self.current_node.on_enter(self.context)

            print(f"Bot: {self.current_node.bot_message}\n")

            if self.current_node.is_terminal:
                print("[End of conversation]")
                break

            user_input = input("You: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("quit", "exit"):
                print("Bot: Goodbye! 👋")
                break

            next_id = self._match_transition(user_input)
            if next_id:
                self.current_node = self.flow.get_node(next_id)
            else:
                print("Bot: I'm sorry, I didn't understand that. Could you rephrase?\n")


# ─────────────────────────────────────────────
# Sample flows
# ─────────────────────────────────────────────

def build_support_flow() -> ConversationFlow:
    """Build a simple customer support triage flow."""
    flow = ConversationFlow(
        name="Customer Support Triage",
        start_node_id="welcome"
    )

    flow.add_node(FlowNode(
        id="welcome",
        bot_message=(
            "Hello! Welcome to customer support. 👋\n"
            "How can I help you today?\n"
            "  1. Track my order\n"
            "  2. Return or refund\n"
            "  3. Technical issue\n"
            "  4. Something else"
        ),
        transitions={
            "1": "track_order", "track": "track_order",
            "2": "return",      "return": "return", "refund": "return",
            "3": "tech",        "technical": "tech",
            "4": "other_issue", "other": "other_issue",
            "*": "other_issue",
        }
    ))

    flow.add_node(FlowNode(
        id="track_order",
        bot_message=(
            "I can help you track your order! 📦\n"
            "Please visit our tracking page at support.example.com/track\n"
            "or provide your order number and I'll look it up.\n\n"
            "Was this helpful?\n  yes / no"
        ),
        transitions={"yes": "resolved", "no": "escalate", "*": "resolved"}
    ))

    flow.add_node(FlowNode(
        id="return",
        bot_message=(
            "For returns and refunds, our policy is:\n"
            "  • Items can be returned within 30 days of purchase.\n"
            "  • Refunds are processed within 5–7 business days.\n\n"
            "Would you like to initiate a return?\n  yes / no"
        ),
        transitions={"yes": "initiate_return", "no": "resolved"}
    ))

    flow.add_node(FlowNode(
        id="initiate_return",
        bot_message=(
            "To initiate a return, please visit support.example.com/returns\n"
            "and fill in your order number and reason.\n\n"
            "Is there anything else I can help with?\n  yes / no"
        ),
        transitions={"yes": "welcome", "no": "resolved"}
    ))

    flow.add_node(FlowNode(
        id="tech",
        bot_message=(
            "I'm sorry to hear you're having a technical issue. 🔧\n"
            "Let me connect you with a specialist.\n\n"
            "Please describe your issue briefly:"
        ),
        transitions={"*": "escalate"}
    ))

    flow.add_node(FlowNode(
        id="other_issue",
        bot_message=(
            "Sure, I'll do my best to help.\n"
            "Could you describe what you need assistance with?"
        ),
        transitions={"*": "escalate"}
    ))

    flow.add_node(FlowNode(
        id="escalate",
        bot_message=(
            "I'm transferring you to a human agent now. 🧑‍💼\n"
            "Average wait time: 2–3 minutes.\n"
            "Thank you for your patience!"
        ),
        is_terminal=True
    ))

    flow.add_node(FlowNode(
        id="resolved",
        bot_message=(
            "Great! I'm glad I could help. 😊\n"
            "Is there anything else you need?\n  yes / no"
        ),
        transitions={"yes": "welcome", "no": "goodbye"}
    ))

    flow.add_node(FlowNode(
        id="goodbye",
        bot_message="Thank you for contacting us. Have a wonderful day! 👋",
        is_terminal=True
    ))

    return flow


def build_onboarding_flow() -> ConversationFlow:
    """Build a simple user onboarding flow."""
    flow = ConversationFlow(
        name="User Onboarding",
        start_node_id="start"
    )

    flow.add_node(FlowNode(
        id="start",
        bot_message=(
            "Welcome! 🎉 I'm here to help you get set up.\n"
            "This will only take about 2 minutes.\n"
            "Ready to begin?\n  yes / no"
        ),
        transitions={"yes": "ask_name", "no": "skip_onboarding", "*": "ask_name"}
    ))

    flow.add_node(FlowNode(
        id="ask_name",
        bot_message="Great! What's your name?",
        transitions={"*": "ask_role"}
    ))

    flow.add_node(FlowNode(
        id="ask_role",
        bot_message=(
            "Nice to meet you! What best describes your role?\n"
            "  1. Developer\n"
            "  2. Designer\n"
            "  3. Product Manager\n"
            "  4. Other"
        ),
        transitions={
            "1": "developer_path", "developer": "developer_path",
            "2": "designer_path",  "designer":  "designer_path",
            "3": "pm_path",        "product":   "pm_path",
            "4": "generic_path",   "*":          "generic_path",
        }
    ))

    for path_id, msg in [
        ("developer_path",
         "Perfect! We've tailored your dashboard for developers.\n"
         "Check out our API docs and code samples to get started.\n"
         "Ready to explore?\n  yes / no"),
        ("designer_path",
         "Wonderful! We've set up your design workspace.\n"
         "Our UI kit and Figma templates are ready for you.\n"
         "Ready to explore?\n  yes / no"),
        ("pm_path",
         "Great! We've configured your analytics and roadmap views.\n"
         "Dive into your first project whenever you're ready.\n"
         "Ready to explore?\n  yes / no"),
        ("generic_path",
         "All set! Your workspace is ready.\n"
         "We'll guide you through the key features step by step.\n"
         "Ready to explore?\n  yes / no"),
    ]:
        flow.add_node(FlowNode(
            id=path_id,
            bot_message=msg,
            transitions={"yes": "complete", "no": "complete", "*": "complete"}
        ))

    flow.add_node(FlowNode(
        id="skip_onboarding",
        bot_message=(
            "No problem! You can always run onboarding again from the settings menu.\n"
            "Welcome aboard! 🚀"
        ),
        is_terminal=True
    ))

    flow.add_node(FlowNode(
        id="complete",
        bot_message=(
            "You're all set! 🎊\n"
            "Welcome aboard. Feel free to explore, and I'm here if you need anything."
        ),
        is_terminal=True
    ))

    return flow


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    # Build the support flow and visualise it
    support_flow = build_support_flow()

    warnings = support_flow.validate()
    if warnings:
        print("⚠️  Flow warnings:")
        for w in warnings:
            print(f"   {w}")
    else:
        print("✅ Flow validation passed.\n")

    support_flow.visualise()

    # Save to JSON
    support_flow.save("support_flow.json")

    # Also build and visualise onboarding flow
    onboarding_flow = build_onboarding_flow()
    onboarding_flow.visualise()

    # Run one of the flows interactively
    print("\nWhich flow would you like to run interactively?")
    print("  1. Customer Support Triage")
    print("  2. User Onboarding")
    choice = input("Enter 1 or 2: ").strip()

    flow = support_flow if choice == "1" else onboarding_flow
    executor = FlowExecutor(flow)
    executor.run()


if __name__ == "__main__":
    main()
