# Using GPT-6.1 Sol
## Capabilities, prompting, workflow design, and migration

**Documentation reviewed:** 13 October 2026 (UTC)  
**Scope:** GPT-6.1 Sol in the OpenAI application programming interface (API), ChatGPT Work, and Codex.  
**Evidence:** Official OpenAI documentation. Recommendations and illustrative calculations are identified as such.

## Executive findings

GPT-6.1 Sol is the documented `gpt-6.1-sol` model, positioned for complex coding, computer use, and professional work at a lower cost than GPT-6 Astra. “Near-Astra” describes OpenAI’s positioning; the model-selection guidance still recommends comparing the models on the actual task. [S004]

The important compatibility changes are concrete: GPT-6.1 supports `low`, `medium`, `high`, `xhigh`, and `max` reasoning, with `medium` as the API default. It does not support `none` or `minimal`. Tool calling requires the Responses API; Chat Completions remains available for requests without tools. [S002]

Much of the GPT-5.6 material remains useful. The current guide deliberately retains the earlier generation’s feature guidance, including programmatic tool calling, multi-agent orchestration, caching, persisted reasoning, compaction, and pro mode. Its behavioral prompting advice, however, largely describes Astra and is presented as a starting point to evaluate across the family. [S001]

For effective use, separate five decisions: the model, reasoning effort, output detail, execution mode, and processing speed. Then evaluate the complete result, including evidence, artifact quality, elapsed time, and cost. This is a recommended interpretation of the documented controls, rather than a claim that one setting is universally optimal. [S008] [S013]

## 1. How to interpret the documentation

### 1.1 Current guidance and historical carryover

The guide retains GPT-5.6 material under “Previous models.” Historical guidance remains useful where current compatibility agrees; Astra-specific observations remain hypotheses to evaluate on Sol. [S001]

A useful reading order is:

1. Consult the exact model page for supported settings and modalities.
2. Consult the relevant feature guide for integration details.
3. Use the family guide for migration context.
4. Use historical sections to understand carryover, while checking the current contract.

This ordering is a recommended reconciliation method. It is especially useful when a general guide includes examples or model-selection language from an earlier generation. [S002] [S010]

### 1.2 What carries forward, what changes, and what needs testing

| Area | Status for GPT-6.1 | Practical interpretation |
| --- | --- | --- |
| Programmatic Tool Calling | Carried forward | Use generated code for bounded processing of tool results. [S027] |
| Multi-agent orchestration | Carried forward; beta support explicitly documented | Enable it deliberately and limit concurrency. [S029] |
| Explicit prompt caching | Carried forward | Choose cache boundaries and account for writes as well as reads. [S016] |
| Persisted reasoning | Carried forward; `all_turns` supported | Preserve compatible response items. [S012] |
| Pro reasoning mode | Available in Responses | Additional model work; independent of effort. [S012] |
| Structured Outputs | Supported | Constrain response structure with a schema. [S034] |
| Compaction | Carried forward | Reduce growing context while preserving continuation state. [S018] |
| Async tool calling | A GPT-6 addition | Let the model continue while application-run tools are pending. [S028] |
| Mid-turn steering | A GPT-6 addition | Send a user correction during an active WebSocket response. [S030] |
| Cache-preserving effort updates | A GPT-6 addition | Change effort between responses using an input item. [S013] |
| `none` reasoning | Unsupported in GPT-6.1 | Older configurations must change. [S002] |
| Chat Completions tool calls | Unsupported in GPT-6.1 | Move tool workflows to Responses. [S025] |
| Astra-specific behavior observations | Transfer hypotheses | Test any autonomy, style, or delegation adjustment on Sol. [S043] |

Feature availability does not enable a workflow automatically. A tool must be supplied or configured, its execution path must exist, and the application must handle its outputs. The tools overview distinguishes built-in tools, application functions, deferred discovery, and external integrations. [S050]

## 2. The exact GPT-6.1 specification

### 2.1 Model facts

| Property | Documented value |
| --- | --- |
| API identifier | `gpt-6.1-sol` |
| Context window | 1,050,000 tokens |
| Maximum output | 128,000 tokens |
| Knowledge cutoff | 30 April 2026 |
| Native inputs | Text and images |
| Native output | Text |
| Native audio/video | Not supported |
| Fine-tuning | Not supported |

Source: GPT-6.1 model page. These are API specifications; they do not establish a particular ChatGPT subscription allowance. [S002]

The API changelog records GPT-6.1 Sol’s release on 29 September 2026 and the addition of its Ultrafast tier on 8 October 2026. This matters when reading launch-era material that describes a feature as forthcoming. [S003]

### 2.2 Comparison with the earlier Sol models

| Property | GPT-5.6 Sol | GPT-6 Sol | GPT-6.1 Sol |
| --- | --- | --- | --- |
| Exact identifier | `gpt-5.6-sol` | `gpt-6-sol` | `gpt-6.1-sol` |
| Supports `none` effort | Yes | Yes | No |
| Standard input, per million tokens | $4.00 | $2.00 | $2.00 |
| Standard cached input, per million | $0.40 | $0.20 | $0.10 |
| Standard output, per million | $20.00 | $10.00 | $10.00 |

The GPT-5.6 and GPT-6 columns come from their respective model pages; GPT-6.1 prices come from the current pricing schedule. Rates shown are for short-context Standard processing. [S006] [S005] [S020]

GPT-6 Sol allowed Chat Completions function calling when reasoning was disabled. Since GPT-6.1 removes that effort option and requires Responses for tools, changing only the model string can break an otherwise working integration. [S005] [S025]

The earlier `gpt-5.6` alias routes to GPT-5.6 Sol. It provides no basis for inventing a `gpt-6.1` alias; use the documented GPT-6.1 identifier. [S006] [S003]

## 3. Choosing the model and the level of work

