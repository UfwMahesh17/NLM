import os
import json
import logging
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Chatbot:
    def __init__(self):
        """Initialize the chatbot with OpenAI for embeddings and completions."""
        # Load FAQs
        try:
            with open('faqs.json', 'r') as f:
                self.faqs = json.load(f)
            logger.info(f"Loaded {len(self.faqs)} FAQs")
        except Exception as e:
            logger.error(f"Error loading FAQs: {e}")
            raise

        # Initialize OpenAI client
        self.openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
        # Initialize FAQ categorization
        self._organize_faqs_by_category()

    def _organize_faqs_by_category(self):
        """Organize FAQs by category for quick retrieval."""
        try:
            self.categories = set()
            self.faqs_by_category = {}
            
            for faq in self.faqs:
                category = faq.get('category', 'General')
                self.categories.add(category)
                
                if category not in self.faqs_by_category:
                    self.faqs_by_category[category] = []
                    
                self.faqs_by_category[category].append(faq)
                
            logger.info(f"Organized FAQs into {len(self.categories)} categories")
        except Exception as e:
            logger.error(f"Error organizing FAQs: {e}")
            raise

    def _find_relevant_faqs(self, text, top_k=3):
        """Find the most relevant FAQs using OpenAI's capabilities."""
        try:
            # Create a completion to analyze the query and identify relevant categories
            category_prompt = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a classifier that reads a customer query and returns only "
                                                 "a comma-separated list of the most likely categories from the following "
                                                 f"options: {', '.join(sorted(self.categories))}. "
                                                 "Output only the category names, no explanations."},
                    {"role": "user", "content": text}
                ],
                temperature=0.3,
                max_tokens=50
            )
            
            # Extract likely categories 
            try:
                likely_categories = [c.strip() for c in category_prompt.choices[0].message.content.split(',')]
                logger.info(f"Identified likely categories: {likely_categories}")
            except:
                likely_categories = list(self.categories)[:3]  # Fallback to a few default categories
            
            # Collect FAQs from these categories
            candidate_faqs = []
            for category in likely_categories:
                if category in self.faqs_by_category:
                    candidate_faqs.extend(self.faqs_by_category[category])
            
            # If we don't have enough candidates, add some general FAQs
            if len(candidate_faqs) < top_k:
                remaining_categories = self.categories - set(likely_categories)
                for category in remaining_categories:
                    candidate_faqs.extend(self.faqs_by_category[category])
                    if len(candidate_faqs) >= top_k * 2:  # Get more than needed for ranking
                        break
            
            # Use OpenAI embeddings to rank the candidates
            if len(candidate_faqs) > top_k:
                # Use completions API to rank FAQs based on relevance
                ranking_prompt = self.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You will be given a user query and a list of FAQs with answers. "
                                                     "Your task is to identify the top 3 most relevant FAQs that best "
                                                     "address the user's query. Return only the numbers of the top FAQs "
                                                     "in order of relevance, comma-separated (e.g., '2,5,1')."},
                        {"role": "user", "content": f"User query: {text}\n\nFAQs:\n" + "\n".join([
                            f"{i}. Q: {faq['question']}\nA: {faq['answer']}"
                            for i, faq in enumerate(candidate_faqs[:top_k * 2])
                        ])}
                    ],
                    temperature=0.3,
                    max_tokens=50
                )
                
                try:
                    # Parse the ranking results
                    ranking_str = ranking_prompt.choices[0].message.content
                    # Extract just numbers from the response
                    import re
                    rank_indices = [int(idx) for idx in re.findall(r'\d+', ranking_str)][:top_k]
                    relevant_faqs = [candidate_faqs[idx] for idx in rank_indices if idx < len(candidate_faqs)]
                    
                    # If we didn't get enough FAQs, fall back to the first few candidates
                    if len(relevant_faqs) < top_k:
                        relevant_faqs.extend(candidate_faqs[:top_k - len(relevant_faqs)])
                    
                    return relevant_faqs[:top_k]
                except:
                    # Fallback if parsing fails
                    return candidate_faqs[:top_k]
            else:
                # Not enough to rank, return what we have
                return candidate_faqs[:top_k]
        except Exception as e:
            logger.error(f"Error finding relevant FAQs: {e}")
            return self.faqs[:top_k]  # Fallback to first few FAQs

    def get_response(self, text):
        """
        Process user input and generate a response using a hybrid RAG approach.
        
        Returns:
            tuple: (response_text, source) where source is "rag"
        """
        try:
            # Find top relevant FAQs
            relevant_faqs = self._find_relevant_faqs(text, top_k=3)
            
            # Format the FAQs for input to GPT
            formatted_faqs = "\n\n".join([
                f"FAQ {i+1}:\nQuestion: {faq['question']}\nAnswer: {faq['answer']}\nCategory: {faq['category']}"
                for i, faq in enumerate(relevant_faqs)
            ])
            
            # Generate response using GPT
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
                messages=[
                    {"role": "system", "content": "You are a customer support agent for an e-commerce website with a "
                                                 "Matrix-themed interface. Your answers should be helpful, accurate, "
                                                 "and styled with subtle references to The Matrix movie. Use the "
                                                 "provided FAQs to ground your answers in factual information. "
                                                 "If the FAQs don't contain the exact answer, use what is most "
                                                 "relevant and indicate when you're extrapolating. If nothing is "
                                                 "relevant, admit you don't know rather than making up information."},
                    {"role": "user", "content": f"Based on these relevant FAQs:\n\n{formatted_faqs}\n\nPlease answer this question: {text}"}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            answer = response.choices[0].message.content
            logger.info("Generated RAG response using OpenAI")
            
            return answer, "rag"
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I'm experiencing a glitch in the Matrix. Please try your question again later.", "error"

    def get_categories(self):
        """Return unique categories from FAQs for quick reply buttons."""
        try:
            return sorted(list(self.categories))
        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            return []
