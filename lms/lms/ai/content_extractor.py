# Copyright (c) 2026, Izensphere and contributors
# For license information, please see license.txt

import json
import os
import re
from typing import Any
import frappe
from frappe import _
from frappe.utils import get_files_path


def parse_editorjs_json(content: str | dict | None) -> str:
	"""Convert Editor.js JSON data structure into clean, human-readable educational Markdown."""
	if not content:
		return ""

	if isinstance(content, str):
		try:
			data = json.loads(content)
		except Exception:
			# If it's already plain text or markdown, return as is
			return content.strip()
	else:
		data = content

	if not isinstance(data, dict) or "blocks" not in data:
		return ""

	lines = []
	for block in data.get("blocks", []):
		btype = block.get("type", "")
		bdata = block.get("data", {})

		if btype == "header":
			level = bdata.get("level", 2)
			text = clean_html(bdata.get("text", ""))
			lines.append(f"{'#' * level} {text}\n")

		elif btype == "paragraph":
			text = clean_html(bdata.get("text", ""))
			if text:
				lines.append(f"{text}\n")

		elif btype == "list":
			style = bdata.get("style", "unordered")
			items = bdata.get("items", [])
			for i, item in enumerate(items, 1):
				if isinstance(item, dict):
					content_text = clean_html(item.get("content", ""))
				else:
					content_text = clean_html(str(item))
				prefix = f"{i}." if style == "ordered" else "-"
				lines.append(f"{prefix} {content_text}")
			lines.append("")

		elif btype in ("codeBox", "code"):
			code = bdata.get("code", "")
			lang = bdata.get("language", "")
			lines.append(f"```{lang}\n{code}\n```\n")

		elif btype == "quote":
			text = clean_html(bdata.get("text", ""))
			caption = clean_html(bdata.get("caption", ""))
			lines.append(f"> {text}")
			if caption:
				lines.append(f"> — *{caption}*")
			lines.append("")

		elif btype == "table":
			content_matrix = bdata.get("content", [])
			for row in content_matrix:
				clean_cells = [clean_html(cell) for cell in row]
				lines.append("| " + " | ".join(clean_cells) + " |")
			lines.append("")

		elif btype == "checklist":
			for item in bdata.get("items", []):
				checked = "x" if item.get("checked") else " "
				lines.append(f"- [{checked}] {clean_html(item.get('text', ''))}")
			lines.append("")

	return "\n".join(lines).strip()


def clean_html(raw_html: str) -> str:
	"""Strip HTML tags while preserving text content."""
	if not raw_html:
		return ""
	# Replace common break/paragraph tags with newlines
	clean = re.sub(r"<(br|p|div)[^>]*>", "\n", raw_html, flags=re.IGNORECASE)
	clean = re.sub(r"<[^>]+>", "", clean)
	# Decode common entities
	clean = clean.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')
	return clean.strip()


def extract_pdf_text_from_file_doc(file_name_or_url: str) -> str:
	"""Extract plain text from an attached PDF document using pypdf."""
	if not file_name_or_url:
		return ""

	try:
		import pypdf

		# Resolve local disk path
		file_path = None
		if file_name_or_url.startswith("/files/"):
			site_path = frappe.get_site_path()
			file_path = os.path.join(site_path, "public", file_name_or_url.lstrip("/"))
		elif file_name_or_url.startswith("/private/files/"):
			site_path = frappe.get_site_path()
			file_path = os.path.join(site_path, file_name_or_url.lstrip("/"))
		elif frappe.db.exists("File", file_name_or_url):
			fdoc = frappe.get_doc("File", file_name_or_url)
			file_path = fdoc.get_full_path()

		if not file_path or not os.path.exists(file_path):
			return ""

		reader = pypdf.PdfReader(file_path)
		extracted_pages = []
		# Cap at 50 pages to prevent memory exhaustion
		max_pages = min(50, len(reader.pages))
		for p_idx in range(max_pages):
			page_text = reader.pages[p_idx].extract_text()
			if page_text:
				extracted_pages.append(page_text.strip())

		return "\n\n".join(extracted_pages)
	except Exception as e:
		frappe.logger("ai_assessment").warning(f"Could not extract text from PDF {file_name_or_url}: {e}")
		return ""


