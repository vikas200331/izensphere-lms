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

					<!-- Batch & Course Curriculum Selection -->
					<div class="space-y-4 rounded-lg border p-3.5 bg-gray-50/50 dark:bg-gray-900/50">
						<div class="flex items-center justify-between">
							<label class="block text-xs font-semibold text-ink-gray-7 uppercase tracking-wider">
								{{ __('Curriculum Scope: Batch & Course Content') }}
							</label>
							<span class="text-[11px] text-violet-700 font-medium">
								{{ __('Extracts batch schedule, live classes, lessons & notes') }}
							</span>
						</div>

						<div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
							<!-- Batch Selection -->
							<div>
								<label class="block text-xs font-medium text-ink-gray-7 mb-1">
									{{ __('Select Batch / Cohort') }}
									<span class="text-xs text-ink-gray-5 font-normal">({{ __('Optional') }})</span>
								</label>
								<select
									v-model="form.batch"
									class="w-full rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm dark:bg-gray-800 dark:border-gray-700"
									@change="onBatchSelect"
								>
									<option value="">{{ __('-- Direct Course Examination (No Batch) --') }}</option>
									<option v-for="b in batchesList" :key="b.name" :value="b.name">
										{{ b.title || b.name }} {{ b.category ? `(${b.category})` : '' }}
									</option>
								</select>
							</div>

							<!-- Course Selection -->
							<div>
								<label class="block text-xs font-medium text-ink-gray-7 mb-1">
									{{ __('Select Course') }} *
								</label>
								<select
									v-model="form.course"
									class="w-full rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm dark:bg-gray-800 dark:border-gray-700"
									@change="onCourseSelect"
								>
									<option value="">{{ __('-- Select Course --') }}</option>
									<option
										v-for="c in (batchCoursesList.length ? batchCoursesList : coursesList)"
										:key="c.course || c.name"
										:value="c.course || c.name"
									>
										{{ c.title || c.name }}
									</option>
								</select>
							</div>
						</div>

						<!-- Chapters Checklist -->
						<div v-if="chaptersList.length" class="space-y-1 pt-1">
							<div class="flex items-center justify-between text-xs text-ink-gray-7">
								<span class="font-medium">{{ __('Select Chapters to Include:') }}</span>
								<div class="flex gap-2 text-[11px]">
									<button type="button" class="text-violet-600 hover:underline" @click="selectAllChapters">{{ __('Select All') }}</button>
									<span class="text-gray-300">|</span>
									<button type="button" class="text-gray-500 hover:underline" @click="clearChapters">{{ __('Clear') }}</button>
								</div>
							</div>
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
										@change="updateContentPreview"
									/>
									<span>{{ ch.title || ch.name }}</span>
								</label>
							</div>
						</div>

						<!-- Live Educational Content Metrics Indicator -->
						<div v-if="contentStats" class="rounded-md border border-emerald-200 bg-emerald-50/60 p-2.5 text-xs text-emerald-900 flex items-center justify-between">
							<div class="flex items-center gap-2">
								<span class="lucide-check-circle size-4 text-emerald-600"></span>
								<div>
									<span class="font-semibold">{{ __('Content Ready:') }}</span>
									<span class="ml-1">{{ contentStats.word_count }} {{ __('words') }} ({{ contentStats.char_count }} {{ __('characters') }}, ~{{ contentStats.estimated_tokens }} {{ __('tokens') }})</span>
								</div>
							</div>
							<Badge variant="subtle" theme="green">{{ form.batch ? __('Batch + Course Content') : __('Course Content') }}</Badge>
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
				<!-- Changes Requested by Principal Banner -->
				<div
					v-if="generatedPaper.approval_status === 'Rejected'"
					class="rounded-xl border border-red-300 bg-red-50 p-4 text-xs text-red-900 space-y-1.5 shadow-sm"
				>
					<div class="flex items-center gap-2 font-bold text-sm text-red-800">
						<span class="lucide-alert-octagon size-4 text-red-600"></span>
						{{ __('Changes Requested by Principal') }}
					</div>
					<p v-if="generatedPaper.rejection_reason" class="text-red-900 ps-6 text-xs font-semibold">
						"{{ generatedPaper.rejection_reason }}"
					</p>
					<p class="text-red-700 ps-6 text-[11px]">
						{{ __('Please edit the paper content, re-validate marks, and click Resubmit for Approval.') }}
					</p>
				</div>

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
					<div class="flex items-center gap-2 flex-wrap">
						<!-- Toggle Edit Mode / Preview Mode -->
						<Button
							:variant="isEditMode ? 'solid' : 'outline'"
							theme="violet"
							size="sm"
							@click="isEditMode = !isEditMode"
						>
							<template #prefix>
								<span :class="isEditMode ? 'lucide-eye size-3.5' : 'lucide-edit-3 size-3.5'"></span>
							</template>
							{{ isEditMode ? __('Preview Paper') : __('Edit Paper') }}
						</Button>

						<div v-if="!isEditMode" class="flex items-center gap-1 border-l pl-2">
							<button
								v-for="tab in ['paper', 'answer_key', 'solutions']"
								:key="tab"
								class="px-2.5 py-1.5 rounded-lg text-xs font-semibold transition-colors"
								:class="previewDocType === tab ? 'bg-violet-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'"
								@click="previewDocType = tab"
							>
								{{ tab === 'paper' ? __('1. Question Paper') : (tab === 'answer_key' ? __('2. Answer Key') : __('3. Detailed Solutions')) }}
							</button>
						</div>
					</div>

					<div class="flex items-center gap-2 flex-wrap">
						<!-- Status Indicator Badge -->
						<Badge
							v-if="generatedPaper?.approval_status"
							:theme="generatedPaper.approval_status === 'Published' ? 'green' : (generatedPaper.approval_status === 'Principal Approved' ? 'blue' : (generatedPaper.approval_status === 'Submitted for Approval' ? 'orange' : (generatedPaper.approval_status === 'Rejected' ? 'red' : 'gray')))"
							variant="subtle"
							size="md"
							class="font-semibold"
						>
							{{ generatedPaper.approval_status === 'Published' ? '✓ ' + __('Published to Students') : generatedPaper.approval_status }}
						</Badge>

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

						<!-- Save as Draft / Save Changes -->
						<Button
							v-if="generatedPaper?.approval_status !== 'Published'"
							variant="outline"
							size="sm"
							:loading="saving"
							@click="savePaper('Draft')"
						>
							<template #prefix><span class="lucide-save size-3.5"></span></template>
							{{ isEditMode ? __('Save Changes') : __('Save as Draft') }}
						</Button>

						<!-- Submit for Approval (Shown when in Draft or Rejected; disabled when already Submitted; hidden when Published/Principal Approved) -->
						<Button
							v-if="generatedPaper?.approval_status !== 'Published' && generatedPaper?.approval_status !== 'Principal Approved'"
							variant="subtle"
							:theme="generatedPaper?.approval_status === 'Rejected' ? 'red' : 'orange'"
							size="sm"
							:disabled="generatedPaper?.approval_status === 'Submitted for Approval'"
							:loading="saving"
							@click="savePaper('Submitted for Approval')"
						>
							<template #prefix>
								<span v-if="generatedPaper?.approval_status === 'Submitted for Approval'" class="lucide-check size-3.5 text-orange-600"></span>
								<span v-else-if="generatedPaper?.approval_status === 'Rejected'" class="lucide-rotate-cw size-3.5 text-red-600"></span>
							</template>
							{{ generatedPaper?.approval_status === 'Submitted for Approval' ? __('Submitted for Approval') : (generatedPaper?.approval_status === 'Rejected' ? __('Resubmit for Approval') : __('Submit for Approval')) }}
						</Button>

						<!-- Approve & Publish: Disabled when already Published; Active otherwise -->
						<Button
							v-if="generatedPaper?.approval_status === 'Published'"
							variant="solid"
							theme="green"
							size="sm"
							:disabled="true"
						>
							<template #prefix><span class="lucide-check-circle size-3.5 text-white"></span></template>
							{{ __('Published') }}
						</Button>

						<Button
							v-else
							variant="solid"
							theme="green"
							size="sm"
							:loading="saving"
							@click="savePaper('Published')"
						>
							<template #prefix><span class="lucide-send size-3.5"></span></template>
							{{ __('Approve & Publish') }}
						</Button>

						<!-- Unpublish to Draft (Available only when paper is Published) -->
						<Button
							v-if="generatedPaper?.approval_status === 'Published'"
							variant="outline"
							theme="gray"
							size="sm"
							:loading="saving"
							@click="savePaper('Draft')"
						>
							{{ __('Unpublish to Draft') }}
						</Button>

						<!-- Delete Paper -->
						<Button
							variant="ghost"
							theme="red"
							size="sm"
							:loading="deleting"
							@click="deleteCurrentPaper"
							:title="__('Delete Question Paper')"
						>
							<template #prefix><span class="lucide-trash-2 size-3.5 text-red-500"></span></template>
							{{ __('Delete') }}
						</Button>
					</div>
				</div>

				<!-- Paper Render Container -->
				<div class="rounded-xl border bg-white p-8 shadow-md min-h-[600px] text-gray-900 space-y-6">
					<!-- Edit Mode Banner -->
					<div v-if="isEditMode" class="rounded-xl border border-violet-200 bg-violet-50/80 p-3.5 text-xs flex items-center justify-between gap-3 shadow-2xs">
						<div class="flex items-center gap-2.5">
							<span class="lucide-edit-3 size-4 text-violet-600 shrink-0"></span>
							<div>
								<span class="font-bold text-violet-950">{{ __('Edit Mode Active:') }}</span>
								<span class="text-violet-800 ml-1">{{ __('You can edit the paper title, school name, instructions, sections, questions, marks, options, and model solutions. Continuous numbering and totals auto-recalculate.') }}</span>
							</div>
						</div>
						<div class="flex items-center gap-2 font-mono font-bold text-violet-800 bg-white px-3 py-1 rounded-lg border border-violet-200 shadow-2xs shrink-0">
							<span>{{ __('Total:') }} {{ generatedPaper.total_marks }} Marks</span>
						</div>
					</div>

					<!-- School Header & Title -->
					<div v-if="isEditMode" class="border-b-2 border-violet-300 pb-4 space-y-3">
						<div class="grid grid-cols-1 md:grid-cols-2 gap-3">
							<div>
								<label class="text-[11px] font-bold uppercase tracking-wider text-gray-600">{{ __('School / Institution Name') }}</label>
								<input
									v-model="generatedPaper.school_name"
									class="w-full mt-1 font-bold text-sm border rounded-lg px-3 py-1.5 bg-white border-gray-300 focus:border-violet-500"
									placeholder="IZENSPHERE INTERNATIONAL SCHOOL"
								/>
							</div>
							<div>
								<label class="text-[11px] font-bold uppercase tracking-wider text-gray-600">{{ __('Examination Title') }}</label>
								<input
									v-model="generatedPaper.title"
									class="w-full mt-1 font-bold text-sm border rounded-lg px-3 py-1.5 bg-white border-gray-300 focus:border-violet-500"
									placeholder="Midterm Examination"
								/>
							</div>
						</div>
					</div>
					<div v-else class="text-center border-b-2 border-gray-900 pb-4 space-y-1">
						<h2 class="text-xl font-bold tracking-wide uppercase">{{ generatedPaper.school_name || 'Izensphere International School' }}</h2>
						<h3 class="text-base font-semibold text-gray-800">{{ generatedPaper.title }}</h3>
						<div class="text-xs font-bold text-violet-800 uppercase tracking-widest">
							{{ previewDocType === 'paper' ? __('QUESTION PAPER') : (previewDocType === 'answer_key' ? __('OFFICIAL ANSWER KEY') : __('DETAILED SOLUTIONS & MARKING SCHEME')) }}
						</div>
					</div>

					<!-- Meta info grid -->
					<div v-if="isEditMode" class="grid grid-cols-2 md:grid-cols-3 gap-3 text-xs border-b pb-4 bg-gray-50/70 p-3 rounded-lg border">
						<div>
							<label class="font-bold text-gray-600 block">{{ __('Class:') }}</label>
							<input v-model="generatedPaper.class_level" class="w-full mt-1 border rounded px-2 py-1 bg-white text-xs" />
						</div>
						<div>
							<label class="font-bold text-gray-600 block">{{ __('Subject:') }}</label>
							<input v-model="generatedPaper.subject" class="w-full mt-1 border rounded px-2 py-1 bg-white text-xs" />
						</div>
						<div>
							<label class="font-bold text-gray-600 block">{{ __('Academic Year:') }}</label>
							<input v-model="generatedPaper.academic_year" class="w-full mt-1 border rounded px-2 py-1 bg-white text-xs" />
						</div>
						<div>
							<label class="font-bold text-gray-600 block">{{ __('Duration:') }}</label>
							<input v-model="generatedPaper.duration" class="w-full mt-1 border rounded px-2 py-1 bg-white text-xs" />
						</div>
						<div>
							<label class="font-bold text-gray-600 block">{{ __('Date:') }}</label>
							<input v-model="generatedPaper.examination_date" type="date" class="w-full mt-1 border rounded px-2 py-1 bg-white text-xs" />
						</div>
						<div>
							<label class="font-bold text-gray-600 block">{{ __('Total Marks (Auto-Calculated):') }}</label>
							<input :value="generatedPaper.total_marks" readonly disabled class="w-full mt-1 border rounded px-2 py-1 bg-gray-100 font-bold text-xs text-violet-800" />
						</div>
					</div>
					<div v-else class="grid grid-cols-3 text-xs border-b pb-3 gap-2">
						<div><strong>{{ __('Class:') }}</strong> {{ generatedPaper.class_level }}</div>
						<div><strong>{{ __('Subject:') }}</strong> {{ generatedPaper.subject }}</div>
						<div class="text-right"><strong>{{ __('Academic Year:') }}</strong> {{ generatedPaper.academic_year }}</div>
						<div><strong>{{ __('Duration:') }}</strong> {{ generatedPaper.duration }}</div>
						<div><strong>{{ __('Date:') }}</strong> {{ generatedPaper.examination_date || __('TBD') }}</div>
						<div class="text-right"><strong>{{ __('Maximum Marks:') }}</strong> {{ generatedPaper.total_marks }}</div>
					</div>

					<!-- Instructions -->
					<div v-if="isEditMode" class="space-y-1">
						<label class="font-bold text-xs uppercase tracking-wider text-gray-700">{{ __('General Instructions (one per line):') }}</label>
						<textarea
							v-model="generatedPaper.instructions"
							rows="3"
							class="w-full border rounded-lg p-2.5 text-xs bg-white border-gray-300 focus:border-violet-500 font-sans"
							placeholder="1. Answer all questions...\n2. Figures to the right indicate full marks..."
						></textarea>
					</div>
					<div v-else-if="generatedPaper.instructions && previewDocType === 'paper'" class="rounded border p-3 bg-gray-50 text-xs space-y-1">
						<div class="font-bold uppercase tracking-wider text-gray-800">{{ __('General Instructions:') }}</div>
						<div class="whitespace-pre-line text-gray-700">{{ generatedPaper.instructions }}</div>
					</div>

					<!-- SECTIONS IN EDIT MODE -->
					<div v-if="isEditMode" class="space-y-6">
						<div
							v-for="(sec, sIdx) in generatedPaper.sections"
							:key="'edit_sec_' + sIdx"
							class="space-y-3 rounded-xl border border-gray-200 bg-white p-4 shadow-2xs"
						>
							<!-- Section Header -->
							<div class="flex items-center justify-between bg-violet-50 p-2.5 rounded-lg border border-violet-200 font-bold text-sm text-gray-900 gap-2 flex-wrap">
								<div class="flex items-center gap-2 flex-1 min-w-[200px]">
									<input
										v-model="sec.section_name"
										class="w-28 font-bold text-xs bg-white border border-gray-300 rounded px-2 py-1"
										placeholder="Section Name"
									/>
									<span class="text-gray-400">:</span>
									<input
										v-model="sec.title"
										class="flex-1 font-semibold text-xs bg-white border border-gray-300 rounded px-2 py-1"
										placeholder="Section Title"
									/>
								</div>
								<div class="flex items-center gap-3">
									<span class="text-xs font-mono font-bold text-violet-800 bg-white px-2 py-1 rounded border border-violet-200">
										{{ sec.total_marks }} Marks ({{ sec.questions?.length || 0 }} Qs)
									</span>
									<Button size="xs" variant="solid" theme="violet" @click="addQuestionToSection(sIdx)">
										<template #prefix><span class="lucide-plus size-3"></span></template>
										{{ __('+ Add Question') }}
									</Button>
								</div>
							</div>

							<div>
								<input
									v-model="sec.instructions"
									class="w-full text-xs italic bg-gray-50 border border-gray-200 rounded px-2 py-1 text-gray-700"
									placeholder="Section instructions (e.g. All questions are compulsory. Each carries 1 mark.)"
								/>
							</div>

							<!-- Questions in Section -->
							<div class="space-y-4 pt-2">
								<div
									v-for="(q, qIdx) in sec.questions"
									:key="'edit_q_' + qIdx"
									class="rounded-lg border border-gray-200 bg-slate-50/50 p-3.5 space-y-3 hover:border-violet-300 transition-colors"
								>
									<!-- Top Question Row: Number, Textarea, Marks, Difficulty, Actions -->
									<div class="flex items-start gap-2.5">
										<span class="font-bold text-sm text-violet-900 pt-1 shrink-0">
											Q{{ q.question_number }}.
										</span>
										<div class="flex-1 space-y-1">
											<textarea
												v-model="q.question"
												rows="2"
												class="w-full text-sm font-medium border border-gray-300 rounded-lg p-2 bg-white focus:border-violet-500"
												placeholder="Enter question statement here..."
											></textarea>
										</div>
										<div class="flex items-center gap-2 shrink-0">
											<div class="flex flex-col items-center">
												<span class="text-[10px] uppercase font-bold text-gray-500">{{ __('Marks') }}</span>
												<input
													type="number"
													min="1"
													v-model.number="q.marks"
													@input="recalculatePaperTotals"
													class="w-14 text-center font-bold text-xs border border-gray-300 rounded p-1 bg-white"
												/>
											</div>
											<div class="flex flex-col items-center">
												<span class="text-[10px] uppercase font-bold text-gray-500">{{ __('Level') }}</span>
												<select
													v-model="q.difficulty"
													class="text-xs border border-gray-300 rounded p-1 bg-white"
												>
													<option value="Easy">Easy</option>
													<option value="Medium">Medium</option>
													<option value="Hard">Hard</option>
												</select>
											</div>
											<!-- Reorder & Delete -->
											<div class="flex items-center gap-1 pt-3">
												<button
													:disabled="qIdx === 0"
													@click="moveQuestion(sIdx, qIdx, -1)"
													class="p-1 rounded text-gray-400 hover:text-gray-700 disabled:opacity-30"
													:title="__('Move Up')"
												>
													<span class="lucide-chevron-up size-4"></span>
												</button>
												<button
													:disabled="qIdx === sec.questions.length - 1"
													@click="moveQuestion(sIdx, qIdx, 1)"
													class="p-1 rounded text-gray-400 hover:text-gray-700 disabled:opacity-30"
													:title="__('Move Down')"
												>
													<span class="lucide-chevron-down size-4"></span>
												</button>
												<button
													@click="deleteQuestion(sIdx, qIdx)"
													class="p-1 rounded text-red-400 hover:text-red-700 hover:bg-red-50"
													:title="__('Delete Question')"
												>
													<span class="lucide-trash-2 size-4"></span>
												</button>
											</div>
										</div>
									</div>

									<!-- MCQ Options (if present) -->
									<div v-if="q.options && q.options.length" class="ps-6 space-y-2">
										<div class="text-[11px] font-bold text-gray-600 flex items-center justify-between">
											<span>{{ __('Options (Select radio for correct answer):') }}</span>
											<button
												@click="addOption(q)"
												class="text-violet-600 hover:underline font-semibold flex items-center gap-1 text-[11px]"
											>
												<span class="lucide-plus size-3"></span> {{ __('Add Option') }}
											</button>
										</div>
										<div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
											<div
												v-for="(opt, optIdx) in q.options"
												:key="optIdx"
												class="flex items-center gap-1.5 bg-white p-1.5 rounded border border-gray-200"
											>
												<input
													type="radio"
													:name="'mcq_correct_' + sIdx + '_' + qIdx"
													:checked="isCorrectOption(q.correct_answer, opt, optIdx)"
													@change="setCorrectOption(q, opt, optIdx)"
													:title="__('Mark as correct answer')"
													class="text-violet-600 focus:ring-violet-500"
												/>
												<span class="font-bold text-xs text-gray-600">{{ String.fromCharCode(65 + optIdx) }}.</span>
												<input
													v-model="q.options[optIdx]"
													class="flex-1 text-xs border-0 p-0 focus:ring-0 text-gray-900"
													placeholder="Option text"
												/>
												<button
													@click="removeOption(q, optIdx)"
													class="text-gray-400 hover:text-red-500 p-0.5"
													:title="__('Remove option')"
												>
													<span class="lucide-x size-3"></span>
												</button>
											</div>
										</div>
									</div>
									<div v-else-if="sec.question_type === 'MCQ' || sec.title?.toLowerCase().includes('mcq')" class="ps-6">
										<button
											@click="addOption(q)"
											class="text-xs text-violet-600 hover:underline font-semibold flex items-center gap-1"
										>
											<span class="lucide-plus size-3"></span> {{ __('Add MCQ Options') }}
										</button>
									</div>

									<!-- Answer Key & Rubric -->
									<div class="ps-6 grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
										<div class="space-y-1">
											<label class="font-bold text-emerald-900 block text-[11px]">
												{{ __('Correct Answer / Answer Key:') }}
											</label>
											<input
												v-model="q.correct_answer"
												class="w-full border border-emerald-300 rounded p-1.5 bg-white text-xs font-medium"
												placeholder="e.g. Option A or concise answer statement"
											/>
										</div>
										<div class="space-y-1">
											<label class="font-bold text-emerald-900 block text-[11px]">
												{{ __('Marking Scheme & Detailed Rubric:') }}
											</label>
											<textarea
												v-model="q.solution"
												rows="2"
												class="w-full border border-emerald-300 rounded p-1.5 bg-white text-xs"
												placeholder="Detailed grading rubric and model solution..."
											></textarea>
										</div>
									</div>

									<!-- Internal Choice (OR Question) -->
									<div class="ps-6">
										<div v-if="q.internal_choice_question" class="rounded-lg border border-indigo-200 bg-indigo-50/50 p-3 space-y-2">
											<div class="flex items-center justify-between text-xs font-bold text-indigo-950">
												<span>--- {{ __('OR Alternative Choice Question') }} ---</span>
												<button
													@click="removeInternalChoice(q)"
													class="text-red-600 hover:underline text-[11px] font-semibold"
												>
													{{ __('Remove OR Choice') }}
												</button>
											</div>
											<textarea
												v-model="q.internal_choice_question.question"
												rows="2"
												class="w-full text-xs border border-indigo-200 rounded p-1.5 bg-white"
												placeholder="Alternative OR question statement..."
											></textarea>
											<div class="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
												<div>
													<label class="text-[10px] font-bold text-indigo-900">{{ __('OR Correct Answer:') }}</label>
													<input
														v-model="q.internal_choice_question.correct_answer"
														class="w-full text-xs border rounded p-1 bg-white"
													/>
												</div>
												<div>
													<label class="text-[10px] font-bold text-indigo-900">{{ __('OR Solution / Rubric:') }}</label>
													<input
														v-model="q.internal_choice_question.solution"
														class="w-full text-xs border rounded p-1 bg-white"
													/>
												</div>
											</div>
										</div>
										<div v-else>
											<button
												@click="addInternalChoice(q)"
												class="text-xs text-indigo-600 hover:underline font-semibold flex items-center gap-1"
											>
												<span class="lucide-git-branch size-3"></span>
												{{ __('+ Add Internal Choice ("OR" Question)') }}
											</button>
										</div>
									</div>
								</div>
							</div>
						</div>
					</div>

					<!-- SECTIONS IN PREVIEW / PRINT MODE -->
					<div v-else class="space-y-6">
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

									<!-- Options if MCQ (Student View) -->
									<div v-if="q.options && previewDocType === 'paper'" class="grid grid-cols-2 gap-2 ps-6 text-xs text-gray-700">
										<div v-for="(opt, optIdx) in q.options" :key="optIdx" class="flex items-center gap-1.5">
											<span class="font-semibold">{{ String.fromCharCode(65 + optIdx) }}.</span>
											<span>{{ opt }}</span>
										</div>
									</div>

									<!-- Options if MCQ (Answer Key View - Highlighting Correct Answer) -->
									<div v-if="q.options && previewDocType === 'answer_key'" class="grid grid-cols-1 sm:grid-cols-2 gap-2 ps-6 text-xs my-1.5">
										<div
											v-for="(opt, optIdx) in q.options"
											:key="optIdx"
											class="flex items-center gap-1.5 px-2 py-1 rounded transition-colors"
											:class="isCorrectOption(q.correct_answer, opt, optIdx) ? 'bg-emerald-100/90 font-semibold text-emerald-950 border border-emerald-300' : 'text-gray-600 bg-gray-50 border border-transparent'"
										>
											<span class="font-bold">{{ String.fromCharCode(65 + optIdx) }}.</span>
											<span class="flex-1">{{ opt }}</span>
											<span v-if="isCorrectOption(q.correct_answer, opt, optIdx)" class="font-bold text-emerald-700 ml-1">✓ Correct</span>
										</div>
									</div>

									<!-- Internal Choice "OR" (Paper View) -->
									<div v-if="q.internal_choice_question && previewDocType === 'paper'" class="ps-6 space-y-1">
										<div class="text-center font-bold text-xs text-gray-500 py-1 uppercase tracking-wide">--- OR ---</div>
										<div class="text-sm italic text-gray-800">{{ q.internal_choice_question.question }}</div>
									</div>

									<!-- Answer Key Mode: Detailed Marking Scheme According to Marks -->
									<div v-if="previewDocType === 'answer_key'" class="ps-6 space-y-2 mt-2">
										<div class="rounded-lg bg-emerald-50/80 border border-emerald-200 p-3 text-xs text-emerald-950 space-y-2 shadow-xs">
											<div class="flex items-center gap-2 flex-wrap">
												<span class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-600 text-white shadow-xs">
													{{ __('Answer Key') }}
												</span>
												<span class="font-semibold text-emerald-900">
													{{ __('Correct Answer:') }}
												</span>
												<span class="font-semibold text-emerald-950 bg-white px-2.5 py-0.5 rounded border border-emerald-300 shadow-2xs">
													{{ q.correct_answer || __('See Marking Scheme') }}
												</span>
											</div>

											<!-- Marking Scheme Breakdown according to marks -->
											<div class="border-t border-emerald-200/80 pt-2 space-y-1">
												<div class="font-bold text-emerald-900 flex items-center justify-between">
													<span>{{ __('Marking Scheme & Evaluation Rubric:') }}</span>
													<span class="text-emerald-800 text-[11px] font-semibold bg-emerald-100/70 px-2 py-0.5 rounded border border-emerald-200">
														[{{ q.marks }} Mark{{ q.marks > 1 ? 's' : '' }} Allocation]
													</span>
												</div>
												<div class="whitespace-pre-line text-emerald-950 leading-relaxed font-sans bg-white/90 p-2.5 rounded border border-emerald-200/70 text-xs">
													{{ q.answer_key_detail || q.solution }}
												</div>
											</div>
										</div>

										<!-- Internal Choice "OR" Answer Key -->
										<div v-if="q.internal_choice_question" class="rounded-lg bg-emerald-50/60 border border-emerald-200/70 p-3 text-xs text-emerald-950 space-y-2 mt-2">
											<div class="text-center font-bold text-xs text-emerald-800 py-0.5 uppercase tracking-wide">
												--- {{ __('OR Alternative Question Answer Key') }} ---
											</div>
											<div class="italic text-gray-800 font-medium">
												{{ q.internal_choice_question.question }}
											</div>
											<div class="flex items-center gap-2 flex-wrap pt-1">
												<span class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-700 text-white">
													{{ __('OR Correct Answer:') }}
												</span>
												<span class="font-semibold text-emerald-950 bg-white px-2.5 py-0.5 rounded border border-emerald-300">
													{{ q.internal_choice_question.correct_answer || __('See Rubric') }}
												</span>
											</div>
											<div class="border-t border-emerald-200/80 pt-1.5 space-y-1">
												<div class="font-bold text-emerald-900 text-[11px] flex items-center justify-between">
													<span>{{ __('OR Marking Scheme & Evaluation Rubric:') }}</span>
													<span class="text-emerald-800 text-[11px] font-semibold bg-emerald-100/70 px-2 py-0.5 rounded border border-emerald-200">
														[{{ q.internal_choice_question.marks || q.marks }} Mark{{ (q.internal_choice_question.marks || q.marks) > 1 ? 's' : '' }} Allocation]
													</span>
												</div>
												<div class="whitespace-pre-line text-emerald-950 leading-relaxed font-sans bg-white/90 p-2.5 rounded border border-emerald-200/70 text-xs">
													{{ q.internal_choice_question.answer_key_detail || q.internal_choice_question.solution }}
												</div>
											</div>
										</div>
									</div>

									<!-- Solutions Mode: Detailed Pedagogical Guide -->
									<div v-if="previewDocType === 'solutions'" class="ps-6 space-y-2 mt-2">
										<div class="rounded-lg bg-sky-50 border border-sky-200 p-3 text-xs text-sky-950 space-y-2 shadow-xs">
											<div class="flex items-center gap-2 flex-wrap">
												<span class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold bg-sky-600 text-white shadow-xs">
													{{ __('Pedagogical Solution') }}
												</span>
												<span v-if="q.correct_answer" class="font-medium text-sky-950 bg-white px-2 py-0.5 rounded border border-sky-300">
													<strong>{{ __('Correct Answer:') }}</strong> {{ q.correct_answer }}
												</span>
											</div>
											<div class="border-t border-sky-200/80 pt-2 space-y-1">
												<div class="font-bold text-sky-900">{{ __('Step-by-Step Marking Explanation:') }}</div>
												<div class="whitespace-pre-line text-slate-800 leading-relaxed font-sans bg-white/90 p-2.5 rounded border border-sky-200/70 text-xs">
													{{ q.solution }}
												</div>
											</div>
										</div>

										<!-- Internal Choice OR Solution -->
										<div v-if="q.internal_choice_question" class="rounded-lg bg-sky-50/70 border border-sky-200/70 p-3 text-xs text-sky-950 space-y-2 mt-2">
											<div class="text-center font-bold text-xs text-sky-800 py-0.5 uppercase tracking-wide">
												--- {{ __('OR Alternative Question Solution') }} ---
											</div>
											<div class="italic text-gray-800 font-medium">
												{{ q.internal_choice_question.question }}
											</div>
											<div v-if="q.internal_choice_question.correct_answer" class="flex items-center gap-2 pt-1">
												<span class="font-medium text-sky-950 bg-white px-2 py-0.5 rounded border border-sky-300">
													<strong>{{ __('OR Correct Answer:') }}</strong> {{ q.internal_choice_question.correct_answer }}
												</span>
											</div>
											<div class="border-t border-sky-200/80 pt-1.5 space-y-1">
												<div class="font-bold text-sky-900 text-[11px]">{{ __('OR Step-by-Step Marking Explanation:') }}</div>
												<div class="whitespace-pre-line text-slate-800 leading-relaxed font-sans bg-white/90 p-2.5 rounded border border-sky-200/70 text-xs">
													{{ q.internal_choice_question.solution }}
												</div>
											</div>
										</div>
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
								<div class="flex items-center gap-1.5 flex-wrap">
									<span class="text-xs font-bold text-violet-700 uppercase">{{ p.subject }} &bull; {{ p.class_level }}</span>
									<Badge v-if="p.batch" variant="outline" theme="purple" size="sm">{{ p.batch }}</Badge>
								</div>
								<h3 class="font-bold text-ink-gray-9 text-sm line-clamp-1 mt-0.5">{{ p.title }}</h3>
							</div>
							<Badge
								:theme="p.approval_status === 'Published' ? 'green' : (p.approval_status === 'Principal Approved' ? 'blue' : (p.approval_status === 'Submitted for Approval' ? 'orange' : (p.approval_status === 'Rejected' ? 'red' : 'gray')))"
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
							<Button size="sm" variant="ghost" theme="violet" @click="openSavedPaper(p.name, true)">
								<template #prefix><span class="lucide-edit-3 size-3.5 text-violet-600"></span></template>
								{{ __('Review & Edit') }}
							</Button>
							<div class="flex items-center gap-1">
								<Button size="sm" variant="outline" @click="downloadSavedPaperPDF(p.name, 'question_paper')">
									{{ __('Paper') }}
								</Button>
								<Button size="sm" variant="outline" @click="downloadSavedPaperPDF(p.name, 'solutions')">
									{{ __('Solutions') }}
								</Button>
								<Button
									size="sm"
									variant="ghost"
									theme="red"
									:loading="deletingPaperName === p.name"
									@click="deleteSavedPaperFromList(p)"
									:title="__('Delete Question Paper')"
								>
									<template #prefix><span class="lucide-trash-2 size-3.5 text-red-500"></span></template>
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
const isEditMode = ref(false)
const generating = ref(false)
const saving = ref(false)
const downloading = ref(false)
const deleting = ref(false)
const deletingPaperName = ref(null)
const loadingSaved = ref(false)

