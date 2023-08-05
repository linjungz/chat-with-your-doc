from chatbot import DocChatbot
import shutil
import os
import streamlit as st
from datetime import datetime

docChatBot = DocChatbot()
available_indexes = docChatBot.get_available_indexes("./data/vector_store")

# Add an option for "Uploaded File"
index_options = ["-- Existing Vector Stores --"] + available_indexes

with st.sidebar:
    st.title("💬 Chat with Your Doc")
    st.write("Upload a document and ask questions about it.")

    with st.form("Upload and Process", True):
        # Dropdown for selecting an index or uploaded file
        selected_index = st.selectbox('Select an existing vector store or upload a file to create one, then press Process button', index_options)

        uploaded_file = st.file_uploader("Upload documents", type=["pdf", "md", "txt", "docx", ".csv", ".xml"])
        submitted = st.form_submit_button("Process")

        if submitted:
            try:
                if selected_index == "-- Existing Vector Stores --":
                    if uploaded_file:
                        ext_name = os.path.splitext(uploaded_file.name)[-1]
                        if ext_name not in [".pdf", ".md", ".txt", ".docx", ".csv", ".xml"]:
                            st.error("Unsupported file type.")
                            st.stop()
                        # Save the uploaded file to local
                        timestamp = int(datetime.timestamp(datetime.now()))
                        local_file_name = f"""./data/uploaded/{timestamp}{ext_name}"""
                        with open(local_file_name, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                            f.close()

                        docChatBot.init_vector_db_from_documents([local_file_name])
                else:
                    docChatBot.load_vector_db_from_local("./data/vector_store", selected_index)

                st.session_state['docChatBot'] = docChatBot
                st.session_state["messages"] = [{"role": "assistant", "content": "Hi!😊"}]

                st.success("Vector db initialized.")
                st.balloons()
            except Exception as e:
                st.error(f"An error occurred while processing the file: {str(e)}")
                st.stop()
                
    with st.container():
        "[Github Repo Link](https://github.com/linjungz/chat-with-your-doc)"

if 'messages' in st.session_state:
    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

if user_input := st.chat_input():
    if 'docChatBot' not in st.session_state:
        st.error("Please upload a document in the side bar and click the 'Process' button.")
        st.stop()

    # Get response from LLM
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user").write(user_input)

    with st.chat_message("assistant"):
        # Streaming answer to the chat window
        condense_question_container = st.empty()
        answer_container = st.empty()
        
        docChatBot = st.session_state['docChatBot']
        docChatBot.init_streaming(condense_question_container, answer_container)
        docChatBot.init_chatchain()
            
        result_answer, result_source = docChatBot.get_answer(
            user_input, 
            st.session_state.messages)
        
        answer_container.markdown(result_answer)

        # Augement source document to the answer
        i = 0
        with st.expander("References"):
            for doc in result_source:
                # For some PDF documents, PyPDF seems not able to extract the page number. So need to check the metadata of the source.
                source_str = os.path.basename(doc.metadata["source"]) if "source" in doc.metadata else ""
                page_str = doc.metadata['page'] + 1 if "page" in doc.metadata else ""
                st.write(f"""### Reference [{i+1}] {source_str} P{page_str}""")
                st.write(doc.page_content)
                i += 1

    # Save the answer to session
    st.session_state.messages.append({"role": "assistant", "content": result_answer})

    
        

    