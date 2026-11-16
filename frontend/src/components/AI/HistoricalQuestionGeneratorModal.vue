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
						<div class="flex justify-between items-center mb-1.5">
							<label class="block text-xs font-semibold uppercase text-gray-600">
								{{ __('Number of Questions') }} *
							</label>
							<span class="text-xs font-bold text-violet-700 bg-violet-100 px-2.5 py-0.5 rounded-full">
								{{ form.number_of_questions }} {{ __('Questions') }}
							</span>
						</div>

						<!-- Direct Number Input -->
						<div class="relative mb-2">
							<input
								v-model.number="form.number_of_questions"
								type="number"
								min="1"
								max="100"
								step="1"
								placeholder="e.g. 10"
								class="w-full text-sm font-semibold rounded-lg border-gray-300 focus:border-violet-500 focus:ring-violet-500 pr-16"
							/>
							<span class="absolute inset-y-0 right-3 flex items-center text-xs text-gray-400 pointer-events-none">
								{{ __('items') }}
							</span>
						</div>

						<!-- Quick Presets -->
						<div class="flex items-center gap-1.5 flex-wrap mb-2">
							<span class="text-[11px] text-gray-400 mr-1 font-medium">{{ __('Presets:') }}</span>
							<button
								v-for="count in [5, 10, 15, 20, 25, 30, 50]"
								:key="count"
								type="button"
								class="px-2.5 py-1 text-xs rounded-md border transition-all cursor-pointer font-medium"
								:class="form.number_of_questions === count ? 'bg-violet-600 text-white border-violet-600 font-bold shadow-sm' : 'bg-white text-gray-700 border-gray-200 hover:bg-gray-50 hover:border-violet-300'"
								@click="form.number_of_questions = count"
							>
								{{ count }}
							</button>
						</div>

						<!-- Styled Range Slider -->
						<input
							v-model.number="form.number_of_questions"
							type="range"
							min="1"
							max="50"
							step="1"
							class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-violet-600"
						/>
						<div class="flex justify-between text-[10px] text-gray-400 mt-1">
							<span>1</span>
							<span>10</span>
							<span>20</span>
							<span>30</span>
							<span>40</span>
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
		const payload: Record<string, any> = {
			course: props.course,
			subject: form.value.subject.trim(),
			number_of_questions: Number(form.value.number_of_questions) || 10,
			question_type: form.value.question_type || 'Mixed',
			difficulty: form.value.difficulty || 'Mixed',
		}
		if (form.value.batch && form.value.batch.trim()) {
			payload.batch = form.value.batch.trim()
		}
		if (form.value.chapter && form.value.chapter.trim()) {
			payload.chapter = form.value.chapter.trim()
		}
		if (
			form.value.marks_per_question !== null &&
			form.value.marks_per_question !== undefined &&
			String(form.value.marks_per_question).trim() !== '' &&
			!isNaN(Number(form.value.marks_per_question))
		) {
			payload.marks_per_question = Number(form.value.marks_per_question)
		}
		if (props.analysisName) {
			payload.analysis_name = props.analysisName
		}

		const res = await createResource({
			url: 'lms.lms.ai.previous_year_api.api_generate_questions_from_history',
			params: payload,
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
