<template>
	<Dialog
		v-model="isOpen"
		:options="{
			title: __('Upload Previous Year Examination Paper'),
			size: '2xl',
		}"
	>
		<template #body-content>
			<div class="space-y-4">
				<p class="text-sm text-gray-500">
					{{ __('Upload past examination papers (10+ years supported). Supported file formats: PDF, DOCX, Scanned PDF, JPG, PNG.') }}
				</p>

				<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
					<div>
						<label class="block text-xs font-semibold uppercase text-gray-600 mb-1">
							{{ __('Course') }} <span class="text-red-500">*</span>
						</label>
						<select
							v-model="form.course"
							class="w-full text-sm rounded-lg border-gray-300 focus:border-violet-500 focus:ring-violet-500"
							:disabled="isCourseLocked"
						>
							<option value="">{{ __('Select Course') }}</option>
							<option v-for="c in courses" :key="c.name" :value="c.name">
								{{ c.title || c.name }}
							</option>
						</select>
					</div>

					<div>
						<label class="block text-xs font-semibold uppercase text-gray-600 mb-1">
							{{ __('Subject') }} <span class="text-red-500">*</span>
						</label>
						<input
							v-model="form.subject"
							type="text"
							placeholder="e.g. Java Programming, Data Structures"
							class="w-full text-sm rounded-lg border-gray-300 focus:border-violet-500 focus:ring-violet-500"
						/>
					</div>

					<div>
						<label class="block text-xs font-semibold uppercase text-gray-600 mb-1">
							{{ __('Examination Year') }} <span class="text-red-500">*</span>
						</label>
						<input
							v-model.number="form.examination_year"
							type="number"
							min="1990"
							max="2035"
							placeholder="e.g. 2024, 2021, 2017"
							class="w-full text-sm rounded-lg border-gray-300 focus:border-violet-500 focus:ring-violet-500"
						/>
					</div>

					<div>
						<label class="block text-xs font-semibold uppercase text-gray-600 mb-1">
							{{ __('Academic Year') }}
						</label>
						<input
							v-model="form.academic_year"
							type="text"
							placeholder="e.g. 2023-2024"
							class="w-full text-sm rounded-lg border-gray-300 focus:border-violet-500 focus:ring-violet-500"
						/>
					</div>

					<div>
						<label class="block text-xs font-semibold uppercase text-gray-600 mb-1">
							{{ __('Examination Type') }}
						</label>
						<select
							v-model="form.examination_type"
							class="w-full text-sm rounded-lg border-gray-300 focus:border-violet-500 focus:ring-violet-500"
						>
							<option value="Annual Examination">Annual Examination</option>
							<option value="Semester Examination">Semester Examination</option>
							<option value="Final Examination">Final Examination</option>
							<option value="Midterm Examination">Midterm Examination</option>
							<option value="Unit Test">Unit Test</option>
							<option value="Model Examination">Model Examination</option>
							<option value="Supplementary Examination">Supplementary Examination</option>
						</select>
					</div>

					<div>
						<label class="block text-xs font-semibold uppercase text-gray-600 mb-1">
							{{ __('Board / University') }}
						</label>
						<input
							v-model="form.board_university"
							type="text"
							placeholder="e.g. Izensphere Autonomous University, State Board"
							class="w-full text-sm rounded-lg border-gray-300 focus:border-violet-500 focus:ring-violet-500"
						/>
					</div>

					<div>
						<label class="block text-xs font-semibold uppercase text-gray-600 mb-1">
							{{ __('Question Paper Title') }} <span class="text-red-500">*</span>
						</label>
						<input
							v-model="form.title"
							type="text"
							placeholder="e.g. MCA Semester 3 - Java Programming 2024"
							class="w-full text-sm rounded-lg border-gray-300 focus:border-violet-500 focus:ring-violet-500"
						/>
					</div>

					<div>
						<label class="block text-xs font-semibold uppercase text-gray-600 mb-1">
							{{ __('Maximum Marks') }}
						</label>
						<input
							v-model.number="form.max_marks"
							type="number"
							placeholder="100"
							class="w-full text-sm rounded-lg border-gray-300 focus:border-violet-500 focus:ring-violet-500"
						/>
					</div>
				</div>

				<!-- File Attachment Area -->
				<div class="mt-4">
					<label class="block text-xs font-semibold uppercase text-gray-600 mb-2">
						{{ __('Question Paper File Attachment') }} <span class="text-red-500">*</span>
					</label>

					<div
						class="border-2 border-dashed rounded-xl p-6 text-center transition-colors cursor-pointer"
						:class="isDragging ? 'border-violet-500 bg-violet-50' : 'border-gray-300 hover:border-gray-400 bg-gray-50'"
						@dragover.prevent="isDragging = true"
						@dragleave.prevent="isDragging = false"
						@drop.prevent="handleFileDrop"
						@click="triggerFileInput"
					>
						<input
							ref="fileInputRef"
							type="file"
							accept=".pdf,.docx,.png,.jpg,.jpeg"
							class="hidden"
							@change="handleFileSelect"
						/>

						<div v-if="!selectedFile && !form.attachment" class="space-y-2">
							<span class="lucide-upload-cloud size-10 text-gray-400 mx-auto block"></span>
							<div class="text-sm font-medium text-gray-700">
								{{ __('Click or drag & drop question paper file here') }}
							</div>
							<div class="text-xs text-gray-400">
								PDF, DOCX, Scanned PDF, JPG, PNG (Max 50MB)
							</div>
						</div>

						<div v-else class="flex items-center justify-between bg-white p-3 rounded-lg border">
							<div class="flex items-center gap-3">
								<span class="lucide-file-text size-6 text-violet-600"></span>
								<div class="text-left">
									<div class="text-sm font-semibold text-gray-800">
										{{ selectedFile ? selectedFile.name : form.attachment }}
									</div>
									<div v-if="selectedFile" class="text-xs text-gray-400">
										{{ formatFileSize(selectedFile.size) }}
									</div>
								</div>
							</div>
							<Button
								variant="ghost"
								theme="red"
								size="sm"
								@click.stop="clearFile"
							>
								{{ __('Remove') }}
							</Button>
						</div>
					</div>
				</div>

				<!-- Error alert if any -->
				<div v-if="errorMessage" class="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700 flex items-center gap-2">
					<span class="lucide-alert-circle size-4 flex-shrink-0"></span>
					<span>{{ errorMessage }}</span>
				</div>
			</div>
		</template>

		<template #actions>
			<div class="flex items-center justify-between w-full">
				<div class="flex items-center gap-2 text-xs text-gray-500">
					<input
						v-model="form.auto_process"
						type="checkbox"
						id="autoProcessCheck"
						class="rounded text-violet-600 focus:ring-violet-500"
					/>
					<label for="autoProcessCheck">{{ __('Automatically extract questions upon upload') }}</label>
				</div>

				<div class="flex items-center gap-2">
					<Button
						variant="subtle"
						theme="gray"
						:disabled="isUploading"
						@click="closeModal"
					>
						{{ __('Cancel') }}
					</Button>
					<Button
						variant="solid"
						theme="violet"
						:loading="isUploading"
						:disabled="!isFormValid || isUploading"
						@click="submitUpload"
					>
						<template #prefix>
							<span class="lucide-upload size-4"></span>
						</template>
						{{ isUploading ? __('Uploading & Processing...') : __('Upload Paper') }}
					</Button>
				</div>
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
	defaultCourse?: string
	defaultSubject?: string
	courses?: Array<{ name: string; title: string }>
}>()

