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
	domain = _detect_subject_domain(content_text=content_text, course=course, batch=batch, user_prompt=user_prompt)

	# Extract content keywords/headings for dynamic anchoring
	raw_lines = [l.strip() for l in content_text.splitlines() if l.strip()]
	headings = [l.replace("#", "").strip() for l in raw_lines if l.startswith("#")]
	bullets = [l.lstrip("*-•1234567890. ").strip() for l in raw_lines if len(l) > 15 and not l.startswith("#")]

	# 3. Retrieve Domain Question Pools
	if domain == "java":
		pool_a = _get_java_mcq_pool(source_tag)
		pool_b = _get_java_vsa_pool(source_tag)
		pool_c = _get_java_short_pool(source_tag)
		pool_d = _get_java_long_pool(source_tag)
		pool_e = _get_java_application_pool(source_tag)
	elif domain == "cs":
		pool_a = _get_cs_mcq_pool(source_tag)
		pool_b = _get_cs_vsa_pool(source_tag)
		pool_c = _get_cs_short_pool(source_tag)
		pool_d = _get_cs_long_pool(source_tag)
		pool_e = _get_cs_application_pool(source_tag)
	elif domain == "c":
		pool_a = _get_c_mcq_pool(source_tag)
		pool_b = _get_c_vsa_pool(source_tag)
		pool_c = _get_c_short_pool(source_tag)
		pool_d = _get_c_long_pool(source_tag)
		pool_e = _get_c_application_pool(source_tag)
	elif domain == "frappe":
		pool_a = _get_frappe_mcq_pool(source_tag)
		pool_b = _get_frappe_vsa_pool(source_tag)
		pool_c = _get_frappe_short_pool(source_tag)
		pool_d = _get_frappe_long_pool(source_tag)
		pool_e = _get_frappe_application_pool(source_tag)
	elif domain == "python":
		pool_a = _get_python_mcq_pool(source_tag)
		pool_b = _get_python_vsa_pool(source_tag)
		pool_c = _get_python_short_pool(source_tag)
		pool_d = _get_python_long_pool(source_tag)
		pool_e = _get_python_application_pool(source_tag)
	else:
		# Generic Content-Driven Pools built dynamically from headings & bullets
		p_a, p_b, p_c, p_d, p_e = _build_dynamic_content_pools(content_text, headings, bullets, source_tag)
		pool_a = p_a or _get_python_mcq_pool(source_tag)
		pool_b = p_b or _get_python_vsa_pool(source_tag)
		pool_c = p_c or _get_python_short_pool(source_tag)
		pool_d = p_d or _get_python_long_pool(source_tag)
		pool_e = p_e or _get_python_application_pool(source_tag)

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


