<template>
	<div class="flex-1 flex flex-col min-h-0 bg-surface-base overflow-y-auto">
		<PageHeader :breadcrumbs="[{ label: __('Assessments'), route: { name: 'Quizzes' } }, { label: __('AI Question Bank') }]">
			<template #actions>
				<div class="flex items-center gap-2">
					<Button variant="solid" theme="violet" size="sm" @click="openAddModal()">
						<template #prefix><span class="lucide-plus size-4"></span></template>
						{{ __('Add Question') }}
					</Button>
				</div>
			</template>
		</PageHeader>

		<div class="max-w-7xl mx-auto w-full p-4 md:p-6 space-y-6">
			<!-- Header Banner -->
			<div class="rounded-xl border bg-gradient-to-r from-emerald-900 to-teal-900 text-white p-6 shadow-sm">
				<div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
					<div>
						<div class="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-xs font-semibold backdrop-blur-sm mb-2">
							<span class="lucide-database size-3.5 text-emerald-300"></span>
							{{ __('Central Repository') }}
						</div>
						<h1 class="text-2xl font-bold tracking-tight">
							{{ __('AI-Assisted Question Bank') }}
						</h1>
						<p class="text-sm text-emerald-200 mt-1 max-w-2xl">
							{{ __('Search, filter, curate and reuse approved AI-generated and teacher-authored questions across quizzes and examination papers with automated duplicate detection.') }}
						</p>
					</div>

					<div class="text-right">
						<div class="text-3xl font-bold text-white">{{ totalQuestions }}</div>
						<div class="text-xs text-emerald-300 font-medium">{{ __('Total Bank Questions') }}</div>
					</div>
				</div>
			</div>

			<!-- Search & Filter Controls -->
			<div class="rounded-xl border bg-surface-base p-4 shadow-sm space-y-3">
				<div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
					<!-- Search Box -->
					<div class="sm:col-span-2">
						<label class="block text-xs font-medium text-ink-gray-7 mb-1">{{ __('Search Question or Explanation') }}</label>
						<input
							type="text"
							v-model="filters.search_query"
							class="w-full rounded-md border border-gray-300 px-3 py-1.5 text-sm dark:bg-gray-800 dark:border-gray-700"
							placeholder="Search terms, keywords..."
							@keyup.enter="searchQuestions"
						/>
					</div>

					<!-- Difficulty Filter -->
					<div>
						<label class="block text-xs font-medium text-ink-gray-7 mb-1">{{ __('Difficulty') }}</label>
						<select
							v-model="filters.difficulty"
							class="w-full rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm dark:bg-gray-800 dark:border-gray-700"
							@change="searchQuestions"
						>
							<option value="All">{{ __('All Difficulties') }}</option>
							<option value="Easy">{{ __('Easy') }}</option>
							<option value="Medium">{{ __('Medium') }}</option>
							<option value="Hard">{{ __('Hard') }}</option>
						</select>
					</div>

					<!-- Question Type Filter -->
					<div>
						<label class="block text-xs font-medium text-ink-gray-7 mb-1">{{ __('Type') }}</label>
						<select
							v-model="filters.question_type"
							class="w-full rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm dark:bg-gray-800 dark:border-gray-700"
							@change="searchQuestions"
						>
							<option value="All">{{ __('All Types') }}</option>
							<option value="Choices">{{ __('Choices (MCQ)') }}</option>
							<option value="User Input">{{ __('User Input / Fill Blanks') }}</option>
							<option value="Open Ended">{{ __('Open Ended / Subjective') }}</option>
						</select>
					</div>

					<!-- Course Filter -->
					<div>
						<label class="block text-xs font-medium text-ink-gray-7 mb-1">{{ __('Course') }}</label>
						<select
							v-model="filters.course"
							class="w-full rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm dark:bg-gray-800 dark:border-gray-700"
							@change="searchQuestions"
						>
							<option value="">{{ __('All Courses') }}</option>
							<option v-for="c in coursesList" :key="c.name" :value="c.name">
								{{ c.title || c.name }}
							</option>
						</select>
					</div>

					<!-- Search Action -->
					<div class="flex items-end">
						<Button variant="solid" theme="violet" class="w-full" @click="searchQuestions">
							<template #prefix><span class="lucide-search size-4"></span></template>
							{{ __('Filter') }}
						</Button>
					</div>
				</div>
			</div>

			<!-- Questions List -->
			<div class="space-y-4">
				<div v-if="loading" class="text-center py-16 text-gray-400">
					{{ __('Loading question bank...') }}
				</div>

				<div v-else-if="!questionsList.length" class="rounded-xl border bg-surface-base p-12 text-center text-gray-500">
					{{ __('No questions found matching the selected filters.') }}
				</div>

				<div v-else class="space-y-3">
					<div
						v-for="q in questionsList"
						:key="q.name"
						class="rounded-xl border bg-surface-base p-5 shadow-sm space-y-3 hover:border-violet-300 transition-colors"
					>
						<div class="flex items-start justify-between gap-4">
							<div class="flex items-center gap-2 flex-wrap">
								<span class="font-mono text-xs font-bold text-violet-700 bg-violet-50 px-2 py-0.5 rounded">
									{{ q.name }}
								</span>
								<Badge
									:theme="q.difficulty === 'Easy' ? 'green' : (q.difficulty === 'Hard' ? 'red' : 'orange')"
									variant="subtle"
									size="sm"
								>
									{{ q.difficulty }}
								</Badge>
								<Badge variant="subtle" theme="blue" size="sm">
									{{ q.type }}
								</Badge>
								<Badge variant="subtle" theme="gray" size="sm">
									{{ q.marks }} {{ __('Mark(s)') }}
								</Badge>
								<Badge
									v-if="q.source"
									variant="subtle"
									:theme="q.source === 'Extended Knowledge' ? 'amber' : (q.source === 'Manual' ? 'purple' : 'green')"
									size="sm"
								>
									{{ q.source }}
								</Badge>
							</div>

							<!-- Question Actions -->
							<div class="flex items-center gap-1">
								<Button size="sm" variant="ghost" @click="openEditModal(q)">
									<template #prefix><span class="lucide-pencil size-3.5"></span></template>
									{{ __('Edit') }}
								</Button>
							</div>
						</div>

						<!-- Question Text -->
						<div class="text-sm font-medium text-ink-gray-9" v-html="q.question"></div>

						<!-- Options if Choices -->
						<div v-if="q.options?.length" class="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs ps-2">
							<div
								v-for="(opt, oIdx) in q.options"
								:key="oIdx"
								class="flex items-center gap-2 p-1.5 rounded border"
								:class="isCorrect(q, opt) ? 'border-emerald-300 bg-emerald-50 text-emerald-900 font-bold' : 'border-gray-200 text-gray-700'"
							>
								<span class="size-4 flex items-center justify-center rounded-full text-[10px]" :class="isCorrect(q, opt) ? 'bg-emerald-600 text-white' : 'bg-gray-200 text-gray-700'">
									{{ String.fromCharCode(65 + oIdx) }}
								</span>
								<span>{{ opt }}</span>
							</div>
						</div>

						<!-- Explanation -->
						<div v-if="q.explanation" class="text-xs text-ink-gray-6 bg-gray-50 dark:bg-gray-800 p-2 rounded border border-gray-100">
							<span class="font-semibold text-ink-gray-7">{{ __('Explanation:') }}</span> {{ q.explanation }}
						</div>

						<!-- Meta Footer -->
						<div class="text-[11px] text-ink-gray-5 flex items-center gap-4 pt-1">
							<span v-if="q.course">{{ __('Course:') }} {{ q.course }}</span>
							<span v-if="q.chapter">{{ __('Chapter:') }} {{ q.chapter }}</span>
							<span v-if="q.subject">{{ __('Subject:') }} {{ q.subject }}</span>
							<span>{{ __('Created:') }} {{ q.creation }}</span>
						</div>
					</div>
				</div>
			</div>
		</div>

		<!-- Add / Edit Modal -->
		<Dialog
			v-model="showQuestionModal"
			:options="{
				title: isEdit ? __('Edit Bank Question') : __('Add Question to Bank'),
				size: '2xl',
			}"
		>
			<template #body-content>
				<div class="space-y-4 py-2 text-xs">
					<div>
						<label class="block font-medium text-ink-gray-7 mb-1">{{ __('Question Text') }} *</label>
						<textarea
							v-model="editForm.question"
							rows="3"
							class="w-full rounded border border-gray-300 p-2 text-sm focus:border-violet-500 dark:bg-gray-800 dark:border-gray-700"
							placeholder="Enter question statement..."
						></textarea>
					</div>

					<div class="grid grid-cols-3 gap-3">
						<div>
							<label class="block font-medium text-ink-gray-7 mb-1">{{ __('Question Type') }}</label>
							<select v-model="editForm.type" class="w-full rounded border p-1.5 bg-white dark:bg-gray-800">
								<option value="Choices">{{ __('Choices (MCQ)') }}</option>
								<option value="User Input">{{ __('User Input') }}</option>
								<option value="Open Ended">{{ __('Open Ended') }}</option>
							</select>
						</div>
						<div>
							<label class="block font-medium text-ink-gray-7 mb-1">{{ __('Difficulty') }}</label>
							<select v-model="editForm.difficulty" class="w-full rounded border p-1.5 bg-white dark:bg-gray-800">
								<option value="Easy">{{ __('Easy') }}</option>
								<option value="Medium">{{ __('Medium') }}</option>
								<option value="Hard">{{ __('Hard') }}</option>
							</select>
						</div>
						<div>
							<label class="block font-medium text-ink-gray-7 mb-1">{{ __('Marks') }}</label>
							<input type="number" v-model.number="editForm.marks" min="1" class="w-full rounded border p-1.5 text-center" />
						</div>
					</div>

					<!-- Options for Choices -->
					<div v-if="editForm.type === 'Choices'" class="space-y-2">
						<label class="block font-medium text-ink-gray-7">{{ __('Answer Options (Select correct option):') }}</label>
						<div v-for="(opt, idx) in editForm.options" :key="idx" class="flex items-center gap-2">
							<input
								type="radio"
								name="modal_correct_opt"
								:checked="editForm.correct_answer === opt"
								@change="editForm.correct_answer = opt"
								class="text-violet-600"
							/>
							<input
								type="text"
								v-model="editForm.options[idx]"
								class="flex-1 rounded border p-1 text-xs"
								:placeholder="`Option ${idx + 1}`"
							/>
						</div>
					</div>

					<div>
						<label class="block font-medium text-ink-gray-7 mb-1">{{ __('Explanation') }}</label>
						<input
							type="text"
							v-model="editForm.explanation"
							class="w-full rounded border p-1.5 text-xs"
							placeholder="Explanation for students..."
						/>
					</div>
				</div>
			</template>

			<template #actions>
				<div class="flex items-center justify-end gap-2">
					<Button variant="outline" @click="showQuestionModal = false">
						{{ __('Cancel') }}
					</Button>
					<Button variant="solid" theme="violet" :loading="modalSaving" @click="saveBankQuestion">
						{{ __('Save Question') }}
					</Button>
				</div>
			</template>
		</Dialog>
	</div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import PageHeader from '@/components/Layouts/PageHeader.vue'
