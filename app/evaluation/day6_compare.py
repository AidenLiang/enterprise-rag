
import time

from app.retrieval.retriever import Retriever
from app.generation.llm import LLM
from app.agent.agent import run_agent
from app.reranking.reranker import (
    build_rerank_prompt,
    parse_rerank_index,
)
from app.config import TOP_K, RETRIEVAL_THRESHOLD


# 与 Day 4 使用相同的五道题和预期事实
evaluation_data = [
    {
        "query": "What database was used in the study?",
        "locations": [(2, 2), (2, 3)],
        "facts": ["Health Facts database"],
    },
    {
        "query": "How was early hospital readmission defined in the study?",
        "locations": [(2, 13)],
        "facts": ["within 30 days of discharge"],
    },
    {
        "query": "What percentage of patients had a medication change when HbA1c was ordered?",
        "locations": [(4, 14)],
        "facts": ["55.0%"],
    },
    {
        "query": "What was the final number of encounters included in the analysis?",
        "locations": [(4, 6)],
        "facts": ["69,984"],
    },
    {
        "query": "What was the readmission rate for patients who had an HbA1c measurement compared with those who did not?",
        "locations": [(4, 15)],
        "facts": ["9.4%", "8.7%"],
    },
]


class CountingLLM:
    """统计 LLM.generate() 被调用的次数。"""

    def __init__(self, llm):
        self.llm = llm
        self.calls = 0

    def generate(self, prompt):
        self.calls += 1
        return self.llm.generate(prompt)


def evaluate_one(data, retriever, base_llm, use_agent):
    query = data["query"]
    llm = CountingLLM(base_llm)

    start = time.perf_counter()

    # 唯一的实验变量：是否启用 Agent
    if use_agent:
        agent_result = run_agent(
            query,
            retriever,
            llm,
            max_retries=1,
            top_k=TOP_K,
        )
        results = agent_result["results"]
        attempts = agent_result["attempts"]
    else:
        results = retriever.retrieve(
            query,
            top_k=TOP_K,
            threshold=RETRIEVAL_THRESHOLD,
        )
        attempts = 1

    locations = {
        (
            item.get("metadata", {}).get("page"),
            item.get("metadata", {}).get("chunk"),
        )
        for item in results
    }

    evidence_hit = bool(
        set(data["locations"]) & locations
    )

    rerank_pass = False
    generation_pass = False
    answer = "I don't know. No relevant information was found."

    if results:
        # 两组使用完全相同的 Reranker
        rerank_prompt = build_rerank_prompt(
            query, results
        )
        rerank_answer = llm.generate(rerank_prompt)

        index = parse_rerank_index(
            rerank_answer, len(results)
        )

        if index is not None:
            selected = results[index]
            selected_location = (
                selected["metadata"]["page"],
                selected["metadata"]["chunk"],
            )
            rerank_pass = (
                selected_location in data["locations"]
            )
        else:
            index = 0

        selected = results[index]

        # 两组使用相同的多 Chunk 上下文策略
        generation_results = [selected] + [
            item
            for i, item in enumerate(results)
            if i != index
        ]

        context_parts = []

        for i, item in enumerate(
            generation_results, start=1
        ):
            metadata = item.get("metadata") or {}

            context_parts.append(
                f"[Evidence {i} | "
                f"Page {metadata.get('page')} | "
                f"Chunk {metadata.get('chunk')}]\n"
                f"{item['text']}"
            )

        context = "\n\n".join(context_parts)

        prompt = retriever.build_prompt(
            query, context
        )
        answer = llm.generate(prompt)

        evidence_supported = all(
            fact in context
            for fact in data["facts"]
        )
        answer_has_facts = all(
            fact in answer
            for fact in data["facts"]
        )

        generation_pass = (
            evidence_supported and answer_has_facts
        )

    elapsed = time.perf_counter() - start

    return {
        "evidence_hit": evidence_hit,
        "rerank_pass": rerank_pass,
        "generation_pass": generation_pass,
        "llm_calls": llm.calls,
        "attempts": attempts,
        "elapsed": elapsed,
        "answer": answer,
    }


def main():
    retriever = Retriever()
    llm = LLM()

    records = {
        "Baseline": [],
        "Agentic": [],
    }

    for i, data in enumerate(evaluation_data, start=1):
        print(f"\n{'=' * 60}")
        print(f"Question {i}: {data['query']}")

        for name, use_agent in [
            ("Baseline", False),
            ("Agentic", True),
        ]:
            result = evaluate_one(
                data,
                retriever,
                llm,
                use_agent,
            )
            records[name].append(result)

            print(f"\n[{name}]")
            print("Evidence hit:", result["evidence_hit"])
            print("Rerank PASS:", result["rerank_pass"])
            print("Generation PASS:", result["generation_pass"])
            print("Attempts:", result["attempts"])
            print("LLM calls:", result["llm_calls"])
            print("Time:", round(result["elapsed"], 2), "s")
            print("Answer:", result["answer"])

    print(f"\n{'=' * 60}")
    print("DAY 6 CONTROLLED COMPARISON")
    print(f"{'Metric':<24} {'Baseline':>12} {'Agentic':>12}")

    metrics = [
        ("evidence_hit", "Evidence Hit Rate"),
        ("rerank_pass", "Rerank Accuracy"),
        ("generation_pass", "Generation Pass Rate"),
        ("llm_calls", "Avg LLM Calls"),
        ("elapsed", "Avg Time (s)"),
    ]

    for key, label in metrics:
        values = []

        for name in ("Baseline", "Agentic"):
            items = records[name]
            avg = sum(
                item[key] for item in items
            ) / len(items)
            values.append(f"{avg:.2f}")

        print(
            f"{label:<24} "
            f"{values[0]:>12} "
            f"{values[1]:>12}"
        )


if __name__ == "__main__":
    main()
