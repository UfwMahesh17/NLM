import os
import json
import re
import logging
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.sentiment import SentimentIntensityAnalyzer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class NLTKProcessor:
    def __init__(self):
        """Initialize NLTK processor with necessary downloads and load FAQs."""
        # Download required NLTK packages if not already present
        try:
            self._download_nltk_dependencies()
            
            # Load and prepare FAQs
            self.load_faqs()
            
            # Initialize NLTK tools
            self.lemmatizer = WordNetLemmatizer()
            self.sia = SentimentIntensityAnalyzer()
            
            # Create TF-IDF vectorizer for question matching
            self.vectorizer = TfidfVectorizer(
                tokenizer=self.preprocess_text,
                stop_words='english'
            )
            
            # Prepare FAQ corpus for vectorization
            questions = [faq['question'] for faq in self.faqs]
            self.question_vectors = self.vectorizer.fit_transform(questions)
            
            logger.info("NLTK processor initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing NLTK processor: {e}")
            raise
    
    def _download_nltk_dependencies(self):
        """Download necessary NLTK data."""
        try:
            nltk_data_path = os.environ.get('NLTK_DATA', os.path.expanduser('~/nltk_data'))
            os.makedirs(nltk_data_path, exist_ok=True)
            nltk.data.path.append(nltk_data_path)
            
            # Download required NLTK packages
            for package in ['punkt', 'wordnet', 'stopwords', 'vader_lexicon']:
                try:
                    nltk.data.find(f'tokenizers/{package}' if package == 'punkt' else package)
                    logger.debug(f"NLTK package {package} already downloaded")
                except LookupError:
                    logger.info(f"Downloading NLTK package: {package}")
                    nltk.download(package, download_dir=nltk_data_path, quiet=True)
        except Exception as e:
            logger.error(f"Error downloading NLTK dependencies: {e}")
            raise
            
    def load_faqs(self):
        """Load FAQs from JSON file."""
        try:
            with open('faqs.json', 'r') as f:
                self.faqs = json.load(f)
            logger.info(f"Loaded {len(self.faqs)} FAQs")
            
            # Create a dictionary to store FAQs by category
            self.faqs_by_category = {}
            self.categories = set()
            
            for faq in self.faqs:
                category = faq.get('category', 'General')
                self.categories.add(category)
                
                if category not in self.faqs_by_category:
                    self.faqs_by_category[category] = []
                
                self.faqs_by_category[category].append(faq)
            
            logger.info(f"Organized FAQs into {len(self.categories)} categories")
            
        except Exception as e:
            logger.error(f"Error loading FAQs: {e}")
            raise
    
    def preprocess_text(self, text):
        """Preprocess text by tokenizing, removing stopwords, and lemmatizing."""
        try:
            # Convert to lowercase
            text = text.lower()
            
            # Use simple split instead of word_tokenize to avoid punkt_tab issues
            tokens = text.split()
            
            # Remove punctuation and non-alphabetic tokens
            tokens = [re.sub(r'[^\w]', '', token) for token in tokens]
            tokens = [token for token in tokens if token.isalpha()]
            
            # Remove stopwords
            stop_words = set(stopwords.words('english'))
            tokens = [token for token in tokens if token not in stop_words]
            
            # Lemmatize tokens
            tokens = [self.lemmatizer.lemmatize(token) for token in tokens]
            
            return tokens
        except Exception as e:
            logger.error(f"Error preprocessing text: {e}")
            return text.lower().split()  # Fallback to simple tokenization
    
    def find_best_match(self, query, threshold=0.3):
        """Find the best matching FAQ for a given query."""
        try:
            # Vectorize the query
            query_vector = self.vectorizer.transform([query])
            
            # Calculate cosine similarity between query and all questions
            similarities = cosine_similarity(query_vector, self.question_vectors).flatten()
            
            # Find the most similar question
            best_match_idx = similarities.argmax()
            best_match_score = similarities[best_match_idx]
            
            # Check if the best match is above the threshold
            if best_match_score >= threshold:
                return self.faqs[best_match_idx], best_match_score
            else:
                return None, best_match_score
        except Exception as e:
            logger.error(f"Error finding best match: {e}")
            return None, 0.0
    
    def find_top_matches(self, query, top_k=3, threshold=0.2):
        """Find top k matching FAQs for a given query."""
        try:
            # Vectorize the query
            query_vector = self.vectorizer.transform([query])
            
            # Calculate cosine similarity between query and all questions
            similarities = cosine_similarity(query_vector, self.question_vectors).flatten()
            
            # Get indices of top k matches
            top_indices = similarities.argsort()[-top_k:][::-1]
            
            # Filter matches below threshold
            top_matches = [
                (self.faqs[idx], similarities[idx])
                for idx in top_indices
                if similarities[idx] >= threshold
            ]
            
            return top_matches
        except Exception as e:
            logger.error(f"Error finding top matches: {e}")
            return []
    
    def get_sentiment(self, text):
        """Analyze sentiment of text."""
        try:
            sentiment_scores = self.sia.polarity_scores(text)
            return sentiment_scores
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {'compound': 0.0, 'pos': 0.0, 'neg': 0.0, 'neu': 1.0}
    
    def get_categories(self):
        """Return unique categories from FAQs."""
        try:
            return sorted(list(self.categories))
        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            return []
    
    def get_questions_by_category(self, category):
        """Return questions for a specific category."""
        try:
            if category in self.faqs_by_category:
                return [faq['question'] for faq in self.faqs_by_category[category]]
            else:
                return []
        except Exception as e:
            logger.error(f"Error getting questions by category: {e}")
            return []

    def extract_keywords(self, text, top_n=5):
        """Extract top keywords from text based on TF-IDF."""
        try:
            # Preprocess the text
            preprocessed_tokens = self.preprocess_text(text)
            
            # If less than 2 tokens, return them all
            if len(preprocessed_tokens) < 2:
                return preprocessed_tokens
            
            # Create a small corpus with the text
            corpus = [text]
            
            # Create a new vectorizer for this text
            keyword_vectorizer = TfidfVectorizer(
                tokenizer=self.preprocess_text,
                stop_words='english'
            )
            
            # Generate TF-IDF matrix
            tfidf_matrix = keyword_vectorizer.fit_transform(corpus)
            
            # Get feature names (words)
            feature_names = keyword_vectorizer.get_feature_names_out()
            
            # Get TF-IDF scores
            scores = tfidf_matrix.toarray().flatten()
            
            # Create a dictionary of words and their TF-IDF scores
            word_scores = {feature_names[i]: scores[i] for i in range(len(feature_names))}
            
            # Sort words by score and get top n
            top_keywords = sorted(word_scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
            
            return [keyword for keyword, score in top_keywords]
        except Exception as e:
            logger.error(f"Error extracting keywords: {e}")
            return []