import { Button, Badge, Dialog, toast, call } from 'frappe-ui'

const loading = ref(false)
const modalSaving = ref(false)
const showQuestionModal = ref(false)
const isEdit = ref(false)

const questionsList = ref([])
const totalQuestions = ref(0)
const coursesList = ref([])

const filters = reactive({
	search_query: '',
	difficulty: 'All',
	question_type: 'All',
	course: '',
})

const editForm = reactive({
	name: '',
	question: '',
	type: 'Choices',
	difficulty: 'Medium',
	marks: 1,
	options: ['', '', '', ''],
	correct_answer: '',
	explanation: '',
	source: 'Manual',
	course: '',
})

onMounted(async () => {
	await loadCourses()
	await searchQuestions()
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

async function searchQuestions() {
	loading.value = true
	try {
		const res = await call('lms.lms.ai.ai_assessment_api.api_search_question_bank', {
			search_query: filters.search_query || undefined,
			difficulty: filters.difficulty !== 'All' ? filters.difficulty : undefined,
			question_type: filters.question_type !== 'All' ? filters.question_type : undefined,
			course: filters.course || undefined,
			start: 0,
			page_length: 50,
		})
		if (res) {
			questionsList.value = res.questions || []
			totalQuestions.value = res.total_count || 0
		}
	} catch (e) {
		toast.error(__('Failed to load question bank.'))
	} finally {
		loading.value = false
	}
}

function isCorrect(q, opt) {
	if (Array.isArray(q.correct_answer)) {
		return q.correct_answer.includes(opt)
	}
	return q.correct_answer === opt
}

function openAddModal() {
	isEdit.value = false
	editForm.name = ''
	editForm.question = ''
	editForm.type = 'Choices'
	editForm.difficulty = 'Medium'
	editForm.marks = 1
	editForm.options = ['Option A', 'Option B', 'Option C', 'Option D']
	editForm.correct_answer = 'Option A'
	editForm.explanation = ''
	editForm.source = 'Manual'
	showQuestionModal.value = true
}

function openEditModal(q) {
	isEdit.value = true
	editForm.name = q.name
	editForm.question = q.question
	editForm.type = q.type
	editForm.difficulty = q.difficulty
	editForm.marks = q.marks
	editForm.options = q.options?.length ? [...q.options] : ['', '', '', '']
	editForm.correct_answer = Array.isArray(q.correct_answer) ? q.correct_answer[0] : q.correct_answer
	editForm.explanation = q.explanation || ''
	editForm.source = q.source || 'Manual'
	showQuestionModal.value = true
}

async function saveBankQuestion() {
	if (!editForm.question.trim()) {
		toast.error(__('Question text is required.'))
		return
	}

	modalSaving.value = true
	try {
		const res = await call('lms.lms.ai.ai_assessment_api.api_save_bank_question', {
			data: JSON.stringify(editForm),
		})
		if (res && res.name) {
			toast.success(__('Question saved successfully!'))
			showQuestionModal.value = false
			await searchQuestions()
		}
	} catch (e) {
		toast.error(e.message || __('Failed to save question.'))
	} finally {
		modalSaving.value = false
	}
}
</script>

