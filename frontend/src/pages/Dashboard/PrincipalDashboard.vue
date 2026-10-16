<template>
	<PageHeader :breadcrumbs="breadcrumbs" />

	<div class="p-5">
		<Tabs v-model="activeTab" :tabs="tabs" class="mb-5">
			<template #tab="{ tab }">
				<div class="flex items-center gap-2">
					<span>{{ __(tab.label) }}</span>
					<Badge v-if="tab.count" theme="blue" size="sm">
						{{ tab.count }}
					</Badge>
				</div>
			</template>
		</Tabs>

		<!-- Tab 0: Pending Courses -->
		<div v-if="activeTab === 0" class="space-y-4">
			<div v-if="pendingCourses.loading" class="text-ink-gray-5">{{ __('Loading...') }}</div>
			<div v-else-if="!pendingCourses.data?.length" class="text-ink-gray-5">{{ __('No courses pending approval.') }}</div>
			<div v-else class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
				<div v-for="course in pendingCourses.data" :key="course.name" class="p-5 border border-gray-200 rounded-xl bg-white shadow-sm hover:shadow-md transition-shadow">
					<h3 class="text-lg font-medium">{{ course.title }}</h3>
					<p class="text-sm text-ink-gray-5 mt-1">{{ __('Instructor') }}: {{ course.owner }}</p>
					<div class="flex gap-2 mt-4">
						<Button variant="solid" theme="blue" @click="handleAction('LMS Course', course.name, 'Approve')">
							{{ __('Approve & Publish') }}
						</Button>
						<Button variant="outline" theme="red" @click="openRejectModal('LMS Course', course.name)">
							{{ __('Reject') }}
						</Button>
					</div>
				</div>
			</div>
		</div>

		<!-- Tab 1: Pending Batches -->
		<div v-if="activeTab === 1" class="space-y-4">
			<div v-if="pendingBatches.loading" class="text-ink-gray-5">{{ __('Loading...') }}</div>
			<div v-else-if="!pendingBatches.data?.length" class="text-ink-gray-5">{{ __('No batches pending approval.') }}</div>
			<div v-else class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
				<div v-for="batch in pendingBatches.data" :key="batch.name" class="p-5 border border-gray-200 rounded-xl bg-white shadow-sm hover:shadow-md transition-shadow">
					<h3 class="text-lg font-medium">{{ batch.title }}</h3>
					<p class="text-sm text-ink-gray-5 mt-1">{{ __('Start Date') }}: {{ batch.start_date }}</p>
					<div class="flex gap-2 mt-4">
						<Button variant="solid" theme="blue" @click="handleAction('LMS Batch', batch.name, 'Approve')">
							{{ __('Approve & Publish') }}
						</Button>
						<Button variant="outline" theme="red" @click="openRejectModal('LMS Batch', batch.name)">
							{{ __('Reject') }}
						</Button>
					</div>
				</div>
			</div>
		</div>

		<!-- Tab 2: Pending New Content in Courses & Batches -->
		<div v-if="activeTab === 2" class="space-y-4">
			<div v-if="pendingContent.loading" class="flex items-center justify-center py-12 text-ink-gray-5">
				<LoadingIndicator class="size-5" />
				<span class="ml-2">{{ __('Loading pending content...') }}</span>
			</div>
			<div v-else-if="!pendingContent.data?.length" class="text-center py-12 text-ink-gray-5">
				<p class="text-base font-medium">{{ __('No new content pending approval.') }}</p>
				<p class="text-sm mt-1 text-ink-gray-4">{{ __('When teachers submit newly added chapters, lessons, quizzes, or assessments in published courses and batches, they will appear here.') }}</p>
			</div>
			<div v-else class="space-y-4">
				<!-- Filter & Bulk Actions Bar -->
				<div class="flex flex-wrap items-center justify-between gap-3 bg-surface-gray-2 p-3.5 rounded-xl border border-outline-gray-2">
					<div class="flex items-center gap-2 flex-wrap">
						<span class="text-xs font-semibold uppercase tracking-wider text-ink-gray-5 mr-1">
							{{ __('Filter Type:') }}
						</span>
						<Button
							size="sm"
							:variant="contentFilter === 'All' ? 'solid' : 'subtle'"
							@click="contentFilter = 'All'"
						>
							{{ __('All') }} ({{ pendingContent.data?.length || 0 }})
						</Button>
						<Button
							v-for="type in availableContentTypes"
							:key="type"
							size="sm"
							:variant="contentFilter === type ? 'solid' : 'subtle'"
							@click="contentFilter = type"
						>
							{{ __(type) }} ({{ countByType(type) }})
						</Button>
					</div>

					<div class="flex items-center gap-2">
						<Button
							v-if="filteredContent.length > 1"
							variant="solid"
							theme="green"
							size="sm"
							:loading="isSubmitting"
							@click="confirmApproveAll"
						>
							<template #prefix>
								<span class="lucide-check-check size-3.5" />
							</template>
							{{ __('Approve All (:count)', { count: filteredContent.length }) }}
						</Button>
					</div>
				</div>

				<!-- Grid of Pending Content Cards -->
				<div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
					<div
						v-for="item in filteredContent"
						:key="item.key"
						class="flex flex-col justify-between p-5 border border-outline-gray-2 rounded-xl bg-surface-white shadow-sm hover:shadow-md transition-all space-y-4"
					>
						<div>
							<div class="flex items-center justify-between gap-2 mb-2.5">
								<Badge :theme="getContentTypeBadgeTheme(item.content_type)" size="sm">
									{{ __(item.content_type) }}
								</Badge>
								<Badge v-if="item.has_unreleased_edits" theme="orange" size="sm">
									{{ __('Unreleased Edits') }}
								</Badge>
								<span class="text-xs text-ink-gray-5">
									{{ formatDate(item.modified) }}
								</span>
							</div>

							<h3 class="text-lg font-semibold text-ink-gray-9 line-clamp-2">
								{{ item.title }}
							</h3>

							<div class="mt-3 space-y-1 text-xs text-ink-gray-6">
								<div v-if="item.course_title" class="flex items-center gap-1.5 truncate">
									<span class="font-medium text-ink-gray-7">{{ __('Course:') }}</span>
									<router-link
										:to="{ name: 'CourseDetail', params: { courseName: item.course } }"
										class="text-blue-600 hover:underline truncate"
									>
										{{ item.course_title }}
									</router-link>
								</div>
								<div v-if="item.chapter_title" class="flex items-center gap-1.5 truncate">
									<span class="font-medium text-ink-gray-7">{{ __('Chapter:') }}</span>
									<span class="truncate">{{ item.chapter_title }}</span>
								</div>
								<div v-if="item.batch_title" class="flex items-center gap-1.5 truncate">
									<span class="font-medium text-ink-gray-7">{{ __('Batch:') }}</span>
									<router-link
										:to="{ name: 'BatchDetail', params: { batchName: item.batch } }"
										class="text-blue-600 hover:underline truncate"
									>
										{{ item.batch_title }}
									</router-link>
								</div>
								<div class="flex items-center gap-1.5 truncate">
									<span class="font-medium text-ink-gray-7">{{ __('Submitted by:') }}</span>
									<span class="truncate">{{ item.owner }}</span>
								</div>
							</div>
						</div>

						<div class="pt-3 border-t border-outline-gray-1 flex items-center justify-between gap-2">
							<router-link
								v-if="getItemLink(item)"
								:to="getItemLink(item)"
								target="_blank"
								class="text-xs font-medium text-blue-600 hover:underline flex items-center gap-1"
							>
								<span>{{ __('Preview Content') }}</span>
								<span class="lucide-external-link size-3" />
							</router-link>
							<div v-else />

							<div class="flex items-center gap-2">
								<Button
									variant="solid"
									theme="green"
									size="sm"
									:loading="isSubmitting"
									@click="handleAction(item.doctype, item.name, 'Approve')"
								>
									{{ __('Approve and Publish') }}
								</Button>
								<Button
									variant="outline"
									theme="red"
									size="sm"
									:loading="isSubmitting"
									@click="openRejectModal(item.doctype, item.name)"
								>
									{{ __('Reject / Request Changes') }}
								</Button>
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>

	<Dialog v-model="showRejectModal" :title="__('Reject / Request Changes')">
		<template #body-content>
			<div class="p-4 space-y-4">
				<p class="text-sm text-ink-gray-7">{{ __('Please provide a reason or specify the changes requested from the teacher.') }}</p>
				<Textarea v-model="rejectReason" :placeholder="__('Rejection reason or requested changes...')" rows="4" class="w-full" />
			</div>
		</template>
		<template #actions>
			<div class="flex justify-end gap-2 p-4 border-t">
				<Button variant="ghost" @click="showRejectModal = false">{{ __('Cancel') }}</Button>
				<Button variant="solid" theme="red" @click="confirmReject" :loading="isSubmitting">{{ __('Confirm Rejection / Request Changes') }}</Button>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import { ref, computed, inject, watch, getCurrentInstance } from 'vue'
