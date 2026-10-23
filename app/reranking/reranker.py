import re

def build_rerank_prompt(query, results):
    candidates = []
    for i ,result in enumerate(results):
        candidates.append(f"candidate {i+1}:\n {result['text']}")
    candidates = '\n\n'.join(candidates)
    return f"""Question: {query}

{candidates}

Which candidate directly answers the question?
Return only the candidate number."""

'''
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
'''

def parse_rerank_index(answer, candidate_count):
    # 1. Check the input type
    if not isinstance(answer, str):
        return None

    # 2. Remove leading and trailing whitespace
    answer = answer.strip()

    # 3. Accept "2", "2.", "Candidate 2",
    #    and "Candidate 2."
    match = re.fullmatch(
        r"(?:candidate\s*:?\s*)?(\d+)\.?",
        answer,
        flags=re.IGNORECASE
    )

    if match is None:
        return None

    # 4. Convert the candidate number to a zero-based index
    index = int(match.group(1)) - 1

    # 5. Check whether the index is valid
    if 0 <= index < candidate_count:
        return index

    return None
