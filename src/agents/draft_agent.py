import os
import re
import json
import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def draft_email(research: dict, sender_name: str, sender_role: str, service_offered: str, style_instruction: str = "", contact: dict = None) -> dict:
    """
    Research agent çıktısını alıp kişiselleştirilmiş outreach email taslağı üretir.
    Returns: {subject, body, personalization_used}
    """
    system_prompt = """You are an expert B2B cold outreach copywriter. You write emails that:
- Sound human, not like a template
- Lead with something specific about the company (not generic flattery)
- Are concise: 4-6 sentences max
- Have one clear call to action (a question, not "book a call")
- Never use buzzwords: "synergy", "leverage", "game-changer", "revolutionary"
- Never open with "I hope this email finds you well"

Respond ONLY with valid JSON, no extra text."""

    style_section = f"\nSTYLE INSTRUCTION:\n{style_instruction}\n" if style_instruction else ""

    contact_section = ""
    if contact:
        name = f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip()
        contact_section = f"\nRECIPIENT:\n- Name: {name}\n- Position: {contact.get('position', '')}\n- Department: {contact.get('department', '')}\n"

    user_message = f"""Write a cold outreach email using this research data:{style_section}{contact_section}

COMPANY RESEARCH:
{json.dumps(research, indent=2, ensure_ascii=False)}

SENDER INFO:
- Name: {sender_name}
- Role: {sender_role}
- Service/offer: {service_offered}

Return ONLY this JSON:
{{
  "subject": "...",
  "body": "...",
  "personalization_used": "one sentence explaining which hook you used and why"
}}"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}]
    )

    text = response.content[0].text.strip()

    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return json.loads(match.group())

    raise ValueError(f"JSON parse edilemedi. Claude cevabı:\n{text}")


if __name__ == "__main__":
    print("ProspectPilot — Draft Agent\n")

    sample_research = {
        "company": "Notion",
        "summary": "Notion Labs is a $10B productivity platform that just crossed $500M ARR with its AI Agents launch, serving 100M+ users.",
        "recent_news": [
            "Launched Notion AI Agents (Notion 3.0) in September 2025, crossing $500M ARR",
            "Shipped 30+ product updates in H1 2025 including Claude 4 integration"
        ],
        "tech_stack": ["React", "TypeScript", "PostgreSQL", "AWS", "Claude 4"],
        "pain_points": [
            "Performance degradation in large enterprise workspaces",
            "Granular permissions and enterprise governance gaps",
            "Steep learning curve causing inconsistent adoption"
        ],
        "personalization_hooks": [
            "Crossing $500M ARR means their GTM team is scaling fast and needs processes that keep pace",
            "Notion AI Agents launch repositions them as autonomous workflow platform — integrations matter more than ever",
            "Their 'connected workspace' vision means they actively want to reduce tool sprawl"
        ]
    }

    result = draft_email(
        research=sample_research,
        sender_name="Alex",
        sender_role="AI Automation Consultant",
        service_offered="Building AI-powered outreach and lead generation systems for B2B SaaS teams"
    )

    print(f"SUBJECT: {result['subject']}\n")
    print(f"BODY:\n{result['body']}\n")
    print(f"PERSONALIZATION: {result['personalization_used']}")
