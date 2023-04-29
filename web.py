import gradio as gr
from chatbot import DocChatbot


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

init_message = """你好，我可以回答关于Surface Pro 9维护相关的信息."""

docChatbot = DocChatbot()

def get_answer(message, chat_history):
    result = "This is a test answer."
    ch = []
    for chat in chat_history:
        q = "" if chat[0] == None else chat[0]
        a = "" if chat[1] == None else chat[1]
        ch.append((q, a))

    result_answer, result_source = docChatbot.get_answer_with_source(message, ch)

    chat_history.append((message, result_answer))
    return "", chat_history

with gr.Blocks(css=block_css) as demo:
    gr.Markdown(webui_title)

    with gr.Tab("Chat"):
        with gr.Row():
            with gr.Column(scale=10):
                chatbot = gr.Chatbot([[None, init_message]],
                                     elem_id="chat-box",
                                     show_label=False).style(height=400)
                query = gr.Textbox(show_label=False,
                                   placeholder="Enter your question here",
                                   ).style(container=False)
                query.submit(
                    get_answer,
                    [query,chatbot],
                    [query,chatbot]
                )

demo.launch()