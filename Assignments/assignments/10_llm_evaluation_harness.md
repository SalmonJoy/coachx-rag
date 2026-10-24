# Assignment 10: LLM Evaluation Harness

**Difficulty:** Intermediate  
**Estimated effort:** 3–5 hours

## Scenario

Your team needs evidence when choosing a model. Compare two callable Ollama Cloud models on factual MCQs and explicit instruction constraints, using a separately selectable judge for the latter.

## Learning objectives

- Separate exact-match grading from model-based judging.
- Preserve per-item evidence and distinguish errors from incorrect answers.
- Compute reproducible overall and grouped metrics.

## Prerequisites

Python JSONL processing and Ollama Cloud access. References: [MCQ evaluator](../../LLM_evaluation/evaluate_ollama_mcq.py), [constraint evaluator](../../LLM_evaluation/evaluate_instruction_constraints.py), and their supplied datasets.

## Requirements

1. Validate the supplied financial-services MCQ and instruction-constraint datasets before evaluation. Keep the originals unchanged. Allow an explicit subset for smoke runs.
2. Display models verified callable for the configured account. Let the user select two distinct evaluated models and a judge; the judge may equal either evaluated model. Do not label an unavailable model as an evaluated run.
3. Evaluate both models on identical tasks. Prompt MCQ models for one answer letter and compare the final response against the answer key; never grade hidden thinking as the final answer.
4. For constraints, send the instruction and constraints to the evaluated model, then send its response plus judge checks to the judge. Require a boolean pass, score from 0 to 1, failed checks, and a reason. Accept plain or fenced JSON; reject malformed verdicts.
5. Save per-item outputs, raw judge verdicts, scores, correctness/pass flags, model names, and errors as separate results for each run. Save completed rows incrementally.
6. Report MCQ accuracy by topic and constraint pass rate/average score by category. Include errors as unsuccessful items in headline metrics and report their counts separately. Include selected settings and evaluated item counts.

## Sample input and expected behavior

A smoke run uses the first five MCQs and first five constraint tasks for both models. Expect 20 result records total across those evaluations; judge calls do not count as additional tasks.

For the final comparison, use all 100 financial MCQs and all 25 constraint tasks: 250 records total across two models. A model timeout must create an error record and allow later items to continue.

## Deliverables

Submit the evaluator, run guide, sanitized result artifacts, a comparison table, and a short discussion of dataset bias and judge limitations. If account limits block a full run, include the smoke results and clearly mark the full run incomplete.

## Acceptance criteria

- Both selections and the judge selection work; evaluated tasks are identical across models.
- Result counts reconcile with successes, failures, and service errors.
- Recomputing metrics from saved rows reproduces the displayed summary.
- A forced API failure and malformed judge response are recorded without stopping the run.
- The report distinguishes measured results from claims about general model quality.
