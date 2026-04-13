"""
Sentiment Analysis Example
Chapter 3: NLP Fundamentals

This script demonstrates how to analyze the sentiment and emotion in user messages.
Understanding sentiment helps chatbots respond with appropriate tone and empathy.
"""

from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch


class SentimentAnalyzer:
    """Analyze sentiment and emotion in text using pre-trained transformers"""
    
    def __init__(self, model_type="basic"):
        """
        Initialize sentiment analyzer
        
        Args:
            model_type: "basic" for simple sentiment or "emotion" for detailed emotion detection
        """
        self.model_type = model_type
        
        if model_type == "basic":
            # Use a lightweight model for basic positive/negative/neutral sentiment
            print("Loading basic sentiment model...")
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english"
            )
        elif model_type == "emotion":
            # Use emotion detection model for more nuanced analysis
            print("Loading emotion detection model...")
            self.sentiment_pipeline = pipeline(
                "text-classification",
                model="j-hartmann/emotion-english-distilroberta-base",
                return_all_scores=True
            )
        
        print("Model loaded successfully!")
    
    def analyze_sentiment(self, text):
        """Analyze the sentiment of given text"""
        result = self.sentiment_pipeline(text)
        
        if self.model_type == "basic":
            return {
                'sentiment': result[0]['label'],
                'confidence': result[0]['score']
            }
        else:
            # For emotion model, return all emotions with scores
            emotions = {item['label']: item['score'] for item in result[0]}
            primary_emotion = max(emotions.items(), key=lambda x: x[1])
            
            return {
                'primary_emotion': primary_emotion[0],
                'confidence': primary_emotion[1],
                'all_emotions': emotions
            }
    
    def analyze_batch(self, texts):
        """Analyze sentiment for multiple texts"""
        results = []
        for text in texts:
            results.append(self.analyze_sentiment(text))
        return results
    
    def get_response_tone(self, sentiment_result):
        """Suggest appropriate response tone based on sentiment"""
        if self.model_type == "basic":
            sentiment = sentiment_result['sentiment']
            confidence = sentiment_result['confidence']
            
            if sentiment == "POSITIVE" and confidence > 0.8:
                return "enthusiastic"
            elif sentiment == "POSITIVE":
                return "friendly"
            elif sentiment == "NEGATIVE" and confidence > 0.8:
                return "empathetic"
            elif sentiment == "NEGATIVE":
                return "supportive"
            else:
                return "neutral"
        else:
            emotion = sentiment_result['primary_emotion']
            
            tone_map = {
                'joy': 'enthusiastic',
                'sadness': 'empathetic',
                'anger': 'calming',
                'fear': 'reassuring',
                'surprise': 'informative',
                'disgust': 'understanding',
                'neutral': 'professional'
            }
            
            return tone_map.get(emotion, 'neutral')


class SimpleSentimentAnalyzer:
    """A lightweight rule-based sentiment analyzer (no ML required)"""
    
    def __init__(self):
        # Simple word lists for demonstration
        self.positive_words = {
            'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic',
            'love', 'like', 'happy', 'pleased', 'satisfied', 'perfect',
            'awesome', 'brilliant', 'superb', 'outstanding'
        }
        
        self.negative_words = {
            'bad', 'terrible', 'awful', 'horrible', 'poor', 'worst',
            'hate', 'dislike', 'angry', 'frustrated', 'disappointed', 'sad',
            'annoyed', 'upset', 'unhappy', 'dissatisfied'
        }
    
    def analyze(self, text):
        """Simple rule-based sentiment analysis"""
        text_lower = text.lower()
        words = text_lower.split()
        
        positive_count = sum(1 for word in words if word in self.positive_words)
        negative_count = sum(1 for word in words if word in self.negative_words)
        
        if positive_count > negative_count:
            sentiment = "POSITIVE"
            score = min(0.5 + (positive_count * 0.1), 1.0)
        elif negative_count > positive_count:
            sentiment = "NEGATIVE"
            score = min(0.5 + (negative_count * 0.1), 1.0)
        else:
            sentiment = "NEUTRAL"
            score = 0.5
        
        return {
            'sentiment': sentiment,
            'confidence': score,
            'positive_words': positive_count,
            'negative_words': negative_count
        }


def demonstrate_sentiment_analysis():
    """Demonstrate sentiment analysis with various examples"""
    
    print("=== Sentiment Analysis Demo ===\n")
    print("Choose analyzer type:")
    print("1. Simple rule-based (fast, no download required)")
    print("2. ML-based basic sentiment (requires model download)")
    print("3. ML-based emotion detection (requires model download)")
    
    choice = input("\nEnter choice (1-3) or press Enter for option 1: ").strip()
    
    if choice == "2":
        analyzer = SentimentAnalyzer(model_type="basic")
    elif choice == "3":
        analyzer = SentimentAnalyzer(model_type="emotion")
    else:
        analyzer = SimpleSentimentAnalyzer()
        print("\nUsing simple rule-based analyzer\n")
    
    # Test messages
    test_messages = [
        "I love this product! It's absolutely amazing!",
        "This is the worst experience I've ever had.",
        "The service was okay, nothing special.",
        "I'm so frustrated with this issue.",
        "Thank you so much for your help!",
        "I'm not sure how I feel about this.",
    ]
    
    print("\n=== Analyzing Sample Messages ===\n")
    
    for message in test_messages:
        print(f"Message: '{message}'")
        print("-" * 60)
        
        if isinstance(analyzer, SimpleSentimentAnalyzer):
            result = analyzer.analyze(message)
            print(f"Sentiment: {result['sentiment']}")
            print(f"Confidence: {result['confidence']:.2%}")
            print(f"Positive words: {result['positive_words']}, Negative words: {result['negative_words']}")
        else:
            result = analyzer.analyze_sentiment(message)
            
            if analyzer.model_type == "basic":
                print(f"Sentiment: {result['sentiment']}")
                print(f"Confidence: {result['confidence']:.2%}")
                tone = analyzer.get_response_tone(result)
                print(f"Suggested response tone: {tone}")
            else:
                print(f"Primary Emotion: {result['primary_emotion']}")
                print(f"Confidence: {result['confidence']:.2%}")
                print("All emotions:")
                for emotion, score in sorted(result['all_emotions'].items(), key=lambda x: x[1], reverse=True):
                    print(f"  {emotion}: {score:.2%}")
                tone = analyzer.get_response_tone(result)
                print(f"Suggested response tone: {tone}")
        
        print()
    
    # Interactive mode
    print("\n=== Interactive Mode ===")
    print("Enter a message to analyze its sentiment (or 'quit' to exit)")
    
    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break
        
        if user_input:
            if isinstance(analyzer, SimpleSentimentAnalyzer):
                result = analyzer.analyze(user_input)
                print(f"\nSentiment: {result['sentiment']} (confidence: {result['confidence']:.2%})")
            else:
                result = analyzer.analyze_sentiment(user_input)
                if analyzer.model_type == "basic":
                    print(f"\nSentiment: {result['sentiment']} (confidence: {result['confidence']:.2%})")
                else:
                    print(f"\nPrimary Emotion: {result['primary_emotion']} (confidence: {result['confidence']:.2%})")


if __name__ == "__main__":
    demonstrate_sentiment_analysis()