OpenAI’s current selection guidance places Sol between Astra’s highest capability and Luna’s lower-cost execution. Sol is recommended for complex projects where time and cost also matter; Astra remains a comparison candidate when a harder task justifies greater capability. [S004]

The following is a proposed starting policy, based on the selection guidance rather than measured results for a particular workload:

| Task shape | Starting configuration | Decision to test |
| --- | --- | --- |
| Focused edit or routine extraction | GPT-6.1, low effort | Whether lower reasoning preserves completeness |
| Complex technical work or a coordinated draft | GPT-6.1, medium effort | Whether the default meets the quality target |
| Conflicting evidence or a polished deliverable | GPT-6.1, high or xhigh | Whether additional reasoning improves the result |
| Exceptionally difficult analysis | Compare GPT-6.1 at xhigh/max with Astra | Which configuration produces the best successful result |
| Repeated, narrowly scoped automation | Compare GPT-6.1 with Luna | Whether a less expensive model meets the same acceptance criteria |

These are evaluation candidates, not fixed rules. The product selection page specifically associates Sol at medium effort with complex technical work and at extra-high effort with polished deliverables and conflicting evidence. [S008]

Increasing effort is useful only when the task benefits from more planning, exploration, or checking. An evaluation should judge the entire workflow rather than reward more reasoning tokens, more tool calls, or a longer explanation. [S047]

## 4. ChatGPT Work and Codex versus the API

### 4.1 Product availability and controls

The current product documentation lists GPT-6.1 Sol in ChatGPT Work and Codex, rather than ordinary Chat. Account, client, rollout, and workspace controls affect availability; selecting a model does not grant permission to use it. [S007]

In the product, use the model switcher to select an available model and reasoning effort. In the Codex command-line interface (CLI), `/model` changes the selection, and `codex -m gpt-6.1-sol` selects the model at launch. [S007]

| Decision | API control | Product interpretation |
| --- | --- | --- |
| Model | `model` | Select the available model in the picker. [S007] |
| Reasoning depth | `reasoning.effort` | Adjust available reasoning effort. [S007] |
| Response detail | `text.verbosity` and the prompt | State the desired length and required content. [S009] [S013] |
| Pro execution | `reasoning.mode` | This API field does not establish a matching product control. [S012] |
| Processing speed | `service_tier` | Use the product’s available speed modes. [S023] |
| Delegation | Multi-agent configuration | Product Ultra mode uses subagents. [S007] |

### 4.2 Names that describe different controls

“Pro,” “Ultra,” and “Ultrafast” should be kept distinct:

- **Pro subscription:** A ChatGPT plan and its usage allowances. [S024]
- **Pro reasoning mode:** Additional model work within a Responses request. [S012]
- **Ultra mode:** Product-level multi-agent work using subagents. [S007]
- **Ultrafast:** A processing tier designed to generate tokens faster. [S022]

A higher subscription tier, greater reasoning effort, multi-agent execution, and faster processing solve different problems. A practical configuration should specify which outcome each control is meant to improve. This distinction follows from their separately documented behavior. [S024] [S029] [S022]

## 5. Prompting GPT-6.1 effectively

### 5.1 Describe the result and the constraints

For substantial work, specify the goal, useful context, output requirements, and action boundaries. The ChatGPT prompting guide recommends these components without requiring a rigid template or a detailed itinerary. [S009]

A proposed general-purpose prompt is:

```text
Produce [deliverable] for [audience] to support [decision or action].

Use [sources and inputs]. Treat [source] as authoritative for [topic].
Success requires [specific acceptance criteria].
Respect [scope, budget, deadline, and formatting constraints].

Resolve ordinary gaps with stated assumptions. Ask when an unresolved choice
would materially change the result or exceed the authorized scope.
Return [format], with evidence beside important claims and a clear account
of material uncertainties.
```

This is an original template synthesizing the documented goal, context, output, and boundary guidance. Replace the placeholders with information that changes the outcome; remove components that add no value. [S009]

### 5.2 Ask for usable justification

Reasoning models already perform internal reasoning. The reasoning best-practices guide recommends direct prompts and does not require a request to expose step-by-step internal thought. Ask instead for the evidence, calculation, assumptions, tradeoffs, or verification that a reader needs to assess the answer. [S011]

For example, “Explain the three assumptions that affect this conclusion and cite the supporting records” is more operationally useful than demanding a transcript of hidden reasoning. This is a recommended prompt design, consistent with the distinction between internal reasoning and externally useful evidence. [S011]

### 5.3 Control style with specific requirements

Specify what a concise answer must preserve: the conclusion, supporting evidence, material uncertainty, and next action. For API applications, `text.verbosity` sets the default level of detail; the prompt should describe any task-specific structure. [S013]

A proposed style instruction is:

```text
Lead with the finding. Use professional, direct language.
For each important conclusion, include the evidence and any material limitation.
Use a table for exact comparisons. Remove repeated explanations and generic
introductions while retaining facts needed to make the decision.
```

Message roles and high-level instructions provide the API mechanism for applying persistent behavioral guidance. Consistency should be evaluated across representative inputs rather than inferred from a single successful answer. [S010]

### 5.4 Calibrate autonomy and skill instructions

Astra’s documented sensitivity to skills and repository instructions is a reason to audit those instructions when adopting a newer model. It is not proof that GPT-6.1 exhibits the same behavior in the same degree. [S001]

The official skills article recommends precise applicability descriptions and progressive disclosure: a small root instruction file should route to supporting material when needed. It also cautions that instructions appropriate for Sol or Luna may overconstrain Astra. The broader lesson is to maintain instructions for the models that actually use them. [S043]

For reusable workflows, a skill consists of a `SKILL.md` manifest and supporting files. Put repeatable actions in scripts, background guidance in references, and reusable templates in assets; make the description clear about when the skill applies. [S042]

