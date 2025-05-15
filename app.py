import os
import json
import logging
from flask import Flask, render_template, request, jsonify
from chatbot_service import ChatbotService

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "aurora-support-secret")

# Initialize chatbot service
chatbot_service = ChatbotService()

@app.route('/')
def home():
    """Render the home page with the chat interface."""
    categories = chatbot_service.get_categories()
    return render_template('index.html', categories=categories)

@app.route('/api/chat', methods=['POST'])
def chat():
    """Process chat messages and return responses."""
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({'error': 'Invalid request. Message is required.'}), 400
        
        user_message = data['message']
        logger.debug(f"Received message: {user_message}")
        
        # Determine whether to use NLTK or RAG/OpenAI
        use_rag = data.get('use_rag', False)
        
        if use_rag:
            # Use OpenAI for more complex or specific questions
            response, source = chatbot_service.get_rag_response(user_message)
        else:
            # Use NLTK for simple, common questions
            response, source, confidence = chatbot_service.get_nltk_response(user_message)
            
            # If NLTK confidence is low, fallback to RAG/OpenAI
            if confidence < 0.6:
                response, source = chatbot_service.get_rag_response(user_message)
        
        return jsonify({
            'response': response,
            'source': source
        })
        
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        return jsonify({
            'error': 'Something went wrong processing your message.',
            'details': str(e)
        }), 500

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Return available FAQ categories for quick replies."""
    try:
        categories = chatbot_service.get_categories()
        return jsonify({'categories': categories})
    except Exception as e:
        logger.error(f"Error getting categories: {str(e)}")
        return jsonify({'error': 'Could not retrieve categories.'}), 500

@app.route('/api/category_questions', methods=['GET'])
def get_category_questions():
    """Return questions for a specific category."""
    try:
        category = request.args.get('category')
        if not category:
            return jsonify({'error': 'Category parameter is required.'}), 400
            
        questions = chatbot_service.get_questions_by_category(category)
        return jsonify({'questions': questions})
    except Exception as e:
        logger.error(f"Error getting questions for category: {str(e)}")
        return jsonify({'error': 'Could not retrieve questions.'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
