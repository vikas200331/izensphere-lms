# Copyright (c) 2026, Izensphere and contributors
# For license information, please see license.txt

import hashlib
import json
import os
import re
import xml.etree.ElementTree as ET
import zipfile
import frappe
from frappe import _
from frappe.utils import cint, now_datetime

try:
	import pypdf
except ImportError:
	pypdf = None

try:
	import pdfplumber
except ImportError:
	pdfplumber = None

try:
	from PIL import Image
except ImportError:
	Image = None


def get_file_absolute_path(file_url: str) -> str:
	"""Resolve Frappe file URL to absolute filesystem path."""
	if not file_url:
		return ""
	if file_url.startswith("/private/files/") or file_url.startswith("/files/"):
		file_doc = frappe.db.get_value(
			"File",
			{"file_url": file_url},
			["name", "file_name", "is_private"],
			as_dict=True,
		)
		if file_doc:
			site_path = frappe.get_site_path()
			folder = "private/files" if file_doc.is_private else "public/files"
			full_path = os.path.join(site_path, folder, file_doc.file_name)
			if os.path.exists(full_path):
				return full_path

	# Fallback resolution
	clean_url = file_url.lstrip("/")
	site_path = frappe.get_site_path()
	candidate = os.path.join(site_path, clean_url)
	if os.path.exists(candidate):
		return candidate

	# Check public files directly
	candidate_public = os.path.join(site_path, "public", clean_url)
	if os.path.exists(candidate_public):
		return candidate_public

	return file_url


def calculate_file_checksum(file_path: str) -> str:
	"""Calculate MD5 checksum of a file on disk."""
	if not os.path.exists(file_path):
		return ""
	hasher = hashlib.md5()
	with open(file_path, "rb") as f:
		for chunk in iter(lambda: f.read(65536), b""):
			hasher.update(chunk)
	return hasher.hexdigest()


def extract_text_from_pdf(file_path: str) -> str:
	"""Extract selectable text from PDF using pdfplumber or pypdf."""
	extracted_text = []

	if pdfplumber:
		try:
			with pdfplumber.open(file_path) as pdf:
				for page in pdf.pages:
					txt = page.extract_text()
					if txt:
						extracted_text.append(txt)
		except Exception as e:
			frappe.logger("ai_assessment").warning(f"pdfplumber extraction failed: {e}")

	if not extracted_text and pypdf:
		try:
			reader = pypdf.PdfReader(file_path)
			for page in reader.pages:
				txt = page.extract_text()
				if txt:
					extracted_text.append(txt)
		except Exception as e:
			frappe.logger("ai_assessment").warning(f"pypdf extraction failed: {e}")

	return "\n\n".join(extracted_text).strip()


def extract_text_from_docx(file_path: str) -> str:
	"""Extract text from DOCX natively using zipfile and xml.etree.ElementTree."""
	if not os.path.exists(file_path):
		return ""

	extracted_paragraphs = []
	try:
		with zipfile.ZipFile(file_path) as docx:
			xml_content = docx.read("word/document.xml")
			tree = ET.fromstring(xml_content)

			# Namespaces in docx xml
			ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

			# Iterate over all paragraphs and table rows
			for p in tree.iter(f"{{{ns['w']}}}p"):
				texts = [node.text for node in p.iter(f"{{{ns['w']}}}t") if node.text]
				if texts:
					extracted_paragraphs.append("".join(texts).strip())

			# Also capture table cells if any
			for tbl in tree.iter(f"{{{ns['w']}}}tbl"):
				for row in tbl.iter(f"{{{ns['w']}}}tr"):
					row_texts = []
					for cell in row.iter(f"{{{ns['w']}}}tc"):
						c_texts = [node.text for node in cell.iter(f"{{{ns['w']}}}t") if node.text]
						if c_texts:
							row_texts.append(" ".join(c_texts).strip())
					if row_texts:
						extracted_paragraphs.append(" | ".join(row_texts))

	except Exception as e:
		frappe.logger("ai_assessment").error(f"DOCX extraction failed: {e}")
		return ""

	return "\n\n".join(extracted_paragraphs).strip()


def extract_text_from_image(file_path: str) -> str:
	"""Extract text from image or scanned document using fallback optical recognition or AI vision."""
	if not os.path.exists(file_path):
		return ""

	# Check if pytesseract is available
	try:
		import pytesseract
		img = Image.open(file_path)
		return pytesseract.image_to_string(img).strip()
	except Exception:
		pass

	# Fallback: Call AI multimodal if available or notify clear message
	return ""


