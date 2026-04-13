"""
A/B Testing Framework for Chatbot Responses
Chapter 13: Testing & Quality Assurance

Demonstrates how to set up, run, and evaluate A/B tests for
different chatbot response variants. Useful for testing:
  - Different welcome message phrasings
  - Response tone (formal vs. friendly)
  - Button labels and quick-reply options
  - Conversation flow alternatives
"""

import random
import json
import math
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
from collections import defaultdict


# ─────────────────────────────────────────────
# Data structures
# ─────────────────────────────────────────────

@dataclass
class Variant:
    """A single variant in an A/B test."""
    name:        str
    description: str
    response:    str
    weight:      float = 0.5   # Traffic split (0–1); variants must sum to 1.0


@dataclass
class ABTest:
    """Definition of an A/B test with two or more variants."""
    test_id:     str
    name:        str
    metric:      str           # What we're optimising (e.g. 'engagement', 'csat')
    variants:    List[Variant]
    created_at:  str = field(default_factory=lambda: datetime.utcnow().isoformat())
    is_active:   bool = True

    def __post_init__(self):
        total = sum(v.weight for v in self.variants)
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Variant weights must sum to 1.0 (got {total:.2f})")

    def select_variant(self) -> Variant:
        """Select a variant for a new session using weighted random selection."""
        r = random.random()
        cumulative = 0.0
        for variant in self.variants:
            cumulative += variant.weight
            if r <= cumulative:
                return variant
        return self.variants[-1]


@dataclass
class Impression:
    """One user seeing a variant."""
    session_id:  str
    variant_name: str
    timestamp:   str


@dataclass
class Conversion:
    """A positive outcome event (e.g. user engaged, gave high CSAT, completed task)."""
    session_id:  str
    variant_name: str
    value:       float   # 1.0 for binary; can be a score (e.g. CSAT 1–5)
    timestamp:   str


# ─────────────────────────────────────────────
# A/B Test Manager
# ─────────────────────────────────────────────

