<template>
	<div class="flex-1 flex flex-col min-h-0 bg-surface-base overflow-y-auto">
		<PageHeader
			:breadcrumbs="[
				{ label: __('Assessments'), route: { name: 'Quizzes' } },
				{ label: __('Previous Year Papers & AI Analysis') },
			]"
		>
			<template #actions>
				<div class="flex items-center gap-2">
					<router-link :to="{ name: 'AIQuestionPaperGenerator' }">
						<Button variant="ghost" size="sm">
							<template #prefix><span class="lucide-file-text size-4"></span></template>
							{{ __('Question Paper Generator') }}
						</Button>
					</router-link>
					<router-link :to="{ name: 'AIQuestionBank' }">
						<Button variant="ghost" size="sm">
							<template #prefix><span class="lucide-database size-4"></span></template>
							{{ __('Question Bank') }}
						</Button>
					</router-link>
				</div>
			</template>
		</PageHeader>

		<div class="max-w-7xl mx-auto w-full p-4 md:p-6 space-y-6">
			<!-- Header Banner Card -->
			<div class="rounded-xl border bg-gradient-to-r from-violet-900 via-indigo-900 to-slate-900 text-white p-6 shadow-sm">
				<div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
					<div>
						<div class="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-xs font-semibold backdrop-blur-sm mb-2">
							<span class="lucide-sparkles size-3.5 text-amber-300"></span>
							{{ __('10+ Years Historical Pattern Analyzer') }}
						</div>
						<h1 class="text-2xl font-bold tracking-tight">
							{{ __('Previous Year Question Paper Analysis & Question Generator') }}
						</h1>
						<p class="text-sm text-indigo-200 mt-1 max-w-2xl">
							{{ __('Upload previous 10+ years examination question papers into one centralized DocType. AI analyzes collective historical patterns, detects repeated questions and high-yield topics, and synthesizes novel questions and university-standard model papers.') }}
						</p>
					</div>

					<div class="flex flex-wrap items-center gap-2">
						<Button
							variant="solid"
							theme="white"
							@click="showUploadModal = true"
						>
							<template #prefix><span class="lucide-upload size-4 text-violet-700"></span></template>
							{{ __('Upload Papers') }}
						</Button>

						<Button
							variant="solid"
							theme="violet"
							:loading="isAnalyzing"
							@click="triggerCollectiveAnalysis"
						>
							<template #prefix><span class="lucide-brain-circuit size-4"></span></template>
							{{ isAnalyzing ? __('Analyzing All Papers...') : __('Analyze All Papers') }}
						</Button>
					</div>
				</div>
			</div>

			<!-- Course & Subject Selector Controls -->
			<div class="bg-white rounded-xl border p-4 shadow-sm grid grid-cols-1 md:grid-cols-3 gap-4 items-center">
				<div>
					<label class="block text-xs font-semibold uppercase text-gray-500 mb-1">
						{{ __('Select Course') }} <span class="text-red-500">*</span>
					</label>
					<select
						v-model="selectedCourse"
						class="w-full text-sm rounded-lg border-gray-300 focus:border-violet-500 focus:ring-violet-500 font-medium"
						@change="onCourseChanged"
					>
						<option value="">{{ __('Select a Course') }}</option>
						<option v-for="c in coursesList" :key="c.name" :value="c.name">
							{{ c.title || c.name }}
						</option>
					</select>
				</div>

				<div>
					<label class="block text-xs font-semibold uppercase text-gray-500 mb-1">
						{{ __('Filter Subject (Optional)') }}
					</label>
					<input
						v-model="selectedSubject"
						type="text"
						placeholder="e.g. Java Programming (Leave blank for all)"
						class="w-full text-sm rounded-lg border-gray-300 focus:border-violet-500 focus:ring-violet-500"
						@change="fetchUploadedPapers"
					/>
				</div>

				<div class="flex items-center gap-2 justify-end pt-5">
					<Button
						variant="outline"
						size="sm"
						:disabled="!selectedCourse"
						@click="openQuestionGenerator"
					>
						<template #prefix><span class="lucide-sparkles size-3.5 text-violet-600"></span></template>
						{{ __('Generate Questions') }}
					</Button>

					<Button
						variant="outline"
						size="sm"
						:disabled="!selectedCourse"
						@click="openModelPaperGenerator"
					>
						<template #prefix><span class="lucide-file-text size-3.5 text-indigo-600"></span></template>
						{{ __('Model Paper') }}
					</Button>
				</div>
			</div>

			<!-- Main Navigation Tabs -->
			<div class="flex items-center gap-3 border-b">
				<button
					class="pb-2 text-sm font-semibold border-b-2 px-2 transition-colors flex items-center gap-1.5"
					:class="activeTab === 'papers' ? 'border-violet-600 text-violet-600' : 'border-transparent text-gray-500 hover:text-gray-700'"
					@click="activeTab = 'papers'"
				>
					<span class="lucide-file-stack size-4"></span>
					{{ __('Uploaded Papers (10+ Years)') }}
					<span class="ml-1 text-xs bg-gray-100 text-gray-700 px-2 py-0.5 rounded-full font-mono">
						{{ uploadedPapers.length }}
					</span>
				</button>

				<button
					class="pb-2 text-sm font-semibold border-b-2 px-2 transition-colors flex items-center gap-1.5"
					:class="activeTab === 'dashboard' ? 'border-violet-600 text-violet-600' : 'border-transparent text-gray-500 hover:text-gray-700'"
					@click="activeTab = 'dashboard'"
				>
					<span class="lucide-bar-chart-3 size-4"></span>
					{{ __('Historical Analysis Dashboard') }}
				</button>

				<button
					class="pb-2 text-sm font-semibold border-b-2 px-2 transition-colors flex items-center gap-1.5"
					:class="activeTab === 'staged' ? 'border-violet-600 text-violet-600' : 'border-transparent text-gray-500 hover:text-gray-700'"
					@click="activeTab = 'staged'"
				>
					<span class="lucide-sparkles size-4"></span>
					{{ __('AI Generated Questions (Review)') }}
					<span v-if="stagedQuestions.length > 0" class="ml-1 text-xs bg-violet-100 text-violet-700 px-2 py-0.5 rounded-full font-mono">
						{{ stagedQuestions.length }}
					</span>
				</button>

				<button
					class="pb-2 text-sm font-semibold border-b-2 px-2 transition-colors flex items-center gap-1.5"
					:class="activeTab === 'model_papers' ? 'border-violet-600 text-violet-600' : 'border-transparent text-gray-500 hover:text-gray-700'"
					@click="activeTab = 'model_papers'"
				>
					<span class="lucide-book-open size-4"></span>
					{{ __('Model Question Papers') }}
				</button>
			</div>

			<!-- TAB 1: UPLOADED PAPERS TABLE -->
			<div v-if="activeTab === 'papers'" class="space-y-4">
				<div class="rounded-xl border bg-white shadow-sm overflow-hidden">
					<div class="p-4 border-b bg-gray-50/50 flex flex-col md:flex-row md:items-center justify-between gap-3">
						<div>
							<h3 class="text-sm font-bold text-gray-900">
								{{ __('Centralized Previous Year Papers Collection') }}
							</h3>
							<p class="text-xs text-gray-500">
								{{ __('All uploaded question papers belonging to this course are analyzed collectively by AI.') }}
							</p>
						</div>

						<Button
							variant="solid"
							theme="violet"
							size="sm"
							@click="showUploadModal = true"
						>
							<template #prefix><span class="lucide-plus size-4"></span></template>
							{{ __('Upload Another Paper') }}
						</Button>
					</div>

					<div v-if="uploadedPapers.length === 0" class="p-12 text-center space-y-3">
						<span class="lucide-upload-cloud size-12 text-gray-300 mx-auto block"></span>
						<h3 class="text-sm font-bold text-gray-700">
							{{ __('No Question Papers Uploaded Yet') }}
						</h3>
						<p class="text-xs text-gray-500 max-w-md mx-auto">
							{{ __('Upload 10 years or more examination papers (PDF, DOCX, Scanned documents). AI will combine and analyze all papers collectively.') }}
						</p>
						<Button
							variant="solid"
							theme="violet"
							size="sm"
							@click="showUploadModal = true"
						>
							{{ __('Upload First Question Paper') }}
						</Button>
					</div>

					<div v-else class="overflow-x-auto">
						<table class="w-full text-left text-xs">
							<thead class="bg-gray-50 text-gray-600 font-semibold uppercase tracking-wider border-b">
								<tr>
									<th class="py-3 px-4">{{ __('Exam Year') }}</th>
									<th class="py-3 px-4">{{ __('Paper Title / Subject') }}</th>
									<th class="py-3 px-4">{{ __('Examination Type') }}</th>
									<th class="py-3 px-4 text-center">{{ __('Max Marks') }}</th>
									<th class="py-3 px-4 text-center">{{ __('Extracted Questions') }}</th>
									<th class="py-3 px-4 text-center">{{ __('AI Processing Status') }}</th>
									<th class="py-3 px-4 text-right">{{ __('Actions') }}</th>
								</tr>
							</thead>
							<tbody class="divide-y text-gray-700">
								<tr
									v-for="paper in uploadedPapers"
									:key="paper.name"
									class="hover:bg-gray-50/80 transition-colors"
								>
									<td class="py-3 px-4 font-mono font-bold text-violet-700 text-sm">
										{{ paper.examination_year }}
									</td>
									<td class="py-3 px-4">
										<div class="font-semibold text-gray-900">{{ paper.title }}</div>
										<div class="text-[11px] text-gray-400">
											{{ paper.subject }} • {{ paper.academic_year || 'Multi-Year' }}
										</div>
									</td>
									<td class="py-3 px-4 text-gray-600">
										{{ paper.examination_type || 'Annual Examination' }}
									</td>
									<td class="py-3 px-4 text-center font-medium">
										{{ paper.max_marks || 100 }} M
									</td>
									<td class="py-3 px-4 text-center">
										<span class="font-bold text-gray-800 font-mono">
											{{ paper.extracted_questions_count || 0 }}
										</span>
									</td>
									<td class="py-3 px-4 text-center">
										<span
											class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold"
											:class="{
												'bg-emerald-100 text-emerald-800': paper.ai_processing_status === 'Processed',
												'bg-amber-100 text-amber-800 animate-pulse': paper.ai_processing_status === 'Processing',
												'bg-gray-100 text-gray-700': paper.ai_processing_status === 'Pending',
												'bg-rose-100 text-rose-800': paper.ai_processing_status === 'Failed',
											}"
										>
											<span v-if="paper.ai_processing_status === 'Processed'" class="lucide-check-circle size-3"></span>
											<span v-else-if="paper.ai_processing_status === 'Processing'" class="lucide-loader-2 size-3 animate-spin"></span>
											<span v-else-if="paper.ai_processing_status === 'Failed'" class="lucide-alert-triangle size-3"></span>
											{{ paper.ai_processing_status }}
										</span>
									</td>
									<td class="py-3 px-4 text-right">
										<div class="flex items-center justify-end gap-1">
											<Button
												v-if="paper.ai_processing_status !== 'Processed'"
												variant="ghost"
												size="sm"
												theme="violet"
												@click="reprocessPaper(paper.name)"
											>
												{{ __('Extract') }}
											</Button>
											<a
												v-if="paper.attachment"
												:href="paper.attachment"
												target="_blank"
												class="p-1.5 text-gray-400 hover:text-gray-700 rounded hover:bg-gray-100"
												title="Download File"
											>
												<span class="lucide-download size-4"></span>
											</a>
											<button
												class="p-1.5 text-red-400 hover:text-red-700 rounded hover:bg-red-50"
												title="Delete Paper"
												@click="deletePaper(paper.name)"
											>
												<span class="lucide-trash-2 size-4"></span>
											</button>
										</div>
									</td>
								</tr>
							</tbody>
						</table>
					</div>
				</div>
			</div>

			<!-- TAB 2: HISTORICAL ANALYSIS DASHBOARD -->
			<div v-else-if="activeTab === 'dashboard'" class="space-y-4">
				<div v-if="!analysisDashboard.has_data && !analysisDashboard.total_uploaded_papers" class="p-12 text-center bg-white rounded-xl border space-y-3">
					<span class="lucide-brain-circuit size-12 text-gray-300 mx-auto block"></span>
					<h3 class="text-sm font-bold text-gray-700">
						{{ __('No Historical Analysis Computed Yet') }}
					</h3>
					<p class="text-xs text-gray-500 max-w-md mx-auto">
						{{ __('Click "Analyze All Papers" to run collective pattern analysis across all uploaded question papers.') }}
					</p>
					<Button
						variant="solid"
						theme="violet"
						size="sm"
						:loading="isAnalyzing"
						@click="triggerCollectiveAnalysis"
					>
						{{ __('Run Collective Analysis Now') }}
					</Button>
				</div>

				<PreviousYearAnalysisDashboard
					v-else
					:analysis-data="analysisDashboard"
					@generate-questions="openQuestionGenerator"
					@generate-model-paper="openModelPaperGenerator"
				/>
			</div>

			<!-- TAB 3: STAGED AI GENERATED QUESTIONS -->
			<div v-else-if="activeTab === 'staged'" class="space-y-4">
				<div class="bg-white rounded-xl border p-4 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-3">
					<div>
						<h3 class="text-sm font-bold text-gray-900">
							{{ __('Staged AI-Generated Questions') }}
						</h3>
						<p class="text-xs text-gray-500">
							{{ __('Review, edit, delete, or regenerate questions before saving approved ones into the permanent Question Bank. Generated questions are strictly hidden from students.') }}
						</p>
					</div>

					<div class="flex items-center gap-2">
						<Button
							variant="solid"
							theme="emerald"
							size="sm"
							:disabled="approvedQuestionsCount === 0 || isSavingToBank"
							:loading="isSavingToBank"
							@click="saveApprovedToBank"
						>
							<template #prefix><span class="lucide-database size-4"></span></template>
							{{ __('Save Approved to Question Bank') }} ({{ approvedQuestionsCount }})
						</Button>

						<Button
							variant="outline"
							size="sm"
							@click="openQuestionGenerator"
						>
							<template #prefix><span class="lucide-plus size-4"></span></template>
							{{ __('Generate More') }}
						</Button>
					</div>
				</div>

				<div v-if="stagedQuestions.length === 0" class="p-12 text-center bg-white rounded-xl border space-y-3">
					<span class="lucide-help-circle size-12 text-gray-300 mx-auto block"></span>
					<h3 class="text-sm font-bold text-gray-700">
						{{ __('No Generated Questions in Staging') }}
					</h3>
					<p class="text-xs text-gray-500 max-w-md mx-auto">
						{{ __('Click "Generate Questions" to synthesize new questions testing historical high-frequency concepts.') }}
					</p>
					<Button
						variant="solid"
						theme="violet"
						size="sm"
						@click="openQuestionGenerator"
					>
						{{ __('Generate New Questions Using AI') }}
					</Button>
				</div>

				<div v-else class="space-y-3">
					<div
						v-for="(q, qIdx) in stagedQuestions"
						:key="q.id || qIdx"
						class="rounded-xl border bg-white p-5 shadow-sm space-y-3 transition-colors"
						:class="{
							'border-emerald-300 bg-emerald-50/10': q.status === 'Approved',
							'border-rose-200 bg-rose-50/20 opacity-70': q.status === 'Rejected',
						}"
					>
						<div class="flex items-start justify-between gap-4">
							<div class="flex items-center gap-2 flex-wrap">
								<span class="font-mono text-xs font-bold text-gray-400">#{{ qIdx + 1 }}</span>
								<span class="text-xs font-bold px-2 py-0.5 rounded bg-violet-100 text-violet-800">
									{{ q.type }}
								</span>
								<span
									class="text-xs font-semibold px-2 py-0.5 rounded"
									:class="{
										'bg-emerald-100 text-emerald-800': q.difficulty === 'Easy',
										'bg-amber-100 text-amber-800': q.difficulty === 'Medium',
										'bg-rose-100 text-rose-800': q.difficulty === 'Hard',
									}"
								>
									{{ q.difficulty }}
								</span>
								<span class="text-xs font-bold text-indigo-700 font-mono">
									{{ q.marks }} Marks
								</span>
								<span class="text-xs text-gray-500">
									Topic: <strong class="text-gray-700">{{ q.topic || q.chapter }}</strong>
								</span>
							</div>

							<!-- Question Review Status Actions -->
							<div class="flex items-center gap-1.5">
								<button
									class="px-2.5 py-1 text-xs font-semibold rounded transition-colors"
									:class="q.status === 'Approved' ? 'bg-emerald-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-emerald-100'"
									@click="q.status = 'Approved'"
								>
									{{ __('Approve') }}
								</button>
								<button
									class="px-2.5 py-1 text-xs font-semibold rounded transition-colors"
									:class="q.status === 'Rejected' ? 'bg-rose-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-rose-100'"
									@click="q.status = 'Rejected'"
								>
									{{ __('Reject') }}
								</button>
								<button
									class="p-1 text-gray-400 hover:text-violet-600 rounded"
									title="Regenerate this question"
									@click="regenerateSingle(q, qIdx)"
								>
									<span class="lucide-refresh-cw size-4"></span>
								</button>
								<button
									class="p-1 text-gray-400 hover:text-red-600 rounded"
									title="Delete"
									@click="deleteStagedQuestion(qIdx)"
								>
									<span class="lucide-trash-2 size-4"></span>
								</button>
							</div>
						</div>

						<!-- Editable Question Text -->
						<div>
							<textarea
								v-model="q.question"
								rows="2"
								class="w-full text-sm font-medium rounded-lg border-gray-200 focus:border-violet-500 focus:ring-violet-500 p-2 text-gray-900"
							></textarea>
						</div>

						<!-- Options for MCQ -->
						<div v-if="q.options && q.options.length > 0" class="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
							<div
								v-for="(opt, oIdx) in q.options"
								:key="oIdx"
								class="p-2 rounded border bg-gray-50/50"
								:class="opt === q.correct_answer ? 'border-emerald-400 bg-emerald-50 text-emerald-900 font-semibold' : 'border-gray-200 text-gray-700'"
							>
								{{ opt }}
							</div>
						</div>

						<!-- Answer & Explanation & Detailed Model Solution -->
						<div class="text-xs bg-gray-50 p-3.5 rounded-lg space-y-2 border border-gray-100">
							<div class="text-emerald-800 font-semibold flex items-start gap-1.5">
								<span class="px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-800 font-bold uppercase text-[10px]">Answer</span>
								<span class="font-normal">{{ q.correct_answer }}</span>
							</div>

							<!-- Marking Rubric -->
							<div v-if="q.answer_key_detail" class="bg-emerald-50/70 p-2.5 rounded border border-emerald-100 text-[11px] text-emerald-950 font-mono whitespace-pre-wrap leading-relaxed">
								<span class="font-sans font-bold text-emerald-800 block mb-1 uppercase text-[10px] tracking-wider">Evaluation Rubric ({{ q.marks }} Marks):</span>
								{{ q.answer_key_detail }}
							</div>

							<!-- Detailed Pedagogical Model Solution Toggle -->
							<details v-if="q.solution" class="group">
								<summary class="cursor-pointer text-violet-700 font-semibold hover:text-violet-900 list-none flex items-center gap-1.5 py-1">
									<span class="lucide-chevron-right size-3.5 transition-transform group-open:rotate-90"></span>
									<span>{{ __('View Detailed Pedagogical Model Solution') }}</span>
								</summary>
								<div class="mt-2 bg-slate-900 text-slate-100 p-3 rounded-lg font-mono text-[11px] leading-relaxed whitespace-pre-wrap overflow-x-auto border border-slate-800 shadow-inner">
									{{ q.solution }}
								</div>
							</details>

							<div v-if="q.historical_reference" class="text-[11px] text-indigo-700 pt-1 font-medium flex items-center gap-1">
								<span class="lucide-history size-3"></span>
								<span>Historical Reference: {{ q.historical_reference }}</span>
							</div>
						</div>
					</div>
				</div>
			</div>

			<!-- TAB 4: MODEL QUESTION PAPERS -->
			<div v-else-if="activeTab === 'model_papers'" class="space-y-4">
				<div class="bg-white rounded-xl border p-4 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-3">
					<div>
						<h3 class="text-sm font-bold text-gray-900">
							{{ __('Historical Model Examination Papers') }}
						</h3>
						<p class="text-xs text-gray-500">
							{{ __('University-standard model papers generated from historical examination analysis. Download printable A4 PDFs and separate Answer Keys.') }}
						</p>
					</div>

					<Button
						variant="solid"
						theme="violet"
						size="sm"
						@click="openModelPaperGenerator"
					>
						<template #prefix><span class="lucide-plus size-4"></span></template>
						{{ __('Generate New Model Paper') }}
					</Button>
				</div>

				<div v-if="modelPapersList.length === 0" class="p-12 text-center bg-white rounded-xl border space-y-3">
					<span class="lucide-book-open size-12 text-gray-300 mx-auto block"></span>
					<h3 class="text-sm font-bold text-gray-700">
						{{ __('No Model Papers Generated Yet') }}
					</h3>
					<p class="text-xs text-gray-500 max-w-md mx-auto">
						{{ __('Generate a formal 100-mark model paper with Section A (MCQs), Section B (Short), Section C (Long), and Section D (Essay) based on historical patterns.') }}
					</p>
					<Button
						variant="solid"
						theme="violet"
						size="sm"
						@click="openModelPaperGenerator"
					>
						{{ __('Generate Model Paper Now') }}
					</Button>
				</div>

				<div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
					<div
						v-for="paper in modelPapersList"
						:key="paper.name"
						class="rounded-xl border bg-white p-5 shadow-sm space-y-4 flex flex-col justify-between"
					>
						<div class="space-y-2">
							<div class="flex items-center justify-between">
								<span class="text-xs font-bold text-violet-700 bg-violet-50 px-2 py-0.5 rounded">
									{{ paper.subject || selectedSubject || 'All' }}
								</span>
								<span class="text-xs font-bold text-gray-700 font-mono">
									{{ paper.total_marks }} Marks • {{ paper.duration || '3 Hours' }}
								</span>
							</div>

							<h4 class="text-base font-bold text-gray-900">
								{{ paper.title }}
							</h4>

							<div class="text-xs text-gray-500 flex items-center gap-3">
								<span>Status: 
									<span 
										class="px-2 py-0.5 rounded text-[11px] font-bold"
										:class="paper.approval_status === 'Published' ? 'bg-emerald-100 text-emerald-800' : (paper.approval_status === 'Principal Approved' ? 'bg-blue-100 text-blue-800' : (paper.approval_status === 'Submitted for Approval' ? 'bg-amber-100 text-amber-800' : 'bg-gray-100 text-gray-700'))"
									>
										{{ paper.approval_status }}
									</span>
								</span>
								<span>{{ paper.creation ? new Date(paper.creation).toLocaleDateString() : '' }}</span>
							</div>
						</div>

						<div class="pt-3 border-t flex items-center justify-between gap-2 flex-wrap">
							<div class="flex items-center gap-2 flex-wrap">
								<Button
									variant="solid"
									theme="violet"
									size="sm"
									@click="downloadPaperPdf(paper.name, 'question_paper')"
								>
									<template #prefix><span class="lucide-download size-3.5"></span></template>
									{{ __('Question Paper PDF') }}
								</Button>

								<Button
									variant="outline"
									theme="gray"
									size="sm"
									@click="downloadPaperPdf(paper.name, 'answer_key')"
								>
									<template #prefix><span class="lucide-key size-3.5 text-amber-600"></span></template>
									{{ __('Answer Key') }}
								</Button>

								<Button
									variant="outline"
									theme="violet"
									size="sm"
									@click="downloadPaperPdf(paper.name, 'detailed_solutions')"
								>
									<template #prefix><span class="lucide-file-text size-3.5 text-violet-600"></span></template>
									{{ __('Detailed Solutions PDF') }}
								</Button>

								<Button
									v-if="paper.approval_status !== 'Published'"
									variant="solid"
									theme="green"
									size="sm"
									:loading="publishingPaper === paper.name"
									@click="publishPaper(paper.name)"
								>
									<template #prefix><span class="lucide-check-circle size-3.5"></span></template>
									{{ __('Publish') }}
								</Button>
							</div>

							<router-link
								:to="{ name: 'AIQuestionPaperGenerator', query: { paper: paper.name } }"
								class="text-xs text-violet-600 font-semibold hover:underline"
							>
								{{ __('Review & Edit') }} →
							</router-link>
						</div>
					</div>
				</div>
			</div>
		</div>

		<!-- MODALS -->
		<PreviousYearUploadModal
			v-model="showUploadModal"
			:default-course="selectedCourse"
			:default-subject="selectedSubject"
			:courses="coursesList"
			@uploaded="onPaperUploaded"
		/>

		<HistoricalQuestionGeneratorModal
			v-model="showQuestionGeneratorModal"
			:course="selectedCourse"
			:subject="selectedSubject"
			:analysis-name="analysisDashboard.analysis_name"
			@generated="onQuestionsGenerated"
		/>

		<HistoricalModelPaperModal
			v-model="showModelPaperModal"
			:course="selectedCourse"
			:subject="selectedSubject"
			:analysis-name="analysisDashboard.analysis_name"
			@created="onModelPaperCreated"
		/>
	</div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { Button, toast } from 'frappe-ui'
