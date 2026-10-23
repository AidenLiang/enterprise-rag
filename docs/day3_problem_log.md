# Enterprise RAG --- Day 3 Problem Log

> **Record status:** Reconstructed from the available conversation
> history, not a verbatim transcript. The history contains multiple
> evaluation passes with different evaluation criteria. Keep those
> results separate; do not combine them into a single score. The final
> selected baseline was discussed, but the history says it was not
> directly restored/applied to the local files.

## Day 3 goal

Extend the original PDF RAG into an Agentic RAG workflow while
preserving the original RAG as a comparison baseline. The stated
requirement was to make retrieval more reasonable without allowing
quality to regress.

The intended flow included query rewriting, a bounded retry
(`max_retries=1`), retrieval over multiple attempts, cumulative
candidate merging and deduplication, evidence-sufficiency assessment,
reranking against the original question, and final answer generation.

## Work completed / confirmed

-   Integrated the Agentic RAG orchestration across multi-round
    retrieval, candidate merging/deduplication, evidence assessment,
    retry, reranking, and generation.
-   Added or exercised tests for candidate merging/deduplication and
    reranker-output parsing.
-   **19 unit tests passed** in the recorded test run.
-   Evaluated Agentic RAG on a five-question set and compared it with
    the traditional RAG baseline.
-   Used a stricter evaluation that checked the selected
    `(page, chunk)`, rather than checking only whether the correct page
    appeared.

## Problem log

### 1. Reranker output format was not parsed robustly

**Observed behavior**

The reranker returned `Candidate 2.`. The old parser rejected the output
and fell back to candidate index `0`, selecting Page 1 / Chunk 1. The
downstream answer was `I don't know.`

**Cause**

The parser expected a plain numeric response and did not reliably handle
the model's labeled response format.

**Fix direction / test coverage**

-   Accept supported formats such as `2` and `Candidate 2.` (including
    simple punctuation variants).
-   Validate that the parsed index is in range.
-   Reject arbitrary explanatory text rather than silently treating it
    as a valid index.
-   A recorded unit-test run passed the reranker parsing tests.

**Status note:** Although the parser fix was discussed and parsing tests
passed, the final baseline choice was not directly applied/restored to
the local files according to the saved conversation. Verify the current
code before claiming the fix is present in the repository.

### 2. Retrieval coverage did not guarantee correct chunk selection or answer quality

**Observed behavior**

The agent could retrieve expected evidence, but strict chunk-level
reranking and final generation did not always pass. A correct page-level
retrieval result was not sufficient to prove that the exact evidence
chunk was selected or used by the generator.

**Evaluation implication**

Keep these checks separate:

1.  Was the expected evidence retrieved?
2.  Did the reranker select the correct `(page, chunk)`?
3.  Did the generated answer use the evidence and answer the question
    correctly?

### 3. Evidence assessment and generation could disagree

**Observed behavior**

-   The medication-change question used two retrieval attempts, but the
    evidence assessor judged the accumulated evidence insufficient.
-   The readmission-rate question used two attempts and accumulated four
    candidates. Evidence was still judged insufficient, yet the
    generation evaluation passed.

**Why it matters**

The workflow's evidence-sufficiency decision and its
generation/evaluation result were not fully aligned. This should be
investigated rather than assuming that a passing generation check means
the evidence assessment was correct.

### 4. Multi-round retrieval needed explicit handling and traceability

The recorded five-question run had the following attempt counts and
cumulative candidate counts:

  ----------------------------------------------------------------------------------
  Test case                            Attempts           Cumulative Recorded note
                                                          candidates 
  ------------------------ -------------------- -------------------- ---------------
  Database-related                            2                    2 First attempt
  question                                                           returned no
                                                                     results; second
                                                                     returned two

  Readmission-definition                      1                    3 Completed in
  question                                                           one attempt

  Medication-change                           2                    3 Evidence
  question                                                           assessed as
                                                                     insufficient

  Unidentified test case                      1                    2 The saved notes
                                                                     do not preserve
                                                                     its question
                                                                     text

  Readmission-rate                            2                    4 Evidence
  question                                                           assessed as
                                                                     insufficient
                                                                     although
                                                                     generation
                                                                     passed
  ----------------------------------------------------------------------------------

The exact fifth-question text is not preserved in the available notes,
so it is intentionally not reconstructed.

### 5. Evaluation criteria and prompts needed to be consistent

The project history flags two risks:

-   Page-level checking can overstate reranker correctness when the
    intended evaluation is exact `(page, chunk)` selection.
-   The prompt used in the traditional retrieval test differed from
    `retriever.build_prompt()`, so results may not be directly
    comparable unless the evaluation path and prompt are standardized.

An earlier `30 days` versus `30-day` string-matching issue also showed
that an overly literal expected-answer matcher can fail a semantically
correct answer. Expected-answer checks should be specific enough to
avoid false positives without requiring an exact surface form.

### 6. Empty candidate lists require a safe path

The history identifies indexing into an empty candidate list as an edge
case to check. The available record does not establish whether this
guard was finally implemented in the local code; verify before marking
it resolved.

## Evaluation record --- keep separate runs separate

### Earlier Agentic RAG evaluation

The recorded five-question run reported:

-   Attempts per test case: `2, 1, 2, 1, 2`
-   Cumulative candidate counts: `2, 3, 3, 2, 4`
-   Rerank Accuracy: `1.0`
-   Generation Accuracy: `0.8`

The historical notes also contain different baseline scores from
different evaluation passes. Do not compare these numbers unless the
question set, prompt, candidate definition, and scoring criteria are the
same.

### Later strict chunk-level evaluation

The later Day 3 stage summary reported:

-   Expected evidence retrieval: **5/5**
-   Strict chunk-level Rerank Accuracy: **0.8**
-   Generation Accuracy: **0.6**

This later evaluation exposed two remaining quality gaps: exact chunk
selection was not always correct, and generation did not always make
effective use of available evidence. These scores apply to the small
development test set only and are not a general performance guarantee.

## Baseline decision and repository status

The selected comparison baseline was:

-   A simple reranker prompt.
-   A tolerant but validated reranker-output parser.
-   Cumulative Agentic retrieval with merging/deduplication.
-   Strict evaluation, including exact `(page, chunk)` checks.
-   Original RAG retained as the non-regression comparison.

The conversation explicitly records that this baseline decision was
**not directly applied/restored to the local files**. No confirmed Day 3
Git commit or push status is preserved in the available history. Check
`git status` and the diff before publishing code changes; do not claim
the selected baseline is already committed or pushed.

## Day 3 conclusion

The Agentic RAG workflow was integrated and its unit tests passed, but
passing unit tests did not establish that end-to-end answer quality had
improved. The later strict evaluation showed full expected-evidence
retrieval (5/5), while chunk-level reranking reached 0.8 and generation
reached 0.6. The appropriate next step recorded in the discussion was to
preserve a clear original-RAG baseline, inspect the failure cases, and
avoid adding more features until the quality regression and evidence-use
issues were understood.
