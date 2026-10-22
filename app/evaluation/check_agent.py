
from app.retrieval.retriever import Retriever
from app.generation.llm import LLM
from app.agent.agent import run_agent


def main():
    # 1. Create real components
    retriever = Retriever()
    llm = LLM()

    # 2. Prepare the question
    query = "What database was used in the study?"

    # 3. Run the real agent
    result = run_agent(
        query,
        retriever,
        llm,
        max_retries=1
    )

    # 4. Inspect the final result
    print("\n===== Agent Result =====")
    print("Success:", result["success"])
    print("Attempts:", result["attempts"])
    print("Original query:", result["original_query"])
    print("Final query:", result["final_query"])
    print("Assessment:", result["assessment"])

    # 5. Inspect each attempt
    print("\n===== Agent History =====")

    for item in result["history"]:
        print(f"\nAttempt: {item['attempt']}")
        print("Query:", item["query"])
        print("Result count:", item["result_count"])
        print("Assessment:", item["assessment"])


if __name__ == "__main__":
    main()
