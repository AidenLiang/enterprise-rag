
from app.retrieval.retriever import Retriever
from app.generation.llm import LLM
from app.agent.tools import retrieve_documents, assess_evidence


def main():
    # 1. Create real objects
    retriever = Retriever()
    llm = LLM()

    # 2. Prepare the question
    query = "What database was used in the study?"

    # 3. Retrieve real document chunks
    results = retrieve_documents(
        retriever,
        query,
        top_k=3,
        threshold=-1
    )

    print("\n===== Retrieved Documents =====")
    print("Number of results:", len(results))

    for i, result in enumerate(results, start=1):
        print(f"\nCandidate {i}")
        print("Page:", result["metadata"]["page"])
        print("Chunk:", result["metadata"]["chunk"])
        print("Score:", result["score"])
        print("Text:", result["text"][:200])

    # 4. Assess evidence using the real LLM
    assessment = assess_evidence(
        llm,
        query,
        results
    )

    print("\n===== Evidence Assessment =====")
    print("Assessment:", assessment)


if __name__ == "__main__":
    main()
