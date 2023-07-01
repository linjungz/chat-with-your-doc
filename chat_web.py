import gradio as gr
from chatbot import DocChatbot
import shutil
import os
import fnmatch
import re

block_css = """.importantButton {
    background: linear-gradient(45deg, #7e0570,#5d1c99, #6e00ff) !important;
    border: none !important;
}
.importantButton:hover {
    background: linear-gradient(45deg, #ff00e0,#8500ff, #6e00ff) !important;
    border: none !important;
}"""

webui_title = """
# Chat with Your Documents
"""

init_message = """Hello!"""

VS_ROOT_PATH = "./data/vector_store"
UPLOAD_ROOT_PATH = "./data/source_documents/"

def get_vs_list():
    if not os.path.exists(VS_ROOT_PATH):
        return []
    
    file_list = os.listdir(VS_ROOT_PATH)
    faiss_file_list = [file.split(".")[0] for file in file_list if fnmatch.fnmatch(file, "*.faiss")]
    index_list = list(set(faiss_file_list))
    # print(index_list)

    return index_list

def select_vs_on_change(vs_id):
    switch_kb(vs_id)
    return [[None, init_message]]

def switch_kb(index: str):
    docChatbot.load_vector_db_from_local(VS_ROOT_PATH, index)
    docChatbot.init_chatchain()

def ingest_docs_to_vector_store(vs_name, files, vs_list, select_vs):
    # print(vs_name)
    # print(files)

    # Check if vs_name already exists
    if vs_name in vs_list:
        return gr.update(visible=True), vs_list, select_vs, gr.update(value="", placeholder=f"Index name {vs_name} already exits."), 

    file_list = []
    if files is not []:
        for file in files:
            filename = os.path.split(file.name)[-1]
            shutil.move(file.name, UPLOAD_ROOT_PATH + filename)
            file_list.append(UPLOAD_ROOT_PATH + filename)

    
    # create new kb and ingest data to vector store   
    docChatbot.init_vector_db_from_documents(file_list)
    docChatbot.save_vector_db_to_local(VS_ROOT_PATH, vs_name)
    docChatbot.init_chatchain()
    return None, vs_list + [vs_name], gr.update(choices=vs_list+[vs_name]), gr.update(value="", placeholder="")

def get_answer(message, chat_history):

    #only process latest 4 messages to reduce token
    MESSAGES_TO_REFERENCE = 4
    msg_count = len(chat_history)
    if msg_count > MESSAGES_TO_REFERENCE:
        chat_history = chat_history[msg_count-MESSAGES_TO_REFERENCE:]

    ch = []
    for chat in chat_history:
        q = "" if chat[0] == None else chat[0]
        a = "" if chat[1] == None else chat[1]
        # remove details for reference to reduce token
        a = re.sub(r"<details>.*</details>", "", a)
        ch.append((q, a))

    #todo: need to handle exception
    result_answer, result_source = docChatbot.get_answer_with_source(message, ch)

    # print(result_answer)
    # print(result_source)
    output_source = "\n\n"
    i = 0
    for doc in result_source:
        reference_html = f"""<details> <summary>Reference [{i+1}] """

        # For some PDF documents, PyPDF seems not able to extract the page number. So need to check the metadata of the source.
        if "source" in doc.metadata:
            reference_html += f"""{os.path.basename(doc.metadata["source"])} """
        if "page" in doc.metadata:
            reference_html += f"""P{doc.metadata['page']+1}"""
            
        reference_html += f"""</summary>\n"""

        reference_html += f"""{doc.page_content}\n"""
        reference_html += f"""</details>"""
        output_source += reference_html
        i += 1

    chat_history.append((message, result_answer + output_source))
    return "", chat_history

# Init for web ui
docChatbot = DocChatbot()
vector_stores_list = get_vs_list()

with gr.Blocks(css=block_css) as demo:
    vs_list = gr.State(value=vector_stores_list)
    vs_path = gr.State(value="")

    gr.Markdown(webui_title)

    with gr.Tab("Chat"):
        with gr.Row():
            with gr.Column(scale=10):
                chatbot = gr.Chatbot([[None, init_message]],
                                     elem_id="chat-box",
                                     show_label=False).style(height=600)
                query = gr.Textbox(show_label=False,
                                   placeholder="Input your question here and press Enter to get answer.",
                                   ).style(container=False)
                query.submit( # type: ignore
                    get_answer,
                    [query,chatbot],
                    [query,chatbot]
                )

            with gr.Column(scale=5):
                vs_setting_switch = gr.Accordion("Switch Knowledge Base")
                with vs_setting_switch:
                    select_vs = gr.Dropdown(vs_list.value,
                                            interactive=True,
                                            show_label=False,
                                            value=vs_list.value[0] if len(vs_list.value) > 0 else None
                                            )
                    if len(vs_list.value) > 0:
                        switch_kb(vs_list.value[0])
                        gr.update(value=f"Swithed to knowledge base: {vs_list.value[0]} and you may start a chat.")

                    select_vs.change(fn=select_vs_on_change,
                                     inputs=[select_vs],
                                     outputs=[chatbot])
                
                vs_setting_upload = gr.Accordion("Upload Documents to Create Knowledge Base")
                with vs_setting_upload:
                    # vs_add = gr.Button(value="Load")
                    # vs_add.click(fn=add_vs_name,
                    #              inputs=[vs_name, vs_list, chatbot],
                    #              outputs=[select_vs, vs_list, chatbot])

                    file2vs = gr.Column(visible=True)
                    with file2vs:
                        # load_vs = gr.Button("加载知识库")
                        # gr.Markdown("Ingest documents to create a new knowledge base")
                        files = gr.File(file_types=['.docx', '.pdf', '.pptx', '.txt', '.md', '.html'],
                                        file_count="multiple"
                                        )
                        
                    vs_name = gr.Textbox(label="Please input a name for the new knowledge base",
                                         lines=1,
                                         interactive=True)
                    
                    load_file_button = gr.Button("Upload & Create Knowledge Base")
                    
                    load_file_button.click(fn=ingest_docs_to_vector_store,
                                           show_progress=True,
                                           inputs=[vs_name, files, vs_list, select_vs],
                                           outputs=[files, vs_list, select_vs, vs_name],
                                           )



demo.launch(
    server_name="0.0.0.0",
    server_port=8000
)