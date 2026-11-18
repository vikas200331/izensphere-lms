# Copyright (c) 2026, Izensphere and contributors
# For license information, please see license.txt

import json
from unittest.mock import MagicMock, patch

import frappe
import requests
from frappe.tests.utils import FrappeTestCase

from lms.lms.ai.ai_assessment_api import (
	api_get_ai_config,
	api_get_generation_history,
	api_save_ai_settings,
	api_test_ai_connection,
)
from lms.lms.ai.ai_service import (
	ANTHROPIC_API_VERSION,
	calculate_cost,
	call_ai_service,
	get_ai_settings,
	get_claude_api_key,
	get_openai_api_key,
	test_ai_connection,
)
from lms.lms.ai.historical_question_generator import generate_historical_ai_questions
from lms.lms.ai.openai_service import get_default_model
from lms.lms.ai.question_bank import create_or_update_bank_question, search_question_bank
from lms.lms.ai.question_paper_generator import generate_question_paper
from lms.lms.ai.quiz_generator import generate_quiz
from lms.lms.ai.student_practice_api import (
	api_ask_ai_question_help,
	api_generate_similar_practice_question,
)


def _mock_http_response(status_code: int = 200, json_data: dict | None = None, text: str = "", headers: dict | None = None):
	resp = MagicMock()
	resp.status_code = status_code
	resp.headers = headers or {}
	if json_data is not None:
		resp.json.return_value = json_data
		resp.text = text or json.dumps(json_data)
	else:
		resp.text = text
		resp.json.side_effect = ValueError("No JSON")
	return resp


def _claude_messages_response(payload_obj: dict, model: str = "claude-sonnet-4-6", in_tok: int = 120, out_tok: int = 240):
	return _mock_http_response(
		200,
		{
			"id": "msg_test_001",
			"type": "message",
			"role": "assistant",
			"model": model,
			"content": [{"type": "text", "text": json.dumps(payload_obj)}],
			"stop_reason": "end_turn",
			"usage": {"input_tokens": in_tok, "output_tokens": out_tok},
		},
	)