def extract_lesson_content(lesson_name: str) -> dict:
	"""Extract rich educational material from a single Course Lesson."""
	if not frappe.db.exists("Course Lesson", lesson_name):
		return {"title": lesson_name, "content": "", "insufficient": True}

	lesson = frappe.get_doc("Course Lesson", lesson_name)
	text_sections = []

	text_sections.append(f"# Lesson: {lesson.title}")

	# 1. Editor.js Content
	if lesson.content:
		parsed = parse_editorjs_json(lesson.content)
		if parsed:
			text_sections.append("## Content\n" + parsed)

	# 2. Markdown Body
	if lesson.body:
		text_sections.append("## Notes & Outline\n" + lesson.body.strip())

	# 3. Instructor notes / instructor content
	if lesson.instructor_notes:
		text_sections.append("## Instructor Notes\n" + lesson.instructor_notes.strip())
	if lesson.instructor_content:
		text_sections.append("## Additional Guidelines\n" + parse_editorjs_json(lesson.instructor_content))

	# 4. Check for attached PDFs
	files = frappe.get_all(
		"File",
		filters={"attached_to_doctype": "Course Lesson", "attached_to_name": lesson.name},
		fields=["name", "file_url", "file_name"],
	)
	for f in files:
		if f.file_name and f.file_name.lower().endswith(".pdf"):
			pdf_text = extract_pdf_text_from_file_doc(f.file_url or f.name)
			if pdf_text:
				text_sections.append(f"## Attached Material: {f.file_name}\n" + pdf_text[:15000])

	# 5. Lesson Notes (lms_lesson_note)
	if frappe.db.table_exists("LMS Lesson Note"):
		notes = frappe.get_all(
			"LMS Lesson Note",
			filters={"lesson": lesson.name},
			fields=["note", "highlighted_text"],
			order_by="creation desc",
			limit_page_length=5,
		)
		for n in notes:
			if n.note:
				text_sections.append("## Study Note\n" + clean_html(n.note))
			if n.highlighted_text:
				text_sections.append("## Highlighted Excerpt\n" + n.highlighted_text.strip())

	full_text = "\n\n".join(text_sections).strip()

	# If the lesson alone has sparse content (< 150 chars), supplement with Chapter and Course curriculum context
	if len(full_text) < 150 and (lesson.chapter or lesson.course):
		context_sections = []
		if lesson.chapter and frappe.db.exists("Course Chapter", lesson.chapter):
			ch_doc = frappe.get_doc("Course Chapter", lesson.chapter)
			context_sections.append(f"## Chapter Context: {ch_doc.title}")
			siblings = frappe.get_all(
				"Course Lesson",
				filters={"chapter": ch_doc.name, "name": ["!=", lesson.name]},
				fields=["title"],
				limit=5,
			)
			if siblings:
				context_sections.append("## Chapter Key Topics:\n" + "\n".join(f"- {s.title.strip()}" for s in siblings if s.title))

		if lesson.course and frappe.db.exists("LMS Course", lesson.course):
			course_doc = frappe.get_doc("LMS Course", lesson.course)
			if course_doc.short_introduction:
				context_sections.append(f"## Course Background\n{course_doc.short_introduction.strip()}")
			if course_doc.description:
				clean_desc = clean_html(course_doc.description)
				context_sections.append(f"## Curriculum Scope\n{clean_desc[:1200].strip()}")

		if context_sections:
			full_text = full_text + "\n\n" + "\n\n".join(context_sections)

	stats = get_content_stats(full_text)

	return {
		"name": lesson.name,
		"title": lesson.title,
		"course": lesson.course,
		"chapter": lesson.chapter,
		"content": full_text,
		"stats": stats,
		"insufficient": stats["is_insufficient"],
		"warning": stats["warning"],
	}


