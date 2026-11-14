<template>
	<Dialog
		v-model="isOpen"
		:options="{
			title: __('Generate Model Question Paper from Historical Analysis'),
			size: '3xl',
		}"
	>
		<template #body-content>
			<div class="space-y-5">
				<div class="rounded-lg bg-gradient-to-r from-indigo-50 to-blue-50 border border-indigo-100 p-3.5 flex items-start gap-3">
					<span class="lucide-file-text size-5 text-indigo-600 flex-shrink-0 mt-0.5"></span>
					<div>
						<h4 class="text-xs font-bold text-indigo-900 uppercase tracking-wide">
							{{ __('Formal Examination Paper Blueprint') }}
						</h4>
						<p class="text-xs text-indigo-700 mt-0.5">
							{{ __('AI synthesizes a balanced, university-standard model examination paper with multiple sections, strict marks validation, downloadable A4 PDF format, and a separate Answer Key.') }}
						</p>
					</div>
				</div>

				<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
					<div class="md:col-span-2">
						<label class="block text-xs font-semibold uppercase text-gray-600 mb-1">
							{{ __('Examination Title') }} <span class="text-red-500">*</span>
						</label>
						<input
							v-model="form.title"
							type="text"
							placeholder="e.g. Model Examination: Java Programming (MCA 2026)"
							class="w-full text-sm rounded-lg border-gray-300 focus:border-violet-500 focus:ring-violet-500 font-medium"
						/>
					</div>

					<div>
						<label class="block text-xs font-semibold uppercase text-gray-600 mb-1">
							{{ __('Course') }}
						</label>
						<input
							type="text"
							:value="courseTitle || course"
							disabled
							class="w-full text-sm rounded-lg bg-gray-100 border-gray-300 text-gray-700"
						/>
					</div>

					<div>
						<label class="block text-xs font-semibold uppercase text-gray-600 mb-1">
							{{ __('Subject') }} <span class="text-red-500">*</span>
						</label>
						<input
							v-model="form.subject"
							type="text"
							placeholder="e.g. Java Programming"
							class="w-full text-sm rounded-lg border-gray-300 focus:border-violet-500 focus:ring-violet-500"
						/>
					</div>

					<div>
						<label class="block text-xs font-semibold uppercase text-gray-600 mb-1">
							{{ __('Total Examination Marks') }} <span class="text-red-500">*</span>
						</label>
						<div class="flex items-center gap-2">
							<button
								type="button"
								class="px-3 py-1.5 text-xs font-semibold rounded-lg border transition-colors"
								:class="form.total_marks === 100 ? 'bg-violet-600 text-white border-violet-600' : 'bg-white text-gray-700 border-gray-300'"
								@click="setTotalMarks(100)"
							>
								100 Marks
							</button>
							<button
								type="button"
								class="px-3 py-1.5 text-xs font-semibold rounded-lg border transition-colors"
								:class="form.total_marks === 80 ? 'bg-violet-600 text-white border-violet-600' : 'bg-white text-gray-700 border-gray-300'"
								@click="setTotalMarks(80)"
							>
								80 Marks
							</button>
							<button
								type="button"
								class="px-3 py-1.5 text-xs font-semibold rounded-lg border transition-colors"
								:class="form.total_marks === 50 ? 'bg-violet-600 text-white border-violet-600' : 'bg-white text-gray-700 border-gray-300'"
								@click="setTotalMarks(50)"
							>
								50 Marks
							</button>
							<input
								v-model.number="form.total_marks"
								type="number"
								min="10"
								max="200"
								class="w-24 text-sm rounded-lg border-gray-300 focus:border-violet-500 focus:ring-violet-500 text-center"
							/>
						</div>
					</div>

					<div>
						<label class="block text-xs font-semibold uppercase text-gray-600 mb-1">
							{{ __('Examination Duration') }}
						</label>
						<select
							v-model="form.duration"
							class="w-full text-sm rounded-lg border-gray-300 focus:border-violet-500 focus:ring-violet-500"
						>
							<option value="3 Hours">3 Hours (180 mins)</option>
							<option value="2.5 Hours">2.5 Hours (150 mins)</option>
							<option value="2 Hours">2 Hours (120 mins)</option>
							<option value="1.5 Hours">1.5 Hours (90 mins)</option>
							<option value="1 Hour">1 Hour (60 mins)</option>
						</select>
					</div>
				</div>

				<!-- Section Configuration Blueprint -->
				<div class="border rounded-xl p-4 bg-gray-50/50 space-y-3">
					<div class="flex items-center justify-between">
						<div>
							<h4 class="text-xs font-bold uppercase text-gray-700">
								{{ __('Sections Blueprint & Marks Allocation') }}
							</h4>
							<p class="text-[11px] text-gray-500">
								{{ __('Configure question counts and marks per section. Sum of section marks must match Total Marks exactly.') }}
							</p>
						</div>

						<div class="flex items-center gap-2">
							<span
								class="text-xs font-bold px-2.5 py-1 rounded-full"
								:class="isMarksSumValid ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'"
							>
								Sum: {{ currentSectionsMarksSum }} / {{ form.total_marks }} Marks
							</span>
						</div>
					</div>

					<div class="space-y-2">
						<div
							v-for="(sec, idx) in form.sections"
							:key="idx"
							class="bg-white border rounded-lg p-3 grid grid-cols-12 gap-2 items-center text-xs"
						>
							<div class="col-span-3 font-semibold text-gray-800">
								<input
									v-model="sec.section_name"
									type="text"
									class="w-full text-xs font-bold border-0 bg-transparent p-0 text-gray-900 focus:ring-0"
								/>
								<div class="text-[10px] text-gray-400 font-normal truncate">{{ sec.title }}</div>
							</div>

							<div class="col-span-3">
								<select
									v-model="sec.question_type"
									class="w-full text-xs rounded border-gray-200 py-1"
								>
									<option value="MCQ">MCQ</option>
									<option value="Short Answer">Short Answer</option>
									<option value="Long Answer">Long Answer</option>
									<option value="Descriptive Questions">Descriptive / Essay</option>
									<option value="Application-Based">Programming / Code</option>
									<option value="True/False">True/False</option>
									<option value="Fill in the Blanks">Fill in Blanks</option>
								</select>
							</div>

							<div class="col-span-2 text-center">
								<label class="block text-[10px] text-gray-400">Questions</label>
								<input
									v-model.number="sec.num_questions"
									type="number"
									min="1"
									class="w-16 text-center text-xs rounded border-gray-200 py-1"
								/>
							</div>

							<div class="col-span-2 text-center">
								<label class="block text-[10px] text-gray-400">Marks Each</label>
								<input
									v-model.number="sec.marks_per_question"
									type="number"
									min="1"
									class="w-16 text-center text-xs rounded border-gray-200 py-1"
								/>
							</div>

							<div class="col-span-2 text-right font-bold text-violet-700">
								{{ sec.num_questions * sec.marks_per_question }} M
							</div>
						</div>
					</div>
				</div>

				<!-- Difficulty Distribution -->
				<div>
					<label class="block text-xs font-semibold uppercase text-gray-600 mb-1">
						{{ __('Difficulty Distribution (%)') }}
					</label>
					<div class="grid grid-cols-3 gap-3">
						<div>
							<span class="text-[11px] text-emerald-700 font-semibold block mb-0.5">Easy (%)</span>
							<input
								v-model.number="form.difficulty_easy_pct"
								type="number"
								min="0"
								max="100"
								class="w-full text-xs rounded border-gray-300 focus:border-emerald-500 focus:ring-emerald-500"
							/>
						</div>
						<div>
							<span class="text-[11px] text-amber-700 font-semibold block mb-0.5">Medium (%)</span>
							<input
								v-model.number="form.difficulty_medium_pct"
								type="number"
								min="0"
								max="100"
								class="w-full text-xs rounded border-gray-300 focus:border-amber-500 focus:ring-amber-500"
							/>
						</div>
						<div>
							<span class="text-[11px] text-rose-700 font-semibold block mb-0.5">Hard (%)</span>
							<input
								v-model.number="form.difficulty_hard_pct"
								type="number"
								min="0"
								max="100"
								class="w-full text-xs rounded border-gray-300 focus:border-rose-500 focus:ring-rose-500"
							/>
						</div>
					</div>
				</div>

				<div v-if="errorMessage" class="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700 flex items-center gap-2">
					<span class="lucide-alert-circle size-4 flex-shrink-0"></span>
					<span>{{ errorMessage }}</span>
				</div>
			</div>
		</template>

		<template #actions>
			<div class="flex items-center justify-end gap-2 w-full">
				<Button
					variant="subtle"
					theme="gray"
					:disabled="isGenerating"
					@click="closeModal"
				>
					{{ __('Cancel') }}
				</Button>
				<Button
					variant="solid"
					theme="violet"
					:loading="isGenerating"
					:disabled="!isMarksSumValid || isGenerating"
					@click="submitGeneratePaper"
				>
					<template #prefix>
						<span class="lucide-file-text size-4"></span>
					</template>
					{{ isGenerating ? __('Generating Model Paper...') : __('Generate Model Paper') }}
				</Button>
			</div>
		</template>
	</Dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Dialog, Button, toast } from 'frappe-ui'
