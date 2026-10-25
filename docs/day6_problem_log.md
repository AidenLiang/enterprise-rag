# Enterprise PDF RAG — Day 6 Experiment & Problem Log

**Stage:** Day 6 — Controlled Baseline vs. Agentic Retrieval Comparison  
**Branch used for the controlled experiment:** `feature/agentic-rag`  
**Experiment command:** `python -m app.evaluation.day6_compare`  
**Status:** Controlled comparison complete; one evaluation false negative investigated and documented.

## 1. Objective

Evaluate whether adding an Agent loop (evidence assessment, query rewriting, and one retry) improves RAG behavior when other major components are held constant. Record quality, LLM call counts, latency, and failure cases. Do not tune the model or change prompts in response to individual test outcomes.

## 2. Experimental design and scope

- **Baseline (controlled):** One retrieval with `top_k=3`, `threshold=0.5`; no Agent loop.
- **Agentic (controlled):** `run_agent(..., max_retries=1, top_k=3)`; evidence assessment, optional query rewrite, and at most one retry; cumulative candidates are merged/deduplicated.
- **Shared components:** Same `Retriever`, `LLM` (`llama3.2:3b`), embedding configuration (`all-MiniLM-L6-v2`), Reranker prompt and index parser, generation prompt, five questions, target evidence locations, and evaluation predicates.
- **Shared answer-generation strategy:** Reranker-selected candidate first; append remaining retrieved candidates as labeled evidence; make a single generation call.
- **Metrics:** Expected evidence location hit, selected `(page, chunk)` accuracy, generation test pass, calls to `LLM.generate`, elapsed time.
- **Evaluation rule:** Generation passes when **all expected fact strings** are found in **both** the combined generation context and the generated answer. This is a lightweight exact-string test, not a general semantic-factuality metric.

**Important scope distinction:** This Baseline ran on the **Agentic code branch**, with the Agent step disabled. It was **not** an execution of the historical `main` branch. A separate, full `main` vs. `feature/agentic-rag` comparison was not performed during this run. The historical `main` version also uses a single-Chunk generation strategy, and its old evaluation script uses a different retrieval threshold (`-1`) and page-only Rerank scoring; its scores are **not directly comparable** to this experiment.

## 3. Raw controlled-run results

| Metric | Baseline | Agentic |
|---|---:|---:|
| Questions | 5 | 5 |
| Expected evidence hit rate | 0.80 (4/5) | 1.00 (5/5) |
| Rerank accuracy (exact expected `(page, chunk)`) | 0.60 (3/5) | 0.80 (4/5) |
| Automatic generation pass rate | 0.60 (3/5) | 0.80 (4/5) |
| Average LLM calls per question | 1.60 | 4.00 |
| Average latency | 1.30 s | 3.11 s |

**Cost observation:** Agentic used **2.5× as many LLM calls** and took approximately **2.39× as long** on average in this single small run. Latency is environment-dependent; LLM call count is not equivalent to token or monetary cost.

### Per-question findings

| ID | Question topic | Baseline generation test | Agentic generation test | Main observation |
|---|---|---|---|---|
| Q1 | Database name | FAIL | PASS | Initial retrieval found no evidence above threshold; Agent rewrote the query and recovered the expected evidence on attempt 2. |
| Q2 | Early readmission definition | PASS | PASS | Both answered; both selected a neighboring rather than the expected exact Chunk. Multi-Chunk context preserved the definition. |
| Q3 | Medication change after HbA1c order | PASS | PASS | Both answered with 55.0%; Agentic retried and incurred extra calls/latency without an observed accuracy benefit. |
| Q4 | Final encounter count | PASS | PASS | Both answered 69,984; Agentic incurred one extra evidence-assessment LLM call. |
| Q5 | Readmission rates for tested vs. untested patients | FAIL | FAIL | The automatic generation test rejected **both** outputs; manual inspection found a false-negative evidence string match and different correctness of the two generated answers. |

## 4. Root-cause investigation: Question 5

**Question:** "What was the readmission rate for patients who had an HbA1c measurement compared with those who did not?"

**Raw context from `description.pdf`, Page 4 / Chunk 15:**