def _detect_subject_domain(content_text: str, course: Optional[str], batch: Optional[str], user_prompt: str) -> str:
	"""Determines the appropriate educational domain from course, batch, user_prompt, and content text."""
	c_lower = (course or "").lower().strip()
	b_lower = (batch or "").lower().strip()

	# 1. Explicit Course / Batch slug check (Highest Priority)
	if "python" in c_lower or "python" in b_lower:
		return "python"
	if c_lower == "java" or b_lower == "java" or (c_lower.startswith("java") and "javascript" not in c_lower):
		return "java"
	if c_lower == "c" or b_lower == "c":
		return "c"
	if "computer-science" in c_lower or "computer-science" in b_lower:
		return "cs"
	if "frappe" in c_lower or "frappe" in b_lower:
		return "frappe"

	# 2. Search corpus check (Prompt, Title, and Content)
	search_corpus = f"{course or ''} {batch or ''} {user_prompt} {content_text}".lower()

	# Python check
	if "python" in search_corpus or "django" in search_corpus or "flask" in search_corpus or "guido van rossum" in search_corpus:
		return "python"

	# Java check (ensure 'javascript' doesn't cause a false positive)
	if re.search(r"\bjava\b", search_corpus) or "james gosling" in search_corpus or "jvm" in search_corpus or "vikas s" in search_corpus:
		if "python" not in search_corpus:
			return "java"

	# CS check
	if "architecture" in search_corpus or "cpu" in search_corpus or "alu" in search_corpus or "quicksort" in search_corpus:
		return "cs"

	# C check
	if "dennis ritchie" in search_corpus or (re.search(r"\bc programming\b", search_corpus)):
		return "c"

	# Frappe check
	if "frappe" in search_corpus or "doctype" in search_corpus:
		return "frappe"

	return "content_driven"


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
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": (
				f"• Point 1 [1 Mark]: Correctly identifies primary specification ({bullet[:60]}).\n"
				f"• Point 2 [1 Mark]: Explains execution constraint or state validation requirement."
			),
			"solution": f"1. Principle: Ensures conformity with {bullet[:80]}.\n2. Validation: Guarantees isolated and repeatable state transitions.",
			"internal_choice_question": None,
		}
	elif marks == 3:
		return {
			"question_number": q_num,
			"question": f"Explain the architectural significance and practical implementation of {topic} in modern systems.",
			"correct_answer": f"Definition of {topic}, adherence to {bullet[:60]}, and prevention of state corruption.",
			"marks": 3,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": (
				f"• Point 1 [1 Mark]: Conceptual definition and role of {topic}.\n"
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


def _build_dynamic_content_pools(content_text: str, headings: List[str], bullets: List[str], source_tag: str):
	"""Builds dynamic pools from parsed content text if no static domain pool is matched."""
	if not headings and not bullets:
		return [], [], [], [], []

	pool_a = []
	for i, h in enumerate(headings[:20]):
		b = bullets[i % max(1, len(bullets))] if bullets else "standard curriculum principles"
		pool_a.append(_synthesize_extra_question(str(i + 1), 1, "MCQ", h, b, source_tag))

	pool_b = []
	for i, h in enumerate(headings[:10]):
		b = bullets[(i + 1) % max(1, len(bullets))] if bullets else "execution state"
		pool_b.append(_synthesize_extra_question(str(i + 1), 2, "Short Answer", h, b, source_tag))

	pool_c = []
	for i, h in enumerate(headings[:10]):
		b = bullets[(i + 2) % max(1, len(bullets))] if bullets else "architectural specification"
		pool_c.append(_synthesize_extra_question(str(i + 1), 3, "Short Answer", h, b, source_tag))

	pool_d = []
	for i, h in enumerate(headings[:5]):
		b = bullets[(i + 3) % max(1, len(bullets))] if bullets else "system lifecycle"
		pool_d.append(_synthesize_extra_question(str(i + 1), 5, "Long Answer", h, b, source_tag))

	pool_e = []
	for i, h in enumerate(headings[:5]):
		b = bullets[(i + 4) % max(1, len(bullets))] if bullets else "production scenario"
		pool_e.append(_synthesize_extra_question(str(i + 1), 4, "Application-Based", h, b, source_tag))

	return pool_a, pool_b, pool_c, pool_d, pool_e


# =====================================================================
# JAVA & OOP QUESTION POOL (Grounded in Java Course & Batch Syllabus)
# =====================================================================

def _get_java_mcq_pool(source_tag: str) -> List[Dict[str, Any]]:
	return [
		{
			"question": "Who led the Sun Microsystems 'Green Team' in 1991 that created the technology that became Java?",
			"options": ["(A) Dennis Ritchie", "(B) James Gosling", "(C) Guido van Rossum", "(D) Bjarne Stroustrup"],
			"correct_answer": "(B) James Gosling",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (B) James Gosling. Evaluation Criterion: Full 1 mark awarded for identifying James Gosling, who led the Sun Microsystems Green Team (including Mike Sheridan and Patrick Naughton) in 1991 and is celebrated as the 'Father of Java'.",
			"solution": "James Gosling led the Green Team at Sun Microsystems starting in 1991. Dennis Ritchie created C, Guido van Rossum created Python, and Bjarne Stroustrup created C++.",
			"internal_choice_question": None,
		},
		{
			"question": "What was the original name of the Java programming language before it was renamed due to trademark issues?",
			"options": ["(A) Oak", "(B) Silk", "(C) Dynamic", "(D) CoffeeScript"],
			"correct_answer": "(A) Oak",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (A) Oak. Evaluation Criterion: Full 1 mark awarded for recognizing that James Gosling originally named the language 'Oak' after an oak tree standing outside his office window, later renamed to Java after Indonesian espresso beans.",
			"solution": "Java was originally called 'Oak'. It was renamed to 'Java' because Oak was already trademarked by another company.",
			"internal_choice_question": None,
		},
		{
			"question": "What does the foundational architectural philosophy of Java, 'WORA', stand for?",
			"options": ["(A) Write Once, Run Anywhere", "(B) Windows Oriented Runtime Architecture", "(C) Web Optimized Resource Allocation", "(D) Wireless Operation and Remote Access"],
			"correct_answer": "(A) Write Once, Run Anywhere",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (A) Write Once, Run Anywhere. Evaluation Criterion: Full 1 mark awarded for stating the exact expansion of WORA, reflecting Java's bytecode platform independence.",
			"solution": "Java code is compiled into bytecode (.class), which can run on any system that has a Java Virtual Machine (JVM), enabling 'Write Once, Run Anywhere'.",
			"internal_choice_question": None,
		},
		{
			"question": "Which virtual execution environment interprets or compiles Java bytecode into native machine instructions?",
			"options": ["(A) Java Virtual Machine (JVM)", "(B) Common Language Runtime (CLR)", "(C) V8 Engine", "(D) Android NDK"],
			"correct_answer": "(A) Java Virtual Machine (JVM)",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (A) Java Virtual Machine (JVM). Evaluation Criterion: Full 1 mark awarded for identifying the JVM as the abstract computing machine that executes compiled Java bytecode.",
			"solution": "The JVM (Java Virtual Machine) loads, verifies, and executes Java bytecode, providing hardware independence and automatic memory management.",
			"internal_choice_question": None,
		},
		{
			"question": "In which year was the first official Java Development Kit (JDK 1.0) publicly released by Sun Microsystems?",
			"options": ["(A) 1991", "(B) 1995", "(C) 1996", "(D) 2000"],
			"correct_answer": "(C) 1996",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (C) 1996. Evaluation Criterion: Full 1 mark awarded for identifying 1996 as the release year of JDK 1.0 following its public debut in 1995.",
			"solution": "Java debuted publicly in 1995 and Sun Microsystems released the official JDK 1.0 in 1996. Sun was later acquired by Oracle in 2010.",
			"internal_choice_question": None,
		},
		{
			"question": "Which corporation acquired Sun Microsystems in 2010, assuming stewardship of Java development?",
			"options": ["(A) Microsoft Corporation", "(B) IBM", "(C) Oracle Corporation", "(D) Google LLC"],
			"correct_answer": "(C) Oracle Corporation",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (C) Oracle Corporation. Evaluation Criterion: Full 1 mark awarded for naming Oracle Corporation as the acquiring entity in 2010.",
			"solution": "Oracle Corporation acquired Sun Microsystems in January 2010, taking over the stewardship and ongoing development of Java and MySQL.",
			"internal_choice_question": None,
		},
		{
			"question": "What is the mandatory method signature required for the runtime entry point of a standalone Java application?",
			"options": ["(A) public static void main(String[] args)", "(B) public void main(String args)", "(C) static int main(String[] argv)", "(D) public abstract void start()"],
			"correct_answer": "(A) public static void main(String[] args)",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (A) public static void main(String[] args). Evaluation Criterion: Full 1 mark awarded for identifying the exact access modifier, static keyword, void return, and String array parameters.",
			"solution": "The JVM looks for `public static void main(String[] args)` to start executing a Java program without having to instantiate the containing class first.",
			"internal_choice_question": None,
		},
		{
			"question": "Which punctuation character must be placed at the end of every executable statement in Java?",
			"options": ["(A) Colon (:)", "(B) Semicolon (;)", "(C) Period (.)", "(D) Ampersand (&)"],
			"correct_answer": "(B) Semicolon (;)",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (B) Semicolon (;). Evaluation Criterion: Full 1 mark awarded for recognizing that Java enforces statement termination with a semicolon (;).",
			"solution": "Java syntax strictly mandates that each statement ends with a semicolon (;). Code blocks are wrapped with curly braces ({}).",
			"internal_choice_question": None,
		},
		{
			"question": "Which of the following represents a primitive data type in Java rather than a reference type?",
			"options": ["(A) String", "(B) Integer", "(C) int", "(D) ArrayList"],
			"correct_answer": "(C) int",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (C) int. Evaluation Criterion: Full 1 mark awarded for identifying `int` as a built-in 32-bit primitive type, whereas String, Integer, and ArrayList are reference types.",
			"solution": "Java has 8 primitive data types: byte, short, int, long, float, double, char, and boolean. Classes like String and Integer wrapper are reference types.",
			"internal_choice_question": None,
		},
		{
			"question": "What is the built-in Java standard output statement used to print a line of text to the console?",
			"options": ["(A) Console.WriteLine()", "(B) echo()", "(C) System.out.println()", "(D) print_line()"],
			"correct_answer": "(C) System.out.println()",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (C) System.out.println(). Evaluation Criterion: Full 1 mark awarded for identifying `System.out.println()` from the java.lang package.",
			"solution": "`System.out.println()` prints the argument passed to standard output and advances the cursor to the next line.",
			"internal_choice_question": None,
		},
		{
			"question": "Which OOP pillar involves bundling variables and methods together while hiding internal object state using private access modifiers?",
			"options": ["(A) Inheritance", "(B) Encapsulation", "(C) Polymorphism", "(D) Compilation"],
			"correct_answer": "(B) Encapsulation",
			"marks": 1,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (B) Encapsulation. Evaluation Criterion: Full 1 mark awarded for defining Encapsulation as data hiding via private fields accessed exclusively through public getters and setters.",
			"solution": "Encapsulation binds data and code into a single unit (class) and restricts direct unauthorized manipulation of internal fields.",
			"internal_choice_question": None,
		},
		{
			"question": "Which Java keyword is used by a derived child class to inherit fields and methods from a parent class?",
			"options": ["(A) implements", "(B) extends", "(C) inherits", "(D) superclass"],
			"correct_answer": "(B) extends",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (B) extends. Evaluation Criterion: Full 1 mark awarded for identifying `extends` for class inheritance (`implements` is used for interfaces).",
			"solution": "In Java, classes use `extends` for single class inheritance and `implements` to realize interface contracts.",
			"internal_choice_question": None,
		},
		{
			"question": "What is the key difference between Method Overloading and Method Overriding in Java?",
			"options": [
				"(A) Overloading occurs in the same class with different parameter lists; Overriding occurs in a subclass with an identical signature",
				"(B) Overloading requires static methods while Overriding requires private methods",
				"(C) Overloading is resolved at runtime while Overriding is resolved at compile time",
				"(D) Overloading applies exclusively to abstract methods",
			],
			"correct_answer": "(A) Overloading occurs in the same class with different parameter lists; Overriding occurs in a subclass with an identical signature",
			"marks": 1,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (A). Evaluation Criterion: Full 1 mark awarded for clearly differentiating compile-time method overloading from runtime dynamic polymorphism via overriding.",
			"solution": "Method overloading provides multiple methods with the same name but different signatures within the same class. Method overriding redefines a parent method in a subclass with matching signature.",
			"internal_choice_question": None,
		},
		{
			"question": "According to the Java Batch syllabus, who is the designated lead instructor for the intensive 3-month online batch?",
			"options": ["(A) James Gosling", "(B) Vikas S", "(C) Guido van Rossum", "(D) Patrick Naughton"],
			"correct_answer": "(B) Vikas S",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (B) Vikas S. Evaluation Criterion: Full 1 mark awarded for identifying Vikas S as documented in the LMS Java batch schedule.",
			"solution": "The Java Batch details explicitly list Vikas S as the lead instructor for the August–November 2026 batch.",
			"internal_choice_question": None,
		},
		{
			"question": "What are the scheduled daily timings for the online Java programming batch?",
			"options": ["(A) 06:00 AM to 12:00 PM", "(B) 09:30 AM to 06:00 PM (IST)", "(C) 02:00 PM to 08:00 PM", "(D) 08:00 PM to 11:00 PM"],
			"correct_answer": "(B) 09:30 AM to 06:00 PM (IST)",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (B) 09:30 AM to 06:00 PM (IST). Evaluation Criterion: Full 1 mark awarded for matching the batch schedule specifications.",
			"solution": "The Java batch schedule is set to 09:30 AM to 06:00 PM Asia/Kolkata (IST).",
			"internal_choice_question": None,
		},
		{
			"question": "Which module of the Java Batch curriculum covers multithreading, exception handling, and the Java Collections Framework?",
			"options": ["(A) Module 1: Java Fundamentals", "(B) Module 2: OOP Principles", "(C) Module 3: Advanced Core Concepts", "(D) Module 4: Real-World Application"],
			"correct_answer": "(C) Module 3: Advanced Core Concepts",
			"marks": 1,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (C) Module 3: Advanced Core Concepts. Evaluation Criterion: Full 1 mark awarded for identifying Module 3 as covering advanced core Java concepts.",
			"solution": "Module 3 covers exception handling, multithreading, Collections, and file I/O operations.",
			"internal_choice_question": None,
		},
		{
			"question": "Which Java API standard is introduced in Module 4 to connect Java applications with relational database management systems?",
			"options": ["(A) JDBC (Java Database Connectivity)", "(B) JPA Hibernate", "(C) JNDI Directory Service", "(D) ODBC Driver"],
			"correct_answer": "(A) JDBC (Java Database Connectivity)",
			"marks": 1,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (A) JDBC (Java Database Connectivity). Evaluation Criterion: Full 1 mark awarded for identifying JDBC as the standard API for database connectivity in Java.",
			"solution": "Module 4 focuses on clean code practices and basic database connectivity using JDBC (Java Database Connectivity).",
			"internal_choice_question": None,
		},
		{
			"question": "Which Java keyword is placed on a code block to guarantee execution regardless of whether an exception is thrown or caught?",
			"options": ["(A) catch", "(B) throw", "(C) finally", "(D) assert"],
			"correct_answer": "(C) finally",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (C) finally. Evaluation Criterion: Full 1 mark awarded for identifying `finally` as the cleanup block that always executes.",
			"solution": "A `finally` block executes after `try` and `catch` blocks complete, ensuring resources like file handles or database connections are closed.",
			"internal_choice_question": None,
		},
		{
			"question": "Which interface from the Java Collections Framework represents an ordered sequence allowing duplicate elements and indexed access?",
			"options": ["(A) java.util.Set", "(B) java.util.List", "(C) java.util.Map", "(D) java.util.Queue"],
			"correct_answer": "(B) java.util.List",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (B) java.util.List. Evaluation Criterion: Full 1 mark awarded for identifying `List` as the ordered collection interface supporting index-based operations.",
			"solution": "The `List` interface (implemented by ArrayList and LinkedList) maintains an ordered sequence of elements and permits duplicates.",
			"internal_choice_question": None,
		},
		{
			"question": "What runtime component automatically reclaims heap memory occupied by objects that are no longer reachable by any active thread reference?",
			"options": ["(A) Class Loader", "(B) Garbage Collector (GC)", "(C) JIT Compiler", "(D) Bytecode Verifier"],
			"correct_answer": "(B) Garbage Collector (GC)",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (B) Garbage Collector (GC). Evaluation Criterion: Full 1 mark awarded for identifying the JVM Garbage Collector as responsible for automatic memory deallocation.",
			"solution": "The JVM's Garbage Collector identifies unreachable objects in heap memory and automatically reclaims that memory to prevent memory leaks.",
			"internal_choice_question": None,
		},
	]


def _get_java_vsa_pool(source_tag: str) -> List[Dict[str, Any]]:
	return [
		{
			"question": "Differentiate between JDK, JRE, and JVM in the Java execution environment.",
			"correct_answer": "JVM executes bytecode. JRE contains JVM and runtime libraries. JDK contains JRE plus development tools like javac and debugger.",
			"marks": 2,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": (
				"• Point 1 [1 Mark]: JVM defines the virtual machine executing bytecode; JRE provides libraries + JVM for execution.\n"
				"• Point 2 [1 Mark]: JDK is the full development kit providing compiler (javac), archiver (jar), and JRE."
			),
			"solution": "JVM (Java Virtual Machine) runs bytecode. JRE (Java Runtime Environment) = JVM + core classes. JDK (Java Development Kit) = JRE + compiler tools.",
			"internal_choice_question": None,
		},
		{
			"question": "State the two primary syntax rules regarding class names and statement termination in Java.",
			"correct_answer": "1. Class names must begin with an uppercase letter. 2. Every executable statement must terminate with a semicolon (;).",
			"marks": 2,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": (
				"• Point 1 [1 Mark]: Identifies PascalCase naming convention for classes (e.g. `public class Main`).\n"
				"• Point 2 [1 Mark]: States mandatory semicolon (;) statement termination."
			),
			"solution": "In Java, classes follow UpperCamelCase convention and statements must terminate with a semicolon.",
			"internal_choice_question": None,
		},
		{
			"question": "Explain the difference between primitive data types and reference types in Java memory allocation.",
			"correct_answer": "Primitive types hold their values directly on the stack; reference types store memory references on the stack pointing to objects allocated on the heap.",
			"marks": 2,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": (
				"• Point 1 [1 Mark]: Explains that 8 primitive types (int, double, boolean, etc.) store actual values in stack frames.\n"
				"• Point 2 [1 Mark]: Explains that reference types (Objects, Arrays, Strings) hold heap addresses."
			),
			"solution": "Primitives store values directly in stack memory. Reference variables store references (addresses) to instances on the heap.",
			"internal_choice_question": None,
		},
		{
			"question": "List the four fundamental pillars of Object-Oriented Programming (OOP) covered in Module 2 of the Java curriculum.",
			"correct_answer": "1. Encapsulation, 2. Inheritance, 3. Polymorphism, 4. Abstraction.",
			"marks": 2,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": (
				"• Point 1 [1 Mark]: Names Encapsulation and Inheritance correctly.\n"
				"• Point 2 [1 Mark]: Names Polymorphism and Abstraction correctly."
			),
			"solution": "The four pillars of OOP in Java are Encapsulation (data hiding), Inheritance (code reuse), Polymorphism (multiple forms), and Abstraction (hiding implementation details).",
			"internal_choice_question": None,
		},
		{
			"question": "Distinguish between the `==` comparison operator and the `.equals()` method when comparing objects in Java.",
			"correct_answer": "`==` compares memory references (addresses), while `.equals()` compares actual value content of objects.",
			"marks": 2,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": (
				"• Point 1 [1 Mark]: Identifies `==` as reference identity check (same memory location).\n"
				"• Point 2 [1 Mark]: Identifies `.equals()` as semantic value equivalence check (when overridden, as in String)."
			),
			"solution": "`==` tests if two references point to the exact same object in memory. `.equals()` tests if the state/content of two objects is logically equal.",
			"internal_choice_question": None,
		},
		{
			"question": "According to the Java Batch structure, state the scheduled delivery mode and total seat capacity.",
			"correct_answer": "Delivery mode is 100% Online, and class size is strictly capped at 50 seats for personalized support.",
			"marks": 2,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": (
				"• Point 1 [1 Mark]: Delivery mode: 100% Online.\n"
				"• Point 2 [1 Mark]: Class size limit: exactly 50 seats."
			),
			"solution": "The Java Batch details confirm 100% online delivery and a strict cap of 50 students.",
			"internal_choice_question": None,
		},
	]


