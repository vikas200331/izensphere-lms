import frappe

def create_java_quiz():
    questions_data = [
        {
            "question": "What is the size of `int` variable in Java?",
            "options": [
                {"option": "8 bit", "is_correct": 0},
                {"option": "16 bit", "is_correct": 0},
                {"option": "32 bit", "is_correct": 1},
                {"option": "64 bit", "is_correct": 0}
            ]
        },
        {
            "question": "Which of the following is not a Java feature?",
            "options": [
                {"option": "Dynamic", "is_correct": 0},
                {"option": "Architecture Neutral", "is_correct": 0},
                {"option": "Use of pointers", "is_correct": 1},
                {"option": "Object-oriented", "is_correct": 0}
            ]
        },
        {
            "question": "What is the extension of java code files?",
            "options": [
                {"option": ".js", "is_correct": 0},
                {"option": ".txt", "is_correct": 0},
                {"option": ".class", "is_correct": 0},
                {"option": ".java", "is_correct": 1}
            ]
        },
        {
            "question": "Which of the following is a reserved keyword in Java?",
            "options": [
                {"option": "object", "is_correct": 0},
                {"option": "strictfp", "is_correct": 1},
                {"option": "main", "is_correct": 0},
                {"option": "system", "is_correct": 0}
            ]
        },
        {
            "question": "What is the default value of a local variable in Java?",
            "options": [
                {"option": "null", "is_correct": 0},
                {"option": "0", "is_correct": 0},
                {"option": "Depends on the data type", "is_correct": 0},
                {"option": "No default value for local variables", "is_correct": 1}
            ]
        },
        {
            "question": "Which exception is thrown when java is out of memory?",
            "options": [
                {"option": "MemoryError", "is_correct": 0},
                {"option": "OutOfMemoryError", "is_correct": 1},
                {"option": "MemoryOutOfBoundsException", "is_correct": 0},
                {"option": "MemoryFullException", "is_correct": 0}
            ]
        },
        {
            "question": "Which of these keywords is used to define interfaces in Java?",
            "options": [
                {"option": "intf", "is_correct": 0},
                {"option": "Intf", "is_correct": 0},
                {"option": "interface", "is_correct": 1},
                {"option": "Interface", "is_correct": 0}
            ]
        },
        {
            "question": "In Java, arrays are considered as:",
            "options": [
                {"option": "Primitive data types", "is_correct": 0},
                {"option": "Objects", "is_correct": 1},
                {"option": "Classes", "is_correct": 0},
                {"option": "None of the above", "is_correct": 0}
            ]
        },
        {
            "question": "Which package contains the Random class?",
            "options": [
                {"option": "java.util package", "is_correct": 1},
                {"option": "java.lang package", "is_correct": 0},
                {"option": "java.awt package", "is_correct": 0},
                {"option": "java.io package", "is_correct": 0}
            ]
        },
        {
            "question": "What does the `final` keyword signify when applied to a variable?",
            "options": [
                {"option": "The variable's value can be changed freely.", "is_correct": 0},
                {"option": "The variable's value cannot be changed once assigned.", "is_correct": 1},
                {"option": "The variable is accessible globally.", "is_correct": 0},
                {"option": "The variable is deleted from memory.", "is_correct": 0}
            ]
        }
    ]

    quiz_questions = []

    for q_data in questions_data:
        q_doc = frappe.new_doc("LMS Question")
        q_doc.question = q_data["question"]
        q_doc.type = "Choices"
        for i, opt in enumerate(q_data["options"], start=1):
            setattr(q_doc, f"option_{i}", opt["option"])
            setattr(q_doc, f"is_correct_{i}", opt["is_correct"])
            
        q_doc.insert(ignore_permissions=True)
        quiz_questions.append(q_doc.name)

    quiz_doc = frappe.new_doc("LMS Quiz")
    quiz_doc.title = "Java Basics Quiz"
    quiz_doc.passing_percentage = 70
    quiz_doc.max_attempts = 3
    quiz_doc.show_answers = 1
    
    for q_name in quiz_questions:
        quiz_doc.append("questions", {
            "question": q_name,
            "marks": 1
        })
    quiz_doc.insert(ignore_permissions=True)
    frappe.db.commit()
    print(f"Quiz '{quiz_doc.title}' created successfully!")
