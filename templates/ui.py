import streamlit as st
import requests

# Set the app title
st.title("Cube AI API Demo")

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display past messages with adjusted alignment
for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(f'<div style="text-align: right;">{message["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(message["content"])  # Default alignment for assistant is left

# Get user input
if prompt := st.chat_input("What's on your mind?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display user message aligned to the right
    st.markdown(f'<div style="text-align: right;">{prompt}</div>', unsafe_allow_html=True)

    # Send request to FastAPI
    try:
        response = requests.post("http://localhost:8080/ask", json={"query": prompt})

        # Handle successful response
        if response.status_code == 200:
            data = response.json()
            answer = data["formatted_data"]

            # Add bot response to chat history
            st.session_state.messages.append({"role": "assistant", "content": answer})

            # Display assistant response (default left alignment)
            st.markdown(answer)

        else:
            # Handle errors from FastAPI
            st.error(f"Error from FastAPI: {response.status_code} - {response.text}")

    except requests.exceptions.RequestException as e:
        # Handle connection errors
        st.error(f"Error connecting to FastAPI: {e}")