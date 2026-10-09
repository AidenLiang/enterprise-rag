import json
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from app.config import CHUNK_PATH, EMBEDDING_PATH, EMBEDDING_MODEL, TOP_K, RETRIEVAL_THRESHOLD

class Retriever:

    def __init__(
        self,
        chunk_path=CHUNK_PATH,
        embedding_path=EMBEDDING_PATH,
        model_name=EMBEDDING_MODEL
    ):
        # 加载 chunks
        with open(chunk_path, "r", encoding="utf-8") as f:
            self.chunks = json.load(f)

        # 加载已经计算好的 embeddings
        self.embeddings = np.load(embedding_path)

        # 加载 embedding model
        self.model = SentenceTransformer(model_name)

    def retrieve(self, query, top_k=TOP_K, threshold=RETRIEVAL_THRESHOLD):

        # 1. Query → embedding
        query_embedding = self.model.encode(query)

        # 2. 调整 shape: (384,) → (1, 384)
        query_embedding = query_embedding.reshape(1, -1)

        # 3. Query 和所有 chunk 计算 cosine similarity
        similarities = cosine_similarity(
            query_embedding,
            self.embeddings
        )

        # 4. (1, 119) → (119,)
        scores = similarities.flatten()

        # 5. 找 similarity 最高的 Top-K
        top_indices = np.argsort(scores)[-top_k:][::-1]

        # 6. 返回对应 chunks
        results = []

        for index in top_indices:
            if scores[index] >= threshold:
                results.append({
                    "text": self.chunks[index]["text"],
                    "metadata": self.chunks[index]["metadata"],
                    "score": float(scores[index])
                })

        return results
    
    def build_context(self, results):

        context = []

        for result in results:
            text = f"[Source: {result["metadata"]["source"]}, Page: {result["metadata"]["page"]}] \n\n{result["text"]}"
            context.append(text)
        
        return '\n\n'.join(context)

    def build_prompt(self, query, context):
        return f"""Instruction:
Answer the question based only on the context.
If the context does not contain the answer, say that you don't know.
Context:
{context}

Question: 
{query}"""



if __name__ == "__main__":

    retriever = Retriever()

    query = "Does HbA1c affect hospital readmission?"

    results = retriever.retrieve(query, top_k=3)
    


    context = retriever.build_context(results)

    prompt = retriever.build_prompt(query, context)

    print(prompt)