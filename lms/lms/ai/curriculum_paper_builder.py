# Copyright (c) 2026, Frappe Technologies and contributors
# For license information, please see license.txt

import re
from typing import Any, Dict, List, Optional


def build_curriculum_question_paper_sections(
	requested_total: int,
	content_text: str = "",
	source_tag: str = "Course Content",
	course: Optional[str] = None,
	batch: Optional[str] = None,
	user_prompt: str = "",
) -> List[Dict[str, Any]]:
	"""Constructs a rigorously structured, highly diversified curriculum examination paper
	with strictly continuous question numbering, mathematically balanced section totals,
	and exhaustive point-by-point Answer Keys and Marking Schemes according to marks allocated.
	"""
	# 1. Parse Blueprint from user_prompt if provided by generator
	blueprint_matches = re.findall(
		r"-\s*([A-Za-z0-9\s]+):\s*(\d+)\s*questions of\s*(\d+)\s*marks each\s*=\s*(\d+)\s*marks\s*\(([^)]+)\)",
		user_prompt,
	)

	blueprint_specs = []
	if blueprint_matches:
		for m in blueprint_matches:
			sec_name = m[0].strip()
			q_count = int(m[1])
			m_each = int(m[2])
			tot_m = int(m[3])
			q_type = m[4].strip()
			blueprint_specs.append({
				"section_name": sec_name,
				"count": q_count,
				"marks_each": m_each,
				"total_marks": tot_m,
				"type": q_type,
			})

	# If blueprint sum doesn't match requested_total, use standard board splits
	calc_blueprint_sum = sum(s["total_marks"] for s in blueprint_specs)
	if not blueprint_specs or calc_blueprint_sum != requested_total:
		if requested_total == 100:
			blueprint_specs = [
				{"section_name": "Section A", "title": "Multiple Choice Questions", "type": "MCQ", "count": 20, "marks_each": 1, "total_marks": 20, "instructions": "All questions are compulsory. Select the correct option."},
				{"section_name": "Section B", "title": "Fill in the Blanks / Very Short Answers", "type": "Fill in the Blanks", "count": 10, "marks_each": 1, "total_marks": 10, "instructions": "Fill in the blank or answer in one line."},
				{"section_name": "Section C", "title": "Short Answer Questions", "type": "Short Answer", "count": 10, "marks_each": 3, "total_marks": 30, "instructions": "Answer in approximately 50-80 words."},
				{"section_name": "Section D", "title": "Long Answer / Descriptive Questions", "type": "Long Answer", "count": 4, "marks_each": 5, "total_marks": 20, "instructions": "Answer in 120-150 words. Internal choices ('OR') are provided."},
				{"section_name": "Section E", "title": "Application-Based / Higher Order Thinking Questions", "type": "Application-Based", "count": 4, "marks_each": 5, "total_marks": 20, "instructions": "Case-based and analytical application problems. Internal choices are provided."},
			]
		elif requested_total == 80:
			blueprint_specs = [
				{"section_name": "Section A", "title": "Multiple Choice Questions", "type": "MCQ", "count": 20, "marks_each": 1, "total_marks": 20, "instructions": "All questions are compulsory. Select the correct option."},
				{"section_name": "Section B", "title": "Very Short Answer Questions", "type": "Short Answer", "count": 6, "marks_each": 2, "total_marks": 12, "instructions": "Answer in one or two concise sentences."},
				{"section_name": "Section C", "title": "Short Answer Questions", "type": "Short Answer", "count": 7, "marks_each": 3, "total_marks": 21, "instructions": "Answer in approximately 50-80 words."},
				{"section_name": "Section D", "title": "Long Answer / Descriptive Questions", "type": "Long Answer", "count": 3, "marks_each": 5, "total_marks": 15, "instructions": "Answer in 120-150 words. Internal choices ('OR') are provided."},
				{"section_name": "Section E", "title": "Application-Based / Higher Order Thinking Questions", "type": "Application-Based", "count": 3, "marks_each": 4, "total_marks": 12, "instructions": "Case-based and analytical application problems. Internal choices are provided."},
			]
		elif requested_total == 50:
			blueprint_specs = [
				{"section_name": "Section A", "title": "Multiple Choice Questions", "type": "MCQ", "count": 10, "marks_each": 1, "total_marks": 10, "instructions": "All questions are compulsory. Select the correct option."},
				{"section_name": "Section B", "title": "Short Answer Questions", "type": "Short Answer", "count": 5, "marks_each": 2, "total_marks": 10, "instructions": "Answer in one or two sentences."},
				{"section_name": "Section C", "title": "Short Answer Questions", "type": "Short Answer", "count": 5, "marks_each": 3, "total_marks": 15, "instructions": "Answer in approximately 50 words."},
				{"section_name": "Section D", "title": "Long Answer Questions", "type": "Long Answer", "count": 3, "marks_each": 5, "total_marks": 15, "instructions": "Answer in 100-120 words. Internal choices ('OR') are provided."},
			]
		else:
			# Dynamic partition matching requested_total
			sec_a = max(2, requested_total // 5)
			rem = requested_total - sec_a
			sec_b = max(1, rem // 10)
			rem -= sec_b * 2
			sec_c = max(1, rem // 6)
			rem -= sec_c * 3
			sec_d = max(1, rem // 5)
			rem -= sec_d * 5
			sec_a += rem

			blueprint_specs = [
				{"section_name": "Section A", "title": "Multiple Choice Questions", "type": "MCQ", "count": sec_a, "marks_each": 1, "total_marks": sec_a, "instructions": "All questions are compulsory. Select the correct option."},
				{"section_name": "Section B", "title": "Very Short Answer Questions", "type": "Short Answer", "count": sec_b, "marks_each": 2, "total_marks": sec_b * 2, "instructions": "Answer in one or two sentences."},
				{"section_name": "Section C", "title": "Short Answer Questions", "type": "Short Answer", "count": sec_c, "marks_each": 3, "total_marks": sec_c * 3, "instructions": "Answer in approximately 50 words."},
				{"section_name": "Section D", "title": "Long Answer Questions", "type": "Long Answer", "count": sec_d, "marks_each": 5, "total_marks": sec_d * 5, "instructions": "Answer in 120 words. Internal choices ('OR') are provided."},
			]

	# 2. Determine Subject Domain & Context
	search_corpus = f"{content_text} {course or ''} {batch or ''} {user_prompt}".lower()
	is_cs_domain = (
		"architecture" in search_corpus
		or "cpu" in search_corpus
		or "alu" in search_corpus
		or "quicksort" in search_corpus
		or "bubblesort" in search_corpus
		or "computer science" in search_corpus
	)

	# Extract content keywords/headings for dynamic anchoring
	raw_lines = [l.strip() for l in content_text.splitlines() if l.strip()]
	headings = [l.replace("#", "").strip() for l in raw_lines if l.startswith("#")]
	bullets = [l.lstrip("*-•1234567890. ").strip() for l in raw_lines if len(l) > 15 and not l.startswith("#")]

	# 3. Retrieve Domain Question Pools
	if is_cs_domain:
		pool_a = _get_cs_mcq_pool(source_tag)
		pool_b = _get_cs_vsa_pool(source_tag)
		pool_c = _get_cs_short_pool(source_tag)
		pool_d = _get_cs_long_pool(source_tag)
		pool_e = _get_cs_application_pool(source_tag)
	else:
		pool_a = _get_python_mcq_pool(source_tag)
		pool_b = _get_python_vsa_pool(source_tag)
		pool_c = _get_python_short_pool(source_tag)
		pool_d = _get_python_long_pool(source_tag)
		pool_e = _get_python_application_pool(source_tag)

	# 4. Build Sections with Continuous Question Numbering
	sections = []
	current_q_num = 1

	for spec in blueprint_specs:
		s_name = spec["section_name"]
		s_title = spec.get("title") or _infer_section_title(s_name, spec["type"])
		s_type = spec["type"]
		s_count = spec["count"]
		s_marks_each = spec["marks_each"]
		s_instructions = spec.get("instructions") or _infer_section_instructions(s_marks_each, s_type)

		# Select appropriate question pool based on section name or question type
		if "Section A" in s_name or s_type == "MCQ" or s_marks_each == 1:
			active_pool = pool_a
		elif "Section B" in s_name or s_marks_each == 2:
			active_pool = pool_b
		elif "Section C" in s_name or s_marks_each == 3:
			active_pool = pool_c
		elif "Section D" in s_name or s_marks_each == 5:
			active_pool = pool_d
		else:
			active_pool = pool_e

		sec_questions = []
		for idx in range(s_count):
			q_number_str = str(current_q_num)
			current_q_num += 1

			if idx < len(active_pool):
				# Clone base question from pool to avoid mutation
				q_item = dict(active_pool[idx])
				q_item["question_number"] = q_number_str
				q_item["marks"] = s_marks_each
				if q_item.get("internal_choice_question"):
					or_copy = dict(q_item["internal_choice_question"])
					or_copy["marks"] = s_marks_each
					q_item["internal_choice_question"] = or_copy
			else:
				# Synthesize additional unique question anchored in content headings/bullets
				h_idx = (idx - len(active_pool)) % max(1, len(headings))
				h_label = headings[h_idx] if headings else f"Curriculum Core Topic {idx+1}"
				b_label = bullets[h_idx % max(1, len(bullets))] if bullets else "standard curriculum principles"

				q_item = _synthesize_extra_question(
					q_num=q_number_str,
					marks=s_marks_each,
					q_type=s_type,
					topic=h_label,
					bullet=b_label,
					source_tag=source_tag,
				)

			sec_questions.append(q_item)

		# Ensure section total marks mathematically matches questions
		s_total = sum(q["marks"] for q in sec_questions)
		sections.append({
			"section_name": s_name,
			"title": s_title,
			"question_type": s_type,
			"marks_per_question": s_marks_each,
			"questions_count": len(sec_questions),
			"total_marks": s_total,
			"instructions": s_instructions,
			"questions": sec_questions,
		})

	return sections


def _infer_section_title(section_name: str, q_type: str) -> str:
	if "Section A" in section_name or q_type == "MCQ":
		return "Multiple Choice Questions"
	if "Section B" in section_name:
		return "Very Short Answer Questions"
	if "Section C" in section_name:
		return "Short Answer Questions"
	if "Section D" in section_name:
		return "Long Answer / Descriptive Questions"
	if "Section E" in section_name:
		return "Application-Based / Higher Order Thinking Questions"
	return f"{section_name} Questions"


def _infer_section_instructions(marks_each: int, q_type: str) -> str:
	if marks_each == 1 and q_type == "MCQ":
		return "All questions are compulsory. Select the correct option."
	if marks_each == 1:
		return "Fill in the blank or provide a one-line answer."
	if marks_each == 2:
		return "Answer in one or two concise sentences."
	if marks_each == 3:
		return "Answer in approximately 50-80 words."
	if marks_each == 4:
		return "Case-based application problems. Internal choices ('OR') are provided."
	if marks_each == 5:
		return "Answer in 120-150 words. Internal choices ('OR') are provided."
	return "Answer all questions according to the designated marks."


def _synthesize_extra_question(
	q_num: str,
	marks: int,
	q_type: str,
	topic: str,
	bullet: str,
	source_tag: str,
) -> Dict[str, Any]:
	"""Dynamically creates authentic, curriculum-grounded questions with exhaustive point-by-point marking schemes."""
	if marks == 1:
		return {
			"question_number": q_num,
			"question": f"Which statement correctly describes the primary objective of {topic}?",
			"options": [
				f"(A) Standard implementation enforcing {bullet[:60]}",
				f"(B) Legacy override bypassing {topic} validation",
				f"(C) Unverified routine ignoring memory bounds",
				f"(D) Arbitrary thread termination without cleanup",
			],
			"correct_answer": f"(A) Standard implementation enforcing {bullet[:60]}",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": f"[1 Mark] Correct Option: (A). Evaluation Criterion: Full 1 mark awarded for identifying adherence to {bullet[:80]}.",
			"solution": f"Option (A) is correct. In {topic}, execution integrity depends upon {bullet[:100]}.",
			"internal_choice_question": None,
		}
	elif marks == 2:
		return {
			"question_number": q_num,
			"question": f"State two fundamental operational characteristics of {topic}.",
			"correct_answer": f"1. Adherence to {bullet[:60]}. 2. Deterministic execution state.",
			"marks": 2,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": (
				f"• Point 1 [1 Mark]: Precise definition of {topic} role in runtime coordination.\n"
				f"• Point 2 [1 Mark]: Technical justification citing {bullet[:80]}."
			),
			"solution": f"1. {topic} coordinates runtime state according to curriculum standards.\n2. It guarantees execution safety by ensuring {bullet[:90]}.",
			"internal_choice_question": None,
		}
	elif marks == 3:
		return {
			"question_number": q_num,
			"question": f"Explain the workflow and execution mechanics of {topic}.",
			"correct_answer": f"{topic} manages structured processing through initialization, state verification, and safe resource release.",
			"marks": 3,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": (
				f"• Point 1 [1 Mark]: Core conceptual purpose of {topic} in the system.\n"
				f"• Point 2 [1 Mark]: Operational workflow and adherence to {bullet[:70]}.\n"
				f"• Point 3 [1 Mark]: Practical advantages, fault tolerance, and trade-off considerations."
			),
			"solution": (
				f"1. Purpose: {topic} provides standardized abstractions for computational tasks.\n"
				f"2. Mechanism: Enforces sequence constraints: {bullet[:100]}.\n"
				f"3. Advantages: Prevents race conditions and maintains deterministic throughput."
			),
			"internal_choice_question": None,
		}
	elif marks == 4:
		return {
			"question_number": q_num,
			"question": f"Case Scenario: An application experiences processing bottlenecks under heavy loads involving {topic}. Formulate a diagnosis and mitigation plan.",
			"correct_answer": "Identify throughput bottlenecks, reorganize resource scheduling, and implement cached intermediate results.",
			"marks": 4,
			"difficulty": "Hard",
			"source": source_tag,
			"answer_key_detail": (
				f"• Sub-part (a) Problem Diagnosis [2 Marks]: Correctly identifies concurrency contention or resource starvation under {topic}.\n"
				f"• Sub-part (b) Technical Mitigation [2 Marks]: Concrete architectural remedy incorporating {bullet[:80]} with verification steps."
			),
			"solution": (
				f"Part (a): Latency stems from unbuffered synchronization operations in {topic}.\n"
				f"Part (b): Apply asynchronous dispatch, pool allocations, and verify using latency histograms."
			),
			"internal_choice_question": {
				"question": f"OR: Case Scenario: Design a high-availability fallback architecture for {topic} when primary services become unresponsive.",
				"marks": 4,
				"correct_answer": "Circuit-breaker pattern with automated failover and idempotent replay queues.",
				"answer_key_detail": (
					"• Sub-part (a) Architecture Breakdown [2 Marks]: Specification of circuit breaker thresholds and state transitions.\n"
					"• Sub-part (b) Failover & Data Consistency [2 Marks]: Mechanism for queue persistence, retry backoff, and state reconciliation."
				),
				"solution": "Full credit for defining Closed, Open, and Half-Open states with idempotent event processing.",
			},
		}
	else:
		return {
			"question_number": q_num,
			"question": f"Provide an in-depth architectural analysis of {topic}. Detail its operational lifecycle, state transitions, and system integration.",
			"correct_answer": f"Comprehensive architecture of {topic} with lifecycle phases, data flow, and error boundary isolation.",
			"marks": 5,
			"difficulty": "Hard",
			"source": source_tag,
			"answer_key_detail": (
				f"• Theoretical Foundation & Principles [1 Mark]: Definition, scope, and foundational role of {topic}.\n"
				f"• Core Architecture & Working Mechanics [2 Marks]: In-depth explanation of internal execution flow and {bullet[:70]}.\n"
				f"• Implementation / Code Demonstration [1 Mark]: Syntactically valid code or configuration demonstrating the pattern.\n"
				f"• Edge Cases, Optimization & Best Practices [1 Mark]: Analysis of failure boundaries, exception recovery, and scalability."
			),
			"solution": (
				f"1. Foundation: {topic} represents a core structural component.\n"
				f"2. Architecture: Implements multi-stage lifecycle including setup, execution, and teardown.\n"
				f"3. Mechanics: Aligns with {bullet[:110]}.\n"
				f"4. Code & Verification: Standard implementation ensures isolated execution context."
			),
			"internal_choice_question": {
				"question": f"OR: Discuss comparative paradigms for {topic}. Evaluate alternative implementations against modern performance metrics.",
				"marks": 5,
				"correct_answer": "Comparative evaluation of synchronous vs asynchronous implementations with benchmark metrics.",
				"answer_key_detail": (
					"• Theoretical Comparison [1 Mark]: Contrasting fundamental architectural paradigms.\n"
					"• Resource & Throughput Analysis [2 Marks]: Evaluation of memory footprints, CPU utilization, and I/O latency.\n"
					"• Implementation Trade-offs [1 Mark]: Scenarios favoring each approach with concrete syntax examples.\n"
					"• Critical Evaluation & Decision Matrix [1 Mark]: Guidelines for production selection based on SLA requirements."
				),
				"solution": "Full credit awarded for detailed trade-off matrix analyzing latency curves, memory overhead, and maintenance complexity.",
			},
		}


# =====================================================================
# PYTHON & FULL STACK DEVELOPMENT QUESTION POOL
# =====================================================================

def _get_python_mcq_pool(source_tag: str) -> List[Dict[str, Any]]:
	return [
		{
			"question": "Who developed the Python programming language and in which year was version 0.9.0 first publicly released?",
			"options": ["(A) Dennis Ritchie in 1972", "(B) Guido van Rossum in 1991", "(C) Bjarne Stroustrup in 1985", "(D) James Gosling in 1995"],
			"correct_answer": "(B) Guido van Rossum in 1991",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (B) Guido van Rossum in 1991. Evaluation Criterion: Full 1 mark awarded for identifying Guido van Rossum, who began implementing Python in December 1989 at CWI in the Netherlands and released version 0.9.0 in February 1991.",
			"solution": "Guido van Rossum conceived Python as a successor to the ABC language capable of exception handling and interfacing with the Amoeba operating system. Dennis Ritchie created C, Bjarne Stroustrup created C++, and James Gosling created Java.",
			"internal_choice_question": None,
		},
		{
			"question": "Which of the following built-in Python collection types is immutable?",
			"options": ["(A) List", "(B) Dictionary", "(C) Set", "(D) Tuple"],
			"correct_answer": "(D) Tuple",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (D) Tuple. Evaluation Criterion: Full 1 mark awarded for identifying Tuple as an immutable sequence type whose elements cannot be modified, added, or removed after instantiation.",
			"solution": "Tuples, integers, floats, booleans, and strings are immutable in Python. Lists, dictionaries, and sets are mutable collections that can be modified in-place.",
			"internal_choice_question": None,
		},
		{
			"question": "What is the boolean evaluation of an empty list expression `bool([])` in Python?",
			"options": ["(A) True", "(B) False", "(C) None", "(D) SyntaxError"],
			"correct_answer": "(B) False",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (B) False. Evaluation Criterion: Full 1 mark awarded for recognizing that empty sequences and collections ([], {}, set(), '') evaluate to boolean False in truth-value testing.",
			"solution": "In Python, any empty sequence, empty mapping, numeric zero (0, 0.0), or None evaluates to boolean False (falsy) under conditional evaluation.",
			"internal_choice_question": None,
		},
		{
			"question": "Which keyword is utilized to define an anonymous, single-expression function in Python?",
			"options": ["(A) func", "(B) def", "(C) lambda", "(D) inline"],
			"correct_answer": "(C) lambda",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (C) lambda. Evaluation Criterion: Full 1 mark awarded for identifying the lambda keyword used for creating small anonymous functions with the syntax `lambda arguments: expression`.",
			"solution": "The `lambda` keyword allows programmers to define single-expression functions without binding them to a formal name, commonly used with higher-order functions like map(), filter(), and sorted().",
			"internal_choice_question": None,
		},
		{
			"question": "What is the primary role of the `__init__` dunder method in Python classes?",
			"options": ["(A) To allocate operating system memory for the class", "(B) To initialize attributes of a newly created instance", "(C) To destroy obsolete object references", "(D) To compile python bytecode to C instructions"],
			"correct_answer": "(B) To initialize attributes of a newly created instance",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (B) To initialize attributes of a newly created instance. Evaluation Criterion: Full 1 mark awarded for explaining that __init__ acts as an instance initializer (constructor) invoked after object instantiation (__new__).",
			"solution": "`__init__` is Python's constructor method. It receives the freshly allocated instance as `self` along with passed arguments to initialize instance state.",
			"internal_choice_question": None,
		},
		{
			"question": "In Python scope resolution, what does the acronym LEGB stand for?",
			"options": ["(A) Local, Enclosing, Global, Built-in", "(B) Linear, External, Global, Binary", "(C) Linked, Environment, Garbage, Base", "(D) Lexical, Enclosing, General, Boolean"],
			"correct_answer": "(A) Local, Enclosing, Global, Built-in",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (A) Local, Enclosing, Global, Built-in. Evaluation Criterion: Full 1 mark awarded for defining the exact four hierarchical namespaces checked during variable resolution in Python.",
			"solution": "Python searches namespaces hierarchically: Local (inside current function), Enclosing (nested outer functions), Global (module level), and Built-in (built-in functions and exceptions).",
			"internal_choice_question": None,
		},
		{
			"question": "Which statement about Python dictionaries is accurate?",
			"options": ["(A) Dictionary keys can be mutable objects like lists", "(B) Dictionary keys must be hashable and unique", "(C) Dictionaries store elements in strictly sorted alphabetical order", "(D) Duplicate keys are allowed and retain distinct values"],
			"correct_answer": "(B) Dictionary keys must be hashable and unique",
			"marks": 1,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (B) Dictionary keys must be hashable and unique. Evaluation Criterion: Full 1 mark awarded for identifying the requirement that dict keys must implement a stable __hash__() and __eq__().",
			"solution": "Python dictionary keys must be hashable, meaning their hash value does not change across their lifetime. Mutable types such as lists and dicts cannot be keys.",
			"internal_choice_question": None,
		},
		{
			"question": "What is the output of the slice expression `text[1:5]` when `text = 'PYTHON'`?",
			"options": ["(A) 'PYTH'", "(B) 'YTHO'", "(C) 'YTHON'", "(D) 'PYTHON'"],
			"correct_answer": "(B) 'YTHO'",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (B) 'YTHO'. Evaluation Criterion: Full 1 mark awarded for correctly calculating slicing indices [start:end] where start index 1 ('Y') is inclusive and stop index 5 ('N') is exclusive.",
			"solution": "Index 0 is 'P', index 1 is 'Y', index 2 is 'T', index 3 is 'H', index 4 is 'O', and index 5 is 'N'. Slicing from 1 up to (not including) 5 yields 'YTHO'.",
			"internal_choice_question": None,
		},
		{
			"question": "Which built-in module is used in Python to serialize Python objects into JSON formatted strings?",
			"options": ["(A) pickle", "(B) marshal", "(C) json", "(D) serialize"],
			"correct_answer": "(C) json",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (C) json. Evaluation Criterion: Full 1 mark awarded for identifying the standard library `json` module providing json.dumps() and json.loads().",
			"solution": "Python's `json` module provides standard serialization and deserialization routines to encode Python objects into JSON strings and decode JSON strings into Python data structures.",
			"internal_choice_question": None,
		},
		{
			"question": "What mechanism does Python's `with` statement implement for safe resource management?",
			"options": ["(A) Dynamic Memory Allocation", "(B) Context Management Protocol", "(C) Multithreaded Semaphore Locking", "(D) Bytecode Optimization"],
			"correct_answer": "(B) Context Management Protocol",
			"marks": 1,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (B) Context Management Protocol. Evaluation Criterion: Full 1 mark awarded for identifying context managers using __enter__ and __exit__ methods to guarantee deterministic cleanup.",
			"solution": "The `with` statement binds execution to a context manager. Its `__enter__()` executes upon entry and `__exit__()` is guaranteed to run upon leaving, even if exceptions occur.",
			"internal_choice_question": None,
		},
		{
			"question": "In Django's MVT architectural pattern, what role is fulfilled by the 'View' component?",
			"options": ["(A) Direct rendering of HTML markup and CSS styles", "(B) Database table schema declaration and ORM mapping", "(C) Business logic execution and HTTP request/response processing", "(D) DNS address resolution for client connections"],
			"correct_answer": "(C) Business logic execution and HTTP request/response processing",
			"marks": 1,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (C) Business logic execution and HTTP request/response processing. Evaluation Criterion: Full 1 mark awarded for specifying that Django Views accept HttpRequest objects and return HttpResponse objects.",
			"solution": "In Django MVT, Models define the data layer, Templates handle presentation, and Views contain the business logic that queries the models and renders templates or returns JSON.",
			"internal_choice_question": None,
		},
		{
			"question": "What is the average time complexity of searching for a key in a Python dictionary?",
			"options": ["(A) O(1)", "(B) O(log n)", "(C) O(n)", "(D) O(n log n)"],
			"correct_answer": "(A) O(1)",
			"marks": 1,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (A) O(1). Evaluation Criterion: Full 1 mark awarded for stating that hash table lookups provide amortized constant O(1) time complexity.",
			"solution": "Python dictionaries are implemented using sparse hash tables with open addressing, providing amortized O(1) average time complexity for key lookups, insertions, and deletions.",
			"internal_choice_question": None,
		},
		{
			"question": "Which method is used in Python to safely remove and return an element from a dictionary without raising a KeyError if absent?",
			"options": ["(A) remove()", "(B) pop()", "(C) discard()", "(D) delete()"],
			"correct_answer": "(B) pop()",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (B) pop(). Evaluation Criterion: Full 1 mark awarded for identifying `dict.pop(key, default)` which returns the default value if the key does not exist.",
			"solution": "`dict.pop(key, default)` removes and returns the value for `key`. If `key` is missing and a default argument is provided, the default is returned instead of raising a KeyError.",
			"internal_choice_question": None,
		},
		{
			"question": "What does the `*args` syntax in a Python function parameter list represent?",
			"options": ["(A) A keyword dictionary of optional arguments", "(B) A tuple of arbitrary positional arguments", "(C) A pointer to external memory", "(D) A mandatory keyword-only parameter"],
			"correct_answer": "(B) A tuple of arbitrary positional arguments",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (B) A tuple of arbitrary positional arguments. Evaluation Criterion: Full 1 mark awarded for recognizing *args captures extra positional arguments into an immutable tuple.",
			"solution": "The `*` unpacking operator in a function definition collects all surplus positional arguments passed to the function into a tuple named `args`.",
			"internal_choice_question": None,
		},
		{
			"question": "What is the primary purpose of the `Global Interpreter Lock (GIL)` in CPython?",
			"options": ["(A) To prevent syntax errors during runtime compilation", "(B) To ensure thread-safe memory management by allowing only one thread to execute Python bytecode at a time", "(C) To restrict user programs from writing to disk without permissions", "(D) To accelerate mathematical matrix operations"],
			"correct_answer": "(B) To ensure thread-safe memory management by allowing only one thread to execute Python bytecode at a time",
			"marks": 1,
			"difficulty": "Hard",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (B) To ensure thread-safe memory management by allowing only one thread to execute Python bytecode at a time. Evaluation Criterion: Full 1 mark awarded for explaining GIL synchronization of CPython's reference-counted memory manager.",
			"solution": "CPython's GIL is a mutual-exclusion lock preventing multiple native threads from executing Python bytecodes concurrently, safeguarding reference counters from race conditions.",
			"internal_choice_question": None,
		},
		{
			"question": "Which HTTP status code signifies that a requested resource was successfully created on the server?",
			"options": ["(A) 200 OK", "(B) 201 Created", "(C) 204 No Content", "(D) 301 Moved Permanently"],
			"correct_answer": "(B) 201 Created",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (B) 201 Created. Evaluation Criterion: Full 1 mark awarded for identifying HTTP 201 Created as the standard response for successful POST creation requests.",
			"solution": "HTTP 201 Created indicates that the request has succeeded and led to the creation of a new resource, typically including a Location header pointing to the new URI.",
			"internal_choice_question": None,
		},
		{
			"question": "In CSS, what components comprise the standard Box Model from the innermost layer outwards?",
			"options": ["(A) Content, Padding, Border, Margin", "(B) Margin, Border, Padding, Content", "(C) Content, Border, Padding, Outline", "(D) Padding, Content, Margin, Shadow"],
			"correct_answer": "(A) Content, Padding, Border, Margin",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (A) Content, Padding, Border, Margin. Evaluation Criterion: Full 1 mark awarded for stating the correct nested sequence of CSS box model layers.",
			"solution": "The CSS box model consists of the inner Content area, surrounded by Padding (space inside the border), Border (boundary line), and Margin (clear space outside the border).",
			"internal_choice_question": None,
		},
		{
			"question": "Which Git command is used to combine changes from a specified branch into the currently checked-out branch?",
			"options": ["(A) git checkout", "(B) git merge", "(C) git fetch", "(D) git rebase --abort"],
			"correct_answer": "(B) git merge",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (B) git merge. Evaluation Criterion: Full 1 mark awarded for identifying `git merge <branch>` as the command that integrates histories of separate branches.",
			"solution": "`git merge` combines the commits from the target branch into the active branch, creating a merge commit if a fast-forward is not possible.",
			"internal_choice_question": None,
		},
		{
			"question": "What is the return type of the built-in function `range(5)` in Python 3?",
			"options": ["(A) list", "(B) tuple", "(C) range object", "(D) generator"],
			"correct_answer": "(C) range object",
			"marks": 1,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (C) range object. Evaluation Criterion: Full 1 mark awarded for noting that range() in Python 3 produces an immutable sequence object of type `range`, not a pre-computed list.",
			"solution": "In Python 3, `range()` yields a space-efficient sequence object representing an arithmetic progression that calculates elements lazily on demand.",
			"internal_choice_question": None,
		},
		{
			"question": "Which exception is raised in Python when attempting to access a dictionary key that does not exist using bracket notation `dict[key]`?",
			"options": ["(A) IndexError", "(B) KeyError", "(C) AttributeError", "(D) LookupException"],
			"correct_answer": "(B) KeyError",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (B) KeyError. Evaluation Criterion: Full 1 mark awarded for identifying KeyError as the specific mapping exception raised on missing key access.",
			"solution": "Accessing `d[key]` when `key not in d` raises a `KeyError`. Using `d.get(key)` returns `None` instead of raising an exception.",
			"internal_choice_question": None,
		},
	]


def _get_python_vsa_pool(source_tag: str) -> List[Dict[str, Any]]:
	return [
		{
			"question": "Differentiate between mutable and immutable objects in Python, giving one example of each.",
			"correct_answer": "Mutable objects can have their state or contents altered in-place (e.g., list, dict); immutable objects cannot be modified once instantiated (e.g., tuple, str, int).",
			"marks": 2,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": (
				"Marking Scheme (2 Marks Total):\n"
				"• Point 1 [1 Mark]: Accurate technical definition of mutable objects (in-place modification without memory address changes) with valid example (e.g., list, dict, set).\n"
				"• Point 2 [1 Mark]: Accurate technical definition of immutable objects (re-allocation required on change) with valid example (e.g., tuple, str, int, float)."
			),
			"solution": "Mutable objects allow in-place modification of their values without changing their identity (memory address `id()`), such as `list` and `dict`. Immutable objects (such as `tuple` and `str`) cannot be modified after creation; any modification generates a new object in memory.",
			"internal_choice_question": None,
		},
		{
			"question": "Explain the purpose of the `__name__ == '__main__'` idiom in Python scripts.",
			"correct_answer": "It allows a Python file to act as either an importable module or an executable standalone script by checking if it is executed as the main program.",
			"marks": 2,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": (
				"Marking Scheme (2 Marks Total):\n"
				"• Point 1 [1 Mark]: Explains that __name__ is automatically assigned '__main__' when run directly via the interpreter.\n"
				"• Point 2 [1 Mark]: Explains that code inside the block is skipped when imported as a library by another module."
			),
			"solution": "When a Python module is executed directly, the interpreter sets the global variable `__name__` to `'__main__'`. If imported, `__name__` is set to the module's file name. This guard prevents executable boilerplate from running unintentionally during imports.",
			"internal_choice_question": None,
		},
		{
			"question": "What is the difference between shallow copy and deep copy in Python? Name the module used to perform them.",
			"correct_answer": "A shallow copy constructs a new object but inserts references to the child objects; a deep copy duplicates both the container and all nested objects recursively. Module used: `copy`.",
			"marks": 2,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": (
				"Marking Scheme (2 Marks Total):\n"
				"• Point 1 [1 Mark]: Distinction between reference copying (shallow) vs recursive object cloning (deep).\n"
				"• Point 2 [1 Mark]: Correct naming of Python's built-in `copy` module (`copy.copy()` and `copy.deepcopy()`)."
			),
			"solution": "The `copy` module provides `copy()` and `deepcopy()`. Shallow copy creates a new compound object but shares references to inner elements; modifying a nested mutable list affects both copies. Deep copy clones every nested object recursively.",
			"internal_choice_question": None,
		},
		{
			"question": "Describe the operational difference between the `is` operator and the `==` operator in Python.",
			"correct_answer": "`==` checks for value equality (equality of contents), whereas `is` checks for identity equality (verifying if both variables reference the exact same memory location).",
			"marks": 2,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": (
				"Marking Scheme (2 Marks Total):\n"
				"• Point 1 [1 Mark]: Identification that `==` evaluates value equality via `__eq__()` method.\n"
				"• Point 2 [1 Mark]: Identification that `is` evaluates object identity equality (`id(a) == id(b)`)."
			),
			"solution": "`==` compares the data values of two objects (e.g. `[1, 2] == [1, 2]` is `True`). The `is` operator checks if two references point to the exact same memory address (e.g. `[1, 2] is [1, 2]` is `False`).",
			"internal_choice_question": None,
		},
		{
			"question": "How does Python's `try...except...finally` block execute, and what is the guarantee provided by `finally`?",
			"correct_answer": "`try` executes the code; `except` catches errors; `finally` is guaranteed to run regardless of whether an exception occurred or was handled.",
			"marks": 2,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": (
				"Marking Scheme (2 Marks Total):\n"
				"• Point 1 [1 Mark]: Correct execution order of `try` followed by conditional `except` dispatch.\n"
				"• Point 2 [1 Mark]: Explicitly highlighting that `finally` runs unconditionally (even upon `return` or unhandled exceptions)."
			),
			"solution": "Code inside `try` is monitored for exceptions. If an error occurs, control passes to the matching `except` block. The `finally` block is guaranteed to execute in all circumstances, making it ideal for closing files or database connections.",
			"internal_choice_question": None,
		},
		{
			"question": "Define list comprehension in Python and write a one-line comprehension that generates squares of even numbers from 0 to 8.",
			"correct_answer": "A concise syntactic construct to generate lists: `[x**2 for x in range(9) if x % 2 == 0]`.",
			"marks": 2,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": (
				"Marking Scheme (2 Marks Total):\n"
				"• Point 1 [1 Mark]: Accurate technical definition of list comprehensions as compact mapping and filtering syntax.\n"
				"• Point 2 [1 Mark]: Correct syntax: `[x**2 for x in range(9) if x % 2 == 0]`."
			),
			"solution": "List comprehension provides a declarative syntax for generating new lists from iterables. The expression `[x**2 for x in range(9) if x % 2 == 0]` evaluates to `[0, 4, 16, 36, 64]`.",
			"internal_choice_question": None,
		},
		{
			"question": "Explain the difference between `*args` and `**kwargs` in Python function definitions.",
			"correct_answer": "`*args` passes variable-length non-keyword positional arguments as a tuple; `**kwargs` passes variable-length keyword arguments as a dictionary.",
			"marks": 2,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": (
				"Marking Scheme (2 Marks Total):\n"
				"• Point 1 [1 Mark]: Stating `*args` unpacks positional arguments into a tuple.\n"
				"• Point 2 [1 Mark]: Stating `**kwargs` unpacks keyword/named arguments into a dictionary."
			),
			"solution": "`*args` collects any number of positional parameters into an immutable tuple. `**kwargs` collects arbitrary keyword arguments into a standard key-value dictionary.",
			"internal_choice_question": None,
		},
		{
			"question": "What is the purpose of the `pass` statement in Python?",
			"correct_answer": "It serves as a syntactic null statement or placeholder where code is syntactically required but no action should be executed.",
			"marks": 2,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": (
				"Marking Scheme (2 Marks Total):\n"
				"• Point 1 [1 Mark]: Definition as a no-operation (NOP) placeholder.\n"
				"• Point 2 [1 Mark]: Practical context (empty functions, classes, or exception pass-throughs)."
			),
			"solution": "Because Python uses indentation to delimit code blocks, empty blocks cause a `SyntaxError`. The `pass` statement acts as a no-op placeholder for future code.",
			"internal_choice_question": None,
		},
		{
			"question": "State the difference between `break` and `continue` statements in Python loop constructs.",
			"correct_answer": "`break` immediately terminates the loop entirely; `continue` skips the remainder of the current iteration and advances to the next iteration.",
			"marks": 2,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": (
				"Marking Scheme (2 Marks Total):\n"
				"• Point 1 [1 Mark]: Clear statement on loop termination for `break`.\n"
				"• Point 2 [1 Mark]: Clear statement on skipping current iteration and jumping to next cycle for `continue`."
			),
			"solution": "When `break` is encountered, the innermost enclosing loop terminates immediately. When `continue` is encountered, execution skips the rest of the loop body and starts the next iteration.",
			"internal_choice_question": None,
		},
		{
			"question": "Explain the difference between GET and POST HTTP request methods in web applications.",
			"correct_answer": "GET requests data from a specified resource via URL query strings without side effects; POST submits data in the HTTP request body to create or modify server resources.",
			"marks": 2,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": (
				"Marking Scheme (2 Marks Total):\n"
				"• Point 1 [1 Mark]: GET parameters in URL query string, idempotent, read-only cacheable.\n"
				"• Point 2 [1 Mark]: POST data payload in request body, non-idempotent, used for state mutation."
			),
			"solution": "GET is safe and idempotent, passing parameters in the URL query string. POST transmits payloads inside the HTTP message body, used for sensitive or state-changing actions like user registration or form submission.",
			"internal_choice_question": None,
		},
	]


