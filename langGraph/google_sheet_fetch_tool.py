from langchain_core.tools import tool

from sample_school_data import ASSIGNMENTS, ATTENDANCE, GRADES


@tool
def fetch_google_sheet_data(sheet_name: str) -> dict:
    """Return dummy rows for a named Google Sheet."""
    sheet_lower = sheet_name.lower()
    if "attendance" in sheet_lower:
        rows = ATTENDANCE
    elif "assignment" in sheet_lower:
        rows = ASSIGNMENTS
    else:
        rows = GRADES

    return {
        "tool": "google_sheet_fetch_tool",
        "sheet_name": sheet_name,
        "description": "Dummy school spreadsheet result. No Google API request was made.",
        "rows": rows,
    }


if __name__ == "__main__":
    print(fetch_google_sheet_data.invoke({"sheet_name": "Attendance"}))
