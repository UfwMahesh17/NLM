import os
import json
import logging
import numpy as np
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Try to import FAISS, fallback to Pinecone if not available
try:
    import faiss
    use_faiss = True
    logger.info("Using FAISS for vector indexing")
except ImportError:
    import pinecone
    use_faiss = False
    logger.info("Using Pinecone for vector indexing")

def load_faqs():
    """Load FAQs from JSON file."""
    try:
        with open('faqs.json', 'r') as f:
            faqs = json.load(f)
        logger.info(f"Loaded {len(faqs)} FAQs from faqs.json")
        return faqs
    except Exception as e:
        logger.error(f"Error loading FAQs: {e}")
        raise

def index_with_faiss(faqs, model):
    """Index FAQs using FAISS."""
    try:
        # Extract questions for embedding
        questions = [faq['question'] for faq in faqs]
        
        # Generate embeddings
        embeddings = model.encode(questions)
        embeddings = np.array(embeddings).astype('float32')
        
        # Create FAISS index
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)  # L2 distance index
        index.add(embeddings)
        
        # Save index to disk
        faiss.write_index(index, 'faiss_index.bin')
        
        # Create and save mapping from index to FAQ
        faqs_mapping = {str(i): {"question": faq["question"], "answer": faq["answer"]} 
                        for i, faq in enumerate(faqs)}
        
        with open('faqs_mapping.json', 'w') as f:
            json.dump(faqs_mapping, f, indent=2)
        
        logger.info(f"Created FAISS index with {index.ntotal} vectors of dimension {dimension}")
        logger.info("Saved index to faiss_index.bin and mapping to faqs_mapping.json")
        
        return index, faqs_mapping
    except Exception as e:
        logger.error(f"Error creating FAISS index: {e}")
        raise

def index_with_pinecone(faqs, model):
    """Index FAQs using Pinecone."""
    try:
        # Initialize Pinecone
        api_key = os.environ.get("PINECONE_API_KEY")
        if not api_key:
            logger.error("PINECONE_API_KEY not found in environment variables")
            raise ValueError("PINECONE_API_KEY environment variable is required")
        
        pinecone.init(api_key=api_key)
        
        # Extract questions for embedding
        questions = [faq['question'] for faq in faqs]
        
        # Generate embeddings
        embeddings = model.encode(questions)
        
        # Create or get index
        index_name = "ecommerce-faq"
        dimension = len(embeddings[0])
        
        # Check if index exists, if not create it
        if index_name not in pinecone.list_indexes():
            pinecone.create_index(name=index_name, dimension=dimension, metric="cosine")
            logger.info(f"Created new Pinecone index: {index_name}")
        
        index = pinecone.Index(index_name)
        
        # Create and upsert vectors
        vectors = []
        for i, (embedding, faq) in enumerate(zip(embeddings, faqs)):
            vector = {
                "id": str(i),
                "values": embedding.tolist(),
                "metadata": {
                    "question": faq["question"],
                    "answer": faq["answer"],
                    "category": faq["category"]
                }
            }
            vectors.append(vector)
        
        # Upsert in batches of 100
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i+batch_size]
            index.upsert(vectors=batch)
        
        # Create and save mapping from index to FAQ
        faqs_mapping = {str(i): {"question": faq["question"], "answer": faq["answer"]} 
                        for i, faq in enumerate(faqs)}
        
        with open('faqs_mapping.json', 'w') as f:
            json.dump(faqs_mapping, f, indent=2)
        
        logger.info(f"Indexed {len(vectors)} vectors in Pinecone index: {index_name}")
        logger.info("Saved mapping to faqs_mapping.json")
        
        return index, faqs_mapping
    except Exception as e:
        logger.error(f"Error indexing with Pinecone: {e}")
        raise

def main():
    """Main function to load FAQs and create vector index."""
    try:
        # Load FAQs
        faqs = load_faqs()
        
        # Initialize sentence transformer model
        model_name = "all-MiniLM-L6-v2"
        model = SentenceTransformer(model_name)
        logger.info(f"Loaded sentence transformer model: {model_name}")
        
        # Create vector index based on available library
        if use_faiss:
            index, faqs_mapping = index_with_faiss(faqs, model)
        else:
            index, faqs_mapping = index_with_pinecone(faqs, model)
        
        logger.info("FAQ indexing completed successfully")
        
        # Simple test of the index
        if use_faiss:
            # Test query with FAISS
            test_query = "How do I return a product?"
            test_embedding = model.encode([test_query])[0]
            test_embedding = np.array([test_embedding]).astype('float32')
            
            distances, indices = index.search(test_embedding, k=3)
            logger.info("Test query: 'How do I return a product?'")
            logger.info(f"Top 3 matches: {[faqs_mapping[str(idx)] for idx in indices[0]]}")
        else:
            # Test query with Pinecone
            test_query = "How do I return a product?"
            test_embedding = model.encode([test_query])[0]
            
            results = index.query(
                vector=test_embedding.tolist(),
                top_k=3,
                include_metadata=True
            )
            
            logger.info("Test query: 'How do I return a product?'")
            logger.info(f"Top 3 matches: {[match['metadata'] for match in results['matches']]}")
    
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        raise

if __name__ == "__main__":
    main()