def _get_python_short_pool(source_tag: str) -> List[Dict[str, Any]]:
	return [
		{
			"question": "Explain Python's LEGB rule for variable scope resolution with a clear illustrative code example.",
			"correct_answer": "LEGB defines scope hierarchy: Local -> Enclosing -> Global -> Built-in. Python searches each namespace sequentially until a matching identifier is located.",
			"marks": 3,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": (
				"Marking Scheme (3 Marks Total):\n"
				"• Point 1 [1 Mark]: Theoretical explanation of the 4 namespaces: Local, Enclosing (nested functions), Global (module level), and Built-in (builtins module).\n"
				"• Point 2 [1 Mark]: Description of sequential resolution order (search stops at first match; raises NameError if exhausted).\n"
				"• Point 3 [1 Mark]: Concrete code snippet demonstrating nested scopes with distinct variable shadowing."
			),
			"solution": (
				"1. Scope Hierarchy (1 Mark): Local (names assigned within a function), Enclosing (enclosing functions from inner to outer), Global (top-level module), Built-in (preassigned system names like len, range).\n"
				"2. Resolution Order (1 Mark): When resolving `x`, Python searches L -> E -> G -> B sequentially.\n"
				"3. Code Example (1 Mark):\n"
				"```python\n"
				"x = 'global'\n"
				"def outer():\n"
				"    x = 'enclosing'\n"
				"    def inner():\n"
				"        x = 'local'\n"
				"        return x\n"
				"    return inner()\n"
				"```"
			),
			"internal_choice_question": None,
		},
		{
			"question": "Describe the Generator protocol in Python. Detail how the `yield` statement operates and explain the memory benefits over standard lists.",
			"correct_answer": "Generators produce items one-at-a-time on demand (lazy evaluation). `yield` returns a value while preserving function execution frame state.",
			"marks": 3,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": (
				"Marking Scheme (3 Marks Total):\n"
				"• Point 1 [1 Mark]: Operational definition of `yield` suspending function state (instruction pointer, local variables) and yielding control.\n"
				"• Point 2 [1 Mark]: Explanation of lazy evaluation and generator iterator protocol (`__iter__` and `__next__`).\n"
				"• Point 3 [1 Mark]: Memory efficiency comparison (O(1) auxiliary memory vs O(N) memory allocation for large lists)."
			),
			"solution": (
				"1. Mechanism (1 Mark): A generator function contains `yield`. When called, it returns a generator object. Calling `next()` executes code until `yield`, which freezes execution state and returns the yielded value.\n"
				"2. Protocol (1 Mark): Implements the iterator protocol, raising `StopIteration` when the function terminates.\n"
				"3. Memory Advantage (1 Mark): A list of 10 million integers consumes hundreds of megabytes of RAM; a generator calculating numbers sequentially requires constant O(1) memory overhead."
			),
			"internal_choice_question": None,
		},
		{
			"question": "Differentiate between `@classmethod`, `@staticmethod`, and regular instance methods in Python classes.",
			"correct_answer": "Instance methods receive `self`; class methods receive `cls` via `@classmethod`; static methods receive neither via `@staticmethod`.",
			"marks": 3,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": (
				"Marking Scheme (3 Marks Total):\n"
				"• Point 1 [1 Mark]: Instance methods take `self` as the first argument to manipulate instance-level attributes.\n"
				"• Point 2 [1 Mark]: `@classmethod` decorator takes `cls` as first argument to access or modify class-level state or serve as alternative constructors.\n"
				"• Point 3 [1 Mark]: `@staticmethod` decorator acts as an isolated utility function without implicit instance or class bindings."
			),
			"solution": (
				"1. Instance Methods: Bound to instances, receiving `self`. Can modify both instance and class state.\n"
				"2. Class Methods: Decorated with `@classmethod`, receiving `cls`. Commonly used for factory methods and modifying class-wide variables.\n"
				"3. Static Methods: Decorated with `@staticmethod`. Do not receive `self` or `cls`, functioning like regular functions namespaced within the class."
			),
			"internal_choice_question": None,
		},
		{
			"question": "Analyze Django's ORM QuerySet evaluation. Explain lazy execution and compare `select_related` with `prefetch_related`.",
			"correct_answer": "QuerySets are lazy (evaluated only when iteration occurs). `select_related` performs SQL JOINs for single-valued relationships; `prefetch_related` performs separate queries in Python for multi-valued relationships.",
			"marks": 3,
			"difficulty": "Hard",
			"source": source_tag,
			"answer_key_detail": (
				"Marking Scheme (3 Marks Total):\n"
				"• Point 1 [1 Mark]: Lazy evaluation concept (QuerySets do not hit the database until sliced, looped over, or serialized).\n"
				"• Point 2 [1 Mark]: `select_related` mechanism (SQL inner/left JOIN for ForeignKey and OneToOneField).\n"
				"• Point 3 [1 Mark]: `prefetch_related` mechanism (separate SQL IN queries for ManyToManyField and reverse ForeignKeys, joined in Python memory)."
			),
			"solution": (
				"1. Lazy Execution: Defining `Post.objects.all()` does not execute SQL immediately; evaluation is deferred until results are consumed.\n"
				"2. `select_related`: Solves the N+1 problem on forward single relationships by creating an SQL JOIN in a single database query.\n"
				"3. `prefetch_related`: Solves N+1 on many-to-many or reverse foreign keys by executing 2 queries and stitching related records in memory."
			),
			"internal_choice_question": None,
		},
		{
			"question": "Explain the concept of Method Resolution Order (MRO) and C3 Linearization in Python multiple inheritance.",
			"correct_answer": "MRO defines the search order for methods across inheritance trees using the C3 Linearization algorithm to ensure monotonicity and local precedence.",
			"marks": 3,
			"difficulty": "Hard",
			"source": source_tag,
			"answer_key_detail": (
				"Marking Scheme (3 Marks Total):\n"
				"• Point 1 [1 Mark]: Definition of MRO as the deterministic search path for attribute lookup in multiple inheritance.\n"
				"• Point 2 [1 Mark]: Principles of C3 Linearization (preserves local precedence order and monotonic inheritance without diamond ambiguity).\n"
				"• Point 3 [1 Mark]: Method inspection syntax (`ClassName.mro()` or `ClassName.__mro__`) and `super()` cooperative method dispatch."
			),
			"solution": (
				"1. Concept: When a class inherits from multiple parents, Python uses MRO to determine which parent method executes first.\n"
				"2. C3 Algorithm: Guarantees that child classes precede parents and the order of parent classes in the class declaration is preserved.\n"
				"3. Inspection: Developers inspect MRO via `Class.__mro__`. Using `super()` delegates calls strictly along the MRO list."
			),
			"internal_choice_question": None,
		},
		{
			"question": "Detail how context managers work under the hood in Python using `__enter__` and `__exit__` dunder methods.",
			"correct_answer": "`__enter__` sets up the resource context; `__exit__` handles cleanup, receiving exception parameters `(exc_type, exc_val, exc_tb)`.",
			"marks": 3,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": (
				"Marking Scheme (3 Marks Total):\n"
				"• Point 1 [1 Mark]: Role of `__enter__()` executing before the block and optionally binding the target with `as`.\n"
				"• Point 2 [1 Mark]: Role of `__exit__(exc_type, exc_val, exc_tb)` executing on block termination with exception details.\n"
				"• Point 3 [1 Mark]: Exception suppression rule (returning `True` from `__exit__` swallows the exception; returning `False` re-raises)."
			),
			"solution": (
				"1. Setup: `with Expression as target:` calls `Expression.__enter__()`, binding its return value to `target`.\n"
				"2. Teardown: Upon block exit, `__exit__(exc_type, exc_val, exc_tb)` is invoked with exception details if an error occurred.\n"
				"3. Error Handling: If no exception occurs, all three arguments are `None`. Returning `True` suppresses exceptions; returning `False` propagates them."
			),
			"internal_choice_question": None,
		},
		{
			"question": "Explain the role and syntax of Python Decorators, illustrating how a decorator wraps a function.",
			"correct_answer": "Decorators are callable functions that accept another function as an argument, extend its behavior dynamically, and return a replacement callable.",
			"marks": 3,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": (
				"Marking Scheme (3 Marks Total):\n"
				"• Point 1 [1 Mark]: Definition of decorators as higher-order functions modifying function behavior without altering source code.\n"
				"• Point 2 [1 Mark]: Use of closure and inner wrapper function accepting `*args` and `**kwargs`.\n"
				"• Point 3 [1 Mark]: Syntax demonstration with `@decorator_name` syntactic sugar and `@functools.wraps` metadata preservation."
			),
			"solution": (
				"1. Theory: Decorators take a callable `f` and return a wrapped callable `wrapper`.\n"
				"2. Implementation:\n"
				"```python\n"
				"from functools import wraps\n"
				"def my_decorator(func):\n"
				"    @wraps(func)\n"
				"    def wrapper(*args, **kwargs):\n"
				"        print('Before call')\n"
				"        res = func(*args, **kwargs)\n"
				"        print('After call')\n"
				"        return res\n"
				"    return wrapper\n"
				"```\n"
				"3. Syntax: Applying `@my_decorator` over `def f()` is equivalent to `f = my_decorator(f)`."
			),
			"internal_choice_question": None,
		},
	]