def _get_java_short_pool(source_tag: str) -> List[Dict[str, Any]]:
	return [
		{
			"question": "Explain the WORA (Write Once, Run Anywhere) paradigm in Java. Detail how bytecode and the JVM enable platform independence.",
			"correct_answer": "Java source code is compiled by javac into intermediate bytecode (.class). Any platform with a JVM can execute this bytecode without recompiling.",
			"marks": 3,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": (
				"• Point 1 [1 Mark]: Compilation stage: javac translates .java source files into architecture-neutral bytecode.\n"
				"• Point 2 [1 Mark]: JVM execution: The platform-specific Java Virtual Machine interprets or JIT-compiles bytecode into native machine code.\n"
				"• Point 3 [1 Mark]: Platform independence: The same compiled .class file executes uniformly across Windows, Linux, and macOS."
			),
			"solution": "1. Java compiler (javac) transforms source code into bytecode rather than machine code.\n2. Each OS has a platform-specific JVM that reads the identical bytecode.\n3. This decouples software development from target hardware architectures.",
			"internal_choice_question": None,
		},
		{
			"question": "Explain the concept and implementation of Encapsulation in Java using private instance fields and public getter/setter methods.",
			"correct_answer": "Private fields restrict direct access; public getters and setters provide controlled access with validation.",
			"marks": 3,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": (
				"• Point 1 [1 Mark]: Principle of data hiding: Declaring class member variables as `private`.\n"
				"• Point 2 [1 Mark]: Access control: Providing `public` getter and setter methods to inspect and modify fields.\n"
				"• Point 3 [1 Mark]: Validation & integrity: Demonstrates how setters enforce business rules and prevent invalid state."
			),
			"solution": "Encapsulation protects object state by restricting field access to class methods. Getters return values and setters validate input before updating private fields.",
			"internal_choice_question": None,
		},
		{
			"question": "Compare `ArrayList` and `LinkedList` in the Java Collections Framework regarding internal data structures and performance trade-offs.",
			"correct_answer": "ArrayList uses a dynamic resizable array with O(1) random access; LinkedList uses a doubly-linked node chain with O(1) insertions/deletions at ends.",
			"marks": 3,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": (
				"• Point 1 [1 Mark]: Structural layout: ArrayList uses contiguous array buffers; LinkedList uses doubly-linked nodes.\n"
				"• Point 2 [1 Mark]: Random access complexity: ArrayList offers O(1) index access vs LinkedList's O(n) traversal.\n"
				"• Point 3 [1 Mark]: Insertion/Deletion complexity: LinkedList offers O(1) node insertion vs ArrayList's O(n) element shifting."
			),
			"solution": "ArrayList is superior for frequent lookups and read-heavy workloads. LinkedList is preferred when frequent element insertions and deletions occur at list boundaries.",
			"internal_choice_question": None,
		},
		{
			"question": "Explain Method Overriding in Java. What is the significance of the `@Override` annotation and dynamic method dispatch?",
			"correct_answer": "Subclass redefines superclass method with matching signature. @Override enables compiler verification, and JVM resolves execution at runtime via dynamic dispatch.",
			"marks": 3,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": (
				"• Point 1 [1 Mark]: Definition: Subclass implements parent method with identical name, parameter types, and return type.\n"
				"• Point 2 [1 Mark]: Role of `@Override`: Tells compiler to verify that the method actually exists in the superclass.\n"
				"• Point 3 [1 Mark]: Runtime dispatch: JVM determines the method to execute based on actual object instance on the heap, not reference type."
			),
			"solution": "Method overriding provides subclass-specific behavior for inherited methods. Dynamic method dispatch determines method execution polymorphically at runtime.",
			"internal_choice_question": None,
		},
		{
			"question": "Describe the lifecycle states of a thread in Java from creation to termination.",
			"correct_answer": "New -> Runnable -> Blocked/Waiting/Timed Waiting -> Terminated.",
			"marks": 3,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": (
				"• Point 1 [1 Mark]: New & Runnable states: Thread created via `new Thread()` and transitioned to Runnable upon `start()`.\n"
				"• Point 2 [1 Mark]: Waiting/Blocked states: Thread temporarily suspended waiting for locks or I/O.\n"
				"• Point 3 [1 Mark]: Terminated state: Thread completes execution of its `run()` method."
			),
			"solution": "Java threads move through NEW, RUNNABLE, BLOCKED, WAITING, TIMED_WAITING, and TERMINATED states managed by the JVM thread scheduler.",
			"internal_choice_question": None,
		},
		{
			"question": "Explain the role and syntax of the `try-catch-finally` construct in Java exception handling.",
			"correct_answer": "Try encloses risky code, catch handles specific exceptions, and finally guarantees execution of cleanup routines.",
			"marks": 3,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": (
				"• Point 1 [1 Mark]: `try` block: Isolates executable code that may throw checked or unchecked exceptions.\n"
				"• Point 2 [1 Mark]: `catch` block: Traps and resolves designated exception types without crashing the application.\n"
				"• Point 3 [1 Mark]: `finally` block: Executes unconditionally for resource reclamation."
			),
			"solution": "The try-catch-finally pattern enables robust error recovery while ensuring critical resources (connections, files) are closed deterministically.",
			"internal_choice_question": None,
		},
		{
			"question": "Outline the four core modules comprising the 3-month Java Batch curriculum and summarize their primary learning objectives.",
			"correct_answer": "Module 1: Fundamentals, Module 2: OOP Principles, Module 3: Advanced Core Concepts, Module 4: Real-World Applications & JDBC.",
			"marks": 3,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": (
				"• Point 1 [1 Mark]: Module 1 (Syntax, data types, control flow, loops, arrays) and Module 2 (Classes, inheritance, polymorphism, encapsulation).\n"
				"• Point 2 [1 Mark]: Module 3 (Exception handling, multithreading, Collections, file I/O).\n"
				"• Point 3 [1 Mark]: Module 4 (Clean code, JDBC database connectivity, and building scalable applications)."
			),
			"solution": "The Java batch curriculum systematically progresses from basic syntax to object-oriented architecture, advanced multithreaded systems, and production database integration.",
			"internal_choice_question": None,
		},
	]


def _get_java_long_pool(source_tag: str) -> List[Dict[str, Any]]:
	return [
		{
			"question": "Provide an in-depth architectural analysis of Object-Oriented Programming (OOP) in Java. Discuss class instantiation, single inheritance using `extends`, method overriding with `@Override`, dynamic polymorphism, and provide a clear Java code snippet demonstrating these concepts.",
			"correct_answer": "Comprehensive breakdown of OOP in Java with class definitions, inheritance, polymorphism, and code demonstration.",
			"marks": 5,
			"difficulty": "Hard",
			"source": source_tag,
			"answer_key_detail": (
				"• Theoretical Foundation & Principles [1 Mark]: Definitions of classes as blueprints, objects as instances, and single inheritance constraints.\n"
				"• Inheritance & Subtyping [1 Mark]: Detailed explanation of `extends`, constructor chaining using `super()`, and field access.\n"
				"• Polymorphism & Dynamic Dispatch [1 Mark]: Analysis of runtime method table lookup and interface contracts.\n"
				"• Code Demonstration [1 Mark]: Fully syntactically valid Java code showing parent class, derived class, `@Override`, and polymorphic invocation.\n"
				"• Best Practices & Pitfalls [1 Mark]: Avoiding deep inheritance hierarchies, composition over inheritance, and encapsulation enforcement."
			),
			"solution": (
				"1. Foundation: In Java, classes model state and behavior. Instances are allocated on the heap.\n"
				"2. Inheritance: `class Dog extends Animal` inherits state and methods. `super()` invokes parent constructor.\n"
				"3. Polymorphism: `Animal a = new Dog(); a.makeSound();` dynamically invokes `Dog.makeSound()`.\n"
				"4. Code:\n"
				"   public class Animal { public void sound() { System.out.println('Generic sound'); } }\n"
				"   public class Dog extends Animal { @Override public void sound() { System.out.println('Bark'); } }\n"
				"5. Best Practices: Use `@Override` to catch typo errors and prefer interface composition."
			),
			"internal_choice_question": {
				"question": "OR: Compare and contrast Abstract Classes and Interfaces in Java. Detail differences in multiple inheritance, method implementations (including default and static methods in Java 8+), and evaluate when software architects should prefer one over the other.",
				"marks": 5,
				"correct_answer": "Abstract classes support state and partial implementation with single inheritance; interfaces define contracts with multiple implementation support.",
				"answer_key_detail": (
					"• Conceptual Comparison [1 Mark]: Abstract classes represent 'is-a' relationships; Interfaces represent 'can-do' behavioral contracts.\n"
					"• Multiple Inheritance & Modifiers [1 Mark]: A class can extend only one abstract class but implement multiple interfaces.\n"
					"• Java 8+ Innovations [1 Mark]: Inclusion of `default` and `static` methods in interfaces without breaking implementations.\n"
					"• State & Fields [1 Mark]: Abstract classes have instance fields; interface fields are implicitly `public static final`.\n"
					"• Architectural Decision Matrix [1 Mark]: Criteria for selecting between abstract classes vs interfaces in system design."
				),
				"solution": "Abstract classes provide shared mutable state and default base implementations. Interfaces provide decoupled polymorphism and permit multiple inheritance of type.",
			},
		},
		{
			"question": "Analyze the Java Memory Architecture and the Garbage Collection mechanism. Distinguish between Stack memory and Heap memory, explain Young and Old generation object allocation, detail how unreachable objects are identified, and explain practices to prevent memory leaks in enterprise Java applications.",
			"correct_answer": "Detailed explanation of Stack vs Heap, generational GC (Eden, Survivor, Tenured), mark-and-sweep, and leak prevention.",
			"marks": 5,
			"difficulty": "Hard",
			"source": source_tag,
			"answer_key_detail": (
				"• Stack vs Heap Architecture [1 Mark]: Stack allocates method frames and primitive values; Heap allocates dynamic objects.\n"
				"• Generational Heap Structure [1 Mark]: Breakdown of Young Generation (Eden, S0, S1) and Old / Tenured Generation.\n"
				"• GC Mechanics [1 Mark]: Mark-and-sweep algorithm, reachability trees starting from GC Roots, and compaction.\n"
				"• Minor vs Major GC [1 Mark]: Minor GC frequency on Young Generation vs Major / Full GC performance overhead on Old Gen.\n"
				"• Memory Leak Mitigation [1 Mark]: Dereferencing obsolete references, closing streams/connections, and avoiding static collection buildup."
			),
			"solution": (
				"1. Stack holds local variables and call frames; Heap stores all instantiated objects.\n"
				"2. New objects are born in Eden. Surviving objects move between Survivor spaces before promotion to Old Gen.\n"
				"3. Unreachable objects are marked during GC cycles and memory is swept and compacted.\n"
				"4. To prevent leaks: Close JDBC resources, remove unneeded listeners, and avoid unbounded static collections."
			),
			"internal_choice_question": {
				"question": "OR: Provide a comprehensive analysis of Java Exception Handling Architecture. Contrast Checked Exceptions vs Unchecked (Runtime) Exceptions, analyze the Throwable hierarchy, explain the use of `try-with-resources` (`AutoCloseable`), and illustrate how to design custom application exceptions.",
				"marks": 5,
				"correct_answer": "Throwable hierarchy, Checked vs Runtime exceptions, try-with-resources automatic closing, and custom exception implementation.",
				"answer_key_detail": (
					"• Hierarchy Breakdown [1 Mark]: Throwable -> Error and Exception -> RuntimeException.\n"
					"• Checked vs Unchecked [1 Mark]: Checked verified at compile-time (IOException); Unchecked runtime (NullPointerException).\n"
					"• Try-with-Resources [1 Mark]: Syntax and mechanics of `try (ResourceType res = new ResourceType())` implementing AutoCloseable.\n"
					"• Custom Exception Design [1 Mark]: Subclassing Exception or RuntimeException with parameterized constructor.\n"
					"• Error Handling Best Practices [1 Mark]: Never swallowing exceptions, logging with stack traces, and clean boundary translations."
				),
				"solution": "Checked exceptions represent recoverable environmental conditions. Unchecked exceptions denote programming errors. Try-with-resources guarantees deterministic cleanup.",
			},
		},
		{
			"question": "Examine the JDBC (Java Database Connectivity) architecture covered in Module 4 of the Java Batch. Detail the step-by-step pipeline required to connect a Java application to a relational database, execute parameterized queries using `PreparedStatement`, process a `ResultSet`, and manage atomic transactions using `commit()` and `rollback()`.",
			"correct_answer": "Complete JDBC workflow: driver loading, connection pooling, PreparedStatement execution, ResultSet parsing, and transaction commit/rollback.",
			"marks": 5,
			"difficulty": "Hard",
			"source": source_tag,
			"answer_key_detail": (
				"• JDBC Architectural Layers [1 Mark]: Role of JDBC API, DriverManager, and vendor-specific JDBC Drivers.\n"
				"• Connection & PreparedStatement Pipeline [1 Mark]: Establishing `Connection`, compiling `PreparedStatement`, and parameter binding.\n"
				"• SQL Injection Prevention [1 Mark]: Why `PreparedStatement` parameters prevent SQL injection attacks compared to raw `Statement`.\n"
				"• ResultSet Processing [1 Mark]: Iterating `while (rs.next())`, typed column retrieval, and mapping to Domain Transfer Objects.\n"
				"• Transaction Management & Cleanup [1 Mark]: `setAutoCommit(false)`, explicit `commit()`, `rollback()` inside catch, and resource closing."
			),
			"solution": (
				"1. Load driver and obtain `Connection` via `DriverManager.getConnection()`.\n"
				"2. Create `PreparedStatement` with parameterized placeholders (`?`) to prevent SQL injection.\n"
				"3. Execute query: `ResultSet rs = pstmt.executeQuery();` and extract data via `rs.getString()`, `rs.getInt()`.\n"
				"4. Manage transaction boundaries: `con.setAutoCommit(false);` followed by `con.commit()` or `con.rollback()` on error.\n"
				"5. Clean up all resources in `finally` or use try-with-resources."
			),
			"internal_choice_question": {
				"question": "OR: Analyze Multithreading and Concurrency in Java as covered in Module 3. Explain thread creation using `Thread` vs `Runnable`, evaluate race conditions and critical sections, detail the working of the `synchronized` keyword and object monitor locks, and describe the advantages of the `java.util.concurrent` Executor framework.",
				"marks": 5,
				"correct_answer": "Thread vs Runnable, race conditions, synchronized blocks, monitor locks (wait/notify), and ExecutorService thread pooling.",
				"answer_key_detail": (
					"• Thread Creation Paradigms [1 Mark]: Extending `Thread` vs implementing `Runnable` / `Callable`.\n"
					"• Concurrency Pitfalls [1 Mark]: Definition of race conditions, shared mutable state, and thread starvation.\n"
					"• Synchronization Mechanics [1 Mark]: Intrinsic locks (monitors), `synchronized` methods/blocks, and atomic memory visibility.\n"
					"• Inter-Thread Communication [1 Mark]: Protocol of `wait()`, `notify()`, and `notifyAll()` within synchronized blocks.\n"
					"• Modern Concurrency Utilities [1 Mark]: Benefits of `ExecutorService`, thread reuse, and preventing thread exhaustion."
				),
				"solution": "Implementing `Runnable` provides superior flexibility over subclassing `Thread`. Intrinsic locks protect critical sections, while `ExecutorService` pools threads efficiently.",
			},
		},
	]


