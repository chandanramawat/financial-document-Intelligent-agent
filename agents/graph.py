# agents/graph.py
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Interrupt     
from agents.state import AgentState
from tools.stock_tool import get_stock_price
from tools.news_tool import get_financial_news
from tools.calculator_tool import calculate
from rag.ingestion import search_documents
from dotenv import load_dotenv

load_dotenv()

# Initialize LLM
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

# Memory
memory = MemorySaver()

# ============================================
# NODE 1 — Supervisor
# ============================================
def supervisor_node(state: AgentState) -> AgentState:
    question = state["question"].lower()
    print(f"\n[Supervisor] Question: {state['question']}")

    # Routing logic
    if any(word in question for word in ["stock", "price", "share", "market cap", "pe ratio"]):
        agent = "stock"
    elif any(word in question for word in ["news", "latest", "update", "recent", "today"]):
        agent = "news"
    elif any(word in question for word in ["calculate", "compute", "%", "percent", "profit", "loss", "ratio"]):
        agent = "calculator"
    elif any(word in question for word in ["document", "invoice", "report", "pdf", "file", "uploaded"]):
        agent = "rag"
    else:
        # LLM decide kare
        messages = [
            SystemMessage(content=(
                "You are a router. Given a financial question, "
                "respond with ONLY one word:\n"
                "- 'stock' for stock price questions\n"
                "- 'news' for news questions\n"
                "- 'calculator' for math questions\n"
                "- 'rag' for document questions\n"
                "- 'general' for general questions"
            )),
            HumanMessage(content=state["question"])
        ]
        response = llm.invoke(messages)
        agent = response.content.strip().lower()
        if agent not in ["stock", "news", "calculator", "rag", "general"]:
            agent = "general"

    print(f"[Supervisor] → {agent} agent")
    return {**state, "agent_used": agent}

# ============================================
# NODE 2 — Stock Agent
# ============================================
def stock_agent_node(state: AgentState) -> AgentState:
    print(f"\n[Stock Agent] Processing...")

    # Extract symbol
    messages = [
        SystemMessage(content=(
            "Extract stock ticker symbol from question. "
            "Return ONLY the symbol. "
            "Indian stocks need .NS suffix: TCS→TCS.NS, RELIANCE→RELIANCE.NS\n"
            "Examples: Apple→AAPL, Tesla→TSLA, TCS→TCS.NS"
        )),
        HumanMessage(content=state["question"])
    ]
    symbol = llm.invoke(messages).content.strip()
    print(f"[Stock Agent] Symbol: {symbol}")

    result = get_stock_price.invoke({"symbol": symbol})
    print(f"[Stock Agent] Result: {str(result)[:100]}")

    return {**state, "stock_result": result}

# ============================================
# NODE 3 — News Agent
# ============================================
def news_agent_node(state: AgentState) -> AgentState:
    print(f"\n[News Agent] Processing...")

    try:
        results = get_financial_news.invoke({"query": state["question"]})

        # ✅ Fix — string ya list dono handle karo
        if isinstance(results, str):
            news_result = results
        elif isinstance(results, list):
            news_result = "\n".join([
                f"News {i+1}:\n{r['content'][:300]}"
                if isinstance(r, dict)
                else str(r)
                for i, r in enumerate(results)
            ])
        else:
            news_result = str(results)

        print(f"[News Agent] Done!")

    except Exception as e:
        news_result = f"News error: {e}"
        print(f"[News Agent] Error: {e}")

    return {**state, "news_result": news_result}
# ============================================
# NODE 4 — RAG Agent
# ============================================
def rag_agent_node(state: AgentState) -> AgentState:
    print(f"\n[RAG Agent] Searching documents...")

    result = search_documents(state["question"])
    print(f"[RAG Agent] Result: {str(result)[:100]}")

    return {**state, "rag_result": result}

# ============================================
# NODE 5 — Calculator Agent
# ============================================
def calculator_agent_node(state: AgentState) -> AgentState:
    print(f"\n[Calculator Agent] Processing...")

    # Extract expression
    messages = [
        SystemMessage(content=(
            "Extract ONLY the math expression from question. "
            "Return ONLY the expression like: 500*0.15, (100-50)/50*100\n"
            "No words, just the math expression."
        )),
        HumanMessage(content=state["question"])
    ]
    expression = llm.invoke(messages).content.strip()
    print(f"[Calculator Agent] Expression: {expression}")

    result = calculate.invoke({"expression": expression})
    print(f"[Calculator Agent] Result: {result}")

    return {**state, "calculator_result": result}

# ============================================
# NODE 6 — General Agent
# ============================================
def general_agent_node(state: AgentState) -> AgentState:
    print(f"\n[General Agent] Processing...")

    chat_history = state.get("chat_history", [])
    messages = [
        SystemMessage(content="You are a helpful financial assistant.")
    ]

    for msg in chat_history[-4:]:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=state["question"]))
    response = llm.invoke(messages)

    return {**state, "final_answer": response.content}

