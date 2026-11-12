# Copyright (c) 2026, Izensphere and contributors
# For license information, please see license.txt

import json
import frappe
from frappe import _
from frappe.utils import cint, escape_html, get_url
from frappe.utils.pdf import get_pdf


def get_paper_html(paper_doc_name: str, doc_type: str = "question_paper") -> str:
	"""Renders crisp, professional A4 printable HTML for:
	- "question_paper": Questions, instructions, marks, options (NO answers/solutions).
	- "answer_key": Concise answer key table for fast grading.
	- "detailed_solutions": Full step-by-step solutions, rubrics, and marking scheme.
	"""
	paper = frappe.get_doc("AI Question Paper", paper_doc_name)

	# Security check: Students are strictly barred from viewing answer key or detailed solutions
	user = frappe.session.user
	if user and user != "Guest":
		roles = frappe.get_roles(user)
		if doc_type in ("answer_key", "detailed_solutions"):
			if "LMS Student" in roles and not any(
				r in roles for r in ["System Manager", "Course Creator", "Instructor", "Principal", "Moderator"]
			):
				frappe.throw(
					_("Access Denied: Students are not permitted to download Answer Keys or Solutions."),
					frappe.PermissionError,
				)

	# Parse sections and questions data
	sections = []
	for sec_row in paper.sections:
		q_list = []
		if sec_row.questions_data:
			try:
				q_list = json.loads(sec_row.questions_data)
			except Exception:
				q_list = []
		sections.append(
			{
				"section_name": sec_row.section_name,
				"title": sec_row.title,
				"instructions": sec_row.instructions,
				"question_type": sec_row.question_type,
				"marks_per_question": sec_row.marks_per_question,
				"total_marks": sec_row.total_marks,
				"questions": q_list,
			}
		)

	# School info
	school_name = paper.school_name or "Izensphere International School"
	school_logo = paper.school_logo
	if school_logo and not school_logo.startswith("http"):
		school_logo = get_url(school_logo)

	doc_title_map = {
		"question_paper": "QUESTION PAPER",
		"answer_key": "OFFICIAL ANSWER KEY",
		"detailed_solutions": "DETAILED SOLUTIONS & MARKING SCHEME",
	}
	subtitle = doc_title_map.get(doc_type, "EXAMINATION")

	# Instructions HTML
	instr_lines = [i.strip() for i in (paper.instructions or "").split("\n") if i.strip()]
	instructions_html = "".join([f"<li>{escape_html(line)}</li>" for line in instr_lines])

	# Render sections HTML
	sections_html = ""
	for sec in sections:
		sec_header = f"""
		<div class="section-container">
			<div class="section-header">
				<span class="section-title">{escape_html(sec['section_name'])}: {escape_html(sec['title'] or '')}</span>
				<span class="section-marks">[{sec['total_marks']} Marks]</span>
			</div>
			{f"<div class='section-instructions'>{escape_html(sec['instructions'])}</div>" if sec['instructions'] else ""}
			<div class="questions-list">
		"""

		questions_inner = ""
		for q in sec["questions"]:
			q_num = q.get("question_number", "")
			q_text = escape_html(q.get("question", ""))
			q_marks = q.get("marks", 1)

			options_html = ""
			if q.get("options") and sec["question_type"] in ("MCQ", "Mixed", "True/False"):
				opt_items = "".join(
					[
						f"<div class='option-item'><span class='opt-marker'>{chr(65 + o_idx)}.</span> {escape_html(opt)}</div>"
						for o_idx, opt in enumerate(q["options"])
					]
				)
				options_html = f"<div class='options-grid'>{opt_items}</div>"

			# Internal Choice "OR" question
			or_html = ""
			if q.get("internal_choice_question"):
				or_q = q["internal_choice_question"]
				or_html = f"""
				<div class="or-separator">--- OR ---</div>
				<div class="or-question">
					<div class="q-row">
						<span class="q-text">{escape_html(or_q.get('question', ''))}</span>
					</div>
				</div>
				"""

			# Answer Key / Solution snippets
			answer_snippet = ""
			if doc_type == "answer_key":
				ans = q.get("correct_answer") or q.get("solution") or "N/A"
				answer_snippet = f"""
				<div class="answer-box">
					<strong>Answer:</strong> {escape_html(str(ans))}
				</div>
				"""
			elif doc_type == "detailed_solutions":
				ans = q.get("correct_answer") or ""
				sol = q.get("solution") or q.get("explanation") or "Step-by-step solution not provided."
				answer_snippet = f"""
				<div class="solution-box">
					<div class="sol-ans"><strong>Correct Answer:</strong> {escape_html(str(ans))}</div>
					<div class="sol-steps"><strong>Marking Scheme & Solution:</strong><br>{escape_html(str(sol)).replace(chr(10), '<br>')}</div>
				</div>
				"""

			questions_inner += f"""
			<div class="question-item">
				<div class="q-header">
					<span class="q-num">Q{q_num}.</span>
					<span class="q-text">{q_text}</span>
					<span class="q-marks">({q_marks} Mark{'s' if q_marks > 1 else ''})</span>
				</div>
				{options_html}
				{or_html}
				{answer_snippet}
			</div>
			"""

		sections_html += sec_header + questions_inner + "</div></div>"

	# Build full HTML document with print styling
	html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{escape_html(paper.title)} - {subtitle}</title>
