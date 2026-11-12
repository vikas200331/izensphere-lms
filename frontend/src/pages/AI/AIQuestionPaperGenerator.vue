<template>
	<div class="flex-1 flex flex-col min-h-0 bg-surface-base overflow-y-auto">
		<PageHeader :breadcrumbs="[{ label: __('Assessments'), route: { name: 'Quizzes' } }, { label: __('AI Question Paper Generator') }]">
			<template #actions>
				<div class="flex items-center gap-2">
					<router-link :to="{ name: 'AIQuestionBank' }">
						<Button variant="ghost" size="sm">
							<template #prefix><span class="lucide-database size-4"></span></template>
							{{ __('Question Bank') }}
						</Button>
					</router-link>
					<router-link :to="{ name: 'AIGenerationHistory' }">
						<Button variant="ghost" size="sm">
							<template #prefix><span class="lucide-history size-4"></span></template>
							{{ __('AI History') }}
						</Button>
					</router-link>
				</div>
			</template>
		</PageHeader>

		<div class="max-w-7xl mx-auto w-full p-4 md:p-6 space-y-6">
			<!-- Header Title Card -->
			<div class="rounded-xl border bg-gradient-to-r from-violet-900 to-indigo-900 text-white p-6 shadow-sm">
				<div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
					<div>
						<div class="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-xs font-semibold backdrop-blur-sm mb-2">
							<span class="lucide-sparkles size-3.5 text-amber-300"></span>
							{{ __('Izensphere AI Assessment Engine') }}
						</div>
						<h1 class="text-2xl font-bold tracking-tight">
							{{ __('AI Question Paper Generator') }}
						</h1>
						<p class="text-sm text-indigo-200 mt-1 max-w-2xl">
							{{ __('Generate formal examination papers with section patterns, internal choice questions, automated marks validation, printable A4 PDFs, Answer Keys, and Step-by-Step Solutions.') }}
						</p>
					</div>

					<div class="flex items-center gap-2">
						<Button
							v-if="generatedPaper"
							variant="solid"
							theme="white"
							@click="activeView = 'preview'"
						>
							{{ __('View Generated Paper') }}
						</Button>
					</div>
				</div>
			</div>

			<!-- Main Content: Tabs for Builder vs Saved Papers -->
			<div class="flex items-center gap-2 border-b">
				<button
					class="pb-2 text-sm font-semibold border-b-2 px-2 transition-colors"
					:class="activeView === 'generator' ? 'border-violet-600 text-violet-600' : 'border-transparent text-gray-500 hover:text-gray-700'"
					@click="activeView = 'generator'"
				>
					{{ __('Create New Question Paper') }}
				</button>
				<button
					v-if="generatedPaper"
					class="pb-2 text-sm font-semibold border-b-2 px-2 transition-colors"
					:class="activeView === 'preview' ? 'border-violet-600 text-violet-600' : 'border-transparent text-gray-500 hover:text-gray-700'"
					@click="activeView = 'preview'"
				>
					{{ __('Paper Preview & Validation') }}
				</button>
				<button
					class="pb-2 text-sm font-semibold border-b-2 px-2 transition-colors"
					:class="activeView === 'saved_list' ? 'border-violet-600 text-violet-600' : 'border-transparent text-gray-500 hover:text-gray-700'"
					@click="loadSavedPapers(); activeView = 'saved_list'"
				>
					{{ __('Saved Question Papers') }}
				</button>
			</div>

			<!-- VIEW 1: GENERATOR FORM -->
			<div v-if="activeView === 'generator'" class="grid grid-cols-1 lg:grid-cols-3 gap-6">
				<!-- Configuration Form (Col 1 & 2) -->
				<div class="lg:col-span-2 space-y-5 rounded-xl border bg-surface-base p-6 shadow-sm">
					<h2 class="text-base font-semibold text-ink-gray-9 border-b pb-3 flex items-center gap-2">
						<span class="lucide-settings-2 size-4 text-violet-600"></span>
						{{ __('Examination Specifications') }}
					</h2>

					<!-- Academic & Exam Metadata -->
					<div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
						<div>
							<label class="block text-xs font-medium text-ink-gray-7 mb-1">{{ __('Academic Year') }} *</label>
							<input
								type="text"
								v-model="form.academic_year"
								class="w-full rounded-md border border-gray-300 px-3 py-1.5 text-sm dark:bg-gray-800 dark:border-gray-700"
								placeholder="2026-27"
							/>
						</div>
						<div>
							<label class="block text-xs font-medium text-ink-gray-7 mb-1">{{ __('Class / Grade') }} *</label>
							<input
								type="text"
								v-model="form.class_level"
								class="w-full rounded-md border border-gray-300 px-3 py-1.5 text-sm dark:bg-gray-800 dark:border-gray-700"
								placeholder="Class 10"
							/>
						</div>
						<div>
							<label class="block text-xs font-medium text-ink-gray-7 mb-1">{{ __('Subject') }} *</label>
							<input
								type="text"
								v-model="form.subject"
								class="w-full rounded-md border border-gray-300 px-3 py-1.5 text-sm dark:bg-gray-800 dark:border-gray-700"
								placeholder="Science / Mathematics"
							/>
						</div>
						<div>
							<label class="block text-xs font-medium text-ink-gray-7 mb-1">{{ __('Exam Type') }}</label>
							<select
								v-model="form.examination_type"
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm dark:bg-gray-800 dark:border-gray-700"
							>
								<option value="Midterm Examination">{{ __('Midterm Examination') }}</option>
								<option value="Unit Test">{{ __('Unit Test') }}</option>
								<option value="Quarterly Examination">{{ __('Quarterly Examination') }}</option>
								<option value="Half Yearly Examination">{{ __('Half Yearly Examination') }}</option>
								<option value="Annual Examination">{{ __('Annual Examination') }}</option>
								<option value="Final Examination">{{ __('Final Examination') }}</option>
								<option value="Pre-Board Examination">{{ __('Pre-Board Examination') }}</option>
								<option value="Practice Test">{{ __('Practice Test') }}</option>
							</select>
						</div>
					</div>

					<!-- Marks, Duration, Date -->
					<div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
						<div>
							<label class="block text-xs font-medium text-ink-gray-7 mb-1">{{ __('Total Marks') }} *</label>
							<select
								v-model.number="form.total_marks"
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm dark:bg-gray-800 dark:border-gray-700"
								@change="onTotalMarksChange"
							>
								<option :value="80">80 {{ __('Marks (Standard CBSE/Board)') }}</option>
								<option :value="50">50 {{ __('Marks') }}</option>
								<option :value="40">40 {{ __('Marks') }}</option>
								<option :value="100">100 {{ __('Marks') }}</option>
								<option :value="25">25 {{ __('Marks (Unit Test)') }}</option>
							</select>
						</div>
						<div>
							<label class="block text-xs font-medium text-ink-gray-7 mb-1">{{ __('Duration') }}</label>
							<input
								type="text"
								v-model="form.duration"
								class="w-full rounded-md border border-gray-300 px-3 py-1.5 text-sm dark:bg-gray-800 dark:border-gray-700"
								placeholder="3 Hours"
							/>
						</div>
						<div>
							<label class="block text-xs font-medium text-ink-gray-7 mb-1">{{ __('Examination Date') }}</label>
							<input
								type="date"
								v-model="form.examination_date"
								class="w-full rounded-md border border-gray-300 px-3 py-1.5 text-sm dark:bg-gray-800 dark:border-gray-700"
							/>
						</div>
					</div>

					<!-- Mode Selection -->
					<div class="rounded-lg border p-3.5 bg-gray-50/50 dark:bg-gray-900/50">
						<label class="block text-xs font-semibold text-ink-gray-7 uppercase tracking-wider mb-2">
							{{ __('Content Generation Mode') }}
						</label>
						<div class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
							<label
								class="flex items-start gap-2.5 p-3 rounded-lg border cursor-pointer bg-white dark:bg-gray-800"
								:class="form.mode === 'Chapter-Based' ? 'border-violet-600 ring-1 ring-violet-500' : ''"
							>
								<input type="radio" v-model="form.mode" value="Chapter-Based" class="mt-0.5 text-violet-600" />
								<div>
									<div class="font-bold text-ink-gray-9">{{ __('Mode 1: Chapter-Based Generation') }}</div>
									<div class="text-ink-gray-6 mt-0.5">{{ __('Generates strictly from syllabus lessons in the LMS.') }}</div>
								</div>
							</label>

							<label
								class="flex items-start gap-2.5 p-3 rounded-lg border cursor-pointer bg-white dark:bg-gray-800"
								:class="form.mode === 'Extended Knowledge' ? 'border-violet-600 ring-1 ring-violet-500' : ''"
							>
								<input type="radio" v-model="form.mode" value="Extended Knowledge" class="mt-0.5 text-violet-600" />
								<div>
									<div class="font-bold text-ink-gray-9">{{ __('Mode 2: Extended Knowledge Generation') }}</div>
									<div class="text-ink-gray-6 mt-0.5">{{ __('Anchored in chapters, enriched with curriculum domain knowledge.') }}</div>
								</div>
							</label>
						</div>
					</div>

					<!-- Course & Chapter Selection -->
					<div class="space-y-2">
						<label class="block text-xs font-medium text-ink-gray-7">{{ __('Select Source Course') }}</label>
						<select
							v-model="form.course"
							class="w-full rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm dark:bg-gray-800 dark:border-gray-700"
							@change="onCourseSelect"
						>
							<option value="">{{ __('-- Select Course --') }}</option>
							<option v-for="c in coursesList" :key="c.name" :value="c.name">
								{{ c.title || c.name }}
							</option>
						</select>

						<!-- Chapters Checklist -->
						<div v-if="chaptersList.length" class="mt-2 space-y-1">
							<label class="block text-xs font-medium text-ink-gray-7">{{ __('Select Chapters to Include:') }}</label>
							<div class="max-h-36 overflow-y-auto rounded-lg border p-2 space-y-1 bg-white dark:bg-gray-800">
								<label
									v-for="ch in chaptersList"
									:key="ch.name"
									class="flex items-center gap-2 p-1.5 rounded hover:bg-gray-50 text-xs cursor-pointer"
								>
									<input
										type="checkbox"
										v-model="form.selected_chapters"
										:value="ch.name"
										class="rounded text-violet-600"
									/>
									<span>{{ ch.title || ch.name }}</span>
								</label>
							</div>
						</div>
					</div>

					<!-- Difficulty Distribution -->
					<div>
						<div class="flex items-center justify-between mb-2">
							<label class="text-xs font-semibold text-ink-gray-7 uppercase tracking-wider">
								{{ __('Difficulty Distribution (%)') }}
							</label>
							<span
								class="text-xs font-bold"
								:class="difficultyTotal === 100 ? 'text-emerald-600' : 'text-red-600'"
							>
								{{ __('Total:') }} {{ difficultyTotal }}% ({{ difficultyTotal === 100 ? __('Balanced') : __('Must equal 100%') }})
							</span>
						</div>
						<div class="grid grid-cols-3 gap-3">
							<div>
								<label class="block text-xs text-ink-gray-6 mb-1">{{ __('Easy (%)') }}</label>
								<input
									type="number"
									v-model.number="form.difficulty_distribution.easy"
									min="0"
									max="100"
									class="w-full rounded border px-2 py-1 text-xs text-center"
								/>
							</div>
							<div>
								<label class="block text-xs text-ink-gray-6 mb-1">{{ __('Medium (%)') }}</label>
								<input
									type="number"
									v-model.number="form.difficulty_distribution.medium"
									min="0"
									max="100"
									class="w-full rounded border px-2 py-1 text-xs text-center"
								/>
							</div>
							<div>
								<label class="block text-xs text-ink-gray-6 mb-1">{{ __('Hard (%)') }}</label>
								<input
									type="number"
									v-model.number="form.difficulty_distribution.hard"
									min="0"
									max="100"
									class="w-full rounded border px-2 py-1 text-xs text-center"
								/>
							</div>
						</div>
					</div>

					<!-- Generate Action Button -->
					<div class="pt-4 border-t flex items-center justify-between">
						<div class="text-xs text-ink-gray-5">
							{{ __('Total Marks to generate:') }} <strong class="text-violet-700 font-bold">{{ form.total_marks }} Marks</strong>
						</div>
						<Button
							variant="solid"
							theme="violet"
							size="lg"
							:loading="generating"
							:disabled="difficultyTotal !== 100"
							@click="generatePaper"
						>
							<template #prefix><span class="lucide-sparkles size-4"></span></template>
							{{ __('Generate Question Paper') }}
						</Button>
					</div>
				</div>

				<!-- Section Blueprint Overview (Col 3) -->
				<div class="space-y-4">
					<div class="rounded-xl border bg-surface-base p-5 shadow-sm space-y-4">
						<div class="flex items-center justify-between border-b pb-2">
							<h3 class="text-sm font-semibold text-ink-gray-9 flex items-center gap-2">
								<span class="lucide-layers size-4 text-violet-600"></span>
								{{ __('Examination Blueprint') }}
							</h3>
							<Badge variant="subtle" theme="violet">{{ form.sections.length }} {{ __('Sections') }}</Badge>
						</div>

						<div class="space-y-2 text-xs">
							<div
								v-for="(sec, idx) in form.sections"
								:key="idx"
								class="p-2.5 rounded-lg border bg-gray-50/60 dark:bg-gray-800/60 space-y-1"
							>
								<div class="flex items-center justify-between font-bold text-ink-gray-8">
									<span>{{ sec.name }}</span>
									<span class="text-violet-700">{{ sec.total }} Marks</span>
								</div>
								<div class="text-ink-gray-6">{{ sec.title }}</div>
								<div class="text-ink-gray-5">
									{{ sec.count }} Qs &times; {{ sec.marks_each }} Mark{{ sec.marks_each > 1 ? 's' : '' }} ({{ sec.type }})
								</div>
							</div>
						</div>

						<div class="pt-2 border-t flex items-center justify-between text-xs font-bold text-ink-gray-9">
							<span>{{ __('Calculated Target Sum:') }}</span>
							<span class="text-sm text-violet-700">{{ calculatedBlueprintTotal }} Marks</span>
						</div>
					</div>

					<!-- Feature checklist -->
					<div class="rounded-xl border bg-surface-base p-5 shadow-sm text-xs space-y-2.5 text-ink-gray-7">
						<div class="font-bold text-ink-gray-9 uppercase tracking-wider text-[11px]">{{ __('Included with Paper:') }}</div>
						<div class="flex items-center gap-2 text-emerald-700"><span class="lucide-check size-3.5"></span> {{ __('Izensphere branding & school header') }}</div>
						<div class="flex items-center gap-2 text-emerald-700"><span class="lucide-check size-3.5"></span> {{ __('Continuous question numbering (Q1 to Qn)') }}</div>
						<div class="flex items-center gap-2 text-emerald-700"><span class="lucide-check size-3.5"></span> {{ __('Internal choice questions ("OR") for high marks') }}</div>
						<div class="flex items-center gap-2 text-emerald-700"><span class="lucide-check size-3.5"></span> {{ __('Independent Answer Key PDF') }}</div>
						<div class="flex items-center gap-2 text-emerald-700"><span class="lucide-check size-3.5"></span> {{ __('Detailed Step-by-Step Solutions PDF') }}</div>
						<div class="flex items-center gap-2 text-emerald-700"><span class="lucide-check size-3.5"></span> {{ __('Strict total marks mathematical validation') }}</div>
					</div>
				</div>
			</div>

			<!-- VIEW 2: PREVIEW & VALIDATION -->
			<div v-else-if="activeView === 'preview' && generatedPaper" class="space-y-6">
				<!-- Validation Status Banner -->
				<div
					v-if="generatedPaper.validation"
					class="rounded-xl border p-4 text-xs space-y-2"
					:class="generatedPaper.validation.is_valid ? 'border-emerald-300 bg-emerald-50 text-emerald-900' : 'border-red-300 bg-red-50 text-red-900'"
				>
					<div class="flex items-center justify-between">
						<div class="flex items-center gap-2 font-bold text-sm">
							<span :class="generatedPaper.validation.is_valid ? 'lucide-check-circle text-emerald-600' : 'lucide-alert-circle text-red-600'" class="size-5"></span>
							{{ generatedPaper.validation.is_valid ? __('Paper Validation Passed! Perfectly Balanced.') : __('Validation Errors Detected!') }}
						</div>
						<Badge :theme="generatedPaper.validation.is_valid ? 'green' : 'red'">
							{{ generatedPaper.validation.calculated_total_marks }} / {{ generatedPaper.validation.target_total_marks }} {{ __('Marks') }}
						</Badge>
					</div>

					<div v-if="generatedPaper.validation.errors?.length" class="text-red-700 ps-7 space-y-1">
						<div v-for="(err, eIdx) in generatedPaper.validation.errors" :key="eIdx">&bull; {{ err }}</div>
					</div>

					<div v-if="generatedPaper.validation.warnings?.length" class="text-amber-800 ps-7 space-y-1">
						<div v-for="(w, wIdx) in generatedPaper.validation.warnings" :key="wIdx">&bull; {{ w }}</div>
					</div>
				</div>

				<!-- Toolbar for Preview -->
				<div class="flex flex-wrap items-center justify-between gap-3 rounded-xl border bg-surface-base p-4 shadow-sm">
					<div class="flex items-center gap-2">
						<button
							v-for="tab in ['paper', 'answer_key', 'solutions']"
							:key="tab"
							class="px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors"
							:class="previewDocType === tab ? 'bg-violet-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'"
							@click="previewDocType = tab"
						>
							{{ tab === 'paper' ? __('1. Question Paper') : (tab === 'answer_key' ? __('2. Answer Key') : __('3. Detailed Solutions')) }}
						</button>
					</div>

					<div class="flex items-center gap-2 flex-wrap">
						<!-- PDF Downloads -->
						<Button
							variant="outline"
							size="sm"
							:loading="downloading"
							@click="downloadPDF(previewDocType)"
						>
							<template #prefix><span class="lucide-download size-3.5"></span></template>
							{{ __('Download PDF') }}
						</Button>

						<!-- Workflow Actions -->
						<Button
							variant="outline"
							size="sm"
							:loading="saving"
							@click="savePaper('Draft')"
						>
							{{ __('Save as Draft') }}
						</Button>

						<Button
							variant="subtle"
							theme="orange"
							size="sm"
							:loading="saving"
							@click="savePaper('Submitted for Approval')"
						>
							{{ __('Submit for Approval') }}
						</Button>

						<Button
							variant="solid"
							theme="green"
							size="sm"
							:loading="saving"
							@click="savePaper('Published')"
						>
							{{ __('Approve & Publish') }}
						</Button>
					</div>
				</div>

				<!-- Paper Render Container -->
				<div class="rounded-xl border bg-white p-8 shadow-md min-h-[600px] text-gray-900 space-y-6">
					<!-- School Header -->
					<div class="text-center border-b-2 border-gray-900 pb-4 space-y-1">
						<h2 class="text-xl font-bold tracking-wide uppercase">{{ generatedPaper.school_name || 'Izensphere International School' }}</h2>
						<h3 class="text-base font-semibold text-gray-800">{{ generatedPaper.title }}</h3>
						<div class="text-xs font-bold text-violet-800 uppercase tracking-widest">
							{{ previewDocType === 'paper' ? __('QUESTION PAPER') : (previewDocType === 'answer_key' ? __('OFFICIAL ANSWER KEY') : __('DETAILED SOLUTIONS & MARKING SCHEME')) }}
						</div>
					</div>

					<!-- Meta info grid -->
					<div class="grid grid-cols-3 text-xs border-b pb-3 gap-2">
						<div><strong>{{ __('Class:') }}</strong> {{ generatedPaper.class_level }}</div>
						<div><strong>{{ __('Subject:') }}</strong> {{ generatedPaper.subject }}</div>
						<div class="text-right"><strong>{{ __('Academic Year:') }}</strong> {{ generatedPaper.academic_year }}</div>
						<div><strong>{{ __('Duration:') }}</strong> {{ generatedPaper.duration }}</div>
						<div><strong>{{ __('Date:') }}</strong> {{ generatedPaper.examination_date || __('TBD') }}</div>
						<div class="text-right"><strong>{{ __('Maximum Marks:') }}</strong> {{ generatedPaper.total_marks }}</div>
					</div>

					<!-- Instructions -->
					<div v-if="generatedPaper.instructions && previewDocType === 'paper'" class="rounded border p-3 bg-gray-50 text-xs space-y-1">
						<div class="font-bold uppercase tracking-wider text-gray-800">{{ __('General Instructions:') }}</div>
						<div class="whitespace-pre-line text-gray-700">{{ generatedPaper.instructions }}</div>
					</div>

					<!-- Sections -->
					<div class="space-y-6">
						<div v-for="(sec, sIdx) in generatedPaper.sections" :key="sIdx" class="space-y-3">
							<!-- Section Banner -->
							<div class="flex items-center justify-between bg-gray-100 p-2 border-y border-gray-400 font-bold text-sm text-gray-800">
								<span>{{ sec.section_name }}: {{ sec.title }}</span>
								<span>[{{ sec.total_marks }} Marks]</span>
							</div>

							<div v-if="sec.instructions" class="text-xs italic text-gray-600 px-2">
								{{ sec.instructions }}
							</div>

							<!-- Questions in Section -->
							<div class="space-y-4 px-2">
								<div
									v-for="(q, qIdx) in sec.questions"
									:key="qIdx"
									class="space-y-2 border-b border-gray-100 pb-3"
								>
									<div class="flex items-start justify-between gap-3 text-sm">
										<div class="flex items-start gap-2">
											<span class="font-bold">Q{{ q.question_number }}.</span>
											<span class="font-medium text-gray-900">{{ q.question }}</span>
										</div>
										<span class="font-semibold text-gray-600 text-xs shrink-0">({{ q.marks }} Mark{{ q.marks > 1 ? 's' : '' }})</span>
									</div>

									<!-- Options if MCQ -->
									<div v-if="q.options && previewDocType === 'paper'" class="grid grid-cols-2 gap-2 ps-6 text-xs text-gray-700">
										<div v-for="(opt, optIdx) in q.options" :key="optIdx" class="flex items-center gap-1.5">
											<span class="font-semibold">{{ String.fromCharCode(65 + optIdx) }}.</span>
											<span>{{ opt }}</span>
										</div>
									</div>

									<!-- Internal Choice "OR" -->
									<div v-if="q.internal_choice_question" class="ps-6 space-y-1">
										<div class="text-center font-bold text-xs text-gray-500 py-1">--- OR ---</div>
										<div class="text-sm italic text-gray-800">{{ q.internal_choice_question.question }}</div>
									</div>

									<!-- Answer Key Mode Snippet -->
									<div v-if="previewDocType === 'answer_key'" class="ps-6 rounded bg-emerald-50 p-2 text-xs text-emerald-900 border border-emerald-200">
										<strong>{{ __('Answer:') }}</strong> {{ q.correct_answer || q.solution }}
									</div>

									<!-- Solutions Mode Snippet -->
									<div v-if="previewDocType === 'solutions'" class="ps-6 rounded bg-sky-50 p-2.5 text-xs text-sky-950 border border-sky-200 space-y-1">
										<div><strong class="text-sky-800">{{ __('Answer:') }}</strong> {{ q.correct_answer }}</div>
										<div><strong class="text-sky-800">{{ __('Step-by-Step Marking Solution:') }}</strong></div>
										<div class="whitespace-pre-line text-gray-700">{{ q.solution }}</div>
									</div>
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>

			<!-- VIEW 3: SAVED PAPERS LIST -->
			<div v-else-if="activeView === 'saved_list'" class="space-y-4">
				<div class="flex items-center justify-between">
					<h2 class="text-base font-semibold text-ink-gray-9">{{ __('Saved Examination Question Papers') }}</h2>
					<Button size="sm" variant="solid" theme="violet" @click="activeView = 'generator'">
						<template #prefix><span class="lucide-plus size-4"></span></template>
						{{ __('Create New Paper') }}
					</Button>
				</div>

				<div v-if="loadingSaved" class="text-center py-12 text-gray-400">
					{{ __('Loading saved question papers...') }}
				</div>

				<div v-else-if="!savedPapersList.length" class="rounded-xl border p-12 text-center text-gray-500 bg-surface-base">
					{{ __('No question papers found. Generate your first paper using the AI generator above!') }}
				</div>

				<div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
					<div
						v-for="p in savedPapersList"
						:key="p.name"
						class="rounded-xl border bg-surface-base p-4 shadow-sm hover:border-violet-300 transition-colors space-y-3"
					>
						<div class="flex items-start justify-between gap-2">
							<div>
								<div class="text-xs font-bold text-violet-700 uppercase">{{ p.subject }} &bull; {{ p.class_level }}</div>
								<h3 class="font-bold text-ink-gray-9 text-sm line-clamp-1 mt-0.5">{{ p.title }}</h3>
							</div>
							<Badge
								:theme="p.approval_status === 'Published' ? 'green' : (p.approval_status === 'Principal Approved' ? 'blue' : (p.approval_status === 'Submitted for Approval' ? 'orange' : 'gray'))"
								variant="subtle"
								size="sm"
							>
								{{ p.approval_status }}
							</Badge>
						</div>

						<div class="grid grid-cols-2 text-xs text-ink-gray-6 gap-1 border-t pt-2">
							<div>{{ __('Marks:') }} <strong>{{ p.total_marks }}</strong></div>
							<div>{{ __('Duration:') }} <strong>{{ p.duration }}</strong></div>
							<div>{{ __('Type:') }} <strong>{{ p.examination_type }}</strong></div>
							<div>{{ __('Year:') }} <strong>{{ p.academic_year }}</strong></div>
						</div>

						<div class="flex items-center justify-between border-t pt-3 gap-2">
							<Button size="sm" variant="ghost" @click="openSavedPaper(p.name)">
								{{ __('View & Edit') }}
							</Button>
							<div class="flex items-center gap-1">
								<Button size="sm" variant="outline" @click="downloadSavedPaperPDF(p.name, 'question_paper')">
									{{ __('Paper') }}
								</Button>
								<Button size="sm" variant="outline" @click="downloadSavedPaperPDF(p.name, 'solutions')">
									{{ __('Solutions') }}
								</Button>
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import PageHeader from '@/components/Layouts/PageHeader.vue'
import { Button, Badge, toast, call } from 'frappe-ui'