class TestClaudeAIProviderIntegration(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")

		# Preserve existing LMS Settings so tests restore cleanly
		cls._orig_settings = get_ai_settings()

		# Setup test Course / Chapter / Lesson
		if not frappe.db.exists("LMS Course", "test-claude-cs"):
			course = frappe.new_doc("LMS Course")
			course.title = "Test Claude CS"
			course.short_introduction = "Introduction to operating systems and distributed computing."
			course.description = "Covers processes, threads, scheduling, virtual memory, and consensus."
			course.published = 1
			course.append("instructors", {"instructor": "Administrator"})
			course.insert(ignore_permissions=True)
		else:
			course = frappe.get_doc("LMS Course", "test-claude-cs")
			if not course.published:
				course.published = 1
				course.save(ignore_permissions=True)
		cls.test_course = course.name

		ch = frappe.new_doc("Course Chapter")
		ch.title = "Claude Test Chapter OS"
		ch.course = cls.test_course
		ch.insert(ignore_permissions=True)
		cls.test_chapter = ch.name

		lesson = frappe.new_doc("Course Lesson")
		lesson.title = "Processes and Threads"
		lesson.chapter = cls.test_chapter
		lesson.course = cls.test_course
		lesson.body = (
			"An operating system process is an independent program in execution with its own virtual address space. "
			"Threads share the process address space while maintaining separate execution stacks and registers. "
			"CPU scheduling algorithms include Round Robin, Shortest Job First, and Priority Scheduling."
		)
		lesson.insert(ignore_permissions=True)
		cls.test_lesson = lesson.name

		# Create Student and Teacher users for permission tests
		cls.student_email = "claude_test_student@example.com"
		if not frappe.db.exists("User", cls.student_email):
			u = frappe.new_doc("User")
			u.email = cls.student_email
			u.first_name = "Claude Student"
			u.send_welcome_email = 0
			u.append("roles", {"role": "LMS Student"})
			u.insert(ignore_permissions=True)

		cls.teacher_email = "claude_test_teacher@example.com"
		if not frappe.db.exists("User", cls.teacher_email):
			u = frappe.new_doc("User")
			u.email = cls.teacher_email
			u.first_name = "Claude Teacher"
			u.send_welcome_email = 0
			u.append("roles", {"role": "Course Creator"})
			u.append("roles", {"role": "Instructor"})
			u.insert(ignore_permissions=True)

		# Enroll student in test_course for practice tests
		if not frappe.db.exists("LMS Enrollment", {"member": cls.student_email, "course": cls.test_course}):
			enr = frappe.new_doc("LMS Enrollment")
			enr.member = cls.student_email
			enr.course = cls.test_course
			enr.insert(ignore_permissions=True)

		frappe.db.commit()

	@classmethod
	def tearDownClass(cls):
		frappe.set_user("Administrator")
		try:
			api_save_ai_settings({
				"provider": cls._orig_settings.get("provider", "Ollama"),
				"ollama_base_url": cls._orig_settings.get("ollama_base_url", "http://localhost:11434"),
				"ollama_model": cls._orig_settings.get("ollama_model", "llama3.2"),
				"openai_base_url": cls._orig_settings.get("openai_base_url", "https://api.openai.com/v1"),
				"openai_model": cls._orig_settings.get("openai_model", "gpt-4o-mini"),
				"claude_base_url": cls._orig_settings.get("claude_base_url", "https://api.anthropic.com"),
				"claude_model": cls._orig_settings.get("claude_model", "claude-sonnet-4-6"),
				"claude_max_tokens": cls._orig_settings.get("claude_max_tokens", 4096),
				"claude_temperature": cls._orig_settings.get("claude_temperature", 0.7),
			})
		except Exception:
			pass
		super().tearDownClass()

	def setUp(self):
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.set_user("Administrator")

	def test_01_provider_switching_and_persistence_preserves_other_configs(self):
		"""Test Cases 8 & 9: Switch between all three providers and verify persistence without overwriting other configs."""
		# 1. Configure Ollama
		api_save_ai_settings({
			"provider": "Ollama",
			"ollama_base_url": "http://localhost:11434",
			"ollama_model": "qwen2.5",
		})
		cfg = api_get_ai_config()
		self.assertEqual(cfg["provider"], "Ollama")
		self.assertEqual(cfg["ollama_model"], "qwen2.5")
		self.assertEqual(get_default_model(), "qwen2.5")

		# 2. Configure OpenAI
		api_save_ai_settings({
			"provider": "OpenAI",
			"openai_base_url": "https://api.openai.com/v1",
			"openai_model": "gpt-4o",
			"openai_api_key": "sk-test-openai-secret-key-1234567890",
		})
		cfg = api_get_ai_config()
		self.assertEqual(cfg["provider"], "OpenAI")
		self.assertEqual(cfg["openai_model"], "gpt-4o")
		self.assertTrue(cfg["has_openai_key"])
		self.assertNotIn("openai_api_key", cfg)
		self.assertEqual(get_default_model(), "gpt-4o")

		# 3. Configure Claude AI (Anthropic)
		api_save_ai_settings({
			"provider": "Claude",
			"claude_base_url": "https://api.anthropic.com",
			"claude_model": "claude-sonnet-4-6",
			"claude_max_tokens": 4096,
			"claude_temperature": 0.4,
			"claude_api_key": "sk-ant-api03-test-claude-secret-key-987654321",
		})
		cfg = api_get_ai_config()
		self.assertEqual(cfg["provider"], "Claude")
		self.assertEqual(cfg["claude_base_url"], "https://api.anthropic.com")
		self.assertEqual(cfg["claude_model"], "claude-sonnet-4-6")
		self.assertEqual(cfg["claude_max_tokens"], 4096)
		self.assertAlmostEqual(cfg["claude_temperature"], 0.4, places=2)
		self.assertTrue(cfg["has_claude_key"])
		self.assertTrue(cfg["has_openai_key"])
		self.assertNotIn("claude_api_key", cfg)
		self.assertNotIn("openai_api_key", cfg)
		self.assertEqual(get_default_model(), "claude-sonnet-4-6")

		# 4. Switch back to Ollama and verify Claude & OpenAI configs & encrypted keys are preserved
		api_save_ai_settings({"provider": "Ollama"})
		cfg = api_get_ai_config()
		self.assertEqual(cfg["provider"], "Ollama")
		self.assertEqual(cfg["ollama_model"], "qwen2.5")
		self.assertEqual(cfg["openai_model"], "gpt-4o")
		self.assertEqual(cfg["claude_model"], "claude-sonnet-4-6")
		self.assertTrue(cfg["has_openai_key"])
		self.assertTrue(cfg["has_claude_key"])
		self.assertEqual(get_claude_api_key(), "sk-ant-api03-test-claude-secret-key-987654321")
		self.assertEqual(get_openai_api_key(), "sk-test-openai-secret-key-1234567890")

		# 5. Switch back to Claude without re-entering key -> key persists
		api_save_ai_settings({"provider": "Claude", "claude_model": "claude-haiku-4-5"})
		cfg = api_get_ai_config()
		self.assertEqual(cfg["provider"], "Claude")
		self.assertEqual(cfg["claude_model"], "claude-haiku-4-5")
		self.assertTrue(cfg["has_claude_key"])

	def test_02_test_claude_connection_success_and_error_cases(self):
		"""Test Cases 3 & 10: Verify Test Claude Connection handles success, missing key, 401, 400 credits, 404 model, 429 rate limit, and network failures."""
		# Missing key
		res_missing = test_ai_connection(provider="Claude", api_key="", model="claude-sonnet-4-6")
		self.assertFalse(res_missing["success"])
		self.assertEqual(res_missing["provider"], "Claude")
		self.assertEqual(res_missing["error_type"], "missing_api_key")

		# Success (200 OK + /v1/models)
		with patch("lms.lms.ai.ai_service.requests.post") as mock_post, patch(
			"lms.lms.ai.ai_service.requests.get"
		) as mock_get:
			mock_post.return_value = _claude_messages_response({"ok": True}, model="claude-sonnet-4-6")
			mock_get.return_value = _mock_http_response(
				200,
				{"data": [{"id": "claude-sonnet-4-6"}, {"id": "claude-haiku-4-5"}]},
			)

			res_ok = api_test_ai_connection(
				provider="Claude",
				base_url="https://api.anthropic.com",
				model="claude-sonnet-4-6",
				api_key="sk-ant-api03-valid-key-test",
			)
			self.assertTrue(res_ok["success"])
			self.assertEqual(res_ok["provider"], "Claude")
			self.assertEqual(res_ok["active_model"], "claude-sonnet-4-6")
			self.assertIn("claude-haiku-4-5", res_ok["models"])

			# Verify Anthropic required headers & endpoint
			call_args = mock_post.call_args
			self.assertEqual(call_args[0][0], "https://api.anthropic.com/v1/messages")
			sent_headers = call_args[1]["headers"]
			self.assertEqual(sent_headers["x-api-key"], "sk-ant-api03-valid-key-test")
			self.assertEqual(sent_headers["anthropic-version"], ANTHROPIC_API_VERSION)
			self.assertEqual(sent_headers["content-type"], "application/json")

		# Invalid API key (401)
		with patch("lms.lms.ai.ai_service.requests.post") as mock_post:
			mock_post.return_value = _mock_http_response(
				401,
				{"type": "error", "error": {"type": "authentication_error", "message": "invalid x-api-key"}},
			)
			res_401 = test_ai_connection(provider="Claude", api_key="sk-ant-bad-key", model="claude-sonnet-4-6")
			self.assertFalse(res_401["success"])
			self.assertEqual(res_401["error_type"], "invalid_api_key")
			self.assertIn("invalid claude api key", res_401["message"].lower())
			self.assertNotIn("sk-ant-bad-key", res_401["message"])

		# Insufficient credits (400)
		with patch("lms.lms.ai.ai_service.requests.post") as mock_post:
			mock_post.return_value = _mock_http_response(
				400,
				{
					"type": "error",
					"error": {
						"type": "invalid_request_error",
						"message": "Your credit balance is too low to access the Anthropic API.",
					},
				},
			)
			res_credits = test_ai_connection(provider="Claude", api_key="sk-ant-test-key", model="claude-sonnet-4-6")
			self.assertFalse(res_credits["success"])
			self.assertEqual(res_credits["error_type"], "insufficient_credits")
			self.assertIn("credit", res_credits["message"].lower())

		# Unavailable model (404)
		with patch("lms.lms.ai.ai_service.requests.post") as mock_post:
			mock_post.return_value = _mock_http_response(
				404,
				{"type": "error", "error": {"type": "not_found_error", "message": "model: claude-nonexistent"}},
			)
			res_404 = test_ai_connection(provider="Claude", api_key="sk-ant-test-key", model="claude-nonexistent")
			self.assertFalse(res_404["success"])
			self.assertEqual(res_404["error_type"], "model_unavailable")

		# Rate limit (429)
		with patch("lms.lms.ai.ai_service.requests.post") as mock_post:
			mock_post.return_value = _mock_http_response(
				429,
				{"type": "error", "error": {"type": "rate_limit_error", "message": "Number of requests exceeded"}},
			)
			res_429 = test_ai_connection(provider="Claude", api_key="sk-ant-test-key", model="claude-sonnet-4-6")
			self.assertFalse(res_429["success"])
			self.assertEqual(res_429["error_type"], "rate_limit")

		# Network error
		with patch("lms.lms.ai.ai_service.requests.post", side_effect=requests.exceptions.ConnectionError("DNS failure")):
			res_net = test_ai_connection(provider="Claude", api_key="sk-ant-test-key", model="claude-sonnet-4-6")
			self.assertFalse(res_net["success"])
			self.assertEqual(res_net["error_type"], "network_error")

	def test_03_generate_quiz_across_all_three_providers(self):
		"""Test Cases 1, 2, 3 & 11: Generate quizzes with Ollama, OpenAI, and Claude independently."""
		sample_quiz_payload = {
			"title": "OS Processes Quiz",
			"questions": [
				{
					"question": "What do threads within the same process share?",
					"type": "Choices",
					"question_type_label": "MCQ",
					"options": [
						"Virtual address space",
						"Separate kernels",
						"Physical MAC addresses",
						"Independent BIOS tables",
					],
					"correct_answer": "Virtual address space",
					"explanation": "Threads share the parent process's address space while keeping independent stacks.",
					"marks": 1,
					"difficulty": "Medium",
				}
			],
			"total_marks": 1,
		}

		# 1. Ollama
		api_save_ai_settings({"provider": "Ollama", "ollama_model": "llama3.2"})
		with patch("lms.lms.ai.ai_service.requests.post") as mock_post:
			mock_post.return_value = _mock_http_response(
				200,
				{"message": {"content": json.dumps(sample_quiz_payload)}, "prompt_eval_count": 50, "eval_count": 80},
			)
			q_ollama = generate_quiz(chapter=self.test_chapter, num_questions=1, total_marks=1)
			self.assertEqual(len(q_ollama["questions"]), 1)
			self.assertEqual(q_ollama["usage"]["provider"], "Ollama")
			self.assertIn("/api/chat", mock_post.call_args[0][0])

		# 2. OpenAI
		api_save_ai_settings({
			"provider": "OpenAI",
			"openai_model": "gpt-4o-mini",
			"openai_api_key": "sk-test-openai-quiz-key-0001",
		})
		fake_choice = MagicMock()
		fake_choice.message.content = json.dumps(sample_quiz_payload)
		fake_completion = MagicMock()
		fake_completion.choices = [fake_choice]
		fake_completion.usage = MagicMock(prompt_tokens=60, completion_tokens=90, total_tokens=150)

		with patch("openai.OpenAI") as mock_openai_cls:
			mock_openai_cls.return_value.chat.completions.create.return_value = fake_completion
			q_openai = generate_quiz(chapter=self.test_chapter, num_questions=1, total_marks=1)
			self.assertEqual(len(q_openai["questions"]), 1)
			self.assertEqual(q_openai["usage"]["provider"], "OpenAI")
			self.assertEqual(q_openai["usage"]["model"], "gpt-4o-mini")

		# 3. Claude AI (Anthropic)
		api_save_ai_settings({
			"provider": "Claude",
			"claude_base_url": "https://api.anthropic.com",
			"claude_model": "claude-sonnet-4-6",
			"claude_max_tokens": 2048,
			"claude_temperature": 0.5,
			"claude_api_key": "sk-ant-api03-claude-quiz-key-0001",
		})
		with patch("lms.lms.ai.ai_service.requests.post") as mock_post:
			mock_post.return_value = _claude_messages_response(sample_quiz_payload, model="claude-sonnet-4-6")
			q_claude = generate_quiz(chapter=self.test_chapter, num_questions=1, total_marks=1)
			self.assertEqual(len(q_claude["questions"]), 1)
			self.assertEqual(q_claude["usage"]["provider"], "Claude")
			self.assertEqual(q_claude["usage"]["model"], "claude-sonnet-4-6")
			self.assertGreater(q_claude["usage"]["estimated_cost"], 0)
			# Ensure Claude settings were actually transmitted
			sent_json = mock_post.call_args[1]["json"]
			self.assertEqual(sent_json["model"], "claude-sonnet-4-6")
			self.assertEqual(sent_json["max_tokens"], 2048)
			self.assertAlmostEqual(sent_json["temperature"], 0.5, places=2)

	def test_04_claude_question_paper_generation(self):
		"""Test Case 4: Generate a model question paper using Claude."""
		api_save_ai_settings({
			"provider": "Claude",
			"claude_model": "claude-sonnet-4-6",
			"claude_api_key": "sk-ant-api03-claude-paper-key",
		})
		paper_payload = {
			"sections": [
				{
					"section_name": "Section A",
					"title": "Multiple Choice Questions",
					"question_type": "MCQ",
					"marks_per_question": 1,
					"questions_count": 2,
					"total_marks": 2,
					"instructions": "Attempt all questions.",
					"questions": [
						{
							"question_number": 1,
							"question": "Which scheduling algorithm assigns fixed time quanta?",
							"marks": 1,
							"difficulty": "Easy",
							"options": ["Round Robin", "FIFO", "LIFO", "None"],
							"correct_answer": "Round Robin",
							"solution": "Round Robin uses fixed time slices.",
						},
						{
							"question_number": 2,
							"question": "What does a process own independently?",
							"marks": 1,
							"difficulty": "Easy",
							"options": ["Virtual address space", "Shared stack", "Global clock", "ROM"],
							"correct_answer": "Virtual address space",
							"solution": "Each process has its own isolated virtual address space.",
						},
					],
				}
			]
		}
		with patch("lms.lms.ai.ai_service.requests.post") as mock_post:
			mock_post.return_value = _claude_messages_response(paper_payload)
			paper = generate_question_paper(
				academic_year="2026-27",
				class_level="Class 12",
				subject="Operating Systems",
				selected_chapters=[self.test_chapter],
				total_marks=2,
				sections_config=[
					{
						"section_name": "Section A",
						"title": "MCQ",
						"question_type": "MCQ",
						"marks_per_question": 1,
						"questions_count": 2,
					}
				],
			)
			self.assertTrue(paper["validation"]["is_valid"])
			self.assertEqual(paper["validation"]["calculated_total_marks"], 2)
			self.assertEqual(paper["_usage"]["provider"], "Claude")

	def test_05_claude_previous_year_analysis_and_question_bank(self):
		"""Test Cases 5 & 6: Generate questions from previous-year analysis and store in AI Question Bank via Claude."""
		api_save_ai_settings({
			"provider": "Claude",
			"claude_model": "claude-haiku-4-5",
			"claude_api_key": "sk-ant-api03-claude-pyq-key",
		})

		historical_payload = {
			"questions": [
				{
					"question": "Differentiate between processes and threads with respect to memory isolation.",
					"type": "Short Answer",
					"options": [],
					"correct_answer": "Processes have isolated virtual address spaces while threads share process memory.",
					"answer_key_detail": "2 marks for process isolation, 3 marks for thread shared memory & stacks.",
					"solution": "A process runs in its own protected address space, whereas threads share heap and code segments.",
					"explanation": "Core OS concurrency distinction.",
					"marks": 5,
					"difficulty": "Medium",
					"chapter": "Claude Test Chapter OS",
					"topic": "Processes and Threads",
					"historical_reference": "Frequently asked in annual OS exams.",
				}
			]
		}

		fake_analysis = {
			"analysis_name": "TEST-ANALYSIS-001",
			"academic_years": "2023-2025",
			"topic_importance": [{"topic": "Processes and Threads", "frequency": 8, "weightage": 40.0}],
			"repeated_questions": [],
		}

		with patch("lms.lms.ai.ai_service.requests.post") as mock_post, patch(
			"lms.lms.ai.historical_question_generator.get_latest_analysis_data",
			return_value=fake_analysis,
		):
			mock_post.return_value = _claude_messages_response(historical_payload, model="claude-haiku-4-5")
			gen_res = generate_historical_ai_questions(
				course=self.test_course,
				subject="Operating Systems",
				number_of_questions=1,
				marks_per_question=5,
			)
			self.assertEqual(len(gen_res["questions"]), 1)
			self.assertIn("processes and threads", gen_res["questions"][0]["question"].lower())

			# Save generated question to AI Question Bank and search
			bank_saved = create_or_update_bank_question({
				"question": gen_res["questions"][0]["question"],
				"type": "Open Ended",
				"difficulty": "Medium",
				"marks": 5,
				"course": self.test_course,
				"explanation": gen_res["questions"][0]["explanation"],
			})
			self.assertTrue(frappe.db.exists("LMS Question", bank_saved["name"]))
			found = search_question_bank(course=self.test_course, search_query="memory isolation")
			self.assertGreaterEqual(found["total_count"], 1)

	def test_06_claude_student_learning_and_practice(self):
		"""Test Case 7: Test AI Learning & Practice (AI Tutor Explanation + Similar Practice Question) using Claude."""
		api_save_ai_settings({
			"provider": "Claude",
			"claude_model": "claude-sonnet-4-6",
			"claude_api_key": "sk-ant-api03-claude-practice-key",
		})

		# Create an approved question for practice
		q_saved = create_or_update_bank_question({
			"question": "Which OS structure stores thread execution state?",
			"type": "Choices",
			"difficulty": "Easy",
			"marks": 1,
			"options": ["Thread Control Block (TCB)", "File Allocation Table", "BIOS", "ARP Cache"],
			"correct_answer": "Thread Control Block (TCB)",
			"course": self.test_course,
			"explanation": "TCB holds thread registers, program counter, and stack pointer.",
			"approval_status": "Approved",
		})
		q_name = q_saved["name"]
		frappe.db.set_value("LMS Question", q_name, "approval_status", "Approved")
		frappe.db.commit()

		frappe.set_user(self.student_email)

		# 1. AI Tutor Explanation via Claude
		with patch("lms.lms.ai.ai_service.requests.post") as mock_post:
			mock_post.return_value = _claude_messages_response(
				{"explanation": "A Thread Control Block (TCB) tracks each thread's registers and stack pointer."}
			)
			help_res = api_ask_ai_question_help(question_id=q_name, course=self.test_course)
			self.assertEqual(help_res["status"], "success")
			self.assertIn("Thread Control Block", help_res["ai_explanation"])

		# 2. Generate Similar Practice Question via Claude
		with patch("lms.lms.ai.ai_service.requests.post") as mock_post:
			mock_post.return_value = _claude_messages_response(
				{
					"question": "What structure maintains per-process scheduling and memory descriptors?",
					"options": ["Process Control Block (PCB)", "DNS Cache", "MBR", "GPU Buffer"],
					"correct_answer": "Process Control Block (PCB)",
					"explanation": "The PCB stores process metadata including state and memory tables.",
				}
			)
			sim_res = api_generate_similar_practice_question(question_id=q_name, course=self.test_course)
			self.assertEqual(sim_res["status"], "success")
			self.assertEqual(sim_res["similar_question"]["correct_answer"], "Process Control Block (PCB)")
			self.assertEqual(sim_res["similar_question"]["_usage"]["provider"], "Claude")

	def test_07_claude_invalid_key_raises_error_and_redacts_secret_in_logs(self):
		"""Test Case 10 & Security: Invalid Claude API key fails loudly and never exposes credentials in logs."""
		bad_secret = "sk-ant-api03-super-secret-invalid-key-99999"
		api_save_ai_settings({
			"provider": "Claude",
			"claude_model": "claude-sonnet-4-6",
			"claude_api_key": bad_secret,
		})

		with patch("lms.lms.ai.ai_service.requests.post") as mock_post:
			mock_post.return_value = _mock_http_response(
				401,
				{"type": "error", "error": {"type": "authentication_error", "message": f"invalid key {bad_secret}"}},
			)
			with self.assertRaises(frappe.ValidationError) as ctx:
				call_ai_service("System", "User prompt", generation_type="Quiz")
			self.assertIn("invalid claude api key", str(ctx.exception).lower())
			self.assertNotIn(bad_secret, str(ctx.exception))

		# Verify AI Generation History does not leak the API key
		history = api_get_generation_history(limit=10)
		history_blob = json.dumps(history, default=str)
		self.assertNotIn(bad_secret, history_blob)

	def test_08_permissions_for_student_and_teacher(self):
		"""Test Case 12: Verify neither students nor teachers can access or modify AI Provider Settings."""
		# Student cannot read, test, or save settings
		frappe.set_user(self.student_email)
		with self.assertRaises(frappe.PermissionError):
			api_get_ai_config()
		with self.assertRaises(frappe.PermissionError):
			api_test_ai_connection(provider="Claude")
		with self.assertRaises(frappe.PermissionError):
			api_save_ai_settings({"provider": "Claude"})

		# Teacher (non-System Manager) cannot read, test, or save AI Provider Settings
		frappe.set_user(self.teacher_email)
		with self.assertRaises(frappe.PermissionError):
			api_get_ai_config()
		with self.assertRaises(frappe.PermissionError):
			api_test_ai_connection(provider="Claude")
		with self.assertRaises(frappe.PermissionError):
			api_save_ai_settings({"provider": "Claude"})

		# System Manager / Administrator CAN access
		frappe.set_user("Administrator")
		cfg = api_get_ai_config()
		self.assertIn("provider", cfg)
		self.assertNotIn("claude_api_key", cfg)
		self.assertNotIn("openai_api_key", cfg)

	def test_09_claude_cost_calculation(self):
		"""Verify token cost calculation for Claude Sonnet, Haiku, and Opus models."""
		self.assertGreater(calculate_cost("claude-sonnet-4-6", 1000, 1000), 0)
		self.assertGreater(calculate_cost("claude-haiku-4-5-20251001", 1000, 1000), 0)
		self.assertGreater(calculate_cost("claude-opus-4-6", 1000, 1000), calculate_cost("claude-haiku-4-5", 1000, 1000))
		self.assertEqual(calculate_cost("ollama:llama3.2", 1000, 1000), 0.0)
