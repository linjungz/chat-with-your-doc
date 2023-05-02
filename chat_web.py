import gradio as gr
from chatbot import DocChatbot
import shutil
import os
import fnmatch

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
    return f"Swithed to knowledge base: {vs_id} and you may start a chat.",  [[None, init_message]]

def switch_kb(index: str):
    docChatbot.load_vector_db_from_local(VS_ROOT_PATH, index)
    docChatbot.init_chatchain()

def ingest_docs_to_vector_store(vs_name, files, vs_list, select_vs):
    # print(vs_name)
    # print(files)

    # Check if vs_name already exists
    if vs_name in vs_list:
        return f"ERROR: Failed to create knowledge base.", gr.update(visible=True), vs_list, select_vs, gr.update(value="", placeholder=f"Index name {vs_name} already exits.")

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
    return f"Knowledge Base {vs_name} created and you may start a chat.", None, vs_list + [vs_name], gr.update(choices=vs_list+[vs_name], value=vs_name), gr.update(value="", placeholder="")

def get_answer(message, chat_history):
    # result = "This is a test answer."
    ch = []
    for chat in chat_history:
        q = "" if chat[0] == None else chat[0]
        a = "" if chat[1] == None else chat[1]
        ch.append((q, a))

    result_answer, result_source = docChatbot.get_answer_with_source(message, ch)

    chat_history.append((message, result_answer))
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
            status = gr.TextArea(show_label=False, 
                                 lines=1, 
                                 interactive=False,
                                 value="Please select a knowledge base to start a chat")
            

        with gr.Row():
            with gr.Column(scale=10):
                chatbot = gr.Chatbot([[None, init_message]],
                                     elem_id="chat-box",
                                     show_label=False).style(height=400)
                query = gr.Textbox(show_label=False,
                                   placeholder="Input your question here and press Enter to get answer.",
                                   ).style(container=False)
                query.submit(
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
                                     outputs=[status, chatbot])
                
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
                    
                    #将上传的文件保存到content文件夹下,并更新下拉框
                    load_file_button.click(fn=ingest_docs_to_vector_store,
                                           show_progress=True,
                                           inputs=[vs_name, files, vs_list, select_vs],
                                           outputs=[status, files, vs_list, select_vs, vs_name],
                                           )



demo.launch()