import os
import openai
from dotenv import load_dotenv
from langchain.chat_models import AzureChatOpenAI
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.callbacks.base import BaseCallbackHandler


from langchain.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain.chains.conversational_retrieval.base import BaseConversationalRetrievalChain
from langchain.prompts import PromptTemplate

from langchain.document_loaders import (UnstructuredPowerPointLoader, UnstructuredWordDocumentLoader, PyPDFLoader, UnstructuredFileLoader, CSVLoader, MWDumpLoader)
import langchain.text_splitter as text_splitter
from langchain.text_splitter import (RecursiveCharacterTextSplitter, CharacterTextSplitter)

from typing import List
import streamlit
import glob

REQUEST_TIMEOUT_DEFAULT = 10
TEMPERATURE_DEFAULT = 0.0
CHAT_MODEL_NAME_DEFAULT = "gpt-3.5-turbo"
OPENAI_EMBEDDING_DEPLOYMENT_NAME_DEFAULT = "text-embedding-ada-002"
CHUNK_SIZE_DEFAULT = 1000
CHUNK_OVERLAP_DEFAULT = 0

class StreamHandler(BaseCallbackHandler):
    def __init__(self, container, initial_text=""):
        self.container = container
        self.text = initial_text

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        self.text += token
        self.container.markdown(self.text)


