<template>
	<PageHeader :breadcrumbs="breadcrumbs" />

	<div class="p-4 md:p-6 space-y-6 max-w-7xl mx-auto w-full">
		<!-- Executive Header & KPI Metric Summary Cards -->
		<div class="space-y-4">
			<div>
				<h1 class="text-2xl font-bold tracking-tight text-ink-gray-9 flex items-center gap-2">
					<span class="lucide-shield-check size-6 text-violet-600"></span>
					{{ __('Principal Approval Center') }}
				</h1>
				<p class="text-sm text-ink-gray-5 mt-1">
					{{ __('Centralized approval hub. Review, validate, approve, or request changes for all submitted question papers, quizzes, assessments, courses, batches, lessons, and chapters.') }}
				</p>
			</div>

			<!-- KPI Cards Grid (Clickable Category Selectors) -->
			<div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
				<!-- KPI 1: All -->
				<button
					type="button"
					class="p-4 rounded-xl border text-left transition-all flex flex-col justify-between"
					:class="activeCategory === 'All' ? 'border-violet-600 bg-violet-50/80 shadow-sm ring-2 ring-violet-500/20' : 'border-outline-gray-2 bg-surface-white hover:border-outline-gray-3 hover:shadow-xs'"
					@click="activeCategory = 'All'"
				>
					<div class="flex items-center justify-between text-xs font-medium text-ink-gray-6 mb-2">
						<span>{{ __('All Approvals') }}</span>
						<span class="lucide-layers size-4 text-violet-600"></span>
					</div>
					<div class="text-2xl font-bold text-ink-gray-9">{{ totalCount }}</div>
					<div class="text-[11px] text-ink-gray-5 mt-1">{{ __('Total Pending') }}</div>
				</button>

				<!-- KPI 2: Question Papers -->
				<button
					type="button"
					class="p-4 rounded-xl border text-left transition-all flex flex-col justify-between"
					:class="activeCategory === 'Question Paper' ? 'border-violet-600 bg-violet-50/80 shadow-sm ring-2 ring-violet-500/20' : 'border-outline-gray-2 bg-surface-white hover:border-outline-gray-3 hover:shadow-xs'"
					@click="activeCategory = 'Question Paper'"
				>
					<div class="flex items-center justify-between text-xs font-medium text-ink-gray-6 mb-2">
						<span>{{ __('Question Papers') }}</span>
						<span class="lucide-file-text size-4 text-violet-600"></span>
					</div>
					<div class="text-2xl font-bold text-violet-700">{{ counts['Question Paper'] || 0 }}</div>
					<div class="text-[11px] text-ink-gray-5 mt-1">{{ __('Examination Papers') }}</div>
				</button>

				<!-- KPI 3: Quizzes -->
				<button
					type="button"
					class="p-4 rounded-xl border text-left transition-all flex flex-col justify-between"
					:class="activeCategory === 'Quiz' ? 'border-amber-600 bg-amber-50/80 shadow-sm ring-2 ring-amber-500/20' : 'border-outline-gray-2 bg-surface-white hover:border-outline-gray-3 hover:shadow-xs'"
					@click="activeCategory = 'Quiz'"
				>
					<div class="flex items-center justify-between text-xs font-medium text-ink-gray-6 mb-2">
						<span>{{ __('Quizzes') }}</span>
						<span class="lucide-help-circle size-4 text-amber-600"></span>
					</div>
					<div class="text-2xl font-bold text-amber-700">{{ counts['Quiz'] || 0 }}</div>
					<div class="text-[11px] text-ink-gray-5 mt-1">{{ __('Course Quizzes') }}</div>
				</button>

				<!-- KPI 4: Assessments -->
				<button
					type="button"
					class="p-4 rounded-xl border text-left transition-all flex flex-col justify-between"
					:class="activeCategory === 'Assessment' ? 'border-teal-600 bg-teal-50/80 shadow-sm ring-2 ring-teal-500/20' : 'border-outline-gray-2 bg-surface-white hover:border-outline-gray-3 hover:shadow-xs'"
					@click="activeCategory = 'Assessment'"
				>
					<div class="flex items-center justify-between text-xs font-medium text-ink-gray-6 mb-2">
						<span>{{ __('Assessments') }}</span>
						<span class="lucide-clipboard-check size-4 text-teal-600"></span>
					</div>
					<div class="text-2xl font-bold text-teal-700">{{ counts['Assessment'] || 0 }}</div>
					<div class="text-[11px] text-ink-gray-5 mt-1">{{ __('Batch Assessments') }}</div>
				</button>

				<!-- KPI 5: Courses & Batches -->
				<button
					type="button"
					class="p-4 rounded-xl border text-left transition-all flex flex-col justify-between"
					:class="(activeCategory === 'Course' || activeCategory === 'Batch') ? 'border-cyan-600 bg-cyan-50/80 shadow-sm ring-2 ring-cyan-500/20' : 'border-outline-gray-2 bg-surface-white hover:border-outline-gray-3 hover:shadow-xs'"
					@click="activeCategory = 'Course'"
				>
					<div class="flex items-center justify-between text-xs font-medium text-ink-gray-6 mb-2">
						<span>{{ __('Courses / Batches') }}</span>
						<span class="lucide-graduation-cap size-4 text-cyan-600"></span>
					</div>
					<div class="text-2xl font-bold text-cyan-700">{{ (counts['Course'] || 0) + (counts['Batch'] || 0) }}</div>
					<div class="text-[11px] text-ink-gray-5 mt-1">{{ __('Programs & Batches') }}</div>
				</button>

				<!-- KPI 6: Lessons & Chapters -->
				<button
					type="button"
					class="p-4 rounded-xl border text-left transition-all flex flex-col justify-between"
					:class="activeCategory === 'Lesson & Chapter' ? 'border-purple-600 bg-purple-50/80 shadow-sm ring-2 ring-purple-500/20' : 'border-outline-gray-2 bg-surface-white hover:border-outline-gray-3 hover:shadow-xs'"
					@click="activeCategory = 'Lesson & Chapter'"
				>
					<div class="flex items-center justify-between text-xs font-medium text-ink-gray-6 mb-2">
						<span>{{ __('Lessons / Units') }}</span>
						<span class="lucide-book-open size-4 text-purple-600"></span>
					</div>
					<div class="text-2xl font-bold text-purple-700">{{ (counts['Lesson'] || 0) + (counts['Chapter'] || 0) }}</div>
					<div class="text-[11px] text-ink-gray-5 mt-1">{{ __('Chapters & Lessons') }}</div>
				</button>
			</div>
		</div>

		<!-- Category Navigation Tabs -->
		<div class="flex items-center gap-2 border-b border-outline-gray-2 overflow-x-auto pb-px">
			<button
				v-for="cat in categoryTabs"
				:key="cat.id"
				type="button"
				class="inline-flex items-center gap-2 px-3.5 py-2.5 text-sm font-semibold border-b-2 whitespace-nowrap transition-colors"
				:class="activeCategory === cat.id ? 'border-violet-600 text-violet-700 bg-violet-50/40' : 'border-transparent text-ink-gray-6 hover:text-ink-gray-9 hover:border-gray-300'"
				@click="activeCategory = cat.id"
			>
				<span :class="cat.icon" class="size-4"></span>
				<span>{{ __(cat.label) }}</span>
				<Badge
					v-if="cat.count"
					size="sm"
					:theme="activeCategory === cat.id ? 'purple' : 'gray'"
				>
					{{ cat.count }}
				</Badge>
			</button>
		</div>

		<!-- Main Content Section -->
		<div class="space-y-4">
			<!-- Loading State -->
			<div v-if="pendingContent.loading" class="flex items-center justify-center py-16 text-ink-gray-5">
				<LoadingIndicator class="size-6" />
				<span class="ml-2.5 text-sm font-medium">{{ __('Loading pending approvals...') }}</span>
			</div>

			<!-- Empty State -->
			<div
				v-else-if="!filteredItems.length"
				class="text-center py-16 px-4 rounded-xl border border-dashed border-outline-gray-2 bg-surface-white space-y-2"
			>
				<div class="inline-flex p-3 rounded-full bg-violet-50 text-violet-600 mb-2">
					<span class="lucide-check-circle-2 size-8"></span>
				</div>
				<h3 class="text-base font-semibold text-ink-gray-9">{{ __('All Caught Up!') }}</h3>
				<p class="text-sm text-ink-gray-5 max-w-md mx-auto">
					{{ getEmptyStateMessage() }}
				</p>
			</div>

			<!-- Filter Bar & Cards Grid -->
			<div v-else class="space-y-4">
				<!-- Search and Bulk Action Bar -->
				<div class="flex flex-wrap items-center justify-between gap-3 bg-surface-gray-2 p-3.5 rounded-xl border border-outline-gray-2">
					<div class="flex items-center gap-3 flex-1 min-w-[260px] max-w-md">
						<div class="relative w-full">
							<span class="lucide-search absolute left-3 top-1/2 -translate-y-1/2 size-4 text-ink-gray-4"></span>
							<input
								v-model="searchQuery"
								type="text"
								:placeholder="__('Search title, course, subject, or teacher...')"
								class="w-full pl-9 pr-3 py-1.5 text-xs rounded-lg border border-outline-gray-2 bg-surface-white focus:outline-none focus:border-violet-500"
							/>
						</div>
						<span class="text-xs text-ink-gray-5 whitespace-nowrap font-medium">
							{{ __('Showing :count items', { count: filteredItems.length }) }}
						</span>
					</div>

					<div class="flex items-center gap-2">
						<Button
							variant="ghost"
							size="sm"
							:loading="pendingContent.loading"
							@click="pendingContent.reload()"
							title="Refresh approvals"
						>
							<template #prefix><span class="lucide-refresh-cw size-3.5"></span></template>
							{{ __('Refresh') }}
						</Button>

						<Button
							v-if="filteredItems.length > 1"
							variant="solid"
							theme="green"
							size="sm"
							:loading="isSubmitting"
							@click="confirmApproveAll"
						>
							<template #prefix><span class="lucide-check-check size-3.5"></span></template>
							{{ __('Approve All (:count)', { count: filteredItems.length }) }}
						</Button>
					</div>
				</div>

				<!-- Grid of Pending Content Cards -->
				<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
					<div
						v-for="item in filteredItems"
						:key="item.key"
						class="flex flex-col justify-between p-5 border border-outline-gray-2 rounded-xl bg-surface-white shadow-xs hover:shadow-md hover:border-violet-200 transition-all space-y-4"
					>
						<div>
							<!-- Card Top Badges -->
							<div class="flex items-center justify-between gap-2 mb-2.5 flex-wrap">
								<div class="flex items-center gap-1.5">
									<Badge :theme="getCategoryBadgeTheme(item.content_type)" size="sm">
										<template #prefix>
											<span :class="getCategoryIcon(item.content_type)" class="size-3 mr-1"></span>
										</template>
										{{ getCategoryLabel(item.content_type) }}
									</Badge>
									<Badge v-if="item.has_unreleased_edits" theme="orange" size="sm">
										{{ __('Unreleased Edits') }}
									</Badge>
								</div>
								<span class="text-xs text-ink-gray-5">
									{{ formatDate(item.modified) }}
								</span>
							</div>

							<!-- Title -->
							<h3 class="text-base font-semibold text-ink-gray-9 line-clamp-2" :title="item.title">
								{{ item.title }}
							</h3>

							<!-- Metadata Rows -->
							<div class="mt-3.5 space-y-1.5 text-xs text-ink-gray-6">
								<!-- Course -->
								<div v-if="item.course_title && item.content_type !== 'Course'" class="flex items-center gap-1.5 truncate">
									<span class="font-medium text-ink-gray-7">{{ __('Course:') }}</span>
									<router-link
										v-if="item.course"
										:to="{ name: 'CourseDetail', params: { courseName: item.course } }"
										class="text-blue-600 hover:underline truncate"
									>
										{{ item.course_title }}
									</router-link>
									<span v-else class="truncate">{{ item.course_title }}</span>
								</div>

								<!-- Batch -->
								<div v-if="item.batch_title && item.content_type !== 'Batch'" class="flex items-center gap-1.5 truncate">
									<span class="font-medium text-ink-gray-7">{{ __('Batch:') }}</span>
									<router-link
										v-if="item.batch"
										:to="{ name: 'BatchDetail', params: { batchName: item.batch } }"
										class="text-blue-600 hover:underline truncate"
									>
										{{ item.batch_title }}
									</router-link>
									<span v-else class="truncate">{{ item.batch_title }}</span>
								</div>

								<!-- Chapter / Lesson -->
								<div v-if="item.chapter_title" class="flex items-center gap-1.5 truncate">
									<span class="font-medium text-ink-gray-7">{{ __('Chapter:') }}</span>
									<span class="truncate">{{ item.chapter_title }}</span>
								</div>

								<!-- Subject / Class for Question Paper -->
								<div v-if="item.class_level || item.subject" class="flex items-center gap-1.5 truncate">
									<span class="font-medium text-ink-gray-7">{{ __('Subject:') }}</span>
									<span class="truncate">{{ item.subject }} &bull; {{ item.class_level }}</span>
								</div>

								<!-- Marks -->
								<div v-if="item.total_marks" class="flex items-center gap-1.5 truncate">
									<span class="font-medium text-ink-gray-7">{{ __('Total Marks:') }}</span>
									<span class="truncate font-semibold text-ink-gray-8">{{ item.total_marks }} {{ __('Marks') }}</span>
								</div>

								<!-- Start Date for Batch -->
								<div v-if="item.start_date" class="flex items-center gap-1.5 truncate">
									<span class="font-medium text-ink-gray-7">{{ __('Start Date:') }}</span>
									<span class="truncate">{{ formatDate(item.start_date) }}</span>
								</div>

								<!-- Submitter -->
								<div class="flex items-center gap-1.5 truncate pt-1">
									<span class="font-medium text-ink-gray-7">{{ __('Submitted by:') }}</span>
									<span class="truncate font-medium text-ink-gray-8">{{ item.owner }}</span>
								</div>
							</div>
						</div>

						<!-- Card Actions Footer -->
						<div class="pt-3 border-t border-outline-gray-1 flex flex-col gap-2.5">
							<div class="flex items-center justify-between gap-2">
								<router-link
									v-if="getItemLink(item)"
									v-external
									:to="getItemLink(item)"
									class="text-xs font-semibold text-blue-600 hover:underline flex items-center gap-1"
								>
									<span>{{ __('Preview Content') }}</span>
									<span class="lucide-external-link size-3" />
								</router-link>
								<div v-else />
							</div>

							<div class="grid grid-cols-2 gap-2 w-full">
								<Button
									variant="solid"
									theme="green"
									size="sm"
									class="w-full justify-center text-xs whitespace-nowrap"
									:loading="isSubmitting"
									@click="handleAction(item.doctype, item.name, 'Approve')"
								>
									<template #prefix><span class="lucide-check size-3.5"></span></template>
									{{ __('Approve & Publish') }}
								</Button>
								<Button
									variant="outline"
									theme="red"
									size="sm"
									class="w-full justify-center text-xs whitespace-nowrap"
									:loading="isSubmitting"
									@click="openRejectModal(item.doctype, item.name)"
								>
									<template #prefix><span class="lucide-x size-3.5"></span></template>
									{{ __('Reject / Changes') }}
								</Button>
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>

	<!-- Rejection Modal -->
	<Dialog v-model="showRejectModal" :title="__('Reject / Request Changes')">
		<template #body-content>
			<div class="p-4 space-y-4">
				<p class="text-sm text-ink-gray-7">
					{{ __('Please provide specific feedback or requested changes so the creator/teacher can revise and resubmit.') }}
				</p>
				<Textarea
					v-model="rejectReason"
					:placeholder="__('Specify required changes or reason for rejection...')"
					rows="4"
					class="w-full"
				/>
			</div>
		</template>
		<template #actions>
			<div class="flex justify-end gap-2 p-4 border-t">
				<Button variant="ghost" @click="showRejectModal = false">{{ __('Cancel') }}</Button>
				<Button variant="solid" theme="red" :loading="isSubmitting" @click="confirmReject">
					{{ __('Confirm Rejection / Request Changes') }}
				</Button>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import { ref, computed, inject, getCurrentInstance } from 'vue'
