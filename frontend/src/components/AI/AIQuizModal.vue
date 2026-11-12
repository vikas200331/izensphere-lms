<template>
	<Dialog
		v-model="isOpen"
		:options="{
			title: __('Generate Quiz with AI'),
			size: '4xl',
		}"
	>
		<template #body-content>
			<div class="space-y-5 py-2">
				<!-- Step Switcher -->
				<div class="flex items-center justify-between border-b pb-3">
					<div class="flex items-center gap-2">
						<div
							class="flex size-7 items-center justify-center rounded-full text-xs font-semibold"
							:class="step === 1 ? 'bg-violet-600 text-white' : 'bg-gray-100 text-gray-700'"
						>
							1
						</div>
						<span class="text-sm font-medium" :class="step === 1 ? 'text-violet-900 font-semibold' : 'text-gray-500'">
							{{ __('Configure & Generate') }}
						</span>
						<span class="lucide-chevron-right size-4 text-gray-400"></span>
						<div
							class="flex size-7 items-center justify-center rounded-full text-xs font-semibold"
							:class="step === 2 ? 'bg-violet-600 text-white' : 'bg-gray-100 text-gray-700'"
						>
							2
						</div>
						<span class="text-sm font-medium" :class="step === 2 ? 'text-violet-900 font-semibold' : 'text-gray-500'">
							{{ __('Review & Approve') }} ({{ generatedQuestions.length }})
						</span>
					</div>

					<Badge v-if="step === 2" variant="subtle" theme="violet">
						{{ __('Total Marks:') }} {{ calculatedTotalMarks }}
					</Badge>
				</div>

				<!-- STEP 1: CONFIGURATION FORM -->
				<div v-if="step === 1" class="space-y-4">
					<!-- Generation Mode Banner -->
					<div class="rounded-lg border bg-surface-base p-3.5 shadow-sm">
						<label class="block text-xs font-semibold text-ink-gray-7 uppercase tracking-wider mb-2">
							{{ __('Generation Mode') }}
						</label>
						<div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
							<div
								class="flex items-start gap-2.5 rounded-lg border p-3 cursor-pointer transition-colors"
								:class="form.mode === 'Chapter-Based' ? 'border-violet-600 bg-violet-50/50 dark:bg-violet-950/20' : 'hover:bg-gray-50'"
								@click="form.mode = 'Chapter-Based'"
							>
								<input
									type="radio"
									v-model="form.mode"
									value="Chapter-Based"
									class="mt-0.5 text-violet-600"
								/>
								<div>
									<div class="text-sm font-semibold text-ink-gray-9">
										{{ __('Mode 1: Chapter-Based') }}
									</div>
									<div class="text-xs text-ink-gray-6 mt-0.5">
										{{ __('Generates questions exclusively from selected LMS lessons and notes. No external claims.') }}
									</div>
								</div>
							</div>

							<div
								class="flex items-start gap-2.5 rounded-lg border p-3 cursor-pointer transition-colors"
								:class="form.mode === 'Extended Knowledge' ? 'border-violet-600 bg-violet-50/50 dark:bg-violet-950/20' : 'hover:bg-gray-50'"
								@click="form.mode = 'Extended Knowledge'"
							>
								<input
									type="radio"
									v-model="form.mode"
									value="Extended Knowledge"
									class="mt-0.5 text-violet-600"
								/>
								<div>
									<div class="text-sm font-semibold text-ink-gray-9">
										{{ __('Mode 2: Extended Knowledge') }}
									</div>
									<div class="text-xs text-ink-gray-6 mt-0.5">
										{{ __('Uses chapter as core foundation, enriched with curriculum educational domain facts.') }}
									</div>
								</div>
							</div>
						</div>
					</div>

					<!-- Hierarchy Selectors -->
					<div class="grid grid-cols-1 md:grid-cols-3 gap-3">
						<div>
							<label class="block text-xs font-medium text-ink-gray-7 mb-1">{{ __('Course') }} *</label>
							<select
								v-model="form.course"
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm shadow-sm focus:border-violet-500 focus:outline-none dark:bg-gray-800 dark:border-gray-700"
								@change="onCourseChange"
							>
								<option value="">{{ __('-- Select Course --') }}</option>
								<option v-for="c in coursesList" :key="c.name" :value="c.name">
									{{ c.title || c.name }}
								</option>
							</select>
						</div>

						<div>
							<label class="block text-xs font-medium text-ink-gray-7 mb-1">{{ __('Chapter') }}</label>
							<select
								v-model="form.chapter"
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm shadow-sm focus:border-violet-500 focus:outline-none dark:bg-gray-800 dark:border-gray-700"
								@change="onChapterChange"
								:disabled="!chaptersList.length"
							>
								<option value="">{{ __('-- All / Select Chapter --') }}</option>
								<option v-for="ch in chaptersList" :key="ch.name" :value="ch.name">
									{{ ch.title || ch.name }}
								</option>
							</select>
						</div>

						<div>
							<label class="block text-xs font-medium text-ink-gray-7 mb-1">{{ __('Lesson') }}</label>
							<select
								v-model="form.lesson"
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm shadow-sm focus:border-violet-500 focus:outline-none dark:bg-gray-800 dark:border-gray-700"
								@change="onLessonChange"
								:disabled="!lessonsList.length"
							>
								<option value="">{{ __('-- All / Select Lesson --') }}</option>
								<option v-for="l in lessonsList" :key="l.name" :value="l.name">
									{{ l.title || l.name }}
								</option>
							</select>
						</div>
					</div>

					<!-- Content Inspection Metric Banner -->
					<div
						v-if="contentStats"
						class="rounded-lg border p-3 text-xs flex flex-wrap items-center justify-between gap-2"
						:class="contentStats.is_insufficient ? 'border-amber-300 bg-amber-50 text-amber-900' : 'border-emerald-200 bg-emerald-50 text-emerald-900'"
					>
						<div class="flex items-center gap-2">
							<span
								:class="contentStats.is_insufficient ? 'lucide-alert-triangle text-amber-600' : 'lucide-check-circle text-emerald-600'"
								class="size-4 shrink-0"
							></span>
							<div>
								<span class="font-semibold">{{ __('Extracted Educational Content:') }}</span>
								{{ contentStats.word_count }} {{ __('words') }} ({{ contentStats.char_count }} {{ __('chars') }}, ~{{ contentStats.estimated_tokens }} {{ __('tokens') }}).
								<div v-if="contentStats.is_insufficient" class="mt-0.5 text-amber-800">
									{{ contentStats.warning }}
								</div>
							</div>
						</div>
						<Badge :theme="contentStats.is_insufficient ? 'orange' : 'green'" variant="subtle">
							{{ contentStats.is_insufficient ? __('Minimal Content') : __('Ready for AI') }}
						</Badge>
					</div>

					<!-- Assessment Parameters -->
					<div class="grid grid-cols-2 md:grid-cols-4 gap-3">
						<div>
							<label class="block text-xs font-medium text-ink-gray-7 mb-1">{{ __('Difficulty') }}</label>
							<select
								v-model="form.difficulty"
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm shadow-sm focus:border-violet-500 dark:bg-gray-800 dark:border-gray-700"
							>
								<option value="Easy">{{ __('Easy') }}</option>
								<option value="Medium">{{ __('Medium') }}</option>
								<option value="Hard">{{ __('Hard') }}</option>
								<option value="Mixed">{{ __('Mixed (Balanced)') }}</option>
							</select>
						</div>

						<div>
							<label class="block text-xs font-medium text-ink-gray-7 mb-1">{{ __('Questions Count') }}</label>
							<input
								type="number"
								v-model.number="form.num_questions"
								min="1"
								max="50"
								class="w-full rounded-md border border-gray-300 px-3 py-1.5 text-sm shadow-sm focus:border-violet-500 dark:bg-gray-800 dark:border-gray-700"
							/>
						</div>

						<div>
							<label class="block text-xs font-medium text-ink-gray-7 mb-1">{{ __('Total Marks') }}</label>
							<input
								type="number"
								v-model.number="form.total_marks"
								min="1"
								class="w-full rounded-md border border-gray-300 px-3 py-1.5 text-sm shadow-sm focus:border-violet-500 dark:bg-gray-800 dark:border-gray-700"
							/>
						</div>

						<div>
							<label class="block text-xs font-medium text-ink-gray-7 mb-1">{{ __('Language') }}</label>
							<input
								type="text"
								v-model="form.language"
								class="w-full rounded-md border border-gray-300 px-3 py-1.5 text-sm shadow-sm focus:border-violet-500 dark:bg-gray-800 dark:border-gray-700"
							/>
						</div>
					</div>

					<!-- Question Types Checkboxes -->
					<div>
						<label class="block text-xs font-semibold text-ink-gray-7 uppercase tracking-wider mb-2">
							{{ __('Supported Question Types') }}
						</label>
						<div class="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs">
							<label class="flex items-center gap-2 cursor-pointer p-2 rounded border hover:bg-gray-50">
								<input type="checkbox" v-model="form.question_types" value="MCQ" class="text-violet-600 rounded" />
								<span>{{ __('Multiple Choice (MCQ)') }}</span>
							</label>
							<label class="flex items-center gap-2 cursor-pointer p-2 rounded border hover:bg-gray-50">
								<input type="checkbox" v-model="form.question_types" value="Multiple Select" class="text-violet-600 rounded" />
								<span>{{ __('Multiple Select') }}</span>
							</label>
							<label class="flex items-center gap-2 cursor-pointer p-2 rounded border hover:bg-gray-50">
								<input type="checkbox" v-model="form.question_types" value="True or False" class="text-violet-600 rounded" />
								<span>{{ __('True or False') }}</span>
							</label>
							<label class="flex items-center gap-2 cursor-pointer p-2 rounded border hover:bg-gray-50">
								<input type="checkbox" v-model="form.question_types" value="Fill in the Blanks" class="text-violet-600 rounded" />
								<span>{{ __('Fill in the Blanks') }}</span>
							</label>
							<label class="flex items-center gap-2 cursor-pointer p-2 rounded border hover:bg-gray-50">
								<input type="checkbox" v-model="form.question_types" value="Short Answer" class="text-violet-600 rounded" />
								<span>{{ __('Short Answer') }}</span>
							</label>
							<label class="flex items-center gap-2 cursor-pointer p-2 rounded border hover:bg-gray-50">
								<input type="checkbox" v-model="form.question_types" value="Descriptive Questions" class="text-violet-600 rounded" />
								<span>{{ __('Descriptive Questions') }}</span>
							</label>
						</div>
					</div>

					<!-- Extra options -->
					<div class="flex flex-wrap items-center gap-6 pt-1 text-sm text-ink-gray-8">
						<label class="flex items-center gap-2 cursor-pointer">
							<input type="checkbox" v-model="form.include_explanations" class="text-violet-600 rounded" />
							<span>{{ __('Include Answer Explanations') }}</span>
						</label>
						<label class="flex items-center gap-2 cursor-pointer">
							<input type="checkbox" v-model="form.randomize" class="text-violet-600 rounded" />
							<span>{{ __('Randomize Question Sequence') }}</span>
						</label>
					</div>
				</div>

				<!-- STEP 2: REVIEW & APPROVAL VIEW -->
				<div v-else class="space-y-4 max-h-[60vh] overflow-y-auto pe-1">
					<div class="flex items-center justify-between gap-3">
						<div class="text-sm font-semibold text-ink-gray-9">
							{{ __('Reviewing') }} {{ generatedQuestions.length }} {{ __('Generated Questions') }}
						</div>
						<div class="flex items-center gap-2">
							<Button size="sm" variant="outline" @click="addManualQuestion">
								<template #prefix><span class="lucide-plus size-3.5"></span></template>
								{{ __('Add Manual Question') }}
							</Button>
							<Button size="sm" variant="ghost" @click="step = 1">
								{{ __('Back to Configuration') }}
							</Button>
						</div>
					</div>

					<!-- Question Cards -->
					<div
						v-for="(q, idx) in generatedQuestions"
						:key="q.temp_id || idx"
						class="rounded-xl border bg-surface-base p-4 shadow-sm space-y-3 transition-all hover:border-violet-300"
					>
						<div class="flex items-start justify-between gap-3">
							<div class="flex items-center gap-2 flex-wrap">
								<span class="flex size-6 items-center justify-center rounded-full bg-violet-100 text-xs font-bold text-violet-800">
									{{ idx + 1 }}
								</span>
								<Badge variant="subtle" theme="violet" size="sm">
									{{ q.question_type_label || q.type }}
								</Badge>
								<select
									v-model="q.difficulty"
									class="rounded border border-gray-200 px-2 py-0.5 text-xs text-ink-gray-7 focus:outline-none dark:bg-gray-800 dark:border-gray-700"
								>
									<option value="Easy">{{ __('Easy') }}</option>
									<option value="Medium">{{ __('Medium') }}</option>
									<option value="Hard">{{ __('Hard') }}</option>
								</select>
								<span class="text-xs text-ink-gray-5 flex items-center gap-1">
									{{ __('Marks:') }}
									<input
										type="number"
										v-model.number="q.marks"
										class="w-12 rounded border px-1 py-0.5 text-xs text-center"
										min="1"
									/>
								</span>
								<Badge v-if="q.source" variant="subtle" :theme="q.source === 'Extended Knowledge' ? 'amber' : 'green'" size="sm">
									{{ q.source }}
								</Badge>
							</div>

							<!-- Question Actions -->
							<div class="flex items-center gap-1">
								<Button
									size="sm"
									variant="ghost"
									:loading="q._regenerating"
									@click="regenerateQuestion(q, idx)"
									:title="__('Regenerate this question')"
								>
									<template #prefix><span class="lucide-refresh-cw size-3.5 text-violet-600"></span></template>
									{{ __('Regenerate') }}
								</Button>
								<Button
									size="sm"
									variant="ghost"
									theme="red"
									@click="deleteQuestion(idx)"
									:title="__('Delete question')"
								>
									<template #icon><span class="lucide-trash-2 size-3.5"></span></template>
								</Button>
							</div>
						</div>

						<!-- Question Text Editor -->
						<div>
							<textarea
								v-model="q.question"
								rows="2"
								class="w-full rounded-md border border-gray-200 p-2 text-sm font-medium text-ink-gray-9 focus:border-violet-500 focus:outline-none dark:bg-gray-900 dark:border-gray-800"
							></textarea>
						</div>

						<!-- Options Editor for Choices -->
						<div v-if="q.type === 'Choices' && q.options" class="space-y-1.5 ps-2">
							<div
								v-for="(opt, optIdx) in q.options"
								:key="optIdx"
								class="flex items-center gap-2 text-xs"
							>
								<input
									v-if="q.question_type_label === 'Multiple Select'"
									type="checkbox"
									:checked="isCorrectOption(q, opt)"
									@change="toggleCorrectOption(q, opt)"
									class="text-violet-600 rounded"
								/>
								<input
									v-else
									type="radio"
									:name="`correct_${q.temp_id || idx}`"
									:checked="q.correct_answer === opt"
									@change="setCorrectOption(q, opt)"
									class="text-violet-600"
								/>
								<span class="w-4 font-bold text-ink-gray-5">{{ String.fromCharCode(65 + optIdx) }}.</span>
								<input
									type="text"
									v-model="q.options[optIdx]"
									class="flex-1 rounded border border-gray-200 px-2 py-1 text-xs focus:outline-none dark:bg-gray-800 dark:border-gray-700"
								/>
							</div>
						</div>

						<!-- Possibilities for User Input -->
						<div v-if="q.type === 'User Input'" class="text-xs space-y-1 ps-2">
							<label class="text-ink-gray-6 font-medium">{{ __('Accepted Answers (Comma-separated):') }}</label>
							<input
								type="text"
								:value="(q.possibilities || []).join(', ')"
								@input="updatePossibilities(q, $event.target.value)"
								class="w-full rounded border border-gray-200 px-2 py-1 text-xs dark:bg-gray-800 dark:border-gray-700"
							/>
						</div>

						<!-- Explanation -->
						<div class="text-xs ps-2 text-ink-gray-6">
							<label class="font-medium text-ink-gray-7">{{ __('Explanation:') }}</label>
							<input
								type="text"
								v-model="q.explanation"
								class="w-full mt-0.5 rounded border border-gray-200 px-2 py-1 text-xs text-ink-gray-7 dark:bg-gray-800 dark:border-gray-700"
							/>
						</div>
					</div>
				</div>
			</div>
		</template>

		<template #actions>
			<div class="flex w-full items-center justify-between">
				<div class="text-xs text-ink-gray-5">
					<span v-if="generationUsage">
						{{ __('Tokens:') }} {{ generationUsage.total_tokens }} (~${{ generationUsage.estimated_cost }})
					</span>
				</div>

				<div class="flex items-center gap-2">
					<Button variant="outline" @click="isOpen = false">
						{{ __('Cancel') }}
					</Button>

					<Button
						v-if="step === 1"
						variant="solid"
						theme="violet"
						:loading="loading"
						@click="handleGenerate"
					>
						<template #prefix><span class="lucide-sparkles size-4"></span></template>
						{{ __('Generate Quiz with AI') }}
					</Button>

					<!-- Step 2 Actions -->
					<template v-else>
						<Button
							variant="outline"
							:loading="saving"
							@click="saveQuiz('Draft')"
						>
							{{ __('Save as Draft') }}
						</Button>

						<Button
							variant="subtle"
							theme="orange"
							:loading="saving"
							@click="saveQuiz('Submitted for Approval')"
						>
							{{ __('Submit for Approval') }}
						</Button>

						<Button
							variant="solid"
							theme="green"
							:loading="saving"
							@click="saveQuiz('Published')"
						>
							{{ __('Publish Quiz') }}
						</Button>
					</template>
				</div>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { Dialog, Button, Badge, toast, call } from 'frappe-ui'