class DocChatbot:
    llm: ChatOpenAI
    condense_question_llm: ChatOpenAI
    embeddings: OpenAIEmbeddings
    vector_db: FAISS
    chatchain: BaseConversationalRetrievalChain

    # configuration for API calls
    request_timeout: int
    temperature: float
    chat_model_name : str
    api_key : str

    def init_llm_openai(self, streaming: bool, condense_question_container = None, answer_container = None) -> None:
        # init for LLM using openai.com api

        self.llm = ChatOpenAI(
                temperature=self.temperature,
                openai_api_key=self.api_key,
                request_timeout=self.request_timeout,
                model=self.chat_model_name,  # Model name is needed for openai.com only
                streaming=streaming,
                callbacks=[StreamHandler(answer_container)] if streaming else []
            ) # type: ignore

        if streaming:
            self.condense_question_llm = ChatOpenAI(
                temperature=self.temperature,
                openai_api_key=self.api_key,
                request_timeout=self.request_timeout,
                streaming=True,
                model=self.chat_model_name,
                callbacks=[StreamHandler(condense_question_container, "🤔...")]
            ) # type: ignore
        else:
            self.condense_question_llm = self.llm

    def init_llm_azure(self, streaming: bool, condense_question_container = None, answer_container = None) -> None:
        # init for LLM using Azure OpenAI Service
        
        assert(os.getenv("OPENAI_GPT_DEPLOYMENT_NAME") is not None)
        assert(os.getenv("OPENAI_API_BASE") is not None)
        assert(os.getenv("OPENAI_EMBEDDING_DEPLOYMENT_NAME") is not None)
        assert(len(self.api_key) == 32)

        self.llm = AzureChatOpenAI(
            deployment_name=os.getenv("OPENAI_GPT_DEPLOYMENT_NAME"),
            temperature=self.temperature,
            openai_api_version="2023-05-15",
            openai_api_type="azure",
            openai_api_base=os.getenv("OPENAI_API_BASE"),
            openai_api_key=self.api_key,
            request_timeout=self.request_timeout,
            streaming=streaming,
            callbacks=[StreamHandler(answer_container)] if streaming else []
        ) # type: ignore

        if streaming:
            self.condense_question_llm = AzureChatOpenAI(
                deployment_name=os.getenv("OPENAI_GPT_DEPLOYMENT_NAME"),
                temperature=self.temperature,
                openai_api_version="2023-05-15",
                openai_api_type="azure",
                openai_api_base=os.getenv("OPENAI_API_BASE"),
                openai_api_key=os.getenv("OPENAI_API_KEY"),
                request_timeout=self.request_timeout,
                model=self.chat_model_name,
                streaming=True,
                callbacks=[StreamHandler(condense_question_container, "🤔...")]
            ) # type: ignore
        else:
            self.condense_question_llm = self.llm

    def __init__(self) -> None:
        #init for LLM and Embeddings, without support for streaming

        #load environment variables
        load_dotenv()
        assert(os.getenv("OPENAI_API_KEY") is not None)
        self.api_key = str(os.getenv("OPENAI_API_KEY"))
        self.request_timeout = REQUEST_TIMEOUT_DEFAULT if os.getenv("REQUEST_TIMEOUT") is None else int(os.getenv("REQUEST_TIMEOUT"))
        self.temperature = TEMPERATURE_DEFAULT if os.getenv("TEMPERATURE") is None else float(os.getenv("TEMPERATURE"))
        self.chat_model_name = CHAT_MODEL_NAME_DEFAULT if os.getenv("CHAT_MODEL_NAME") is None else str(os.getenv("CHAT_MODEL_NAME"))

        #check if user is using API from openai.com or Azure OpenAI Service by inspecting the api key
        if self.api_key.startswith("sk-"):
            # user is using API from openai.com
            assert(len(self.api_key) == 51)
            self.init_llm_openai(False)
        else:
            # user is using Azure OpenAI Service
            self.init_llm_azure(False)

        embedding_deployment = OPENAI_EMBEDDING_DEPLOYMENT_NAME_DEFAULT if os.getenv("OPENAI_EMBEDDING_DEPLOYMENT_NAME") is None else str(os.getenv("OPENAI_EMBEDDING_DEPLOYMENT_NAME"))
        self.embeddings = OpenAIEmbeddings(
            deployment=embedding_deployment,
            chunk_size=1
            ) # type: ignore

    def init_streaming(self, condense_question_container, answer_container) -> None:
        #init for LLM and Embeddings, with support for streaming

        if self.api_key.startswith("sk-"):
            # user is using API from openai.com
            self.init_llm_openai(True, condense_question_container, answer_container)
        else:
            # user is using Azure OpenAI Service
            self.init_llm_azure(True, condense_question_container, answer_container)

    # def init_streaming(self, condense_question_container, answer_container) -> None:
    #     #init for LLM and Embeddings, with support for streaming

    #     api_key = str(os.getenv("OPENAI_API_KEY"))
    #     temperature=float(os.getenv("TEMPERATURE"))
    #     request_timeout=int(os.getenv("REQUEST_TIMEOUT"))
    #     model_name=str(os.getenv("CHAT_MODEL_NAME"))
    #     if api_key.startswith("sk-"):
    #         # user is using API from openai.com
    #         self.llm = ChatOpenAI(
    #             temperature=temperature,
    #             openai_api_key=api_key,
    #             request_timeout=request_timeout,
    #             streaming=True,
    #             model=model_name,
    #             callbacks=[StreamHandler(answer_container)]
    #         ) # type: ignore

    #         self.condense_question_llm = ChatOpenAI(
    #             temperature=temperature,
    #             openai_api_key=api_key,
    #             request_timeout=request_timeout,
    #             streaming=True,
    #             model=model_name,
    #             callbacks=[StreamHandler(condense_question_container, "🤔...")]
    #         ) # type: ignore
    #     else:
    #         # user is using Azure OpenAI Service
    #         self.llm = AzureChatOpenAI(
    #             deployment_name=os.getenv("OPENAI_GPT_DEPLOYMENT_NAME"),
    #             temperature=temperature,
    #             openai_api_version="2023-05-15",
    #             openai_api_type="azure",
    #             openai_api_base=os.getenv("OPENAI_API_BASE"),
    #             openai_api_key=os.getenv("OPENAI_API_KEY"),
    #             request_timeout=request_timeout,
    #             model=model_name,
    #             streaming=True,
    #             callbacks=[StreamHandler(answer_container)]
    #         ) # type: ignore

    #         self.condense_question_llm = AzureChatOpenAI(
    #             deployment_name=os.getenv("OPENAI_GPT_DEPLOYMENT_NAME"),
    #             temperature=temperature,
    #             openai_api_version="2023-05-15",
    #             openai_api_type="azure",
    #             openai_api_base=os.getenv("OPENAI_API_BASE"),
    #             openai_api_key=os.getenv("OPENAI_API_KEY"),
    #             request_timeout=request_timeout,
    #             model=model_name,
    #             streaming=True,
    #             callbacks=[StreamHandler(condense_question_container, "🤔...")]
    #         ) # type: ignore
        
    def init_chatchain(self, chain_type : str = "stuff") -> None:
        # init for ConversationalRetrievalChain
        CONDENSE_QUESTION_PROMPT = PromptTemplate.from_template("""Given the following conversation and a follow up input, rephrase the standalone question. 
        The standanlone question to be generated should be in the same language with the input. 
        For example, if the input is in Chinese, the follow up question or the standalone question below should be in Chinese too.
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
                                                condense_question_llm=self.condense_question_llm,
                                                chain_type=chain_type,
                                                return_source_documents=True,
                                                verbose=False)
                                                # combine_docs_chain_kwargs=dict(return_map_steps=False))

    # get answer from query, return answer and source documents
    def get_answer_with_source(self, query, chat_history):
        result = self.chatchain({
                "question": query,
                "chat_history": chat_history
        },
        return_only_outputs=True)
        
        return result['answer'], result['source_documents']

    # get answer from query. 
    # This function is for streamlit app and the chat history is in a format aligned with openai api
    def get_answer(self, query, chat_history):
        ''' 
        Here's the format for chat history:
        [{"role": "assistant", "content": "How can I help you?"}, {"role": "user", "content": "What is your name?"}]
        The input for the Chain is in a format like this:
        [("How can I help you?", "What is your name?")]
        That is, it's a list of question and answer pairs.
        So need to transform the chat history to the format for the Chain
        '''  
        chat_history_for_chain = []

        for i in range(0, len(chat_history), 2):
            chat_history_for_chain.append((
                chat_history[i]['content'], 
                chat_history[i+1]['content'] if chat_history[i+1] is not None else ""
                ))

        result = self.chatchain({
                "question": query,
                "chat_history": chat_history_for_chain
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
        chunk_size = CHUNK_SIZE_DEFAULT if os.getenv("CHUNK_SIZE") is None else int(os.getenv("CHUNK_SIZE"))
        chunk_overlap = CHUNK_OVERLAP_DEFAULT if os.getenv("CHUNK_OVERLAP") is None else int(os.getenv("CHUNK_OVERLAP"))
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

        docs = []
        for file in file_list:
            print(f"Loading file: {file}")
            ext_name = os.path.splitext(file)[-1]
            # print(ext_name)

            if ext_name == ".pptx":
                loader = UnstructuredPowerPointLoader(file)
            elif ext_name == ".docx":
                loader = UnstructuredWordDocumentLoader(file)
            elif ext_name == ".pdf":
                loader = PyPDFLoader(file)
            elif ext_name == ".csv":
                loader = CSVLoader(file_path=file)
            elif ext_name == ".xml":
                loader = MWDumpLoader(file_path=file, encoding="utf8")
            else:
                # process .txt, .html
                loader = UnstructuredFileLoader(file)

            doc = loader.load_and_split(text_splitter)            
            docs.extend(doc)
            print("Processed document: " + file)
    
        print("Generating embeddings and ingesting to vector db.")
        self.vector_db = FAISS.from_documents(docs, self.embeddings)
        print("Vector db initialized.")

    # Get indexes available
    def get_available_indexes(self, path: str):
        return [os.path.splitext(os.path.basename(file))[0] for file in glob.glob(f"{path}/*.faiss")]
        