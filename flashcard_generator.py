import re
import random
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import torch
from typing import List, Dict, Any
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
import warnings

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

warnings.filterwarnings("ignore", category=UserWarning)

class FlashcardGenerator:
    def __init__(self):
        self.model_name = "google/flan-t5-base"  # Smaller model for better performance
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.generator = None
        self.tokenizer = None
        self._load_model()
    
    def _load_model(self):
        """Load the LLM model and tokenizer"""
        try:
            print("Loading model... This may take a few minutes on first run.")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            model = AutoModelForSeq2SeqLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto" if self.device == "cuda" else None
            )
            
            self.generator = pipeline(
                "text2text-generation",
                model=model,
                tokenizer=self.tokenizer,
                device=0 if self.device == "cuda" else -1,
                max_length=512,
                do_sample=True,
                temperature=0.7
            )
            print("Model loaded successfully!")
            
        except Exception as e:
            print(f"Error loading model: {e}")
            # Fallback to a rule-based approach if model loading fails
            self.generator = None
    
    def _chunk_text(self, text: str, max_chunk_size: int = 1000) -> List[str]:
        """Split text into manageable chunks"""
        sentences = sent_tokenize(text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk + sentence) < max_chunk_size:
                current_chunk += sentence + " "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + " "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _extract_key_concepts(self, text: str) -> List[str]:
        """Extract key concepts from text using simple NLP"""
        try:
            stop_words = set(stopwords.words('english'))
        except:
            stop_words = set()
        
        # Simple keyword extraction
        words = word_tokenize(text.lower())
        words = [word for word in words if word.isalpha() and word not in stop_words and len(word) > 3]
        
        # Get word frequency
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency and return top concepts
        key_concepts = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:20]
        return [concept[0] for concept in key_concepts]
    
    def _detect_topics(self, text: str) -> List[str]:
        """Detect topics from text structure"""
        topics = []
        
        # Look for headings and section markers
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if len(line) > 0:
                # Check for potential headings (short lines, capitalized, etc.)
                if (len(line) < 100 and 
                    (line.isupper() or line.istitle()) and 
                    not line.endswith('.') and
                    len(line.split()) <= 8):
                    topics.append(line)
        
        # If no clear topics found, use key concepts
        if not topics:
            key_concepts = self._extract_key_concepts(text)
            topics = key_concepts[:5]  # Use top 5 concepts as topics
        
        return topics[:10]  # Limit to 10 topics max
    
    def _generate_question_answer_with_llm(self, text: str, subject: str, difficulty: str) -> Dict[str, str]:
        """Generate Q&A using the LLM"""
        if not self.generator:
            return self._generate_question_answer_fallback(text, subject, difficulty)
        
        # Create prompts based on subject and difficulty
        subject_context = {
            "Biology": "biological concepts, processes, and terminology",
            "Chemistry": "chemical reactions, elements, compounds, and formulas",
            "Physics": "physical laws, equations, and phenomena",
            "Mathematics": "mathematical concepts, formulas, and problem-solving",
            "History": "historical events, dates, people, and causes",
            "Computer Science": "programming concepts, algorithms, and data structures",
            "Literature": "literary devices, themes, and analysis",
            "Psychology": "psychological theories, concepts, and research",
            "Economics": "economic principles, theories, and market concepts",
            "General": "key concepts and important information"
        }
        
        difficulty_instruction = {
            "Easy": "Create a simple, straightforward question that tests basic understanding.",
            "Medium": "Create a question that requires some analysis and understanding.",
            "Hard": "Create a challenging question that requires deep understanding and critical thinking.",
            "Mixed": "Create a question with appropriate difficulty for the content."
        }
        
        context = subject_context.get(subject, subject_context["General"])
        diff_inst = difficulty_instruction.get(difficulty, difficulty_instruction["Mixed"])
        
        prompt = f"""Based on the following educational content about {context}, {diff_inst}

Content: {text[:800]}

Generate one clear question and its complete answer. Format your response as:
Question: [Your question here]
Answer: [Your detailed answer here]"""
        
        try:
            result = self.generator(prompt, max_length=300, num_return_sequences=1)
            generated_text = result[0]['generated_text']
            
            # Parse the generated text
            return self._parse_qa_response(generated_text, difficulty)
            
        except Exception as e:
            print(f"LLM generation failed: {e}")
            return self._generate_question_answer_fallback(text, subject, difficulty)
    
    def _parse_qa_response(self, response: str, difficulty: str) -> Dict[str, str]:
        """Parse the LLM response to extract question and answer"""
        lines = response.strip().split('\n')
        question = ""
        answer = ""
        
        for line in lines:
            line = line.strip()
            if line.lower().startswith('question:'):
                question = line[9:].strip()
            elif line.lower().startswith('answer:'):
                answer = line[7:].strip()
            elif question and not answer and line:
                # Continue building the answer
                answer = line
        
        # Fallback parsing if standard format not found
        if not question or not answer:
            parts = response.split('?', 1)
            if len(parts) == 2:
                question = parts[0].strip() + '?'
                answer = parts[1].strip()
            else:
                # Last resort: create from content
                question = "What is the main concept discussed in this content?"
                answer = response[:200] + "..."
        
        return {
            'question': question,
            'answer': answer,
            'difficulty': difficulty
        }
    
    def _generate_question_answer_fallback(self, text: str, subject: str, difficulty: str) -> Dict[str, str]:
        """Fallback method for generating Q&A without LLM"""
        sentences = sent_tokenize(text)
        if not sentences:
            return None
        
        # Simple rule-based question generation
        key_sentence = random.choice(sentences[:min(10, len(sentences))])
        
        # Generate different types of questions based on patterns
        question_templates = [
            f"What is mentioned about {self._extract_main_subject(key_sentence)}?",
            f"Explain the concept related to {self._extract_main_subject(key_sentence)}.",
            f"What are the key points about {self._extract_main_subject(key_sentence)}?",
            f"Describe {self._extract_main_subject(key_sentence)}.",
            "What is the main idea presented in this content?",
            "What are the important details mentioned?",
            "How would you summarize this information?"
        ]
        
        question = random.choice(question_templates)
        answer = key_sentence
        
        return {
            'question': question,
            'answer': answer,
            'difficulty': difficulty
        }
    
    def _extract_main_subject(self, sentence: str) -> str:
        """Extract main subject from a sentence"""
        words = word_tokenize(sentence)
        # Simple heuristic: look for nouns
        nouns = [word for word in words if word.isalpha() and len(word) > 3]
        return nouns[0] if nouns else "the topic"
    
    def generate_flashcards(self, content: str, subject: str, difficulty: str, 
                          num_cards: int, language: str = "English") -> List[Dict[str, Any]]:
        """Generate flashcards from content"""
        if not content.strip():
            return []
        
        # Chunk the content
        chunks = self._chunk_text(content)
        
        # Detect topics
        topics = self._detect_topics(content)
        
        flashcards = []
        
        # Generate cards from chunks
        for i, chunk in enumerate(chunks):
            if len(flashcards) >= num_cards:
                break
            
            # Assign difficulty
            if difficulty == "Mixed":
                current_difficulty = random.choice(["Easy", "Medium", "Hard"])
            else:
                current_difficulty = difficulty
            
            # Assign topic
            current_topic = topics[i % len(topics)] if topics else "General"
            
            # Generate Q&A
            qa_pair = self._generate_question_answer_with_llm(chunk, subject, current_difficulty)
            
            if qa_pair:
                flashcard = {
                    'question': qa_pair['question'],
                    'answer': qa_pair['answer'],
                    'difficulty': current_difficulty,
                    'topic': current_topic,
                    'subject': subject,
                    'language': language
                }
                flashcards.append(flashcard)
        
        # If we don't have enough cards, generate more from key concepts
        while len(flashcards) < num_cards:
            key_concepts = self._extract_key_concepts(content)
            if not key_concepts:
                break
            
            concept = random.choice(key_concepts)
            current_difficulty = random.choice(["Easy", "Medium", "Hard"]) if difficulty == "Mixed" else difficulty
            current_topic = topics[len(flashcards) % len(topics)] if topics else "General"
            
            # Create concept-based question
            concept_questions = [
                f"What is {concept}?",
                f"Define {concept}.",
                f"Explain the significance of {concept}.",
                f"What are the key characteristics of {concept}?"
            ]
            
            question = random.choice(concept_questions)
            
            # Find relevant content for answer
            relevant_sentences = [s for s in sent_tokenize(content) if concept in s.lower()]
            answer = relevant_sentences[0] if relevant_sentences else f"A key concept related to {subject}."
            
            flashcard = {
                'question': question,
                'answer': answer,
                'difficulty': current_difficulty,
                'topic': current_topic,
                'subject': subject,
                'language': language
            }
            flashcards.append(flashcard)
        
        return flashcards[:num_cards]