**Recommended adoption method:** remove duplicate instructions one group at a time, preserve genuine requirements, and compare outcomes before adopting the leaner prompt. Do not delete domain constraints merely because the model is more capable. [S010] [S043]

## 6. Reasoning, output length, and pro execution

### 6.1 Independent controls

| Control | What it changes |
| --- | --- |
| `reasoning.effort` | Reasoning depth |
| `reasoning.mode` | Standard or pro execution |
| `text.verbosity` | Default response detail |
| `max_output_tokens` | Total generated-token ceiling |
| `service_tier` | Processing tier |

Mode and effort are independent. Pro applies additional model work and bills the resulting token usage at the selected model’s token rates; it does not require an invented GPT-6.1 Pro model identifier. [S012]

Generated-token usage includes visible text, reasoning, and non-visible formatting. Consequently, a small output ceiling can limit thinking as well as the answer. Count the reported generated tokens when estimating cost. [S019]

### 6.2 Effort changes during a conversation

For GPT-6 standard, single-agent requests, append a `configuration_update` before the next user message to change effort while leaving request-level effort unchanged. Updates persist until replaced. The response’s `reasoning.effort` still reports the request-level value, and adjacent configuration updates are rejected. [S012]

```json
{
  "type": "configuration_update",
  "reasoning": { "effort": "high" }
}
```

Do not combine this mechanism with automatic compaction or automatic truncation. The standalone `/responses/compact` endpoint rejects histories containing updates. The documented alternative is a `compaction_trigger` item, followed by a fresh effort update after compaction. [S013]

This is a between-response configuration change. Sending an instruction while a response is already running uses the separate steering mechanism described in Section 9. [S030]

### 6.3 Persisted reasoning and transparency

GPT-6.1 supports `reasoning.context: "all_turns"` for available compatible reasoning items; the setting does not create missing history. Cross-family reasoning may be omitted as incompatible. Check the returned effective context rather than assuming every model shares an earlier model’s default. Raw reasoning remains opaque. [S012]

**Recommended practice:** compare standard and pro at the same effort before changing both. Select higher effort or pro when the added work improves an acceptance criterion, not merely when the answer becomes longer. [S008] [S047]

## 7. A practical Responses API baseline

### 7.1 A small starting request

The following is an illustrative request body for `POST /v1/responses`, not a benchmark result:

```json
{
  "model": "gpt-6.1-sol",
  "reasoning": { "effort": "medium" },
  "text": { "verbosity": "medium" },
  "instructions": "Give a decision-ready assessment with evidence and explicit uncertainties.",
  "input": "Assess the supplied proposal against its stated acceptance criteria."
}
```

Responses accepts a string or input items and returns typed output items. An integration should inspect those items rather than assume every response is a single final text message. Applications using the software development kit (SDK) can read its `output_text` convenience property for generated text. [S014]

### 7.2 Remove incompatible legacy settings

For GPT-6.1, remove `temperature`, `top_p`, and `top_logprobs`. Also remove Chat Completions `logprobs`, or `message.output_text.logprobs` from a Responses `include` array. The family migration guidance prohibits these settings when reasoning is enabled, and GPT-6.1 cannot disable reasoning. [S001]

For an existing `none` or `minimal` configuration, start with `low`. Preserve other supported effective effort settings before tuning. [S001]

### 7.3 Continue the workflow correctly

For a stored chain, send `previous_response_id` and new input. Resend top-level `instructions`: that field is not inherited from the previous request. For manual history management, retain the output items, including tool and reasoning items, rather than reconstructing only the prose. [S014]

Preserve assistant message `phase` values when replaying history: `commentary` denotes intermediate work, and `final_answer` denotes the completed response. Losing that distinction can make a progress message look like completion. [S013]

For custom functions, the application executes the requested function and returns its result with the original `call_id`. The model’s function request does not itself execute the external action. Use explicit strict schemas when argument shape is part of the contract, and handle schema-rejection errors. [S025]

## 8. Conversation state, context size, and continuation

### 8.1 Keep the different kinds of state distinct

| Mechanism | Purpose |
| --- | --- |
| Conversation history | Preserve visible inputs, answers, and tool results. [S015] |
| Persisted reasoning | Make compatible prior reasoning available. [S012] |
| Prompt cache | Reuse processing of an identical prompt prefix. [S016] |
| Compaction | Carry continuation state in a smaller representation. [S018] |

These mechanisms are complementary. A cached prefix does not replace the need to supply or reference the relevant conversation, and a large context window does not by itself preserve state between independent requests. This is a recommended interpretation of the separately documented mechanisms. [S015] [S016]

A `previous_response_id` chain reduces what the application must resend; it does not make previous context free. Earlier input in the chain remains billable, subject to applicable caching. [S015]

For stateless continuation, encrypted reasoning permits continuity without stored response state. Replay the returned opaque items with the relevant inputs and tool results; reconstructing only the visible answer loses information the continuation may need. [S014] [S015]

### 8.2 Plan for growing context

Compaction reduces context size while carrying relevant prior state and reasoning into later work. Server-side compaction uses `context_management` with `compact_threshold`; the standalone endpoint provides another integration path. Preserve the returned opaque compaction item when managing input arrays. With response-ID chaining, do not independently prune the chain. [S018]

**Recommended practice:** preserve authoritative decisions, acceptance criteria, unresolved questions, and artifact locations in an explicit project record. Evaluate whether compaction retains these details and whether changed context affects cache reuse. Compaction is a continuation mechanism, not an independently verified record of every earlier fact. [S018] [S047]

For large inputs, use the input-token-count endpoint with the actual payload, including files and tools. Its count includes message structure and formatting that a plain-text tokenizer can miss. This is particularly useful before crossing a pricing boundary or approaching the context limit. [S019]

## 9. Tool orchestration: choose the mechanism by task shape

### 9.1 A decision table

The GPT-6.1 model page confirms support for web/file search, computer use, execution tools, Apply Patch, skills, MCP, and tool search. Each still needs its appropriate integration. [S002]