const route = useRoute()

const activeView = ref('generator')
const previewDocType = ref('paper')
const generating = ref(false)
const saving = ref(false)
const downloading = ref(false)
const loadingSaved = ref(false)

const coursesList = ref([])
const chaptersList = ref([])
const savedPapersList = ref([])
const generatedPaper = ref(null)

const form = reactive({
	academic_year: '2026-27',
	class_level: 'Class 10',
	subject: 'Science',
	examination_type: 'Midterm Examination',
	course: '',
	selected_chapters: [],
	total_marks: 80,
	duration: '3 Hours',
	examination_date: '',
	language: 'English',
	mode: 'Chapter-Based',
	difficulty_distribution: {
		easy: 30,
		medium: 40,
		hard: 30,
	},
	sections: [
		{ name: 'Section A', title: 'Multiple Choice Questions', type: 'MCQ', count: 20, marks_each: 1, total: 20 },
		{ name: 'Section B', title: 'Very Short Answer Questions', type: 'Short Answer', count: 6, marks_each: 2, total: 12 },
		{ name: 'Section C', title: 'Short Answer Questions', type: 'Short Answer', count: 7, marks_each: 3, total: 21 },
		{ name: 'Section D', title: 'Long Answer Questions (Internal Choice)', type: 'Long Answer', count: 3, marks_each: 5, total: 15 },
		{ name: 'Section E', title: 'Case Study / Competency Questions', type: 'Case Study / Assertion-Reason', count: 3, marks_each: 4, total: 12 },
	],
})