import {
	createResource,
	Button,
	Tabs,
	Badge,
	Dialog,
	Textarea,
	LoadingIndicator,
	toast,
	call,
} from 'frappe-ui'
import PageHeader from '@/components/Layouts/PageHeader.vue'

const activeTab = ref(0)
const showRejectModal = ref(false)
const rejectReason = ref('')
const rejectTarget = ref(null)
const isSubmitting = ref(false)
const contentFilter = ref('All')
const dayjs = inject('$dayjs')
const { $dialog } = getCurrentInstance().appContext.config.globalProperties

const breadcrumbs = computed(() => [
	{
		label: __('Principal Dashboard'),
		route: { name: 'PrincipalDashboard' },
	},
])

const pendingCourses = createResource({
	url: 'frappe.client.get_list',
	params: {
		doctype: 'LMS Course',
		filters: { workflow_state: 'Pending Principal Approval' },
		fields: ['name', 'title', 'owner', 'workflow_state'],
	},
	auto: true,
})

const pendingBatches = createResource({
	url: 'frappe.client.get_list',
	params: {
		doctype: 'LMS Batch',
		filters: { workflow_state: 'Pending Principal Approval' },
		fields: ['name', 'title', 'start_date', 'workflow_state'],
	},
	auto: true,
})

const pendingContent = createResource({
	url: 'lms.lms.api.get_pending_content_for_principal',
	auto: true,
})

