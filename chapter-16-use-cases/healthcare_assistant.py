"""
Healthcare Appointment Assistant
Chapter 16: Industry Use-Cases — Healthcare

A conversational assistant for booking medical appointments.
Demonstrates:
  - Slot-filling for appointment booking (specialty, date, time)
  - Basic symptom triage with urgency classification
  - Appointment confirmation and reminders
  - Safe escalation for potential emergencies

⚠️  DISCLAIMER: This is a demonstration only.
    This bot is NOT a substitute for professional medical advice.
    Always consult a qualified healthcare professional for medical concerns.
"""

import re
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from enum import Enum, auto


# ─────────────────────────────────────────────
# Domain data
# ─────────────────────────────────────────────

SPECIALTIES = {
    "general": "General Physician (GP)",
    "gp": "General Physician (GP)",
    "cardio": "Cardiologist",
    "heart": "Cardiologist",
    "derma": "Dermatologist",
    "skin": "Dermatologist",
    "ortho": "Orthopaedist",
    "bone": "Orthopaedist",
    "neuro": "Neurologist",
    "eye": "Ophthalmologist",
    "dental": "Dentist",
    "teeth": "Dentist",
    "paediatric": "Paediatrician",
    "child": "Paediatrician",
    "gynaecology": "Gynaecologist",
    "mental health": "Psychiatrist / Psychologist",
    "psychology": "Psychiatrist / Psychologist",
}

AVAILABLE_SLOTS = {
    "Monday":    ["09:00", "10:30", "14:00", "15:30"],
    "Tuesday":   ["09:30", "11:00", "14:30", "16:00"],
    "Wednesday": ["10:00", "11:30", "15:00"],
    "Thursday":  ["09:00", "10:00", "13:30", "14:30"],
    "Friday":    ["09:30", "11:00", "14:00", "15:00", "16:30"],
}

EMERGENCY_SYMPTOMS = [
    "chest pain", "difficulty breathing", "can't breathe",
    "severe bleeding", "unconscious", "stroke", "heart attack",
    "seizure", "severe allergic reaction",
]

URGENT_SYMPTOMS = [
    "high fever", "severe pain", "vomiting blood",
    "broken bone", "deep cut", "head injury",
]


# ─────────────────────────────────────────────
# State machine
# ─────────────────────────────────────────────

class AppointmentState(Enum):
    WELCOME        = auto()
    TRIAGE         = auto()
    COLLECT_SPEC   = auto()
    COLLECT_DAY    = auto()
    COLLECT_TIME   = auto()
    CONFIRM        = auto()
    BOOKED         = auto()
    EMERGENCY      = auto()


@dataclass
class AppointmentSlots:
    specialty: Optional[str] = None
    day:       Optional[str] = None
    time:      Optional[str] = None
    name:      Optional[str] = None

    def is_complete(self) -> bool:
        return all([self.specialty, self.day, self.time])

    def summary(self) -> str:
        return (
            f"  Specialty: {self.specialty}\n"
            f"  Day:       {self.day}\n"
            f"  Time:      {self.time}\n"
        )


# ─────────────────────────────────────────────
# Healthcare Assistant
# ─────────────────────────────────────────────

