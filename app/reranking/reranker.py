def build_rerank_prompt(query, results):
    candidates = []
    for i ,result in enumerate(results):
        candidates.append(f"candidate {i+1}:\n {result['text']}")
    candidates = '\n\n'.join(candidates)
    return f"""Question: {query}

{candidates}

Which candidate directly answers the question?
Return only the candidate number."""
