
from app.agent.tools import (
    retrieve_documents,
    rewrite_query,
    assess_evidence,
)
from app.config import TOP_K

def merge_results(existing_results, new_results):
    merged = list(existing_results)

    seen = set()

    for result in merged:
        metadata = result.get("metadata") or {}
        source = metadata.get("source")
        page = metadata.get("page")
        chunk = metadata.get("chunk")

        if page is not None and chunk is not None:
            key = ("location", source, page, chunk)
        else:
            key = ("text", result.get("text", "").strip())

        seen.add(key)

    for result in new_results:
        metadata = result.get("metadata") or {}
        source = metadata.get("source")
        page = metadata.get("page")
        chunk = metadata.get("chunk")

        if page is not None and chunk is not None:
            key = ("location", source, page, chunk)
        else:
            key = ("text", result.get("text", "").strip())

        if key not in seen:
            merged.append(result)
            seen.add(key)

    return merged

def run_agent(query, retriever, llm, max_retries=1, top_k = TOP_K):
    current_query = query
    history = []
    initial_results = None
    all_results = []

    for attempt in range(max_retries + 1):

        # 1. Retrieve documents
        results = retrieve_documents(
            retriever,
            current_query,
            top_k=top_k
        )
        if attempt == 0:
            initial_results = results
        
        all_results = merge_results(all_results, results)

        # 2. Assess whether evidence is sufficient
        assessment = assess_evidence(
            llm,
            query,
            all_results
        )

        # 3. Record this attempt for debugging
        history.append({
            "attempt": attempt + 1,
            "query": current_query,
            "result_count": len(results),
            "assessment": assessment,
            "cumulative_result_count": len(all_results),
        })

        # 4. Stop if evidence is sufficient
        if assessment["sufficient"]:
            return {
                "success": True,
                "original_query": query,
                "final_query": current_query,
                "results": all_results,
                "initial_results": initial_results,
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
        "results": all_results,
        "initial_results": initial_results,
        "assessment": assessment,
        "attempts": len(history),
        "history": history,
    }
