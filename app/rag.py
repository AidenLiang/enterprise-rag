from app.retrieval.retriever import Retriever
from app.generation.llm import LLM
from app.reranking.reranker import (
    build_rerank_prompt,
    parse_rerank_index,
)
from app.config import TOP_K
class RAG:
    def __init__(self):
        self.retriever = Retriever()
        self.llm = LLM()
    
    def ask(self, query, top_k = TOP_K):
        result = self.retriever.retrieve(query, top_k = top_k)
        if not result:
            return "I don't know. No relevant information was found in the knowledge base.", None
        rerank_prompt = build_rerank_prompt(query, result)
        rerank_answer = self.llm.generate(rerank_prompt)
        print("Reranker answer:", repr(rerank_answer))

        index = parse_rerank_index(rerank_answer, len(result))
        if index is None:
            print("Warning: invalid reranker output. Using top retrieval result.")
            index = 0
        selected_result = result[index]
        print("Selected index:", index)
        print("Selected page:",  selected_result["metadata"]["page"])
        print("Selected chunk:",  selected_result["metadata"]["chunk"])
        selected_result = result[index]
        context = selected_result["text"]
        # context = self.retriever.build_context(result)
        prompt = self.retriever.build_prompt(query, context)
        return self.llm.generate(prompt), selected_result


if __name__ == "__main__":


    query = "What was the readmission rate for patients who had an HbA1c measurement compared with those who did not?"
   
    rag = RAG()
    answer, result = rag.ask(query)
    print(answer)
    print("\nSources:")

    print(
            f"- {result['metadata']['source']}, "
            f"Page {result['metadata']['page']}"
            f"Score: {result['score']:.4f}"
        )