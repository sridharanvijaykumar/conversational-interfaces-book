# Chapter 3: NLP Fundamentals

This directory contains practical examples demonstrating core NLP concepts used in conversational AI systems.

## Examples Included

### 1. Intent Classification (`intent_classification.py`)
Demonstrates how to classify user intents using machine learning models. This is fundamental for understanding what users want from a chatbot.

**Key Concepts:**
- Text preprocessing
- Feature extraction (TF-IDF)
- Classification using scikit-learn
- Training and evaluation

**Usage:**
```bash
python intent_classification.py
```

### 2. Entity Extraction (`entity_extraction.py`)
Shows how to extract named entities (dates, locations, names, etc.) from user messages using both rule-based and ML approaches.

**Key Concepts:**
- Named Entity Recognition (NER)
- Using spaCy for entity extraction
- Custom entity patterns
- Entity linking

**Usage:**
```bash
python entity_extraction.py
```

### 3. Sentiment Analysis (`sentiment_analysis.py`)
Analyzes the emotional tone of user messages to enable emotionally intelligent responses.

**Key Concepts:**
- Sentiment classification
- Using pre-trained transformers
- Emotion detection
- Confidence scoring

**Usage:**
```bash
python sentiment_analysis.py
```

## Setup

Install required dependencies:
```bash
pip install nltk spacy scikit-learn transformers torch

# Download spaCy model
python -m spacy download en_core_web_sm

# Download NLTK data
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
```

## Learning Outcomes

After working through these examples, you will understand:
- How chatbots interpret user input
- The role of NLP in conversational AI
- How to preprocess and analyze text data
- How to build basic NLP pipelines

## Related Book Sections

- Section 3.1: Natural Language Understanding (NLU)
- Section 3.2: Intent Recognition and Entity Extraction
- Section 3.3: Context and Semantic Understanding