import { createResource } from 'frappe-ui'

const props = defineProps<{
	modelValue: boolean
	course: string
	courseTitle?: string
	subject?: string
	batch?: string
	analysisName?: string
}>()

const emit = defineEmits<{
	(e: 'update:modelValue', value: boolean): void
	(e: 'created', paperResult: any): void
}>()

const isOpen = computed({
	get: () => props.modelValue,
	set: (val) => emit('update:modelValue', val),
})

const form = ref({
	title: `Model Examination: ${props.subject || 'Subject'} (${props.course || 'Course'})`,
	subject: props.subject || '',
	batch: props.batch || '',
	total_marks: 100,
	duration: '3 Hours',
	difficulty_easy_pct: 30,
	difficulty_medium_pct: 40,
	difficulty_hard_pct: 30,
	sections: [
		{
			section_name: 'Section A',
			title: 'Objective & Conceptual Questions',
			instructions: 'Answer all questions. Each question carries 1 mark.',
			question_type: 'MCQ',
			num_questions: 10,
			marks_per_question: 1,
		},
		{
			section_name: 'Section B',
			title: 'Short Answer & Core Definitions',
			instructions: 'Answer all questions. Each question carries 4 marks.',
			question_type: 'Short Answer',
			num_questions: 5,
			marks_per_question: 4,
		},
		{
			section_name: 'Section C',
			title: 'Analytical & Problem-Solving Questions',
			instructions: 'Answer all questions. Each question carries 6 marks.',
			question_type: 'Long Answer',
			num_questions: 5,
			marks_per_question: 6,
		},
		{
			section_name: 'Section D',
			title: 'Comprehensive & Programming / Essay Questions',
			instructions: 'Answer all questions. Each question carries 10 marks.',
			question_type: 'Descriptive Questions',
			num_questions: 4,
			marks_per_question: 10,
		},
	],
})

