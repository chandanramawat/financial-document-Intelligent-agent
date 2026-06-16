from langchain_tavily import TavilySearch
from langchain_core.tools import tool
from dotenv import load_dotenv

load_dotenv()

tavily = TavilySearch(max_results=5)

@tool
def get_financial_news(query: str) -> str:
    """
    Get latest financial news for a company or topic.
    Use when user asks about news, updates, or market events.
    Args:
        query: Company name or financial topic
    """
    try:
        results = tavily.invoke(query)
        
        print(f"[News Tool] Result type: {type(results)}")
        print(f"[News Tool] Result: {str(results)[:200]}")

        # ✅ String result
        if isinstance(results, str):
            return results

        # ✅ List result
        elif isinstance(results, list):
            news = ""
            for i, r in enumerate(results, 1):
                if isinstance(r, dict):
                    news += f"News {i}:\n"
                    news += f"URL    : {r.get('url', 'N/A')}\n"
                    news += f"Content: {r.get('content', 'N/A')[:300]}\n\n"
                else:
                    news += f"News {i}: {str(r)[:300]}\n\n"
            return news if news else "No news found"

        # ✅ Dict result
        elif isinstance(results, dict):
            return str(results.get("content", str(results)))[:500]

        else:
            return str(results)[:500]

    except Exception as e:
        return f"Error fetching news: {e}"
