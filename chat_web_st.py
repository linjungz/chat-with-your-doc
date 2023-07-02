from chatbot import DocChatbot
import shutil
import os
import streamlit as st

docChatbot = DocChatbot()
docChatbot.load_vector_db_from_local("./data/vector_store", "index")
docChatbot.init_chatchain()


with st.sidebar:
    "[Github Repo Link](https://github.com/linjungz/chat-with-your-doc)"

st.title("💬 Chat with Your Doc")

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if user_input := st.chat_input():
    # Get response from LLM
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user").write(user_input)

    result_answer, result_source = docChatbot.get_answer(
        user_input, 
        st.session_state.messages)
        

    # Write answer to the chat window and save it to session
    st.session_state.messages.append({"role": "assistant", "content": result_answer})

    with st.chat_message("assistant"):
        st.write(result_answer)
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

    