"""
NLU Training Data Analysis & Optimization
Chapter 13: Testing & Quality Assurance

Tools for analysing the quality of NLU training data and identifying
common issues before they reach production:
  - Class imbalance detection
  - Duplicate and near-duplicate utterance detection
  - Short/low-quality utterance flagging
  - Intent confusion analysis (overlapping vocabulary)
  - Suggestions for improving coverage
"""

import re
import math
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Set


# ─────────────────────────────────────────────
# Sample NLU training data
# ─────────────────────────────────────────────

SAMPLE_TRAINING_DATA = {
    "greeting": [
        "hello",
        "hi",
        "hey",
        "good morning",
        "good evening",
        "hi there",
        "hello there",
        "hey there",
        "greetings",
        "howdy",
    ],
    "book_flight": [
        "I want to book a flight",
        "book a ticket to Paris",
        "reserve a flight",
        "I need to fly to London",
        "schedule a flight",
        "I'd like to book a flight",
        "book flight",
        "I want to fly",
        "help me book a flight",
        "need a flight",
        "book a flight to Mumbai",
    ],
    "check_status": [
        "what's my booking status",
        "check my reservation",
        "where is my order",
        "track my booking",
        "status of my flight",
        "what's the status",
        "check status",
        "order status",
        # Near-duplicate pair intentionally included for demo:
        "check my reservation",
        "where is my booking",
    ],
    "cancel": [
        "cancel my booking",
        "I want to cancel",
        "cancel my reservation",
        "remove my booking",
        "delete my order",
        "cancel",
        # Very short, low-information utterances
        "no",
        "stop",
    ],
    "help": [
        "I need help",
        "can you help me",
        "what can you do",
        "how does this work",
        "support",
        "help me",
        "help",
        # Overlap with greeting intent
        "hi can you help",
        "hello I need help",
    ],
    "farewell": [
        "bye",
        "goodbye",
        "see you later",
        "talk to you later",
        "have a nice day",
        "bye bye",
    ],
}


# ─────────────────────────────────────────────
# Analysis tools
# ─────────────────────────────────────────────

@dataclass
class NLUIssue:
    severity:    str    # "error" | "warning" | "info"
    intent:      str
    message:     str
    examples:    List[str] = field(default_factory=list)