> Measurement of HbA1c was associated with a significantly reduced rate of readmission (9.4 versus 8.7%, P = 0.007).

**Corroborating evidence from Page 6 / Chunk 1 (Table 3):** The row **"No test was performed"** reports a **9.4%** readmission rate. Together with the reduced rate reported in Page 4 / Chunk 15, the available text supports **no HbA1c test: 9.4%; with HbA1c test: 8.7%**.

**The actual responses:**

- **Baseline:** Claimed tested patients: **9.4%**, untested: **8.7%**. The group-to-rate correspondence was reversed relative to the evidence.
- **Agentic:** Claimed tested patients: **8.7%**, untested: **9.4%**. This matches the evidence reviewed.

**Why the automatic check still failed:**

```python
expected_facts = ["9.4%", "8.7%"]
evidence_supported = all(fact in context for fact in expected_facts)
```

The retrieved Page 4 / Chunk 15 contains **`9.4 versus 8.7%`**, not the contiguous string **`9.4%`**. Thus the literal evidence check yields `False` even when both rates are substantively present. This is an **evaluation false negative**, not proof that the Agentic answer was wrong. The tested generation contexts did not necessarily include the corroborating Page 6 table.

**Action taken:** Kept the **raw automatic results unchanged** and documented the manual review separately. We did **not** edit expected facts, rewrite prompts, or retroactively present a higher automatic score.

**Future improvement (not implemented in Day 6):** Normalize numerical expressions or use relation-aware checks verifying both the percentage and its associated patient group; avoid treating substring presence alone as factual grounding. Evaluate this under a fixed protocol and rerun all conditions if the scoring rule changes.

## 5. Additional findings and limitations

1. **Real recovery benefit (Q1):** The Agentic loop found relevant evidence after ordinary single-pass retrieval returned none. The extra LLM calls were justified for this example.
2. **Avoidable overhead (Q3):** Evidence assessment was conservative and caused a retry although Baseline already produced the expected answer.
3. **Same Reranker, different candidates:** The rise in overall Rerank accuracy (3/5 to 4/5) does **not** show that the Reranker model itself improved; it is largely attributable to an additional question reaching reranking with useful retrieved evidence.
4. **Retrieval success is not answer validity:** A candidate may contain the necessary numbers without supporting the correct grouping. Human review exposed an answer error that exact-string evaluation could miss.
5. **Very small sample:** Five questions, one run, model-dependent behavior. Treat these as exploratory observations, not general reliability or statistically significant improvements.
6. **Not a Git-branch benchmark:** The controlled comparison isolates whether the Agent is enabled within one codebase. The older `main` pipeline and evaluation have other differences, so do not market these numbers as head-to-head `main` vs. feature-branch measurements.
7. **Metrics reflect the implemented test:** The `Generation Pass Rate` is the code's exact-string-and-evidence predicate, not a comprehensive hallucination or semantic-accuracy score.

## 6. Interview-ready project explanation

> I built a controlled evaluation in which both RAG variants used the same embedding model, retrieval threshold, Reranker, generation prompt, and multi-Chunk context. The only main change was whether the retrieval step was run directly or through an Agent that could assess evidence, rewrite the query, and retry once. On five questions, the Agentic variant recovered one question whose initial retrieval returned no evidence, increasing the automatic generation pass rate from 3/5 to 4/5. The trade-off was higher average LLM calls (1.6 to 4.0) and latency (1.30 s to 3.11 s). I also audited an automatic false negative caused by PDF text formatting (`9.4 versus 8.7%` vs. the string `9.4%`), showing why a keyword-match test cannot replace relation-aware answer verification.

## 7. Day 6 conclusion

**Controlled experiment completed.** Keep the Day 4 multi-Chunk implementation and the Day 5 robustness baseline unchanged. Preserve the raw comparison results, document the Q5 false negative and relation-check limitations, and avoid additional prompt tuning solely to improve the five-question score. Further branch-level benchmarking or expanded evaluation, if undertaken later, must use a shared protocol and label its methodology separately.

**Suggested commit:** `Add Day 6 controlled comparison and evaluation log`  
**Suggested repository location:** `docs/day6_problem_log.md`
