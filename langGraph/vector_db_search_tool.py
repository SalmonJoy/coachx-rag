from langchain_core.tools import tool

from sample_school_data import SUBJECT_NOTES


@tool
def search_vector_db(search_query: str) -> dict:
    """Return dummy vector database search matches for a query."""
    query_terms = {
        term.lower()
        for term in search_query.replace("-", " ").split()
        if len(term) > 2
    }
    matches = []
    for note in SUBJECT_NOTES:
        note_terms = note["text"].lower().replace("-", " ").split()
        overlap = sum(1 for term in query_terms if term in note_terms)
        score = round(0.72 + min(overlap, 3) * 0.07, 2)
        matches.append(
            {
                "id": note["id"],
                "subject_id": note["subject_id"],
                "score": score,
                "text": note["text"],
            }
        )

    matches = sorted(matches, key=lambda item: item["score"], reverse=True)

    return {
        "tool": "vector_db_search_tool",
        "search_query": search_query,
        "description": "Dummy subject-note vector search. No vector database was contacted.",
        "matches": matches[:3],
    }


if __name__ == "__main__":
    print(search_vector_db.invoke({"search_query": "linear equations practice"}))