const isGenerating = ref(false)
const errorMessage = ref('')

const currentSectionsMarksSum = computed(() => {
	return form.value.sections.reduce(
		(sum, sec) => sum + (Number(sec.num_questions) || 0) * (Number(sec.marks_per_question) || 0),
		0
	)
})

const isMarksSumValid = computed(() => {
	return currentSectionsMarksSum.value === Number(form.value.total_marks)
})

watch(
	() => props.subject,
	(val) => {
		if (val) {
			form.value.subject = val
			form.value.title = `Model Examination: ${val} (${props.course || 'Course'})`
		}
	}
)

function setTotalMarks(marks: number) {
	form.value.total_marks = marks
	if (marks === 100) {
		form.value.sections = [
			{ section_name: 'Section A', title: 'Objective Type', instructions: '1 Mark each', question_type: 'MCQ', num_questions: 10, marks_per_question: 1 },
			{ section_name: 'Section B', title: 'Short Answer', instructions: '4 Marks each', question_type: 'Short Answer', num_questions: 5, marks_per_question: 4 },
			{ section_name: 'Section C', title: 'Long Answer', instructions: '6 Marks each', question_type: 'Long Answer', num_questions: 5, marks_per_question: 6 },
			{ section_name: 'Section D', title: 'Essay / Programming', instructions: '10 Marks each', question_type: 'Descriptive Questions', num_questions: 4, marks_per_question: 10 },
		]
	} else if (marks === 80) {
		form.value.sections = [
			{ section_name: 'Section A', title: 'Objective Type', instructions: '1 Mark each', question_type: 'MCQ', num_questions: 10, marks_per_question: 1 },
			{ section_name: 'Section B', title: 'Short Answer', instructions: '3 Marks each', question_type: 'Short Answer', num_questions: 10, marks_per_question: 3 },
			{ section_name: 'Section C', title: 'Long Answer', instructions: '8 Marks each', question_type: 'Long Answer', num_questions: 5, marks_per_question: 8 },
		]
	} else if (marks === 50) {
		form.value.sections = [
			{ section_name: 'Section A', title: 'Objective Type', instructions: '1 Mark each', question_type: 'MCQ', num_questions: 10, marks_per_question: 1 },
			{ section_name: 'Section B', title: 'Short Answer', instructions: '4 Marks each', question_type: 'Short Answer', num_questions: 5, marks_per_question: 4 },
			{ section_name: 'Section C', title: 'Long Answer', instructions: '10 Marks each', question_type: 'Long Answer', num_questions: 2, marks_per_question: 10 },
		]
	}
}