const coursesList = ref([])
const batchesList = ref([])
const batchCoursesList = ref([])
const chaptersList = ref([])
const savedPapersList = ref([])
const generatedPaper = ref(null)
const contentStats = ref(null)
const loadingContent = ref(false)

const form = reactive({
	academic_year: '2026-27',
	class_level: 'Class 10',
	subject: 'Science',
	examination_type: 'Midterm Examination',
	batch: '',
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
	await loadBatches()
	await loadCourses()
	await loadSavedPapers()
	if (route.query.paper) {
		await openSavedPaper(route.query.paper, route.query.mode === 'edit')
	} else if (route.query.batch) {
		form.batch = route.query.batch
		await onBatchSelect()
	} else if (route.query.course) {
		form.course = route.query.course
		await onCourseSelect()
	}
})

async function loadBatches() {
	try {
		const res = await call('frappe.client.get_list', {
			doctype: 'LMS Batch',
			fields: ['name', 'title', 'category'],
			limit_page_length: 100,
			order_by: 'creation desc',
		})
		batchesList.value = res || []
	} catch (e) {
		console.error(e)
	}
}

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

async function onBatchSelect() {
	if (!form.batch) {
		batchCoursesList.value = []
		await updateContentPreview()
		return
	}
	try {
		const b = await call('lms.lms.ai.ai_assessment_api.api_get_batch_details', { batch: form.batch })
		if (b) {
			if (b.title) form.class_level = b.title
			if (b.category && (!form.subject || form.subject === 'Science')) form.subject = b.category
			batchCoursesList.value = b.courses || []
			if (b.courses && b.courses.length > 0) {
				form.course = b.courses[0].course
				await onCourseSelect()
			} else {
				await updateContentPreview()
			}
		}
	} catch (e) {
		console.error(e)
	}
}

