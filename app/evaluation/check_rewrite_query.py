
from app.generation.llm import LLM
from app.agent.tools import rewrite_query
from app.retrieval.retriever import Retriever
from app.agent.tools import retrieve_documents


def main():
    # 1. Create the real LLM
    llm = LLM()

    # 2. Prepare the original question
    query = "What database was used in the study?"

    # 3. Simulate feedback from a failed retrieval
    feedback = "No documents were retrieved."
    # 4. Call the real query rewriting function
    rewritten_query = rewrite_query(
        llm,
        query,
        feedback
    )

    # 5. Inspect the output
    print("\n===== Query Rewrite Test =====")
    print("Original query:", repr(query))
    print("Feedback:", repr(feedback))
    print("Rewritten query:", repr(rewritten_query))

    # 6. Check for the placeholder found previously
    lower_query = rewritten_query.lower()

    if (
        "[insert" in lower_query
        or "insert relevant field" in lower_query
    ):
        print("Warning: Placeholder detected!")
    else:
        print("No known placeholder detected.")

    
    # 7. Compare retrieval results
    retriever = Retriever()

    original_results = retrieve_documents(
        retriever,
        query,
        top_k=3,
        threshold=0.5
    )

    rewritten_results = retrieve_documents(
        retriever,
        rewritten_query,
        top_k=3,
        threshold=0.5
    )

    # 8. Print original query results
    print("\n===== Original Query Retrieval =====")
    print("Number of results:", len(original_results))

    for i, result in enumerate(original_results, start=1):
        print(f"\nCandidate {i}")
        print("Page:", result["metadata"]["page"])
        print("Chunk:", result["metadata"]["chunk"])
        print("Score:", round(result["score"], 4))
        print("Text:", result["text"][:150])

    # 9. Print rewritten query results
    print("\n===== Rewritten Query Retrieval =====")
    print("Number of results:", len(rewritten_results))

    for i, result in enumerate(rewritten_results, start=1):
        print(f"\nCandidate {i}")
        print("Page:", result["metadata"]["page"])
        print("Chunk:", result["metadata"]["chunk"])
        print("Score:", round(result["score"], 4))
        print("Text:", result["text"][:150])



if __name__ == "__main__":
    main()

