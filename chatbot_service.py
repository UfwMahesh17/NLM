import os
import json
import logging
from openai import OpenAI
from nltk_processor import NLTKProcessor

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class ChatbotService:
    def __init__(self):
        """Initialize the chatbot service with NLTK and OpenAI capabilities."""
        try:
            # Initialize NLTK processor
            self.nltk_processor = NLTKProcessor()
            
            # Initialize OpenAI client
            self.openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            
            logger.info("ChatbotService initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing ChatbotService: {e}")
            raise
    
    def get_nltk_response(self, text):
        """Get response using NLTK-based FAQ matching."""
        try:
            # Find best matching FAQ
            best_match, confidence = self.nltk_processor.find_best_match(text)
            
            if best_match:
                answer = best_match['answer']
                source = 'nltk'
                logger.info(f"NLTK found match with confidence: {confidence:.4f}")
                return answer, source, confidence
            else:
                # No good match found
                return None, 'nltk', confidence
        except Exception as e:
            logger.error(f"Error getting NLTK response: {e}")
            return "I encountered an error processing your question.", 'error', 0.0
    
    def get_rag_response(self, text):
        """Get response using RAG approach with OpenAI."""
        try:
            # Find top relevant FAQs using NLTK
            top_matches = self.nltk_processor.find_top_matches(text, top_k=3)
            
            # Format the FAQs for input to GPT
            if top_matches:
                formatted_faqs = "\n\n".join([
                    f"FAQ {i+1}:\nQuestion: {faq['question']}\nAnswer: {faq['answer']}\nCategory: {faq['category']}"
                    for i, (faq, _) in enumerate(top_matches)
                ])
            else:
                formatted_faqs = "No specific FAQ matches found for this query."
            
            # Generate response using GPT
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
                messages=[
                    {"role": "system", "content": "You are AURORA, an advanced customer support agent for an e-commerce website with a "
                                                 "Matrix-themed interface. Your answers should be helpful, accurate, "
                                                 "and styled with subtle references to The Matrix movie. Occasionally use phrases like "
                                                 "'Welcome to the Matrix', 'The truth is out there', or 'Follow the white rabbit'. "
                                                 "Use the provided FAQs to ground your answers in factual information. "
                                                 "If the FAQs don't contain the exact answer, use what is most "
                                                 "relevant and indicate when you're extrapolating. If nothing is "
                                                 "relevant, admit you don't know rather than making up information. "
                                                 "Keep your answers concise and to the point, with a maximum of "
                                                 "3-4 sentences unless more detail is required. Sign off with 'AURORA' for important responses."},
                    {"role": "user", "content": f"Based on these relevant FAQs:\n\n{formatted_faqs}\n\nPlease answer this question: {text}"}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            answer = response.choices[0].message.content
            logger.info("Generated RAG response using OpenAI")
            
            return answer, "rag"
        except Exception as e:
            logger.error(f"Error generating RAG response: {e}")
            return "I'm experiencing a glitch in the Matrix. Please try your question again later.", "error"
    
    def get_categories(self):
        """Return unique categories from FAQs for quick reply buttons."""
        try:
            return self.nltk_processor.get_categories()
        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            return []
    
    def get_questions_by_category(self, category):
        """Return questions for a specific category."""
        try:
            return self.nltk_processor.get_questions_by_category(category)
        except Exception as e:
            logger.error(f"Error getting questions by category: {e}")
            return []