| Situation | Suitable mechanism |
| --- | --- |
| A single lookup or a result requiring fresh judgment | Direct tool calling. [S050] |
| A large catalog whose schemas would inflate context | Tool search. [S026] |
| Predictable filtering, joining, or aggregation | Programmatic Tool Calling. [S027] |
| A slow application tool plus independent work | Async tool calling. [S028] |
| Independent research or implementation workstreams | Multi-agent orchestration. [S029] |
| A correction during active model work | Mid-turn steering. [S030] |

### 9.2 Tool search

Tool search loads deferred definitions when needed. Add `{"type": "tool_search"}` and mark eligible functions or Model Context Protocol (MCP) servers with `defer_loading: true`. The model initially sees searchable names and descriptions; discovery adds the selected definitions to context. [S026]

Grouping related functions into well-described namespaces or MCP servers can produce more useful savings than deferring individual functions. Hosted discovery suits a known catalog; client-executed discovery allows an application to enforce its own tenant, project, or permission-dependent availability. [S026]

**Recommended use:** expose a compact, accurate description of each searchable surface. Treat discovery as a way to reduce irrelevant definitions, not as permission to call every tool a registry happens to contain. [S026] [S050]

### 9.3 Programmatic Tool Calling

Programmatic Tool Calling (PTC) lets the model compose eligible tools in JavaScript and reduce intermediate results in a hosted runtime. Enable `programmatic_tool_calling` and set the eligible tools’ `allowed_callers`. Provide reliable return shapes, using `output_schema` where appropriate. [S027]

PTC is useful when code can perform bounded filtering, joining, ranking, deduplication, or aggregation. Prefer direct calls for adaptive investigation, approval-sensitive actions, or final citation and artifact checks unless the program explicitly preserves the needed evidence. A program cannot itself run tool search; discovery must occur before it uses deferred tools. [S027]

A proposed workflow boundary is: “Retrieve the approved records, calculate the comparison, and return the source identifiers plus the relevant values; then assess the business implications.” The calculation is a bounded program stage, while the interpretation remains a model judgment. [S027]

### 9.4 Async tool calling

Set `async: true` on an application-run function or custom tool. The model can continue independent work while the application executes the job, then receive a matching output using the original `call_id`. The application remains responsible for pending-job state and returning the result. [S028]

Important limits: async does not apply to hosted built-in tools; use direct calls rather than PTC for async tools. In multi-agent mode, do not combine async tools with parallel tool calls. A developer-defined wait tool can help the model pause when it reaches a real dependency. [S028]

**Recommended use:** overlap a slow read-only lookup with unrelated drafting or analysis. Do not let a preliminary answer appear complete when it still depends on an unresolved result. That is a workflow-design recommendation based on the documented pending-result model. [S028]

### 9.5 Multi-agent orchestration

GPT-6.1’s Responses multi-agent capability is beta. Enable `multi_agent.enabled` and set an appropriate `max_concurrent_subagents`. The beta SDK uses `responses_multi_agent=v1`; raw requests and WebSocket connections use the corresponding `OpenAI-Beta` header. Beta item schemas may change. [S029]

The root agent synthesizes the subagents’ results. In this Responses implementation, subagents share the request’s model and available tools. Independent document reviews, codebase areas, and competing hypotheses are appropriate workstreams. [S029]

**Recommended delegation contract:** give each workstream a distinct question, an evidence requirement, an output format, and a stopping condition. Require the coordinator to reconcile duplicates and disagreements. Shared writes need coordination; parallel work is helpful only if the resulting deliverable remains coherent. [S029]

### 9.6 Steering while work is active

Over a Responses WebSocket connection, send `response.steer` after `response.created`, referencing the active response through `previous_response_id`. An accepted steering event means the instruction is queued, not yet implemented. Follow the subsequent events and preserve any required tool-result or approval handling. [S030]

Steering does not retract already streamed text, reverse completed actions, or cancel tools already started. The server completes the current output item and running hosted work before creating its continuation; do not start a competing response merely because the steering update was accepted. [S030]

**Recommended correction:** identify the changed requirement and the work still wanted, such as “Continue the analysis, but replace the revenue-growth objective with margin improvement and revise the recommendation accordingly.” [S030]

## 10. Files, visual inputs, coding, and structured results

### 10.1 Match the task to the input or execution path

| Task | Suitable path | Reason |
| --- | --- | --- |
| Read a visually complex Portable Document Format (PDF) file | Direct file input | Vision-capable models receive extracted text and page images. [S037] |
| Search a large document collection | File search | Hosted semantic and keyword retrieval over vector stores. [S036] |
| Calculate across complete spreadsheets | Shell or Code Interpreter | Execute explicit calculations over actual file data. [S040] [S039] |
| Inspect a screenshot or diagram | Image input | Native vision analysis; select detail according to the task. [S038] |
| Modify code files | Apply Patch with an execution harness | Apply structured changes and report their results. [S041] |
| Return a machine-readable assessment | Structured Outputs | Constrain final response shape. [S034] |

### 10.2 Document and spreadsheet limitations

Non-PDF document inputs extract text rather than embedded charts and images. For a Word document or presentation whose graphics matter, convert it to PDF before direct input. Spreadsheet augmentation processes up to the first 1,000 rows per sheet and adds summary/header information; it is not equivalent to a complete deterministic calculation over the workbook. [S037]

For large collections, file search retrieves relevant passages rather than placing the entire corpus into every prompt. Search-result content is not returned by default; request `file_search_call.results` when the application needs to inspect the retrieved evidence. [S036]

Code Interpreter runs Python in a sandbox and can process files, perform analysis, and generate artifacts. Hosted or local shell supports richer terminal-based processing. A proposed numerical workflow is to calculate first, reconcile totals and units, and then ask the model to explain the result with the computed evidence. [S039] [S040]