class NLUAnalyzer:
    """
    Analyses a set of NLU training data and surfaces quality issues.
    """

    MIN_EXAMPLES_PER_INTENT = 10
    MAX_DUPLICATE_RATIO     = 0.10   # More than 10% duplicates = warning
    SHORT_UTTERANCE_WORDS   = 2      # Utterances with ≤ this many words are flagged

    def __init__(self, training_data: Dict[str, List[str]]):
        self.data   = training_data
        self.issues: List[NLUIssue] = []

    def analyse(self) -> List[NLUIssue]:
        """Run all checks and return a list of issues."""
        self.issues = []
        self._check_class_balance()
        self._check_duplicates()
        self._check_short_utterances()
        self._check_intent_confusion()
        return self.issues

    def _check_class_balance(self):
        counts = {intent: len(examples) for intent, examples in self.data.items()}
        total  = sum(counts.values())
        avg    = total / len(counts)

        for intent, count in counts.items():
            if count < self.MIN_EXAMPLES_PER_INTENT:
                self.issues.append(NLUIssue(
                    severity="error",
                    intent=intent,
                    message=(
                        f"Only {count} training examples. "
                        f"Minimum recommended: {self.MIN_EXAMPLES_PER_INTENT}."
                    ),
                ))
            elif count < avg * 0.5:
                self.issues.append(NLUIssue(
                    severity="warning",
                    intent=intent,
                    message=(
                        f"{count} examples — significantly below average "
                        f"({avg:.0f}). Consider adding more data."
                    ),
                ))

    def _check_duplicates(self):
        for intent, examples in self.data.items():
            normalised = [self._normalise(e) for e in examples]
            counts     = Counter(normalised)
            duplicates = [text for text, count in counts.items() if count > 1]

            if not duplicates:
                continue

            ratio = len(duplicates) / len(examples)
            severity = "error" if ratio > self.MAX_DUPLICATE_RATIO else "warning"
            self.issues.append(NLUIssue(
                severity=severity,
                intent=intent,
                message=f"{len(duplicates)} duplicate utterance(s) found.",
                examples=duplicates[:5],
            ))

    def _check_short_utterances(self):
        for intent, examples in self.data.items():
            short = [e for e in examples
                     if len(e.split()) <= self.SHORT_UTTERANCE_WORDS]
            if short:
                self.issues.append(NLUIssue(
                    severity="warning",
                    intent=intent,
                    message=(
                        f"{len(short)} very short utterance(s) "
                        f"(≤{self.SHORT_UTTERANCE_WORDS} words). "
                        "These may be too ambiguous for reliable classification."
                    ),
                    examples=short,
                ))

    def _check_intent_confusion(self):
        """Flag intents that share many common words — likely to confuse the model."""
        intent_words: Dict[str, Set[str]] = {}
        for intent, examples in self.data.items():
            words = set()
            for e in examples:
                words.update(self._tokenise(e))
            # Remove stop words
            intent_words[intent] = words - self._stop_words()

        intents = list(intent_words.keys())
        for i in range(len(intents)):
            for j in range(i + 1, len(intents)):
                a, b   = intents[i], intents[j]
                shared = intent_words[a] & intent_words[b]
                overlap_ratio = len(shared) / max(
                    len(intent_words[a]), len(intent_words[b]), 1
                )
                if overlap_ratio > 0.25 and shared:
                    self.issues.append(NLUIssue(
                        severity="warning",
                        intent=f"{a} ↔ {b}",
                        message=(
                            f"High vocabulary overlap ({overlap_ratio:.0%}). "
                            "The model may confuse these intents."
                        ),
                        examples=sorted(shared)[:8],
                    ))

    @staticmethod
    def _normalise(text: str) -> str:
        return re.sub(r'\s+', ' ', text.lower().strip())

    @staticmethod
    def _tokenise(text: str) -> Set[str]:
        return set(re.findall(r'\b[a-z]+\b', text.lower()))

    @staticmethod
    def _stop_words() -> Set[str]:
        return {
            "i", "a", "an", "the", "to", "my", "me", "you", "it", "is", "of",
            "and", "or", "in", "on", "at", "can", "do", "be", "am", "are", "was",
            "want", "need", "like", "please", "would", "could", "get", "have",
        }

    def print_report(self):
        print("\n" + "=" * 55)
        print("  NLU TRAINING DATA ANALYSIS REPORT")
        print("=" * 55)

        intents = list(self.data.keys())
        counts  = {i: len(self.data[i]) for i in intents}
        total   = sum(counts.values())
        print(f"\n  Total intents:    {len(intents)}")
        print(f"  Total utterances: {total}")
        print(f"\n  {'Intent':<25} {'Examples':>8}")
        print(f"  {'-' * 35}")
        for intent in sorted(intents):
            bar = "█" * min(counts[intent], 20)
            print(f"  {intent:<25} {counts[intent]:>4}  {bar}")

        if not self.issues:
            print("\n  ✅ No issues found. Training data looks good!")
        else:
            errors   = [i for i in self.issues if i.severity == "error"]
            warnings = [i for i in self.issues if i.severity == "warning"]

            print(f"\n  {'─' * 50}")
            print(f"  Issues found: {len(errors)} error(s), {len(warnings)} warning(s)")
            print(f"  {'─' * 50}")

            for issue in self.issues:
                icon = "🔴" if issue.severity == "error" else "🟡"
                print(f"\n  {icon} [{issue.severity.upper()}] Intent: {issue.intent}")
                print(f"     {issue.message}")
                if issue.examples:
                    print(f"     Examples: {issue.examples}")

        print("\n" + "=" * 55)

    def generate_suggestions(self) -> List[str]:
        """Return actionable suggestions based on the issues found."""
        suggestions = []
        for issue in self.issues:
            if "duplicate" in issue.message.lower():
                suggestions.append(
                    f"Remove duplicates from '{issue.intent}' to avoid "
                    "training data memorisation."
                )
            if "short" in issue.message.lower():
                suggestions.append(
                    f"Expand short utterances in '{issue.intent}' with more "
                    "natural phrasing to improve generalisation."
                )
            if "overlap" in issue.message.lower():
                suggestions.append(
                    f"Review shared vocabulary between {issue.intent}. "
                    "Consider adding negative examples (entity-level disambiguation)."
                )
            if "Only" in issue.message or "below average" in issue.message:
                suggestions.append(
                    f"Add more training examples to '{issue.intent}'. "
                    "Aim for at least 10–20 diverse phrasings."
                )
        return list(dict.fromkeys(suggestions))  # deduplicate


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

if __name__ == "__main__":
    analyzer = NLUAnalyzer(SAMPLE_TRAINING_DATA)
    issues   = analyzer.analyse()
    analyzer.print_report()

    suggestions = analyzer.generate_suggestions()
    if suggestions:
        print("\n  IMPROVEMENT SUGGESTIONS")
        print("  " + "─" * 50)
        for i, s in enumerate(suggestions, 1):
            print(f"  {i}. {s}")
        print()
