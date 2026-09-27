from langchain_core.tools import tool

from sample_school_data import SUBJECTS, student_profiles, teacher_schedules


@tool
def call_external_api(endpoint: str) -> dict:
    """Return a dummy API response for the requested endpoint."""
    endpoint_lower = endpoint.lower()
    if "teacher" in endpoint_lower:
        data = {"teacher_schedules": teacher_schedules()}
    elif "subject" in endpoint_lower:
        data = {"subjects": SUBJECTS}
    else:
        data = {"student_profiles": student_profiles()}

    return {
        "tool": "api_call_tool",
        "endpoint": endpoint,
        "description": "Dummy school API result. No HTTP request was made.",
        "status_code": 200,
        "data": data,
    }


if __name__ == "__main__":
    print(call_external_api.invoke({"endpoint": "/api/v1/school/teacher-schedules"}))
