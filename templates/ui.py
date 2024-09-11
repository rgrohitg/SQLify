import streamlit as st
import requests
import json
import matplotlib.pyplot as plt

# Set the app title
st.title("Cube AI API Demo with Plotting")

# Gemini AI inspired CSS styling with sidebar and corrected colors
st.markdown("""
<style>
body {
    font-family: Arial, sans-serif; /* Similar font */
    background-color: #2e3440; /* Dark background similar to Gemini AI */
    color: #d8dee9; /* Light text color */
}

.user-message {
    text-align: right;
    margin-bottom: 10px;
}

.bot-message {
    background-color: #434c5e; /* Slightly lighter gray for better contrast */
    padding: 10px;
    border-radius: 5px;
    margin-bottom: 10px;
    color: #d8dee9; /* Ensure text color is visible on the background */
}

.stChatInputContainer { /* Style the chat input area */
    border: 1px solid #ccc;
    border-radius: 5px;
    padding: 5px;
}

/* Sidebar styling */
.sidebar {
    width: 250px; /* Adjust as needed */
    padding: 20px;
    background-color: #3b4252; /* Darker gray for the sidebar */
    border-right: 1px solid #ccc;
    overflow-y: auto; /* Enable scrolling if content overflows */
}

.sidebar .message {
    margin-bottom: 10px;
}

/* New Chat button */
.new-chat-button {
    background-color: #4c566a; /* Button background color */
    color: #d8dee9; /* Button text color */
    border: none;
    padding: 10px 20px;
    text-align: center;
    text-decoration: none;
    display: inline-block;
    font-size: 16px;
    margin: 4px 2px;
    cursor: pointer;
    border-radius: 5px;
}

/* Chat session styling */
.chat-session {
    margin-bottom: 20px; /* Add spacing between chat sessions */
}
</style>
""", unsafe_allow_html=True)


# Initialize chat history in session state, now as a list of sessions
if "chat_sessions" not in st.session_state:
    st.session_state.chat_sessions = []

# Create sidebar for Conversation History and New Chat button
with st.sidebar:
    # New Chat button functionality
    if st.button("New Chat"):
        st.session_state.chat_sessions.append([])  # Start a new chat session

    st.header("Conversation History")
    for session_index, session_messages in enumerate(st.session_state.chat_sessions):
        # Display the first question as the conversation title (if available)
        conversation_title = session_messages[0]["content"] if session_messages else "Empty Conversation"
        st.markdown(f'<div class="chat-session">**{conversation_title}**</div>', unsafe_allow_html=True)

# Main chat area
# Get user input
if prompt := st.chat_input("What's on your mind?"):
    # If no chat sessions exist, start a new one
    if not st.session_state.chat_sessions:
        st.session_state.chat_sessions.append([])

    # Add user message to the current chat session
    st.session_state.chat_sessions[-1].append({"role": "user", "content": prompt})

    # Send request to FastAPI
    try:
        response = requests.post("http://localhost:8080/ask", json={"query": prompt})

        # Handle successful response
        if response.status_code == 200:
            data = response.json()
            answer = data["formatted_data"]

            # Add bot response to the current chat session
            st.session_state.chat_sessions[-1].append({"role": "assistant", "content": answer})

            # ... (plotting logic remains the same)

        else:
            # Handle errors from FastAPI
            st.error(f"Error from FastAPI: {response.status_code} - {response.text}")

    except requests.exceptions.RequestException as e:
        # Handle connection errors
        st.error(f"Error connecting to FastAPI: {e}")

# Display the current conversation in the main area
if st.session_state.chat_sessions:
    # Display all messages from the last (current) session
    for message in st.session_state.chat_sessions[-1]:
        if message["role"] == "user":
            st.markdown(f'<div class="user-message">{message["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="bot-message">{message["content"]}</div>', unsafe_allow_html=True)
else:
    st.write("Start a new chat to see the conversation here.")