const emit = defineEmits<{
	(e: 'update:modelValue', value: boolean): void
	(e: 'uploaded', payload: any): void
}>()

const isOpen = computed({
	get: () => props.modelValue,
	set: (val) => emit('update:modelValue', val),
})

const isCourseLocked = computed(() => !!props.defaultCourse)

const form = ref({
	course: props.defaultCourse || '',
	subject: props.defaultSubject || '',
	title: '',
	examination_year: new Date().getFullYear(),
	academic_year: `${new Date().getFullYear() - 1}-${new Date().getFullYear()}`,
	examination_type: 'Annual Examination',
	board_university: '',
	max_marks: 100,
	duration: '3 Hours',
	attachment: '',
	auto_process: true,
})

const selectedFile = ref<File | null>(null)
const isDragging = ref(false)
const isUploading = ref(false)
const errorMessage = ref('')
const fileInputRef = ref<HTMLInputElement | null>(null)

watch(
	() => props.defaultCourse,
	(val) => {
		if (val) form.value.course = val
	}
)

watch(
	() => props.defaultSubject,
	(val) => {
		if (val) form.value.subject = val
	}
)

watch(
	[() => form.value.subject, () => form.value.examination_year],
	([sub, yr]) => {
		if (sub && yr && !form.value.title) {
			form.value.title = `${sub} - ${yr} Examination Paper`
		}
	}
)

