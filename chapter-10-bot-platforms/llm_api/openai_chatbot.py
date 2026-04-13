"""
OpenAI API Chatbot Example
Chapter 10: Bot Development Platforms

This script demonstrates how to build a chatbot using OpenAI's GPT models.
It shows conversation management, system prompts, and function calling.
"""

import os
from openai import OpenAI
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()


class OpenAIChatbot:
    """A chatbot powered by OpenAI's GPT models"""
    
    def __init__(self, model="gpt-4-turbo-preview", system_prompt=None):
        """
        Initialize the chatbot
        
        Args:
            model: OpenAI model to use (gpt-4, gpt-3.5-turbo, etc.)
            system_prompt: System message to define chatbot behavior
        """
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model
        self.conversation_history = []
        
        # Set default system prompt if none provided
        if system_prompt is None:
            system_prompt = """You are a helpful, friendly AI assistant. 
            You provide clear, concise answers and ask clarifying questions when needed.
            You maintain a professional yet warm tone."""
        
        self.conversation_history.append({
            "role": "system",
            "content": system_prompt
        })
    
    def chat(self, user_message):
        """
        Send a message and get a response
        
        Args:
            user_message: The user's message
            
        Returns:
            The assistant's response
        """
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        try:
            # Get response from OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.conversation_history,
                temperature=0.7,
                max_tokens=500
            )
            
            # Extract assistant's response
            assistant_message = response.choices[0].message.content
            
            # Add to conversation history
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })
            
            # Track token usage
            self.last_token_usage = {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            }
            
            return assistant_message
            
        except Exception as e:
            return f"Error: {str(e)}"
    
    def chat_stream(self, user_message):
        """
        Send a message and stream the response
        
        Args:
            user_message: The user's message
            
        Yields:
            Chunks of the assistant's response
        """
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        try:
            # Get streaming response from OpenAI
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=self.conversation_history,
                temperature=0.7,
                max_tokens=500,
                stream=True
            )
            
            full_response = ""
            
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield content
            
            # Add complete response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": full_response
            })
            
        except Exception as e:
            yield f"Error: {str(e)}"
    
    def get_token_usage(self):
        """Get token usage from last API call"""
        return self.last_token_usage if hasattr(self, 'last_token_usage') else None
    
    def clear_history(self):
        """Clear conversation history (keeps system prompt)"""
        system_message = self.conversation_history[0]
        self.conversation_history = [system_message]
    
    def export_conversation(self, filepath):
        """Export conversation history to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.conversation_history, f, indent=2)
        print(f"Conversation exported to {filepath}")


def demo_basic_chat():
    """Demonstrate basic chatbot functionality"""
    print("=== Basic OpenAI Chatbot Demo ===\n")
    
    # Create chatbot with custom system prompt
    system_prompt = """You are a customer support assistant for a fictional airline called SkyHigh Airlines.
    You help customers with bookings, flight information, and general inquiries.
    Be professional, helpful, and empathetic."""
    
    chatbot = OpenAIChatbot(
        model="gpt-3.5-turbo",  # Using 3.5-turbo for cost efficiency
        system_prompt=system_prompt
    )
    
    # Simulate a conversation
    test_messages = [
        "Hello, I need help with my booking",
        "I want to change my flight from New York to London",
        "What's your cancellation policy?",
    ]
    
    for message in test_messages:
        print(f"User: {message}")
        response = chatbot.chat(message)
        print(f"Assistant: {response}")
        
        # Show token usage
        usage = chatbot.get_token_usage()
        if usage:
            print(f"[Tokens used: {usage['total_tokens']}]")
        print()


def demo_streaming_chat():
    """Demonstrate streaming responses"""
    print("\n=== Streaming Response Demo ===\n")
    
    chatbot = OpenAIChatbot(model="gpt-3.5-turbo")
    
    user_message = "Explain how chatbots work in simple terms"
    print(f"User: {user_message}")
    print("Assistant: ", end="", flush=True)
    
    for chunk in chatbot.chat_stream(user_message):
        print(chunk, end="", flush=True)
    
    print("\n")


def interactive_mode():
    """Run chatbot in interactive mode"""
    print("\n=== Interactive Chatbot ===")
    print("Commands: 'quit' to exit, 'clear' to reset conversation, 'export' to save\n")
    
    # Let user choose personality
    print("Choose chatbot personality:")
    print("1. Professional Assistant")
    print("2. Friendly Tutor")
    print("3. Creative Writer")
    print("4. Technical Expert")
    
    choice = input("\nEnter choice (1-4) or press Enter for default: ").strip()
    
    personalities = {
        "1": "You are a professional assistant. Provide clear, concise, business-appropriate responses.",
        "2": "You are a friendly tutor. Explain concepts clearly and encourage learning with enthusiasm.",
        "3": "You are a creative writer. Use vivid language and help with storytelling and creative projects.",
        "4": "You are a technical expert. Provide detailed technical explanations with examples and best practices."
    }
    
    system_prompt = personalities.get(choice, None)
    chatbot = OpenAIChatbot(system_prompt=system_prompt)
    
    print("\nChatbot ready! Start chatting...\n")
    
    while True:
        user_input = input("You: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break
        elif user_input.lower() == 'clear':
            chatbot.clear_history()
            print("[Conversation history cleared]")
            continue
        elif user_input.lower() == 'export':
            chatbot.export_conversation("conversation_history.json")
            continue
        
        if user_input:
            response = chatbot.chat(user_input)
            print(f"\nAssistant: {response}\n")
            
            # Show token usage
            usage = chatbot.get_token_usage()
            if usage:
                print(f"[Tokens: {usage['total_tokens']}]\n")


def main():
    """Main function"""
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found in environment variables")
        print("Please set it in your .env file or environment")
        return
    
    # Run demos
    demo_basic_chat()
    demo_streaming_chat()
    
    # Interactive mode
    interactive_mode()


if __name__ == "__main__":
    main()