def _get_python_long_pool(source_tag: str) -> List[Dict[str, Any]]:
	return [
		{
			"question": "Analyze the Object-Oriented Programming (OOP) paradigm in Python. Detail the four core pillars (Encapsulation, Abstraction, Inheritance, and Polymorphism), explain private vs protected naming conventions, and demonstrate inheritance with a syntactically complete code example.",
			"correct_answer": "Comprehensive breakdown of Python OOP pillars, name mangling with double underscores (`__`), single underscore conventions (`_`), and clean inheritance demonstration.",
			"marks": 5,
			"difficulty": "Hard",
			"source": source_tag,
			"answer_key_detail": (
				"Marking Scheme (5 Marks Total):\n"
				"• Theoretical Concept & Definitions [1 Mark]: Explicit definition and purpose of the 4 OOP pillars in Python.\n"
				"• Encapsulation & Access Modifiers [1 Mark]: Detailed explanation of `_protected` (convention) vs `__private` (name mangling: `_ClassName__var`).\n"
				"• Inheritance Architecture & `super()` [1 Mark]: Mechanics of child class derivation and constructor chaining via `super().__init__()`.\n"
				"• Polymorphism & Dynamic Dispatch [1 Mark]: How method overriding enables interchangeable interfaces at runtime.\n"
				"• Code Implementation [1 Mark]: Complete, error-free Python class hierarchy demonstrating base class, derived class, and method overriding."
			),
			"solution": (
				"1. Core OOP Pillars (1 Mark): Encapsulation bundles data and methods; Abstraction hides implementation complexity; Inheritance promotes code reuse; Polymorphism provides unified interfaces.\n"
				"2. Access Conventions (1 Mark): Python lacks strict access keywords. `_attr` is an advisory private convention. `__attr` invokes name mangling (`_Class__attr`) to prevent subclass collision.\n"
				"3. Inheritance & `super()` (1 Mark): `super()` delegates constructor execution up the MRO tree.\n"
				"4. Code Implementation (2 Marks):\n"
				"```python\n"
				"class Employee:\n"
				"    def __init__(self, name: str, salary: float):\n"
				"        self.name = name\n"
				"        self._salary = salary\n"
				"    def calculate_bonus(self) -> float:\n"
				"        return self._salary * 0.10\n\n"
				"class Manager(Employee):\n"
				"    def __init__(self, name: str, salary: float, department: str):\n"
				"        super().__init__(name, salary)\n"
				"        self.department = department\n"
				"    def calculate_bonus(self) -> float:\n"
				"        return self._salary * 0.20\n"
				"```"
			),
			"internal_choice_question": {
				"question": "OR: Analyze Python's internal Memory Management architecture. Explain Reference Counting, the Generational Garbage Collector (Generations 0, 1, and 2), cyclic reference handling, and the impact of the Global Interpreter Lock (GIL) on multithreaded concurrency.",
				"marks": 5,
				"difficulty": "Hard",
				"source": source_tag,
				"correct_answer": "Complete analysis of CPython reference counters (`ob_refcnt`), cyclic garbage detection algorithm across 3 generations, and GIL concurrency limits.",
				"answer_key_detail": (
					"Marking Scheme (5 Marks Total):\n"
					"• Reference Counting Mechanics [1 Mark]: How `ob_refcnt` increments on assignment/passing and decrements on `del` or scope exit, triggering immediate deallocation at 0.\n"
					"• Cyclic Garbage Collection [1 Mark]: Why reference counting fails on circular references (e.g. `a.ref = b; b.ref = a`).\n"
					"• Generational GC Architecture [1 Mark]: Breakdown of Generations 0, 1, and 2 based on object survival heuristics.\n"
					"• Global Interpreter Lock (GIL) [1 Mark]: Thread synchronization mechanism ensuring thread-safe reference counting in CPython.\n"
					"• Performance & Concurrency Trade-offs [1 Mark]: CPU-bound multithreading limitations vs multiprocessing or asyncio solutions."
				),
				"solution": (
					"1. Reference Counting: Every object contains an `ob_refcnt`. When zero, memory is immediately released back to Python's memory allocator (PyMalloc).\n"
					"2. Cyclic References: Objects referencing each other never reach count zero. Python's cyclic GC scans pointer graphs to identify isolated reference islands.\n"
					"3. Generational Heuristics: New objects start in Generation 0. Surviving garbage collection cycles promotes them to Gen 1 and Gen 2, which are scanned less frequently.\n"
					"4. The GIL: Protects internal memory structures from race conditions. Consequently, threads cannot execute bytecode concurrently across multiple CPU cores; developers use `multiprocessing` for CPU-bound parallelism."
				),
			},
		},
		{
			"question": "Examine Django's MVT (Model-View-Template) architectural pattern. Detail how HTTP requests traverse from URL routing to view processing, how the ORM manages relational data schemas, and how templates render dynamic contexts with security protections against Cross-Site Scripting (XSS).",
			"correct_answer": "Full end-to-end trace of Django's HTTP request pipeline: urls.py -> Middleware -> views.py -> models.py (ORM) -> template rendering with auto-escaping.",
			"marks": 5,
			"difficulty": "Hard",
			"source": source_tag,
			"answer_key_detail": (
				"Marking Scheme (5 Marks Total):\n"
				"• Architecture & Request Lifecycle [1 Mark]: Sequential flow from WSGI/ASGI entry through URL pattern matching to view dispatch.\n"
				"• View Business Logic [1 Mark]: Processing of HttpRequest objects and generation of HttpResponse / JsonResponse.\n"
				"• Model & ORM Abstraction [1 Mark]: Mapping Python class definitions to relational database tables and migrations.\n"
				"• Template System & Security [1 Mark]: Context injection, template tags/filters, and automatic HTML escaping for XSS prevention.\n"
				"• Architectural Comparison [1 Mark]: Clear distinction between Django MVT and classic MVC (where the framework itself serves as Controller)."
			),
			"solution": (
				"1. Request Pipeline: Web server passes request to Django's WSGI handler. `MIDDLEWARE` processes authentication and security headers. `urls.py` resolves URL patterns to view callables.\n"
				"2. Views: Views execute business logic, querying the database through Model ORM managers (`Model.objects.filter(...)`).\n"
				"3. Models: Models define schema fields, relationships (ForeignKey, ManyToManyField), and validation rules.\n"
				"4. Templates: Views pass dictionary contexts to templates. Django's template engine interpolates variables (`{{ var }}`) with automatic HTML character escaping.\n"
				"5. MVT vs MVC: In MVT, the Model is the data, the View is the controller, and the Template is the view; Django itself acts as the overall controller."
			),
			"internal_choice_question": {
				"question": "OR: Analyze Relational Database Design and the ACID properties in modern full-stack web applications. Detail Atomicity, Consistency, Isolation, and Durability, explain database normalization (1NF, 2NF, 3NF), and discuss how database transactions prevent race conditions during concurrent financial updates.",
				"marks": 5,
				"difficulty": "Hard",
				"source": source_tag,
				"correct_answer": "Complete analysis of ACID guarantees, normalization rules from 1NF through 3NF, and database transactions (`transaction.atomic`) preventing lost updates.",
				"answer_key_detail": (
					"Marking Scheme (5 Marks Total):\n"
					"• ACID Properties Definition [1 Mark]: Detailed technical definition of Atomicity, Consistency, Isolation, and Durability.\n"
					"• Normalization Principles (1NF, 2NF, 3NF) [1.5 Marks]: Atomic attributes (1NF), elimination of partial dependencies (2NF), and elimination of transitive dependencies (3NF).\n"
					"• Concurrency & Isolation Levels [1 Mark]: Read Uncommitted, Read Committed, Repeatable Read, and Serializable levels.\n"
					"• Transaction Management & Code [1.5 Marks]: Implementing atomic transactions and row-locking (`select_for_update()`) in web backends to avoid race conditions."
				),
				"solution": (
					"1. ACID Properties: Atomicity (all-or-nothing execution), Consistency (maintaining schema constraints), Isolation (concurrent transactions do not interfere), Durability (committed data survives crashes).\n"
					"2. Normalization: 1NF requires scalar values without repeating groups; 2NF requires 1NF and no non-key attribute dependent on a subset of the candidate key; 3NF requires 2NF and no transitive functional dependencies.\n"
					"3. Race Conditions: In financial transfers, concurrent debits can overdraft accounts. Wrapping updates in `transaction.atomic()` with `select_for_update()` locks rows until commit, ensuring deterministic serial execution."
				),
			},
		},
		{
			"question": "Detail the architecture of Asynchronous Programming in modern Python using `asyncio`. Compare asynchronous coroutines (`async`/`await`) with OS-level multithreading and multiprocessing, explain event loop mechanics, and illustrate asynchronous concurrent I/O with code.",
			"correct_answer": "In-depth breakdown of single-threaded cooperative multitasking via event loop, comparison with threads and processes, and `asyncio.gather()` code example.",
			"marks": 5,
			"difficulty": "Hard",
			"source": source_tag,
			"answer_key_detail": (
				"Marking Scheme (5 Marks Total):\n"
				"• Event Loop Architecture [1 Mark]: Single-threaded event loop multiplexing asynchronous I/O sockets without OS thread overhead.\n"
				"• Coroutines & `async`/`await` [1 Mark]: Mechanics of pausing execution on I/O boundaries and relinquishing control to pending tasks.\n"
				"• Comparison Matrix [1 Mark]: Explicit trade-off comparison across Asyncio (I/O bound), Threading (I/O bound with GIL), and Multiprocessing (CPU bound).\n"
				"• Code Implementation [1 Mark]: Syntactically valid asynchronous routine utilizing `async def`, `await`, and `asyncio.gather()`.\n"
				"• Production Pitfalls & Best Practices [1 Mark]: Warning against blocking calls (e.g. `time.sleep()`, synchronous DB drivers) that freeze the event loop."
			),
			"solution": (
				"1. Event Loop: Python's `asyncio` runs a single-threaded loop that monitors file descriptors and network sockets using epoll/kqueue.\n"
				"2. Coroutines: `async def` defines a coroutine. The `await` keyword yields execution back to the loop until the awaited Future completes.\n"
				"3. Comparison:\n"
				"- Asyncio: Cooperative, low memory footprint, ideal for 10,000+ concurrent network connections.\n"
				"- Threading: Preemptive, higher memory overhead, subject to CPython GIL.\n"
				"- Multiprocessing: Multiple distinct Python processes, bypasses GIL, ideal for heavy CPU calculations.\n"
				"4. Code Example:\n"
				"```python\n"
				"import asyncio\n"
				"async def fetch_data(item_id):\n"
				"    await asyncio.sleep(0.1)\n"
				"    return {'id': item_id, 'status': 'complete'}\n\n"
				"async def main():\n"
				"    tasks = [fetch_data(i) for i in range(5)]\n"
				"    results = await asyncio.gather(*tasks)\n"
				"```"
			),
			"internal_choice_question": {
				"question": "OR: Analyze Web Security vulnerabilities and defense strategies in full-stack Python applications. Detail SQL Injection, Cross-Site Scripting (XSS), and Cross-Site Request Forgery (CSRF). Explain the root cause of each vulnerability and the concrete countermeasures enforced by modern frameworks.",
				"marks": 5,
				"difficulty": "Hard",
				"source": source_tag,
				"correct_answer": "Complete security analysis of SQLi, XSS (stored, reflected), and CSRF with parameterized queries, template auto-escaping, and CSRF token cookies.",
				"answer_key_detail": (
					"Marking Scheme (5 Marks Total):\n"
					"• SQL Injection (SQLi) [1.5 Marks]: Root cause (untrusted string concatenation in SQL queries) and mitigation (parameterized queries / ORM prepared statements).\n"
					"• Cross-Site Scripting (XSS) [1.5 Marks]: Root cause (untrusted script execution in user browsers) and mitigation (contextual output encoding, Content Security Policy, template auto-escaping).\n"
					"• Cross-Site Request Forgery (CSRF) [1 Mark]: Root cause (ambient credentials exploited across cross-origin requests) and mitigation (SameSite cookies and cryptographic CSRF tokens).\n"
					"• Password Hashing & Encryption [1 Mark]: Utilizing slow cryptographic hashing algorithms (bcrypt, Argon2) with per-user salt."
				),
				"solution": (
					"1. SQL Injection: Occurs when user input alters query syntax. Mitigation: Never concatenate SQL strings; use parameterized queries or ORMs that separate query code from data parameters.\n"
					"2. XSS: Attackers inject malicious JavaScript. Stored XSS persists in databases; Reflected XSS reflects off immediate parameters. Mitigation: Context-aware HTML entity encoding and strict Content Security Policy (CSP).\n"
					"3. CSRF: Tricks authenticated browsers into submitting malicious state-changing requests. Mitigation: Cryptographic anti-CSRF tokens embedded in forms and verified against session cookies upon submission.\n"
					"4. Password Storage: Plaintext or MD5/SHA1 is insecure. Use salted, key-stretching algorithms like Argon2id or bcrypt."
				),
			},
		},
		{
			"question": "Examine the Git Version Control workflow and branching strategies for full-stack engineering teams. Explain Git's internal object store (blobs, trees, commits, and tags), detail the differences between `git merge` and `git rebase`, and outline a standard GitFlow release process.",
			"correct_answer": "Detailed analysis of Git DAG and internal objects (blob, tree, commit), comparison of non-destructive merges vs linear rebase history, and GitFlow branches.",
			"marks": 5,
			"difficulty": "Hard",
			"source": source_tag,
			"answer_key_detail": (
				"Marking Scheme (5 Marks Total):\n"
				"• Internal Object Model [1 Mark]: Explanation of SHA-1 content-addressable storage for Blobs (files), Trees (directories), Commits (metadata/pointers), and Annotated Tags.\n"
				"• Three Trees Architecture [1 Mark]: Working Directory -> Staging Area (Index) -> Git Repository (HEAD).\n"
				"• Merge vs Rebase [1.5 Marks]: Non-destructive 3-way merge commits vs replaying commits on top of base branch to maintain a linear history.\n"
				"• GitFlow Strategy [1 Mark]: Distinct roles of `main`, `develop`, `feature/*`, `release/*`, and `hotfix/*` branches.\n"
				"• Merge Conflict Resolution [0.5 Mark]: Identifying conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`) and verifying post-merge integrity."
			),
			"solution": (
				"1. Git Internal Store: Git is a directed acyclic graph (DAG) of content-addressed objects stored under `.git/objects`. Blobs hold raw file content; Trees map filenames to blobs/subtrees; Commits reference a root tree, parent commits, author, and commit message.\n"
				"2. Three Areas: Working Directory holds editable files; Staging Area (`git add`) prepares changes; Repository (`git commit`) permanently logs immutable snapshots.\n"
				"3. Merge vs Rebase:\n"
				"- `git merge` creates a merge commit preserving exact historical timeline and commit order.\n"
				"- `git rebase` rewrites history by moving the base of the current branch onto the target branch tip, creating a clean linear history.\n"
				"4. GitFlow: `main` tracks production releases; `develop` aggregates features; developers branch off `develop` into `feature/name` and merge via pull requests."
			),
			"internal_choice_question": {
				"question": "OR: Analyze Software Testing methodologies in Python applications. Differentiate between Unit Testing, Integration Testing, and End-to-End (E2E) testing. Explain test fixtures and test mocks using `unittest.mock`, and write a complete test case verifying an authenticated API endpoint.",
				"marks": 5,
				"difficulty": "Hard",
				"source": source_tag,
				"correct_answer": "Comprehensive testing breakdown across testing pyramid, fixture lifecycle, mocking external I/O with `unittest.mock.patch`, and complete test case code.",
				"answer_key_detail": (
					"Marking Scheme (5 Marks Total):\n"
					"• Testing Pyramid & Types [1 Mark]: Definition and scope of Unit Tests (isolated units), Integration Tests (component interaction), and E2E Tests (user workflows).\n"
					"• Test Fixtures & Lifecycles [1 Mark]: Setup and teardown methods (`setUp()`, `tearDown()` in `unittest` or `@pytest.fixture`).\n"
					"• Mocking Principles [1 Mark]: Purpose of replacing external services (HTTP calls, database connections) using `unittest.mock.MagicMock` and `patch()`.\n"
					"• Code Implementation [1.5 Marks]: Complete test case using `unittest.TestCase` with proper assertions (`assertEqual`, `assertTrue`).\n"
					"• Test Driven Development (TDD) [0.5 Mark]: Explanation of the Red-Green-Refactor development cycle."
				),
				"solution": (
					"1. Testing Pyramid: Unit tests are numerous, fast, and test single functions in isolation. Integration tests verify interactions between modules (e.g. View + Database). E2E tests test full workflows.\n"
					"2. Fixtures: Initialize test state before execution and perform teardown to maintain test idempotency.\n"
					"3. Mocking: `unittest.mock` isolates tests from unreliable or slow third-party APIs by substituting mock objects.\n"
					"4. Code Example:\n"
					"```python\n"
					"import unittest\n"
					"from unittest.mock import patch\n\n"
					"class TestUserAPI(unittest.TestCase):\n"
					"    @patch('my_app.services.fetch_remote_profile')\n"
					"    def test_profile_lookup(self, mock_fetch):\n"
					"        mock_fetch.return_value = {'id': 101, 'role': 'Admin'}\n"
					"        user_data = mock_fetch(101)\n"
					"        self.assertEqual(user_data['role'], 'Admin')\n"
					"```"
				),
			},
		},
	]


