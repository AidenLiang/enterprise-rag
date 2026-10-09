from sentence_transformers import SentenceTransformer
import json
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")
# 读取 data/processed/chunks.json
# 得到 119 个 chunk
# 先打印一下结果数量
with open("data/processed/chunks.json", "r", encoding= "utf-8") as f:
# 得到 119 个 chunk
    chunk_document = json.load(f)

# 对每个 chunk 的 text 做 model.encode()
embedd_document = []
for chunk in chunk_document:
    embedding = model.encode(chunk["text"])
    embedd_document.append(embedding)

embeddings = np.array(embedd_document)
np.save("data/processed/embeddings.npy", embeddings)