def extract_raw_text(file_path: str) -> str:
	"""Route file by extension to appropriate extractor."""
	if not os.path.exists(file_path):
		raise FileNotFoundError(f"File not found: {file_path}")

	ext = os.path.splitext(file_path)[1].lower()
	if ext == ".pdf":
		text = extract_text_from_pdf(file_path)
		if not text:
			# Could be scanned PDF
			text = extract_text_from_image(file_path)
		return text
	elif ext == ".docx":
		return extract_text_from_docx(file_path)
	elif ext in {".png", ".jpg", ".jpeg"}:
		return extract_text_from_image(file_path)
	else:
		raise ValueError(f"Unsupported file format '{ext}'")


def parse_questions_from_text(raw_text: str, paper_meta: dict | None = None) -> list[dict]:
	"""Parse extracted raw text into structured question objects.
	Identifies questions, options, marks, sections, and question types.
	"""
	if not raw_text or not raw_text.strip():
		return []

	meta = paper_meta or {}
	paper_title = meta.get("title", "")
	exam_year = meta.get("examination_year") or meta.get("academic_year", "")
	course = meta.get("course", "")
	subject = meta.get("subject", "")
	paper_name = meta.get("name", "")

	questions = []
	lines = raw_text.splitlines()

	current_section = "General"
	current_q_num = None
	current_q_text = []
	current_marks = 1
	current_options = []
	current_type = "Short Answer"

	# Regular expressions for sections, questions, marks, options
	section_pattern = re.compile(
		r"^(SECTION\s*[-–:]*\s*[A-Z0-9]+|PART\s*[-–:]*\s*[A-Z0-9]+|GROUP\s*[-–:]*\s*[A-Z0-9]+)",
		re.IGNORECASE,
	)
	question_start_pattern = re.compile(
		r"^(?:(?:Q(?:uestion)?\.?\s*(\d+[a-z]?))|(\d{1,3})[\.\)\-]\s+)(.*)$",
		re.IGNORECASE,
	)
	marks_pattern = re.compile(
		r"\[\s*(\d+)\s*(?:marks?|m)?\s*\]|\(\s*(\d+)\s*(?:marks?|m)?\s*\)|=\s*(\d+)\s*marks?",
		re.IGNORECASE,
	)
	option_pattern = re.compile(
		r"^\s*[\(\[]?([a-dA-D1-4])[\)\]\.]\s+(.*)$"
	)

	def flush_question():
		nonlocal current_q_num, current_q_text, current_marks, current_options, current_type
		if not current_q_text:
			return

		full_text = " ".join(current_q_text).strip()
		# Clean extra spaces
		full_text = re.sub(r"\s+", " ", full_text)

		if len(full_text) < 5:
			return

		# Determine question type
		q_type = current_type
		lower = full_text.lower()
		if current_options:
			q_type = "Choices"
		elif "true or false" in lower or "true/false" in lower:
			q_type = "True or False"
		elif "fill in the blank" in lower or "____" in full_text:
			q_type = "Fill in the Blanks"
		elif any(w in lower for w in ["write a program", "code to", "algorithm for", "python program", "java program", "sql query", "function to"]):
			q_type = "Programming"
		elif current_marks >= 8 or any(w in lower for w in ["explain in detail", "discuss", "elaborate", "essay on"]):
			q_type = "Essay"
		elif current_marks >= 5:
			q_type = "Long Answer"
		else:
			q_type = "Short Answer"

		questions.append({
			"question_number": str(current_q_num or len(questions) + 1),
			"section": current_section,
			"question": full_text,
			"options": list(current_options),
			"marks": cint(current_marks) or 1,
			"type": q_type,
			"course": course,
			"subject": subject,
			"examination_year": exam_year,
			"paper_title": paper_title,
			"paper_name": paper_name,
		})

		current_q_text = []
		current_options = []
		current_marks = 1
		current_type = "Short Answer"

	for line in lines:
		trimmed = line.strip()
		if not trimmed:
			continue

		# Check section header
		sec_match = section_pattern.match(trimmed)
		if sec_match:
			flush_question()
			current_section = sec_match.group(1).upper()
			continue

		# Check if new question starts
		q_match = question_start_pattern.match(trimmed)
		if q_match:
			flush_question()
			q_num = q_match.group(1) or q_match.group(2)
			rest_of_line = q_match.group(3) or ""

			current_q_num = q_num
			# Check marks in this line
			m_match = marks_pattern.search(rest_of_line)
			if m_match:
				current_marks = cint(m_match.group(1) or m_match.group(2) or m_match.group(3) or 1)
				rest_of_line = marks_pattern.sub("", rest_of_line).strip()

			current_q_text = [rest_of_line] if rest_of_line else []
			continue

		# Check if line is an MCQ option
		opt_match = option_pattern.match(trimmed)
		if opt_match and current_q_text:
			opt_letter = opt_match.group(1)
			opt_text = opt_match.group(2).strip()
			current_options.append(f"{opt_letter}. {opt_text}")
			continue

		# Check for marks at end of sentence
		m_match = marks_pattern.search(trimmed)
		if m_match and current_q_text:
			current_marks = cint(m_match.group(1) or m_match.group(2) or m_match.group(3) or current_marks)
			trimmed = marks_pattern.sub("", trimmed).strip()

		# Continuation of existing question or instructions
		if current_q_text:
			current_q_text.append(trimmed)
		else:
			# Stray line before first question
			pass

	flush_question()

	# If pattern parsing extracted 0 or very few questions from substantial text,
	# split by paragraph or numbered lines as fallback
	if not questions and len(raw_text.strip()) > 50:
		paragraphs = [p.strip() for p in raw_text.split("\n\n") if len(p.strip()) > 15]
		for idx, para in enumerate(paragraphs, 1):
			# Skip obvious header info
			if any(h in para.lower() for h in ["university", "examination", "time: 3 hours", "max marks", "instructions:"]):
				continue
			questions.append({
				"question_number": str(idx),
				"section": "Section A",
				"question": para,
				"options": [],
				"marks": 2 if len(para) < 100 else 5,
				"type": "Short Answer" if len(para) < 100 else "Long Answer",
				"course": course,
				"subject": subject,
				"examination_year": exam_year,
				"paper_title": paper_title,
				"paper_name": paper_name,
			})

	return questions