def _get_python_application_pool(source_tag: str) -> List[Dict[str, Any]]:
	return [
		{
			"question": "Case Scenario: An e-commerce web application built with Django experiences severe response latency when rendering customer order history. Query profiling reveals that fetching 100 customer orders triggers 101 separate database queries (the N+1 query problem). Diagnose the root cause of this defect and formulate a concrete solution using Django's ORM optimization methods.",
			"correct_answer": "Diagnosis of un-joined foreign key access inside template loops and solution using `select_related('customer')` or `prefetch_related('items')`.",
			"marks": 4,
			"difficulty": "Hard",
			"source": source_tag,
			"answer_key_detail": (
				"Marking Scheme (4 Marks Total):\n"
				"• Sub-part (a) Problem Diagnosis [2 Marks]: Explicitly explains that iterating over 100 order objects while accessing related ForeignKeys (e.g., `order.customer.name`) triggers 1 initial query for orders plus 100 individual queries for each customer.\n"
				"• Sub-part (b) Technical Remedy & Implementation [2 Marks]: Demonstrates usage of `select_related('customer')` (SQL JOIN) for single-valued relationships or `prefetch_related('items')` for multi-valued relationships, reducing queries from 101 to 1 or 2."
			),
			"solution": (
				"Sub-part (a) Diagnosis (2 Marks):\n"
				"The N+1 problem occurs when a query fetches N records (e.g., `orders = Order.objects.all()`), and subsequent code accesses a related ForeignKey attribute inside a loop (`for o in orders: print(o.customer.name)`). Django's lazy ORM executes an additional SQL query for each iteration, degrading database throughput.\n\n"
				"Sub-part (b) Remedy (2 Marks):\n"
				"Refactor the QuerySet using `select_related`:\n"
				"```python\n"
				"optimized_orders = Order.objects.select_related('customer').prefetch_related('order_items').all()\n"
				"```\n"
				"`select_related` performs an SQL `INNER JOIN` (1 query total for orders and customers). `prefetch_related` executes one additional query using `IN (...)` for order items, collapsing 101+ queries into exactly 2."
			),
			"internal_choice_question": {
				"question": "OR: Case Scenario: A Python microservice application suffers from recurring memory leaks under sustained production load. Investigation identifies that event handlers store circular references to user session instances that are never garbage collected by reference counting alone. Diagnose why reference counting fails and formulate an architectural remedy using weak references (`weakref` module).",
				"marks": 4,
				"difficulty": "Hard",
				"source": source_tag,
				"correct_answer": "Diagnosis of cyclic reference graphs maintaining non-zero `ob_refcnt` and solution utilizing `weakref.ref` or `weakref.WeakValueDictionary`.",
				"answer_key_detail": (
					"Marking Scheme (4 Marks Total):\n"
					"• Sub-part (a) Problem Diagnosis [2 Marks]: Identifies that when Session references EventHandler and EventHandler references Session, reference counts never drop to 0, preventing immediate deallocation.\n"
					"• Sub-part (b) Architectural Remedy [2 Marks]: Implements `weakref.ref()` or `weakref.WeakKeyDictionary` allowing sessions to be deallocated naturally when no strong references remain."
				),
				"solution": (
					"Sub-part (a) Diagnosis (2 Marks):\n"
					"Python's primary memory management is reference counting. When object A points to B and B points to A, their reference counts remain at least 1 even after all outer scope variables are deleted. If generational GC is delayed or objects have legacy `__del__` methods, memory leaks accumulate.\n\n"
					"Sub-part (b) Remedy (2 Marks):\n"
					"Break strong reference cycles using the `weakref` module:\n"
					"```python\n"
					"import weakref\n"
					"class EventHandler:\n"
					"    def __init__(self, session):\n"
					"        self._session_ref = weakref.ref(session)\n"
					"    @property\n"
					"    def session(self):\n"
					"        return self._session_ref()\n"
					"```\n"
					"Weak references allow tracking session objects without incrementing their reference count, enabling immediate garbage collection."
				),
			},
		},
		{
			"question": "Case Scenario: A digital banking web application encounters race conditions during simultaneous fund withdrawals. When a user with a balance of $100 submits two concurrent withdrawal requests of $80 within milliseconds, both requests read the $100 balance, deduce sufficient funds, and deduct $80, resulting in an illegal negative balance of -$60. Diagnose the concurrency defect and formulate a solution using atomic transactions and row-level locking.",
			"correct_answer": "Diagnosis of Check-Then-Act race condition and implementation of `transaction.atomic()` with `select_for_update()` in Django ORM.",
			"marks": 4,
			"difficulty": "Hard",
			"source": source_tag,
			"answer_key_detail": (
				"Marking Scheme (4 Marks Total):\n"
				"• Sub-part (a) Problem Diagnosis [2 Marks]: Identifies the Check-Then-Act concurrency flaw where interleaved reads occur before writes commit, causing lost updates.\n"
				"• Sub-part (b) Technical Remedy [2 Marks]: Formulates the database fix using `transaction.atomic()` and `select_for_update()` to enforce exclusive row locks."
			),
			"solution": (
				"Sub-part (a) Concurrency Diagnosis (2 Marks):\n"
				"This is a classic 'lost update' race condition. Both thread 1 and thread 2 execute `SELECT balance FROM account WHERE id = 1` concurrently, observing $100. Both validate `100 >= 80`. Thread 1 writes $20, and thread 2 immediately overwrites balance to $20 (or drops to -$60 if using relative subtraction).\n\n"
				"Sub-part (b) Database Remedy (2 Marks):\n"
				"```python\n"
				"from django.db import transaction\n\n"
				"def withdraw(account_id, amount):\n"
				"    with transaction.atomic():\n"
				"        account = Account.objects.select_for_update().get(id=account_id)\n"
				"        if account.balance >= amount:\n"
				"            account.balance -= amount\n"
				"            account.save()\n"
				"            return True\n"
				"        return False\n"
				"```\n"
				"`select_for_update()` executes `SELECT ... FOR UPDATE`, placing an exclusive row-level lock in PostgreSQL/MySQL. The second thread blocks until the first transaction commits, reading the updated balance."
			),
			"internal_choice_question": {
				"question": "OR: Case Scenario: A Python backend API endpoint crashes intermittently with `UnboundLocalError: local variable 'total_count' referenced before assignment` during request processing. Diagnose why Python raises this exception for enclosing-scope variables and formulate the fix using the `global` and `nonlocal` keywords.",
				"marks": 4,
				"difficulty": "Hard",
				"source": source_tag,
				"correct_answer": "Diagnosis of compile-time local variable detection upon assignment and fix utilizing `nonlocal` keyword for nested functions.",
				"answer_key_detail": (
					"Marking Scheme (4 Marks Total):\n"
					"• Sub-part (a) Language Semantics Diagnosis [2 Marks]: Explains that Python parses assignment statements at compile-time; if a variable is assigned anywhere inside a function, it is treated as local throughout that entire function.\n"
					"• Sub-part (b) Code Fix & Explanation [2 Marks]: Demonstrates `nonlocal total_count` (for enclosing functions) or `global total_count` (for module globals)."
				),
				"solution": (
					"Sub-part (a) Diagnosis (2 Marks):\n"
					"In Python, if a variable is assigned a value anywhere within a function (`total_count += 1` translates to `total_count = total_count + 1`), Python marks `total_count` as local to that scope at compile time. When the function tries to read `total_count` on the right side before assignment, it finds the unassigned local variable and raises `UnboundLocalError`.\n\n"
					"Sub-part (b) Remedy (2 Marks):\n"
					"```python\n"
					"def outer_service():\n"
					"    total_count = 0\n"
					"    def increment():\n"
					"        nonlocal total_count\n"
					"        total_count += 1\n"
					"        return total_count\n"
					"    return increment\n"
					"```\n"
					"Using `nonlocal` explicitly binds the identifier to the nearest enclosing scope variable, permitting modification without shadowing."
				),
			},
		},
		{
			"question": "Case Scenario: A software development firm is preparing to deploy a full-stack Python web application to production on cloud infrastructure. Outline the complete production deployment architecture incorporating Nginx, Gunicorn (WSGI), PostgreSQL, and environment variable configuration. Explain the distinct responsibility of each layer in handling incoming HTTP client traffic.",
			"correct_answer": "Full architectural specification: Nginx as reverse proxy/SSL terminator -> Gunicorn as WSGI app server -> Django Python application -> PostgreSQL database.",
			"marks": 4,
			"difficulty": "Hard",
			"source": source_tag,
			"answer_key_detail": (
				"Marking Scheme (4 Marks Total):\n"
				"• Sub-part (a) Architecture Diagram & Component Responsibilities [2 Marks]: Details Nginx (reverse proxy, TLS termination, static file serving) and Gunicorn (WSGI process supervisor managing Python worker processes).\n"
				"• Sub-part (b) Security & Data Isolation [2 Marks]: Details database connection pooling with PostgreSQL and environment variable management (Twelve-Factor App) for secrets isolation."
			),
			"solution": (
				"Sub-part (a) Architectural Layers (2 Marks):\n"
				"1. Nginx (Reverse Proxy): Sits at the public edge. Handles TLS/SSL termination, buffers slow clients, protects against DDoS attacks, and serves static/media files directly from disk without touching Python.\n"
				"2. Gunicorn (WSGI Server): Communicates with Nginx via a UNIX socket. Manages a pool of pre-forked Python worker processes (`workers = 2 * CPU_CORES + 1`) to execute Django application code.\n\n"
				"Sub-part (b) Database & Configuration (2 Marks):\n"
				"3. PostgreSQL: Provides ACID-compliant relational data persistence. Connection pooling (e.g. PgBouncer) prevents database connection exhaustion.\n"
				"4. Environment Configuration: Production secrets (`SECRET_KEY`, `DATABASE_URL`) are injected via OS environment variables adhering to the Twelve-Factor App methodology."
			),
			"internal_choice_question": {
				"question": "OR: Case Scenario: An automated web data extraction pipeline built with Python encounters frequent connection dropouts, HTTP 429 (Too Many Requests) rate-limiting errors, and memory exhaustion when scraping large document repositories. Formulate a robust architecture implementing exponential backoff retry logic, session connection pooling, and streaming downloads.",
				"marks": 4,
				"difficulty": "Hard",
				"source": source_tag,
				"correct_answer": "Architecture incorporating `requests.Session` with `HTTPAdapter`, exponential backoff retry strategies, and `stream=True` chunked response handling.",
				"answer_key_detail": (
					"Marking Scheme (4 Marks Total):\n"
					"• Sub-part (a) Network Resilience & Rate Limiting [2 Marks]: Explains exponential backoff algorithms with jitter to handle HTTP 429 and transient 500-series errors.\n"
					"• Sub-part (b) Connection Pooling & Memory Streaming [2 Marks]: Demonstrates `requests.Session` with urllib3 `Retry` adapter and `response.iter_content(chunk_size)` for constant O(1) memory streaming."
				),
				"solution": (
					"Sub-part (a) Exponential Backoff (2 Marks):\n"
					"When receiving 429 or 503, wait $T = \text{base} \times 2^{\text{retry}} + \text{jitter}$ seconds before retrying. This desynchronizes requests, preventing server thundering herds.\n\n"
					"Sub-part (b) Implementation (2 Marks):\n"
					"```python\n"
					"import requests\n"
					"from urllib3.util import Retry\n"
					"from requests.adapters import HTTPAdapter\n\n"
					"session = requests.Session()\n"
					"retries = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])\n"
					"session.mount('https://', HTTPAdapter(max_retries=retries))\n\n"
					"with session.get('https://example.com/largefile.zip', stream=True) as resp:\n"
					"    with open('file.zip', 'wb') as f:\n"
					"        for chunk in resp.iter_content(chunk_size=8192):\n"
					"            f.write(chunk)\n"
					"```"
				),
			},
		},
	]