def _get_java_application_pool(source_tag: str) -> List[Dict[str, Any]]:
	return [
		{
			"question": "Case Study: An enterprise banking application in Java handles simultaneous funds transfer requests across customer accounts. Under peak load, concurrent thread execution produces corrupted account balances due to uncoordinated access to shared account objects. Formulate a technical diagnosis of the concurrency defect and design a robust thread-safe synchronization strategy using synchronized blocks or `ReentrantLock`.",
			"correct_answer": "Diagnosis of race condition on shared mutable balance. Remediation using synchronized blocks on account objects with consistent lock ordering to prevent deadlock.",
			"marks": 4,
			"difficulty": "Hard",
			"source": source_tag,
			"answer_key_detail": (
				"• Sub-part (a) Problem Diagnosis [2 Marks]: Correctly identifies race conditions caused by non-atomic read-modify-write operations on shared balance fields.\n"
				"• Sub-part (b) Technical Remediation [2 Marks]: Implementation of intrinsic lock synchronization with strict global lock ordering (e.g. by account ID) to eliminate deadlock."
			),
			"solution": (
				"Part (a): Balance decrement and increment operations are not atomic at the CPU level. Interleaved thread execution causes lost updates.\n"
				"Part (b): Enforce thread safety by acquiring locks on both source and destination accounts in consistent numerical ID order using `synchronized` blocks or `ReentrantLock`."
			),
			"internal_choice_question": {
				"question": "OR: Case Study: A high-throughput Java payment service experiences intermittent connection drops while communicating with an external database. Design an atomic database transaction workflow using JDBC that ensures funds are never debited if the ledger credit operation fails.",
				"marks": 4,
				"correct_answer": "Implementation of manual transaction boundaries (`con.setAutoCommit(false)`) with rollback in exception handlers.",
				"answer_key_detail": (
					"• Sub-part (a) Failure Mode Analysis [2 Marks]: Identification of partial state update risks when autocommit is enabled.\n"
					"• Sub-part (b) Transaction Workflow Implementation [2 Marks]: Explicit transaction boundary management with `setAutoCommit(false)`, `commit()`, and `rollback()` in catch block."
				),
				"solution": "Disable autocommit on the database connection. Execute both debit and credit prepared statements within a single try block. Call `con.commit()` upon success, and invoke `con.rollback()` inside the catch block on failure.",
			},
		},
		{
			"question": "Case Study: A student enrollment portal for the Java Batch (capped at 50 seats) requires maintaining registered student records. The system must prevent duplicate registrations by student ID, allow rapid lookup by ID, and support sorting students alphabetically by name for reporting. Evaluate Java Collection interfaces (`List`, `Set`, `Map`) and formulate an optimal collection architecture for this system.",
			"correct_answer": "Use `Map<String, Student>` (e.g. HashMap or ConcurrentHashMap) for O(1) duplicate checks and lookup, and `TreeSet` or `ArrayList` with `Comparator` for sorted output.",
			"marks": 4,
			"difficulty": "Hard",
			"source": source_tag,
			"answer_key_detail": (
				"• Sub-part (a) Collection Evaluation [2 Marks]: Analysis of Set (uniqueness), Map (keyed access), and List (ordered sequence) trade-offs.\n"
				"• Sub-part (b) Architectural Strategy [2 Marks]: Recommendation of a primary `Map<String, Student>` for O(1) duplicate check/lookup combined with a custom `Comparator<Student>` for sorted export."
			),
			"solution": (
				"Part (a): A plain List requires O(n) scan to detect duplicates. A HashSet enforces uniqueness but lacks fast key-to-object lookup.\n"
				"Part (b): Maintain a `HashMap<String, Student>` where studentId is the key. To export sorted reports, wrap `new ArrayList<>(map.values())` and sort with `Comparator.comparing(Student::getName)`."
			),
			"internal_choice_question": {
				"question": "OR: Case Study: An enterprise Java log ingestion engine must process large log files (exceeding 2 GB) without encountering `java.lang.OutOfMemoryError: Java heap space`. Design a streaming I/O pipeline using `BufferedReader` and evaluate its memory efficiency compared to loading full file content.",
				"marks": 4,
				"correct_answer": "Stream lines iteratively using `BufferedReader.readLine()` or `Files.lines()` with constant O(1) heap footprint.",
				"answer_key_detail": (
					"• Sub-part (a) Root Cause Analysis [2 Marks]: Demonstrates why loading entire files into memory strings exhausts the JVM heap.\n"
					"• Sub-part (b) Streaming Implementation [2 Marks]: Implementation of buffered line-by-line streaming with automatic resource disposal via try-with-resources."
				),
				"solution": "Use `try (BufferedReader br = new BufferedReader(new FileReader(file)))` and process each line sequentially with `while ((line = br.readLine()) != null)`. This maintains constant O(1) memory overhead regardless of file size.",
			},
		},
		{
			"question": "Case Study: A software architecture team is building an extensible e-commerce platform in Java. The system must support diverse payment providers (Credit Card, PayPal, UPI) without modifying existing checkout business logic. Formulate a decoupled architecture using Java Interfaces adhering to the Open/Closed Principle.",
			"correct_answer": "Define `PaymentProcessor` interface with `processPayment()` method. Concrete payment classes implement the interface, and checkout client depends on the abstraction.",
			"marks": 4,
			"difficulty": "Hard",
			"source": source_tag,
			"answer_key_detail": (
				"• Sub-part (a) Architectural Design [2 Marks]: Definition of the `PaymentProcessor` interface and decoupling of checkout service from concrete implementations.\n"
				"• Sub-part (b) Extensibility & SOLID Compliance [2 Marks]: Demonstration of adding new payment providers without modifying existing checkout code."
			),
			"solution": (
				"Part (a): Declare `public interface PaymentProcessor { boolean pay(double amount); }`.\n"
				"Part (b): Create `CreditCardProcessor`, `UPIProcessor`, and `PayPalProcessor` implementing this interface. The `OrderService` accepts any `PaymentProcessor` via constructor dependency injection.",
			),
			"internal_choice_question": {
				"question": "OR: Case Study: A Java microservice receives JSON payloads and must validate mandatory fields before processing. Design an exception-handling pipeline featuring custom unchecked exceptions and a global exception controller mapping errors to standardized HTTP responses.",
				"marks": 4,
				"correct_answer": "Custom `ValidationException` subclassing `RuntimeException` with field-level error mappings and central exception handler.",
				"answer_key_detail": (
					"• Sub-part (a) Custom Exception Architecture [2 Marks]: Implementation of `ValidationException` extending RuntimeException with metadata.\n"
					"• Sub-part (b) Error Translation Pipeline [2 Marks]: Structured extraction of invalid fields and formatting into standardized JSON error responses."
				),
				"solution": "Define `ValidationException extends RuntimeException` holding field names and validation messages. Wrap service invocation in an error controller that intercepts validation exceptions and maps them to HTTP 400 Bad Request.",
			},
		},
	]


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
			"answer_key_detail": "[1 Mark] Correct Option: (B) Context Management Protocol. Evaluation Criterion: Full 1 mark awarded for identifying the Context Management Protocol implemented via `__enter__` and `__exit__` dunder methods.",
			"solution": "The `with` statement guarantees cleanup actions upon exiting a code block by automatically invoking `__enter__()` upon entry and `__exit__()` upon termination.",
			"internal_choice_question": None,
		},
		{
			"question": "In Python Full Stack development, which architectural pattern does the Django web framework follow?",
			"options": ["(A) Model-View-Controller (MVC)", "(B) Model-View-Template (MVT)", "(C) Presentation-Abstraction-Control (PAC)", "(D) Entity-Component-System (ECS)"],
			"correct_answer": "(B) Model-View-Template (MVT)",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (B) Model-View-Template (MVT). Evaluation Criterion: Full 1 mark awarded for identifying Django's MVT architectural pattern.",
			"solution": "Django uses MVT: Model (database access), View (business logic and HTTP handling), and Template (HTML rendering).",
			"internal_choice_question": None,
		},
		{
			"question": "Which HTTP status code signifies that a client request was successfully processed and a new resource was created on the server?",
			"options": ["(A) 200 OK", "(B) 201 Created", "(C) 204 No Content", "(D) 301 Moved Permanently"],
			"correct_answer": "(B) 201 Created",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (B) 201 Created. Evaluation Criterion: Full 1 mark awarded for identifying HTTP 201 Created as the standard REST response for resource creation.",
			"solution": "HTTP 200 means success, HTTP 201 indicates a resource was successfully created (typically following a POST request), and 204 means success with no message body.",
			"internal_choice_question": None,
		},
		{
			"question": "Which modern JavaScript (ES6+) feature allows unpacking values from arrays or properties from objects into distinct variables?",
			"options": ["(A) Currying", "(B) Destructuring Assignment", "(C) Hoisting", "(D) Event Bubbling"],
			"correct_answer": "(B) Destructuring Assignment",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (B) Destructuring Assignment. Evaluation Criterion: Full 1 mark awarded for identifying destructuring syntax `const { a, b } = obj`.",
			"solution": "Destructuring assignment allows extracting fields directly from objects or arrays into variables cleanly.",
			"internal_choice_question": None,
		},
		{
			"question": "Which relational database engine is commonly bundled with Django by default for lightweight local development?",
			"options": ["(A) PostgreSQL", "(B) SQLite", "(C) MariaDB", "(D) MongoDB"],
			"correct_answer": "(B) SQLite",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (B) SQLite. Evaluation Criterion: Full 1 mark awarded for recognizing SQLite as the default zero-configuration database configured in Django settings.py.",
			"solution": "Django ships preconfigured with `django.db.backends.sqlite3` out of the box, making it simple to run without an external database daemon.",
			"internal_choice_question": None,
		},
		{
			"question": "What is the primary function of the Git command `git merge` in a collaborative development workflow?",
			"options": ["(A) To clone an external repository", "(B) To integrate changes from one branch into the currently active branch", "(C) To discard all uncommitted staging changes", "(D) To delete obsolete remote branches"],
			"correct_answer": "(B) To integrate changes from one branch into the currently active branch",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (B). Evaluation Criterion: Full 1 mark awarded for defining `git merge` as integrating commit histories from a specified branch into the current HEAD branch.",
			"solution": "`git merge <branch>` combines independent lines of development into the current working branch.",
			"internal_choice_question": None,
		},
		{
			"question": "According to the Python Programming August 2026 batch schedule, what is the planned duration of the batch?",
			"options": ["(A) 4 weeks", "(B) 8 weeks", "(C) 16 weeks", "(D) 6 months"],
			"correct_answer": "(B) 8 weeks",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (B) 8 weeks. Evaluation Criterion: Full 1 mark awarded for identifying the 8-week duration as documented in the LMS batch overview.",
			"solution": "The Python Programming August 2026 batch is documented as an 8-week beginner-level batch covering fundamentals to practical projects.",
			"internal_choice_question": None,
		},
		{
			"question": "What are the scheduled daily timings for the Python Programming August 2026 batch?",
			"options": ["(A) 08:00 to 12:00", "(B) 09:00 to 18:00 (Asia/Kolkata)", "(C) 14:00 to 20:00", "(D) 18:00 to 21:00"],
			"correct_answer": "(B) 09:00 to 18:00 (Asia/Kolkata)",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (B) 09:00 to 18:00 (Asia/Kolkata). Evaluation Criterion: Full 1 mark awarded for matching the batch schedule specifications.",
			"solution": "The batch schedule is configured from 09:00:00 to 18:00:00 in timezone Asia/Kolkata.",
			"internal_choice_question": None,
		},
		{
			"question": "Which Python release introduced list comprehensions and a cycle-detecting garbage collector in October 2000?",
			"options": ["(A) Python 1.0", "(B) Python 2.0", "(C) Python 3.0", "(D) Python 3.8"],
			"correct_answer": "(B) Python 2.0",
			"marks": 1,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (B) Python 2.0. Evaluation Criterion: Full 1 mark awarded for recognizing Python 2.0 (released October 2000) as the milestone introducing list comprehensions and cycle-detecting GC.",
			"solution": "Python 2.0 debuted in October 2000 with list comprehensions and cycle-detecting garbage collection. Python 3.0 was released in December 2008.",
			"internal_choice_question": None,
		},
		{
			"question": "Which official Python enhancement proposal establishes standard style guidelines for formatting Python code?",
			"options": ["(A) PEP 8", "(B) PEP 20", "(C) PEP 257", "(D) PEP 484"],
			"correct_answer": "(A) PEP 8",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (A) PEP 8. Evaluation Criterion: Full 1 mark awarded for identifying PEP 8 as the Style Guide for Python Code.",
			"solution": "PEP 8 provides conventions for Python code formatting (e.g. 4 spaces per indentation level, 79 character line length limit).",
			"internal_choice_question": None,
		},
		{
			"question": "What is the honorific title affectionately bestowed upon Guido van Rossum by the Python community?",
			"options": ["(A) Chief Software Architect", "(B) Benevolent Dictator For Life (BDFL)", "(C) Master of Pythonic Zen", "(D) Open Source Commander"],
			"correct_answer": "(B) Benevolent Dictator For Life (BDFL)",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (B) Benevolent Dictator For Life (BDFL). Evaluation Criterion: Full 1 mark awarded for identifying BDFL as detailed in the course history lesson.",
			"solution": "Guido van Rossum held the title Benevolent Dictator For Life (BDFL) until stepping down in 2018.",
			"internal_choice_question": None,
		},
	]


