from chatbot import DocChatbot
import typer
from typing_extensions import Annotated
import os
from dotenv import load_dotenv

import glob

app = typer.Typer()
docChatbot = DocChatbot()
load_dotenv()
VECTORDB_PATH = os.getenv("VECTORDB_PATH")

if VECTORDB_PATH is None:
    typer.echo(typer.style("VECTORDB_PATH environment variable not found and default path ./data/vector_store will be used.", fg=typer.colors.RED))
    VECTORDB_PATH = "./data/vector_store"

@app.command()
def ingest(
        path : Annotated[str, typer.Option(help="Path to the documents to be ingested, support glob pattern", show_default=False)],
        name : Annotated[str, typer.Option(help="Name of the index to be created", show_default=False)]):
    """
    Ingests documents into a vector database.

    Args:
        path: The path to the documents to be ingested (supports glob patterns).
        name: The name of the index to be created.
    """
    #support for glob in doc_path
    file_list = glob.glob(path)
    # print(file_list)
    
    docChatbot.init_vector_db_from_documents(file_list)
    docChatbot.save_vector_db_to_local(VECTORDB_PATH, name)

@app.command()
def chat(name : str = "index"):
    """
    Initiates a chat interface allowing users to query the vector database.

    Args:
        name: The name of the index to be used (default is "index").
    """
    
    docChatbot.load_vector_db_from_local(VECTORDB_PATH, name)
    docChatbot.init_chatchain()

    chat_history = []

    while True:
        question_prompt = typer.style("Question：", fg=typer.colors.GREEN)  # Style the prompt
        query = input(question_prompt)  # Use the styled prompt
        if query == "exit":
            break
        if query == "reset":
            chat_history = []
            continue

        result_answer, result_source = docChatbot.get_answer_with_source(query, chat_history)

        # Style the answer in yellow
        styled_answer = typer.style(f"A: {result_answer}", fg=typer.colors.YELLOW)

        print(f"Q: {query}\n{styled_answer}")  # Print the styled answer
        print("Source Documents:")
        for doc in result_source:
            print(doc.metadata)
            # print(doc.page_content)

        # print(chat_history)
        chat_history.append((query, result_answer))
        # print(chat_history)

if __name__ == "__main__":
    app()