import {
	createResource,
	Button,
	Badge,
	Dialog,
	Textarea,
	LoadingIndicator,
	toast,
	call,
} from 'frappe-ui'
import PageHeader from '@/components/Layouts/PageHeader.vue'

const activeCategory = ref('All')
const searchQuery = ref('')
const showRejectModal = ref(false)
const rejectReason = ref('')
const rejectTarget = ref(null)
const isSubmitting = ref(false)
const dayjs = inject('$dayjs')
const { $dialog } = getCurrentInstance().appContext.config.globalProperties

const breadcrumbs = computed(() => [
	{
		label: __('Principal Dashboard'),
		route: { name: 'PrincipalDashboard' },
	},
])

const pendingContent = createResource({
	url: 'lms.lms.api.get_pending_content_for_principal',
	auto: true,
})

const allPendingItems = computed(() => pendingContent.data || [])

const counts = computed(() => {
	const c = {
		'Question Paper': 0,
		Quiz: 0,
		Assessment: 0,
		Course: 0,
		Batch: 0,
		Lesson: 0,
		Chapter: 0,
	}
	for (const it of allPendingItems.value) {
		if (c[it.content_type] !== undefined) {
			c[it.content_type]++
		} else {
			c[it.content_type] = 1
		}
	}
	return c
})

