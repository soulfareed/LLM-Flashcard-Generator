import re
import string
from typing import List, Dict, Any
import nltk
from collections import Counter

class TextUtils:
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text"""
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove special characters but keep punctuation
        text = ''.join(char for char in text if char.isprintable())
        
        return text.strip()
    
    @staticmethod
    def extract_sentences(text: str, min_length: int = 10) -> List[str]:
        """Extract sentences from text with minimum length filter"""
        try:
            sentences = nltk.sent_tokenize(text)
        except:
            # Fallback sentence splitting
            sentences = re.split(r'[.!?]+', text)
        
        # Filter sentences by length and content
        valid_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if (len(sentence) >= min_length and 
                not sentence.isdigit() and 
                len(sentence.split()) >= 3):
                valid_sentences.append(sentence)
        
        return valid_sentences
    
    @staticmethod
    def calculate_readability_score(text: str) -> float:
        """Calculate a simple readability score (0-100, higher is easier)"""
        if not text:
            return 0
        
        sentences = TextUtils.extract_sentences(text)
        words = text.split()
        
        if not sentences or not words:
            return 0
        
        # Simple metrics
        avg_sentence_length = len(words) / len(sentences)
        avg_word_length = sum(len(word.strip(string.punctuation)) for word in words) / len(words)
        
        # Simple readability calculation (inverse of complexity)
        complexity = (avg_sentence_length * 0.5) + (avg_word_length * 2)
        readability = max(0, 100 - complexity * 2)
        
        return min(100, readability)
    
    @staticmethod
    def extract_keywords(text: str, num_keywords: int = 10) -> List[str]:
        """Extract keywords from text"""
        # Simple keyword extraction
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Remove common stop words
        stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before',
            'after', 'above', 'below', 'between', 'among', 'this', 'that', 'these',
            'those', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'may', 'might', 'must', 'can', 'shall', 'not', 'no', 'yes'
        }
        
        filtered_words = [word for word in words if word not in stop_words and len(word) > 3]
        
        # Count frequency
        word_counts = Counter(filtered_words)
        
        # Return top keywords
        return [word for word, count in word_counts.most_common(num_keywords)]

class ValidationUtils:
    @staticmethod
    def validate_flashcard(flashcard: Dict[str, Any]) -> List[str]:
        """Validate a flashcard and return list of errors"""
        errors = []
        
        # Check required fields
        if not flashcard.get('question', '').strip():
            errors.append("Question is required and cannot be empty")
        
        if not flashcard.get('answer', '').strip():
            errors.append("Answer is required and cannot be empty")
        
        # Check question format
        question = flashcard.get('question', '')
        if question and not question.strip().endswith('?'):
            if not any(question.startswith(word) for word in ['What', 'How', 'Why', 'When', 'Where', 'Who', 'Which', 'Define', 'Explain', 'Describe']):
                errors.append("Question should be in question format or start with an interrogative word")
        
        # Check minimum lengths
        if len(flashcard.get('question', '')) < 10:
            errors.append("Question is too short (minimum 10 characters)")
        
        if len(flashcard.get('answer', '')) < 5:
            errors.append("Answer is too short (minimum 5 characters)")
        
        # Check maximum lengths
        if len(flashcard.get('question', '')) > 200:
            errors.append("Question is too long (maximum 200 characters)")
        
        if len(flashcard.get('answer', '')) > 1000:
            errors.append("Answer is too long (maximum 1000 characters)")
        
        return errors
    
    @staticmethod
    def validate_flashcard_set(flashcards: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate a set of flashcards"""
        validation_result = {
            'valid': True,
            'total_cards': len(flashcards),
            'valid_cards': 0,
            'errors': [],
            'warnings': []
        }
        
        if not flashcards:
            validation_result['valid'] = False
            validation_result['errors'].append("No flashcards provided")
            return validation_result
        
        # Check each flashcard
        for i, card in enumerate(flashcards):
            card_errors = ValidationUtils.validate_flashcard(card)
            if card_errors:
                validation_result['errors'].extend([f"Card {i+1}: {error}" for error in card_errors])
            else:
                validation_result['valid_cards'] += 1
        
        # Check for duplicates
        questions = [card.get('question', '') for card in flashcards]
        duplicates = [q for q in set(questions) if questions.count(q) > 1]
        if duplicates:
            validation_result['warnings'].append(f"Found {len(duplicates)} duplicate questions")
        
        # Overall validation
        if validation_result['valid_cards'] == 0:
            validation_result['valid'] = False
        
        return validation_result

class FormatUtils:
    @staticmethod
    def format_question(text: str) -> str:
        """Format text as a proper question"""
        text = text.strip()
        if not text:
            return text
        
        # Capitalize first letter
        text = text[0].upper() + text[1:] if len(text) > 1 else text.upper()
        
        # Add question mark if not present and it looks like a question
        if not text.endswith('?') and any(text.startswith(word) for word in [
            'What', 'How', 'Why', 'When', 'Where', 'Who', 'Which', 'Is', 'Are', 'Do', 'Does', 'Can', 'Could', 'Would', 'Should'
        ]):
            text += '?'
        
        return text
    
    @staticmethod
    def format_answer(text: str) -> str:
        """Format text as a proper answer"""
        text = text.strip()
        if not text:
            return text
        
        # Capitalize first letter
        text = text[0].upper() + text[1:] if len(text) > 1 else text.upper()
        
        # Add period if not present and doesn't end with punctuation
        if not text[-1] in '.!?':
            text += '.'
        
        return text