import { createResource } from 'frappe-ui'
import PageHeader from '@/components/Layouts/PageHeader.vue'
import PreviousYearUploadModal from '@/components/AI/PreviousYearUploadModal.vue'
import HistoricalQuestionGeneratorModal from '@/components/AI/HistoricalQuestionGeneratorModal.vue'
import HistoricalModelPaperModal from '@/components/AI/HistoricalModelPaperModal.vue'
import PreviousYearAnalysisDashboard from '@/components/AI/PreviousYearAnalysisDashboard.vue'

const route = useRoute()

const activeTab = ref<'papers' | 'dashboard' | 'staged' | 'model_papers'>('papers')
const selectedCourse = ref((route.query.course as string) || '')
const selectedSubject = ref((route.query.subject as string) || '')
const selectedBatch = ref((route.query.batch as string) || '')

const coursesList = ref<Array<{ name: string; title: string }>>([])
const uploadedPapers = ref<any[]>([])
const stagedQuestions = ref<any[]>([])
const modelPapersList = ref<any[]>([])
const analysisDashboard = ref<any>({})

const isAnalyzing = ref(false)
const isSavingToBank = ref(false)
const publishingPaper = ref<string | null>(null)
const showUploadModal = ref(false)
const showQuestionGeneratorModal = ref(false)
const showModelPaperModal = ref(false)

