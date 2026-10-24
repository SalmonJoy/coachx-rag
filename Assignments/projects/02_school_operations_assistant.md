# Project 02: School Operations Assistant

**Difficulty:** Intermediate  
**Estimated effort:** 8–16 hours

## Scenario

A fictional school administrator asks questions across grades, attendance, assignments, teacher schedules, and subject notes. Build an agent that chooses appropriate dummy tools and explains what the returned records actually show.

## Learning objectives

- Plan and execute multiple tool calls through LangGraph.
- Separate routing from evidence-based answer generation.
- Handle static data limitations, invalid plans, and missing records.

## Prerequisites

Assignments 08–09 or equivalent graph/tool knowledge. Reuse the [school sample data](../../langGraph/sample_school_data.py) and four tools referenced by the [school graph](../../langGraph/school_agent_graph.py). Both model roles need callable Ollama Cloud access.

## Minimum implementation requirements

1. Preserve the four existing tool names and signatures: `fetch_sql_data(query)`, `call_external_api(endpoint)`, `search_vector_db(search_query)`, and `fetch_google_sheet_data(sheet_name)`. Keep them static; no real databases or accounts are required.
2. Use an explicit graph for configuration, planning, tool execution, and answer generation. Default to configurable GPT-OSS 20B for routing and GPT-OSS 120B for final answers.
3. Let the router select multiple calls, including repeated use of a tool with different arguments. Validate the complete plan against a registry before executing it.
4. Record selected tools, arguments, returned evidence, model roles, and failures in a sanitized trace. Explain that the SQL tool returns static joined rows and does not execute arbitrary SQL.
5. Ground answers in returned rows/notes and cite the supplying tools. Use thresholds and reference dates explicitly supplied by the user; do not invent school policy or assume historical assignments are currently due.
6. On a malformed router plan, return a readable planning error without executing tools. On a tool failure, preserve available results and clearly identify the missing evidence in the final response. Do not silently replace failed records with invented data.
7. Provide a CLI that accepts a question. A web interface is not required.

## Sample inputs and demonstration scenarios

| Scenario | Query or action | Observable expected behavior |
| --- | --- | --- |
| Structured records | “Which students have an algebra score below 85?” | Grade evidence is fetched; comparisons use 85, not an inferred intervention rule. |
| Multiple tool calls | “Show recorded absences and all assignment due dates.” | Attendance and assignment records are fetched separately and attributed. |
| Mixed evidence | “Who teaches science, and what do the science notes cover?” | Teacher/subject data and subject-note evidence are both used. |
| Missing information | “What is Aarav's parent phone number?” | The answer says the supplied records do not contain it. |
| Invalid plan | Inject a controlled unregistered tool name | No unregistered tool executes; the graph reports the planning error. |
| Tool failure | Make one selected tool raise a controlled exception | Trace records it; the answer distinguishes available facts from unavailable evidence. |

Prepare eight demonstration queries: two structured-record questions, two spreadsheet questions, two mixed-tool questions, and two unsupported questions. Judge tool choice by whether its returned data supports the request, rather than requiring one exact plan.

## Deliverables

Submit the graph, tool imports or compatible copies, dependency/configuration files, a state-and-edge diagram, run instructions, eight query traces, and a short limitations report. Include controlled failure demonstrations separately from normal model runs.

## Acceptance criteria

- All four tools are exercised across the demonstrations, with at least one multi-call run.
- Both model roles are visible in the trace and final answers use only returned evidence.
- Named students, subjects, dates, and scores agree with the data.
- Unsupported requests and tool failures remain explicit.
- Malformed plans cannot execute unknown tools or generated Python/SQL.

## Submission checklist

- [ ] Graph code, dependencies, and configuration template are included.
- [ ] All tools remain dummy and their behavior is documented.
- [ ] Diagram and eight query traces are provided.
- [ ] Multi-tool, missing-data, invalid-plan, and tool-failure cases are demonstrated.
- [ ] Answers identify tool evidence and avoid invented school policies.
- [ ] Credentials and real personal information are excluded.