const props = defineProps({
	modelValue: Boolean,
	initialCourse: String,
	initialChapter: String,
	initialLesson: String,
	quizName: String,
	quizTitle: String,
})

const emit = defineEmits(['update:modelValue', 'quizSaved'])

const isOpen = computed({
	get: () => props.modelValue,
	set: (val) => emit('update:modelValue', val),
})

const step = ref(1)
const loading = ref(false)
const saving = ref(false)
const contentStats = ref(null)
const generationUsage = ref(null)

const coursesList = ref([])
const chaptersList = ref([])
const lessonsList = ref([])

const form = reactive({
	course: props.initialCourse || '',
	chapter: props.initialChapter || '',
	lesson: props.initialLesson || '',
	difficulty: 'Medium',
	num_questions: 5,
	total_marks: 5,
	marks_per_question: 1,
	language: 'English',
	question_types: ['MCQ', 'Multiple Select', 'True or False', 'Fill in the Blanks', 'Short Answer', 'Descriptive Questions'],
	include_explanations: true,
	randomize: false,
	mode: 'Chapter-Based',
})

const generatedQuestions = ref([])

const calculatedTotalMarks = computed(() => {
	return generatedQuestions.value.reduce((sum, q) => sum + (Number(q.marks) || 1), 0)
})