const totalCount = computed(() => allPendingItems.value.length)

const categoryTabs = computed(() => [
	{
		id: 'All',
		label: 'All Approvals',
		icon: 'lucide-layers',
		count: totalCount.value,
	},
	{
		id: 'Question Paper',
		label: 'Question Paper Approvals',
		icon: 'lucide-file-text',
		count: counts.value['Question Paper'] || 0,
	},
	{
		id: 'Quiz',
		label: 'Quiz Approvals',
		icon: 'lucide-help-circle',
		count: counts.value['Quiz'] || 0,
	},
	{
		id: 'Assessment',
		label: 'Assessment Approvals',
		icon: 'lucide-clipboard-check',
		count: counts.value['Assessment'] || 0,
	},
	{
		id: 'Course',
		label: 'Course Approvals',
		icon: 'lucide-graduation-cap',
		count: counts.value['Course'] || 0,
	},
	{
		id: 'Batch',
		label: 'Batch Approvals',
		icon: 'lucide-users',
		count: counts.value['Batch'] || 0,
	},
	{
		id: 'Lesson & Chapter',
		label: 'Lessons & Chapters',
		icon: 'lucide-book-open',
		count: (counts.value['Lesson'] || 0) + (counts.value['Chapter'] || 0),
	},
])

const filteredItems = computed(() => {
	let list = allPendingItems.value

	// 1. Filter by category
	if (activeCategory.value === 'Question Paper') {
		list = list.filter((it) => it.content_type === 'Question Paper')
	} else if (activeCategory.value === 'Quiz') {
		list = list.filter((it) => it.content_type === 'Quiz')
	} else if (activeCategory.value === 'Assessment') {
		list = list.filter((it) => it.content_type === 'Assessment')
	} else if (activeCategory.value === 'Course') {
		list = list.filter((it) => it.content_type === 'Course')
	} else if (activeCategory.value === 'Batch') {
		list = list.filter((it) => it.content_type === 'Batch')
	} else if (activeCategory.value === 'Lesson & Chapter') {
		list = list.filter(
			(it) => it.content_type === 'Lesson' || it.content_type === 'Chapter'
		)
	}

	// 2. Filter by search query
	const q = searchQuery.value.trim().toLowerCase()
	if (q) {
		list = list.filter((it) => {
			return (
				(it.title && it.title.toLowerCase().includes(q)) ||
				(it.course_title && it.course_title.toLowerCase().includes(q)) ||
				(it.batch_title && it.batch_title.toLowerCase().includes(q)) ||
				(it.subject && it.subject.toLowerCase().includes(q)) ||
				(it.owner && it.owner.toLowerCase().includes(q))
			)
		})
	}

	return list
})