<style>
	@page {{
		size: A4;
		margin: 15mm 15mm 18mm 15mm;
		@bottom-right {{
			content: "Page " counter(page) " of " counter(pages);
			font-size: 8pt;
			color: #666;
		}}
		@bottom-left {{
			content: "Izensphere LMS Assessment System";
			font-size: 8pt;
			color: #666;
		}}
	}}
	body {{
		font-family: 'Helvetica Neue', Arial, sans-serif;
		color: #1a1a1a;
		line-height: 1.45;
		font-size: 10pt;
		margin: 0;
		padding: 0;
	}}
	.header-table {{
		width: 100%;
		border-collapse: collapse;
		margin-bottom: 12px;
		border-bottom: 2px solid #222;
		padding-bottom: 8px;
	}}
	.school-name {{
		font-size: 16pt;
		font-weight: bold;
		text-align: center;
		letter-spacing: 0.5px;
		color: #111;
		margin: 0;
	}}
	.exam-title {{
		font-size: 13pt;
		font-weight: 600;
		text-align: center;
		margin: 3px 0 2px 0;
		color: #2b2b2b;
	}}
	.doc-subtitle {{
		font-size: 10pt;
		font-weight: bold;
		text-align: center;
		color: #0d5257;
		text-transform: uppercase;
		letter-spacing: 1px;
		margin-bottom: 6px;
	}}
	.meta-table {{
		width: 100%;
		border-collapse: collapse;
		font-size: 9pt;
		margin-top: 6px;
		margin-bottom: 10px;
	}}
	.meta-table td {{
		padding: 3px 6px;
		vertical-align: top;
	}}
	.instructions-box {{
		border: 1px solid #ddd;
		background: #fbfbfb;
		padding: 8px 12px;
		margin-bottom: 16px;
		border-radius: 4px;
		font-size: 8.5pt;
	}}
	.instructions-box h4 {{
		margin: 0 0 4px 0;
		font-size: 9pt;
		text-transform: uppercase;
		color: #333;
	}}
	.instructions-box ul {{
		margin: 0;
		padding-left: 18px;
	}}
	.section-container {{
		margin-bottom: 18px;
		page-break-inside: auto;
	}}
	.section-header {{
		background: #f0f4f8;
		border-top: 1.5px solid #0d5257;
		border-bottom: 1.5px solid #0d5257;
		padding: 4px 8px;
		font-weight: bold;
		font-size: 10pt;
		display: flex;
		justify-content: space-between;
		margin-bottom: 8px;
		page-break-after: avoid;
	}}
	.section-title {{
		color: #0d5257;
	}}
	.section-marks {{
		float: right;
		font-weight: bold;
	}}
	.section-instructions {{
		font-style: italic;
		font-size: 8.5pt;
		margin-bottom: 8px;
		color: #555;
	}}
	.question-item {{
		margin-bottom: 12px;
		page-break-inside: avoid;
	}}
	.q-header {{
		width: 100%;
		display: table;
	}}
	.q-num {{
		display: table-cell;
		width: 32px;
		font-weight: bold;
		vertical-align: top;
	}}
	.q-text {{
		display: table-cell;
		vertical-align: top;
	}}
	.q-marks {{
		display: table-cell;
		width: 60px;
		text-align: right;
		font-weight: 600;
		color: #444;
		vertical-align: top;
	}}
	.options-grid {{
		margin: 4px 0 6px 32px;
	}}
	.option-item {{
		font-size: 9pt;
		margin-bottom: 2px;
	}}
	.opt-marker {{
		font-weight: bold;
		margin-right: 4px;
	}}
	.or-separator {{
		text-align: center;
		font-weight: bold;
		font-size: 8.5pt;
		margin: 6px 0;
		color: #777;
	}}
	.or-question {{
		margin-left: 32px;
	}}
	.answer-box {{
		margin: 4px 0 4px 32px;
		background: #eef7ee;
		border-left: 3px solid #2e7d32;
		padding: 4px 8px;
		font-size: 9pt;
	}}
	.solution-box {{
		margin: 6px 0 6px 32px;
		background: #f7f9fc;
		border: 1px solid #d0dbe5;
		border-left: 3px solid #0288d1;
		padding: 6px 10px;
		font-size: 8.5pt;
	}}
	.sol-ans {{
		color: #0288d1;
		font-weight: bold;
		margin-bottom: 3px;
	}}
	.sol-steps {{
		color: #333;
		line-height: 1.4;
	}}
	.watermark {{
		position: fixed;
		top: 45%;
		left: 20%;
		font-size: 60pt;
		color: rgba(200, 200, 200, 0.15);
		transform: rotate(-35deg);
		z-index: -100;
		text-transform: uppercase;
		pointer-events: none;
	}}