onMounted(async () => {
	await loadCourses()
	if (form.course) {
		await loadChapters(form.course)
	}
	if (form.chapter) {
		await loadLessons(form.chapter)
	}
	checkContentPreview()
})

async function loadCourses() {
	try {
		const res = await call('frappe.client.get_list', {
			doctype: 'LMS Course',
			fields: ['name', 'title'],
			order_by: 'title asc',
			limit_page_length: 100,
		})
		coursesList.value = res || []
	} catch (e) {
		console.error(e)
	}
}

async function loadChapters(courseName) {
	try {
		const res = await call('frappe.client.get_list', {
			doctype: 'Course Chapter',
			filters: { course: courseName },
			fields: ['name', 'title'],
			order_by: 'idx asc',
		})
		chaptersList.value = res || []
	} catch (e) {
		console.error(e)
	}
}

async function loadLessons(chapterName) {
	try {
		const res = await call('frappe.client.get_list', {
			doctype: 'Course Lesson',
			filters: { chapter: chapterName },
			fields: ['name', 'title'],
			order_by: 'idx asc',
		})
		lessonsList.value = res || []
	} catch (e) {
		console.error(e)
	}
}

async function onCourseChange() {
	form.chapter = ''
	form.lesson = ''
	chaptersList.value = []
	lessonsList.value = []
	if (form.course) {
		await loadChapters(form.course)
	}
	checkContentPreview()
}