# =====================================================================
# COMPUTER SCIENCE & ARCHITECTURE QUESTION POOL
# =====================================================================

def _get_cs_mcq_pool(source_tag: str) -> List[Dict[str, Any]]:
	return [
		{
			"question": "Which component of the Central Processing Unit (CPU) is directly responsible for executing mathematical calculations and logical comparisons?",
			"options": ["(A) Control Unit (CU)", "(B) Arithmetic Logic Unit (ALU)", "(C) Program Counter (PC)", "(D) Memory Address Register (MAR)"],
			"correct_answer": "(B) Arithmetic Logic Unit (ALU)",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (B) Arithmetic Logic Unit (ALU). Evaluation Criterion: Full 1 mark awarded for identifying the ALU as the primary sub-component of the CPU that carries out integer arithmetic and logical bitwise operations.",
			"solution": "The ALU performs arithmetic (addition, subtraction) and logic (AND, OR, NOT, comparisons). The Control Unit fetches and decodes instructions, while registers provide temporary high-speed storage.",
			"internal_choice_question": None,
		},
		{
			"question": "What is the defining characteristic of the classic Von Neumann computer architecture?",
			"options": ["(A) Physically separate physical memories and buses for program instructions and data", "(B) Shared memory space and common system bus for both instructions and data", "(C) Elimination of the Control Unit in favor of direct hardware interrupts", "(D) Exclusive reliance on asynchronous analog vacuum circuits"],
			"correct_answer": "(B) Shared memory space and common system bus for both instructions and data",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (B) Shared memory space and common system bus for both instructions and data. Evaluation Criterion: Full 1 mark awarded for articulating the stored-program concept where instructions and data share primary memory.",
			"solution": "The Von Neumann architecture features a stored-program model where both instructions and operational data reside in the same physical memory, leading to the Von Neumann bottleneck.",
			"internal_choice_question": None,
		},
		{
			"question": "Which dedicated internal CPU register stores the memory address of the next instruction waiting to be fetched and executed?",
			"options": ["(A) Accumulator (ACC)", "(B) Instruction Register (IR)", "(C) Program Counter (PC)", "(D) Memory Data Register (MDR)"],
			"correct_answer": "(C) Program Counter (PC)",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (C) Program Counter (PC). Evaluation Criterion: Full 1 mark awarded for identifying the Program Counter (PC) as the register holding the address of the next sequential instruction.",
			"solution": "The Program Counter (PC) holds the memory address of the next instruction to fetch. Once fetched, the PC automatically increments unless a branch or jump occurs.",
			"internal_choice_question": None,
		},
		{
			"question": "What is the average-case time complexity of the QuickSort algorithm when sorting an array of n elements?",
			"options": ["(A) O(n)", "(B) O(n log n)", "(C) O(n^2)", "(D) O(log n)"],
			"correct_answer": "(B) O(n log n)",
			"marks": 1,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (B) O(n log n). Evaluation Criterion: Full 1 mark awarded for stating QuickSort's average-case asymptotic time complexity of O(n log n).",
			"solution": "QuickSort uses a divide-and-conquer strategy. On average, it divides the array into two roughly equal halves, producing log n levels of recursion with O(n) partitioning work per level, yielding O(n log n).",
			"internal_choice_question": None,
		},
		{
			"question": "Under what condition does the standard QuickSort algorithm with first-element pivot selection exhibit its worst-case time complexity of O(n^2)?",
			"options": ["(A) When elements are randomly shuffled with uniform distribution", "(B) When the input array is already sorted in ascending or descending order", "(C) When all array elements are powers of two", "(D) When the array length is a prime number"],
			"correct_answer": "(B) When the input array is already sorted in ascending or descending order",
			"marks": 1,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (B) When the input array is already sorted in ascending or descending order. Evaluation Criterion: Full 1 mark awarded for identifying that sorted inputs produce unbalanced partitions of size 1 and n-1.",
			"solution": "If the array is already sorted, picking the first element creates maximally unbalanced partitions: 0 elements on one side and n-1 on the other, degrading recursion depth to n and time to O(n^2).",
			"internal_choice_question": None,
		},
		{
			"question": "What is the worst-case time complexity of the BubbleSort algorithm?",
			"options": ["(A) O(1)", "(B) O(log n)", "(C) O(n log n)", "(D) O(n^2)"],
			"correct_answer": "(D) O(n^2)",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (D) O(n^2). Evaluation Criterion: Full 1 mark awarded for stating that BubbleSort performs n*(n-1)/2 comparisons in the worst case, yielding O(n^2).",
			"solution": "In reverse-sorted inputs, BubbleSort compares and swaps every adjacent pair across n passes, requiring n*(n-1)/2 comparisons, which is O(n^2).",
			"internal_choice_question": None,
		},
		{
			"question": "In the memory hierarchy of modern computing systems, which memory level provides the fastest access latency?",
			"options": ["(A) Main Memory (DRAM)", "(B) Solid State Drive (NVMe SSD)", "(C) CPU Registers", "(D) Level 3 (L3) Cache"],
			"correct_answer": "(C) CPU Registers",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (C) CPU Registers. Evaluation Criterion: Full 1 mark awarded for identifying internal CPU registers as the fastest storage located directly inside CPU processing pipelines.",
			"solution": "CPU Registers can be accessed in a single CPU clock cycle (sub-nanosecond). L1/L2/L3 caches take 3-40 cycles, DRAM takes ~100-200 cycles, and SSDs take microseconds.",
			"internal_choice_question": None,
		},
		{
			"question": "What four sequential phases constitute the classic CPU Instruction Cycle?",
			"options": ["(A) Compile, Assemble, Link, Load", "(B) Fetch, Decode, Execute, Store", "(C) Push, Pop, Peek, Clear", "(D) Input, Process, Output, Archive"],
			"correct_answer": "(B) Fetch, Decode, Execute, Store",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (B) Fetch, Decode, Execute, Store. Evaluation Criterion: Full 1 mark awarded for identifying the 4 stages of the machine instruction execution cycle.",
			"solution": "The CPU fetches the instruction from memory, decodes opcodes in the Control Unit, executes signals via the ALU/datapath, and stores (writes back) results to registers or RAM.",
			"internal_choice_question": None,
		},
		{
			"question": "Which computer architecture eliminates the Von Neumann bottleneck by employing separate physical buses and memory units for instructions and data?",
			"options": ["(A) Harvard Architecture", "(B) Princeton Architecture", "(C) Turing Machine", "(D) CISC Monolithic Architecture"],
			"correct_answer": "(A) Harvard Architecture",
			"marks": 1,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (A) Harvard Architecture. Evaluation Criterion: Full 1 mark awarded for identifying Harvard architecture with isolated instruction and data buses.",
			"solution": "Harvard architecture provides separate memory and signal buses for code and data, allowing simultaneous instruction fetch and data read/write without bus contention.",
			"internal_choice_question": None,
		},
		{
			"question": "What type of data structure operates on a Last-In, First-Out (LIFO) access principle?",
			"options": ["(A) Queue", "(B) Stack", "(C) Hash Map", "(D) Binary Search Tree"],
			"correct_answer": "(B) Stack",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (B) Stack. Evaluation Criterion: Full 1 mark awarded for identifying Stack as the LIFO structure supporting push and pop operations.",
			"solution": "A Stack operates on LIFO (Last-In, First-Out), where the most recently pushed element is the first popped. Queues operate on FIFO (First-In, First-Out).",
			"internal_choice_question": None,
		},
		{
			"question": "What does the term 'locality of reference' refer to in the context of computer cache design?",
			"options": ["(A) Translating IP addresses to physical MAC addresses", "(B) The tendency of processors to access the same memory locations repeatedly (temporal) or nearby locations (spatial)", "(C) Restricting memory read operations strictly to regional cloud data centers", "(D) Allocating contiguous disk blocks during filesystem formatting"],
			"correct_answer": "(B) The tendency of processors to access the same memory locations repeatedly (temporal) or nearby locations (spatial)",
			"marks": 1,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (B) Locality of Reference. Evaluation Criterion: Full 1 mark awarded for defining temporal locality (recently accessed items) and spatial locality (neighboring items).",
			"solution": "Cache memory efficiency is founded on locality of reference: temporal locality (accessed data will be accessed again soon) and spatial locality (adjacent memory addresses will be accessed soon).",
			"internal_choice_question": None,
		},
		{
			"question": "Which system bus is responsible for transmitting memory addresses from the CPU to main memory and peripheral controllers?",
			"options": ["(A) Data Bus", "(B) Address Bus", "(C) Control Bus", "(D) Power Bus"],
			"correct_answer": "(B) Address Bus",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (B) Address Bus. Evaluation Criterion: Full 1 mark awarded for identifying the Address Bus as the unidirectional bus specifying target memory locations.",
			"solution": "The Address Bus carries memory addresses from the CPU to memory. The Data Bus carries actual data bidirectionally. The Control Bus transmits timing and command signals.",
			"internal_choice_question": None,
		},
		{
			"question": "What is the time complexity of searching for an element in a balanced Binary Search Tree (BST) containing n nodes?",
			"options": ["(A) O(1)", "(B) O(log n)", "(C) O(n)", "(D) O(n log n)"],
			"correct_answer": "(B) O(log n)",
			"marks": 1,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (B) O(log n). Evaluation Criterion: Full 1 mark awarded for identifying logarithmic O(log n) search time in balanced binary search trees.",
			"solution": "In a balanced BST (e.g. AVL, Red-Black), the tree height is log2(n). Each comparison halves the remaining search space, yielding O(log n) search complexity.",
			"internal_choice_question": None,
		},
		{
			"question": "Which register holds the instruction currently being decoded and executed by the Control Unit?",
			"options": ["(A) Instruction Register (IR)", "(B) Program Counter (PC)", "(C) Memory Buffer Register (MBR)", "(D) Status Flag Register"],
			"correct_answer": "(A) Instruction Register (IR)",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (A) Instruction Register (IR). Evaluation Criterion: Full 1 mark awarded for identifying the IR as holding the active instruction during decoding.",
			"solution": "Once an instruction is fetched from memory via the MDR, it is placed into the Instruction Register (IR) where its opcode and operands are decoded by the Control Unit.",
			"internal_choice_question": None,
		},
		{
			"question": "What algorithm design paradigm is utilized by MergeSort and QuickSort?",
			"options": ["(A) Greedy Approach", "(B) Dynamic Programming", "(C) Divide and Conquer", "(D) Backtracking"],
			"correct_answer": "(C) Divide and Conquer",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (C) Divide and Conquer. Evaluation Criterion: Full 1 mark awarded for identifying the Divide and Conquer paradigm (divide, conquer subproblems, combine).",
			"solution": "Divide and Conquer breaks a problem into smaller subproblems of the same type, solves them recursively, and combines their solutions to solve the original problem.",
			"internal_choice_question": None,
		},
		{
			"question": "What is the primary function of the Control Unit (CU) inside the CPU?",
			"options": ["(A) Storing operating system files permanently on disk", "(B) Directing and coordinating operations of the CPU by fetching, decoding, and generating control signals", "(C) Cooling the microprocessor during thermal throttling", "(D) Converting optical network packets into audio signals"],
			"correct_answer": "(B) Directing and coordinating operations of the CPU by fetching, decoding, and generating control signals",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (B) Directing and coordinating operations of the CPU. Evaluation Criterion: Full 1 mark awarded for identifying the Control Unit's role in orchestrating instruction dispatch.",
			"solution": "The Control Unit directs the flow of data through the CPU. It manages the fetch-decode-execute cycle and issues timing/control signals to the ALU, registers, and memory.",
			"internal_choice_question": None,
		},
		{
			"question": "Which sorting algorithm is guaranteed to be stable and have an O(n log n) worst-case time complexity?",
			"options": ["(A) QuickSort", "(B) HeapSort", "(C) MergeSort", "(D) SelectionSort"],
			"correct_answer": "(C) MergeSort",
			"marks": 1,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (C) MergeSort. Evaluation Criterion: Full 1 mark awarded for recognizing MergeSort preserves relative order of duplicate elements with O(n log n) worst case.",
			"solution": "MergeSort divides the array in half and merges sorted halves, maintaining O(n log n) in best, average, and worst cases, and is stable (equal keys maintain initial order).",
			"internal_choice_question": None,
		},
		{
			"question": "What is the purpose of the Memory Address Register (MAR)?",
			"options": ["(A) Holds the data read from or written to memory", "(B) Holds the memory address of the location in main memory currently being read from or written to", "(C) Stores the CPU clock frequency", "(D) Manages graphical rendering shaders"],
			"correct_answer": "(B) Holds the memory address of the location in main memory currently being read from or written to",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (B) Memory Address Register (MAR). Evaluation Criterion: Full 1 mark awarded for identifying the MAR as connected to the address bus holding the target address.",
			"solution": "The MAR holds the address on the address bus where data is to be read or written. The MDR (Memory Data Register) holds the actual data payload.",
			"internal_choice_question": None,
		},
		{
			"question": "Which of the following describes the 'Von Neumann Bottleneck'?",
			"options": ["(A) Inability of the CPU to perform floating point division", "(B) Throughput limitation caused by the shared bus between CPU and memory being slower than CPU execution speeds", "(C) Thermal degradation of silicon transistors under high voltages", "(D) Limited hard drive capacity on personal workstations"],
			"correct_answer": "(B) Throughput limitation caused by the shared bus between CPU and memory being slower than CPU execution speeds",
			"marks": 1,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (B) Von Neumann Bottleneck. Evaluation Criterion: Full 1 mark awarded for identifying the data transfer throughput constraint between CPU and RAM.",
			"solution": "The Von Neumann bottleneck occurs because CPU processing speeds vastly outpace the throughput of the shared bus connecting memory, causing the CPU to idle waiting for instructions or data.",
			"internal_choice_question": None,
		},
		{
			"question": "What is the best-case time complexity of an optimized BubbleSort algorithm equipped with a swapped flag on an already-sorted array?",
			"options": ["(A) O(1)", "(B) O(n)", "(C) O(n log n)", "(D) O(n^2)"],
			"correct_answer": "(B) O(n)",
			"marks": 1,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (B) O(n). Evaluation Criterion: Full 1 mark awarded for noting that a swapped flag detects zero swaps on pass 1, terminating in O(n) linear time.",
			"solution": "An optimized BubbleSort sets `swapped = False` before each pass. If no swaps occur during the first pass of n-1 comparisons, the array is already sorted, terminating in O(n) time.",
			"internal_choice_question": None,
		},
	]


