# Model Requirements for MCP Tool Calling

## Why model size matters

MCP tool calling requires multi-step reasoning: discover available tools, select the right one, construct valid JSON parameters, interpret the result, and optionally chain further calls. Models under ~30B parameters frequently fail at one or more of these steps, especially when the tool schema is large (ha-mcp exposes 15+ tools).

When a model fails to invoke a tool, it typically **hallucates a plausible response** rather than admitting it cannot access the data. This produces "synthetic" sensor readings, entity states, or automation confirmations that look real but are fabricated.

## Model tiers

### Tier 1 — Reliable (recommended)

These models handle ha-mcp tool calling consistently:

| Model | Type | Notes |
|-------|------|-------|
| Claude 4.5 Sonnet | Cloud API | Excellent multi-step tool chaining |
| GPT-4o | Cloud API | Reliable native function calling |
| Gemini 2.5 Flash | Cloud API | Fast, good tool support |
| Claude Opus 4 | Cloud API | Most capable, higher cost |
| Llama 3.3 70B | Local (40GB+ VRAM) | Best open-weight option for tool calling |

### Tier 2 — Usable with caveats

These models work but may need Default (prompt-based) mode or careful configuration:

| Model | Type | Caveats |
|-------|------|---------|
| Qwen 3 32B | Local (20GB+ VRAM at Q4) | Works in Native mode; occasional parameter errors |
| Mistral Large | Cloud API | Message ordering issues through some middleware |
| Llama 3.1 70B | Local | Older; occasionally hallucinates tool results in chained calls |
| Command R+ | Cloud API | Adequate for single-step tool calls |

### Tier 3 — Unreliable (not recommended)

These models frequently fail at MCP tool calling:

| Model | Type | Failure mode |
|-------|------|-------------|
| Ministral 3 8B | Local (10GB VRAM) | Message ordering bug with tool results via Ollama; hallucates instead of calling tools |
| Llama 3.1 8B | Local | Ignores tools or produces malformed JSON |
| Phi-3 / Phi-4 mini | Local | Inconsistent tool-call token generation |
| Gemma 3 9B | Local | System message conflicts after tool results |
| Any model < 14B | Local | Generally insufficient reasoning for multi-tool workflows |

## VRAM requirements for local models

| Model | Precision | Approximate VRAM |
|-------|-----------|-----------------|
| 8B models | Q4_K_M | 5-6 GB |
| 8B models | FP16 | 16 GB |
| 32B models | Q4_K_M | 18-20 GB |
| 32B models | Q8 | 34 GB |
| 70B models | Q4_K_M | 38-42 GB |
| 70B models | Q8 | 70+ GB |

## OpenWebUI function-calling modes

### Native mode

The model uses its own function-calling tokens (e.g., `<tool_call>`, `<|tool_use|>`). Requires:
- Model with trained function-calling capability
- Correct chat template in Ollama modelfile
- 30B+ parameters for reliability with ha-mcp's tool count

### Default (prompt-based) mode

OpenWebUI injects a system prompt that instructs the model to output tool requests in a structured format. OpenWebUI parses the output and executes the tool call.

- Works with any model, including those without native function calling
- More reliable for small models (8B-14B)
- Slower (extra prompt tokens) and less reliable for complex multi-step chains
- Configure in: Admin > Settings > Models > Advanced Params > Function Calling

## Known middleware issues

### Ollama OpenAI-compatible endpoint

Mistral and Ministral models fail with `"Unexpected role 'system' after role 'tool'"` when the conversation includes system messages after tool results. This is a message ordering issue in Ollama's OpenAI compatibility layer, not the model itself.

**Workaround:** Use Default mode, or access the model through Ollama's native API instead of the OpenAI-compatible endpoint.

### Multiple tool server configs

When OpenWebUI loads multiple tool servers from a config file, some models ignore all tools. Test with a single MCP server first to isolate this issue.