async function onChapterChange() {
	form.lesson = ''
	lessonsList.value = []
	if (form.chapter) {
		await loadLessons(form.chapter)
	}
	checkContentPreview()
}

function onLessonChange() {
	checkContentPreview()
}

async function checkContentPreview() {
	if (!form.course && !form.chapter && !form.lesson) {
		contentStats.value = null
		return
	}
	try {
		const res = await call('lms.lms.ai.ai_assessment_api.api_get_content_preview', {
			course: form.course || undefined,
			chapter: form.chapter || undefined,
			lesson: form.lesson || undefined,
		})
		if (res && res.stats) {
			contentStats.value = res.stats
		}
	} catch (e) {
		// Non-blocking
	}
}

async function handleGenerate() {
	if (!form.course && !form.chapter && !form.lesson) {
		toast.error(__('Please select a Course, Chapter, or Lesson.'))
		return
	}

	loading.value = true
	try {
		const res = await call('lms.lms.ai.ai_assessment_api.api_generate_quiz', {
			course: form.course || undefined,
			chapter: form.chapter || undefined,
			lesson: form.lesson || undefined,
			difficulty: form.difficulty,
			num_questions: form.num_questions,
			total_marks: form.total_marks,
			marks_per_question: form.marks_per_question,
			language: form.language,
			question_types: JSON.stringify(form.question_types),
			include_explanations: form.include_explanations ? 1 : 0,
			randomize: form.randomize ? 1 : 0,
			mode: form.mode,
		})

		if (res && res.questions) {
			generatedQuestions.value = res.questions
			generationUsage.value = res.usage
			step.value = 2
			toast.success(__('Generated {0} questions successfully!').replace('{0}', res.questions.length))
			if (res.warning) {
				toast.warning(res.warning)
			}
		} else {
			toast.error(__('Failed to generate questions.'))
		}
	} catch (e) {
		toast.error(e.message || __('Error generating quiz with AI.'))
	} finally {
		loading.value = false
	}
}

