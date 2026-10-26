# Enterprise RAG: From Traditional RAG to Agentic RAG

An end-to-end Retrieval-Augmented Generation (RAG) project built with Python, Sentence Transformers, and a local LLM served by Ollama.

This project explores how an Agentic RAG workflow can improve evidence retrieval through evidence assessment, query rewriting, cumulative result merging, and controlled evaluation.

## 1. Project Overview

The project starts with a traditional RAG pipeline and extends it with an agent-driven retrieval workflow.

The system uses a PDF document as its knowledge source. It extracts and chunks the document, generates embeddings, retrieves relevant passages, reranks candidate evidence, and generates answers grounded in the retrieved context.

The Agentic RAG implementation adds a decision loop that assesses whether the retrieved evidence is sufficient. If the evidence is insufficient, the agent can rewrite the query and retry retrieval within a configurable retry limit.

## 2. Architecture

### Traditional RAG

The original implementation on the `main` branch follows a fixed pipeline:

```text
PDF Document
     |
     v
Parsing and Chunking
     |
     v
Embedding Generation
     |
     v
Vector Retrieval
     |
     v
Top-K Candidates
     |
     v
LLM Reranking
     |
     v
Selected Chunk
     |
     v
Answer Generation
```

### Agentic RAG

The `feature/agentic-rag` branch adds an evidence assessment and query-rewriting loop.

```text
User Question
     |
     v
Initial Retrieval
     |
     v
Evidence Assessment
     |
     +---- Sufficient ----> Stop Retrieval
     |
     +---- Insufficient
                |
                v
          Query Rewriting
                |
                v
          Retry Retrieval
                |
                v
       Merge and Deduplicate
                |
                +----> Evidence Assessment
                |
                v
        Retry Limit Reached
                |
                v
       Return Available Evidence
                |
                v
          LLM Reranking
                |
                v
     Selected Chunk First
                |
                v
       Multi-Chunk Context
                |
                v
        Answer Generation
```

The agent stops when the evidence assessment reports sufficient evidence or the retry limit is reached.

When multiple retrieval attempts produce results, the system merges them and removes duplicate chunks before reranking.

If evidence remains insufficient after the retry limit, the system can still generate an answer from the available evidence. Consequently, agent success does not guarantee that the final answer is correct.

## 3. Key Features

- PDF parsing with PyMuPDF.
- Text chunking with overlap.
- Page, chunk, and source metadata preservation.
- Sentence Transformer embeddings.
- Cosine-similarity-based retrieval.
- Configurable Top-K retrieval and similarity threshold.
- LLM-based evidence assessment.
- Feedback-driven query rewriting.
- Cumulative retrieval result merging and duplicate removal.
- LLM-based candidate reranking.
- Reranker output validation and fallback handling.
- Multi-chunk context construction for answer generation.
- Unit tests for agent behavior, evidence assessment, reranking, and error handling.
- Controlled comparison between baseline and Agentic RAG retrieval workflows.

## 4. Tech Stack

| Component | Technology |
|---|---|
| Language | Python |
| PDF processing | PyMuPDF |
| Embeddings | Sentence Transformers |
| Embedding model | `all-MiniLM-L6-v2` |
| Vector similarity | NumPy / cosine similarity |
| Local LLM runtime | Ollama |
| Language model | `llama3.2:3b` |
| Testing | Python `unittest` |
| Version control | Git and GitHub |

## 5. Core Implementation

### 5.1 Document Processing

The PDF parser extracts document text page by page.

The chunking component divides the extracted text into smaller passages with overlap, helping preserve context across chunk boundaries.

The current sample document contains 12 pages and 119 chunks.

Each chunk retains metadata similar to:

```python
{
    "source": "description.pdf",
    "page": 1,
    "chunk": 1
}
```

### 5.2 Embedding and Retrieval

Each chunk is converted into an embedding using `all-MiniLM-L6-v2`.

The query is embedded using the same model. The retriever compares the query embedding against stored chunk embeddings using cosine similarity and returns the Top-K candidates.

The current evaluation configuration uses:

```python
TOP_K = 3
RETRIEVAL_THRESHOLD = 0.5
```

These parameters are configurable and can affect retrieval coverage.

### 5.3 Evidence Assessment and Query Rewriting

The agent evaluates the retrieved evidence against the original question.

The assessment component returns two fields:

- `sufficient`: whether the evidence contains enough explicit information to answer the question.
- `feedback`: an explanation of what evidence is missing or unclear.

If the evidence is insufficient, the query-rewriting component uses the feedback to produce a revised search query.

The agent then retrieves documents using the revised query.

The retry count is bounded to avoid unlimited retrieval loops.

### 5.4 Cumulative Result Merging

Different retrieval queries can return overlapping or complementary evidence.

The agent merges results from successive attempts and removes duplicates using source, page, and chunk metadata when available, with text-based deduplication as a fallback.

This preserves potentially useful evidence from earlier attempts instead of discarding it when a later query is executed.

### 5.5 LLM Reranking

The reranker receives the original question and the retrieved candidate passages.

It selects the candidate that most directly answers the question.

Because an LLM may return an invalid number or unexpected formatting, the output parser validates the response and checks whether the selected index is within range.

If the response is invalid, the system falls back to the first candidate rather than crashing.

### 5.6 Multi-Chunk Answer Generation

The selected candidate is placed first, followed by the other retrieved candidates.

Each passage is labeled with its page and chunk metadata before the passages are combined into a single context.

The generator then receives the original question and the combined evidence.

This design retains supporting information that might be absent from the highest-ranked chunk alone. However, additional context can also introduce irrelevant information or competing numerical values, so the generation results must be evaluated rather than assumed to improve.

## 6. Evaluation Methodology

