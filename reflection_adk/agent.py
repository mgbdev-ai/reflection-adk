"""A small producer -> critic -> refiner workflow built with Google ADK.

Run from the repository root:
    adk run reflection_adk
"""

import os

from google.adk.agents import Agent, SequentialAgent
from pydantic import BaseModel, Field


MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


class Critique(BaseModel):
    """The contract between the critic and the refiner."""

    approved: bool = Field(description="Whether the draft already meets every requirement.")
    strengths: list[str] = Field(description="Specific things the draft does well.")
    improvements: list[str] = Field(
        description="Concrete changes needed before the draft is publishable."
    )


writer = Agent(
    name="writer",
    model=MODEL,
    description="Writes a first draft in response to the user's request.",
    instruction="""
You are a concise technical writer. Create a first draft that directly answers the
user's request. Use clear headings when useful, avoid inventing facts, and make
the draft useful to a developer. This is a draft: do not mention this workflow
or ask the user questions unless the request is genuinely ambiguous.
""",
    output_key="draft",
)


critic = Agent(
    name="critic",
    model=MODEL,
    description="Checks the draft against the user's request and returns actionable feedback.",
    instruction="""
You are an exacting editor. Review the draft below against the original user
request and identify only material issues: missed requirements, unsupported
claims, unclear wording, poor structure, or unnecessary content.

Draft to review:
{draft}

Return the Critique schema. A useful critique is specific enough that another
writer can apply it without guessing.
""",
    output_schema=Critique,
    output_key="critique",
)


refiner = Agent(
    name="refiner",
    model=MODEL,
    description="Produces the final answer by applying the critic's feedback to the draft.",
    instruction="""
You are the final editor. Rewrite the draft to satisfy the original user request.
Apply every relevant improvement in the critique, preserving good material.
Return only the finished answer—no preamble, review notes, or references to
agents, drafts, or the reflection process.

Draft:
{draft}

Critique:
{critique}
""",
    output_key="final_answer",
)


# ADK runs these agents in order and shares session state between them.
root_agent = SequentialAgent(
    name="reflection_pipeline",
    description="A transparent writer, critic, and refiner reflection workflow.",
    sub_agents=[writer, critic, refiner],
)

