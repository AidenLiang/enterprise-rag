
from app.agent.tools import (
    retrieve_documents,
    rewrite_query,
    assess_evidence,
)


def run_agent(query, retriever, llm, max_retries=1):
    current_query = query
    history = []

    for attempt in range(max_retries + 1):

        # 1. Retrieve documents
        results = retrieve_documents(
            retriever,
            current_query
        )

        # 2. Assess whether evidence is sufficient
        assessment = assess_evidence(
            llm,
            current_query,
            results
        )

        # 3. Record this attempt for debugging
        history.append({
            "attempt": attempt + 1,
            "query": current_query,
            "result_count": len(results),
            "assessment": assessment,
        })

        # 4. Stop if evidence is sufficient
        if assessment["sufficient"]:
            return {
                "success": True,
                "original_query": query,
                "final_query": current_query,
                "results": results,
                "assessment": assessment,
                "attempts": len(history),
                "history": history,
            }

        # 5. Stop if no retries remain
        if attempt >= max_retries:
            break

        # 6. Rewrite the query using the feedback
        current_query = rewrite_query(
            llm,
            current_query,
            assessment["feedback"]
        )

    # 7. Return failure if evidence remains insufficient
    return {
        "success": False,
        "original_query": query,
        "final_query": current_query,
        "results": results,
        "assessment": assessment,
        "attempts": len(history),
        "history": history,
    }
