from api.schemas.chat_state import ChatState
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
load_dotenv()

def chat(state: ChatState):
    model = ChatOpenAI(model='gpt-4o-mini')

    messages = state['messages']

    result = model.invoke(messages)

    return {
        'messages': [result]
    }