# ============================================
# NODE 7 — Synthesizer
# ============================================
def synthesizer_node(state: AgentState) -> AgentState:
    print(f"\n[Synthesizer] Creating final answer...")

    agent_used = state.get("agent_used", "general")

    # Get relevant result
    if agent_used == "stock":
        context = state.get("stock_result", "")
    elif agent_used == "news":
        context = state.get("news_result", "")
    elif agent_used == "rag":
        context = state.get("rag_result", "")
    elif agent_used == "calculator":
        context = state.get("calculator_result", "")
    else:
        return state

    chat_history = state.get("chat_history", [])

    messages = [
        SystemMessage(content=(
            "You are a helpful financial assistant. "
            "Use the provided data to give a detailed answer."
        ))
    ]

    # Add chat history
    for msg in chat_history[-4:]:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=(
        f"Question: {state['question']}\n\n"
        f"Data:\n{context}"
    )))

    response = llm.invoke(messages)
    print(f"[Synthesizer] Done!")

    return {**state, "final_answer": response.content}


# NODE 8 Human approval node
# ✅ Pehle yeh node nahi tha — naya add kiya
def human_approval_node(state: AgentState) -> AgentState:
    print(f"\n[Human Approval] Checking...")

    question  = state["question"].lower()
    high_risk = any(word in question for word in [
        "buy", "sell", "invest", "purchase",
        "transfer", "withdraw", "deposit", "order"
    ])

    print(f"[Human Approval] High risk: {high_risk}")

    if high_risk:
        print(f"[Human Approval] Interrupting for approval...")
        
        # ✅ interrupt call karo
        decision = Interrupt(
            f"⚠️ High risk action detected!\n"
            f"Question: {state['question']}\n"
            f"Do you want to proceed? (approve/reject)"
        )

        print(f"[Human Approval] Decision received: {decision}")

        if decision == "approve":
            return {
                **state,
                "human_approved"   : True,
                "requires_approval": True,
                "approval_message" : "✅ Action approved!"
            }
        else:
            return {
                **state,
                "human_approved"   : False,
                "requires_approval": True,
                "final_answer"     : "❌ Action cancelled by user.",
                "approval_message" : "❌ Action rejected!"
            }

    return {
        **state,
        "human_approved"   : True,
        "requires_approval": False,
        "approval_message" : ""
    }
# ============================================
# ROUTING FUNCTION
# ============================================
def route_after_supervisor(state: AgentState) -> str:
    agent = state.get("agent_used", "general")
    routes = {
        "stock"      : "stock_agent",
        "news"       : "news_agent",
        "rag"        : "rag_agent",
        "calculator" : "calculator_agent",
        "general"    : "general_agent",
    }
    return routes.get(agent, "general_agent")

def route_after_agent(state: AgentState) -> str:
    agent = state.get("agent_used", "general")
    if agent == "general":
        return END
    return "synthesizer"

def route_after_approval(state: AgentState) -> str:
    if state.get("human_approved", True):
        return "synthesizer"    # ✅ Approved → continue
    return END                  # ❌ Rejected → stop

# ============================================
# BUILD GRAPH
# ============================================
def build_graph():
    graph = StateGraph(AgentState)

    # Nodes
    graph.add_node("supervisor",       supervisor_node)
    graph.add_node("stock_agent",      stock_agent_node)
    graph.add_node("news_agent",       news_agent_node)
    graph.add_node("rag_agent",        rag_agent_node)
    graph.add_node("calculator_agent", calculator_agent_node)
    graph.add_node("general_agent",    general_agent_node)
    graph.add_node("human_approval",   human_approval_node)  # ✅ Naya node
    graph.add_node("synthesizer",      synthesizer_node)

    graph.set_entry_point("supervisor")

    # Supervisor → Agents (same as before)
    graph.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {
            "stock_agent"     : "stock_agent",
            "news_agent"      : "news_agent",
            "rag_agent"       : "rag_agent",
            "calculator_agent": "calculator_agent",
            "general_agent"   : "general_agent",
        }
    )

    # ✅ Change — Agents → Human Approval (pehle directly synthesizer jaate the)
    for agent in ["stock_agent", "news_agent", "rag_agent", "calculator_agent"]:
        graph.add_edge(agent, "human_approval")     # ✅ Naya edge

    # ✅ Change — Human Approval → Synthesizer ya END
    graph.add_conditional_edges(
        "human_approval",
        route_after_approval,                       # ✅ Naya routing
        {
            "synthesizer": "synthesizer",
            END          : END
        }
    )

    graph.add_edge("general_agent", END)
    graph.add_edge("synthesizer",   END)

    return graph.compile(checkpointer=memory)
# ✅ Yeh last line honi chahiye
finance_graph = build_graph()
print("✅ LangGraph Finance Agent with HITL ready!")
