import json
import os

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from agent.analyzer import HealthReport
from agent.config import settings


class ProposedChange(BaseModel):
    """Structured output we require from the LLM."""
    file_path: str = Field(description="Path of the file to create or modify, relative to repo root")
    new_content: str = Field(description="The new content to add. For docs/section additions, this should be ONLY the new section/snippet being added (not the whole file). For brand-new files, this is the complete file content.")
    commit_message: str = Field(description="Conventional-commit style message, e.g. 'docs: add usage section to README'")
    pr_title: str = Field(description="Short PR title")
    pr_description: str = Field(description="Markdown PR description explaining what was analyzed and why this change was chosen")
    change_type: str = Field(description="One of: docs, tests, style, chore")
    apply_mode: str = Field(description="One of: 'append' (add new_content to the end of the existing file) or 'overwrite' (replace the whole file - only for new files or full rewrites)")

SYSTEM_PROMPT = """You are an AI repository maintenance agent. You will be given a
health report describing gaps found in a real GitHub repository. Your job is to
pick exactly ONE gap to fix in this run - the one that is highest value and
LOWEST RISK to fix automatically without human review of the code logic.

Strongly prefer documentation-only changes (README sections, docstrings) over
anything that changes runtime behavior. Never invent facts about the project;
if you don't have enough information to write a specific section, write a
clear, honest placeholder that a human can fill in (e.g. an "## Installation"
section with generic, standard steps for the language you can detect).

Respond with ONLY valid JSON matching this schema, no markdown fences, no
extra commentary:
{format_instructions}
Keep your proposed change SMALL and TARGETED. If the gap is a missing README
section, output ONLY that new section's content (a few lines to a paragraph) -
never rewrite the entire file. If unsure how content will be merged, assume it
will be appended, not used to replace the whole file.
"""


def _build_chain():
    llm = ChatGroq(
        api_key=settings.groq_api_key,
        model=settings.groq_model,
        temperature=0.2,
        max_tokens=4096,
    )
    structured_llm = llm.with_structured_output(ProposedChange)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("human", "Health report (JSON):\n{health_report}\n\nRelevant file snippets:\n{snippets}"),
        ]
    )
    return prompt | structured_llm


def _gather_snippets(report: HealthReport, max_files: int = 3) -> str:
    """Pull a little bit of real file content for context, so the model
    isn't hallucinating in a vacuum. Kept small to save tokens."""
    snippets = []
    seen = set()
    for gap in sorted(report.gaps, key=lambda g: g.priority, reverse=True):
        if gap.file_path in seen or len(seen) >= max_files:
            continue
        full_path = os.path.join(report.repo_path, gap.file_path)
        if os.path.exists(full_path) and os.path.isfile(full_path):
            with open(full_path, "r", encoding="utf-8", errors="ignore") as fh:
                content = fh.read()[:1500]  # cap per file
            snippets.append(f"--- {gap.file_path} ---\n{content}")
            seen.add(gap.file_path)
    return "\n\n".join(snippets) if snippets else "(no existing file content available)"


def propose_change(report: HealthReport) -> ProposedChange:
    """
    Main entry point: send the health report to Groq and get back one
    concrete, structured change proposal.
    """
    if not report.gaps:
        raise ValueError("Health report has no gaps - nothing to propose.")

    chain = _build_chain()
    result = chain.invoke(
        {
            "health_report": json.dumps(report.to_dict(), indent=2),
            "snippets": _gather_snippets(report),
            "format_instructions": ProposedChange.model_json_schema(),
        }
    )
    return result