def _get_cs_vsa_pool(source_tag: str) -> List[Dict[str, Any]]:
	return [
		{
			"question": "Differentiate between the primary roles of the Arithmetic Logic Unit (ALU) and the Control Unit (CU) in a computer processor.",
			"correct_answer": "The ALU performs mathematical calculations and logical comparisons; the Control Unit fetches, decodes instructions, and orchestrates CPU timing and data flow.",
			"marks": 2,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": (
				"Marking Scheme (2 Marks Total):\n"
				"• Point 1 [1 Mark]: Precise technical definition of the ALU (arithmetic computation, bitwise operations, logical comparisons).\n"
				"• Point 2 [1 Mark]: Precise technical definition of the Control Unit (instruction fetch/decode, clock orchestration, control signals)."
			),
			"solution": "The ALU is the calculating engine of the processor, executing operations like addition, subtraction, AND, and OR. The Control Unit acts as the supervisor, fetching opcodes from memory, decoding them into micro-operations, and issuing control signals across the datapath.",
			"internal_choice_question": None,
		},
		{
			"question": "Explain the stored-program concept in computer architecture and name the scientist who formalized it.",
			"correct_answer": "The stored-program concept stores program instructions and operational data in the same electronic read/write memory; formalized by John von Neumann.",
			"marks": 2,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": (
				"Marking Scheme (2 Marks Total):\n"
				"• Point 1 [1 Mark]: Definition of the stored-program concept (code and data coexisting in primary memory).\n"
				"• Point 2 [1 Mark]: Identification of John von Neumann (1945 First Draft of a Report on the EDVAC)."
			),
			"solution": "Before the stored-program concept, computers were hardwired or reprogrammed with patch cords. The stored-program concept stores instructions in binary form in memory alongside data, enabling computers to reprogram themselves dynamically. Formalized by John von Neumann in 1945.",
			"internal_choice_question": None,
		},
		{
			"question": "Describe the function of the Program Counter (PC) and explain how its value changes during normal linear execution versus a branch instruction.",
			"correct_answer": "The PC stores the address of the next instruction; it increments linearly during normal execution and is loaded with a target branch address during jumps.",
			"marks": 2,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": (
				"Marking Scheme (2 Marks Total):\n"
				"• Point 1 [1 Mark]: Explains normal linear operation where the PC increments by instruction length (e.g. +4 bytes).\n"
				"• Point 2 [1 Mark]: Explains jump/branch operation where the target address overwrites the PC."
			),
			"solution": "The Program Counter points to the next memory address to fetch. In sequential execution, it increments automatically after each fetch. If a conditional branch or jump is executed, the Control Unit overwrites the PC with the target jump address.",
			"internal_choice_question": None,
		},
		{
			"question": "What is the Von Neumann bottleneck and how do modern computer architectures mitigate its performance impact?",
			"correct_answer": "The throughput restriction between CPU and memory across a shared bus; mitigated by multi-level CPU cache hierarchies (L1, L2, L3) and branch prediction.",
			"marks": 2,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": (
				"Marking Scheme (2 Marks Total):\n"
				"• Point 1 [1 Mark]: Explanation of the bottleneck (CPU speed significantly exceeds memory bus throughput).\n"
				"• Point 2 [1 Mark]: Concrete mitigation strategy (integration of high-speed SRAM caches and prefetching)."
			),
			"solution": "The Von Neumann bottleneck describes the delay where a fast CPU idles waiting for memory transfers over a single shared bus. Modern architectures mitigate this by adding high-speed L1/L2/L3 SRAM caches on the CPU die and using hardware prefetchers.",
			"internal_choice_question": None,
		},
		{
			"question": "Explain the divide-and-conquer strategy as implemented in the QuickSort algorithm.",
			"correct_answer": "QuickSort selects a pivot, partitions elements into smaller and larger subsets (Divide), sorts each subset recursively (Conquer), requiring no explicit Combine step.",
			"marks": 2,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": (
				"Marking Scheme (2 Marks Total):\n"
				"• Point 1 [1 Mark]: Division step (pivot selection and partitioning of elements around the pivot).\n"
				"• Point 2 [1 Mark]: Recursive conquer step (independent recursive calls on left and right sub-arrays)."
			),
			"solution": "In QuickSort, the Divide step picks a pivot element and rearranges the array so elements less than the pivot precede it and elements greater follow it. The Conquer step recursively applies QuickSort to both sub-arrays. Because partitioning happens in-place, combining is trivial.",
			"internal_choice_question": None,
		},
		{
			"question": "What are CPU registers, and why are they constructed from Static RAM (SRAM) instead of Dynamic RAM (DRAM)?",
			"correct_answer": "Internal high-speed memory cells directly accessible by CPU execution units; built using flip-flops/SRAM for nanosecond access without refresh cycles.",
			"marks": 2,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": (
				"Marking Scheme (2 Marks Total):\n"
				"• Point 1 [1 Mark]: Definition of registers as on-chip storage holding immediate operands and processor state.\n"
				"• Point 2 [1 Mark]: Distinction between SRAM (fast flip-flops, no refresh required) and DRAM (capacitors requiring periodic refresh cycles)."
			),
			"solution": "Registers are small, ultrafast storage locations built directly into the CPU core. They use SRAM (bistable flip-flop circuits) to operate at CPU clock speeds (GHz frequencies). DRAM uses capacitive storage that requires periodic refresh cycles, making it too slow for register operations.",
			"internal_choice_question": None,
		},
	]


