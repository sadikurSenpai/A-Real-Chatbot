from fastapi import APIRouter
from psycopg_pool import ConnectionPool
from api.schemas.chat_schema import ChatSchema
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from api.schemas.chat_state import ChatState
from langgraph.checkpoint.postgres import PostgresSaver
from services.nodes.chat import chat
from sqlmodel import Field, Session, SQLModel, create_engine, select
import uuid
import sys
from dotenv import load_dotenv
load_dotenv()
import os

router = APIRouter()


DATABASE_URL = os.getenv("DATABASE_URL")
DB_URI = os.getenv("DB_URI")

class UserThread(SQLModel, table=True):
    __tablename__ = "user_threads"
    user_id: str = Field(primary_key=True)
    thread_id: str = Field(primary_key=True)
    created_at: str # Storing as ISO string or using datetime type is better, but string is robust for MVP

engine = create_engine(DATABASE_URL)

def init_db():
    SQLModel.metadata.create_all(engine)

init_db()

pool = ConnectionPool(conninfo=DB_URI, kwargs={"autocommit": True})
checkpointer = PostgresSaver(pool)
checkpointer.setup()

graph = StateGraph(ChatState)
graph.add_node('chat', chat)
graph.add_edge(START, 'chat')
graph.add_edge('chat', END)


@router.post('/chat', tags=['Chat'], response_model=dict)
def chat_endpoint(request: ChatSchema):
    thread_id = request.thread_id
    new_thread = False
    
    if not thread_id:
        thread_id = str(uuid.uuid4())
        new_thread = True

    if new_thread:
        try:
            with Session(engine) as session:
                from datetime import datetime
                thread_record = UserThread(
                    user_id=request.user_id, 
                    thread_id=thread_id,
                    created_at=datetime.now().isoformat()
                )
                session.add(thread_record)
                session.commit()
        except Exception as e:
            # If duplication or other error, log it. 
            print(f"Error saving thread mapping: {e}", file=sys.stderr)

    config = {
        'configurable': {
            'thread_id': thread_id
        }
    }
    
    workflow = graph.compile(checkpointer=checkpointer)
    user_message = HumanMessage(content=request.msg)
    
    result = workflow.invoke({
        'messages': [user_message]
    }, config=config)

    last_ai_message = next(
        msg for msg in reversed(result["messages"])
        if isinstance(msg, AIMessage)
    )

    return {
        'thread_id': thread_id,
        'msg': last_ai_message.content
    }

@router.get('/chat/history/{user_id}', tags=['Chat'])
def get_user_history(user_id: str):
    """
    Fetch all conversation threads for a specific user using SQLModel.
    """
    with Session(engine) as session:
        statement = select(UserThread).where(UserThread.user_id == user_id).order_by(UserThread.created_at.desc()) # type: ignore
        results = session.exec(statement).all()
        
        threads = []
        for row in results:
            threads.append({
                "thread_id": row.thread_id,
                "created_at": row.created_at
            })
    return {"threads": threads}

@router.get('/chat/thread/{thread_id}', tags=['Chat'])
def get_thread_messages(thread_id: str):
    """
    Fetch message history for a specific thread from LangGraph state.
    """
    config = {'configurable': {'thread_id': thread_id}}
    workflow = graph.compile(checkpointer=checkpointer)
    state = workflow.get_state(config)
    
    if not state.values:
        return {"messages": []}
    
    messages = state.values.get("messages", [])
    
    # Format messages for frontend
    formatted_messages = []
    for msg in messages:
        role = "user" if isinstance(msg, HumanMessage) else "assistant"
        formatted_messages.append({
            "role": role,
            "content": msg.content
        })
    return {"messages": formatted_messages}