def _get_python_vsa_pool(source_tag: str) -> List[Dict[str, Any]]:
	return [
		{
			"question": "Differentiate between mutable and immutable data types in Python with two concrete examples of each.",
			"correct_answer": "Mutable types can be altered in-place after creation (e.g. list, dict). Immutable types cannot be modified in-place; alterations create new objects (e.g. tuple, int).",
			"marks": 2,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": (
				"• Point 1 [1 Mark]: Clear definition of in-place mutation vs reallocation.\n"
				"• Point 2 [1 Mark]: Valid examples: Lists/Dictionaries as mutable; Integers/Tuples/Strings as immutable."
			),
			"solution": "Mutable objects (list, dict, set) can change their content without changing their memory ID. Immutable objects (int, float, str, tuple) cannot be changed once created.",
			"internal_choice_question": None,
		},
		{
			"question": "Explain the significance of indentation in Python syntax compared to languages like C or Java.",
			"correct_answer": "Python uses whitespace indentation to define code blocks instead of curly braces {} or keywords like begin/end.",
			"marks": 2,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": (
				"• Point 1 [1 Mark]: States that indentation replaces curly braces for grouping statements into blocks.\n"
				"• Point 2 [1 Mark]: Notes that consistent 4 spaces indentation is mandated by PEP 8 and enforced by the interpreter."
			),
			"solution": "Indentation is syntactically mandatory in Python. Failing to maintain uniform indentation results in an `IndentationError`.",
			"internal_choice_question": None,
		},
		{
			"question": "What is the purpose of the `*args` and `**kwargs` parameters in Python function definitions?",
			"correct_answer": "`*args` allows a function to accept any number of positional arguments as a tuple; `**kwargs` allows accepting arbitrary keyword arguments as a dictionary.",
			"marks": 2,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": (
				"• Point 1 [1 Mark]: Explains `*args` unpacks variable positional arguments into a tuple.\n"
				"• Point 2 [1 Mark]: Explains `**kwargs` unpacks keyword arguments into a dictionary."
			),
			"solution": "`*args` captures surplus positional arguments as a tuple. `**kwargs` captures surplus keyword arguments as a key-value dictionary.",
			"internal_choice_question": None,
		},
		{
			"question": "Differentiate between `==` and `is` operators in Python expressions.",
			"correct_answer": "`==` checks value equality (whether values are identical), while `is` checks reference identity (whether both variables point to the exact same memory address).",
			"marks": 2,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": (
				"• Point 1 [1 Mark]: Identifies `==` as value comparison via `__eq__()`.\n"
				"• Point 2 [1 Mark]: Identifies `is` as identity comparison via `id(a) == id(b)`."
			),
			"solution": "`a == b` compares the contents of two objects. `a is b` tests whether `a` and `b` share the identical object identity in memory.",
			"internal_choice_question": None,
		},
		{
			"question": "According to the course syllabus, what are the two primary Python back-end frameworks covered for building RESTful APIs?",
			"correct_answer": "Django and Flask.",
			"marks": 2,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": (
				"• Point 1 [1 Mark]: Names Django as the full-featured web framework.\n"
				"• Point 2 [1 Mark]: Names Flask as the lightweight microframework."
			),
			"solution": "The Full Stack Web Development module covers building robust server-side logic and RESTful APIs using Django or Flask.",
			"internal_choice_question": None,
		},
		{
			"question": "State two major changes introduced in Python 3.0 that were deliberately backward-incompatible with Python 2.",
			"correct_answer": "1. `print` statement changed to a `print()` function. 2. Text strings became Unicode by default with separate `bytes` type.",
			"marks": 2,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": (
				"• Point 1 [1 Mark]: Conversion of `print` statement to `print()` function.\n"
				"• Point 2 [1 Mark]: Unicode string representation and integer true division (`/` returning float)."
			),
			"solution": "Python 3.0 broke backward compatibility to eliminate historical flaws, transitioning `print` to a function and enforcing distinct `str` (Unicode) and `bytes` types.",
			"internal_choice_question": None,
		},
	]


def _get_python_short_pool(source_tag: str) -> List[Dict[str, Any]]:
	return [
		{
			"question": "Explain the concept and advantages of List Comprehensions in Python. Provide a clear code example converting a list of temperatures from Celsius to Fahrenheit.",
			"correct_answer": "List comprehension provides a concise syntax for creating lists from iterables. Example: `fahrenheit = [(c * 9/5) + 32 for c in celsius]`.",
			"marks": 3,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": (
				"• Point 1 [1 Mark]: Definition and syntax: `[expression for item in iterable if condition]`.\n"
				"• Point 2 [1 Mark]: Performance and readability: C-level loop optimization and reduced boilerplate compared to `for` loops.\n"
				"• Point 3 [1 Mark]: Valid code implementation calculating `(c * 9/5) + 32` across a collection."
			),
			"solution": "List comprehensions offer a readable, expressive way to transform data. They execute faster than explicit Python `for` loops because loop construction runs in optimized C bytecode.",
			"internal_choice_question": None,
		},
		{
			"question": "Explain the LEGB rule of variable scope resolution in Python. Describe how Python resolves variable lookups in nested functions.",
			"correct_answer": "Python checks Local, then Enclosing, then Global, and finally Built-in scope. It raises NameError if the identifier is not found.",
			"marks": 3,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": (
				"• Point 1 [1 Mark]: Sequential order: Local -> Enclosing -> Global -> Built-in.\n"
				"• Point 2 [1 Mark]: Explanation of inner functions accessing outer function closures (Enclosing scope).\n"
				"• Point 3 [1 Mark]: The role of `global` and `nonlocal` keywords when modifying outer namespaces."
			),
			"solution": "When resolving a variable name, Python searches the Local namespace first, moves outward to Enclosing closures, inspects Global module attributes, and finally checks the Built-in namespace.",
			"internal_choice_question": None,
		},
		{
			"question": "Describe the MVT (Model-View-Template) architectural pattern utilized by Django in Python Full Stack Web Development.",
			"correct_answer": "Model handles database schema and ORM; View handles HTTP request logic; Template renders dynamic HTML to the user.",
			"marks": 3,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": (
				"• Point 1 [1 Mark]: Model: Defines data structures, validations, and ORM mapping to relational database tables.\n"
				"• Point 2 [1 Mark]: View: Processes HTTP requests, invokes models, and prepares context dictionaries.\n"
				"• Point 3 [1 Mark]: Template: Presentation layer rendering HTML with Django Template Language (DTL)."
			),
			"solution": "Django's MVT pattern decouples data access (Model), business logic (View), and user interface representation (Template), promoting maintainability and separation of concerns.",
			"internal_choice_question": None,
		},
		{
			"question": "Explain how Python manages memory using Reference Counting and the Generational Cycle-Detecting Garbage Collector.",
			"correct_answer": "Reference counting deallocates memory when ref count reaches 0; cyclic GC detects and collects circular reference graphs across 3 generations.",
			"marks": 3,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": (
				"• Point 1 [1 Mark]: Reference counting: Tracks references per object; immediately frees memory when count drops to zero.\n"
				"• Point 2 [1 Mark]: Circular references: Explains why reference counting alone fails for self-referential structures (e.g. `a.ref = b; b.ref = a`).\n"
				"• Point 3 [1 Mark]: Generational GC: Classifies objects into Gen 0, Gen 1, and Gen 2, running cycle-detection heuristics."
			),
			"solution": "CPython uses reference counting as its primary memory management strategy. To handle circular reference cycles, Python runs a generational garbage collector that inspects object graphs periodically.",
			"internal_choice_question": None,
		},
		{
			"question": "Compare relational databases (PostgreSQL/SQLite) with document databases in the context of Full Stack web applications.",
			"correct_answer": "Relational databases enforce strict schemas and ACID transactions with foreign keys; document databases offer flexible JSON-like schemas.",
			"marks": 3,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": (
				"• Point 1 [1 Mark]: Relational schema: Tables, columns, foreign key constraints, and relational normalization.\n"
				"• Point 2 [1 Mark]: ACID compliance: Strong consistency and transactional rollback guarantees in PostgreSQL/SQLite.\n"
				"• Point 3 [1 Mark]: Use case comparison: When to choose relational (financial, structured data) vs NoSQL (unstructured, high-velocity)."
			),
			"solution": "Relational databases provide strong ACID guarantees and structured schema validation, essential for financial and core application data. Document databases provide dynamic schema flexibility.",
			"internal_choice_question": None,
		},
		{
			"question": "Explain the role and lifecycle of the Context Manager protocol in Python. Detail the responsibilities of `__enter__` and `__exit__`.",
			"correct_answer": "`__enter__` acquires resources and returns context; `__exit__` guarantees resource release and handles exceptions.",
			"marks": 3,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": (
				"• Point 1 [1 Mark]: Role of `with` statement: Automatic setup and teardown for external resources.\n"
				"• Point 2 [1 Mark]: `__enter__`: Sets up the resource and binds target variable.\n"
				"• Point 3 [1 Mark]: `__exit__`: Receives exception type, value, and traceback; returns boolean indicating whether exception was suppressed."
			),
			"solution": "Context managers eliminate resource leaks by ensuring teardown routines execute reliably even when runtime exceptions occur.",
			"internal_choice_question": None,
		},
		{
			"question": "Outline the Front-End Foundations taught in the Python Full Stack Developer course (HTML5, CSS3, modern JavaScript ES6+).",
			"correct_answer": "HTML5 semantic markup, CSS3 responsive styling (flexbox/grid), and JavaScript ES6+ for dynamic UI and DOM manipulation.",
			"marks": 3,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": (
				"• Point 1 [1 Mark]: HTML5: Semantic elements (`<header>`, `<nav>`, `<article>`, `<section>`) ensuring accessibility and structure.\n"
				"• Point 2 [1 Mark]: CSS3: Responsive design with Flexbox, CSS Grid, media queries, and animations.\n"
				"• Point 3 [1 Mark]: Modern JavaScript (ES6+): Arrow functions, promises, async/await, and fetch API for asynchronous backend communication."
			),
			"solution": "The front-end curriculum equips developers to construct accessible HTML5 structures, style responsive interfaces using CSS3, and manage interactive state with modern JavaScript.",
			"internal_choice_question": None,
		},
	]