const difficultyTotal = computed(() => {
	const d = form.difficulty_distribution
	return (Number(d.easy) || 0) + (Number(d.medium) || 0) + (Number(d.hard) || 0)
})

const calculatedBlueprintTotal = computed(() => {
	return form.sections.reduce((sum, s) => sum + (Number(s.total) || 0), 0)
})

onMounted(async () => {
	await loadCourses()
	await loadSavedPapers()
	if (route.query.course) {
		form.course = route.query.course
		await onCourseSelect()
	} else if (route.query.batch) {
		try {
			const b = await call('frappe.client.get', { doctype: 'LMS Batch', name: route.query.batch })
			if (b) {
				form.class_level = b.title || form.class_level
				if (b.courses && b.courses.length > 0) {
					form.course = b.courses[0].course
					await onCourseSelect()
				}
			}
		} catch (e) {
			console.error(e)
		}
	}
})

async function loadCourses() {
	try {
		const res = await call('frappe.client.get_list', {
			doctype: 'LMS Course',
			fields: ['name', 'title'],
			limit_page_length: 100,
		})
		coursesList.value = res || []
	} catch (e) {
		console.error(e)
	}
}

async function onCourseSelect() {
	chaptersList.value = []
	form.selected_chapters = []
	if (!form.course) return
	try {
		const res = await call('frappe.client.get_list', {
			doctype: 'Course Chapter',
			filters: { course: form.course },
			fields: ['name', 'title'],
			order_by: 'idx asc',
		})
		chaptersList.value = res || []
		// Pre-select all chapters
		form.selected_chapters = (res || []).map((ch) => ch.name)
	} catch (e) {
		console.error(e)
	}
}

