# Enterprise RAG — Day 5 Problem Log

> **Focus:** Agentic RAG abnormal-case handling, fault tolerance, and regression testing  
> **Status:** Day 5 baseline tests completed; no production-code refactoring performed.

## 1. Day 5 objectives

Day 5 focused on verifying **what the system does when something goes wrong**, rather than increasing answer accuracy or tuning LLM prompts.

The six planned scenarios were:

1. Retrieval returns no documents.
2. Evidence is insufficient and the Agent must retry.
3. The Agent exhausts the allowed retries.
4. The LLM returns malformed or incorrectly typed evidence-assessment JSON.
5. The Reranker returns an invalid candidate number.
6. Different retrieval attempts return duplicate chunks.

The aim was to confirm safe exits, bounded retries, predictable fallback behavior, and correct deduplication through automated tests.

## 2. Initial baseline: 19 existing tests passed

Command:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

**Initial result:** `Ran 19 tests ... OK`.

Existing tests already covered much of the Day 5 scope:

| Area | Existing test coverage |
| --- | --- |
| Agent retry on insufficient evidence | `test_retries_when_evidence_is_insufficient` |
| Stop on sufficient evidence | `test_stops_when_evidence_is_sufficient` |
| Stop when retries are exhausted | `test_stops_when_retries_are_exhausted` |
| Merge results and remove duplicate chunks | `test_merges_new_results_in_order`, `test_removes_duplicate_chunks` |
| Empty evidence and malformed assessment JSON | `test_assess_evidence_handles_empty_results`, `test_assess_evidence_handles_invalid_json` |
| Reject malformed assessment field types | `test_assess_evidence_rejects_invalid_feedback_type`, `test_assess_evidence_rejects_invalid_field_type` |
| Validate Reranker response format | `tests/test_reranker.py` parser tests, including invalid format and out-of-range values |

**Gap identified:** Existing tests exercised the underlying components, but did not directly verify two critical behaviors at the `RAG.ask()` entry point: an empty retrieval result and an invalid Reranker number.

## 3. New integration-boundary unit tests: `tests/test_rag.py`

Two tests were added. Both call the **real `RAG.ask()` method**, but replace external dependencies with mocks; no live Retriever or Ollama call is required. These are isolated unit tests at the RAG entry point, **not** full end-to-end model tests.

### Problem 1 — No documents retrieved

**Failure scenario:** The Agent returns no candidate evidence.

**Test:** `test_returns_unknown_when_no_documents`

**Setup:**

- Use `@patch("app.rag.run_agent")` to replace the function name actually used in `app/rag.py`.
- Configure its return value as `{"success": False, "results": []}`.
- Create a `RAG` instance via `RAG.__new__(RAG)` to avoid initializing live model dependencies; supply simple placeholders for `retriever` and `llm`.
- Call the real `RAG.ask()` method and inspect its return values.

**Expected behavior:**

```python
(
    "I don't know. No relevant information was found in the knowledge base.",
    None,
)
```

**Observed result:** `PASS`.

**Engineering conclusion:** When the cumulative candidate list is empty, `RAG.ask()` exits without trying to rerank or generate an answer. This checks the empty-result path only; it does not prove that the LLM will consistently refuse to answer when *nonempty but irrelevant* evidence is present.

### Problem 2 — Invalid Reranker output

**Failure scenario:** The system has **two** candidate chunks, but the LLM-based Reranker returns the invalid choice `"99"`.

**Test:** `test_fallback_when_reranker_returns_invalid_index`

**Setup:**

- Patch `run_agent()` to return two synthetic results with `text`, `metadata`, and `score`.
- Use `MagicMock` for the Retriever and LLM dependencies.
- Set `llm.generate.side_effect = ["99", "The database is Health Facts."]`, modeling a Reranker call followed by a generation call.
- Mock `retriever.build_prompt()` and call the real `RAG.ask()`.

**Observed output:**

```text
Agent success: True
Using cumulative retrieval results.
Reranker answer: '99'
Warning: invalid reranker output. Using top retrieval result.
Selected index: 0
Selected page: 2
Selected chunk: 2
ok
```

**Observed result:** `PASS`.

**Checks verified:**

- The invalid result is detected by `parse_rerank_index()`.
- The pipeline falls back to the first retrieved candidate, `index = 0`.
- The selected source is Page 2 / Chunk 2.
- Answer generation continues and returns the configured response.
- The mocked LLM's `generate()` method is called twice (rerank, then generate).

