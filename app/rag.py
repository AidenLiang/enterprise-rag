from app.retrieval.retriever import Retriever
from app.generation.llm import LLM
from app.reranking.reranker import (
    build_rerank_prompt,
    parse_rerank_index,
)
from app.config import TOP_K
from app.agent.agent import run_agent

class RAG:
    def __init__(self):
        self.retriever = Retriever()
        self.llm = LLM()

    def ask(self, query, top_k = TOP_K):
        # result = self.retriever.retrieve(query, top_k = top_k)
        # if not result:
        #    return "I don't know. No relevant information was found in the knowledge base.", None

        # 1. Run the Agent
        agent_result = run_agent(
            query,
            self.retriever,
            self.llm,
            top_k=top_k
        )

        # 2. Use cumulative results from all retrieval attempts
        results = agent_result["results"]

        print("Agent success:", agent_result["success"])
        print("Using cumulative retrieval results.")


        # 3. Stop only if no results are available
        if not results:
            return (
                "I don't know. No relevant information was found "
                "in the knowledge base.",
                None
            )

        rerank_prompt = build_rerank_prompt(query, results)
        rerank_answer = self.llm.generate(rerank_prompt)
        print("Reranker answer:", repr(rerank_answer))

        index = parse_rerank_index(rerank_answer, len(results))
        if index is None:
            print("Warning: invalid reranker output. Using top retrieval result.")
            index = 0
        selected_result = results[index]
        print("Selected index:", index)
        print("Selected page:",  selected_result["metadata"]["page"])
        print("Selected chunk:",  selected_result["metadata"]["chunk"])

        selected_result = results[index]

        # 1. 将 Reranker 选中的 Chunk 放在最前面
        # 2. 保留其他检索结果，避免丢掉正确证据
        generation_results = [selected_result] + [
            result
            for i, result in enumerate(results)
            if i != index
        ]

        # 3. 将所有候选证据组合成生成模型的上下文
        context_parts = []

        for i, item in enumerate(generation_results, start=1):
            metadata = item.get("metadata") or {}

            context_parts.append(
                f"[Evidence {i} | Page {metadata.get('page')} "
                f"| Chunk {metadata.get('chunk')}]\n"
                f"{item['text']}"
            )

        context = "\n\n".join(context_parts)

        # 4. 仍然使用原来的生成 Prompt
        prompt = self.retriever.build_prompt(query, context)
        answer = self.llm.generate(prompt)

        # 5. 保持原来的返回接口，同时记录实际使用的证据
        source_result = dict(selected_result)
        source_result["context_results"] = generation_results

        return answer, source_result



if __name__ == "__main__":


    query = "What was the readmission rate for patients who had an HbA1c measurement compared with those who did not?"

    rag = RAG()
    answer, result = rag.ask(query, top_k=5)
    print(answer)
    print("\nSources:")

    for item in result.get("context_results", [result]):
        metadata = item.get("metadata", {})

        print(
            f"- {metadata.get('source')}, "
            f"Page {metadata.get('page')}, "
            f"Chunk {metadata.get('chunk')}, "
            f"Score: {item.get('score', 0.0):.4f}"
        )