class HealthcareAssistant:
    """Appointment booking assistant with symptom triage."""

    def __init__(self):
        self.state  = AppointmentState.WELCOME
        self.slots  = AppointmentSlots()

    def respond(self, user_input: str) -> str:
        text = user_input.lower().strip()

        # Emergency check at every turn
        if any(s in text for s in EMERGENCY_SYMPTOMS):
            self.state = AppointmentState.EMERGENCY
            return (
                "🚨 This sounds like a medical emergency.\n"
                "Please call emergency services immediately:\n"
                "  India: 108 (Ambulance)  |  112 (Emergency)\n"
                "  Do not wait to book an appointment."
            )

        if self.state == AppointmentState.WELCOME:
            return self._handle_welcome(text)
        if self.state == AppointmentState.TRIAGE:
            return self._handle_triage(text)
        if self.state == AppointmentState.COLLECT_SPEC:
            return self._handle_specialty(text)
        if self.state == AppointmentState.COLLECT_DAY:
            return self._handle_day(text)
        if self.state == AppointmentState.COLLECT_TIME:
            return self._handle_time(text, user_input)
        if self.state == AppointmentState.CONFIRM:
            return self._handle_confirm(text)
        if self.state == AppointmentState.BOOKED:
            return "Your appointment is already booked. Type 'new' to book another."

        return "I'm sorry, something went wrong. Please start over."

    def _handle_welcome(self, text: str) -> str:
        if re.search(r'\b(book|appointment|schedule|visit|see\s+a\s+doctor)\b', text):
            self.state = AppointmentState.TRIAGE
            return (
                "I can help you book an appointment. 🏥\n\n"
                "First, could you briefly describe your symptoms or the "
                "reason for your visit? This helps me suggest the right specialist.\n"
                "(Or type 'skip' to choose a specialty directly.)"
            )
        return (
            "Hello! Welcome to HealthBot. 👋\n"
            "I can help you:\n"
            "  • Book a doctor's appointment\n"
            "  • Find the right specialist\n"
            "  • Get general health information\n\n"
            "How can I assist you today?"
        )

    def _handle_triage(self, text: str) -> str:
        if text == "skip":
            self.state = AppointmentState.COLLECT_SPEC
            return self._ask_specialty()

        # Urgent but not emergency
        if any(s in text for s in URGENT_SYMPTOMS):
            self.state = AppointmentState.COLLECT_SPEC
            return (
                "⚠️  Your symptoms may need prompt attention.\n"
                "I'll help you book an appointment as soon as possible.\n\n"
                + self._ask_specialty()
            )

        # Suggest specialty from symptoms
        suggestion = self._suggest_specialty(text)
        self.state = AppointmentState.COLLECT_SPEC
        if suggestion:
            self.slots.specialty = suggestion
            self.state = AppointmentState.COLLECT_DAY
            return (
                f"Based on your description, I recommend seeing a "
                f"**{suggestion}**.\n\n"
                "Which day works best for you?\n"
                + self._format_available_days()
            )

        return self._ask_specialty()

    def _handle_specialty(self, text: str) -> str:
        specialty = self._extract_specialty(text)
        if specialty:
            self.slots.specialty = specialty
            self.state = AppointmentState.COLLECT_DAY
            return (
                f"Great — booking with a {specialty}.\n\n"
                "Which day would you prefer?\n"
                + self._format_available_days()
            )
        return (
            "I didn't recognise that specialty. Please choose from:\n"
            + ", ".join(set(SPECIALTIES.values()))
        )

    def _handle_day(self, text: str) -> str:
        for day in AVAILABLE_SLOTS:
            if day.lower() in text:
                self.slots.day = day
                self.state = AppointmentState.COLLECT_TIME
                slots = AVAILABLE_SLOTS[day]
                return (
                    f"Available times on {day}:\n"
                    + "\n".join(f"  • {t}" for t in slots)
                    + "\n\nWhich time works for you?"
                )
        return (
            "Please choose a day from our available schedule:\n"
            + self._format_available_days()
        )

    def _handle_time(self, text: str, original: str) -> str:
        time_match = re.search(r'\d{1,2}:\d{2}', original)
        if time_match:
            chosen = time_match.group(0)
            available = AVAILABLE_SLOTS.get(self.slots.day, [])
            if chosen in available:
                self.slots.time = chosen
                self.state = AppointmentState.CONFIRM
                return (
                    "Here's your appointment summary:\n\n"
                    + self.slots.summary()
                    + "\nConfirm booking? (yes / no)"
                )
            return f"That time isn't available. Please choose from: {', '.join(available)}"
        return "Please enter a time in HH:MM format, e.g. 09:00 or 14:30."

    def _handle_confirm(self, text: str) -> str:
        if re.search(r'\b(yes|confirm|ok|sure|book)\b', text):
            self.state = AppointmentState.BOOKED
            return (
                "✅ Appointment confirmed!\n\n"
                + self.slots.summary()
                + "\nYou'll receive a confirmation SMS/email shortly.\n"
                "Please arrive 10 minutes early and bring a valid ID.\n\n"
                "⚠️  REMINDER: This bot provides demonstration only. "
                "Always consult a real healthcare provider for medical advice."
            )
        if re.search(r'\b(no|cancel|change)\b', text):
            self.slots = AppointmentSlots()
            self.state = AppointmentState.COLLECT_SPEC
            return "No problem! Let's start over.\n\n" + self._ask_specialty()
        return "Please reply 'yes' to confirm or 'no' to change."

    def _suggest_specialty(self, text: str) -> Optional[str]:
        symptom_map = {
            ("chest", "heart", "palpitation"):     "Cardiologist",
            ("skin", "rash", "acne", "itch"):       "Dermatologist",
            ("bone", "joint", "knee", "back pain"): "Orthopaedist",
            ("headache", "migraine", "nerve"):       "Neurologist",
            ("eye", "vision", "blur"):               "Ophthalmologist",
            ("tooth", "teeth", "gum", "dental"):     "Dentist",
            ("child", "kid", "infant", "baby"):      "Paediatrician",
            ("anxiety", "depression", "mental"):     "Psychiatrist / Psychologist",
        }
        for keywords, specialty in symptom_map.items():
            if any(k in text for k in keywords):
                return specialty
        return None

    def _extract_specialty(self, text: str) -> Optional[str]:
        for keyword, specialty in SPECIALTIES.items():
            if keyword in text:
                return specialty
        return None

    def _ask_specialty(self) -> str:
        return (
            "What type of specialist do you need?\n"
            "  • General Physician (GP)\n"
            "  • Cardiologist (heart)\n"
            "  • Dermatologist (skin)\n"
            "  • Orthopaedist (bones/joints)\n"
            "  • Neurologist (brain/nerves)\n"
            "  • Dentist, Paediatrician, and more\n\n"
            "Just type the specialty or describe your concern."
        )

    def _format_available_days(self) -> str:
        return "\n".join(f"  • {day}" for day in AVAILABLE_SLOTS)


def main():
    print("=== Healthcare Appointment Assistant ===")
    print("⚠️  For demonstration only. Not a substitute for real medical advice.\n")
    print("(Type 'quit' to exit)\n")

    bot = HealthcareAssistant()
    print(f"Bot: {bot.respond('hello')}\n")

    while True:
        user_input = input("You: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit"):
            print("Bot: Take care! 👋")
            break
        print(f"Bot: {bot.respond(user_input)}\n")


if __name__ == "__main__":
    main()