def extract_chapter_content(chapter_name: str) -> dict:
	"""Extract all lesson content, notes, and attached materials for an entire chapter."""
	if not frappe.db.exists("Course Chapter", chapter_name):
		return {"title": chapter_name, "content": "", "insufficient": True}

	chapter = frappe.get_doc("Course Chapter", chapter_name)
	text_sections = [f"# Chapter: {chapter.title}"]

	# Get all lessons in this chapter
	lessons = frappe.get_all(
		"Course Lesson",
		filters={"chapter": chapter.name},
		fields=["name", "title"],
		order_by="idx asc, creation asc",
	)

	lesson_results = []
	for l in lessons:
		l_res = extract_lesson_content(l.name)
		lesson_results.append(l_res)
		if l_res["content"]:
			text_sections.append(l_res["content"])

	# Check for attached files directly on Course Chapter
	chapter_files = frappe.get_all(
		"File",
		filters={"attached_to_doctype": "Course Chapter", "attached_to_name": chapter.name},
		fields=["name", "file_url", "file_name"],
	)
	for f in chapter_files:
		if f.file_name and f.file_name.lower().endswith(".pdf"):
			pdf_text = extract_pdf_text_from_file_doc(f.file_url or f.name)
			if pdf_text:
				text_sections.append(f"## Chapter PDF Document: {f.file_name}\n" + pdf_text[:20000])

	full_text = "\n\n".join(text_sections).strip()

	# If the chapter alone has sparse content (< 150 chars), supplement with Course curriculum context
	if len(full_text) < 150 and chapter.course and frappe.db.exists("LMS Course", chapter.course):
		course_doc = frappe.get_doc("LMS Course", chapter.course)
		context_sections = []
		if course_doc.short_introduction:
			context_sections.append(f"## Course Background\n{course_doc.short_introduction.strip()}")
		if course_doc.description:
			clean_desc = clean_html(course_doc.description)
			context_sections.append(f"## Curriculum Scope\n{clean_desc[:1200].strip()}")
		if context_sections:
			full_text = full_text + "\n\n" + "\n\n".join(context_sections)

	stats = get_content_stats(full_text)

	return {
		"name": chapter.name,
		"title": chapter.title,
		"course": chapter.course,
		"lessons": lesson_results,
		"content": full_text,
		"stats": stats,
		"insufficient": stats["is_insufficient"],
		"warning": stats["warning"],
	}


def extract_course_content(course_name: str, selected_chapters: list[str] | None = None) -> dict:
	"""Extract course overview and content for specified chapters."""
	if not frappe.db.exists("LMS Course", course_name):
		return {"title": course_name, "content": "", "insufficient": True}

	course = frappe.get_doc("LMS Course", course_name)
	sections = [f"# Course: {course.title}"]

	if course.short_introduction:
		sections.append(f"## Course Overview\n{course.short_introduction}")
	if course.description:
		sections.append(f"## Course Description\n{clean_html(course.description)}")

	# Get chapters
	chapter_filters = {"course": course.name}
	if selected_chapters:
		chapter_filters["name"] = ["in", selected_chapters]

	chapters = frappe.get_all(
		"Course Chapter",
		filters=chapter_filters,
		fields=["name", "title"],
		order_by="idx asc, creation asc",
	)

	chapter_data = []
	for ch in chapters:
		ch_res = extract_chapter_content(ch.name)
		chapter_data.append(ch_res)
		if ch_res["content"]:
			sections.append(ch_res["content"])

	full_text = "\n\n".join(sections).strip()
	stats = get_content_stats(full_text)

	return {
		"name": course.name,
		"title": course.title,
		"chapters": chapter_data,
		"content": full_text,
		"stats": stats,
		"insufficient": stats["is_insufficient"],
		"warning": stats["warning"],
	}