</style>
</head>
<body>

<div class="watermark">IZENSPHERE</div>

<table class="header-table">
	<tr>
		{f"<td style='width: 70px;'><img src='{school_logo}' style='max-width: 65px; max-height: 65px;'></td>" if school_logo else ""}
		<td style="text-align: center;">
			<div class="school-name">{escape_html(school_name)}</div>
			<div class="exam-title">{escape_html(paper.title)}</div>
			<div class="doc-subtitle">{subtitle}</div>
		</td>
	</tr>
</table>

<table class="meta-table">
	<tr>
		<td><strong>Class / Batch:</strong> {escape_html(paper.class_level or '')}{f" (Batch: {escape_html(paper.batch)})" if getattr(paper, 'batch', None) and paper.batch != paper.class_level else ""}</td>
		<td><strong>Subject:</strong> {escape_html(paper.subject or '')}</td>
		<td style="text-align: right;"><strong>Academic Year:</strong> {escape_html(paper.academic_year or '2026-27')}</td>
	</tr>
	<tr>
		<td><strong>Duration:</strong> {escape_html(paper.duration or '3 Hours')}</td>
		<td><strong>Date:</strong> {escape_html(str(paper.examination_date or ''))}</td>
		<td style="text-align: right;"><strong>Maximum Marks:</strong> {paper.total_marks}</td>
	</tr>
</table>

{f'''
<div class="instructions-box">
	<h4>General Instructions:</h4>
	<ul>
		{instructions_html}
	</ul>
</div>
''' if instructions_html else ""}

<div class="paper-content">
	{sections_html}
</div>

</body>
</html>
"""
	return html


def generate_paper_pdf_file(paper_doc_name: str, doc_type: str = "question_paper") -> bytes:
	"""Generates binary PDF data using Frappe's PDF renderer."""
	html = get_paper_html(paper_doc_name, doc_type=doc_type)
	options = {
		"page-size": "A4",
		"margin-top": "15mm",
		"margin-bottom": "18mm",
		"margin-left": "15mm",
		"margin-right": "15mm",
		"encoding": "UTF-8",
		"no-outline": None,
	}
	return get_pdf(html, options=options)