async function regenerateQuestion(q, idx) {
	q._regenerating = true
	try {
		const res = await call('lms.lms.ai.ai_assessment_api.api_regenerate_question', {
			question_data: JSON.stringify(q),
			course: form.course || undefined,
			chapter: form.chapter || undefined,
			lesson: form.lesson || undefined,
			mode: form.mode,
			target_difficulty: q.difficulty,
		})
		if (res && res.question) {
			generatedQuestions.value[idx] = res
			toast.success(__('Question regenerated!'))
		}
	} catch (e) {
		toast.error(__('Failed to regenerate question.'))
	} finally {
		q._regenerating = false
	}
}

function deleteQuestion(idx) {
	generatedQuestions.value.splice(idx, 1)
	toast.info(__('Question removed.'))
}

function addManualQuestion() {
	generatedQuestions.value.push({
		temp_id: `manual_${Date.now()}`,
		question: 'New Question Text',
		type: 'Choices',
		question_type_label: 'MCQ',
		options: ['Option A', 'Option B', 'Option C', 'Option D'],
		correct_answer: 'Option A',
		explanation: 'Explanation for correct answer.',
		marks: 1,
		difficulty: 'Medium',
		source: 'Manual',
		course: form.course || '',
		chapter: form.chapter || '',
		lesson: form.lesson || '',
	})
}