function onTotalMarksChange() {
	if (form.total_marks === 100) {
		form.sections = [
			{ name: 'Section A', title: 'Multiple Choice Questions', type: 'MCQ', count: 20, marks_each: 1, total: 20 },
			{ name: 'Section B', title: 'Fill in the Blanks / Very Short Answers', type: 'Fill in the Blanks', count: 10, marks_each: 1, total: 10 },
			{ name: 'Section C', title: 'Short Answer Questions', type: 'Short Answer', count: 10, marks_each: 3, total: 30 },
			{ name: 'Section D', title: 'Long Answer / Descriptive Questions', type: 'Long Answer', count: 4, marks_each: 5, total: 20 },
			{ name: 'Section E', title: 'Application-Based / Higher Order Thinking Questions', type: 'Application-Based', count: 4, marks_each: 5, total: 20 },
		]
	} else if (form.total_marks === 80) {
		form.sections = [
			{ name: 'Section A', title: 'Multiple Choice Questions', type: 'MCQ', count: 20, marks_each: 1, total: 20 },
			{ name: 'Section B', title: 'Very Short Answer Questions', type: 'Short Answer', count: 6, marks_each: 2, total: 12 },
			{ name: 'Section C', title: 'Short Answer Questions', type: 'Short Answer', count: 7, marks_each: 3, total: 21 },
			{ name: 'Section D', title: 'Long Answer Questions (Internal Choice)', type: 'Long Answer', count: 3, marks_each: 5, total: 15 },
			{ name: 'Section E', title: 'Application-Based / Higher Order Thinking Questions', type: 'Application-Based', count: 3, marks_each: 4, total: 12 },
		]
	} else if (form.total_marks === 50) {
		form.sections = [
			{ name: 'Section A', title: 'Objective Type', type: 'MCQ', count: 10, marks_each: 1, total: 10 },
			{ name: 'Section B', title: 'Short Answer', type: 'Short Answer', count: 5, marks_each: 2, total: 10 },
			{ name: 'Section C', title: 'Medium Answer', type: 'Short Answer', count: 5, marks_each: 3, total: 15 },
			{ name: 'Section D', title: 'Long Answer (with Internal Choice)', type: 'Long Answer', count: 3, marks_each: 5, total: 15 },
		]
	} else {
		form.sections = [
			{ name: 'Section A', title: 'Objective Type', type: 'MCQ', count: Math.floor(form.total_marks / 2), marks_each: 1, total: Math.floor(form.total_marks / 2) },
			{ name: 'Section B', title: 'Subjective Questions', type: 'Short Answer', count: Math.ceil(form.total_marks / 4), marks_each: 2, total: Math.ceil(form.total_marks / 4) * 2 },
		]
	}
}