### 10.3 Image understanding and image generation

The vision guide distinguishes image analysis from generation: a mainline model can invoke an image-generation tool, but generated imagery comes through that tool’s separate image-model path. Tool-assisted image output should not be confused with native image generation by GPT-6.1. [S038]

Image detail, image-token cost, and coordinate handling depend on the supported model and encoding rules. For small text or precise visual analysis, use an appropriate supported detail setting and validate the result against the original image. Do not blindly apply an Astra or GPT-5.6 image-limit row to GPT-6.1. [S038]

**Recommended document verification:** check a consequential chart or table against the relevant page image, especially when numbers, units, labels, or footnotes drive the conclusion. This is an application-level verification choice, supported by the file-input distinction between text-only and visual processing. [S037]

### 10.4 Coding and computer use

Apply Patch emits file operations that an application applies and acknowledges using `apply_patch_call_output`. A patch proposal and a successful application are different states; the subsequent model turn needs the actual outcome. [S041]

The computer-use guide describes both code execution in an isolated browser/desktop environment and structured computer-tool actions. Its specific preference for code execution is stated for Astra. For GPT-6.1, retain a working interface or compare integration approaches rather than treating that preference as a measured Sol result. [S051]

A proposed coding acceptance contract is: “Reproduce the failure, make the scoped change, run checks that exercise the changed behavior, and report the files affected and remaining limitations.” This adapts the patch-and-feedback loop to a reviewable result. [S041]

### 10.5 Structured Outputs

Structured Outputs constrains the response to supported JavaScript Object Notation (JSON) Schema rules. In Responses, use `text.format` with `type: "json_schema"`, a schema name, and the schema; strict mode constrains permitted fields and values. Tool argument schemas and final-answer schemas serve different purposes. [S034]

Schema compliance does not establish factual correctness. The application must also handle refusals and incomplete responses; these do not necessarily produce the desired business object. For a research output, a useful proposed schema includes the claim, supporting source identifiers, uncertainty, and any missing evidence. [S034]

## 11. Cost, caching, and processing speed

### 11.1 GPT-6.1 API token rates

Prices below are US dollars per million tokens. [S020]

| Token category | Standard, up to 272,000 input tokens | Standard, over 272,000 input tokens |
| --- | ---: | ---: |
| Ordinary input | $2.00 | $4.00 |
| Cached input | $0.10 | $0.20 |
| Cache writes | $2.50 | $5.00 |
| Output | $10.00 | $15.00 |

Long-context rates apply to the full request when the input exceeds the threshold, not only to the excess tokens. Tool and container charges may add to token charges. [S020]

Regional processing adds a 10% premium where available. [S002]

The headline context capacity and the lower pricing band are different limits. **Recommended practice:** estimate token count before inserting an entire corpus, and compare retrieval or staged analysis when a large request changes the economics. [S019]

### 11.2 Calculate cache cost correctly

Cache writes are a separate input category, not an extra fee added to ordinary input pricing for the same tokens. Use reported `cached_tokens` and `cache_write_tokens`; ordinary input is total input minus those categories. [S016]

For a short-context Standard request, a useful derived calculation is:

```text
Token cost =
  (2.00 × ordinary_input_tokens
   + 0.10 × cached_input_tokens
   + 2.50 × cache_write_tokens
   + 10.00 × output_tokens) / 1,000,000
```

Illustration: a 100,000-token prefix written once and fully reused once costs $0.26 in input charges: $0.25 for the write plus $0.01 for the read. Two ordinary passes cost $0.40. This is arithmetic from the published rates, assuming an eligible full cache hit and excluding outputs and tools. [S020]

### 11.3 Make caching useful

Reuse requires an exact compatible prefix. Stable instructions and tools belong before changing content. GPT-5.6-and-later caching has a 1,024-token minimum visible prefix; `prompt_cache_options.ttl` uses `"30m"`, its default and only supported value. Explicit mode uses developer-selected breakpoints; implicit mode allows automatic ones. [S016]

On these models, `prompt_cache_key` is optional for separate accounting rather than required to optimize routing. Rewriting earlier messages, tool definitions, effort, or output configuration can disrupt reuse. A cache lifetime is not a guarantee that every eligible request finds the same cached state. [S016]

When reuse is unexpectedly low, set `prompt_cache_options.comparison_response_id` to a suitable baseline response and inspect `prompt_cache_diagnostics`. This requests a comparison; it does not load the earlier conversation or change the caching policy. Measure actual reuse using `usage.input_tokens_details.cached_tokens`. [S017]

**Recommended operational method:** compare similar requests before and after a prompt or tool-catalog change. Diagnose configuration differences before padding a prompt or adding cache breakpoints simply to increase a hit-rate metric. [S017]

### 11.4 Choose a processing tier

| API processing option | Published price relationship to Standard |
| --- | --- |
| Batch | 50% lower |
| Flex | 50% lower |
| Fast | 2× |
| Ultrafast | 6× |

These multipliers describe token pricing; suitability, latency, availability, and limits should be checked in the relevant tier documentation. [S020]

Fast is configured with `service_tier: "fast"`; `"priority"` is the earlier name with the same behavior for supported models. It is useful when more consistent latency justifies the cost. [S021]

Ultrafast uses `service_tier: "ultrafast"`, supports GPT-6.1, and has separate rate limits. The guide recommends persistent WebSockets for tool-heavy applications because network overhead can reduce the benefit of faster token generation. Faster generation does not establish a universal task-speed multiplier. [S022]

### 11.5 Product allowances are priced differently

ChatGPT Work and Codex share usage. API token rates should not be used to estimate how many tasks are included in a subscription; API-key billing follows API pricing instead. [S024]

For included product usage, Fast consumes allowances at 2.5× Standard and Ultrafast at 8×. Purchased credits and eligible Enterprise pay-as-you-go usage use 2× and 6× respectively. Product Ultrafast is available on Pro $500 and eligible Enterprise/Edu plans, subject to workspace controls. [S023]

