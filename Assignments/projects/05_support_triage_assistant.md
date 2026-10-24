# Project 05: Support Triage Assistant

**Difficulty:** Intermediate  
**Estimated effort:** 8–16 hours

## Scenario

A fictional software company wants an assistant to explain account information, summarize support tickets, and suggest documented troubleshooting steps. Some requests need a person rather than an automatically generated promise. Build a tool-routing graph that makes this distinction visible.

## Learning objectives

- Adapt the school-tool pattern to a new domain with static data.
- Combine model-selected tools with explicit workflow decisions.
- Ground responses and route unsupported or actionable requests to human review.

## Prerequisites

Assignments 08–09 or equivalent LangGraph and LangChain tool experience. Reference: [school routing graph](../../langGraph/school_agent_graph.py). Use configurable Ollama Cloud GPT-OSS models for routing and final generation. A CLI is sufficient; no live support system or database is required.

## Minimum implementation requirements

1. Create three dummy LangChain tools for account lookup, ticket lookup, and knowledge-note search. Store at least four accounts, six linked tickets, and six knowledge notes with stable IDs in a shared synthetic-data module. Lookups for absent IDs must return an explicit not-found result.
2. Build a LangGraph flow with configuration, planning, tool execution, review decision, and final response nodes. Use a smaller GPT-OSS model to choose tools and a larger GPT-OSS model to explain their outputs; print selected calls and node progress.
3. Validate tool names and arguments before execution. Keep tool calls read-only and static; the assistant must not change accounts, send messages, close tickets, issue refunds, or claim those actions happened.
4. Return a structured application result containing the answer, tool/source IDs, `needs_human_review`, and a review reason when applicable. Enforce review when a requested account/ticket is absent, a required tool fails, planning is invalid, no relevant guidance is found, or the user requests an account change/refund. Uncertainty in these conditions must route to review.
5. Cite the returned account, ticket, and note IDs used in explanations. Describe only documented troubleshooting steps; do not invent service commitments, resolution times, or refund eligibility.
6. Preserve successful tool results when another call fails. A review response may summarize known facts, but must identify what remains unverified and avoid presenting the requested action as completed.
7. Document how the graph makes review decisions and how dummy lookup/search behavior works. Use controlled fixtures for planner/tool failures.

## Sample inputs and demonstration scenarios

Include active Starter account `A100`, an open email-delivery ticket `T100` linked to `A100`, and knowledge note `N100` describing how to check an email address and spam folder. The note must not promise that these steps resolve every case.

| Scenario | Query or action | Observable expected behavior |
| --- | --- | --- |
| Account question | “Which plan is account A100 on?” | Answer says Starter and cites A100. |
| Combined evidence | “Summarize ticket T100 and suggest documented next steps.” | Ticket and note data are fetched, cited, and clearly separated from actions taken. |
| Missing record | “What is happening with ticket T999?” | Not-found evidence produces human-review status without an invented ticket. |
| Action request | “Upgrade A100 and refund last month's charge.” | Human review is required; no upgrade or refund is claimed. |
| Missing guidance | Ask about an issue absent from all notes | The assistant acknowledges the gap and requests review rather than inventing steps. |
| Tool failure | Simulate a timeout while retrieving a required ticket | Known facts remain visible, and review status explains the missing evidence. |
| Invalid plan | Supply a controlled unregistered tool call | It is not executed; the result requests review with a planning reason. |

Prepare eight demo queries covering these behaviors, including at least two requests that combine tools. Review flags and reasons must be visible independently of natural-language phrasing.

## Deliverables

Submit the graph, dummy tools/data, dependencies/configuration template, run guide, state/edge diagram, eight query traces, and a short report explaining review decisions and limitations.

## Acceptance criteria

- All three tools are exercised, with at least two multi-tool demonstrations.
- Account/ticket links and cited IDs agree with the returned data.
- Every review-triggering scenario returns `needs_human_review: true` and a specific reason.
- A supported informational request can complete without unnecessary review.
- Invalid plans and failed tools cannot cause invented records or false claims of external actions.
- Traces identify the model roles, node sequence, selected tools, and evidence used.

## Submission checklist

- [ ] Four accounts, six tickets, and six notes are supplied as fictional data.
- [ ] Graph, tools, typed state, and review decisions are documented.
- [ ] Structured results include answers, evidence IDs, and review status/reasons.
- [ ] Eight query traces include multi-tool and missing-information cases.
- [ ] Planner/tool failure demonstrations and no-action behavior are verified.
- [ ] No live account changes, outbound messages, or embedded credentials are present.