def _get_python_long_pool(source_tag: str) -> List[Dict[str, Any]]:
	return [
		{
			"question": "Provide an in-depth architectural analysis of Python's Object-Oriented Programming (OOP) model. Explain class instantiation, constructor initialization (`__init__`), single and multiple inheritance, method resolution order (MRO / C3 linearization), and illustrate with a complete code demonstration.",
			"correct_answer": "Comprehensive breakdown of Python OOP: classes, instances, inheritance, MRO, and syntactically valid code.",
			"marks": 5,
			"difficulty": "Hard",
			"source": source_tag,
			"answer_key_detail": (
				"• Theoretical Foundation & Principles [1 Mark]: Definition of classes as type factories and `__new__` vs `__init__`.\n"
				"• Inheritance & Super Mechanism [1 Mark]: Detailed explanation of `super()` and cooperative multiple inheritance.\n"
				"• Method Resolution Order (MRO) [1 Mark]: Explanation of C3 linearization algorithm and `Class.__mro__`.\n"
				"• Implementation / Code Demonstration [1 Mark]: Syntactically valid Python code showing base class, subclass, `super()`, and method overriding.\n"
				"• Best Practices & Pitfalls [1 Mark]: Avoiding fragile multiple inheritance diamond problems and enforcing encapsulation with `@property`."
			),
			"solution": (
				"1. Foundation: In Python, everything is an object. `__new__` allocates memory, while `__init__` sets initial instance attributes.\n"
				"2. Inheritance: `class Derived(Base):` establishes inheritance. `super().__init__()` delegates to parent constructors.\n"
				"3. MRO: C3 linearization algorithm resolves attributes consistently in multiple inheritance hierarchies.\n"
				"4. Code:\n"
				"   class User:\n"
				"       def __init__(self, username): self.username = username\n"
				"   class Admin(User):\n"
				"       def __init__(self, username, level):\n"
				"           super().__init__(username)\n"
				"           self.level = level\n"
				"5. Best Practices: Use `@property` for getters/setters and favor composition over deeply nested inheritance trees."
			),
			"internal_choice_question": {
				"question": "OR: Analyze Python Decorators and Higher-Order Functions. Explain how decorators leverage closures and first-class functions, write a custom parameterized decorator that measures and logs execution time of arbitrary functions, and discuss practical production use cases.",
				"marks": 5,
				"correct_answer": "Detailed breakdown of decorators, closures, `functools.wraps`, timing decorator implementation, and production applications.",
				"answer_key_detail": (
					"• Theoretical Foundation [1 Mark]: First-class functions, inner function closures, and the `@decorator` syntactic sugar.\n"
					"• Decorator Anatomy [1 Mark]: Explanation of outer wrapper function, inner wrapper function, and `*args, **kwargs` forwarding.\n"
					"• Role of `functools.wraps` [1 Mark]: Preserving function introspection (`__name__`, `__doc__`).\n"
					"• Code Demonstration [1 Mark]: Syntactically valid timer decorator using `time.perf_counter()`.\n"
					"• Production Applications [1 Mark]: Authentication, rate limiting, logging, and caching in web frameworks."
				),
				"solution": "Decorators wrap functions to dynamically extend their behavior without altering source code. Using `functools.wraps` ensures metadata preservation.",
			},
		},
		{
			"question": "Examine the end-to-end architecture of a modern Python Full Stack Web Application. Detail the request-response lifecycle from browser client to Nginx, WSGI/ASGI application server (Gunicorn/Uvicorn), Django/Flask routing and ORM, and database persistence (PostgreSQL).",
			"correct_answer": "Complete request lifecycle from client HTTP request through reverse proxy, WSGI gateway, framework routing, ORM SQL execution, and response rendering.",
			"marks": 5,
			"difficulty": "Hard",
			"source": source_tag,
			"answer_key_detail": (
				"• Client to Reverse Proxy [1 Mark]: Client initiates HTTPS request -> DNS lookup -> Nginx handles SSL termination and static files.\n"
				"• WSGI/ASGI Interface [1 Mark]: Nginx proxies request to Gunicorn/Uvicorn using the WSGI/ASGI protocol.\n"
				"• Framework Routing & Middleware [1 Mark]: Django middleware pipeline executes security, session, and CSRF checks before dispatching to View.\n"
				"• ORM & Database Layer [1 Mark]: Django ORM translates querysets into optimized SQL statements executed against PostgreSQL.\n"
				"• Response Pipeline [1 Mark]: View returns HTTP response or serialized JSON, traversing middleware back to client."
			),
			"solution": (
				"1. Nginx terminates TLS and serves static assets directly.\n"
				"2. Dynamic requests pass via WSGI/ASGI socket to Gunicorn worker processes.\n"
				"3. Django passes request through middleware layers (Security, Sessions, CSRF) to the URL dispatcher.\n"
				"4. The view queries the database via Django ORM and builds the response.\n"
				"5. The response travels back through middleware to Nginx and down to the client browser."
			),
			"internal_choice_question": {
				"question": "OR: Examine Database Design and Query Optimization in Full Stack applications using Django ORM and PostgreSQL. Detail entity modeling, foreign key relationships, the N+1 query problem, and how `select_related` and `prefetch_related` resolve performance bottlenecks.",
				"marks": 5,
				"correct_answer": "Relational schema design, normalization, N+1 query diagnosis, and optimization using select_related (SQL JOIN) and prefetch_related (batch IN query).",
				"answer_key_detail": (
					"• Schema Design & Normalization [1 Mark]: 1-to-1, 1-to-Many, and Many-to-Many entity relationships with foreign keys.\n"
					"• N+1 Query Problem Diagnosis [1 Mark]: Explaining how loop iteration over related models triggers N separate SQL queries.\n"
					"• `select_related` Mechanics [1 Mark]: Using SQL inner/left outer JOINs for single-valued relationships (ForeignKey, OneToOne).\n"
					"• `prefetch_related` Mechanics [1 Mark]: Using multi-table batch lookups with SQL `IN` operators for multi-valued relationships (ManyToMany).\n"
					"• Database Indexing & Metrics [1 Mark]: Adding `db_index=True`, compound indexes, and evaluating query plans with `EXPLAIN ANALYZE`."
				),
				"solution": "The N+1 problem occurs when querying related objects inside loops. `select_related` performs an immediate SQL JOIN, while `prefetch_related` executes an efficient separate batch query.",
			},
		},
		{
			"question": "Provide a comprehensive analysis of Asynchronous Programming in Python using `asyncio`. Contrast synchronous multithreading with cooperative multitasking, detail the Event Loop architecture, explain `async`/`await` keywords, and illustrate with a code demonstration fetching concurrent mock API endpoints.",
			"correct_answer": "Detailed breakdown of asyncio event loop, coroutines, async/await, non-blocking I/O, and concurrent execution code.",
			"marks": 5,
			"difficulty": "Hard",
			"source": source_tag,
			"answer_key_detail": (
				"• Synchronous vs Asynchronous Paradigms [1 Mark]: OS thread context switching overhead vs single-threaded cooperative event loops.\n"
				"• Event Loop Architecture [1 Mark]: Task scheduling, I/O multiplexing (epoll/kqueue), and non-blocking sockets.\n"
				"• Coroutines & `async`/`await` [1 Mark]: Coroutines as suspended execution states yielding control upon `await`.\n"
				"• Code Implementation [1 Mark]: Syntactically valid `asyncio` code with `asyncio.gather()` executing multiple concurrent tasks.\n"
				"• Pitfalls & Best Practices [1 Mark]: Avoiding CPU-bound blocking calls inside the event loop and utilizing `run_in_executor()`."
			),
			"solution": (
				"1. `asyncio` enables high-concurrency I/O bound execution without thread switching overhead.\n"
				"2. An Event Loop manages task execution and schedules coroutines when non-blocking I/O completes.\n"
				"3. `async def` defines a coroutine; `await` yields execution until the awaited future resolves.\n"
				"4. Code uses `asyncio.gather(*tasks)` to run concurrent network operations efficiently."
			),
			"internal_choice_question": {
				"question": "OR: Analyze Software Testing Methodologies for Python Applications. Differentiate between Unit Testing, Integration Testing, and End-to-End Testing. Detail test fixtures, parameterization with `pytest`, mocking external dependencies with `unittest.mock`, and continuous integration pipelines.",
				"marks": 5,
				"correct_answer": "Testing pyramid, unit vs integration vs E2E, pytest fixtures and parameterization, mocking, and CI/CD integration.",
				"answer_key_detail": (
					"• Testing Pyramid Breakdown [1 Mark]: Unit tests (fast, isolated), Integration tests (database, services), and E2E tests (user journey).\n"
					"• Pytest Fixtures & Lifecycle [1 Mark]: Scope of fixtures (`function`, `module`, `session`), dependency injection, and teardown.\n"
					"• Parameterized Testing [1 Mark]: Using `@pytest.mark.parametrize` to execute multiple test cases across data sets.\n"
					"• Mocking & Isolation [1 Mark]: Using `unittest.mock.patch` to isolate third-party APIs and prevent flaky tests.\n"
					"• Code Coverage & CI [1 Mark]: Enforcing coverage thresholds with `pytest-cov` and running automated test suites in CI pipelines."
				),
				"solution": "Comprehensive testing combines fast isolated unit tests with mock objects and robust integration tests against realistic database fixtures.",
			},
		},
	]


def _get_python_application_pool(source_tag: str) -> List[Dict[str, Any]]:
	return [
		{
			"question": "Case Study: A Python Full Stack web application experiences catastrophic performance degradation during high-traffic flash sales. Database CPU utilization spikes to 100%, and API response times jump from 80ms to over 12 seconds. Technical investigation reveals redundant identical database queries for product catalog records. Formulate a technical diagnosis and design a high-throughput caching architecture using Redis.",
			"correct_answer": "Diagnosis of cache stampede and unindexed database queries. Architecture using Redis Cache-Aside pattern with TTL expiration and database indexing.",
			"marks": 4,
			"difficulty": "Hard",
			"source": source_tag,
			"answer_key_detail": (
				"• Sub-part (a) Problem Diagnosis [2 Marks]: Correctly identifies unmitigated database read contention, unindexed foreign key queries, and absence of an in-memory caching tier.\n"
				"• Sub-part (b) Technical Mitigation [2 Marks]: Concrete architectural design implementing Redis Cache-Aside pattern, setting appropriate TTL, and implementing automated cache invalidation on product updates."
			),
			"solution": (
				"Part (a): Direct database lookups under high concurrent traffic overload relational connection pools and saturated database CPU.\n"
				"Part (b): Deploy an in-memory Redis caching layer. Implement the Cache-Aside pattern: Check Redis first; on cache miss, query PostgreSQL, populate Redis with a 5-minute TTL, and return results."
			),
			"internal_choice_question": {
				"question": "OR: Case Study: A financial web portal built in Python must prevent SQL Injection vulnerabilities across all dynamic search and reporting endpoints. Explain the mechanics of SQL Injection attacks and demonstrate how Django ORM parameterized query generation guarantees security against malicious payloads.",
				"marks": 4,
				"correct_answer": "Explanation of SQL injection mechanisms and parameter binding via prepared statements in Django ORM.",
				"answer_key_detail": (
					"• Sub-part (a) Vulnerability Mechanics [2 Marks]: Details how untrusted user input directly concatenated into raw SQL strings allows attackers to alter query logic.\n"
					"• Sub-part (b) Secure Remediation [2 Marks]: Explains how Django ORM escapes input and utilizes parameterized prepared statements, rendering injected syntax harmless."
				),
				"solution": "Raw SQL concatenation enables attackers to inject syntax (e.g. `' OR 1=1 --`). Django ORM uses parameterized queries where user inputs are treated strictly as data literals rather than executable commands.",
			},
		},
		{
			"question": "Case Study: An e-commerce platform requires background processing for video encoding and invoice PDF generation. Performing these tasks synchronously inside HTTP request handlers causes gateway timeouts (HTTP 504) for clients. Design an asynchronous task worker architecture using Celery, Redis message broker, and Django.",
			"correct_answer": "Asynchronous task delegation via Celery workers and Redis message queue, returning immediate 202 Accepted HTTP responses to clients.",
			"marks": 4,
			"difficulty": "Hard",
			"source": source_tag,
			"answer_key_detail": (
				"• Sub-part (a) Architecture Breakdown [2 Marks]: Decoupling web request handling from heavy computational tasks via a message broker (Redis) and worker pool (Celery).\n"
				"• Sub-part (b) Client Workflow & State Polling [2 Marks]: Returning immediate HTTP 202 Accepted with task ID, and providing a polling or WebSocket endpoint to report task completion."
			),
			"solution": (
				"Part (a): Offload intensive operations by defining `@shared_task` in Celery. The web view dispatches `task.delay(args)` to Redis and returns immediately.\n"
				"Part (b): Celery workers consume tasks from the queue in the background. The client polls a task status endpoint or receives a webhook/WebSocket event upon completion."
			),
			"internal_choice_question": {
				"question": "OR: Case Study: A collaborative developer team experiences frequent merge conflicts and broken production builds. Formulate a robust Git branching strategy (such as GitFlow or GitHub Flow) and specify automated CI/CD safeguards to enforce code quality before merging into main.",
				"marks": 4,
				"correct_answer": "Feature branching strategy, pull requests with required peer review, automated linters, and CI test pipeline gates.",
				"answer_key_detail": (
					"• Sub-part (a) Branching Strategy [2 Marks]: Definition of main, develop, and short-lived feature branches with rebase/merge standards.\n"
					"• Sub-part (b) CI/CD Quality Gates [2 Marks]: Automated pull request verification enforcing PEP 8 linting, unit test execution, and minimum code coverage thresholds."
				),
				"solution": "Adopt GitHub Flow with short-lived feature branches. Protect the `main` branch with mandatory PR reviews and automated GitHub Actions running linters and test suites.",
			},
		},
		{
			"question": "Case Study: A RESTful API built in Python needs to implement secure authentication and authorization for multi-tenant users. Compare Session-based authentication with Token-based JSON Web Token (JWT) authentication for web and mobile clients, and evaluate token expiration, revocation, and security best practices.",
			"correct_answer": "Comparative evaluation of server-side sessions vs stateless JWT tokens, token payload security, and refresh token rotation.",
			"marks": 4,
			"difficulty": "Hard",
			"source": source_tag,
			"answer_key_detail": (
				"• Sub-part (a) Paradigm Comparison [2 Marks]: Stateful server-side sessions requiring centralized store vs stateless JWTs carrying cryptographically signed claims.\n"
				"• Sub-part (b) Security & Lifecycle [2 Marks]: Implementation of short-lived Access Tokens (15 min) paired with Refresh Tokens in HTTP-only cookies to mitigate XSS and CSRF."
			),
			"solution": (
				"Part (a): Stateful sessions require shared Redis storage across cluster nodes. JWTs are stateless, self-contained, and ideal for microservices and mobile apps.\n"
				"Part (b): Store Access Tokens in memory and Refresh Tokens in secure `HttpOnly`, `SameSite=Strict` cookies with refresh token rotation upon each exchange."
			),
			"internal_choice_question": {
				"question": "OR: Case Study: A data processing service reads CSV files uploaded by external vendors. Malformed rows with invalid types and missing columns intermittently crash the ingestion pipeline. Design a defensive data validation pipeline using Python data classes or Pydantic with automated error reporting.",
				"marks": 4,
				"correct_answer": "Pydantic schema validation with automatic type coercion, row-level error logging, and graceful isolation of corrupted records.",
				"answer_key_detail": (
					"• Sub-part (a) Defensive Schema Design [2 Marks]: Definition of Pydantic BaseModel specifying strict field types, default values, and custom validators.\n"
					"• Sub-part (b) Fault-Tolerant Pipeline [2 Marks]: Row-by-row validation inside try-except blocks, storing invalid rows in an error log while continuing ingestion."
				),
				"solution": "Define a Pydantic schema for expected columns. During ingestion, parse each row into the model; valid rows are batched for database insertion, while rejected rows are appended to an error audit report.",
			},
		},
	]


