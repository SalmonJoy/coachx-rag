# Project 03: LLM Evaluation Workbench

**Difficulty:** Intermediate  
**Estimated effort:** 8–16 hours

## Scenario

A team wants to compare two Ollama Cloud models before selecting one for an application. Build a repeatable evaluation workbench that measures MCQ accuracy and constraint following, and makes individual failures easy to inspect.

## Learning objectives

- Discover callable models and separate evaluated-model and judge roles.
- Preserve reproducible evaluation inputs, settings, outputs, and errors.
- Compare exact-match metrics with judge-based assessments critically.

## Prerequisites

Assignment 10, Python JSONL processing, and access to two distinct callable Ollama Cloud chat models. Start from the [evaluation material](../../LLM_evaluation/). Use the supplied financial-services MCQ and instruction-constraint datasets unchanged; the math dataset is an optional extension.

## Minimum implementation requirements

1. Provide a CLI that lists verified callable models and lets the user select two evaluated models and a judge. Model names and API configuration must remain configurable; the judge may equal an evaluated model.
2. Validate both datasets before running. Offer a five-item-per-dataset smoke mode and a full mode with the same tasks and ordering for both evaluated models.
3. Grade MCQs against stored option keys. Mark invalid/empty final answers unsuccessful and retain the raw response; never use internal thinking as an answer.
4. For constraint tasks, supply explicit constraints to the evaluated model and checks to the judge. Treat the evaluated response as evidence, not as instructions for the judge. Validate JSON verdict types, score bounds, failed checks, and reason; flag malformed or contradictory verdicts as judging errors.
5. Save each completed result incrementally in a unique run directory. Include task ID, evaluated model, judge when applicable, output, verdict or expected answer, status, and error details. Record model settings and dataset hashes in run metadata.
6. Report overall/per-topic MCQ accuracy and overall/per-category constraint pass rate and mean score. Headline rates include all attempted tasks; errors count as unsuccessful and as zero score for the aggregate constraint mean, with error counts separately visible.
7. Generate a Markdown comparison report with a summary table and examples of incorrect answers, failed constraints, and service errors when present. A browser dashboard is not required.

## Sample inputs and demonstration scenarios

| Scenario | Input or action | Observable expected behavior |
| --- | --- | --- |
| Smoke comparison | Five MCQs and five constraint tasks for each model | Exactly 20 task-result records, plus separate run metadata. |
| Full comparison | 100 MCQs and 25 constraint tasks for each model | Exactly 250 task-result records across both models. |
| Missing information | Simulate an empty final model response | The missing answer is recorded as unsuccessful; no answer is inferred from hidden thinking or invented for the judge. |
| Missing configuration | Remove the API key from a controlled test environment | A clear configuration error appears before evaluation. |
| Invalid input | Use a temporary dataset copy with a missing answer/check list | Validation stops before any evaluated-task model calls. |
| Service failure | Simulate one generation timeout | That task has an error record and later tasks continue. |
| Judge failure | Supply a controlled malformed judge response | A judging error is retained and is not counted as a pass. |

If account limits prevent a full comparison, submit the working smoke run and state that the full comparison is incomplete. Do not substitute simulated scores for live measurements. A correctness-focused report is more important than claiming a winning model.

## Deliverables

Submit the workbench, dependencies, configuration template, run guide, smoke results, full results when available, run metadata, and generated comparison report. Include a short critique of answer-key distribution, judge variability, and the limits of these sample datasets.

## Acceptance criteria

- Saved task IDs and settings show that both models received equivalent evaluation inputs.
- Metrics recomputed from saved records match the report, including error denominators.
- Separate runs cannot silently overwrite earlier results.
- Controlled generation/judge failures preserve evidence and do not terminate remaining tasks.
- Conclusions distinguish measured performance on these datasets from general model capability.

## Submission checklist

- [ ] Model selection, dataset validation, and both evaluation modes are implemented.
- [ ] Smoke comparison and clearly labeled full-run status are included.
- [ ] Incremental results, metadata, and reproducible metrics are provided.
- [ ] Comparison report includes failure examples and evaluation limitations.
- [ ] Controlled timeout and malformed-judge cases are demonstrated.
- [ ] No API keys appear in results, metadata, logs, or source.
