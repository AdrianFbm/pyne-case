# Feature Roadmap

Potential additions to AIoli, each showcasing a distinct AI engineering skill.

## Priority 1 — High signal, low effort

### Observability / Tracing

There is currently zero visibility into LLM calls. Integrating a tracing library (e.g. [Langfuse](https://langfuse.com), OpenTelemetry) would log every call with latency, token count, cost, prompt content, and response. This is table-stakes for production AI systems.

**Where it fits:** wraps `_call_llm` in `agent.py` with a decorator or context manager.

### Native Function/Tool Calling

JSON is currently parsed from free text with a regex fallback to strip markdown fences (`agent.py` lines 88–97). Both Anthropic and OpenAI have native structured output / tool-calling APIs that guarantee valid JSON conforming to a schema. The existing `LLMResponse` Pydantic model maps directly to a tool schema.

**Where it fits:** replace the raw chat completion calls in `_call_llm` with tool-use / structured output API calls.

## Priority 2 — Portfolio differentiators

### LLM-as-Judge Evaluation

The eval suite checks DataFrame values, which is smart for deterministic validation. But it can't assess answer quality ("is this explanation clear and accurate?"). A second LLM call that grades the narrative response on a rubric (accuracy, clarity, completeness) is a widely-used eval pattern.

**Where it fits:** new test file or extension of `eval/test_queries.py` that scores `result.answer` via a grading prompt.

### Semantic Caching

Identical or near-identical questions hit the LLM every time. Embedding each question (e.g. with OpenAI's embedding API or a local model), storing results in a FAISS index, and returning cached answers for semantically similar queries demonstrates embeddings, similarity search, and cost optimization.

**Where it fits:** a caching layer in `ask()` that checks similarity before calling `_call_llm`.

### Dynamic Few-Shot Example Selection

The system prompt has static examples. A more sophisticated approach: maintain a bank of (question, SQL, answer) triples, embed them, and at query time retrieve the 2–3 most similar to include in the prompt. Lightweight RAG that directly improves SQL generation accuracy.

**Where it fits:** extends `LLMClient.__init__` to build an example index, and `_call_llm` to inject retrieved examples into the messages.

## Priority 3 — Nice to have

### Streaming Responses

The UI blocks while waiting for the full LLM response (loading dots). Server-sent events or WebSocket streaming would show tokens as they arrive. Dash supports this via `dcc.Interval` polling or background callbacks.

### Guardrails / Input Validation

Beyond SQL keyword blocking: prompt injection detection, output validation (does the generated SQL reference tables that actually exist?), content-level filtering.

### User Feedback Loop

Thumbs up/down buttons on each assistant response, stored alongside the question/SQL/answer. Foundation for prompt iteration, fine-tuning data collection, or RLHF-style improvement.

## Not recommended

- **RAG with external documents** — the schema is small and self-contained; a vector DB for "business context" would feel forced.
- **Fine-tuning** — dataset too small, use case doesn't warrant it.
- **Multi-agent orchestration** — the two-call pattern is appropriate for the complexity; a planner/executor/critic chain would be over-engineering.
