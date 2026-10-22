from app.config import TOP_K, RETRIEVAL_THRESHOLD
import json

def retrieve_documents(
    retriever,
    query,
    top_k=TOP_K,
    threshold=RETRIEVAL_THRESHOLD
):
    """Retrieve relevant documents for a query."""

    return retriever.retrieve(
        query,
        top_k=top_k,
        threshold=threshold
    )

def rewrite_query(llm, query, feedback):
    prompt = f"""You are a query rewriting assistant.

Your task is to rewrite the original question into one
concise, natural search query that improves document retrieval.

Original question:
{query}

Feedback from previous retrieval:
{feedback}

Instructions:
1. Preserve the original question's intent and important entities.
2. Use the feedback to clarify what information is missing.
3. Do not answer the question.
4. Do not invent facts or add unsupported assumptions.
5. Do not use placeholders, template instructions, or
   bracketed text such as "[insert relevant field or domain]".
6. Return only the rewritten query, without quotation marks
   or additional explanation.

If the original question is already sufficiently specific,
make only the changes needed to improve retrieval.
"""

    rewritten_query = llm.generate(prompt)
    return rewritten_query.strip()



def assess_evidence(llm, query, results):
    # TODO 1: Handle the case where results is empty
    if not results:
        return {
                "sufficient": False,
                "feedback": "No documents were retrieved."
            }

    # TODO 2: Collect the text from all retrieved candidates
    evidence = []
    for result in results:
        evidence.append(result["text"])
    
    evidence_text = "\n\n".join(evidence)

    prompt = f"""You are an evidence assessment assistant.

Question:
{query}

Retrieved evidence:
{evidence_text}

Determine whether the retrieved evidence contains enough
explicit information to answer the question.

Do not assume that relevant background information is
sufficient evidence. Do not invent missing facts.

Return your assessment as JSON with exactly two fields:
- "sufficient": true or false
- "feedback": a short explanation of the evidence
"""

    # TODO 3: Call the LLM and save its response
    response = llm.generate(prompt)

    # TODO 4: Parse the JSON and validate the result
    try:
        assessment = json.loads(response)       
    except json.JSONDecodeError:
        return {
            "sufficient": False,
            "feedback": "Error decoding response!"
        }
    
    if not isinstance(assessment, dict):
        return {
            "sufficient": False,
            "feedback": "Error Type!"
        }
    if not isinstance(assessment.get("sufficient"), bool):
        return {
            "sufficient": False,
            "feedback": "Error Type!"
        }
    if not isinstance(assessment.get("feedback"),str):
        return {
            "sufficient": False,
            "feedback": "Error Type!"
        }
    return assessment