def process_question_paper_document(paper_name: str) -> dict:
	"""Process an uploaded Previous Year Question Paper record.
	Extracts raw text, parses questions, computes checksum, and updates document.
	"""
	if not frappe.db.exists("Previous Year Question Papers", paper_name):
		return {"status": "error", "message": f"Question paper {paper_name} not found"}

	doc = frappe.get_doc("Previous Year Question Papers", paper_name)
	doc.ai_processing_status = "Processing"
	doc.error_message = None
	doc.save(ignore_permissions=True)
	frappe.db.commit()

	try:
		if not doc.attachment:
			raise ValueError("No attachment found on document")

		file_path = get_file_absolute_path(doc.attachment)
		if not file_path or not os.path.exists(file_path):
			raise FileNotFoundError(f"Attachment file not found at path: {file_path}")

		# Compute checksum
		doc.file_checksum = calculate_file_checksum(file_path)

		# Extract text
		raw_text = extract_raw_text(file_path)
		if not raw_text or not raw_text.strip():
			raise ValueError("Extracted text is empty. Document might be an unreadable image or password protected.")

		doc.extracted_text = raw_text

		# Parse structured questions
		paper_meta = {
			"name": doc.name,
			"title": doc.title,
			"examination_year": doc.examination_year or doc.academic_year,
			"academic_year": doc.academic_year,
			"course": doc.course,
			"subject": doc.subject,
		}
		questions = parse_questions_from_text(raw_text, paper_meta=paper_meta)

		doc.extracted_questions_json = json.dumps(questions, ensure_ascii=False)
		doc.extracted_questions_count = len(questions)
		doc.ai_processing_status = "Processed"
		doc.error_message = None
		doc.save(ignore_permissions=True)
		frappe.db.commit()

		return {
			"status": "success",
			"name": doc.name,
			"questions_count": len(questions),
			"checksum": doc.file_checksum,
		}

	except Exception as e:
		frappe.db.rollback()
		err_msg = str(e)
		frappe.logger("ai_assessment").error(f"Error processing paper {paper_name}: {err_msg}")
		
		# Update failure status
		doc.reload()
		doc.ai_processing_status = "Failed"
		doc.error_message = err_msg
		doc.save(ignore_permissions=True)
		frappe.db.commit()

		return {"status": "error", "message": err_msg}
