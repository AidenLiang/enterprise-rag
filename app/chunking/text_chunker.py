def split_text(text, chunk_size=500, overlap=100):
    start = 0
    chunk = []
    while start < len(text):
        end = start + chunk_size
        if end < len(text):
            space_position = text.rfind(" ", start, end)
            if space_position > start:
                end = space_position
        c = text[start:end].strip()
        if c:
            chunk.append(c)

        if end >= len(text):
            break
        start = end - overlap
    return chunk

if __name__ == "__main__":
    text = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" * 10

    chunks = split_text(
        text,
        chunk_size=50,
        overlap=10
    )

    print("Chunk 数量：", len(chunks))

    for i, chunk in enumerate(chunks):
        print(f"\nChunk {i + 1}")
        print("长度：", len(chunk))
        print(chunk)