# =====================================================================
# COMPUTER SCIENCE & SYSTEMS ARCHITECTURE QUESTION POOL
# =====================================================================

def _get_cs_mcq_pool(source_tag: str) -> List[Dict[str, Any]]:
	return [
		{
			"question": "Which CPU component performs basic arithmetic calculations and logical bitwise operations?",
			"options": ["(A) Arithmetic Logic Unit (ALU)", "(B) Control Unit (CU)", "(C) Program Counter (PC)", "(D) Memory Address Register (MAR)"],
			"correct_answer": "(A) Arithmetic Logic Unit (ALU)",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (A) Arithmetic Logic Unit (ALU). Evaluation Criterion: Full 1 mark awarded for identifying the ALU.",
			"solution": "The Arithmetic Logic Unit (ALU) executes arithmetic operations (addition, subtraction) and logical bitwise evaluations (AND, OR, NOT).",
			"internal_choice_question": None,
		},
		{
			"question": "What is the primary function of the Program Counter (PC) register in CPU execution?",
			"options": ["(A) Stores the result of the last arithmetic operation", "(B) Holds the memory address of the next instruction to be fetched", "(C) Decodes opcode into control signals", "(D) Stores system interrupt flags"],
			"correct_answer": "(B) Holds the memory address of the next instruction to be fetched",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (B). Evaluation Criterion: Full 1 mark awarded for identifying the PC as holding the address of the next instruction.",
			"solution": "The Program Counter (PC) stores the address of the next instruction in memory and increments automatically after each fetch cycle.",
			"internal_choice_question": None,
		},
		{
			"question": "Which sorting algorithm exhibits an average-case time complexity of O(n log n) and worst-case of O(n^2)?",
			"options": ["(A) MergeSort", "(B) QuickSort", "(C) BubbleSort", "(D) HeapSort"],
			"correct_answer": "(B) QuickSort",
			"marks": 1,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (B) QuickSort. Evaluation Criterion: Full 1 mark awarded for identifying QuickSort.",
			"solution": "QuickSort operates in O(n log n) average time using partitioning. If poor pivots are chosen consistently, complexity degrades to O(n^2).",
			"internal_choice_question": None,
		},
		{
			"question": "Which condition is NOT one of the four necessary Coffman conditions required for a system deadlock to occur?",
			"options": ["(A) Mutual Exclusion", "(B) Hold and Wait", "(C) Preemptive Resource Reallocation", "(D) Circular Wait"],
			"correct_answer": "(C) Preemptive Resource Reallocation",
			"marks": 1,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (C). Evaluation Criterion: Full 1 mark awarded for recognizing 'No Preemption' is the necessary condition.",
			"solution": "The 4 Coffman conditions for deadlock are: Mutual Exclusion, Hold and Wait, No Preemption, and Circular Wait. Preemption breaks deadlock.",
			"internal_choice_question": None,
		},
		{
			"question": "In the memory hierarchy, which storage level offers the fastest access latency?",
			"options": ["(A) Main RAM", "(B) L1 CPU Cache", "(C) L3 CPU Cache", "(D) Solid State Drive (NVMe)"],
			"correct_answer": "(B) L1 CPU Cache",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (B) L1 CPU Cache. Evaluation Criterion: Full 1 mark awarded for identifying L1 cache.",
			"solution": "L1 cache resides directly on the CPU core and operates with sub-nanosecond access latency.",
			"internal_choice_question": None,
		},
	]


def _get_cs_vsa_pool(source_tag: str) -> List[Dict[str, Any]]:
	return [
		{
			"question": "Differentiate between a Process and a Thread in operating system execution.",
			"correct_answer": "A process is an isolated executing program with its own dedicated memory space; a thread is a lightweight execution unit sharing memory with sibling threads.",
			"marks": 2,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": (
				"• Point 1 [1 Mark]: Memory isolation: Processes have independent virtual address spaces.\n"
				"• Point 2 [1 Mark]: Resource sharing: Threads within the same process share heap, code, and global data."
			),
			"solution": "Processes are heavyweight with separate memory maps. Threads share the process address space, enabling low-overhead communication.",
			"internal_choice_question": None,
		},
		{
			"question": "State the four stages comprising the classic Von Neumann CPU Instruction Cycle.",
			"correct_answer": "1. Fetch, 2. Decode, 3. Execute, 4. Writeback / Store.",
			"marks": 2,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": (
				"• Point 1 [1 Mark]: Identifies Fetch and Decode stages correctly.\n"
				"• Point 2 [1 Mark]: Identifies Execute and Writeback/Store stages correctly."
			),
			"solution": "The CPU fetches the instruction from RAM, decodes opcode into control signals, executes the instruction, and writes results back to memory or registers.",
			"internal_choice_question": None,
		},
	]


def _get_cs_short_pool(source_tag: str) -> List[Dict[str, Any]]:
	return [
		{
			"question": "Explain the concept of Virtual Memory and how Paging eliminates external memory fragmentation.",
			"correct_answer": "Virtual memory maps virtual addresses to physical frames via page tables, allowing non-contiguous allocation and eliminating external fragmentation.",
			"marks": 3,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": (
				"• Point 1 [1 Mark]: Virtual Memory abstraction: Decoupling process address space from physical RAM.\n"
				"• Point 2 [1 Mark]: Fixed-size paging: Dividing virtual memory into pages and physical memory into identical frames.\n"
				"• Point 3 [1 Mark]: External fragmentation mitigation: Because any free frame can hold any page, external fragmentation is eliminated."
			),
			"solution": "Virtual memory allows programs to execute without requiring contiguous physical memory allocations, mapped dynamically via Page Tables and the MMU.",
			"internal_choice_question": None,
		},
	]


def _get_cs_long_pool(source_tag: str) -> List[Dict[str, Any]]:
	return [
		{
			"question": "Provide a comprehensive architectural analysis of CPU Cache Memory and Cache Coherence in modern multi-core processors. Detail cache hierarchy (L1, L2, L3), cache mapping policies (Direct-Mapped vs Set-Associative), and explain the MESI protocol for maintaining coherence across core caches.",
			"correct_answer": "Complete analysis of L1/L2/L3 cache hierarchy, set-associative mapping, cache miss classifications, and MESI protocol states.",
			"marks": 5,
			"difficulty": "Hard",
			"source": source_tag,
			"answer_key_detail": (
				"• Cache Hierarchy & Latency [1 Mark]: Organization of private L1/L2 per core and shared L3 cache.\n"
				"• Cache Mapping & Misses [1 Mark]: Direct-mapped vs n-way Set-Associative mapping; Compulsory, Capacity, and Conflict misses.\n"
				"• MESI Protocol States [1 Mark]: Modified, Exclusive, Shared, and Invalid state transitions.\n"
				"• Write Policies [1 Mark]: Write-Through vs Write-Back and Write-Allocate mechanics.\n"
				"• False Sharing & Optimization [1 Mark]: Cache line bouncing and data alignment techniques."
			),
			"solution": "Modern CPUs use multi-level caches to bridge the CPU-DRAM speed gap. The MESI protocol maintains memory consistency across cores via snooping and state transitions.",
			"internal_choice_question": {
				"question": "OR: Analyze Deadlock Detection and Avoidance in Operating Systems. Detail the Banker's Algorithm with resource-allocation matrices, evaluate safe vs unsafe system states, and contrast avoidance with deadlock prevention techniques.",
				"marks": 5,
				"correct_answer": "Banker's Algorithm specification, safe state analysis, resource allocation matrices, and Coffman condition disruption.",
				"answer_key_detail": (
					"• Theoretical Foundations [1 Mark]: Definition of deadlock and Coffman conditions.\n"
					"• Banker's Algorithm Matrices [1 Mark]: Allocation, Max, Available, and Need matrices.\n"
					"• Safe State Verification [1 Mark]: Step-by-step simulation demonstrating whether a request can be granted safely.\n"
					"• Prevention vs Avoidance [1 Mark]: Static restriction (prevention) vs dynamic runtime checking (avoidance).\n"
					"• Real-World Trade-Offs [1 Mark]: Overhead of tracking maximum resource claims in modern operating systems."
				),
				"solution": "The Banker's Algorithm tests for safety by simulating the allocation of predetermined maximum possible amounts of all resources, ensuring circular wait cannot develop.",
			},
		},
	]


def _get_cs_application_pool(source_tag: str) -> List[Dict[str, Any]]:
	return [
		{
			"question": "Case Scenario: A multi-threaded storage service experiences high latency and lock contention when multiple worker threads concurrently append entries to a shared transaction log. Formulate an architectural strategy using lock-free ring buffers or read-copy-update (RCU) to maximize throughput.",
			"correct_answer": "Implementation of lock-free circular ring buffer using atomic compare-and-swap (CAS) operations.",
			"marks": 4,
			"difficulty": "Hard",
			"source": source_tag,
			"answer_key_detail": (
				"• Sub-part (a) Contention Diagnosis [2 Marks]: Analyzes thread blocking and cache invalidation under mutex locks.\n"
				"• Sub-part (b) Lock-Free Remediation [2 Marks]: Designs single-producer single-consumer or multi-producer ring buffer using atomic CAS pointers."
			),
			"solution": "Replace coarse-grained mutex locking with a pre-allocated lock-free ring buffer utilizing atomic memory operations, eliminating thread sleep and context switching.",
			"internal_choice_question": {
				"question": "OR: Case Scenario: An analytical database query engine must sort in-memory datasets consisting of 100 million records. Compare QuickSort, MergeSort, and RadixSort for this workload, considering CPU cache locality, memory overhead, and parallel scalability.",
				"marks": 4,
				"correct_answer": "Comparative evaluation of O(n log n) comparison sorts vs O(k*n) non-comparison RadixSort with SIMD vectorization.",
				"answer_key_detail": (
					"• Sub-part (a) Algorithmic Analysis [2 Marks]: Comparison of cache locality, branch predictability, and auxiliary memory footprints.\n"
					"• Sub-part (b) Parallel Architecture [2 Marks]: Selection of parallel RadixSort or multi-threaded sample sort for memory bandwidth saturation."
				),
				"solution": "For integer keys, RadixSort achieves linear O(n) runtime without branch mispredictions. Parallel MergeSort guarantees stability with predictable O(n) auxiliary memory.",
			},
		},
	]


# =====================================================================
# C PROGRAMMING QUESTION POOL
# =====================================================================

def _get_c_mcq_pool(source_tag: str) -> List[Dict[str, Any]]:
	return [
		{
			"question": "Who created the C programming language at Bell Labs in 1972?",
			"options": ["(A) Dennis Ritchie", "(B) Ken Thompson", "(C) Brian Kernighan", "(D) Bjarne Stroustrup"],
			"correct_answer": "(A) Dennis Ritchie",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (A) Dennis Ritchie. Evaluation Criterion: Full 1 mark awarded for identifying Dennis Ritchie.",
			"solution": "Dennis Ritchie created C at Bell Labs in 1972 to implement the UNIX operating system.",
			"internal_choice_question": None,
		},
		{
			"question": "Which operator is used in C to extract the memory address of a variable?",
			"options": ["(A) Asterisk (*)", "(B) Ampersand (&)", "(C) Arrow (->)", "(D) Percent (%)"],
			"correct_answer": "(B) Ampersand (&)",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (B) Ampersand (&). Evaluation Criterion: Full 1 mark awarded for identifying the address-of operator.",
			"solution": "The ampersand `&` yields the memory address of an lvalue. The asterisk `*` dereferences a pointer.",
			"internal_choice_question": None,
		},
	]


def _get_c_vsa_pool(source_tag: str) -> List[Dict[str, Any]]:
	return [
		{
			"question": "Differentiate between `malloc()` and `calloc()` in C dynamic memory allocation.",
			"correct_answer": "`malloc()` allocates uninitialized raw bytes; `calloc()` allocates memory and zeroes out all allocated bytes.",
			"marks": 2,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": (
				"• Point 1 [1 Mark]: Parameter difference (`malloc(size)` vs `calloc(num, size)`).\n"
				"• Point 2 [1 Mark]: Memory initialization (calloc zeroes memory; malloc leaves garbage values)."
			),
			"solution": "`malloc` allocates uninitialized memory. `calloc` initializes all allocated bytes to zero.",
			"internal_choice_question": None,
		},
	]


