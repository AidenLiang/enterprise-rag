from app.retrieval.retriever import Retriever
from app.reranking.reranker import (
    build_rerank_prompt,
    parse_rerank_index,
)
from app.generation.llm import LLM


def is_answer_correct(generated, expected_facts):
    return all(answer in generated for answer in expected_facts)

evaluation_data = [
    {
        "query": "What database was used in the study?",
        "expected_page": 2,
        "expected_facts": ["Health Facts database"]
    },
    {
        "query": "How was early hospital readmission defined in the study?",
        "expected_page": 2,
        "expected_facts": ["within 30 days of discharge"]
    },
    {
        "query": "What percentage of patients had a medication change when HbA1c was ordered?",
        "expected_page": 4,
        "expected_facts": ["55.0%"]
    },
    {
        "query": "What was the final number of encounters included in the analysis?",
        "expected_page": 4,
        "expected_facts": ["69,984"]
    },
    {
        "query": "What was the readmission rate for patients who had an HbA1c measurement compared with those who did not?",
        "expected_page": 4,
        "expected_facts": ["9.4%", "8.7%"]
    }
]

retriever = Retriever()
llm = LLM()
correct = 0
generation_correct = 0
for data in evaluation_data:
    # print(data)
    result = retriever.retrieve(data['query'], top_k=3)
    # 检查是否检索到了文档
    if not result:
        print("No retrieval results.")
        print("Rerank result: FAIL")
        print("Generation result: FAIL")
        continue
    prompt = build_rerank_prompt(data['query'],result)

    rerank_answer = llm.generate(prompt)


    print("Reranker answer:", repr(rerank_answer))

    index = parse_rerank_index(rerank_answer, len(result))

    rerank_valid = index is not None

    if not rerank_valid:
        print("Invalid reranker output. Using top retrieval result.")
        index = 0

    print("Selected index:", index)

    context = result[index]["text"]


    print("Selected page:", result[index]["metadata"]["page"])
    if rerank_valid and result[index]["metadata"]["page"] == data["expected_page"]:
        correct += 1
    print("Selected chunk:", result[index]["metadata"]["chunk"])
    print("----- SELECTED TEXT -----")
    print(result[index]["text"])
    print("-------------------------")

   
    
    generation_prompt = retriever.build_prompt(
    data["query"],
    context,
)

    generated_answer = llm.generate(generation_prompt)

    print("Generated answer:", generated_answer)

    answer_correct = is_answer_correct(generated_answer, data["expected_facts"])
    print("Generation result:", "PASS" if answer_correct else "FAIL")
    if answer_correct: generation_correct += 1
print("Generation Accuracy: ", generation_correct/ len(evaluation_data))
rerank_accuracy = correct / len(evaluation_data)
print("Rerank Accuracy:", rerank_accuracy)