const approvedQuestionsCount = computed(() => {
	return stagedQuestions.value.filter((q) => q.status === 'Approved').length
})

onMounted(async () => {
	await fetchCourses()
	if (selectedCourse.value) {
		await fetchUploadedPapers()
		await fetchHistoricalDashboard()
		await fetchModelPapers()
	}
})

async function fetchCourses() {
	try {
		const res = await createResource({
			url: 'frappe.client.get_list',
			params: {
				doctype: 'LMS Course',
				fields: ['name', 'title'],
				limit_page_length: 100,
			},
		}).fetch()
		coursesList.value = res || []
		if (!selectedCourse.value && coursesList.value.length > 0) {
			selectedCourse.value = coursesList.value[0].name
			await fetchUploadedPapers()
			await fetchHistoricalDashboard()
			await fetchModelPapers()
		}
	} catch (err) {
		console.error('Failed to fetch courses:', err)
	}
}

async function onCourseChanged() {
	await fetchUploadedPapers()
	await fetchHistoricalDashboard()
	await fetchModelPapers()
}

async function fetchUploadedPapers() {
	if (!selectedCourse.value) return
	try {
		const res = await createResource({
			url: 'lms.lms.ai.previous_year_api.api_get_uploaded_papers',
			params: {
				course: selectedCourse.value,
				subject: selectedSubject.value || undefined,
				batch: selectedBatch.value || undefined,
			},
		}).fetch()
		uploadedPapers.value = res || []
	} catch (err) {
		console.error('Failed to load uploaded papers:', err)
	}
}

