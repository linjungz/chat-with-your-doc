from chatbot import DocChatbot
import typer
from typing_extensions import Annotated

import glob



VECTORDB_PATH = "./data/vector_store"
app = typer.Typer()
docChatbot = DocChatbot()

@app.command()
def ingest(
        doc_path : Annotated[str, typer.Argument(help="Path to the documents to be ingested, support glob pattern", show_default=False)],
        index_name : Annotated[str, typer.Argument(help="Name of the index to be created")]):
    #support for glob in doc_path
    file_list = glob.glob(doc_path)
    # print(file_list)
    
    docChatbot.init_vector_db_from_documents(file_list)
    docChatbot.save_vector_db_to_local(VECTORDB_PATH, index_name)

@app.command()
def chat(index_name : str = "index"):
    
    docChatbot.load_vector_db_from_local(VECTORDB_PATH, index_name)
    docChatbot.init_chatchain()

    chat_history = []

    while True:
        query = input("Question：")
        if query == "exit":
            break
        if query == "reset":
            chat_history = []
            continue

        result_answer, result_source = docChatbot.get_answer_with_source(query, chat_history)
        print(f"Q: {query}\nA: {result_answer}")
        print("Source Documents:")
        for doc in result_source:
            print(doc.metadata)
            # print(doc.page_content)

        # print(chat_history)
        chat_history.append((query, result_answer))
        # print(chat_history)

if __name__ == "__main__":
    app()