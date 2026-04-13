"""
Automated Usability Testing for Chatbots
Chapter 13: Testing & Quality Assurance

Runs a suite of scripted test conversations against a chatbot endpoint
and scores each interaction on:
  - Response relevance (intent match)
  - Response latency
  - Fallback rate
  - Turn completion

Works against any chatbot that exposes a POST /chat endpoint
(compatible with chatbot_backend.py from Chapter 11).
"""

import time
import json
import statistics
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


# ─────────────────────────────────────────────
# Test data structures
# ─────────────────────────────────────────────

@dataclass
class TestTurn:
    """A single user→bot exchange in a test case."""
    user_message:     str
    expected_intent:  Optional[str]  = None
    expected_keywords: List[str]     = field(default_factory=list)
    should_not_contain: List[str]    = field(default_factory=list)


@dataclass
class TestCase:
    """A complete scripted test conversation."""
    name:        str
    description: str
    turns:       List[TestTurn]


@dataclass
class TurnResult:
    turn:             int
    user_message:     str
    bot_response:     str
    detected_intent:  Optional[str]
    expected_intent:  Optional[str]
    intent_match:     bool
    keyword_hits:     List[str]
    keyword_misses:   List[str]
    forbidden_hits:   List[str]
    latency_ms:       float
    passed:           bool


@dataclass
class TestCaseResult:
    test_case:    TestCase
    turn_results: List[TurnResult]
    passed:       bool
    score:        float          # 0.0–1.0

    def summary(self) -> str:
        status = "✅ PASS" if self.passed else "❌ FAIL"
        return (
            f"{status}  {self.test_case.name}  "
            f"score={self.score:.0%}  "
            f"turns={len(self.turn_results)}"
        )


# ─────────────────────────────────────────────
# Mock chatbot (used when no live endpoint available)
# ─────────────────────────────────────────────

class MockChatbot:
    """
    A simple rule-based mock chatbot for running tests locally
    without needing a running server.
    """
    RESPONSES = {
        "hello":    ("Hi! How can I help you today?",         "greeting"),
        "hi":       ("Hello! How can I help?",                "greeting"),
        "hours":    ("We're open Monday–Friday, 9 AM–6 PM.",  "hours"),
        "return":   ("Returns are accepted within 30 days.",  "return"),
        "refund":   ("Refunds take 5–7 business days.",       "refund"),
        "shipping": ("Standard delivery takes 3–5 days.",     "shipping"),
        "thanks":   ("You're welcome!",                       "thanks"),
        "bye":      ("Goodbye! Have a great day!",            "farewell"),
        "cancel":   ("I've cancelled your request.",          "cancel"),
    }

    def chat(self, message: str, session_id: str = "test") -> Dict:
        msg_lower = message.lower()
        for keyword, (response, intent) in self.RESPONSES.items():
            if keyword in msg_lower:
                return {"response": response, "intent": intent, "session_id": session_id}
        return {
            "response":   "I'm sorry, I didn't understand that.",
            "intent":     "fallback",
            "session_id": session_id,
        }


# ─────────────────────────────────────────────
# Test runner
# ─────────────────────────────────────────────

