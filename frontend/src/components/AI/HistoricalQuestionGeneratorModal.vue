<template>
	<Dialog
		v-model="isOpen"
		:options="{
			title: __('Generate New Questions Using AI'),
			size: '2xl',
		}"
	>
		<template #body-content>
			<div class="space-y-4">
				<div class="rounded-lg bg-gradient-to-r from-violet-50 to-indigo-50 border border-violet-100 p-3 flex items-start gap-3">
					<span class="lucide-sparkles size-5 text-violet-600 flex-shrink-0 mt-0.5"></span>
					<div>
						<h4 class="text-xs font-bold text-violet-900 uppercase tracking-wide">
							{{ __('Historical Exam Pattern Intelligence') }}
						</h4>
						<p class="text-xs text-violet-700 mt-0.5">
							{{ __('AI analyzes ALL historical papers for this Course, detects high-yield repeated concepts, and synthesizes completely NEW questions with fresh wording, examples, and problem scenarios.') }}
						</p>
					</div>
				</div>

				<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
					<div>
						<label class="block text-xs font-semibold uppercase text-gray-600 mb-1">
							{{ __('Course') }}
						</label>
						<input
							type="text"
							:value="courseTitle || course"
							disabled
							class="w-full text-sm rounded-lg bg-gray-100 border-gray-300 text-gray-700 font-medium"
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
							{{ __('Target Chapter / Unit (Optional)') }}
						</label>
						<select
							v-if="availableChapters && availableChapters.length > 0"
							v-model="form.chapter"
							class="w-full text-sm rounded-lg border-gray-300 focus:border-violet-500 focus:ring-violet-500"
						>
							<option value="">{{ __('All High-Yield Chapters / Topics') }}</option>
							<option v-for="ch in availableChapters" :key="ch" :value="ch">
								{{ ch }}
							</option>
						</select>
						<input
							v-else
							v-model="form.chapter"
							type="text"
							placeholder="e.g. Object-Oriented Programming, Polymorphism"
							class="w-full text-sm rounded-lg border-gray-300 focus:border-violet-500 focus:ring-violet-500"
						/>
					</div>

					<div>
						<label class="block text-xs font-semibold uppercase text-gray-600 mb-1">
							{{ __('Target Batch (Optional)') }}
						</label>
						<input
							v-model="form.batch"
							type="text"
							placeholder="e.g. MCA 2026 Batch"
							class="w-full text-sm rounded-lg border-gray-300 focus:border-violet-500 focus:ring-violet-500"
						/>
					</div>

					<div>
						<label class="block text-xs font-semibold uppercase text-gray-600 mb-1">
							{{ __('Question Type') }}
						</label>
						<select
							v-model="form.question_type"
							class="w-full text-sm rounded-lg border-gray-300 focus:border-violet-500 focus:ring-violet-500"
						>
							<option value="Mixed">Mixed (All Types Proportional)</option>
							<option value="Choices">Multiple Choice Questions (MCQ)</option>
							<option value="Multiple Select">Multiple Select Questions</option>
							<option value="True or False">True or False</option>
							<option value="Fill in the Blanks">Fill in the Blanks</option>
							<option value="Short Answer">Short Answer (1-3 Marks)</option>
							<option value="Long Answer">Long Answer (4-7 Marks)</option>
							<option value="Essay">Essay / Descriptive (8-15 Marks)</option>
							<option value="Programming">Programming / Code Implementation</option>
						</select>
					</div>

					<div>
						<label class="block text-xs font-semibold uppercase text-gray-600 mb-1">
							{{ __('Difficulty Level') }}
						</label>
						<select
							v-model="form.difficulty"
							class="w-full text-sm rounded-lg border-gray-300 focus:border-violet-500 focus:ring-violet-500"
						>
							<option value="Mixed">Mixed (Balanced: 30% Easy, 40% Med, 30% Hard)</option>
							<option value="Easy">Easy (Recall & Fundamentals)</option>
							<option value="Medium">Medium (Application & Explanation)</option>
							<option value="Hard">Hard (Analysis, Design, Complex Problems)</option>
						</select>
					</div>

					<div>
						<div class="flex justify-between items-center mb-1">
							<label class="block text-xs font-semibold uppercase text-gray-600">
								{{ __('Number of Questions') }}
							</label>
							<span class="text-xs font-bold text-violet-700 bg-violet-100 px-2 py-0.5 rounded-full">
								{{ form.number_of_questions }} Questions
							</span>
						</div>
						<input
							v-model.number="form.number_of_questions"
							type="range"
							min="5"
							max="50"
							step="5"
							class="w-full accent-violet-600 cursor-pointer"
						/>
						<div class="flex justify-between text-[10px] text-gray-400 mt-0.5">
							<span>5</span>
							<span>15</span>
							<span>30</span>
							<span>50</span>
						</div>
					</div>

					<div>
						<label class="block text-xs font-semibold uppercase text-gray-600 mb-1">
							{{ __('Marks per Question (Optional)') }}
						</label>
						<input
							v-model.number="form.marks_per_question"
							type="number"
							min="1"
							max="20"
							placeholder="Leave empty for proportional marks"
							class="w-full text-sm rounded-lg border-gray-300 focus:border-violet-500 focus:ring-violet-500"
						/>
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
					:disabled="!form.subject || isGenerating"
					@click="submitGenerate"
				>
					<template #prefix>
						<span class="lucide-sparkles size-4"></span>
					</template>
					{{ isGenerating ? __('Synthesizing Questions...') : __('Generate Questions') }}
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
	availableChapters?: string[]
	analysisName?: string
}>()

const emit = defineEmits<{
	(e: 'update:modelValue', value: boolean): void
	(e: 'generated', questions: any[]): void
}>()

const isOpen = computed({
	get: () => props.modelValue,
	set: (val) => emit('update:modelValue', val),
})

const form = ref({
	subject: props.subject || '',
	batch: props.batch || '',
	chapter: '',
	number_of_questions: 10,
	question_type: 'Mixed',
	difficulty: 'Mixed',
	marks_per_question: null as number | null,
})

const isGenerating = ref(false)
const errorMessage = ref('')

watch(
	() => props.subject,
	(val) => {
		if (val) form.value.subject = val
	}
)

function closeModal() {
	isOpen.value = false
	errorMessage.value = ''
}

async function submitGenerate() {
	if (!form.value.subject) return
	isGenerating.value = true
	errorMessage.value = ''

	try {
		const res = await createResource({
			url: 'lms.lms.ai.previous_year_api.api_generate_questions_from_history',
			params: {
				course: props.course,
				subject: form.value.subject,
				batch: form.value.batch,
				chapter: form.value.chapter,
				number_of_questions: form.value.number_of_questions,
				question_type: form.value.question_type,
				difficulty: form.value.difficulty,
				marks_per_question: form.value.marks_per_question,
				analysis_name: props.analysisName,
			},
		}).fetch()

		if (res && res.questions) {
			toast.success(`Generated ${res.questions.length} novel examination questions for review.`)
			emit('generated', res.questions)
			closeModal()
		} else {
			throw new Error('No questions generated. Please verify historical analysis.')
		}
	} catch (err: any) {
		errorMessage.value = err.message || 'Generation failed. Please try again.'
	} finally {
		isGenerating.value = false
	}
}
</script>