async function fetchHistoricalDashboard() {
	if (!selectedCourse.value) return
	try {
		const res = await createResource({
			url: 'lms.lms.ai.previous_year_api.api_get_historical_dashboard',
			params: {
				course: selectedCourse.value,
				subject: selectedSubject.value || undefined,
				batch: selectedBatch.value || undefined,
			},
		}).fetch()
		analysisDashboard.value = res || {}
	} catch (err) {
		console.error('Failed to load dashboard:', err)
	}
}

async function fetchModelPapers() {
	if (!selectedCourse.value) return
	try {
		const res = await createResource({
			url: 'frappe.client.get_list',
			params: {
				doctype: 'AI Question Paper',
				filters: {
					course: selectedCourse.value,
				},
				fields: ['name', 'title', 'subject', 'total_marks', 'duration', 'approval_status', 'creation'],
				order_by: 'creation desc',
				limit_page_length: 20,
			},
		}).fetch()
		modelPapersList.value = res || []
	} catch (err) {
		console.error('Failed to fetch model papers:', err)
	}
}

async function triggerCollectiveAnalysis() {
	if (!selectedCourse.value) return
	isAnalyzing.value = true
	try {
		const res = await createResource({
			url: 'lms.lms.ai.previous_year_api.api_analyze_all_papers',
			params: {
				course: selectedCourse.value,
				subject: selectedSubject.value || undefined,
				batch: selectedBatch.value || undefined,
			},
		}).fetch()
		analysisDashboard.value = res
		activeTab.value = 'dashboard'
		toast.success(`Analyzed ${res.total_uploaded_papers} papers and extracted ${res.total_extracted_questions} questions.`)
	} catch (err: any) {
		toast.error(err.message || 'Could not complete collective analysis.')
	} finally {
		isAnalyzing.value = false
	}
}

