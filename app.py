import os
import streamlit as st
from chatbot_service import ChatbotService

# Initialize chatbot service
chatbot_service = ChatbotService()

# Streamlit UI
st.title("Aurora Support Chatbot")

# Load categories from the service
categories = chatbot_service.get_categories()
selected_category = st.selectbox("Select a Category", categories)

# User input
user_message = st.text_input("Your Message", "")

if st.button("Send"):
    if user_message.strip() == "":
        st.warning("Please enter a message.")
    else:
        try:
            # Get response from the chatbot
            response = chatbot_service.chat(user_message, selected_category)
            st.markdown(f"**Bot:** {response}")
        except Exception as e:
            st.error(f"Error: {str(e)}")
