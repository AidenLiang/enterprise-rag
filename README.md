# Enterprise RAG

A small end-to-end Retrieval-Augmented Generation (RAG) system for answering questions from PDF documents.

The project implements a complete RAG pipeline from document parsing and chunking to vector retrieval, LLM-based reranking, answer generation, and evaluation.

## Overview

The system takes a PDF document as the knowledge source and answers user questions using only information retrieved from the document.

```text
PDF
 ↓
Parsing
 ↓
Chunking
 ↓
Embedding
 ↓
Vector Retrieval
 ↓
Top-K Candidates
 ↓
LLM Reranking
 ↓
Selected Context
 ↓
LLM Generation
 ↓
Evaluation
```

## Features

* PDF text extraction with PyMuPDF
* Text chunking with overlap
* Document metadata preservation
* Sentence-transformer embeddings
* Cosine-similarity based retrieval
* Top-K retrieval
* LLM-based reranking
* Context-grounded answer generation
* Component-level evaluation for retrieval, reranking, and generation

## Tech Stack

* Python
* PyMuPDF
* Sentence Transformers
* NumPy
* Ollama
* Llama 3.2 3B
* `all-MiniLM-L6-v2`

## Project Structure

```text
enterprise-rag/
├── app/
│   ├── parser/
│   │   └── pdf_parser.py
│   ├── chunking/
│   │   └── text_chunker.py
│   ├── retrieval/
│   │   └── retriever.py
│   ├── reranking/
│   │   └── reranker.py
│   ├── generation/
│   │   └── llm.py
│   ├── evaluation/
│   │   └── test_retrieval.py
│   ├── config.py
│   └── rag.py
│
├── data/
│   ├── raw/
│   │   └── description.pdf
│   └── processed/
│       ├── chunks.json
│       └── embeddings.npy
│
└── README.md
```

## Pipeline

### 1. PDF Parsing

The PDF is parsed page by page using PyMuPDF.

The parser preserves the page number so that retrieved information can later be traced back to the original document.

### 2. Chunking

The extracted text is divided into smaller chunks to make retrieval more precise.

Current configuration:

```text
Chunk size: 500
Overlap: 100
```

The sample document contains:

```text
12 pages
119 chunks
```

Each chunk also stores metadata such as:

```python
{
    "source": "description.pdf",
    "page": 1,
    "chunk": 1
}
```

### 3. Embedding

Each chunk is converted into a vector using:

```text
all-MiniLM-L6-v2
```

The embeddings are stored in:

```text
data/processed/embeddings.npy
```

The embedding at each position corresponds to the chunk at the same position in `chunks.json`.

### 4. Retrieval

The user's query is converted into an embedding and compared with the chunk embeddings using cosine similarity.

The retriever returns the Top-K most similar chunks.

For evaluation, the system uses:

```text
Top-K = 3
```

### 5. LLM Reranking

Semantic similarity does not always place the most useful chunk at rank 1.

The retrieved Top-K candidates are therefore passed to an LLM reranker.

The reranker receives:

```text
Question
Candidate 1
Candidate 2
Candidate 3
```

and returns the candidate number that most directly answers the question.

For example:

```text
Reranker answer: '2'
```

Python converts the candidate number to a list index:

```python
index = int(rerank_answer) - 1
```

The selected chunk is then used as the generation context.

### 6. Generation

The selected chunk is passed to the LLM together with the user's question.

The generator is instructed to answer using only the provided context.

The current local LLM is:

```text
llama3.2:3b
```

Temperature is set to:

```text
0
```

to reduce randomness in the evaluation.

### 7. Evaluation

The project evaluates the pipeline at multiple stages rather than only checking the final answer.

#### Retrieval

Five manually selected questions are used as an evaluation set.

Results:

```text
Recall@1: 80%
Recall@3: 100%
```

This means the correct page was included in the Top-3 for all five questions, while it was ranked first for four of the five questions.

#### Reranking

The reranker is evaluated based on whether the selected candidate comes from the expected page.

```text
Rerank Accuracy: 100%
```

#### Generation

Generated answers are evaluated by checking whether the expected facts appear in the answer.

```text
Generation Accuracy: 100%
```

Final evaluation:

| Component  | Metric              | Result |
| ---------- | ------------------- | -----: |
| Retrieval  | Recall@1            |    80% |
| Retrieval  | Recall@3            |   100% |
| Reranking  | Accuracy            |   100% |
| Generation | Fact-based Accuracy |   100% |

## Example

Question:

```text
What was the readmission rate for patients who had an HbA1c measurement compared with those who did not?
```

The retriever returns the Top-3 candidates.

The reranker selects:

```text
Page 4, Chunk 15
```

The selected context contains:

```text
measurement of HbA1c was associated with a significantly
reduced rate of readmission (9.4 versus 8.7%)
```

The generated answer is:

```text
The readmission rate for patients who had an HbA1c measurement
was 9.4%, and for those who did not, it was 8.7%.
```

The final response also reports the source:

```text
description.pdf, Page 4
```

## Evaluation and Observations

The evaluation demonstrates that retrieval and generation are separate problems.

In an earlier generation test, the model incorrectly selected a nearby numerical value when multiple percentages appeared in the same context.

For example, the context contained both:

```text
42.5%
55.0%
```

The correct value for the question was `55.0%`.

This demonstrates that retrieving the correct context does not guarantee that the generator will correctly interpret every piece of information in that context.

The evaluation also showed why reranking can be useful: the vector retriever identified relevant candidates, but the LLM reranker could reconsider the Top-K candidates based on whether they directly answered the question.

## Limitations

This project is a small baseline RAG system and has several limitations:

* The evaluation dataset contains only five questions.
* Retrieval uses a simple cosine-similarity approach.
* The reranker relies on an LLM rather than a dedicated cross-encoder reranker.
* Generation evaluation is based on expected-fact matching rather than a semantic evaluation model.
* The system currently works with a small local knowledge base.
* No persistent vector database is used.
* No web interface or production serving layer is included.

These limitations leave room for future improvements such as larger evaluation datasets, hybrid retrieval, dedicated reranking models, vector databases, and more robust answer evaluation.

## How to Run

Create and activate the virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

Run the PDF parser:

```bash
python -m app.parser.pdf_parser
```

Run the evaluation:

```bash
python -m app.evaluation.test_retrieval
```

Run the end-to-end RAG pipeline:

```bash
python -m app.rag
```

Make sure Ollama is installed and the configured model is available locally before running generation.

## Key Takeaway

This project implements and evaluates an end-to-end RAG pipeline:

```text
Document
→ Parse
→ Chunk
→ Embed
→ Retrieve
→ Rerank
→ Generate
→ Evaluate
```

The main focus of the project is understanding how each component contributes to the final answer and how to identify errors at different stages of the RAG pipeline.