def _get_c_short_pool(source_tag: str) -> List[Dict[str, Any]]:
	return [
		{
			"question": "Explain the four primary stages of the C compilation pipeline: Preprocessing, Compiling, Assembling, and Linking.",
			"correct_answer": "Preprocessor expands macros/includes -> Compiler generates assembly -> Assembler generates machine code object files -> Linker binds objects and libraries into executable.",
			"marks": 3,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": (
				"• Point 1 [1 Mark]: Preprocessing (`#include`, `#define`) and Compilation (C source to assembly).\n"
				"• Point 2 [1 Mark]: Assembly (assembly instructions to `.o` object files).\n"
				"• Point 3 [1 Mark]: Linking (resolving external references and library symbols into final binary)."
			),
			"solution": "The C compilation pipeline transforms human-readable source code into machine code through four sequential stages.",
			"internal_choice_question": None,
		},
	]


def _get_c_long_pool(source_tag: str) -> List[Dict[str, Any]]:
	return [
		{
			"question": "Provide an in-depth architectural analysis of Pointers and Dynamic Memory Management in C. Explain pointer arithmetic, memory allocation on the heap (`malloc`, `realloc`, `free`), dangling pointers, memory leaks, and buffer overflows with code examples.",
			"correct_answer": "Complete examination of C pointer mechanics, heap lifecycle, dangling pointer prevention, and boundary safety.",
			"marks": 5,
			"difficulty": "Hard",
			"source": source_tag,
			"answer_key_detail": (
				"• Pointer Arithmetic & Indirection [1 Mark]: Scaling arithmetic by `sizeof(T)` and dereferencing.\n"
				"• Heap Management Lifecycle [1 Mark]: Correct usage of `malloc`, `realloc`, and `free`.\n"
				"• Dangling Pointers & Double Free [1 Mark]: Hazards of referencing deallocated memory and mitigation by setting pointers to `NULL`.\n"
				"• Buffer Overflows & Security [1 Mark]: Exploitation of unbounded string functions (`strcpy`) vs safe alternatives (`strncpy`).\n"
				"• Code Demonstration [1 Mark]: Syntactically valid C program demonstrating safe allocation, validation, and deallocation."
			),
			"solution": "Direct pointer manipulation gives C high efficiency, but manual memory management requires strict discipline to prevent leaks and buffer overflows.",
			"internal_choice_question": {
				"question": "OR: Analyze Structs and Data Alignment in C. Explain structure padding, memory alignment rules based on data types, bit-fields, and the `#pragma pack` directive.",
				"marks": 5,
				"correct_answer": "Structure layout, compiler alignment padding, hardware word boundary constraints, and packing directives.",
				"answer_key_detail": (
					"• Hardware Alignment Constraints [1 Mark]: Why CPUs access memory faster on aligned word boundaries.\n"
					"• Structure Padding Mechanics [1 Mark]: How compilers insert unused bytes between struct members.\n"
					"• Reordering Optimization [1 Mark]: Arranging struct members by decreasing size to minimize memory footprints.\n"
					"• Bit-Fields & Packing [1 Mark]: Defining bit-level flags and utilizing `#pragma pack(1)` for embedded protocols.\n"
					"• Architectural Trade-offs [1 Mark]: Compact memory footprints vs CPU access latency penalties."
				),
				"solution": "Compilers add padding between struct fields to ensure alignment on CPU word boundaries. Reordering fields minimizes waste.",
			},
		},
	]


def _get_c_application_pool(source_tag: str) -> List[Dict[str, Any]]:
	return [
		{
			"question": "Case Scenario: A C embedded firmware application crashes intermittently with segmentation faults (`SIGSEGV`). Investigation reveals that worker routines access pointers after calling `free()`. Formulate a memory management strategy to eliminate use-after-free defects.",
			"correct_answer": "Set pointers to NULL immediately after freeing, implement custom wrapper allocation macros, and utilize static analysis tools (Valgrind / AddressSanitizer).",
			"marks": 4,
			"difficulty": "Hard",
			"source": source_tag,
			"answer_key_detail": (
				"• Sub-part (a) Defect Diagnosis [2 Marks]: Explains use-after-free and dangling pointer risks under dynamic heap re-allocation.\n"
				"• Sub-part (b) Remediation Strategy [2 Marks]: Safe free macro (`#define SAFE_FREE(p) do { free(p); p = NULL; } while(0)`) and sanitizer integration."
			),
			"solution": "Always set pointers to NULL upon freeing to turn undefined behavior into predictable null pointer exceptions. Run AddressSanitizer during CI builds.",
			"internal_choice_question": {
				"question": "OR: Case Scenario: Design an efficient, thread-safe dynamic string buffer in C capable of automatic resizing without memory leaks.",
				"marks": 4,
				"correct_answer": "Dynamic string struct holding data pointer, length, and capacity, using geometric growth with `realloc()`.",
				"answer_key_detail": (
					"• Sub-part (a) Struct Design [2 Marks]: Specification of struct with `char *buffer`, `size_t length`, and `size_t capacity`.\n"
					"• Sub-part (b) Resizing & Error Safety [2 Marks]: Geometric doubling with `realloc()` temporary pointer to prevent memory leaks on failure."
				),
				"solution": "Store capacity and length alongside buffer pointer. Double capacity upon overflow using `temp = realloc(buf, new_cap)` to prevent losing original memory if allocation fails.",
			},
		},
	]


# =====================================================================
# FRAPPE FRAMEWORK QUESTION POOL
# =====================================================================

def _get_frappe_mcq_pool(source_tag: str) -> List[Dict[str, Any]]:
	return [
		{
			"question": "In the Frappe Framework, what is the core metadata model defining database schema, controllers, and UI views?",
			"options": ["(A) ModelView", "(B) DocType", "(C) MigrationSchema", "(D) EntityMap"],
			"correct_answer": "(B) DocType",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (B) DocType. Evaluation Criterion: Full 1 mark awarded for identifying DocType.",
			"solution": "In Frappe, DocType is the foundational building block describing fields, database tables, validations, and permissions.",
			"internal_choice_question": None,
		},
		{
			"question": "Which Python controller method is invoked immediately before saving a Frappe document to the database?",
			"options": ["(A) before_insert()", "(B) validate()", "(C) on_update()", "(D) on_submit()"],
			"correct_answer": "(B) validate()",
			"marks": 1,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": "[1 Mark] Correct Option: (B) validate(). Evaluation Criterion: Full 1 mark awarded for identifying validate().",
			"solution": "The `validate()` hook runs on every save prior to database persistence, allowing custom business logic and constraint checks.",
			"internal_choice_question": None,
		},
	]


def _get_frappe_vsa_pool(source_tag: str) -> List[Dict[str, Any]]:
	return [
		{
			"question": "Differentiate between a Single DocType and a standard DocType in Frappe.",
			"correct_answer": "A standard DocType creates a dedicated MariaDB table for multiple records; a Single DocType stores key-value settings in the `tabSingles` table.",
			"marks": 2,
			"difficulty": "Easy",
			"source": source_tag,
			"answer_key_detail": (
				"• Point 1 [1 Mark]: Standard DocType creates a distinct MariaDB table (`tabDocTypeName`).\n"
				"• Point 2 [1 Mark]: Single DocType stores singleton configuration values in `tabSingles` without creating a new table."
			),
			"solution": "Standard DocTypes hold multiple records (like Customer, Item). Single DocTypes store application-wide settings (like LMS Settings).",
			"internal_choice_question": None,
		},
	]


def _get_frappe_short_pool(source_tag: str) -> List[Dict[str, Any]]:
	return [
		{
			"question": "Explain the role and syntax of Client Scripts vs Server Scripts in extending Frappe applications.",
			"correct_answer": "Client Scripts execute in the browser using JavaScript for UI interactivity; Server Scripts execute on the backend using Python for data validation and API endpoints.",
			"marks": 3,
			"difficulty": "Medium",
			"source": source_tag,
			"answer_key_detail": (
				"• Point 1 [1 Mark]: Client Script triggers (`refresh`, `validate`, field changes) in browser runtime.\n"
				"• Point 2 [1 Mark]: Server Script hooks (DocType Events, API endpoints, Permission queries) in Python.\n"
				"• Point 3 [1 Mark]: Security separation between client-side validation and enforced server-side constraints."
			),
			"solution": "Client scripts handle dynamic form behavior in the browser. Server scripts enforce server-side business rules and expose whitelisted API methods.",
			"internal_choice_question": None,
		},
	]


def _get_frappe_long_pool(source_tag: str) -> List[Dict[str, Any]]:
	return [
		{
			"question": "Provide a comprehensive architectural analysis of the Frappe ORM and Document Lifecycle. Detail the sequence of controller hooks from `before_insert` to `on_submit`, explain Child Tables and database representation, and demonstrate ORM query APIs (`get_doc`, `get_all`, `db.set_value`).",
			"correct_answer": "Detailed examination of Frappe Document lifecycle hooks, child table architecture, and ORM database interaction methods.",
			"marks": 5,
			"difficulty": "Hard",
			"source": source_tag,
			"answer_key_detail": (
				"• Document Lifecycle Sequence [1 Mark]: Execution order: `before_insert` -> `validate` -> `before_save` -> `on_update` -> `on_submit`.\n"
				"• Submittable DocTypes & Workflow [1 Mark]: Docstatus values: 0 (Draft), 1 (Submitted), 2 (Cancelled) and immutability constraints.\n"
				"• Child Tables Architecture [1 Mark]: Parent-child foreign key linkage (`parent`, `parenttype`, `parentfield`, `idx`).\n"
				"• ORM API Demonstration [1 Mark]: Proper usage of `frappe.get_doc()`, `frappe.db.get_value()`, and `frappe.get_all()` with filters.\n"
				"• Transaction Boundaries & Performance [1 Mark]: Managing `frappe.db.commit()`, rollback triggers, and avoiding N+1 queries."
			),
			"solution": "Frappe wraps MariaDB/PostgreSQL with an active-record ORM. Controller hooks ensure validations and business rules execute reliably during document saves and submissions.",
			"internal_choice_question": {
				"question": "OR: Analyze Frappe's Role-Based Access Control (RBAC) and Permission System. Detail Role Permissions Manager, User Permissions, Document Level Permissions, and Permission Query Conditions.",
				"marks": 5,
				"correct_answer": "RBAC architecture, Role Permissions Manager, User Permission filtering, and Permission Query Conditions.",
				"answer_key_detail": (
					"• Role Permissions Manager [1 Mark]: Mapping roles to CRUD operations on DocTypes at specific permission levels (0-9).\n"
					"• Permission Levels [1 Mark]: Restricting sensitive fields to privileged roles using field-level permlevels.\n"
					"• User Permissions [1 Mark]: Enforcing row-level security restricting users to specific documents (e.g. Branch, Company).\n"
					"• Permission Query Hooks [1 Mark]: Using `permission_query_conditions` hook to dynamically append SQL WHERE clauses.\n"
					"• Controller Security Enforcement [1 Mark]: Proper usage of `has_permission()` and avoiding unrestricted `ignore_permissions=True`."
				),
				"solution": "Frappe combines role-based CRUD matrices with row-level User Permissions and dynamic SQL permission queries for comprehensive data isolation.",
			},
		},
	]


def _get_frappe_application_pool(source_tag: str) -> List[Dict[str, Any]]:
	return [
		{
			"question": "Case Scenario: An educational institution using Frappe LMS experiences slow loading times on assessment list views during final examinations. The database server reports heavy CPU load caused by repeated queries fetching related child table records. Formulate a database indexing and caching optimization plan.",
			"correct_answer": "Index child table foreign keys, utilize `frappe.get_all()` with selective field projection, and cache static syllabus data in Redis.",
			"marks": 4,
			"difficulty": "Hard",
			"source": source_tag,
			"answer_key_detail": (
				"• Sub-part (a) Bottleneck Diagnosis [2 Marks]: Identifies unindexed child table parent queries and excessive `frappe.get_doc()` loop calls.\n"
				"• Sub-part (b) Technical Remediation [2 Marks]: Concrete optimization using `frappe.get_all()` with explicit fields, indexing `parent` columns, and utilizing `frappe.cache().get_value()`."
			),
			"solution": "Avoid calling `get_doc` in list loops. Use `frappe.get_all` to project only necessary fields, ensure index on `parent`, and cache configuration in Redis.",
			"internal_choice_question": {
				"question": "OR: Case Scenario: An automated assessment grading background job times out when processing 1,000 student submissions simultaneously. Design a distributed background job queue architecture using Frappe's background enqueue framework.",
				"marks": 4,
				"correct_answer": "Batch processing using `frappe.enqueue()` across default, short, and long Redis worker queues.",
				"answer_key_detail": (
					"• Sub-part (a) Architecture Breakdown [2 Marks]: Chunking student submissions into sub-batches and enqueuing via `frappe.enqueue()`.\n"
					"• Sub-part (b) Monitoring & Fault Tolerance [2 Marks]: Implementing job progress logging, retry backoff, and state persistence upon completion."
				),
				"solution": "Partition submissions into batches of 50. Enqueue each chunk using `frappe.enqueue('module.process_batch', queue='long', timeout=1800)` to execute concurrently across Redis workers.",
			},
		},
	]
