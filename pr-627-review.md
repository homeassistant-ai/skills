# Review: PR #627 — Tool Search Proxy for Context Reduction (Phase 1)

## What the PR Does

This PR replaces direct MCP registration of 10 tools (from 5 modules: zones, labels, addons, voice_assistant, traces) with 3 meta-tools:

| Meta-Tool | Purpose |
|---|---|
| `ha_find_tools(query)` | Search proxied tools by name, category, or keyword |
| `ha_get_tool_details(tool_name)` | Return full schema and a `schema_hash` |
| `ha_execute_tool(tool_name, args, tool_schema)` | Validate hash, then execute |

The goal is to reduce idle context consumption. Today, 94+ tools occupy ~35,500 tokens — 17.8 % of Claude's window and 27.8 % of GPT-4o's. The problem is real and well-quantified.

## MCP Compliance

The 3 meta-tools are valid MCP tools: they register normally, appear in `tools/list`, and are invoked via `tools/call`. At the wire-protocol level, nothing is broken. But the approach works against the protocol's design intent in four ways.

### 1. Tools vanish from `tools/list`

MCP designates `tools/list` as *the* discovery mechanism. Once proxied, the 10 underlying tools become invisible to every standard MCP host — Claude Desktop, Cursor, Copilot, or any other client that relies on `tools/list`. Those clients would need to know the custom find-then-details-then-execute workflow to reach the hidden tools.

### 2. Typed invocation is replaced by string dispatch

Each MCP tool normally carries its own `inputSchema` (JSON Schema), letting both client and LLM know exactly what parameters are expected. The proxy collapses this into:

```
ha_execute_tool(
  tool_name="ha_create_zone",
  args='{"name":"Home","latitude":40.7}',
  tool_schema="a1b2c3d4"
)
```

`args` is an opaque JSON string. Neither the MCP client nor protocol-level validation can verify its structure before the call reaches the server.

### 3. Tool annotations are hidden

MCP annotations (`readOnlyHint`, `destructiveHint`, `idempotentHint`) let *clients* enforce safety policies — for example, requiring user confirmation for destructive operations. The proxy tracks these internally (exposing `is_destructive` in search results), but MCP clients cannot see them. `ha_execute_tool` carries no annotation reflecting the danger level of whatever it dispatches.

### 4. It rebuilds protocol-level features at the application layer

The PR constructs a bespoke discovery-and-invocation protocol on top of MCP. The spec already provides:

- **Pagination** on `tools/list` for large tool sets.
- **`notifications/tools/list_changed`** for dynamic tool sets.
- **[SEP-1821](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1821)** — an active draft proposal that adds a `query` parameter to `tools/list`, which is functionally identical to `ha_find_tools`.

## Other Technical Concerns

**Schema-hash gate offers false confidence.** The hash proves the LLM called `ha_get_tool_details`, not that it understood the schema. An LLM can retrieve the hash and immediately call `ha_execute_tool` with wrong arguments. The 8-hex-character (32-bit) hash is also small enough to hallucinate.

**`_MockMCP` is fragile.** It mimics the SDK's `@mcp.tool()` decorator to intercept registrations. Any change to the SDK's decorator API will break the mock silently.

**Extra round-trips.** A single operation now requires 2–3 LLM turns (find, get details, execute), trading context tokens for latency and added reasoning burden.

**Breaking change in practice.** The PR states "zero breaking changes," but any MCP client that was calling `ha_create_zone` directly will find it gone from `tools/list`. That is a breaking change.

## What's Done Well

- **Problem identification** — clearly motivated, well-quantified.
- **Test coverage** — 30+ unit tests, E2E tests, and a transparent `_ProxyAwareClient` wrapper so existing tests keep working.
- **Registry design** — `ToolProxyRegistry` with search, catalog, and validation is cleanly structured.
- **Phased rollout** — starting with 5 low-traffic modules is pragmatic.
- **No changes to existing tool implementations** — a sound architectural constraint.

## MCP-Aligned Alternatives

1. **Dynamic registration via `listChanged`.** Register a base set, then add or remove tools as the conversation narrows. Every tool stays first-class with proper schemas and annotations.
2. **Adopt SEP-1821.** Contribute to or implement the draft `query` parameter on `tools/list` — the same filtering this PR wants, but at the protocol level where all clients benefit.
3. **Multiple MCP servers.** Split by domain (zones, labels, etc.). Clients already support multiple server connections.
4. **Rich annotations.** Tag every tool with categories so clients can filter and prioritize on their side.
5. **Connection-time negotiation.** Use a configuration tool or init-phase handshake so the client declares which domains it needs; register only those.

## Summary

| Dimension | Assessment |
|---|---|
| Problem identification | Strong — real and well-quantified |
| Wire-level MCP compliance | Compliant — meta-tools are valid |
| Design-intent MCP alignment | Misaligned — hides tools, strips annotations, replaces typed invocation |
| Code quality | Good — clean registry, thorough tests |
| Architectural direction | Concerning — parallel discovery protocol diverges from SEP-1821 |
| Breaking changes | Yes — 10 tools disappear from `tools/list` |
| Security model | Weak — schema hash provides false confidence |

**Bottom line:** Well-engineered code solving a real problem at the wrong layer. It builds a custom tool-discovery protocol on top of MCP instead of leveraging MCP's own mechanisms. The approach will cause compatibility issues with standard MCP clients and diverges from the direction the spec is heading. The project would be better served by adopting or contributing to protocol-level solutions for tool-set scaling.