def _get_cs_short_pool(source_tag: str) -> List[Dict[str, Any]]:
	return [
		{
			"question": "Explain the three classic stages of the CPU instruction cycle: Fetch, Decode, and Execute, detailing the role of the PC, MAR, MDR, and IR during each phase.",
			"correct_answer": "Fetch loads the instruction from memory into IR via MAR/MDR and increments PC; Decode interprets opcodes in CU; Execute triggers ALU and datapath signals.",
			"marks": 3,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": (
				"Marking Scheme (3 Marks Total):\n"
				"• Point 1 [1 Mark]: Fetch Phase: PC address placed on MAR -> data read over data bus into MDR -> transferred to IR; PC incremented.\n"
				"• Point 2 [1 Mark]: Decode Phase: Control Unit decodes opcodes and addressing modes in IR to generate control signals.\n"
				"• Point 3 [1 Mark]: Execute Phase: ALU performs operations, registers receive results, or data is stored back to memory."
			),
			"solution": (
				"1. Fetch Phase (1 Mark): The Program Counter (PC) copies its address to the Memory Address Register (MAR). The Control Unit signals a memory read, loading the instruction into the Memory Data Register (MDR), which forwards it to the Instruction Register (IR). PC increments.\n"
				"2. Decode Phase (1 Mark): The Control Unit analyzes the opcode in the IR to determine the operation and readies operand addresses.\n"
				"3. Execute Phase (1 Mark): The ALU and data registers execute the instruction, saving the output to the accumulator or main memory."
			),
			"internal_choice_question": None,
		},
		{
			"question": "Compare QuickSort and BubbleSort algorithms. Detail their average-case time complexities, worst-case time complexities, and memory requirements.",
			"correct_answer": "QuickSort: Average O(n log n), Worst O(n^2), Space O(log n). BubbleSort: Average O(n^2), Worst O(n^2), Space O(1).",
			"marks": 3,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": (
				"Marking Scheme (3 Marks Total):\n"
				"• Point 1 [1 Mark]: Time complexity contrast (QuickSort O(n log n) average vs BubbleSort O(n^2) average).\n"
				"• Point 2 [1 Mark]: Worst-case analysis (both are O(n^2), but QuickSort degrades only on degenerate pivot selection).\n"
				"• Point 3 [1 Mark]: Space complexity and stability (QuickSort requires O(log n) stack space and is unstable; BubbleSort is in-place O(1) and stable)."
			),
			"solution": (
				"1. Average Time: QuickSort operates in O(n log n) by partitioning; BubbleSort operates in O(n^2) by repeatedly comparing adjacent elements.\n"
				"2. Worst-case Time: Both exhibit O(n^2) worst case. In QuickSort, this occurs when partitions are maximally unbalanced. In BubbleSort, it occurs when elements are reversed.\n"
				"3. Auxiliary Space: BubbleSort is strictly in-place with O(1) space. QuickSort requires O(log n) auxiliary stack space for recursion."
			),
			"internal_choice_question": None,
		},
		{
			"question": "Analyze the Memory Hierarchy in computer systems. Explain the trade-offs between access speed, storage capacity, and manufacturing cost across Registers, Caches, RAM, and Secondary Storage.",
			"correct_answer": "As you move from Registers down to Secondary Storage, access latency increases, capacity increases, and cost per bit decreases dramatically.",
			"marks": 3,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": (
				"Marking Scheme (3 Marks Total):\n"
				"• Point 1 [1 Mark]: Speed hierarchy ranking (Registers < L1 Cache < L2 Cache < L3 Cache < DRAM < SSD/HDD).\n"
				"• Point 2 [1 Mark]: Capacity and cost inversion (higher speed levels have tiny capacity and high cost; lower levels provide terabytes at low cost).\n"
				"• Point 3 [1 Mark]: Architectural rationale (caches exploit temporal and spatial locality to give the illusion of memory that is both large and fast)."
			),
			"solution": (
				"1. Latency: Registers (~0.5 ns), L1 Cache (~1 ns), L2 Cache (~4 ns), L3 Cache (~15 ns), Main RAM (~60 ns), NVMe SSD (~25,000 ns).\n"
				"2. Trade-offs: SRAM used in caches requires 6 transistors per bit, making it fast but physically large and expensive. DRAM uses 1 transistor and 1 capacitor, achieving density at lower cost.\n"
				"3. Purpose: By staging hot data in small, ultrafast caches, the CPU achieves high effective memory access times without needing expensive SRAM for the entire system memory."
			),
			"internal_choice_question": None,
		},
	]


