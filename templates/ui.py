import streamlit as st
import requests
import json
import matplotlib.pyplot as plt

# Set the app title
st.title("Cube AI API Demo with Plotting")

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display past messages
for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(f'<div style="text-align: right;">{message["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(message["content"], unsafe_allow_html=True)

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

            # Display assistant response (text part)
            st.markdown(answer, unsafe_allow_html=True)

            # Extract the dictionary for plotting from the LLM response (if present)
            if "{" in answer and "}" in answer:  # Checking if JSON-like structure is present
                start = answer.find("{")
                end = answer.find("}") + 1
                plot_data_str = answer[start:end]

                # Convert the extracted string to a Python dictionary
                plot_data = json.loads(plot_data_str)

                # Plot the data using matplotlib
                categories = list(plot_data.keys())
                values = list(plot_data.values())

                fig, ax = plt.subplots()
                ax.bar(categories, values)
                ax.set_xlabel("Product Categories")
                ax.set_ylabel("Product Count")
                ax.set_title("Product Categories vs. Number of Products")

                # Display the plot in Streamlit
                st.pyplot(fig)

        else:
            # Handle errors from FastAPI
            st.error(f"Error from FastAPI: {response.status_code} - {response.text}")

    except requests.exceptions.RequestException as e:
        # Handle connection errors
        st.error(f"Error connecting to FastAPI: {e}")
