from app.agent.agent import run_agent
from app.retrieval.retriever import Retriever
from app.generation.llm import LLM
from app.reranking.reranker import (
    build_rerank_prompt,
    parse_rerank_index,
)


def is_answer_correct(generated, expected_facts):
    return all(
        fact in generated
        for fact in expected_facts
    )


evaluation_data = [
    {
        "query": "What database was used in the study?",
        "expected_locations": [(2, 2), (2, 3)],
        "expected_facts": ["Health Facts database"],
    },
    {
        "query": (
            "How was early hospital readmission defined in the study?"
        ),
        "expected_locations": [(2, 13)],
        "expected_facts": [
            "within 30 days of discharge",
        ],
    },
    {
        "query": (
            "What percentage of patients had a medication "
            "change when HbA1c was ordered?"
        ),
        "expected_locations": [(4, 14)],
        "expected_facts": ["55.0%"],
    },
    {
        "query": (
            "What was the final number of encounters "
            "included in the analysis?"
        ),
        "expected_locations": [(4, 6)],
        "expected_facts": ["69,984"],
    },
    {
        "query": (
            "What was the readmission rate for patients "
            "who had an HbA1c measurement compared "
            "with those who did not?"
        ),
        "expected_locations": [(4, 15)],
        "expected_facts": ["9.4%", "8.7%"],
    },
]


retriever = Retriever()
llm = LLM()

rerank_correct = 0
generation_correct = 0
# evaluated_count = 0


for data in evaluation_data:
    query = data["query"]

    print("\n" + "=" * 60)
    print("Question:", query)

    # 1. Run Agentic RAG retrieval and assessment
    agent_result = run_agent(
        query,
        retriever,
        llm,
        max_retries=1,
        top_k=3,
    )

    results = agent_result["results"]
    expected_locations = set(data["expected_locations"])

    retrieved_locations = {
        (
            result.get("metadata", {}).get("page"),
            result.get("metadata", {}).get("chunk"),
        )
        for result in results
    }

    print(
        "Expected evidence retrieved:",
        bool(expected_locations & retrieved_locations),
    )

    if query == "How was early hospital readmission defined in the study?":
        for i, item in enumerate(results, start=1):
            print(f"\nCandidate {i}")
            print("Page:", item["metadata"].get("page"))
            print("Chunk:", item["metadata"].get("chunk"))
            print("Score:", item.get("score"))
            print("Text:", item["text"])

    print("Agent success:", agent_result["success"])
    print("Attempts:", agent_result["attempts"])
    print("Final query:", agent_result["final_query"])
    print("History:", agent_result["history"])
    print("Cumulative candidate count:", len(results))

    if not results:
        print("No retrieval results.")
        continue

    # 2. Rerank all cumulative retrieval results
    rerank_prompt = build_rerank_prompt(
        query,
        results,
    )

    rerank_answer = llm.generate(rerank_prompt)

    print("Reranker answer:", repr(rerank_answer))

    index = parse_rerank_index(
        rerank_answer,
        len(results),
    )

    rerank_valid = index is not None

    if not rerank_valid:
        print("Invalid reranker output. Using index 0.")
        index = 0

    selected_result = results[index]

    selected_page = selected_result["metadata"]["page"]

    print("Selected index:", index)
    print("Selected page:", selected_page)
    print("Selected chunk:", selected_result["metadata"]["chunk"])

    selected_location = (
        selected_result["metadata"]["page"],
        selected_result["metadata"]["chunk"],
    )

    if (
        rerank_valid
        and selected_location in data["expected_locations"]
    ):
        rerank_correct += 1

    # 3. Generate an answer from the selected document
    prompt = retriever.build_prompt(
        query,
        selected_result["text"],
    )

    generated_answer = llm.generate(prompt)

    print("Generated answer:", generated_answer)

    answer_correct = is_answer_correct(
        generated_answer,
        data["expected_facts"],
    )

    print(
        "Generation result:",
        "PASS" if answer_correct else "FAIL",
    )

    if answer_correct:
        generation_correct += 1

    # evaluated_count += 1

'''
print("\n" + "=" * 60)
print("Agentic RAG Evaluation Summary")
print("Evaluated questions:", evaluated_count)

if evaluated_count:
    print(
        "Generation Accuracy:",
        generation_correct / evaluated_count,
    )
    print(
        "Rerank Accuracy:",
        rerank_correct / evaluated_count,
    )
else:
    print("No questions were evaluated.")
'''

print("\n" + "=" * 60)
print("Agentic RAG Evaluation Summary")
print("Total questions:", len(evaluation_data))

print(
    "Generation Accuracy:",
    generation_correct / len(evaluation_data),
)

print(
    "Rerank Accuracy:",
    rerank_correct / len(evaluation_data),
)