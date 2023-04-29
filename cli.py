from chatbot import DocChatbot

def chat():
    docChatbot = DocChatbot()
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
    chat()