function isCorrectOption(q, opt) {
	if (Array.isArray(q.correct_answer)) {
		return q.correct_answer.includes(opt)
	}
	return q.correct_answer === opt
}

function toggleCorrectOption(q, opt) {
	if (!Array.isArray(q.correct_answer)) {
		q.correct_answer = q.correct_answer ? [q.correct_answer] : []
	}
	const idx = q.correct_answer.indexOf(opt)
	if (idx > -1) {
		q.correct_answer.splice(idx, 1)
	} else {
		q.correct_answer.push(opt)
	}
}

function setCorrectOption(q, opt) {
	q.correct_answer = opt
}

function updatePossibilities(q, val) {
	q.possibilities = val.split(',').map((s) => s.trim()).filter(Boolean)
}

async function saveQuiz(action = 'Draft') {
	if (!generatedQuestions.value.length) {
		toast.error(__('No questions to save.'))
		return
	}

	saving.value = true
	try {
		const title = props.quizTitle || `Quiz: ${form.chapter || form.course || 'Assessment'}`
		const res = await call('lms.lms.ai.ai_assessment_api.api_save_quiz', {
			quiz_title: title,
			questions: JSON.stringify(generatedQuestions.value),
			course: form.course || undefined,
			chapter: form.chapter || undefined,
			lesson: form.lesson || undefined,
			action: action,
			quiz_name: props.quizName || undefined,
		})

		if (res && res.quiz_name) {
			toast.success(__('Quiz saved successfully as {0}!').replace('{0}', res.release_status))
			isOpen.value = false
			emit('quizSaved', res)
		}
	} catch (e) {
		toast.error(e.message || __('Failed to save quiz.'))
	} finally {
		saving.value = false
	}
}
</script>

