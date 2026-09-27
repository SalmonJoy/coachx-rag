from langchain_core.tools import tool

from sample_school_data import joined_grade_rows


@tool
def fetch_sql_data(query: str) -> dict:
    """Return dummy SQL rows for a natural-language or SQL-style query."""
    return {
        "tool": "sql_data_fetcher",
        "query": query,
        "description": "Dummy SQL result for student grades. No database was contacted.",
        "rows": joined_grade_rows(),
    }


if __name__ == "__main__":
    print(fetch_sql_data.invoke({"query": "student grades with teacher and subject"}))