def extract_batch_content(
	batch_name: str,
	course_name: str | None = None,
	selected_chapters: list[str] | None = None,
) -> dict:
	"""Extract rich educational material combining Batch details, schedule, live classes,
	and linked Course chapters and lessons.
	"""
	if not frappe.db.exists("LMS Batch", batch_name):
		return {"title": batch_name, "content": "", "insufficient": True}

	batch = frappe.get_doc("LMS Batch", batch_name)
	sections = [f"# Batch: {batch.title}"]

	# 1. Batch metadata & schedule
	meta_parts = []
	if batch.category:
		meta_parts.append(f"**Category:** {batch.category}")
	if batch.medium:
		meta_parts.append(f"**Medium:** {batch.medium}")
	if batch.start_date:
		date_str = f"{batch.start_date}"
		if batch.end_date:
			date_str += f" to {batch.end_date}"
		if batch.start_time:
			date_str += f" ({batch.start_time}"
			if batch.end_time:
				date_str += f" - {batch.end_time}"
			if batch.timezone:
				date_str += f" {batch.timezone}"
			date_str += ")"
		meta_parts.append(f"**Batch Schedule:** {date_str}")

	if meta_parts:
		sections.append("## Batch Information\n" + "\n".join(meta_parts))

	# 2. Batch Description & Detailed Curriculum / Syllabus
	if batch.description:
		sections.append(f"## Batch Overview\n{clean_html(batch.description)}")

	if batch.batch_details:
		parsed_details = parse_editorjs_json(batch.batch_details)
		if not parsed_details:
			parsed_details = clean_html(batch.batch_details)
		if parsed_details:
			sections.append(f"## Batch Syllabus & Topics Covered\n{parsed_details}")
	elif batch.batch_details_raw:
		sections.append(f"## Batch Topics\n{clean_html(batch.batch_details_raw)}")

	# 3. Batch Live Classes & Interactive Sessions
	live_classes = frappe.get_all(
		"LMS Live Class",
		filters={"batch_name": batch.name},
		fields=["title", "description", "date", "time"],
		order_by="date asc, time asc",
	)
	if live_classes:
		lc_sections = ["## Batch Live Classes & Interactive Sessions"]
		for lc in live_classes:
			lc_title = lc.get("title", "")
			lc_desc = clean_html(lc.get("description", ""))
			lc_line = f"- **{lc_title}**"
			if lc.get("date"):
				lc_line += f" ({lc.get('date')})"
			if lc_desc:
				lc_line += f": {lc_desc}"
			lc_sections.append(lc_line)
		sections.append("\n".join(lc_sections))

	# 4. Batch Timetable
	if hasattr(batch, "timetable") and batch.timetable:
		tt_lines = []
		for t in batch.timetable:
			if t.reference_docname or t.milestone:
				tt_lines.append(f"- Day {t.day}: {t.reference_docname or 'Milestone Session'} ({t.duration or '1 hr'})")
		if tt_lines:
			sections.append("## Batch Timetable & Progression\n" + "\n".join(tt_lines))

	# 5. Extract Linked Course Content
	batch_courses = []
	if hasattr(batch, "courses") and batch.courses:
		batch_courses = [c.course for c in batch.courses if c.course]

	target_courses = []
	if course_name:
		target_courses = [course_name]
	elif batch_courses:
		target_courses = batch_courses

	course_data = []
	for c_name in target_courses:
		if frappe.db.exists("LMS Course", c_name):
			c_res = extract_course_content(c_name, selected_chapters=selected_chapters)
			course_data.append(c_res)
			if c_res.get("content"):
				sections.append(f"## Course Curriculum: {c_res.get('title', c_name)}\n" + c_res["content"])

	full_text = "\n\n".join(sections).strip()
	stats = get_content_stats(full_text)

	return {
		"name": batch.name,
		"title": batch.title,
		"category": batch.category,
		"description": batch.description,
		"batch_courses": batch_courses,
		"courses": course_data,
		"live_classes_count": len(live_classes),
		"content": full_text,
		"stats": stats,
		"insufficient": stats["is_insufficient"],
		"warning": stats["warning"],
	}


def get_content_stats(text: str) -> dict:
	"""Computes text metrics and verifies if content meets minimum threshold (> 100 characters)."""
	char_count = len(text)
	words = text.split()
	word_count = len(words)
	estimated_tokens = int(char_count / 3.5) if char_count > 0 else 0

	is_insufficient = char_count < 100 or word_count < 20
	warning = (
		"Warning: Educational content is insufficient (< 100 characters). Please enrich the lesson content or select 'Extended Knowledge' mode."
		if is_insufficient
		else None
	)

	return {
		"char_count": char_count,
		"word_count": word_count,
		"estimated_tokens": estimated_tokens,
		"is_insufficient": is_insufficient,
		"warning": warning,
	}


def chunk_content(text: str, max_chunk_tokens: int = 3500, overlap_tokens: int = 200) -> list[str]:
	"""Splits long educational texts by header or paragraph boundaries to fit LLM context limits."""
	paragraphs = text.split("\n\n")
	chunks = []
	current_chunk = []
	current_length = 0

	for para in paragraphs:
		para_tokens = int(len(para) / 3.5)
		if current_length + para_tokens > max_chunk_tokens and current_chunk:
			chunks.append("\n\n".join(current_chunk))
			# Keep last paragraph for overlap
			if overlap_tokens > 0 and len(current_chunk) > 1:
				current_chunk = [current_chunk[-1], para]
				current_length = int(len(current_chunk[0]) / 3.5) + para_tokens
			else:
				current_chunk = [para]
				current_length = para_tokens
		else:
			current_chunk.append(para)
			current_length += para_tokens

	if current_chunk:
		chunks.append("\n\n".join(current_chunk))

	return chunks or [text]
