"""
Entity Extraction Example
Chapter 3: NLP Fundamentals

This script demonstrates how to extract entities (names, dates, locations, etc.)
from user messages using spaCy's Named Entity Recognition (NER).
"""

import spacy
from datetime import datetime
import re


class EntityExtractor:
    """Extract entities from text using spaCy and custom patterns"""
    
    def __init__(self, model_name="en_core_web_sm"):
        """Initialize the entity extractor with a spaCy model"""
        try:
            self.nlp = spacy.load(model_name)
            print(f"Loaded spaCy model: {model_name}")
        except OSError:
            print(f"Model {model_name} not found. Downloading...")
            import os
            os.system(f"python -m spacy download {model_name}")
            self.nlp = spacy.load(model_name)
    
    def extract_entities(self, text):
        """Extract named entities from text"""
        doc = self.nlp(text)
        
        entities = []
        for ent in doc.ents:
            entities.append({
                'text': ent.text,
                'label': ent.label_,
                'start': ent.start_char,
                'end': ent.end_char
            })
        
        return entities
    
    def extract_dates(self, text):
        """Extract date mentions from text"""
        doc = self.nlp(text)
        dates = []
        
        for ent in doc.ents:
            if ent.label_ == "DATE":
                dates.append({
                    'text': ent.text,
                    'type': 'date',
                    'normalized': self._normalize_date(ent.text)
                })
        
        return dates
    
    def extract_locations(self, text):
        """Extract location mentions from text"""
        doc = self.nlp(text)
        locations = []
        
        for ent in doc.ents:
            if ent.label_ in ["GPE", "LOC", "FAC"]:  # Geo-political entity, location, facility
                locations.append({
                    'text': ent.text,
                    'type': ent.label_
                })
        
        return locations
    
    def extract_persons(self, text):
        """Extract person names from text"""
        doc = self.nlp(text)
        persons = []
        
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                persons.append(ent.text)
        
        return persons
    
    def extract_custom_entities(self, text, patterns):
        """Extract entities based on custom regex patterns"""
        custom_entities = []
        
        for pattern_name, pattern in patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                custom_entities.append({
                    'text': match.group(),
                    'label': pattern_name,
                    'start': match.start(),
                    'end': match.end()
                })
        
        return custom_entities
    
    def _normalize_date(self, date_text):
        """Attempt to normalize date text to a standard format"""
        # This is a simplified version - in production, use dateparser library
        date_text = date_text.lower()
        
        if date_text == "today":
            return datetime.now().strftime("%Y-%m-%d")
        elif date_text == "tomorrow":
            from datetime import timedelta
            return (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        elif date_text == "yesterday":
            from datetime import timedelta
            return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            return date_text  # Return as-is if can't normalize
    
    def extract_all(self, text):
        """Extract all types of entities and return structured data"""
        entities = self.extract_entities(text)
        
        # Organize by type
        organized = {
            'persons': [],
            'locations': [],
            'dates': [],
            'organizations': [],
            'other': []
        }
        
        for ent in entities:
            if ent['label'] == 'PERSON':
                organized['persons'].append(ent['text'])
            elif ent['label'] in ['GPE', 'LOC', 'FAC']:
                organized['locations'].append(ent['text'])
            elif ent['label'] == 'DATE':
                organized['dates'].append(ent['text'])
            elif ent['label'] == 'ORG':
                organized['organizations'].append(ent['text'])
            else:
                organized['other'].append({
                    'text': ent['text'],
                    'type': ent['label']
                })
        
        return organized


def demonstrate_entity_extraction():
    """Demonstrate entity extraction with various examples"""
    
    extractor = EntityExtractor()
    
    # Example messages
    test_messages = [
        "I want to book a flight from New York to London on December 25th",
        "My name is John Smith and I live in San Francisco",
        "Can you schedule a meeting with Sarah Johnson tomorrow at 3 PM?",
        "I need to transfer $500 to Apple Inc. by next Friday",
        "Book a hotel in Paris for March 15th to March 20th",
        "Contact Dr. Emily Brown at Stanford University",
    ]
    
    print("=== Entity Extraction Examples ===\n")
    
    for message in test_messages:
        print(f"Message: '{message}'")
        print("-" * 60)
        
        # Extract all entities
        all_entities = extractor.extract_all(message)
        
        if all_entities['persons']:
            print(f"Persons: {', '.join(all_entities['persons'])}")
        if all_entities['locations']:
            print(f"Locations: {', '.join(all_entities['locations'])}")
        if all_entities['dates']:
            print(f"Dates: {', '.join(all_entities['dates'])}")
        if all_entities['organizations']:
            print(f"Organizations: {', '.join(all_entities['organizations'])}")
        if all_entities['other']:
            print(f"Other entities: {all_entities['other']}")
        
        print()
    
    # Demonstrate custom pattern extraction
    print("\n=== Custom Pattern Extraction ===\n")
    
    custom_patterns = {
        'EMAIL': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'PHONE': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        'BOOKING_ID': r'\b[A-Z]{2}\d{6}\b'
    }
    
    custom_message = "Please send confirmation to john@example.com or call 555-123-4567. Booking ID: AB123456"
    print(f"Message: '{custom_message}'")
    print("-" * 60)
    
    custom_entities = extractor.extract_custom_entities(custom_message, custom_patterns)
    for entity in custom_entities:
        print(f"{entity['label']}: {entity['text']}")
    
    # Interactive mode
    print("\n=== Interactive Mode ===")
    print("Enter a message to extract entities (or 'quit' to exit)")
    
    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break
        
        if user_input:
            entities = extractor.extract_all(user_input)
            print("\nExtracted Entities:")
            for entity_type, values in entities.items():
                if values:
                    print(f"  {entity_type.capitalize()}: {values}")


if __name__ == "__main__":
    demonstrate_entity_extraction()
