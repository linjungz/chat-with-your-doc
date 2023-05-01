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

init_message = """你好，我可以根据已有的知识库回答相关问题."""

VS_ROOT_PATH = "./data/vector_store"
docChatbot = DocChatbot()

def log(msg: str):
    status.value = msg

def get_vs_list():
    if not os.path.exists(VS_ROOT_PATH):
        return []
    
    file_list = os.listdir(VS_ROOT_PATH)
    faiss_file_list = [file.split(".")[0] for file in file_list if fnmatch.fnmatch(file, "*.faiss")]
    index_list = list(set(faiss_file_list))
    # print(index_list)

    return index_list

vs_list = get_vs_list()

def select_vs_on_change(vs_id):
    switch_kb(vs_id)
    return f"Swithced to knowledge base: {vs_id}", ""

def switch_kb(index: str):
    docChatbot.load_vector_db_from_local(VS_ROOT_PATH, index)
    docChatbot.init_chatchain()


def get_vector_store(vs_id, files, history):
    vs_path = VS_ROOT_PATH + vs_id
    filelist = []
    for file in files:
        filename = os.path.split(file.name)[-1]
        shutil.move(file.name, UPLOAD_ROOT_PATH + filename)
        filelist.append(UPLOAD_ROOT_PATH + filename)
    if local_doc_qa.llm and local_doc_qa.embeddings:
        vs_path, loaded_files = local_doc_qa.init_knowledge_vector_store(filelist, vs_path)
        if len(loaded_files):
            file_status = f"已上传 {'、'.join([os.path.split(i)[-1] for i in loaded_files])} 至知识库，并已加载知识库，请开始提问"
        else:
            file_status = "文件未成功加载，请重新上传文件"
    else:
        file_status = "模型未完成加载，请先在加载模型后再导入文件"
        vs_path = None
    print(file_status)
    return vs_path, None, history + [[None, file_status]]

def add_vs_name(vs_name, vs_list, chatbot):
    if vs_name in vs_list:
        vs_status = "与已有知识库名称冲突，请重新选择其他名称后提交"
        chatbot = chatbot + [[None, vs_status]]
        return gr.update(visible=True), vs_list, chatbot
    else:
        vs_status = f"""已新增知识库"{vs_name}",将在上传文件并载入成功后进行存储。请在开始对话前，先完成文件上传。 """
        chatbot = chatbot + [[None, vs_status]]
        return gr.update(visible=True, choices=vs_list + [vs_name], value=vs_name), vs_list + [vs_name], chatbot

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

with gr.Blocks(css=block_css) as demo:
    vs_list = gr.State(vs_list)
    vs_path = gr.State("")
    gr.Markdown(webui_title)

    with gr.Tab("Chat"):
        with gr.Row():
            status = gr.TextArea(show_label=False, lines=1, interactive=False)
            log("Please select a knowledge base to start a chat")

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
                vs_setting = gr.Accordion("Configure Knowledge Base")
                with vs_setting:
                    select_vs = gr.Dropdown(vs_list.value,
                                            label="Select Knowledge Base",
                                            interactive=True,
                                            value=vs_list.value[0] if len(vs_list.value) > 0 else None
                                            )

                    select_vs.change(fn=select_vs_on_change,
                                     inputs=[select_vs],
                                     outputs=[status, chatbot])
                    
                    
                                            
                    # vs_name = gr.Textbox(label="请输入新建知识库名称",
                    #                      lines=1,
                    #                      interactive=True)
                    # vs_add = gr.Button(value="Load")
                    # vs_add.click(fn=add_vs_name,
                    #              inputs=[vs_name, vs_list, chatbot],
                    #              outputs=[select_vs, vs_list, chatbot])

                    # file2vs = gr.Column(visible=True)
                    # with file2vs:
                    #     # load_vs = gr.Button("加载知识库")
                    #     gr.Markdown("向知识库中添加文件")
                    #     with gr.Tab("上传文件"):
                    #         files = gr.File(label="添加文件",
                    #                         file_types=['.txt', '.md', '.docx', '.pdf'],
                    #                         file_count="multiple",
                    #                         show_label=False
                    #                         )
                    #         load_file_button = gr.Button("上传文件并加载知识库")
                    #     with gr.Tab("上传文件夹"):
                    #         folder_files = gr.File(label="添加文件",
                    #                                # file_types=['.txt', '.md', '.docx', '.pdf'],
                    #                                file_count="directory",
                    #                                show_label=False
                    #                                )
                    #         load_folder_button = gr.Button("上传文件夹并加载知识库")
                    # load_vs.click(fn=)
                    
                    # 将上传的文件保存到content文件夹下,并更新下拉框
                    # load_file_button.click(get_vector_store,
                    #                        show_progress=True,
                    #                        inputs=[select_vs, files, chatbot],
                    #                        outputs=[vs_path, files, chatbot],
                    #                        )
                    # load_folder_button.click(get_vector_store,
                    #                          show_progress=True,
                    #                          inputs=[select_vs, folder_files, chatbot],
                    #                          outputs=[vs_path, folder_files, chatbot],
                    #                          )

    


demo.launch()