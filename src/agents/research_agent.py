import os
import re
import json
import anthropic
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


def web_search(query: str, max_results: int = 5) -> str:
    """Tavily ile web araması yapar, sonuçları string olarak döner."""
    results = tavily_client.search(query=query, max_results=max_results)
    output = []
    for r in results.get("results", []):
        output.append(f"Title: {r['title']}\nURL: {r['url']}\nContent: {r['content']}\n")
    return "\n---\n".join(output)


tools = [
    {
        "name": "web_search",
        "description": "Search the web for information about a company or person. Use this to find recent news, company details, LinkedIn profiles, product information, and any publicly available data.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query string"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Number of results to return (default: 5)",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    }
]


def process_tool_call(tool_name: str, tool_input: dict) -> str:
    if tool_name == "web_search":
        return web_search(tool_input["query"], tool_input.get("max_results", 5))
    raise ValueError(f"Unknown tool: {tool_name}")


def research_company(company_name: str, company_domain: str = "") -> dict:
    """
    Bir şirket hakkında araştırma yapar.
    Returns: {company, domain, summary, recent_news, tech_stack, pain_points, personalization_hooks}
    """
    domain_hint = f" (domain: {company_domain})" if company_domain else ""
    system_prompt = """You are a B2B sales research assistant. Your job is to research companies
and extract key information that will help craft personalized outreach emails.
Always respond with valid JSON in the exact format requested."""

    user_message = f"""Research the company "{company_name}"{domain_hint} and provide:
1. The company's official web domain (e.g. "notion.so", "stripe.com") — just the domain, no "https://" or "www"
2. A brief company summary (2-3 sentences)
3. Recent news or developments (last 6 months)
4. Their likely tech stack or tools they use
5. Potential pain points or challenges they might face
6. 2-3 personalization hooks for an outreach email

Use the web_search tool multiple times to gather comprehensive information.
After research, respond with ONLY this JSON (no markdown, no extra text):
{{
  "company": "{company_name}",
  "domain": "...",
  "summary": "...",
  "recent_news": ["...", "..."],
  "tech_stack": ["...", "..."],
  "pain_points": ["...", "..."],
  "personalization_hooks": ["...", "..."]
}}"""

    messages = [{"role": "user", "content": user_message}]

    # Agentic loop — Claude tool kullanmayı bitirene kadar döner
    while True:
        response = anthropic_client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=system_prompt,
            tools=tools,
            messages=messages
        )

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"  [tool] {block.name}({block.input.get('query', '')})")
                    result = process_tool_call(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })

            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})

        elif response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    text = block.text.strip()
                    # Markdown code fence varsa temizle
                    if "```" in text:
                        text = text.split("```")[1]
                        if text.startswith("json"):
                            text = text[4:]
                        text = text.strip()
                    # Metin içindeki JSON objesini bul (önünde açıklama olabilir)
                    match = re.search(r'\{.*\}', text, re.DOTALL)
                    if match:
                        return json.loads(match.group())
            raise ValueError("No text block in final response")

        else:
            raise ValueError(f"Unexpected stop_reason: {response.stop_reason}")


if __name__ == "__main__":
    print("ProspectPilot — Research Agent\n")
    company = input("Şirket adı gir: ").strip()
    domain = input("Domain (opsiyonel, Enter ile geç): ").strip()

    print(f"\n'{company}' araştırılıyor...\n")
    result = research_company(company, domain)

    print(json.dumps(result, indent=2, ensure_ascii=False))
