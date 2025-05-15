import os
import logging
import json
from flask import Flask, render_template, request, jsonify
from chatbot_model import Chatbot

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "fallback_secret_key")

# Initialize the chatbot
try:
    chatbot = Chatbot()
    logger.info("Chatbot initialized successfully")
except Exception as e:
    logger.error(f"Error initializing chatbot: {e}")
    chatbot = None

@app.route('/')
def index():
    """Render the chat interface."""
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    """Process user message and return chatbot response."""
    try:
        data = request.json
        message = data.get('message', '')
        
        if not message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Find relevant FAQs with improved matching
        relevant_faqs = []
        
        # First, try to match by exact category
        if message.lower().startswith("tell me about "):
            category = message.lower().replace("tell me about ", "").strip()
            for faq in faqs:
                if faq['category'].lower() == category:
                    relevant_faqs.append((faq, 2))  # Higher score for category match
        
        # Then try to match by keywords with scoring
        message_words = set(message.lower().split())
        for faq in faqs:
            # Count how many words match
            question_words = set(faq['question'].lower().split())
            category_words = set(faq['category'].lower().split())
            
            # Calculate score based on matching words
            word_matches = len(message_words.intersection(question_words))
            category_matches = len(message_words.intersection(category_words))
            
            # Base score from word matches
            score = word_matches * 2  # Give more weight to question matches
            
            # Add score from category matches with special emphasis
            if category_matches > 0:
                # Add extra points for category matches
                score += category_matches * 3
                
                # Special emphasis on payment-related matches
                if faq['category'] == 'Payments':
                    # Significant boost for payment-related questions
                    payment_keywords = ['payment', 'payments', 'pay', 'paid', 'card', 'credit', 'debit', 
                                      'visa', 'mastercard', 'paypal', 'apple pay', 'google pay',
                                      'method', 'methods', 'charge', 'billing', 'installment',
                                      'rupee', 'rupees', 'inr', '₹', 'upi', 'paytm', 'phonepe', 'gpay',
                                      'bhim', 'net banking', 'emi', 'hdfc', 'icici', 'sbi', 'axis',
                                      'rupay', 'gst', 'india', 'indian']
                    
                    # Check if message contains any payment keywords
                    if any(keyword in message.lower() for keyword in payment_keywords):
                        score += 8  # Very high boost for payment questions
                        
                    # Extra boost for exact question matches
                    if "what payment methods" in message.lower() and "payment methods" in faq['question'].lower():
                        score += 10  # Maximum priority for exact payment methods question
                        
                    # Special case for Indian payment methods
                    if any(term in message.lower() for term in ['india', 'indian', 'rupee', 'rupees', 'inr', '₹', 'upi']) and "indian" in faq['question'].lower():
                        score += 15  # Absolute highest priority for Indian payment method questions
                
            # Add to relevant FAQs if score is positive
            if score > 0:
                relevant_faqs.append((faq, score))
        
        # Sort by score (highest first)
        relevant_faqs.sort(key=lambda x: x[1], reverse=True)
        
        # If we found relevant FAQs directly
        if relevant_faqs:
            selected_faq = relevant_faqs[0][0]  # Take the highest scoring match
            logger.info(f"Matched FAQ: {selected_faq['question']} with score {relevant_faqs[0][1]}")
            return jsonify({
                'reply': selected_faq['answer'],
                'source': 'direct'
            })
        
        # Otherwise use OpenAI to generate a response
        try:
            # Select relevant FAQs for context based on query
            filtered_faqs = []
            
            # Try to identify the category
            category_keywords = {
                'product': 'Products',
                'products': 'Products',
                'item': 'Products',
                'items': 'Products',
                'shipping': 'Shipping',
                'delivery': 'Shipping',
                'ship': 'Shipping',
                'return': 'Returns',
                'refund': 'Returns',
                'exchange': 'Returns',
                'payment': 'Payments',
                'payments': 'Payments',
                'pay': 'Payments',
                'paid': 'Payments',
                'card': 'Payments',
                'credit': 'Payments',
                'debit': 'Payments',
                'paypal': 'Payments',
                'method': 'Payments',
                'methods': 'Payments',
                'visa': 'Payments',
                'mastercard': 'Payments',
                'billing': 'Payments',
                'rupee': 'Payments',
                'rupees': 'Payments',
                'inr': 'Payments',
                '₹': 'Payments',
                'upi': 'Payments',
                'paytm': 'Payments',
                'phonepe': 'Payments',
                'gpay': 'Payments',
                'bhim': 'Payments',
                'netbanking': 'Payments',
                'emi': 'Payments',
                'hdfc': 'Payments',
                'icici': 'Payments',
                'sbi': 'Payments',
                'axis': 'Payments',
                'rupay': 'Payments',
                'gst': 'Payments',
                'india': 'Payments',
                'indian': 'Payments',
                'account': 'Account',
                'login': 'Account',
                'profile': 'Account'
            }
            
            # Determine likely categories
            likely_categories = set()
            for word in message.lower().split():
                if word in category_keywords:
                    likely_categories.add(category_keywords[word])
            
            # If we've identified categories, prioritize those FAQs
            if likely_categories:
                for faq in faqs:
                    if faq['category'] in likely_categories:
                        filtered_faqs.append(faq)
                
                # Add some FAQs from other categories to provide context
                additional_faqs = [faq for faq in faqs if faq['category'] not in likely_categories][:5]
                filtered_faqs.extend(additional_faqs)
            else:
                # Otherwise, use a mix of all categories
                filtered_faqs = faqs[:15]
            
            # Build prompt with selected FAQs
            prompt_faqs = "\n".join([
                f"Category: {faq['category']}\nQ: {faq['question']}\nA: {faq['answer']}"
                for faq in filtered_faqs
            ])
            
            # Determine if any specific categories were identified
            category_info = ""
            system_instructions = ""
            
            if likely_categories:
                category_info = f"The user is asking about: {', '.join(likely_categories)}. "
                
                # Special instructions for payment queries
                if 'Payments' in likely_categories:
                    system_instructions = """
When answering payment-related questions:
1. Be very precise about accepted payment methods
2. Emphasize security features for payment processing
3. Explain exactly when payments are processed
4. Make sure to cover all payment methods mentioned in the FAQs
5. If asked about payment methods, prioritize giving a complete list of all accepted methods
6. For questions about Indian payment methods, include details about UPI (PhonePe, Google Pay, Paytm), net banking, and RuPay cards
7. Mention that for Indian customers, all prices are in INR (₹) and GST is included
8. If asked about installments or EMI, include available options for Indian banks (HDFC, ICICI, SBI, Axis)
                    """
            
            # Call OpenAI API with improved prompt
            response = openai_client.chat.completions.create(
                model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
                messages=[
                    {"role": "system", "content": f"You are a friendly e-commerce customer support assistant. {category_info}Answer questions precisely and accurately based only on the FAQs provided. Do not invent information. If the FAQs don't contain a direct answer, use the closest related information from the FAQs to provide a helpful response.\n\n{system_instructions}"},
                    {"role": "user", "content": f"Here are the relevant FAQs to use for answering:\n\n{prompt_faqs}\n\nUser question: {message}"}
                ],
                temperature=0.5,  # Lower temperature for more focused responses
                max_tokens=300
            )
            
            answer = response.choices[0].message.content
            logger.info("Generated response using OpenAI")
            
            return jsonify({
                'reply': answer,
                'source': 'rag'
            })
        except Exception as e:
            logger.error(f"Error calling OpenAI: {e}")
            return jsonify({
                'reply': "I'm having trouble generating a response. Please try asking in a different way.",
                'source': 'error'
            })
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        return jsonify({'error': 'Failed to process message'}), 500

@app.route('/categories')
def categories():
    """Get all available FAQ categories."""
    try:
        # Extract unique categories from FAQs
        unique_categories = sorted(list(set(faq['category'] for faq in faqs)))
        return jsonify(unique_categories)
    except Exception as e:
        logger.error(f"Error fetching categories: {e}")
        return jsonify({'error': 'Failed to fetch categories'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