class ChatbotTestRunner:
    """
    Runs scripted test cases against a chatbot and produces
    a detailed report.
    """

    def __init__(self, endpoint: Optional[str] = None):
        """
        Args:
            endpoint: Base URL of the chatbot API (e.g. 'http://localhost:5000').
                      If None, uses the built-in MockChatbot.
        """
        self.endpoint = endpoint
        self.mock     = MockChatbot() if not endpoint else None
        self.results: List[TestCaseResult] = []

    def _call_chatbot(self, message: str, session_id: str) -> Dict:
        """Send a message to the chatbot and return the response dict."""
        if self.mock:
            return self.mock.chat(message, session_id)

        if not REQUESTS_AVAILABLE:
            raise RuntimeError("Install 'requests' to use a live endpoint.")

        response = requests.post(
            f"{self.endpoint}/chat",
            json={"message": message, "session_id": session_id},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    def run_test_case(self, test_case: TestCase) -> TestCaseResult:
        """Execute all turns in a test case and collect results."""
        session_id   = f"test_{int(time.time())}"
        turn_results = []
        all_passed   = True

        for i, turn in enumerate(test_case.turns, start=1):
            t0 = time.monotonic()
            response = self._call_chatbot(turn.user_message, session_id)
            latency  = (time.monotonic() - t0) * 1000  # ms

            bot_text = response.get("response", "")
            intent   = response.get("intent", "unknown")

            # Scoring
            intent_match   = (intent == turn.expected_intent) if turn.expected_intent else True
            bot_lower      = bot_text.lower()
            keyword_hits   = [k for k in turn.expected_keywords   if k.lower() in bot_lower]
            keyword_misses = [k for k in turn.expected_keywords   if k.lower() not in bot_lower]
            forbidden_hits = [k for k in turn.should_not_contain  if k.lower() in bot_lower]

            turn_passed = (
                intent_match and
                len(keyword_misses) == 0 and
                len(forbidden_hits) == 0
            )
            all_passed = all_passed and turn_passed

            turn_results.append(TurnResult(
                turn=i,
                user_message=turn.user_message,
                bot_response=bot_text,
                detected_intent=intent,
                expected_intent=turn.expected_intent,
                intent_match=intent_match,
                keyword_hits=keyword_hits,
                keyword_misses=keyword_misses,
                forbidden_hits=forbidden_hits,
                latency_ms=round(latency, 1),
                passed=turn_passed,
            ))

        passed_turns = sum(1 for r in turn_results if r.passed)
        score = passed_turns / len(turn_results) if turn_results else 0.0

        return TestCaseResult(
            test_case=test_case,
            turn_results=turn_results,
            passed=all_passed,
            score=score,
        )

    def run_all(self, test_cases: List[TestCase]) -> List[TestCaseResult]:
        """Run all test cases and store results."""
        self.results = []
        for tc in test_cases:
            result = self.run_test_case(tc)
            self.results.append(result)
            print(result.summary())
        return self.results

    def print_full_report(self):
        """Print a detailed test report to stdout."""
        if not self.results:
            print("No results to report.")
            return

        print("\n" + "=" * 60)
        print("  CHATBOT USABILITY TEST REPORT")
        print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        all_latencies = []
        total_turns   = 0
        passed_turns  = 0
        fallback_count = 0

        for result in self.results:
            print(f"\n{'─' * 50}")
            print(f"Test Case: {result.test_case.name}")
            print(f"Description: {result.test_case.description}")
            print(f"Overall: {'PASS ✅' if result.passed else 'FAIL ❌'}  "
                  f"Score: {result.score:.0%}")

            for tr in result.turn_results:
                status = "✅" if tr.passed else "❌"
                print(f"\n  {status} Turn {tr.turn}")
                print(f"     User:    {tr.user_message}")
                print(f"     Bot:     {tr.bot_response[:80]}")
                print(f"     Intent:  {tr.detected_intent} "
                      f"(expected: {tr.expected_intent or 'any'})")
                print(f"     Latency: {tr.latency_ms:.1f} ms")

                if tr.keyword_misses:
                    print(f"     ⚠️  Missing keywords: {tr.keyword_misses}")
                if tr.forbidden_hits:
                    print(f"     🚫 Forbidden content found: {tr.forbidden_hits}")

                all_latencies.append(tr.latency_ms)
                total_turns += 1
                if tr.passed:
                    passed_turns += 1
                if tr.detected_intent == "fallback":
                    fallback_count += 1

        print(f"\n{'=' * 60}")
        print("  AGGREGATE METRICS")
        print("=" * 60)
        print(f"  Total test cases:  {len(self.results)}")
        print(f"  Cases passed:      {sum(1 for r in self.results if r.passed)}")
        print(f"  Total turns:       {total_turns}")
        print(f"  Turns passed:      {passed_turns} ({passed_turns/total_turns:.0%})")
        print(f"  Fallback rate:     {fallback_count}/{total_turns} "
              f"({fallback_count/total_turns:.0%})")
        if all_latencies:
            print(f"  Avg latency:       {statistics.mean(all_latencies):.1f} ms")
            print(f"  P95 latency:       "
                  f"{sorted(all_latencies)[int(len(all_latencies)*0.95)]:.1f} ms")
        print("=" * 60)


# ─────────────────────────────────────────────
# Test suite definition
# ─────────────────────────────────────────────

def get_test_suite() -> List[TestCase]:
    return [
        TestCase(
            name="Basic Greeting Flow",
            description="Verifies the bot responds correctly to greetings and farewells.",
            turns=[
                TestTurn("Hello!", expected_intent="greeting",
                         expected_keywords=["help", "assist", "hi", "hello"]),
                TestTurn("Thanks, goodbye!", expected_intent="farewell",
                         expected_keywords=["goodbye", "bye", "day"],
                         should_not_contain=["error", "sorry"]),
            ]
        ),
        TestCase(
            name="Store Hours Query",
            description="Verifies the bot provides accurate opening hours.",
            turns=[
                TestTurn("Hi", expected_intent="greeting"),
                TestTurn("What are your opening hours?", expected_intent="hours",
                         expected_keywords=["monday", "friday", "9", "6"]),
                TestTurn("Thank you", expected_intent="thanks"),
            ]
        ),
        TestCase(
            name="Return Policy",
            description="Verifies the bot explains the return and refund policy.",
            turns=[
                TestTurn("I want to return something", expected_intent="return",
                         expected_keywords=["30", "day"]),
                TestTurn("How long does a refund take?", expected_intent="refund",
                         expected_keywords=["5", "7", "business"]),
            ]
        ),
        TestCase(
            name="Fallback Handling",
            description="Verifies the bot handles nonsensical input gracefully.",
            turns=[
                TestTurn("xyzzy frobulate the whatsit",
                         expected_intent="fallback",
                         expected_keywords=["sorry", "understand", "help"],
                         should_not_contain=["crash", "error 500"]),
            ]
        ),
    ]


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("Running chatbot usability tests against MockChatbot...\n")
    runner = ChatbotTestRunner()   # Uses mock; pass endpoint URL for live testing
    runner.run_all(get_test_suite())
    runner.print_full_report()
