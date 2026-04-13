# Chapter 8: Conversational Flows & Prototyping

This directory contains working implementations of the dialogue management and conversation flow concepts covered in Chapter 8.

## Files

| File | Description |
|------|-------------|
| `dialogue_manager.py` | A finite-state-machine (FSM) dialogue manager for a flight booking assistant |
| `conversation_flow_builder.py` | A declarative flow builder for designing, visualising, and executing conversation flows |

---

## dialogue_manager.py

Implements a **state machine dialogue manager** — the same pattern described in the Conversation State Machine diagram (Figure 8.1).

**Key concepts demonstrated:**
- Dialogue states (GREETING, COLLECT_ORIGIN, COLLECT_DATE, etc.)
- Slot filling (collecting origin, destination, and date incrementally)
- Simple pattern-based NLU (intent detection + entity extraction)
- Graceful fallback and cancellation handling
- Conversation history tracking

**Run it:**
```bash
python dialogue_manager.py
```

The script first runs a scripted demo, then switches to interactive mode where you can talk to the flight booking bot yourself.

---

## conversation_flow_builder.py

Demonstrates a **declarative, graph-based approach** to designing conversation flows — the equivalent of what you'd sketch in Botpress or draw as a flowchart.

**Key concepts demonstrated:**
- Defining flows as directed graphs (nodes = bot turns, edges = user responses)
- Flow validation (detecting broken links and dead-end nodes)
- ASCII visualisation of the flow graph
- Serialisation/deserialisation to JSON
- Interactive flow execution via `FlowExecutor`

Two sample flows are included:
1. **Customer Support Triage** — routes users to tracking, returns, technical support, or escalation
2. **User Onboarding** — personalises the experience based on the user's role

**Run it:**
```bash
python conversation_flow_builder.py
```

---

## Connection to Rasa (Chapter 10)

The `stories.yml` file in `chapter-10-bot-platforms/rasa/` shows how the flow patterns from this chapter translate into Rasa training data. Compare the state transitions in `dialogue_manager.py` with the story paths in `stories.yml` to see the direct correspondence.

## Requirements

```bash
pip install -r ../../requirements.txt
```

No external APIs needed — these examples run entirely locally.