The project uses five manually selected questions based on the sample research paper.

The questions cover:

1. The database used in the study.
2. The definition of early hospital readmission.
3. Medication changes associated with HbA1c testing.
4. The final number of encounters.
5. Readmission rates for patients with and without HbA1c measurements.

The evaluation separates several stages:

- **Evidence hit rate:** whether at least one expected evidence location was retrieved.
- **Rerank accuracy:** whether the selected candidate matched an expected evidence location.
- **Generation pass rate:** whether the expected facts appeared in both the generation context and the generated answer.
- **Average LLM calls:** the average number of `LLM.generate()` calls per question.
- **Average latency:** the average elapsed time per question.

The generation metric uses expected-fact matching rather than a semantic evaluator. It does not independently verify every claim, numerical relationship, or interpretation in an answer.

## 7. Day 6 Controlled Comparison

The following results are from the recorded five-question comparison run.

| Metric | Baseline | Agentic RAG |
|---|---:|---:|
| Evidence hit rate | 80% | 100% |
| Rerank accuracy | 60% | 80% |
| Generation pass rate | 60% | 80% |
| Average LLM calls | 1.60 | 4.00 |
| Average latency | 1.30 s | 3.11 s |

### Observations

**Evidence retrieval improved in this test set.**

The baseline retrieved expected evidence for four of the five questions, while Agentic RAG retrieved expected evidence for all five.

**Reranking and generation also improved in the observed run.**

Both metrics increased by 20 percentage points. However, reranking was evaluated using expected evidence locations, and generation was evaluated through expected-fact matching.

**The improvement came with additional computational cost.**

Agentic RAG used an average of 4.00 LLM calls per question, compared with 1.60 for the baseline. Average latency increased from 1.30 seconds to 3.11 seconds.

This reflects the additional LLM calls used for evidence assessment and query rewriting.

### Important Experimental Limitation

The comparison contains only five questions, so the results are preliminary and cannot establish general performance improvements.

The Day 6 comparison also uses the same downstream reranking and multi-chunk generation strategy for both conditions. It isolates the effect of enabling the agent-driven retrieval workflow rather than reproducing every detail of the untouched `main` branch's original single-chunk generation pipeline.

A larger evaluation set, repeated runs, and more robust answer-quality metrics would be needed for stronger conclusions.

## 8. Example: Readmission Rate Comparison

One evaluation question asks:

> What was the readmission rate for patients who had an HbA1c measurement compared with those who did not?

The retrieved paper states that HbA1c measurement was associated with a reduced readmission rate, reporting 9.4% versus 8.7%.

The corresponding interpretation is:

- Patients without an HbA1c measurement: 9.4%.
- Patients with an HbA1c measurement: 8.7%.

This example highlights an important RAG challenge: retrieving the correct numerical evidence does not guarantee that the generator will assign each number to the correct group.

The system must therefore be evaluated on factual accuracy and interpretation, not just evidence retrieval.

## 9. Project Structure

```text
enterprise-rag/
├── app/
│   ├── agent/
│   │   ├── agent.py
│   │   └── tools.py
│   ├── chunking/
│   ├── parser/
│   ├── retrieval/
│   │   └── retriever.py
│   ├── reranking/
│   │   └── reranker.py
│   ├── generation/
│   │   └── llm.py
│   ├── evaluation/
│   │   ├── test_retrieval.py
│   │   ├── test_agentic_rag.py
│   │   └── day6_compare.py
│   ├── config.py
│   └── rag.py
├── tests/
│   ├── test_agent.py
│   ├── test_agent_tools.py
│   ├── test_rag.py
│   └── test_reranker.py
├── data/
│   ├── raw/
│   └── processed/
├── docs/
│   ├── day1_day2_problem_log.md
│   ├── day3_problem_log.md
│   ├── day4_problem_log.md
│   ├── day5_problem_log.md
│   └── day6_problem_log.md
├── requirements.txt
└── README.md
```

## 10. How to Run

### Prerequisites

- Python and a virtual environment.
- Dependencies listed in `requirements.txt`.
- Ollama installed and running.
- The configured `llama3.2:3b` model available locally.

### Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Run the baseline evaluation

```bash
python -m app.evaluation.test_retrieval
```

### Run the Agentic RAG evaluation

```bash
python -m app.evaluation.test_agentic_rag
```

### Run the controlled comparison

```bash
python -m app.evaluation.day6_compare
```

### Run unit tests

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

### Run the RAG application

```bash
python -m app.rag
```

The application uses the configured local LLM. Ensure that the model is available through Ollama before running generation or evaluation commands.

## 11. Limitations and Future Work

- The evaluation dataset contains only five manually selected questions.
- Expected-fact matching is not a comprehensive measure of answer quality.
- LLM-based evidence assessment can make incorrect judgments.
- Query rewriting may not improve retrieval on every question.
- Multi-chunk contexts can contain conflicting or distracting evidence.
- LLM reranking and evidence assessment increase inference cost and latency.
- The project does not yet include a production web interface, persistent vector database, or large-scale evaluation pipeline.

Potential future improvements include larger benchmark datasets, hybrid retrieval, more robust evidence verification, dedicated reranking models, and more systematic latency and cost measurements.

## 12. Key Takeaway

This project demonstrates the transition from a fixed RAG pipeline to a retrieval workflow that can assess evidence, rewrite queries, retry retrieval, and combine evidence from multiple attempts.

The observed five-question experiment suggests that the agentic workflow can improve retrieval coverage and answer pass rates, while also increasing latency and LLM usage.

The central engineering lesson is that RAG quality depends on the entire evidence pipeline: retrieving relevant information, selecting useful passages, preserving supporting context, and generating an answer that interprets the evidence correctly.