const getCategoryLabel = (type) => {
	switch (type) {
		case 'Question Paper':
			return __('Question Paper')
		case 'Quiz':
			return __('Quiz')
		case 'Assessment':
			return __('Assessment')
		case 'Course':
			return __('Course')
		case 'Batch':
			return __('Batch')
		case 'Lesson':
			return __('Lesson')
		case 'Chapter':
			return __('Chapter')
		default:
			return type
	}
}

const getCategoryBadgeTheme = (type) => {
	switch (type) {
		case 'Question Paper':
			return 'violet'
		case 'Quiz':
			return 'orange'
		case 'Assessment':
			return 'teal'
		case 'Course':
			return 'cyan'
		case 'Batch':
			return 'amber'
		case 'Lesson':
			return 'blue'
		case 'Chapter':
			return 'purple'
		default:
			return 'gray'
	}
}

const getCategoryIcon = (type) => {
	switch (type) {
		case 'Question Paper':
			return 'lucide-file-text'
		case 'Quiz':
			return 'lucide-help-circle'
		case 'Assessment':
			return 'lucide-clipboard-check'
		case 'Course':
			return 'lucide-graduation-cap'
		case 'Batch':
			return 'lucide-users'
		case 'Lesson':
			return 'lucide-book'
		case 'Chapter':
			return 'lucide-layers'
		default:
			return 'lucide-file'
	}
}