The product speed guide’s “up to 8× faster” generation statement specifically describes Astra. Do not turn that statement, or the 8× allowance multiplier, into a guaranteed GPT-6.1 completion-speed claim. [S023]

## 12. Production behavior and data handling

### 12.1 Streaming, WebSockets, and background execution

These mechanisms solve different problems:

| Mechanism | Purpose | Integration consequence |
| --- | --- | --- |
| HTTP streaming | Deliver output while generation continues | Consume typed server-sent events (SSE); early text is not completion. [S032] |
| WebSocket mode | Reduce repeated continuation overhead | Keep a persistent connection and send incremental inputs with response IDs. [S031] |
| Background mode | Execute long requests asynchronously | Poll response status or integrate the completion workflow. [S033] |
| Async tool calling | Overlap application tools with independent model work | Maintain pending tool jobs and matching results. [S028] |

WebSocket requests use `response.create` events; transport-specific HTTP fields such as `stream` and `background` are not used in those events. The documented WebSocket mode also supports `stream_id` for multiplexed conversations and response-chain forks. [S031]

Background requests use `background: true`. The current guide states that background requests from Zero Data Retention (ZDR) projects use `store: false`, while response data is temporarily written to disk for roughly ten minutes to support polling. This is a feature-specific retention detail that needs to be considered explicitly. [S033]

**Recommended completion rule:** an application should distinguish partial text, pending tools, a finished response, an incomplete response, and an error. Show a result as final only after the relevant model and application work has completed. Streaming is a delivery mechanism, not evidence that the task succeeded. [S032] [S050]

### 12.2 Privacy controls have different scopes

By default, OpenAI does not use API data for model training unless the customer opts in. API abuse-monitoring logs and application state are separate retention categories. Standard abuse logs may retain customer content for up to thirty days, subject to documented exceptions; approved ZDR and Modified Abuse Monitoring controls change that behavior. [S044]

Setting `store: false` disables stored response state; it does not, by itself, establish an organization-wide zero-retention arrangement. Stateful tools, files, caches, background requests, processing regions, and external services must be checked against their own documented retention behavior. [S044]

GPT-6.1 supports United States and European Union (EU) data residency, including Fast and Ultrafast. Check project eligibility and endpoint requirements before choosing a region or tier. [S002] [S044]

Remote MCP tools connect the application to another service. Configure the server, authentication, allowed tools, and approval policy deliberately; a tool result or outbound request may involve data outside the model provider’s own controls. The MCP guide also documents a tunnel path for private servers. [S052]

### 12.3 Handle limits and safety stops by their actual cause

Rate limits may constrain requests or tokens independently. Follow a valid `Retry-After` header when provided; otherwise use bounded exponential backoff with jitter. Avoid multiplying SDK retries with application retries, and do not automatically retry billing, quota, or other action-required failures. [S046]

For requests covered by misalignment monitoring, `misalignment_policy_violation` can stop a conversation. The documented response is to stop dispatching actions, retain relevant records, and review what already happened. Do not automatically retry the blocked workflow. Monitoring is asynchronous and does not reverse prior actions. [S045]

Coverage depends on the model and request path; the monitoring guide distinguishes Responses context mechanisms from Chat Completions. Its coverage rules should not be replaced with a blanket assumption that every GPT-6.1 request is monitored in the same way. [S045]

## 13. A migration and evaluation plan

### 13.1 Preserve a baseline before adding capabilities

The following is a proposed adoption sequence:

1. **Record the baseline.** Retain representative prompts, tools, artifacts, success criteria, latency, token usage, and cost.
2. **Make the compatibility changes.** Select the exact GPT-6.1 identifier, replace unsupported effort values, use Responses for tools, and remove incompatible sampling fields.
3. **Compare equivalent tasks.** Keep inputs and acceptance criteria fixed so the model change can be assessed.
4. **Tune one dimension at a time.** Compare effort, prompt detail, pro mode, caching, and speed independently where practical.
5. **Add orchestration selectively.** Introduce tool search, PTC, async, or delegation only for a stage that benefits.
6. **Retain a regression set.** Recheck difficult cases after prompt, tool, model, or integration changes.

This sequence combines the documented migration requirements with task-specific evaluation principles. It does not assume a guaranteed quality improvement from a model upgrade. [S005] [S025] [S047]

### 13.2 Evaluate the complete deliverable

A proposed evaluation record should include:

| Dimension | Example acceptance question |
| --- | --- |
| Correctness | Are the central findings and calculations correct? |
| Completeness | Does the result satisfy every required part? |
| Evidence | Can the important claims be traced to the relevant source? |
| Action fidelity | Did the agent act within the authorized scope? |
| Artifact usability | Can the delivered file be opened and used? |
| Continuity | Did a correction or follow-up preserve the right task state? |
| Efficiency | What were total elapsed time and billed usage? |

Use ordinary cases, difficult cases, and known failures. A small representative set is an initial diagnostic, not a statistically established guarantee. Human judgment should calibrate automated grading. This is a proposed application-level rubric based on the evaluation guide. [S047]

A useful derived metric is **cost per successful task**: evaluated cost divided by tasks meeting the acceptance criteria. An incomplete result does not count as a success. [S013]

### 13.3 Check the platform lifecycle

The evaluation discipline remains relevant, but the hosted Evals platform is scheduled to become read-only on 31 October 2026 and shut down on 30 November 2026. Reusable prompt objects and Agent Builder are also scheduled for shutdown on 30 November. Avoid building a new workflow around these retiring services without a migration plan. [S048]

GPT-5.5’s 14 October 2026 retirement from ChatGPT, Work, and Codex is separate from API availability. A product-model retirement should not be interpreted as an API retirement unless the API deprecations page says so. [S024]