class ABTestManager:
    """
    Manages active A/B tests, records impressions/conversions,
    and computes statistical significance.
    """

    def __init__(self):
        self.tests:       Dict[str, ABTest]           = {}
        self.assignments: Dict[str, Dict[str, str]]   = defaultdict(dict)
        self.impressions: Dict[str, List[Impression]] = defaultdict(list)
        self.conversions: Dict[str, List[Conversion]] = defaultdict(list)

    def register_test(self, test: ABTest):
        self.tests[test.test_id] = test
        print(f"Registered A/B test: '{test.name}' [{test.test_id}]")

    def get_variant(self, test_id: str, session_id: str) -> Optional[Variant]:
        """
        Get (or consistently assign) a variant for a given session.
        The same session always gets the same variant.
        """
        if test_id not in self.tests:
            return None
        test = self.tests[test_id]
        if not test.is_active:
            return None

        # Sticky assignment — same session always gets the same variant
        if test_id not in self.assignments[session_id]:
            variant = test.select_variant()
            self.assignments[session_id][test_id] = variant.name

        variant_name = self.assignments[session_id][test_id]
        variant = next(v for v in test.variants if v.name == variant_name)

        # Record impression
        self.impressions[test_id].append(Impression(
            session_id=session_id,
            variant_name=variant_name,
            timestamp=datetime.utcnow().isoformat(),
        ))

        return variant

    def record_conversion(
        self,
        test_id:    str,
        session_id: str,
        value:      float = 1.0,
    ):
        """Record a conversion event for a session."""
        if session_id not in self.assignments:
            return
        variant_name = self.assignments[session_id].get(test_id)
        if not variant_name:
            return

        self.conversions[test_id].append(Conversion(
            session_id=session_id,
            variant_name=variant_name,
            value=value,
            timestamp=datetime.utcnow().isoformat(),
        ))

    def get_results(self, test_id: str) -> Dict:
        """Compute conversion rates and statistical significance for a test."""
        if test_id not in self.tests:
            return {"error": "Test not found."}

        test       = self.tests[test_id]
        results    = {}
        variant_data = {}

        for variant in test.variants:
            impressions  = [i for i in self.impressions[test_id]
                            if i.variant_name == variant.name]
            conversions  = [c for c in self.conversions[test_id]
                            if c.variant_name == variant.name]
            n = len(impressions)
            k = len(conversions)
            avg_value = sum(c.value for c in conversions) / k if k > 0 else 0.0
            rate      = k / n if n > 0 else 0.0

            variant_data[variant.name] = {
                "impressions":       n,
                "conversions":       k,
                "conversion_rate":   round(rate, 4),
                "avg_value":         round(avg_value, 4),
            }

        # Z-test for two-proportion significance (works for binary conversion)
        variant_names = [v.name for v in test.variants]
        significance  = None
        winner        = None

        if len(variant_names) == 2:
            a, b = variant_names
            na   = variant_data[a]["impressions"]
            nb   = variant_data[b]["impressions"]
            ka   = variant_data[a]["conversions"]
            kb   = variant_data[b]["conversions"]

            if na > 0 and nb > 0:
                pa = ka / na
                pb = kb / nb
                p_pool = (ka + kb) / (na + nb)
                if p_pool > 0 and p_pool < 1:
                    se    = math.sqrt(p_pool * (1 - p_pool) * (1/na + 1/nb))
                    z     = abs(pa - pb) / se if se > 0 else 0
                    # Approximate two-tailed p-value using normal distribution
                    p_val = 2 * (1 - _normal_cdf(z))
                    significance = {
                        "z_score":    round(z, 3),
                        "p_value":    round(p_val, 4),
                        "significant": p_val < 0.05,
                    }
                    if p_val < 0.05:
                        winner = a if pa > pb else b

        return {
            "test_id":      test_id,
            "test_name":    test.name,
            "metric":       test.metric,
            "variants":     variant_data,
            "significance": significance,
            "winner":       winner,
        }

    def print_report(self, test_id: str):
        results = self.get_results(test_id)
        if "error" in results:
            print(results["error"])
            return

        print(f"\n{'=' * 55}")
        print(f"  A/B TEST RESULTS: {results['test_name']}")
        print(f"  Metric: {results['metric']}")
        print(f"{'=' * 55}")

        for name, data in results["variants"].items():
            print(f"\n  Variant: {name}")
            print(f"    Impressions:     {data['impressions']}")
            print(f"    Conversions:     {data['conversions']}")
            print(f"    Conversion rate: {data['conversion_rate']:.1%}")
            print(f"    Avg value:       {data['avg_value']:.3f}")

        sig = results.get("significance")
        if sig:
            print(f"\n  Statistical Significance:")
            print(f"    Z-score:        {sig['z_score']}")
            print(f"    P-value:        {sig['p_value']}")
            print(f"    Significant:    {'Yes ✅' if sig['significant'] else 'No (need more data)'}")
            if results.get("winner"):
                print(f"    Winner:         {results['winner']} 🏆")
        else:
            print("\n  (Need at least 2 variants with data for significance test)")
        print("=" * 55)


def _normal_cdf(z: float) -> float:
    """Approximate cumulative distribution function for the standard normal."""
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


# ─────────────────────────────────────────────
# Demo
# ─────────────────────────────────────────────

def demo():
    print("=== A/B Testing Framework Demo ===\n")

    manager = ABTestManager()

    # Define a test: two welcome message variants
    test = ABTest(
        test_id="welcome_msg_v1",
        name="Welcome Message Phrasing",
        metric="first_turn_engagement",
        variants=[
            Variant(
                name="control",
                description="Formal welcome",
                response="Hello. How may I assist you today?",
                weight=0.5,
            ),
            Variant(
                name="treatment",
                description="Friendly welcome with emoji",
                response="Hey there! 👋 I'm here to help — what can I do for you?",
                weight=0.5,
            ),
        ]
    )
    manager.register_test(test)

    # Simulate 200 sessions
    random.seed(42)
    sessions = [f"session_{i:04d}" for i in range(200)]

    for session_id in sessions:
        variant = manager.get_variant("welcome_msg_v1", session_id)
        if variant:
            # Simulate that the "treatment" (friendly) variant has a higher
            # engagement rate (40%) vs control (28%)
            if variant.name == "treatment":
                engaged = random.random() < 0.40
            else:
                engaged = random.random() < 0.28

            if engaged:
                manager.record_conversion(
                    "welcome_msg_v1", session_id, value=1.0
                )

    manager.print_report("welcome_msg_v1")


if __name__ == "__main__":
    demo()
