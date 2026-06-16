# backend/main.py
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from agents.graph import finance_graph
from rag.ingestion import process_pdf, list_documents
from langgraph.types import Command
from langgraph.errors import GraphInterrupt
import tempfile
import json
import asyncio

app = FastAPI(title="Financial Document Intelligence Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# LLM for streaming
llm_streaming = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0,
    streaming=True,
)

print("✅ Financial Document Intelligence Agent ready!")
print("✅ LangSmith monitoring enabled!")
print("✅ Streaming enabled!")
print("✅ HITL enabled!")

# ============================================
# Models
# ============================================
class ChatRequest(BaseModel):
    message    : str
    chat_history: list = []
    session_id : str = "default"

class ChatResponse(BaseModel):
    response  : str
    agent_used: str = "none"

class UploadResponse(BaseModel):
    message  : str
    documents: list = []

class HITLRequest(BaseModel):
    session_id: str
    decision  : str  # "approve" ya "reject"

# ============================================
# Health Check
# ============================================
@app.get("/")
def health_check():
    return {"status": "running", "app": "Financial Document Intelligence Agent"}

# ============================================
# Upload PDF
# ============================================
@app.post("/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    try:
        print(f"[Upload] Receiving: {file.filename}")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        result = process_pdf(tmp_path, file.filename)
        os.unlink(tmp_path)
        docs = list_documents()

        return UploadResponse(message=result, documents=docs)

    except Exception as e:
        return UploadResponse(message=f"Error: {e}", documents=[])

# ============================================
# List Documents
# ============================================
@app.get("/documents")
def get_documents():
    return {"documents": list_documents()}

# ============================================
# Ask Endpoint (Normal)
# ============================================
@app.post("/ask", response_model=ChatResponse)
def ask(request: ChatRequest):
    try:
        print(f"\n📩 Question: {request.message}")
        config = {"configurable": {"thread_id": request.session_id}}

        result = finance_graph.invoke({
            "question"          : request.message,
            "chat_history"      : request.chat_history,
            "stock_result"      : "",
            "news_result"       : "",
            "rag_result"        : "",
            "calculator_result" : "",
            "final_answer"      : "",
            "agent_used"        : "",
            "human_approved"    : False,
            "requires_approval" : False,
            "approval_message"  : ""
        }, config=config)

        print(f"✅ Agent : {result['agent_used']}")
        return ChatResponse(
            response   = result["final_answer"],
            agent_used = result["agent_used"]
        )

    except Exception as e:
        print(f"❌ Error: {e}")
        return ChatResponse(response=f"Error: {str(e)}", agent_used="none")

# ============================================
# Streaming Endpoint
# ============================================
@app.post("/ask/stream")
async def ask_stream(request: ChatRequest):

    async def generate():
        try:
            print(f"\n📩 Streaming: {request.message}")
            config = {"configurable": {"thread_id": request.session_id}}

            # ✅ GraphInterrupt catch karo
            try:
                result = finance_graph.invoke({
                    "question"          : request.message,
                    "chat_history"      : request.chat_history,
                    "stock_result"      : "",
                    "news_result"       : "",
                    "rag_result"        : "",
                    "calculator_result" : "",
                    "final_answer"      : "",
                    "agent_used"        : "",
                    "human_approved"    : False,
                    "requires_approval" : False,
                    "approval_message"  : ""
                }, config=config)

            except GraphInterrupt as e:
                print(f"[HITL] ✅ Interrupt caught!")

                # Message extract karo
                interrupt_value = "⚠️ High risk action detected! Please approve or reject."
                if e.args:
                    args = e.args[0]
                    if isinstance(args, list) and len(args) > 0:
                        first = args[0]
                        if hasattr(first, 'value'):
                            interrupt_value = str(first.value)
                        else:
                            interrupt_value = str(first)
                    else:
                        interrupt_value = str(args)

                print(f"[HITL] Message: {interrupt_value}")

                # ✅ Frontend ko interrupt signal bhejo
                yield f"data: {json.dumps({'type': 'interrupt', 'message': interrupt_value})}\n\n"
                return

            # ✅ Normal flow
            agent_used   = result.get("agent_used", "general")
            tool_context = ""

            if agent_used == "stock":
                tool_context = result.get("stock_result", "")
            elif agent_used == "news":
                tool_context = result.get("news_result", "")
            elif agent_used == "rag":
                tool_context = result.get("rag_result", "")
            elif agent_used == "calculator":
                tool_context = result.get("calculator_result", "")

            # Agent info bhejo
            yield f"data: {json.dumps({'type': 'agent', 'agent': agent_used})}\n\n"

            # Messages banao
            messages = [
                SystemMessage(content="You are a helpful financial assistant.")
            ]

            for msg in request.chat_history[-4:]:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))

            if tool_context:
                messages.append(HumanMessage(content=(
                    f"Question: {request.message}\n\nData:\n{tool_context}"
                )))
            else:
                messages.append(HumanMessage(content=request.message))

            # ✅ Stream tokens
            async for chunk in llm_streaming.astream(messages):
                if chunk.content:
                    yield f"data: {json.dumps({'type': 'token', 'content': chunk.content})}\n\n"
                    await asyncio.sleep(0.02)

            # Done signal
            yield f"data: {json.dumps({'type': 'done', 'agent': agent_used})}\n\n"

        except Exception as e:
            print(f"❌ Stream Error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control"    : "no-cache",
            "X-Accel-Buffering": "no"
        }
    )

# ============================================
# HITL Approve/Reject Endpoint
# ============================================
@app.post("/approve", response_model=ChatResponse)
async def approve_action(request: HITLRequest):
    try:
        config = {"configurable": {"thread_id": request.session_id}}
        print(f"\n[HITL] Decision: {request.decision}")

        # ✅ Graph resume karo with decision
        result = finance_graph.invoke(
            Command(resume=request.decision),
            config=config
        )

        print(f"✅ HITL Done! Answer: {str(result.get('final_answer', ''))[:100]}")

        return ChatResponse(
            response   = result.get("final_answer", "Action completed"),
            agent_used = result.get("agent_used", "none")
        )

    except Exception as e:
        print(f"❌ HITL Error: {e}")
        return ChatResponse(
            response   = f"Error: {str(e)}",
            agent_used = "none"
        )