async function reprocessPaper(paperName: string) {
	try {
		await createResource({
			url: 'lms.lms.ai.previous_year_api.api_process_paper',
			params: { paper_name: paperName },
		}).fetch()
		await fetchUploadedPapers()
		toast.success('Questions successfully extracted from document.')
	} catch (err: any) {
		toast.error(err.message || 'Extraction failed.')
	}
}

async function deletePaper(paperName: string) {
	if (!confirm('Are you sure you want to delete this previous year question paper?')) return
	try {
		await createResource({
			url: 'lms.lms.ai.previous_year_api.api_delete_uploaded_paper',
			params: { paper_name: paperName },
		}).fetch()
		await fetchUploadedPapers()
		toast.success('Paper Deleted.')
	} catch (err: any) {
		toast.error(err.message || 'Deletion failed.')
	}
}

function onPaperUploaded() {
	fetchUploadedPapers()
}

function openQuestionGenerator() {
	showQuestionGeneratorModal.value = true
}

function openModelPaperGenerator() {
	showModelPaperModal.value = true
}

function onQuestionsGenerated(questions: any[]) {
	// Set initial status to Approved for teacher convenience
	questions.forEach((q) => (q.status = 'Approved'))
	stagedQuestions.value.unshift(...questions)
	activeTab.value = 'staged'
}

