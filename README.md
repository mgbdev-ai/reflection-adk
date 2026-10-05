# Reflection with Google ADK

A small, runnable project demonstrating the **reflection** design pattern with [Google Agent Development Kit (ADK)](https://google.github.io/adk-docs/).

The workflow treats the first model response as a draft—not the final answer:

```text
User request → Writer creates a draft → Critic reviews it → Refiner produces the final answer
```

This is the producer–critic form of reflection described in the [Agentic Design Patterns reflection chapter](https://adp.xindoo.xyz/original/Chapter%204_%20Reflection/). The critic has a different role and a structured output contract, making its feedback easier for the refiner to apply.

## What it demonstrates

- **State passing:** the writer saves `draft`; the critic saves `critique`; the refiner saves `final_answer`.
- **Specialised roles:** writing and reviewing are deliberately separate prompts.
- **Structured criticism:** Pydantic guarantees that the critic returns an approval decision, strengths, and actionable improvements.
- **Simple orchestration:** `SequentialAgent` makes the order explicit and easy to inspect.

It makes three model calls per request. This tends to improve quality on high-value writing or planning tasks, but costs more and takes longer than a single call.

## Prerequisites

- Python 3.10 or newer
- A [Gemini API key](https://aistudio.google.com/apikey)

## Run it

```bash
git clone https://github.com/mgbdev-ai/reflection-adk.git
cd reflection-adk
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
# Add your real GOOGLE_API_KEY to .env
adk run reflection_adk
```

Then try a request such as:

> Draft a short README for a Python CLI that resizes images. Include installation, one example, and a troubleshooting note.

ADK will run the writer, critic, and refiner in sequence. The final response is the refiner's output; the intermediate values remain available in session state for debugging in ADK's UI.

To inspect the workflow visually instead, run:

```bash
adk web
```

and open the URL shown in the terminal.

## How the code works

[`reflection_adk/agent.py`](reflection_adk/agent.py) defines three agents:

| Stage | State output | Responsibility |
| --- | --- | --- |
| `writer` | `draft` | Produces a useful first version. |
| `critic` | `critique` | Checks it against the request using a typed `Critique` schema. |
| `refiner` | `final_answer` | Rewrites it using the critique. |

`SequentialAgent` shares state across every stage, so `{draft}` and `{critique}` in downstream instructions are resolved from earlier outputs.

## Extending it into a loop

This sample intentionally runs one review cycle. For a production loop, add a maximum-iteration counter and rerun the writer/refiner only while `critique.approved` is false. Always set a hard cap: reflection can otherwise increase cost, latency, and prompt size without a guarantee of convergence.

Useful next steps include replacing the general critic with a domain reviewer (for example, a code reviewer), adding tool-based checks, and recording the critic's feedback for evaluation.

## Test

```bash
pip install pytest
pytest
```

The tests verify the agent graph and the critique contract without making model calls.

## License

MIT

