# Chapter 10: Large Language Model APIs

This directory contains practical examples of integrating modern LLM APIs into chatbot applications.

## Examples Included

### 1. OpenAI API Integration (`openai_chatbot.py`)
Demonstrates how to build a chatbot using OpenAI's GPT models (GPT-4, GPT-3.5-turbo).

**Features:**
- Basic chat completion
- Conversation history management
- System prompts for personality
- Streaming responses
- Function calling

### 2. Anthropic Claude Integration (`anthropic_chatbot.py`)
Shows how to use Anthropic's Claude API for conversational AI.

**Features:**
- Claude-specific prompt formatting
- Multi-turn conversations
- Safety and content filtering
- Context window management

### 3. Google Gemini Integration (`gemini_chatbot.py`)
Demonstrates Google's Gemini API for multimodal conversations.

**Features:**
- Text-based conversations
- Multimodal input (text + images)
- Safety settings
- Structured output

## Setup

1. Install required packages:
```bash
pip install openai anthropic google-generativeai
```

2. Set up your API keys in `.env` file:
```env
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GOOGLE_API_KEY=your_google_key
```

3. Run any example:
```bash
python openai_chatbot.py
python anthropic_chatbot.py
python gemini_chatbot.py
```

## Key Concepts

### Conversation History
All examples demonstrate how to maintain conversation context across multiple turns.

### System Prompts
Learn how to define chatbot personality and behavior through system prompts.

### Error Handling
Proper error handling for API failures, rate limits, and network issues.

### Cost Management
Understanding token usage and implementing cost controls.

## Related Book Sections

- Section 10.2: Large Language Model APIs
- Section 10.4: The Future of Bot Development Platforms
- Section 17.1: Generative AI in Conversation Design
