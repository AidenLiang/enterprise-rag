import pymupdf
import os
import json
from app.chunking.text_chunker import split_text

pdf_path = "data/raw/description.pdf"

# 1. 打开 PDF
doc = pymupdf.open(pdf_path)
# 2. 获取页数
print("total page num:", len(doc))
# 3. 读取第一页
documents = []
for pagenum, page in enumerate(doc):
    text = page.get_text()
    document = {
        "text" : text,
        "metadata" : {
            "source" : os.path.basename(pdf_path),
            "page" : pagenum +1
        }
    }
    documents.append(document)

chunk_documents = []

for document in documents:
    # 获取当前页面文本
    current_text = document
    # 获取当前页面 metadata

    # 把当前页面切成 chunks
    chunks = split_text(
        current_text["text"],
        chunk_size = 500,
        overlap = 100
    )
    # 遍历 chunks
    for i, chunk in enumerate(chunks):
    # text = c.get_text()
        doc1 = {
            "text" : chunk,
            "metadata" : {
                "source" : os.path.basename(pdf_path),
                "page" : current_text["metadata"]["page"],
                "chunk" : i+1
            }
        }
        # 创建 chunk_document
        chunk_documents.append(doc1)
        # 加入 chunk_documents
print("Total chunk documents:", len(chunk_documents))
print(chunk_documents[0])
print(chunk_documents[-1])

output_path = "data/processed/chunks.json"
with open(output_path, "w", encoding = "utf-8") as f:
    json.dump(
        chunk_documents,
        f,
        ensure_ascii = False,
        indent = 2
    )
print("Json file saved to", output_path)