const formatDate = (dateStr) => {
	if (!dateStr) return ''
	if (dayjs) return dayjs(dateStr).format('DD MMM YYYY, HH:mm')
	return dateStr
}

const getItemLink = (item) => {
	if (item.doctype === 'LMS Course') {
		return { name: 'CourseDetail', params: { courseName: item.name } }
	}
	if (item.doctype === 'LMS Batch') {
		return { name: 'BatchDetail', params: { batchName: item.name } }
	}
	if (item.doctype === 'Course Lesson') {
		if (item.course && item.chapter_number && item.lesson_number) {
			return {
				name: 'Lesson',
				params: {
					courseName: item.course,
					chapterNumber: String(item.chapter_number),
					lessonNumber: String(item.lesson_number),
				},
			}
		}
		if (item.course) {
			return { name: 'CourseDetail', params: { courseName: item.course } }
		}
	}
	if (item.doctype === 'Course Chapter' && item.course) {
		return { name: 'CourseDetail', params: { courseName: item.course } }
	}
	if (item.doctype === 'LMS Quiz') {
		return { name: 'QuizPage', params: { quizID: item.name } }
	}
	if (item.doctype === 'LMS Assessment' && item.batch) {
		return { name: 'BatchDetail', params: { batchName: item.batch } }
	}
	if (item.doctype === 'AI Question Paper') {
		return { name: 'AIQuestionPaperGenerator', query: { paper: item.name } }
	}
	return null
}