const isFormValid = computed(() => {
	return (
		form.value.course &&
		form.value.subject &&
		form.value.title &&
		form.value.examination_year &&
		(selectedFile.value || form.value.attachment)
	)
})

function triggerFileInput() {
	fileInputRef.value?.click()
}

function handleFileSelect(e: Event) {
	const target = e.target as HTMLInputElement
	if (target.files && target.files[0]) {
		setFile(target.files[0])
	}
}

function handleFileDrop(e: DragEvent) {
	isDragging.value = false
	if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0]) {
		setFile(e.dataTransfer.files[0])
	}
}

function setFile(file: File) {
	const validExts = ['.pdf', '.docx', '.png', '.jpg', '.jpeg']
	const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase()
	if (!validExts.includes(ext)) {
		errorMessage.value = `Unsupported file format '${ext}'. Please upload a PDF, DOCX, PNG, or JPG.`
		return
	}
	errorMessage.value = ''
	selectedFile.value = file
	if (!form.value.title) {
		form.value.title = file.name.replace(/\.[^/.]+$/, '')
	}
}

function clearFile() {
	selectedFile.value = null
	form.value.attachment = ''
	if (fileInputRef.value) fileInputRef.value.value = ''
}

function formatFileSize(bytes: number): string {
	if (bytes === 0) return '0 B'
	const k = 1024
	const sizes = ['B', 'KB', 'MB', 'GB']
	const i = Math.floor(Math.log(bytes) / Math.log(k))
	return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

function closeModal() {
	isOpen.value = false
	errorMessage.value = ''
	selectedFile.value = null
}

async function uploadFileToFrappe(file: File): Promise<string> {
	const formData = new FormData()
	formData.append('file', file, file.name)
	formData.append('is_private', '0')
	formData.append('folder', 'Home')

	const res = await fetch('/api/method/upload_file', {
		method: 'POST',
		headers: {
			'X-Frappe-CSRF-Token': (window as any).csrf_token || '',
		},
		body: formData,
	})

	if (!res.ok) {
		throw new Error('File upload to server failed.')
	}

	const data = await res.json()
	return data.message.file_url
}

async function submitUpload() {
	if (!isFormValid.value) return
	isUploading.value = true
	errorMessage.value = ''

	try {
		let attachmentUrl = form.value.attachment
		if (selectedFile.value) {
			attachmentUrl = await uploadFileToFrappe(selectedFile.value)
		}

		const payload: Record<string, any> = {
			course: form.value.course,
			subject: form.value.subject,
			title: form.value.title,
			examination_year: Number(form.value.examination_year) || new Date().getFullYear(),
			examination_type: form.value.examination_type || 'Annual Examination',
			max_marks: Number(form.value.max_marks) || 100,
			duration: form.value.duration || '3 Hours',
			attachment: attachmentUrl,
			auto_process: form.value.auto_process ? 1 : 0,
		}
		if (form.value.academic_year && form.value.academic_year.trim()) {
			payload.academic_year = form.value.academic_year.trim()
		}
		if (form.value.board_university && form.value.board_university.trim()) {
			payload.board_university = form.value.board_university.trim()
		}

		const res = await createResource({
			url: 'lms.lms.ai.previous_year_api.api_upload_previous_year_paper',
			params: payload,
		}).fetch()

		toast.success(
			form.value.auto_process
				? 'Document uploaded and questions extracted.'
				: 'Document saved. Ready for extraction.'
		)

		emit('uploaded', res)
		closeModal()
	} catch (err: any) {
		errorMessage.value = err.message || 'Failed to upload paper. Please check required fields.'
	} finally {
		isUploading.value = false
	}
}
</script>
