# Financial Document Intelligent Agent

A **multi-agent financial intelligence system** that combines real-time stock data, financial news, PDF document Q&A, and mathematical calculations — all orchestrated through a LangGraph state machine with human-in-the-loop approval for high-risk actions.

![Tech Stack](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-7B2D8E)
![Groq](https://img.shields.io/badge/LLM-Groq%20LLaMA%203.3%2070B-F97316)
![FastAPI](https://img.shields.io/badge/API-FastAPI-009688?logo=fastapi)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B?logo=streamlit)
![FAISS](https://img.shields.io/badge/Vector%20DB-FAISS-37A779)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Table of Contents

- [Architecture](#architecture)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [Running the App](#running-the-app)
- [API Reference](#api-reference)
- [Project Structure](#project-structure)
- [How It Works](#how-it-works)
  - [Agent Orchestration](#agent-orchestration)
  - [Human-in-the-Loop](#human-in-the-loop)
  - [RAG Pipeline](#rag-pipeline)
- [Roadmap](#roadmap)

---

## Architecture

```
User Question
      │
      ▼
┌──────────────┐
│  Supervisor  │  ◄── Keyword matching + LLM routing
└──────┬───────┘
       │
       ├──────────────────────────────────────────────┐
       │                                              │
       ▼                                              ▼
┌─────────────┐  ┌──────────┐  ┌───────────┐  ┌───────────┐  ┌──────────────┐
│ Stock Agent │  │News Agent│  │Calculator │  │ RAG Agent │  │General Agent │
│  (yfinance) │  │ (Tavily) │  │  (Safe    │  │  (FAISS)  │  │  (Direct     │
│             │  │          │  │   Eval)   │  │           │  │   LLM)       │
└──────┬──────┘  └────┬─────┘  └─────┬─────┘  └─────┬─────┘  └──────┬───────┘
       │              │              │              │               │
       └──────────────┴──────────────┴──────────────┘               │
                              │                                     │
                              ▼                                     │
                  ┌──────────────────┐                              │
                  │ Human Approval   │  ◄── Interrupt on high-risk  │
                  │  (Buy/Sell/etc.) │       actions                │
                  └────────┬─────────┘                              │
                           │ (approved)                             │
                           ▼                                        │
                  ┌──────────────────┐                              │
                  │   Synthesizer    │  ◄── Polished final answer    │
                  └────────┬─────────┘                              │
                           │                                        │
                           └────────────┬───────────────────────────┘
                                        ▼
                              ┌─────────────────┐
                              │   Final Answer  │
                              └─────────────────┘
```

## Features

- **Multi-Agent Orchestration** — 6 specialized agents (Supervisor, Stock, News, Calculator, RAG, General) routed via a LangGraph state machine.
- **Real-Time Stock Data** — Look up stock prices for any US or Indian (`.NS`) symbol via `yfinance`.
- **Financial News Search** — Fetch top financial news articles via Tavily Search API.
- **PDF Document Q&A** — Upload financial PDFs and ask questions against them using a FAISS vector store with HuggingFace embeddings.
- **Math Calculations** — Evaluate arithmetic expressions safely.
- **Human-in-the-Loop** — High-risk actions (buy/sell/invest/transfer/withdraw/deposit/order) pause execution and require user approval before proceeding.
- **Streaming Responses** — Real-time token-by-token streaming via Server-Sent Events (SSE).
- **Dark-Mode UI** — Polished Streamlit interface with agent status badges, chat history, PDF upload, and approval panel.
- **LangSmith Monitoring** — Optional observability via LangSmith.

## Tech Stack

| Category | Technology |
|----------|------------|
| **Language** | Python 3.10+ |
| **Agent Framework** | [LangGraph](https://langchain-ai.github.io/langgraph/) |
| **LLM** | LLaMA 3.3 70B via [Groq](https://groq.com) |
| **Backend** | [FastAPI](https://fastapi.tiangolo.com) + Uvicorn |
| **Frontend** | [Streamlit](https://streamlit.io) |
| **Vector Store** | [FAISS](https://github.com/facebookresearch/faiss) (local) |
| **Embeddings** | `all-MiniLM-L6-v2` via HuggingFace (free, CPU) |
| **Stock Data** | [yfinance](https://github.com/ranaroussi/yfinance) |
| **News API** | [Tavily](https://tavily.com) |
| **Document Loader** | PyPDFLoader (LangChain) |
| **Monitoring** | LangSmith (optional) |
| **State Persistence** | LangGraph `MemorySaver` |

## Getting Started

### Prerequisites

- Python 3.10 or higher
- [Groq API key](https://console.groq.com) (free tier available)
- [Tavily API key](https://tavily.com) (free tier available)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/financial-document-intelligent-agent.git
cd financial-document-intelligent-agent

# Create and activate a virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```env
GROQ_API_KEY=gsk_your_groq_api_key
TAVILY_API_KEY=tvly_your_tavily_api_key

# Optional: LangSmith for monitoring
LANGSMITH_API_KEY=lsv2_your_langsmith_key
LANGSMITH_PROJECT=financial-agent
```

### Running the App

The app runs as two processes — a FastAPI backend and a Streamlit frontend.

```bash
# Terminal 1: Start the backend
uvicorn backend.main:app --reload --port 8000

# Terminal 2: Start the frontend
streamlit run frontend/app.py --server.port 8501
```

Navigate to **http://localhost:8501** to use the app.

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check — returns `{"status": "running"}` |
| `POST` | `/upload` | Upload a PDF for RAG ingestion |
| `POST` | `/ask` | Ask a question (synchronous, returns final answer) |
| `POST` | `/ask/stream` | Ask a question (SSE stream — agent info, tokens, interrupts) |
| `POST` | `/approve` | Approve or reject a paused human-in-the-loop action |

### Example: Ask a question

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the current price of Apple stock?"}'
```

## Project Structure

```
├── agents/                    # LangGraph agent orchestration
│   ├── graph.py               # StateGraph definition & routing
│   └── state.py               # AgentState TypedDict
├── backend/
│   └── main.py                # FastAPI server (4 endpoints)
├── faiss_db/                  # FAISS vector store on disk
│   ├── index.faiss
│   └── index.pkl
├── frontend/
│   └── app.py                 # Streamlit dark-mode UI
├── rag/
│   └── ingestion_retriever.py # RAG pipeline (load, chunk, embed, retrieve)
├── tools/
│   ├── calculator_tool.py     # Safe arithmetic evaluation
│   ├── news_tool.py           # Tavily financial news search
│   └── stock_tool.py          # yfinance stock price lookup
├── memory/                    # Memory module (placeholder)
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## How It Works

### Agent Orchestration

The core intelligence lives in `agents/graph.py`, which defines a **LangGraph StateGraph** with 7 nodes:

1. **Supervisor** — Classifies the user's intent using keyword matching (fast path) or LLM-based routing (fallback).
2. **Stock Agent** — Extracts a ticker symbol and calls `yfinance` to get the current price.
3. **News Agent** — Queries Tavily for the top 5 financial news articles.
4. **Calculator Agent** — Extracts a math expression and evaluates it safely.
5. **RAG Agent** — Queries the FAISS vector store for relevant document chunks.
6. **General Agent** — Answers general financial questions directly via the LLM.
7. **Synthesizer** — Takes the tool result and chat history, produces a polished final answer.

### Human-in-the-Loop

When the Supervisor detects high-risk keywords (`buy`, `sell`, `invest`, `transfer`, `withdraw`, `deposit`, `order`), the graph pauses via LangGraph's `Interrupt`. The user sees an approval prompt in the Streamlit UI and can **Approve** or **Reject** before any action is taken.

### RAG Pipeline

```
PDF Upload → PyPDFLoader → RecursiveCharacterTextSplitter
    (200-char chunks, 20 overlap)
    → all-MiniLM-L6-v2 Embeddings → FAISS Index
    → Top-3 Retriever → Formatted Answer
```

Uploaded PDFs are chunked, embedded, and stored in a local FAISS index. The RAG agent retrieves the top 3 most relevant chunks for each query and passes them to the LLM for synthesis.

## Roadmap

- [ ] Web search integration for broader financial queries
- [ ] Multi-LLM support (OpenAI, Anthropic, Ollama)
- [ ] Persistent chat history database (SQLite/PostgreSQL)
- [ ] Portfolio tracking and visualization
- [ ] Docker deployment with docker-compose
- [ ] Unit and integration tests
- [ ] CI/CD pipeline

---

Built with LangGraph, Groq, FastAPI, and Streamlit.