async function onCourseSelect() {
	chaptersList.value = []
	form.selected_chapters = []
	if (!form.course) {
		await updateContentPreview()
		return
	}
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
		await updateContentPreview()
	} catch (e) {
		console.error(e)
	}
}

function selectAllChapters() {
	form.selected_chapters = chaptersList.value.map((ch) => ch.name)
	updateContentPreview()
}

function clearChapters() {
	form.selected_chapters = []
	updateContentPreview()
}

async function updateContentPreview() {
	if (!form.batch && !form.course) {
		contentStats.value = null
		return
	}
	loadingContent.value = true
	try {
		const res = await call('lms.lms.ai.ai_assessment_api.api_get_content_preview', {
			batch: form.batch || undefined,
			course: form.course || undefined,
		})
		contentStats.value = res?.stats || null
	} catch (e) {
		console.error(e)
	} finally {
		loadingContent.value = false
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
			batch: form.batch || undefined,
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

async function openSavedPaper(paperName, editMode = false) {
	try {
		const res = await call('lms.lms.ai.ai_assessment_api.api_get_question_paper', {
			name: paperName,
		})
		if (res) {
			generatedPaper.value = res
			activeView.value = 'preview'
			if (editMode || route.query.mode === 'edit') {
				isEditMode.value = true
			}
		}
	} catch (e) {
		toast.error(__('Failed to load question paper details.'))
	}
}

function recalculatePaperTotals() {
	if (!generatedPaper.value?.sections) return
	let runningQNum = 1
	let grandTotal = 0

	generatedPaper.value.sections.forEach((sec) => {
		sec.questions_count = sec.questions ? sec.questions.length : 0
		let secTotal = 0
		if (sec.questions) {
			sec.questions.forEach((q) => {
				q.question_number = runningQNum++
				secTotal += Number(q.marks) || 0
			})
		}
		sec.total_marks = secTotal
		grandTotal += secTotal
	})

	generatedPaper.value.total_marks = grandTotal

	if (generatedPaper.value.validation) {
		generatedPaper.value.validation.calculated_total_marks = grandTotal
		generatedPaper.value.validation.target_total_marks = grandTotal
		generatedPaper.value.validation.is_valid = true
		generatedPaper.value.validation.errors = []
	}
}

function deleteQuestion(sIdx, qIdx) {
	if (!confirm(__('Are you sure you want to delete this question?'))) return
	const sec = generatedPaper.value?.sections?.[sIdx]
	if (sec?.questions) {
		sec.questions.splice(qIdx, 1)
		recalculatePaperTotals()
		toast.success(__('Question deleted.'))
	}
}

function moveQuestion(sIdx, qIdx, direction) {
	const sec = generatedPaper.value?.sections?.[sIdx]
	if (!sec?.questions) return
	const targetIdx = qIdx + direction
	if (targetIdx < 0 || targetIdx >= sec.questions.length) return
	const [item] = sec.questions.splice(qIdx, 1)
	sec.questions.splice(targetIdx, 0, item)
	recalculatePaperTotals()
}

function addQuestionToSection(sIdx) {
	const sec = generatedPaper.value?.sections?.[sIdx]
	if (!sec) return
	if (!sec.questions) sec.questions = []
	const defaultMarks = Number(sec.marks_per_question) || (sec.question_type === 'MCQ' ? 1 : 3)
	const isMCQ = sec.question_type === 'MCQ' || sec.title?.toLowerCase().includes('mcq') || sec.title?.toLowerCase().includes('multiple choice')
	const newQ = {
		question_number: 1,
		question: 'New Question: Enter statement here',
		marks: defaultMarks,
		difficulty: 'Medium',
		options: isMCQ ? ['Option A', 'Option B', 'Option C', 'Option D'] : undefined,
		correct_answer: isMCQ ? 'Option A' : 'Model Answer / Solution Summary',
		solution: 'Detailed step-by-step solution and grading rubric.',
		internal_choice_question: null,
	}
	sec.questions.push(newQ)
	recalculatePaperTotals()
	toast.success(__('Question added to section.'))
}

function addOption(q) {
	if (!q.options) q.options = []
	const nextLetter = String.fromCharCode(65 + q.options.length)
	q.options.push(`Option ${nextLetter}`)
}

function removeOption(q, optIdx) {
	if (!q.options || q.options.length <= 2) {
		toast.error(__('A multiple choice question must have at least 2 options.'))
		return
	}
	q.options.splice(optIdx, 1)
}

function setCorrectOption(q, opt, optIdx) {
	q.correct_answer = opt
}

function addInternalChoice(q) {
	q.internal_choice_question = {
		question: 'Alternative OR Question: Enter statement here',
		marks: q.marks,
		correct_answer: 'Alternative question correct answer',
		solution: 'Alternative question step-by-step solution.',
	}
}

function removeInternalChoice(q) {
	q.internal_choice_question = null
}

async function deleteCurrentPaper() {
	if (!generatedPaper.value?.name) {
		generatedPaper.value = null
		activeView.value = 'generator'
		return
	}
	const paperName = generatedPaper.value.name
	const paperTitle = generatedPaper.value.title || paperName
	if (!confirm(__('Are you sure you want to delete this Question Paper "{0}" ({1})? This action cannot be undone.').format(paperTitle, paperName))) {
		return
	}
	deleting.value = true
	try {
		await call('lms.lms.ai.ai_assessment_api.api_delete_question_paper', {
			name: paperName,
		})
		toast.success(__('Question paper deleted successfully.'))
		generatedPaper.value = null
		await loadSavedPapers()
		activeView.value = 'saved_list'
	} catch (e) {
		toast.error(e.message || __('Failed to delete question paper.'))
	} finally {
		deleting.value = false
	}
}

async function deleteSavedPaperFromList(p) {
	const paperTitle = p.title || p.name
	if (!confirm(__('Are you sure you want to delete Question Paper "{0}" ({1})? This action cannot be undone.').format(paperTitle, p.name))) {
		return
	}
	deletingPaperName.value = p.name
	try {
		await call('lms.lms.ai.ai_assessment_api.api_delete_question_paper', {
			name: p.name,
		})
		toast.success(__('Question paper deleted successfully.'))
		if (generatedPaper.value?.name === p.name) {
			generatedPaper.value = null
		}
		await loadSavedPapers()
	} catch (e) {
		toast.error(e.message || __('Failed to delete question paper.'))
	} finally {
		deletingPaperName.value = null
	}
}

function isCorrectOption(correctAnswer, optText, optIdx) {
	if (!correctAnswer || !optText) return false
	const ans = String(correctAnswer).trim().toLowerCase()
	const opt = String(optText).trim().toLowerCase()
	const letter = String.fromCharCode(65 + optIdx).toLowerCase()
	if (ans === opt) return true
	if (ans.startsWith(`(${letter})`) || ans.startsWith(`${letter}.`) || ans === letter) return true
	const optClean = opt.replace(/^\([a-d]\)\s*|^[a-d]\.\s*/i, '').trim()
	const ansClean = ans.replace(/^\([a-d]\)\s*|^[a-d]\.\s*/i, '').trim()
	if (optClean && ansClean && (optClean === ansClean || ans.includes(optClean))) return true
	return false
}
</script>