function closeModal() {
	isOpen.value = false
	errorMessage.value = ''
}

async function submitGeneratePaper() {
	if (!isMarksSumValid.value) {
		errorMessage.value = `Section marks sum to ${currentSectionsMarksSum.value}, but Total Marks is ${form.value.total_marks}.`
		return
	}

	isGenerating.value = true
	errorMessage.value = ''

	try {
		const payloadSections = form.value.sections.map((sec) => ({
			section_name: sec.section_name,
			title: sec.title,
			instructions: sec.instructions,
			question_type: sec.question_type,
			num_questions: Number(sec.num_questions),
			marks_per_question: Number(sec.marks_per_question),
			total_marks: Number(sec.num_questions) * Number(sec.marks_per_question),
		}))

		const payload: Record<string, any> = {
			title: form.value.title.trim(),
			course: props.course,
			subject: form.value.subject.trim(),
			total_marks: Number(form.value.total_marks) || 100,
			duration: form.value.duration || '3 Hours',
			sections_config: JSON.stringify(payloadSections),
			difficulty_easy_pct: Number(form.value.difficulty_easy_pct) || 30,
			difficulty_medium_pct: Number(form.value.difficulty_medium_pct) || 40,
			difficulty_hard_pct: Number(form.value.difficulty_hard_pct) || 30,
		}
		if (form.value.batch && form.value.batch.trim()) {
			payload.batch = form.value.batch.trim()
		}
		if (props.analysisName) {
			payload.analysis_name = props.analysisName
		}

		const res = await createResource({
			url: 'lms.lms.ai.previous_year_api.api_generate_model_paper_from_history',
			params: payload,
		}).fetch()

		if (res && res.status === 'success') {
			toast.success(`Created '${res.title}' with ${res.total_marks} marks in Draft status.`)
			emit('created', res)
			closeModal()
		} else {
			throw new Error('Failed to create model question paper.')
		}
	} catch (err: any) {
		errorMessage.value = err.message || 'Generation failed. Please try again.'
	} finally {
		isGenerating.value = false
	}
}
</script>
