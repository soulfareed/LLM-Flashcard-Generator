import json
import csv
import io
from typing import List, Dict, Any
import pandas as pd

class FlashcardExporter:
    def __init__(self):
        pass
    
    def to_json(self, flashcards: List[Dict[str, Any]]) -> str:
        """Export flashcards to JSON format"""
        export_data = {
            "metadata": {
                "total_cards": len(flashcards),
                "export_format": "json",
                "version": "1.0"
            },
            "flashcards": flashcards
        }
        return json.dumps(export_data, indent=2, ensure_ascii=False)
    
    def to_csv(self, flashcards: List[Dict[str, Any]]) -> str:
        """Export flashcards to CSV format"""
        if not flashcards:
            return ""
        
        # Convert to DataFrame
        df = pd.DataFrame(flashcards)
        
        # Create CSV string
        output = io.StringIO()
        df.to_csv(output, index=False, encoding='utf-8')
        return output.getvalue()
    
    def to_anki(self, flashcards: List[Dict[str, Any]]) -> str:
        """Export flashcards to Anki import format"""
        anki_cards = []
        
        for card in flashcards:
            # Anki format: Front\tBack\tTags
            question = card['question'].replace('\t', ' ').replace('\n', '<br>')
            answer = card['answer'].replace('\t', ' ').replace('\n', '<br>')
            
            # Create tags from metadata
            tags = []
            if 'subject' in card:
                tags.append(card['subject'].replace(' ', '_'))
            if 'difficulty' in card:
                tags.append(f"difficulty_{card['difficulty'].lower()}")
            if 'topic' in card:
                tags.append(card['topic'].replace(' ', '_'))
            
            tag_string = ' '.join(tags)
            
            anki_line = f"{question}\t{answer}\t{tag_string}"
            anki_cards.append(anki_line)
        
        # Add header with instructions
        header = """# Anki Import File
# Import Instructions:
# 1. Open Anki
# 2. Go to File > Import
# 3. Select this file
# 4. Make sure 'Fields separated by: Tab' is selected
# 5. Map fields: Field 1 -> Front, Field 2 -> Back, Field 3 -> Tags
# 6. Click Import

"""
        
        return header + '\n'.join(anki_cards)
    
    def to_quizlet(self, flashcards: List[Dict[str, Any]]) -> str:
        """Export flashcards to Quizlet import format"""
        quizlet_cards = []
        
        for card in flashcards:
            # Quizlet format: Term\tDefinition
            question = card['question'].replace('\t', ' ').replace('\n', ' ')
            answer = card['answer'].replace('\t', ' ').replace('\n', ' ')
            
            quizlet_line = f"{question}\t{answer}"
            quizlet_cards.append(quizlet_line)
        
        # Add header with instructions
        header = """# Quizlet Import File
# Import Instructions:
# 1. Go to Quizlet.com and create a new study set
# 2. Click on "Import from Word, Excel, Google Docs, etc."
# 3. Copy and paste the content below (excluding this header)
# 4. Make sure "Between term and definition" is set to "Tab"
# 5. Make sure "Between cards" is set to "New line"
# 6. Click "Import"

"""
        
        return header + '\n'.join(quizlet_cards)
    
    def to_custom_format(self, flashcards: List[Dict[str, Any]], format_name: str) -> str:
        """Export flashcards to a custom format"""
        if format_name.lower() == "markdown":
            return self._to_markdown(flashcards)
        elif format_name.lower() == "txt":
            return self._to_plain_text(flashcards)
        else:
            return self.to_json(flashcards)
    
    def _to_markdown(self, flashcards: List[Dict[str, Any]]) -> str:
        """Export flashcards to Markdown format"""
        markdown_content = "# Flashcards\n\n"
        
        # Group by topic if available
        topics = {}
        for card in flashcards:
            topic = card.get('topic', 'General')
            if topic not in topics:
                topics[topic] = []
            topics[topic].append(card)
        
        for topic, cards in topics.items():
            markdown_content += f"## {topic}\n\n"
            
            for i, card in enumerate(cards, 1):
                markdown_content += f"### Card {i}\n\n"
                markdown_content += f"**Question:** {card['question']}\n\n"
                markdown_content += f"**Answer:** {card['answer']}\n\n"
                
                if 'difficulty' in card:
                    markdown_content += f"*Difficulty: {card['difficulty']}*\n\n"
                
                markdown_content += "---\n\n"
        
        return markdown_content
    
    def _to_plain_text(self, flashcards: List[Dict[str, Any]]) -> str:
        """Export flashcards to plain text format"""
        text_content = "FLASHCARDS\n" + "="*50 + "\n\n"
        
        for i, card in enumerate(flashcards, 1):
            text_content += f"CARD {i}\n"
            text_content += "-" * 20 + "\n"
            text_content += f"Q: {card['question']}\n\n"
            text_content += f"A: {card['answer']}\n"
            
            if 'difficulty' in card:
                text_content += f"Difficulty: {card['difficulty']}\n"
            if 'topic' in card:
                text_content += f"Topic: {card['topic']}\n"
            
            text_content += "\n" + "="*50 + "\n\n"
        
        return text_content
    
    def get_export_stats(self, flashcards: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get statistics about the flashcards for export"""
        if not flashcards:
            return {}
        
        stats = {
            "total_cards": len(flashcards),
            "subjects": list(set(card.get('subject', 'Unknown') for card in flashcards)),
            "difficulties": {},
            "topics": list(set(card.get('topic', 'General') for card in flashcards)),
            "languages": list(set(card.get('language', 'English') for card in flashcards))
        }
        
        # Count difficulties
        for card in flashcards:
            diff = card.get('difficulty', 'Unknown')
            stats["difficulties"][diff] = stats["difficulties"].get(diff, 0) + 1
        
        return stats