const tabs = computed(() => [
	{ label: 'Pending Courses', count: pendingCourses.data?.length || 0 },
	{ label: 'Pending Batches', count: pendingBatches.data?.length || 0 },
	{ label: 'Pending New Content', count: pendingContent.data?.length || 0 },
])

watch(
	() => [pendingCourses.data, pendingBatches.data, pendingContent.data],
	([courses, batches, content]) => {
		if (courses && batches && content) {
			if (!courses.length && !batches.length && content.length && activeTab.value === 0) {
				activeTab.value = 2
			}
		}
	}
)

const availableContentTypes = computed(() => {
	const set = new Set()
	for (const it of pendingContent.data || []) {
		if (it.content_type) set.add(it.content_type)
	}
	return Array.from(set)
})

const countByType = (type) => {
	return (pendingContent.data || []).filter((it) => it.content_type === type).length
}

const filteredContent = computed(() => {
	const all = pendingContent.data || []
	if (contentFilter.value === 'All') return all
	return all.filter((it) => it.content_type === contentFilter.value)
})

const getContentTypeBadgeTheme = (type) => {
	switch (type) {
		case 'Lesson':
			return 'blue'
		case 'Chapter':
			return 'purple'
		case 'Quiz':
			return 'orange'
		case 'Assessment':
			return 'teal'
		default:
			return 'gray'
	}
}

const formatDate = (dateStr) => {
	if (!dateStr) return ''
	if (dayjs) return dayjs(dateStr).format('DD MMM YYYY, HH:mm')
	return dateStr
}

const getItemLink = (item) => {
	if (item.doctype === 'Course Lesson' && item.course) {
		return { name: 'CourseDetail', params: { courseName: item.course } }
	}
	if (item.doctype === 'Course Chapter' && item.course) {
		return { name: 'CourseDetail', params: { courseName: item.course } }
	}
	if (item.doctype === 'LMS Quiz') {
		return { name: 'QuizForm', params: { quizID: item.name } }
	}
	if (item.doctype === 'LMS Assessment' && item.batch) {
		return { name: 'BatchDetail', params: { batchName: item.batch } }
	}
	return null
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
		pendingCourses.reload()
		pendingBatches.reload()
		pendingContent.reload()
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
		title: __('Approve All Pending Content?'),
		message: __(
			'Are you sure you want to approve and publish all {0} pending content items to students?',
			[filteredContent.value.length]
		),
		actions: [
			{
				label: __('Cancel'),
				variant: 'outline',
				onClick: (close) => close(),
			},
			{
				label: __('Approve & Publish All'),
				variant: 'solid',
				theme: 'green',
				onClick: async (close) => {
					isSubmitting.value = true
					try {
						for (const item of filteredContent.value) {
							await call('lms.lms.api.process_approval', {
								doctype: item.doctype,
								docname: item.name,
								action: 'Approve',
							})
						}
						toast.success(__('All pending content approved and published successfully.'))
						pendingContent.reload()
					} catch (e) {
						toast.error(e.message || __('Failed to approve some content'))
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
