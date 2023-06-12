import os
import openai
from dotenv import load_dotenv
from langchain.chat_models import AzureChatOpenAI
from langchain.embeddings import OpenAIEmbeddings

from langchain.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain.chains.conversational_retrieval.base import BaseConversationalRetrievalChain
from langchain.prompts import PromptTemplate

from langchain.document_loaders import (UnstructuredPowerPointLoader, UnstructuredWordDocumentLoader, PyPDFLoader, UnstructuredFileLoader)
import langchain.text_splitter as text_splitter
from langchain.text_splitter import (RecursiveCharacterTextSplitter, CharacterTextSplitter)

from typing import List

class DocChatbot:
    llm: AzureChatOpenAI
    embeddings: OpenAIEmbeddings
    vector_db: FAISS
    chatchain: BaseConversationalRetrievalChain

    def __init__(self) -> None:
        #init for OpenAI GPT-4 and Embeddings
        load_dotenv()

        self.llm = AzureChatOpenAI(
            deployment_name=os.getenv("OPENAI_GPT_DEPLOYMENT_NAME"),
            temperature=0,
            openai_api_version="2023-05-15",
            openai_api_type="azure",
            openai_api_base=os.getenv("OPENAI_API_BASE"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            request_timeout=30
        )

        self.embeddings = OpenAIEmbeddings(
            deployment=os.getenv("OPENAI_EMBEDDING_DEPLOYMENT_NAME"), 
            chunk_size=1
            )
        
    def init_chatchain(self, chain_type : str = "stuff") -> None:
        # init for ConversationalRetrievalChain
        CONDENSE_QUESTION_PROMPT = PromptTemplate.from_template("""Given the following conversation and a follow up question, rephrase the follow up question. 
        The follow up question should be in the same language with the input. For example, if the input is in Chinese, the follow up question or the standalone question below should be in Chinese too.
            Chat History:
            {chat_history}

            Follow Up Input:
            {question}

            Standalone Question:"""
            )
                                                                    
        # stuff chain_type seems working better than others
        self.chatchain = ConversationalRetrievalChain.from_llm(llm=self.llm, 
                                                retriever=self.vector_db.as_retriever(),
                                                condense_question_prompt=CONDENSE_QUESTION_PROMPT,
                                                chain_type=chain_type,
                                                return_source_documents=True,
                                                verbose=True)
                                                # combine_docs_chain_kwargs=dict(return_map_steps=False))

    # get answer from query, return answer and source documents
    def get_answer_with_source(self, query, chat_history):
        result = self.chatchain({
                "question": query,
                "chat_history": chat_history
        },
        return_only_outputs=True)
        
        return result['answer'], result['source_documents']

    # load vector db from local
    def load_vector_db_from_local(self, path: str, index_name: str):
        self.vector_db = FAISS.load_local(path, self.embeddings, index_name)
        print(f"Loaded vector db from local: {path}/{index_name}")

    # save vector db to local
    def save_vector_db_to_local(self, path: str, index_name: str):
        FAISS.save_local(self.vector_db, path, index_name)
        print("Vector db saved to local")


    # split documents, generate embeddings and ingest to vector db
    def init_vector_db_from_documents(self, file_list: List[str]):
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)

        docs = []
        for file in file_list:
            print(f"Loading file: {file}")
            ext_name = os.path.splitext(file)[1]
            # print(ext_name)

            if ext_name == ".pptx":
                loader = UnstructuredPowerPointLoader(file)
            elif ext_name == ".docx":
                loader = UnstructuredWordDocumentLoader(file)
            elif ext_name == ".pdf":
                loader = PyPDFLoader(file)
            else:
                # process .txt, .html
                loader = UnstructuredFileLoader(file)

            doc = loader.load_and_split(text_splitter)            
            docs.extend(doc)
            print("Processed document: " + file)
    
        print("Generating embeddings and ingesting to vector db.")
        self.vector_db = FAISS.from_documents(docs, self.embeddings)
        print("Vector db initialized.")

        