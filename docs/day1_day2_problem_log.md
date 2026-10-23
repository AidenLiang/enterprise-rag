# Enterprise RAG --- Day 1 & Day 2 Problem Log

> **Record status:** Reconstructed from saved project notes, not a
> verbatim export of the original chats. The available history does not
> preserve every day's exact boundary, command, or code diff. Items
> below are marked as confirmed from project history or as stage-level
> summaries where exact timing is uncertain.

## Day 1 --- Basic PDF RAG Pipeline

### Work completed

-   Built the initial local PDF question-answering pipeline: PDF parsing
    → chunking → embeddings → retrieval → prompt construction → LLM
    answer generation.
-   Used PyMuPDF for PDF parsing, `all-MiniLM-L6-v2` for embeddings, and
    Ollama with Llama 3.2 3B for local generation.
-   Used chunk metadata such as `source`, `page`, and `chunk` so
    retrieved evidence could be traced back to the document.
-   The recorded chunking configuration was `chunk_size=500` and
    `overlap=100`; retrieval used Top-K candidates, with `top_k=3` used
    in testing.

### Problems and resolutions

1.  **PDF path was incorrect.** A path written as
    `/data/raw/description.pdf` was treated as an absolute path and
    could not be found; use the repository-relative path
    `data/raw/description.pdf` when running from the project root.
2.  **Python module imports depended on the launch location.** Running a
    module from the wrong working directory caused import issues; run
    commands from the repository root using module execution, for
    example `python -m app.parser.pdf_parser`.
3.  **The pipeline's separate stages needed to be understood and
    connected.** The project was developed as distinct parsing,
    chunking, embedding, retrieval, prompt, and generation steps before
    being wrapped into a unified RAG interface.

### Day 1 outcome

The basic PDF-to-answer pipeline was recorded as working. The saved
notes do not preserve a complete Day 1 test transcript or exact list of
all code changes.

## Day 2 --- RAG Integration and Evaluation

### Work completed

-   Continued organizing the retrieval, reranking, and generation
    components into a usable RAG flow, including work on a unified
    `RAG.ask()` interface.
-   Added LLM-based reranking to choose a candidate passage before
    answer generation.
-   Added a small evaluation set of approximately five questions to
    check retrieval, reranking, and answer generation.
-   Preserved page/chunk metadata to make selected evidence and answer
    sources traceable.

### Problems and resolutions

1.  **A text-matching test was too sensitive to wording.** One
    evaluation case failed because the expected text used `30 days`
    while the generated answer used `30-day`; the matching expectation
    was adjusted, after which the case passed. This was a
    string-matching issue and did not by itself prove a change in model
    quality.
2.  **Evaluation metrics measured different stages.** Retrieval
    hit/Recall, reranker selection accuracy, and generation correctness
    were treated as separate checks; a correct retrieved page does not
    automatically mean the selected chunk or final answer is correct.
3.  **Small-sample results needed cautious interpretation.** The
    historical five-question evaluation recorded Recall@1 = 80%,
    Recall@3 = 100%, rerank accuracy = 100%, and generation accuracy =
    100% after the text-match adjustment. These results apply only to
    that small test set and should not be presented as a general
    performance guarantee.

### Git checkpoint

The saved project history notes a Day 2 commit `11f58b4`; at that point,
the local branch was one commit ahead of the remote, the working tree
was clean, and that commit had not yet been pushed. Confirm the current
Git state before relying on this as the present status.

## Issues deliberately not assigned to Day 1 or Day 2

The following appeared in later Agentic RAG debugging, or their exact
timing cannot be verified from the saved notes. They should remain in
the Day 3 log unless the original history confirms otherwise:

-   Merging and deduplicating results across multiple retrieval
    attempts.
-   Evidence assessment and query rewriting when retrieval results are
    empty or insufficient.
-   Reranker output parsing when the model returns formats such as
    `Candidate 2.` instead of a plain number.
-   Handling an empty candidate list before indexing into retrieval
    results.
-   Differences between the prompt used by the traditional retrieval
    test and `retriever.build_prompt()`.
-   Evaluating the exact selected `(page, chunk)` rather than checking
    only the page.
-   Instability across repeated LLM runs and false positives caused by
    overly broad expected-answer strings.

## Notes for future continuation

-   Keep this log as a record of the development process, not as a claim
    that every issue was definitively fixed.
-   Before publishing, check that the listed configuration and
    historical Git state still match the repository.
-   Keep Day 1/Day 2 history separate from the Day 3 Agentic RAG
    baseline and its later evaluation results.
