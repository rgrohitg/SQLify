import streamlit as st
import requests

# Set the app title
st.title("Cube AI API Demo")

# Add custom CSS for ChatGPT-like styling
def add_custom_css():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

            body, input, textarea {
                font-family: 'Inter', sans-serif;
                font-size: 16px;
            }

            .user-message {
                background-color: #0056D2;
                color: white;
                font-size: 16px;
                font-weight: 500;
                border-radius: 10px;
                padding: 10px;
                margin-bottom: 10px;
                max-width: 60%;
                align-self: flex-end;
                text-align: right;
            }

            .bot-message {
                background-color: #E1E1E1;
                color: #444;
                font-size: 16px;
                border-radius: 10px;
                padding: 10px;
                margin-bottom: 10px;
                max-width: 60%;
                text-align: left;
            }

            .feedback {
                display: flex;
                gap: 10px;
                margin-top: -5px;
            }

            .feedback button {
                border: none;
                background-color: transparent;
                font-size: 20px;
                cursor: pointer;
                padding: 0;
            }

            .fixed-bottom-input {
                position: fixed;
                bottom: 0;
                width: 100%;
                left: 0;
                background-color: #FFFFFF;
                padding: 10px 15px;
                box-shadow: 0px -3px 5px rgba(0, 0, 0, 0.1);
                display: flex;
                align-items: center;
                z-index: 99;
            }

            .chat-container {
                display: flex;
                flex-direction: column;
                padding-bottom: 100px;  /* Avoid overlapping input */
                max-height: 70vh;       /* Limit the chat height */
                overflow-y: auto;
            }

            .send-icon {
                background-color: #0056D2;
                color: white;
                font-size: 20px;
                border: none;
                border-radius: 50%;
                padding: 10px;
                margin-left: 10px;
                cursor: pointer;
            }

        </style>
    """, unsafe_allow_html=True)

add_custom_css()

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Function to display thumbs up/down feedback
def display_feedback(message_index):
    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("👍", key=f'thumbs_up_{message_index}', help="Thumbs up"):
            st.success("You gave thumbs up!")
            # Send feedback to your API or log the action

    with col2:
        if st.button("👎", key=f'thumbs_down_{message_index}', help="Thumbs down"):
            st.error("You gave thumbs down!")
            # Send feedback to your API or log the action

# Display chat history
if st.session_state.messages:
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for i, message in enumerate(st.session_state.messages):
        if message["role"] == "user":
            st.markdown(f'<div class="user-message">{message["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="bot-message">{message["content"]}</div>', unsafe_allow_html=True)
            # Display thumbs up and down after bot response
            display_feedback(i)
    st.markdown('</div>', unsafe_allow_html=True)

# Input form at the bottom
def input_ui():
    # Use a form to capture the input and the send icon
    with st.form(key='input_form', clear_on_submit=True):
        col1, col2 = st.columns([10, 1])
        with col1:
            prompt = st.text_input("You: ", key="user_input", placeholder="Type your message here...", label_visibility="collapsed")
        with col2:
            submit_button = st.form_submit_button(label="Send", use_container_width=False, help="Send message", button_type='primary')

        if submit_button and prompt:
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})

            # Send request to the backend API
            try:
                response = requests.post("http://localhost:8080/ask", json={"query": prompt})

                # Handle successful response
                if response.status_code == 200:
                    data = response.json()
                    answer = data.get("formatted_data", "Sorry, I didn't understand that.")

                    # Add bot response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                else:
                    st.error(f"Error from API: {response.status_code} - {response.text}")

            except requests.exceptions.RequestException as e:
                st.error(f"Error connecting to API: {e}")

# Always show input at the bottom
st.markdown('<div class="fixed-bottom-input">', unsafe_allow_html=True)
input_ui()
st.markdown('</div>', unsafe_allow_html=True)
