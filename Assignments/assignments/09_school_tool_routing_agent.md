# Assignment 09: School Tool-Routing Agent

**Difficulty:** Intermediate  
**Estimated effort:** 3–5 hours

## Scenario

A school assistant must choose between structured records, profile/schedule data, subject notes, and spreadsheet-like data. Let a smaller model select tools and a larger model explain their outputs.

## Learning objectives

- Expose static functions as LangChain tools.
- Validate a model-generated tool plan before execution.
- Ground final answers in one or more tool results.

## Prerequisites

Assignment 08 and access to both Ollama Cloud GPT-OSS models. References: [school graph](../../langGraph/school_agent_graph.py) and [sample data](../../langGraph/sample_school_data.py).

## Requirements

1. Reuse `fetch_sql_data(query)`, `call_external_api(endpoint)`, `search_vector_db(search_query)`, and `fetch_google_sheet_data(sheet_name)` without changing their signatures or replacing static data with live systems.
2. Build nodes for configuration, planning, tool execution, and final generation. Use configurable `gpt-oss:20b-cloud` for planning and `gpt-oss:120b-cloud` for answers, subject to account availability.
3. Let the router select one or more tools and arguments. Validate tool names and arguments against a registry; never evaluate arbitrary generated code.
4. For invalid JSON or invalid tool selections, clearly log a fallback to vector-note search with the original query. Preserve the reason in the run trace.
5. Print selected tools and arguments, capture their outputs, and instruct the final model to cite tool names and acknowledge missing facts.
6. Respect the mock tools' actual behavior: SQL returns static joined rows, and sheet/API tools choose broad payloads from argument text. Inspect returned rows rather than claiming that arbitrary SQL or HTTP calls ran.

## Sample input and expected behavior

- “Which students have an algebra score below 85?” Expect grade data and comparisons using the explicit threshold.
- “Show recorded absences and assignment due dates.” Expect attendance and assignment data, potentially through two sheet calls.
- “Who teaches science, and what do the science notes cover?” Expect schedule/subject data plus note evidence.

Do not infer a school intervention policy or interpret historical dates as current deadlines unless the question supplies a reference date.

## Deliverables

Submit the graph, run guide, and traces for the three questions, one unsupported question, and one controlled invalid router output.

## Acceptance criteria

- Traces distinguish the routing and final-answer model roles.
- At least one run executes multiple tool calls and passes all results to generation.
- Answers are consistent with returned records and identify their tool evidence.
- Unsupported questions acknowledge missing data.
- Invalid plans trigger the documented fallback without invoking unregistered tools.