const getEmptyStateMessage = () => {
	switch (activeCategory.value) {
		case 'Question Paper':
			return __('No question papers currently pending Principal approval.')
		case 'Quiz':
			return __('No quizzes currently pending Principal approval.')
		case 'Assessment':
			return __('No batch assessments currently pending Principal approval.')
		case 'Course':
			return __('No courses currently pending Principal approval.')
		case 'Batch':
			return __('No batches currently pending Principal approval.')
		case 'Lesson & Chapter':
			return __('No lessons or chapters currently pending Principal approval.')
		default:
			return __('No pending approvals found across any category. Newly submitted courses, batches, quizzes, assessments, and examination papers will appear here.')
	}
}

const handleAction = async (doctype, name, action, comments = '') => {
	try {
		isSubmitting.value = true
		await call('lms.lms.api.process_approval', {
			doctype: doctype,
			docname: name,
			action: action,
			comments: comments,
		})
		toast.success(__('Action completed successfully'))
		await pendingContent.reload()
	} catch (error) {
		toast.error(error.message || __('Failed to process action'))
	} finally {
		isSubmitting.value = false
	}
}

const openRejectModal = (doctype, name) => {
	rejectTarget.value = { doctype, name }
	rejectReason.value = ''
	showRejectModal.value = true
}

const confirmReject = async () => {
	if (!rejectReason.value.trim()) {
		toast.error(__('Reason is required'))
		return
	}
	isSubmitting.value = true
	await handleAction(
		rejectTarget.value.doctype,
		rejectTarget.value.name,
		'Reject',
		rejectReason.value
	)
	isSubmitting.value = false
	showRejectModal.value = false
}

const confirmApproveAll = () => {
	$dialog({
		title: __('Approve All Pending Items?'),
		message: __(
			'Are you sure you want to approve and publish all {0} pending items in this category?',
			[filteredItems.value.length]
		),
		actions: [
			{
				label: __('Cancel'),
				variant: 'outline',
				onClick: (close) => close(),
			},
			{
				label: __('Approve All'),
				variant: 'solid',
				theme: 'green',
				onClick: async (close) => {
					isSubmitting.value = true
					try {
						for (const item of filteredItems.value) {
							await call('lms.lms.api.process_approval', {
								doctype: item.doctype,
								docname: item.name,
								action: 'Approve',
							})
						}
						toast.success(__('All items approved successfully'))
						await pendingContent.reload()
					} catch (e) {
						toast.error(e.message || __('Failed to approve some items'))
					} finally {
						isSubmitting.value = false
						close()
					}
				},
			},
		],
	})
}
</script>