For applications that prefer a managed agent harness, the Agents API provides sessions, orchestration, compaction, recovery, sandbox execution, and artifacts. It is a distinct integration surface; do not copy Responses request fields into an Agents session without consulting that API’s configuration. [S049]

## 14. Task-specific prompt recipes

The following original examples apply documented prompting and tool principles. They are starting templates to evaluate, not claims about a tested GPT-6.1 benchmark.

### 14.1 Source-backed research

```text
Investigate [question] for [audience and decision].
Use the supplied primary sources, then retrieve current official evidence
for gaps. Cite the source beside each material claim.
Separate documented facts, calculations, and recommendations.
Resolve conflicts by checking dates, applicability, and the exact version.
Return a complete report covering [required topics], with a comparison table,
material uncertainties, and an actionable conclusion.
```

This recipe asks for an evidence-bearing result. In an API web-search application, preserve source annotations and show visible, clickable citations; prose that appears authoritative is not a substitute for accessible evidence. [S035]

### 14.2 Analysis of a workbook or document set

```text
Analyze [files] to answer [decision question].
Use execution tools for calculations over the complete data.
Check totals, units, missing values, and the treatment of excluded records.
For charts or diagrams, inspect the relevant page images when available.
Return the computed result, the method, the source location, and any
limitation that could change the decision.
```

This is a proposed combination of deterministic computation and source inspection. Use complete file data for calculations; do not rely on a spreadsheet’s automatically augmented preview as proof that every row was analyzed. [S039] [S037]

### 14.3 Review with a constrained output

```text
Assess [proposal] against [criteria].
For each finding, provide severity, the supporting record, the consequence,
and the smallest useful corrective action.
State when evidence is insufficient instead of inventing a missing fact.
Return the agreed schema and keep the narrative consistent with its fields.
```

A final-answer schema can make the result easier for software to consume, while substantive evidence and validation still determine whether the assessment is trustworthy. [S034]

### 14.4 Work that uses connected tools

```text
Complete [in-scope task] using [approved connected sources].
Use available reads to resolve routine uncertainty.
Prepare any consequential action as a concrete, reviewable result.
Apply the stated approval boundary to [specific action types].
Confirm the actual tool outcome before reporting that an action completed.
```

This proposed recipe must be paired with real application permissions and an explicit tool approval policy. A prompt alone is not an access-control or execution system. [S052] [S050]

## 15. Important limits on interpretation

- **Model positioning is not a universal result.** Compare Sol and Astra against the actual acceptance criteria. [S004]
- **Astra behavior is not a verified Sol default.** Treat autonomy, style, and delegation adjustments as transfer hypotheses. [S043]
- **API and product allowances are different.** Context specifications and API prices do not determine subscription task counts. [S024]
- **History and caching are different.** Referencing an earlier response does not establish a cache hit or eliminate billing. [S015] [S017]
- **Configuration updates have compatibility limits.** They should not be combined indiscriminately with pro, multi-agent, or automatic compaction workflows. [S013]
- **The final message matters.** A correct intermediate program result can still lead to an incomplete user-facing result; assess both stages. [S027]
- **Visual limits are model-specific.** Verify the applicable encoding rules instead of inheriting another model’s numerical limits. [S038]
- **Tool execution needs its own verification.** A requested patch, function, or browser action is not evidence of success. [S025] [S041] [S051]

The reviewed GPT-6.1 model page lists the `gpt-6.1-sol` selector without a separate dated snapshot identifier. Do not invent a dated slug. If production stability requires a pinned version, use only a snapshot that OpenAI actually documents and makes available. [S002] [S010]

## 16. A focused reading path

| Need | Primary reading |
| --- | --- |
| Exact GPT-6.1 contract | Model page and API changelog. [S002] [S003] |
| Family changes and historical carryover | Using GPT-6. [S001] |
| Everyday product use | Product models, prompting, and speed. [S007] [S009] [S023] |
| Reasoning and continuation | Reasoning, conversation state, and compaction. [S012] [S015] [S018] |
| Tool orchestration | Tool search, PTC, async, and multi-agent. [S026] [S027] [S028] [S029] |
| Active corrections | Steering and WebSockets. [S030] [S031] |
| Cost control | Pricing, prompt caching, diagnostics, and token counting. [S020] [S016] [S017] [S019] |
| Document and data work | File inputs, file search, vision, and execution tools. [S037] [S036] [S038] [S039] [S040] |
| Deployment quality | Evaluation principles, data controls, limits, and deprecations. [S047] [S044] [S046] [S048] |

## References

All sources below are official OpenAI publications reviewed on 13 October 2026 (UTC). Feature and model pages are living documentation; release and retirement dates are stated separately where material.

