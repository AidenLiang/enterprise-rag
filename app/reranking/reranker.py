def build_rerank_prompt(query, results):
    candidates = []
    for i ,result in enumerate(results):
        candidates.append(f"candidate {i+1}:\n {result['text']}")
    candidates = '\n\n'.join(candidates)
    return f"""Question: {query}

{candidates}

Which candidate directly answers the question?
Return only the candidate number."""


def parse_rerank_index(answer, candidate_count):
    # check type
    if not isinstance(answer, str):
        return None
    
    try:
        index = int(answer.strip()) - 1
    except ValueError:
        return None
    

    if 0<= index < candidate_count:
        return index
    
    return None
