from api.schemas.chat_state import ChatState
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode
from services.tools.tools import calculator, internet_search_tool, get_stock_price
from dotenv import load_dotenv
load_dotenv()

def chat(state: ChatState):
    model = ChatOpenAI(model='gpt-4o-mini')
    tools = [calculator, internet_search_tool, get_stock_price]
    model_with_tools = model.bind_tools(tools)

    messages = state['messages']

    result = model_with_tools.invoke(messages)

    return {
        'messages': [result]
    }

tool_node = ToolNode(tools=[calculator, internet_search_tool, get_stock_price], name='tools')