**Engineering conclusion:** The system handles an invalid Reranker selection without throwing an index error. This is a **graceful-degradation / availability fallback**, not a guarantee of answer accuracy. In particular, falling back to the first retrieved candidate may still select an unsuitable source.

## 4. Python testing concepts learned

### `@patch("app.rag.run_agent")`

The decorator temporarily replaces the `run_agent` name **at the lookup location used by `RAG.ask()`**. Because `rag.py` imports `run_agent` with `from app.agent.agent import run_agent`, patching `app.rag.run_agent` intercepts calls in that module. The original is restored after the test.

### `RAG.__new__(RAG)`

Creates an instance without running `RAG.__init__()`. This avoids loading/initializing the project's real Retriever and LLM in tests that only need to exercise a small control-flow branch. Required attributes are supplied manually. This is a focused testing technique, not the usual way to instantiate `RAG` in application code.

### `MagicMock` and `side_effect`

- `return_value`: the value returned by a mocked call.
- `side_effect = [first, second]`: consecutive calls return different configured values.
- Mocked dependencies make the abnormal path fast, deterministic, and independent of LLM variability.

## 5. Final regression run

Command:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

**Final result:**

```text
----------------------------------------------------------------------
Ran 21 tests in 0.002s

OK
```

All 21 listed tests passed, including both new `tests/test_rag.py` cases.

### Day 5 scenario coverage summary

| Scenario | Validation | Status |
| --- | --- | --- |
| Retrieval returns no documents | `RAG.ask()` returns unknown answer and `None` | PASS |
| Insufficient evidence triggers retry | `test_retries_when_evidence_is_insufficient` | PASS |
| Retries exhausted | `test_stops_when_retries_are_exhausted` | PASS |
| Invalid assessment JSON / types | `tests/test_agent_tools.py` assessment tests | PASS |
| Invalid Reranker choice | `RAG.ask()` falls back to index `0` | PASS |
| Duplicate candidates | `merge_results()` deduplication tests | PASS |

**Interpretation:** All planned abnormal-case scenarios now have passing automated **unit-test coverage**. The results do not establish complete end-to-end reliability, semantic correctness of every generated answer, or resilience to all external failures.

## 6. Limitations and deferred work

- **Evaluation sample size:** The Day 4 answer-quality evaluation uses only five questions; its reported metrics are not population-level accuracy estimates. Day 5's 21 tests measure software behavior, not answer accuracy.
- **Evidence sufficiency judgment:** The LLM-based assessor can reject sufficient evidence or accept incomplete evidence. Existing tests verify JSON handling and retry control flow, not the real-world quality of its semantic judgment.
- **Fallback accuracy:** Choosing index `0` after an invalid Reranker output keeps the system running but may not produce the best answer.
- **Source-grounded claims:** Text-based checks for expected facts cannot fully validate numerical condition-to-group mappings or detect every unsupported statement.
- **Untested runtime failures:** Timeouts, interrupted Ollama connections, model-loading failures, or unexpected external errors were not established as covered by these tests.
- **Duplicate orchestration logic:** `app/evaluation/test_agentic_rag.py` currently implements its own evaluation pipeline instead of calling `RAG.ask()` directly; future refactoring could expose diagnostic information from the production pipeline and remove duplication. **No refactor was made on Day 5.**

## 7. Day 5 decision

**Day 5 is complete for the agreed six-scenario basic fault-tolerance scope.**

- Keep the Day 4 multi-chunk context baseline unchanged.
- Preserve the existing Agent and Reranker behavior; do not reopen prompt tuning.
- Add `tests/test_rag.py` to the test suite.
- Record results honestly: **21 / 21 automated tests passed** in the final regression run.
- Move on to the next planned project work rather than repeatedly optimizing single questions.

## 8. GitHub handoff

Suggested repository path:

```text
docs/day5_problem_log.md
```

Suggested Git commands **after reviewing `git status`**:

```bash
git add docs/day5_problem_log.md tests/test_rag.py
git diff --cached --stat
git commit -m "Add Day 5 fault tolerance tests and problem log"
git push
```

> This document records a local test run provided by the developer. It does **not** assert that these files have already been committed or pushed to GitHub.
