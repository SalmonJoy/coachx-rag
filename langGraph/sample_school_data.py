STUDENTS = [
    {
        "student_id": "S1001",
        "name": "Aarav Mehta",
        "grade_level": 8,
        "homeroom": "8A",
        "advisor_teacher_id": "T201",
    },
    {
        "student_id": "S1002",
        "name": "Maya Johnson",
        "grade_level": 8,
        "homeroom": "8A",
        "advisor_teacher_id": "T202",
    },
    {
        "student_id": "S1003",
        "name": "Lina Chen",
        "grade_level": 9,
        "homeroom": "9B",
        "advisor_teacher_id": "T203",
    },
    {
        "student_id": "S1004",
        "name": "Omar Hassan",
        "grade_level": 9,
        "homeroom": "9B",
        "advisor_teacher_id": "T201",
    },
]

TEACHERS = [
    {
        "teacher_id": "T201",
        "name": "Dr. Priya Nair",
        "department": "Science",
        "email": "priya.nair@example.edu",
    },
    {
        "teacher_id": "T202",
        "name": "Mr. Daniel Brooks",
        "department": "Mathematics",
        "email": "daniel.brooks@example.edu",
    },
    {
        "teacher_id": "T203",
        "name": "Ms. Elena Garcia",
        "department": "Humanities",
        "email": "elena.garcia@example.edu",
    },
]

SUBJECTS = [
    {
        "subject_id": "SCI-801",
        "name": "Integrated Science",
        "teacher_id": "T201",
        "room": "Lab 2",
    },
    {
        "subject_id": "MATH-802",
        "name": "Algebra Foundations",
        "teacher_id": "T202",
        "room": "Room 14",
    },
    {
        "subject_id": "HIST-901",
        "name": "World History",
        "teacher_id": "T203",
        "room": "Room 22",
    },
]

ENROLLMENTS = [
    {"student_id": "S1001", "subject_id": "SCI-801"},
    {"student_id": "S1001", "subject_id": "MATH-802"},
    {"student_id": "S1002", "subject_id": "SCI-801"},
    {"student_id": "S1002", "subject_id": "MATH-802"},
    {"student_id": "S1003", "subject_id": "HIST-901"},
    {"student_id": "S1003", "subject_id": "SCI-801"},
    {"student_id": "S1004", "subject_id": "HIST-901"},
    {"student_id": "S1004", "subject_id": "MATH-802"},
]

GRADES = [
    {"student_id": "S1001", "subject_id": "SCI-801", "term": "Term 1", "score": 92},
    {"student_id": "S1001", "subject_id": "MATH-802", "term": "Term 1", "score": 88},
    {"student_id": "S1002", "subject_id": "SCI-801", "term": "Term 1", "score": 85},
    {"student_id": "S1002", "subject_id": "MATH-802", "term": "Term 1", "score": 91},
    {"student_id": "S1003", "subject_id": "HIST-901", "term": "Term 1", "score": 94},
    {"student_id": "S1003", "subject_id": "SCI-801", "term": "Term 1", "score": 89},
    {"student_id": "S1004", "subject_id": "HIST-901", "term": "Term 1", "score": 81},
    {"student_id": "S1004", "subject_id": "MATH-802", "term": "Term 1", "score": 84},
]

ATTENDANCE = [
    {"student_id": "S1001", "date": "2026-09-21", "status": "Present"},
    {"student_id": "S1002", "date": "2026-09-21", "status": "Present"},
    {"student_id": "S1003", "date": "2026-09-21", "status": "Absent"},
    {"student_id": "S1004", "date": "2026-09-21", "status": "Present"},
    {"student_id": "S1001", "date": "2026-09-22", "status": "Present"},
    {"student_id": "S1002", "date": "2026-09-22", "status": "Late"},
    {"student_id": "S1003", "date": "2026-09-22", "status": "Present"},
    {"student_id": "S1004", "date": "2026-09-22", "status": "Present"},
]

ASSIGNMENTS = [
    {
        "assignment_id": "A-501",
        "subject_id": "SCI-801",
        "title": "Ecosystem Observation Journal",
        "due_date": "2026-10-03",
    },
    {
        "assignment_id": "A-502",
        "subject_id": "MATH-802",
        "title": "Linear Equations Practice Set",
        "due_date": "2026-10-05",
    },
    {
        "assignment_id": "A-503",
        "subject_id": "HIST-901",
        "title": "Ancient Trade Routes Essay",
        "due_date": "2026-10-07",
    },
]

SUBJECT_NOTES = [
    {
        "id": "note-science-001",
        "subject_id": "SCI-801",
        "text": "Integrated Science is currently covering ecosystems, food webs, and energy transfer.",
    },
    {
        "id": "note-math-001",
        "subject_id": "MATH-802",
        "text": "Algebra Foundations focuses on variables, linear equations, and graphing simple relationships.",
    },
    {
        "id": "note-history-001",
        "subject_id": "HIST-901",
        "text": "World History students are studying ancient trade routes and how geography shaped civilizations.",
    },
    {
        "id": "note-support-001",
        "subject_id": "MATH-802",
        "text": "Maya Johnson is strong in algebra fluency, while Omar Hassan may need extra equation practice.",
    },
]


def find_by_id(items: list[dict], key: str, value: str) -> dict:
    for item in items:
        if item.get(key) == value:
            return item
    return {}


def joined_grade_rows() -> list[dict]:
    rows = []
    for grade in GRADES:
        student = find_by_id(STUDENTS, "student_id", grade["student_id"])
        subject = find_by_id(SUBJECTS, "subject_id", grade["subject_id"])
        teacher = find_by_id(TEACHERS, "teacher_id", subject.get("teacher_id", ""))
        rows.append(
            {
                "student_id": grade["student_id"],
                "student_name": student.get("name", "Unknown"),
                "grade_level": student.get("grade_level", ""),
                "subject_id": grade["subject_id"],
                "subject_name": subject.get("name", "Unknown"),
                "teacher_name": teacher.get("name", "Unknown"),
                "term": grade["term"],
                "score": grade["score"],
            }
        )
    return rows


def student_profiles() -> list[dict]:
    profiles = []
    for student in STUDENTS:
        advisor = find_by_id(TEACHERS, "teacher_id", student["advisor_teacher_id"])
        subjects = [
            find_by_id(SUBJECTS, "subject_id", enrollment["subject_id"]).get("name")
            for enrollment in ENROLLMENTS
            if enrollment["student_id"] == student["student_id"]
        ]
        profiles.append(
            {
                **student,
                "advisor_name": advisor.get("name", "Unknown"),
                "subjects": [subject for subject in subjects if subject],
            }
        )
    return profiles


def teacher_schedules() -> list[dict]:
    schedules = []
    for teacher in TEACHERS:
        teacher_subjects = [
            subject
            for subject in SUBJECTS
            if subject["teacher_id"] == teacher["teacher_id"]
        ]
        schedules.append(
            {
                "teacher_id": teacher["teacher_id"],
                "teacher_name": teacher["name"],
                "department": teacher["department"],
                "classes": [
                    {
                        "subject_id": subject["subject_id"],
                        "subject_name": subject["name"],
                        "room": subject["room"],
                    }
                    for subject in teacher_subjects
                ],
            }
        )
    return schedules