async function generatePaper() {
	if (difficultyTotal.value !== 100) {
		toast.error(__('Difficulty distribution must equal 100%'))
		return
	}

	generating.value = true
	try {
		const res = await call('lms.lms.ai.ai_assessment_api.api_generate_question_paper', {
			academic_year: form.academic_year,
			class_level: form.class_level,
			subject: form.subject,
			examination_type: form.examination_type,
			course: form.course || undefined,
			selected_chapters: JSON.stringify(form.selected_chapters),
			total_marks: form.total_marks,
			duration: form.duration,
			examination_date: form.examination_date || undefined,
			language: form.language,
			difficulty_distribution: JSON.stringify(form.difficulty_distribution),
			sections_config: JSON.stringify(form.sections),
			mode: form.mode,
		})

		if (res && res.sections) {
			generatedPaper.value = res
			activeView.value = 'preview'
			toast.success(__('Question paper generated successfully!'))
		} else {
			toast.error(__('Failed to generate question paper.'))
		}
	} catch (e) {
		toast.error(e.message || __('Error generating question paper.'))
	} finally {
		generating.value = false
	}
}

async function savePaper(action = 'Draft') {
	if (!generatedPaper.value) return
	saving.value = true
	try {
		const res = await call('lms.lms.ai.ai_assessment_api.api_save_question_paper', {
			paper_data: JSON.stringify(generatedPaper.value),
			action: action,
		})
		if (res && res.name) {
			generatedPaper.value.name = res.name
			generatedPaper.value.approval_status = res.approval_status
			toast.success(__('Paper saved as {0} ({1})!').format(res.approval_status, res.name))
			await loadSavedPapers()
		}
	} catch (e) {
		toast.error(e.message || __('Failed to save question paper.'))
	} finally {
		saving.value = false
	}
}

async function downloadPDF(docType = 'question_paper') {
	if (!generatedPaper.value?.name) {
		// Save first as Draft
		await savePaper('Draft')
	}
	if (!generatedPaper.value?.name) return
	downloadSavedPaperPDF(generatedPaper.value.name, docType)
}

function downloadSavedPaperPDF(paperName, docType = 'question_paper') {
	const url = `/api/method/lms.lms.ai.ai_assessment_api.api_download_paper_pdf?name=${encodeURIComponent(paperName)}&doc_type=${encodeURIComponent(docType)}`
	window.open(url, '_blank')
}

async function loadSavedPapers() {
	loadingSaved.value = true
	try {
		const res = await call('lms.lms.ai.ai_assessment_api.api_list_question_papers')
		savedPapersList.value = res || []
	} catch (e) {
		console.error(e)
	} finally {
		loadingSaved.value = false
	}
}

async function openSavedPaper(paperName) {
	try {
		const res = await call('lms.lms.ai.ai_assessment_api.api_get_question_paper', {
			name: paperName,
		})
		if (res) {
			generatedPaper.value = res
			activeView.value = 'preview'
		}
	} catch (e) {
		toast.error(__('Failed to load question paper details.'))
	}
}
</script>

