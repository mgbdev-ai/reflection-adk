---
title: "Build a Reflection Agent with Google ADK"
description: "A small producer–critic–refiner project that improves AI output before it reaches the user."
tags: [google-adk, gemini, ai-agents, reflection, python]
---

# Build a Reflection Agent with Google ADK

Most AI applications use a single model call: a user asks a question and the model immediately returns an answer. That is fast, but the first answer is not always the clearest, most complete, or most accurate one.

The **Reflection** pattern adds a quality-control step. One agent creates a draft, another agent reviews it, and a final agent applies the feedback. This post walks through a compact implementation using the Google Agent Development Kit (ADK).

## The idea

Our workflow has three roles:

```text
User request → Writer → Critic → Refiner → Final answer
```

The writer focuses on producing a useful first version. The critic focuses only on finding important problems. The refiner uses both pieces of information to create the final response.

Separating these roles matters. A model that has just written an answer can be biased toward defending it. Giving the review step its own prompt and explicit criteria makes the feedback more focused.

## Project setup

Install the dependencies and add a Gemini API key:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
```

Add your `GOOGLE_API_KEY` to `.env`, then start the agent:

```bash
adk run reflection_adk
```

The project uses `gemini-2.5-flash` by default. You can choose another model by setting `GEMINI_MODEL` in the environment.

## Define a contract for feedback

The critic should not produce unstructured prose that the refiner has to interpret. We define a Pydantic model so that its output always has the same shape:

```python
class Critique(BaseModel):
    approved: bool
    strengths: list[str]
    improvements: list[str]
```

For example, the critic may return:

```json
{
  "approved": false,
  "strengths": ["The introduction is concise"],
  "improvements": [
    "Include a concrete installation example",
    "Explain how the API key is configured"
  ]
}
```

This small contract is valuable because it makes downstream behavior easier to understand, test, and evolve.

## Create the writer

The first ADK agent receives the user's request and saves its response in shared workflow state under the key `draft`.

```python
writer = Agent(
    name="writer",
    model=MODEL,
    instruction="""
You are a concise technical writer. Create a first draft that directly answers
the user's request. Avoid inventing facts and make the draft useful to a developer.
""",
    output_key="draft",
)
```

`output_key` is the handoff mechanism. Later agents can refer to the writer's result as `{draft}` in their instructions.

## Add a critic

The critic sees the draft but has a different job: evaluate it against the user request and propose concrete improvements.

```python
critic = Agent(
    name="critic",
    model=MODEL,
    instruction="""
You are an exacting editor. Review the draft below against the original user
request. Identify material issues such as missed requirements, unsupported claims,
unclear wording, poor structure, or unnecessary content.

Draft to review:
{draft}
""",
    output_schema=Critique,
    output_key="critique",
)
```

ADK resolves `{draft}` using workflow state. The `output_schema` makes the critic follow the `Critique` contract, and `output_key` stores its result as `critique`.

## Refine the answer

The final agent receives both the original draft and the critique. Its only job is to produce the polished answer.

```python
refiner = Agent(
    name="refiner",
    model=MODEL,
    instruction="""
You are the final editor. Rewrite the draft to satisfy the original user request.
Apply every relevant improvement in the critique. Return only the finished answer.

Draft:
{draft}

Critique:
{critique}
""",
    output_key="final_answer",
)
```

We explicitly tell the refiner not to expose internal workflow details. Users should receive a strong answer—not the draft, the critique, or a description of how the agents collaborated.

## Orchestrate the workflow

`SequentialAgent` executes the agents in order and shares state between them:

```python
root_agent = SequentialAgent(
    name="reflection_pipeline",
    sub_agents=[writer, critic, refiner],
)
```

At runtime, the state evolves like this:

| Stage | New state | Purpose |
| --- | --- | --- |
| Writer | `draft` | A useful first answer |
| Critic | `critique` | Structured quality feedback |
| Refiner | `final_answer` | The improved response |

## When to use reflection

Reflection is most useful when quality matters more than the lowest possible latency and cost. Good examples include technical documentation, code explanations, implementation plans, long-form content, and responses with many requirements.

It is less suitable for a fast chat response, a simple classification task, or any situation where three model calls are not worth the added delay.

## Take it further

This project intentionally runs one review cycle. A production system can add a loop:

1. Write a draft.
2. Review it.
3. Refine it only if the critic does not approve it.
4. Stop after a fixed maximum number of attempts.

Always use a maximum iteration count. More reflection can improve an answer, but it also increases token usage, latency, and the chance of repeatedly rewriting already-good work.

Other useful extensions are a domain-specific critic, tool-based fact checks, automated tests for code outputs, and evaluation datasets built from real user requests.

## Final thought

Reflection is not about making an agent appear thoughtful. It is a practical workflow for treating an initial model response as a draft and deliberately checking it before delivery. With ADK state passing and `SequentialAgent`, the pattern remains small, transparent, and easy to adapt.

The complete implementation is in [`reflection_adk/agent.py`](reflection_adk/agent.py).