- **S001** — OpenAI. [Using GPT-6][S001].
- **S002** — OpenAI. [GPT-6.1 Sol model][S002].
- **S003** — OpenAI. [API changelog][S003].
- **S004** — OpenAI. [API model selection][S004].
- **S005** — OpenAI. [GPT-6 Sol model][S005].
- **S006** — OpenAI. [GPT-5.6 Sol model][S006].
- **S007** — OpenAI. [Models in ChatGPT and Codex][S007].
- **S008** — OpenAI. [Model selection in ChatGPT][S008].
- **S009** — OpenAI. [Prompting in ChatGPT Work and Codex][S009].
- **S010** — OpenAI. [Prompt engineering][S010].
- **S011** — OpenAI. [Reasoning best practices][S011].
- **S012** — OpenAI. [Reasoning models][S012].
- **S013** — OpenAI. [API deployment checklist][S013].
- **S014** — OpenAI. [Migrate to the Responses API][S014].
- **S015** — OpenAI. [Conversation state][S015].
- **S016** — OpenAI. [Prompt caching][S016].
- **S017** — OpenAI. [Prompt cache diagnostics][S017].
- **S018** — OpenAI. [Compaction][S018].
- **S019** — OpenAI. [Counting tokens][S019].
- **S020** — OpenAI. [API pricing][S020].
- **S021** — OpenAI. [Fast mode in the API][S021].
- **S022** — OpenAI. [Ultrafast mode in the API][S022].
- **S023** — OpenAI. [Speed in ChatGPT Work and Codex][S023].
- **S024** — OpenAI. [ChatGPT Work and Codex pricing][S024].
- **S025** — OpenAI. [Function calling][S025].
- **S026** — OpenAI. [Tool search][S026].
- **S027** — OpenAI. [Programmatic Tool Calling][S027].
- **S028** — OpenAI. [Async tool calling][S028].
- **S029** — OpenAI. [Multi-agent in the Responses API][S029].
- **S030** — OpenAI. [Mid-turn steering][S030].
- **S031** — OpenAI. [WebSocket mode][S031].
- **S032** — OpenAI. [Streaming API responses][S032].
- **S033** — OpenAI. [Background mode][S033].
- **S034** — OpenAI. [Structured model outputs][S034].
- **S035** — OpenAI. [Web search][S035].
- **S036** — OpenAI. [File search][S036].
- **S037** — OpenAI. [File inputs][S037].
- **S038** — OpenAI. [Images and vision][S038].
- **S039** — OpenAI. [Code Interpreter][S039].
- **S040** — OpenAI. [Shell][S040].
- **S041** — OpenAI. [Apply Patch][S041].
- **S042** — OpenAI. [Skills][S042].
- **S043** — OpenAI. [Rethinking skills and prompts for GPT-6 Astra][S043].
- **S044** — OpenAI. [Data controls in the OpenAI platform][S044].
- **S045** — OpenAI. [Misalignment monitoring][S045].
- **S046** — OpenAI. [Rate limits][S046].
- **S047** — OpenAI. [Evaluation best practices][S047].
- **S048** — OpenAI. [Deprecations][S048].
- **S049** — OpenAI. [Agents API overview][S049].
- **S050** — OpenAI. [Using tools][S050].
- **S051** — OpenAI. [Computer use][S051].
- **S052** — OpenAI. [MCP servers][S052].

[S001]: https://developers.openai.com/api/docs/guides/latest-model
[S002]: https://developers.openai.com/api/docs/models/gpt-6.1-sol
[S003]: https://developers.openai.com/api/docs/changelog
[S004]: https://developers.openai.com/api/docs/guides/model-selection
[S005]: https://developers.openai.com/api/docs/models/gpt-6-sol
[S006]: https://developers.openai.com/api/docs/models/gpt-5.6-sol
[S007]: https://learn.chatgpt.com/docs/models
[S008]: https://learn.chatgpt.com/docs/model-selection
[S009]: https://learn.chatgpt.com/docs/prompting
[S010]: https://developers.openai.com/api/docs/guides/prompt-engineering
[S011]: https://developers.openai.com/api/docs/guides/reasoning-best-practices
[S012]: https://developers.openai.com/api/docs/guides/reasoning
[S013]: https://developers.openai.com/api/docs/guides/deployment-checklist
[S014]: https://developers.openai.com/api/docs/guides/migrate-to-responses
[S015]: https://developers.openai.com/api/docs/guides/conversation-state
[S016]: https://developers.openai.com/api/docs/guides/prompt-caching
[S017]: https://developers.openai.com/api/docs/guides/prompt-caching/diagnostics
[S018]: https://developers.openai.com/api/docs/guides/compaction
[S019]: https://developers.openai.com/api/docs/guides/token-counting
[S020]: https://developers.openai.com/api/docs/pricing
[S021]: https://developers.openai.com/api/docs/guides/fast-mode
[S022]: https://developers.openai.com/api/docs/guides/ultrafast-mode
[S023]: https://learn.chatgpt.com/docs/agent-configuration/speed
[S024]: https://learn.chatgpt.com/docs/pricing
[S025]: https://developers.openai.com/api/docs/guides/function-calling
[S026]: https://developers.openai.com/api/docs/guides/tools-tool-search
[S027]: https://developers.openai.com/api/docs/guides/tools-programmatic-tool-calling
[S028]: https://developers.openai.com/api/docs/guides/async-tool-calling
[S029]: https://developers.openai.com/api/docs/guides/responses-multi-agent
[S030]: https://developers.openai.com/api/docs/guides/steering
[S031]: https://developers.openai.com/api/docs/guides/websocket-mode
[S032]: https://developers.openai.com/api/docs/guides/streaming-responses
[S033]: https://developers.openai.com/api/docs/guides/background
[S034]: https://developers.openai.com/api/docs/guides/structured-outputs
[S035]: https://developers.openai.com/api/docs/guides/tools-web-search
[S036]: https://developers.openai.com/api/docs/guides/tools-file-search
[S037]: https://developers.openai.com/api/docs/guides/file-inputs
[S038]: https://developers.openai.com/api/docs/guides/images-vision
[S039]: https://developers.openai.com/api/docs/guides/tools-code-interpreter
[S040]: https://developers.openai.com/api/docs/guides/tools-shell
[S041]: https://developers.openai.com/api/docs/guides/tools-apply-patch
[S042]: https://developers.openai.com/api/docs/guides/tools-skills
[S043]: https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra
[S044]: https://developers.openai.com/api/docs/guides/your-data
[S045]: https://developers.openai.com/api/docs/guides/safety-checks/misalignment-monitoring
[S046]: https://developers.openai.com/api/docs/guides/rate-limits
[S047]: https://developers.openai.com/api/docs/guides/evaluation-best-practices
[S048]: https://developers.openai.com/api/docs/deprecations
[S049]: https://developers.openai.com/api/docs/guides/agents-api/overview
[S050]: https://developers.openai.com/api/docs/guides/tools
[S051]: https://developers.openai.com/api/docs/guides/tools-computer-use
[S052]: https://developers.openai.com/api/docs/guides/tools-connectors-mcp