def _get_cs_long_pool(source_tag: str) -> List[Dict[str, Any]]:
	return [
		{
			"question": "Analyze the Von Neumann architecture in detail. Explain the roles and interactions between the CPU, Main Memory, and the System Bus (Data, Address, and Control buses). Discuss the architectural origin of the Von Neumann bottleneck and detail how modern microprocessors mitigate memory latency.",
			"correct_answer": "Comprehensive structural analysis of Von Neumann architecture, tripartite bus system, memory bottleneck analysis, and modern cache mitigation.",
			"marks": 5,
			"difficulty": "Hard",
			"source": source_tag,
			"answer_key_detail": (
				"Marking Scheme (5 Marks Total):\n"
				"• Theoretical Principles & Stored-Program Concept [1 Mark]: Formal definition of Von Neumann architecture with shared memory for data and instructions.\n"
				"• System Bus Structure & Mechanics [1.5 Marks]: Detailed roles of the Address Bus (unidirectional memory addressing), Data Bus (bidirectional data transport), and Control Bus (timing/read/write signals).\n"
				"• The Von Neumann Bottleneck [1 Mark]: In-depth explanation of bus contention where instruction fetching and data transfers cannot occur simultaneously.\n"
				"• Modern Hardware Mitigations [1.5 Marks]: Discussion of multi-tier on-die SRAM caches (L1 Instruction & L1 Data separation), prefetching algorithms, and branch prediction."
			),
			"solution": (
				"1. Core Principles: The Von Neumann architecture unifies code and data inside a single read-write memory address space.\n"
				"2. System Buses: The Address Bus transmits target locations from CPU to RAM. The Data Bus transfers actual instruction words and operands bidirectionally. The Control Bus transmits control signals (READ, WRITE, CLOCK, INTERRUPT).\n"
				"3. The Bottleneck: Because instructions and data share the same bus, the CPU cannot read an instruction and write data simultaneously. Bus throughput is bounded, stalling CPU execution.\n"
				"4. Mitigations: Modern CPUs implement a modified Harvard architecture internally: on-die L1 cache is split into dedicated L1-Instruction and L1-Data caches, with hardware prefetchers loading data blocks ahead of execution."
			),
			"internal_choice_question": {
				"question": "OR: Compare the Von Neumann architecture with the Harvard architecture. Detail their structural differences regarding bus pathways, analyze how instruction pipelining benefits from separate buses, and evaluate their real-world usage in general-purpose computing versus embedded Digital Signal Processors (DSPs).",
				"marks": 5,
				"difficulty": "Hard",
				"source": source_tag,
				"correct_answer": "Complete comparative evaluation of shared vs independent buses, pipelining hazards elimination, and domain applications in PCs vs DSPs.",
				"answer_key_detail": (
					"Marking Scheme (5 Marks Total):\n"
					"• Structural Architectural Differences [1.5 Marks]: Contrasting shared memory/bus in Von Neumann with independent code/data memories and dual bus pathways in Harvard.\n"
					"• Pipelining Performance [1.5 Marks]: How separate buses eliminate structural pipeline hazards by allowing concurrent instruction fetch and data read/write.\n"
					"• Circuit Complexity & Flexibility [1 Mark]: Trade-offs between memory utilization flexibility in Von Neumann vs fixed memory partitions and increased pin counts in Harvard.\n"
					"• Industry Applications [1 Mark]: General-purpose microprocessors (x86/ARM) using Von Neumann/hybrid models vs DSPs and microcontrollers (AVR/PIC) using pure Harvard."
				),
				"solution": (
					"1. Structure: Harvard architecture provides distinct memory units and buses for instructions and data. Von Neumann shares both.\n"
					"2. Pipelining Impact: In a classic 5-stage pipeline, the Fetch stage reads instructions while the Memory stage reads/writes data. In Von Neumann, this creates a structural hazard (both stages demand the bus). Harvard executes both concurrently without stalling.\n"
					"3. Trade-offs: Harvard requires more silicon area, wiring, and pins. If instruction memory is empty, data cannot utilize that space.\n"
					"4. Applications: Embedded systems and DSPs (e.g. ARM Cortex-M, Texas Instruments DSPs) use Harvard for deterministic real-time throughput. Personal computers use modified Harvard internally and Von Neumann externally."
				),
			},
		},
	]


def _get_cs_application_pool(source_tag: str) -> List[Dict[str, Any]]:
	return [
		{
			"question": "Case Scenario: A software system sorting high-volume real-time telemetry data crashes due to recursion stack overflow when executing QuickSort on datasets that are already sorted in ascending order. Diagnose the mathematical and algorithmic root cause of this failure, and formulate an architectural remedy using randomized pivot selection or hybrid Introsort.",
			"correct_answer": "Diagnosis of O(n) recursion depth on sorted arrays with fixed pivot, and remedy using median-of-three or randomized pivot selection and recursion limits.",
			"marks": 4,
			"difficulty": "Hard",
			"source": source_tag,
			"answer_key_detail": (
				"Marking Scheme (4 Marks Total):\n"
				"• Sub-part (a) Algorithmic Diagnosis [2 Marks]: Explains that picking the first/last element on sorted data creates partitions of size 0 and n-1, causing recursion depth to degrade from O(log n) to O(n), exhausting call stack frames.\n"
				"• Sub-part (b) Technical Mitigation [2 Marks]: Proposes Randomized Pivot Selection or Median-of-Three pivot selection, or switching to Introsort (which falls back to HeapSort when recursion depth exceeds 2*log(n))."
			),
			"solution": (
				"Sub-part (a) Diagnosis (2 Marks):\n"
				"When an array is already sorted and QuickSort selects the first or last element as the pivot, every partition is maximally unbalanced (size 0 and size n-1). This requires n recursive stack frames instead of log n. On large datasets (e.g. 100,000 items), this exceeds default call stack limits, triggering a stack overflow crash.\n\n"
				"Sub-part (b) Remedy (2 Marks):\n"
				"1. Randomized Pivot: Swap a randomly chosen index with the first element before partitioning, ensuring expected O(n log n) time on sorted data.\n"
				"2. Median-of-Three: Sample the first, middle, and last elements, selecting their median as the pivot.\n"
				"3. Introsort: Monitor recursion depth. If depth exceeds 2*floor(log2(n)), switch immediately to HeapSort, guaranteeing O(n log n) worst-case without stack exhaustion."
			),
			"internal_choice_question": {
				"question": "OR: Case Scenario: A database engine sorting millions of fixed-width customer records encounters severe CPU cache misses, spending over 85% of execution time waiting for memory transfers during sorting passes. Formulate an optimization strategy analyzing spatial locality, cache line utilization (64 bytes), and cache-conscious sorting algorithms.",
				"marks": 4,
				"difficulty": "Hard",
				"source": source_tag,
				"correct_answer": "Analysis of spatial locality and pointer-chasing cache misses, with remedy reorganizing memory layouts (Structure of Arrays) and using Blocked/Radix sorting.",
				"answer_key_detail": (
					"Marking Scheme (4 Marks Total):\n"
					"• Sub-part (a) Hardware Diagnosis [2 Marks]: Explains that random memory access and large record structures cause cache lines (64 bytes) to be underutilized, inducing frequent L1/L2/L3 cache misses.\n"
					"• Sub-part (b) Architectural Remedy [2 Marks]: Recommends Key-Index sorting (sorting an array of keys and pointers), or cache-blocked sorting algorithms fitted to L2 cache sizes."
				),
				"solution": (
					"Sub-part (a) Diagnosis (2 Marks):\n"
					"CPUs load memory in 64-byte cache lines. If records are large (e.g. 512 bytes) and elements are swapped by pointer dereference, each comparison triggers a cache miss, stalling the CPU for ~200 clock cycles.\n\n"
					"Sub-part (b) Remedy (2 Marks):\n"
					"1. Key-Index Separation: Extract keys and 4-byte index pointers into a compact contiguous array. Sorting this array achieves dense spatial locality (16 keys per cache line).\n"
					"2. Cache-conscious Blocking: Divide datasets into chunks that fit entirely within L2/L3 cache (e.g. 256 KB blocks), sort locally in-cache, and perform a streaming multi-way merge."
				),
			},
		},
	]