function onModelPaperCreated() {
	fetchModelPapers()
	activeTab.value = 'model_papers'
}

function deleteStagedQuestion(idx: number) {
	stagedQuestions.value.splice(idx, 1)
}

async function regenerateSingle(q: any, idx: number) {
	try {
		const res = await createResource({
			url: 'lms.lms.ai.previous_year_api.api_regenerate_single_question',
			params: {
				question_id: q.id,
				analysis_name: analysisDashboard.value?.analysis_name,
				course: selectedCourse.value,
				subject: selectedSubject.value || q.subject || 'General',
				topic: q.topic || q.chapter,
				question_type: q.type,
				difficulty: q.difficulty,
				marks: q.marks,
			},
		}).fetch()
		if (res && res.question) {
			stagedQuestions.value[idx] = res.question
			toast.success('Fresh question generated from historical pattern.')
		}
	} catch (err: any) {
		toast.error(err.message || 'Regeneration failed.')
	}
}

async function saveApprovedToBank() {
	const approved = stagedQuestions.value.filter((q) => q.status === 'Approved')
	if (approved.length === 0) return

	isSavingToBank.value = true
	try {
		const res = await createResource({
			url: 'lms.lms.ai.previous_year_api.api_save_approved_questions_to_bank',
			params: {
				questions: JSON.stringify(approved),
				course: selectedCourse.value,
				subject: selectedSubject.value,
			},
		}).fetch()

		toast.success(`Successfully added ${res.saved_count} questions to the LMS Question Bank.`)

		// Remove approved questions from staging
		stagedQuestions.value = stagedQuestions.value.filter((q) => q.status !== 'Approved')
	} catch (err: any) {
		toast.error(err.message || 'Save failed.')
	} finally {
		isSavingToBank.value = false
	}
}

function downloadPaperPdf(paperName: string, docType: 'question_paper' | 'answer_key' | 'detailed_solutions') {
	window.open(
		`/api/method/lms.lms.ai.previous_year_api.api_download_model_paper_pdf?paper_name=${encodeURIComponent(
			paperName
		)}&doc_type=${docType}`,
		'_blank'
	)
}

async function publishPaper(paperName: string) {
	publishingPaper.value = paperName
	try {
		await createResource({
			url: 'lms.lms.ai.ai_assessment_api.api_publish_assessment',
			params: {
				doctype: 'AI Question Paper',
				name: paperName,
			},
		}).fetch()
		toast.success('Question paper successfully published to students.')
		await fetchModelPapers()
	} catch (err: any) {
		toast.error(err.message || 'Failed to publish question paper.')
	} finally {
		publishingPaper.value = null
	}
}
</script>
