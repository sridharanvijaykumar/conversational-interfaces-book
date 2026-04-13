"""
Intent Classification Example
Chapter 3: NLP Fundamentals

This script demonstrates how to build a simple intent classifier for a chatbot.
Intent classification is the process of determining what the user wants to accomplish.
"""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import pickle


# Sample training data - in practice, you'd have much more data
TRAINING_DATA = [
    # Greeting intents
    ("hello", "greeting"),
    ("hi there", "greeting"),
    ("good morning", "greeting"),
    ("hey", "greeting"),
    ("greetings", "greeting"),
    
    # Booking intents
    ("I want to book a flight", "book_flight"),
    ("book a ticket to Paris", "book_flight"),
    ("reserve a flight", "book_flight"),
    ("I need to fly to London", "book_flight"),
    ("schedule a flight", "book_flight"),
    
    # Check status intents
    ("what's my booking status", "check_status"),
    ("check my reservation", "check_status"),
    ("where is my order", "check_status"),
    ("track my booking", "check_status"),
    ("status of my flight", "check_status"),
    
    # Cancel intents
    ("cancel my booking", "cancel"),
    ("I want to cancel", "cancel"),
    ("cancel my reservation", "cancel"),
    ("remove my booking", "cancel"),
    ("delete my order", "cancel"),
    
    # Help intents
    ("I need help", "help"),
    ("can you help me", "help"),
    ("what can you do", "help"),
    ("how does this work", "help"),
    ("support", "help"),
    
    # Goodbye intents
    ("bye", "goodbye"),
    ("goodbye", "goodbye"),
    ("see you later", "goodbye"),
    ("talk to you later", "goodbye"),
    ("have a nice day", "goodbye"),
]


class IntentClassifier:
    """Simple intent classifier using TF-IDF and Naive Bayes"""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            ngram_range=(1, 2),  # Use unigrams and bigrams
            max_features=1000
        )
        self.classifier = MultinomialNB()
        self.is_trained = False
        
    def train(self, texts, labels):
        """Train the intent classifier"""
        print("Training intent classifier...")
        
        # Convert texts to TF-IDF features
        X = self.vectorizer.fit_transform(texts)
        
        # Train the classifier
        self.classifier.fit(X, labels)
        self.is_trained = True
        
        print(f"Training complete! Model trained on {len(texts)} examples.")
        
    def predict(self, text):
        """Predict the intent of a given text"""
        if not self.is_trained:
            raise Exception("Model must be trained before prediction")
            
        # Transform text to features
        X = self.vectorizer.transform([text])
        
        # Predict intent
        intent = self.classifier.predict(X)[0]
        
        # Get probability scores
        probabilities = self.classifier.predict_proba(X)[0]
        confidence = max(probabilities)
        
        return intent, confidence
    
    def evaluate(self, texts, labels):
        """Evaluate the classifier on test data"""
        X = self.vectorizer.transform(texts)
        predictions = self.classifier.predict(X)
        
        print("\n=== Evaluation Results ===")
        print(f"Accuracy: {accuracy_score(labels, predictions):.2%}")
        print("\nDetailed Report:")
        print(classification_report(labels, predictions))
        
    def save(self, filepath):
        """Save the trained model"""
        with open(filepath, 'wb') as f:
            pickle.dump({'vectorizer': self.vectorizer, 
                        'classifier': self.classifier}, f)
        print(f"Model saved to {filepath}")
        
    def load(self, filepath):
        """Load a trained model"""
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
            self.vectorizer = data['vectorizer']
            self.classifier = data['classifier']
            self.is_trained = True
        print(f"Model loaded from {filepath}")


def main():
    """Main function to demonstrate intent classification"""
    
    # Prepare data
    texts = [item[0] for item in TRAINING_DATA]
    labels = [item[1] for item in TRAINING_DATA]
    
    # Split into train and test sets
    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42
    )
    
    # Create and train classifier
    classifier = IntentClassifier()
    classifier.train(X_train, y_train)
    
    # Evaluate on test set
    classifier.evaluate(X_test, y_test)
    
    # Test with new examples
    print("\n=== Testing with New Examples ===")
    test_messages = [
        "hi, how are you?",
        "I'd like to book a flight to New York",
        "can you check my booking status?",
        "I want to cancel my reservation",
        "what services do you offer?",
    ]
    
    for message in test_messages:
        intent, confidence = classifier.predict(message)
        print(f"\nMessage: '{message}'")
        print(f"Predicted Intent: {intent}")
        print(f"Confidence: {confidence:.2%}")
    
    # Save the model
    classifier.save("intent_classifier.pkl")
    
    print("\n=== Interactive Mode ===")
    print("Type a message to classify its intent (or 'quit' to exit)")
    
    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break
            
        if user_input:
            intent, confidence = classifier.predict(user_input)
            print(f"Intent: {intent} (confidence: {confidence:.2%})")


if __name__ == "__main__":
    main()
