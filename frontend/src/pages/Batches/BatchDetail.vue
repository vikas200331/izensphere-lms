<template>
	<TabbedDetailPage
		ref="page"
		:tabs="tabs"
		:breadcrumbs="breadcrumbs"
		:published="Boolean(batch.data?.published)"
		:loading="!batch.data"
		:doc="batch"
		doc-prop="batch"
	>
		<template #actions="{ tab, instance }">
			<Badge v-if="tab?.key === 'settings' && instance?.isDirty" theme="orange">
				{{ __('Not Saved') }}
			</Badge>
			<!-- Batch Workflow Actions & Status (always visible when batch is loaded) -->
			<template v-if="batch.data">
				<Badge
					v-if="batch.data.workflow_state"
					:theme="getWorkflowBadgeTheme(batch.data.workflow_state)"
					size="sm"
				>
					{{ __(batch.data.workflow_state) }}
				</Badge>

				<!-- Teacher / Creator Submit / Resubmit -->
				<Button
					v-if="canSubmitForApproval"
					variant="solid"
					theme="blue"
					size="sm"
					:loading="workflowActionToggle.loading"
					@click="submitForApproval"
				>
					<template #prefix>
						<span class="lucide-file-check size-3.5" />
					</template>
					{{ batch.data.workflow_state === 'Rejected' ? __('Resubmit for Approval') : __('Submit for Principal Approval') }}
				</Button>

				<!-- Principal Approve & Publish -->
				<Button
					v-if="canPrincipalReviewBatch"
					variant="solid"
					theme="green"
					size="sm"
					:loading="approveActionToggle.loading"
					@click="approveBatch"
				>
					<template #prefix>
						<span class="lucide-check-check size-3.5" />
					</template>
					{{ __('Approve and Publish') }}
				</Button>

				<!-- Principal Reject / Request Changes -->
				<Button
					v-if="canPrincipalReviewBatch"
					variant="outline"
					theme="red"
					size="sm"
					:loading="rejectActionToggle.loading"
					@click="openBatchRejectModal"
				>
					<template #prefix>
						<span class="lucide-x size-3.5" />
					</template>
					{{ __('Reject / Request Changes') }}
				</Button>

				<!-- Principal Direct Publish -->
				<Button
					v-if="batch.data?.transitions?.includes('Publish')"
					variant="solid"
					theme="green"
					size="sm"
					:loading="publishToggle.loading"
					@click="togglePublishBatch"
				>
					<template #prefix>
						<span class="lucide-send size-3.5" />
					</template>
					{{ __('Publish') }}
				</Button>

				<!-- Principal Direct Unpublish -->
				<Button
					v-if="batch.data?.transitions?.includes('Unpublish')"
					variant="outline"
					theme="gray"
					size="sm"
					:loading="publishToggle.loading"
					@click="togglePublishBatch"
				>
					{{ __('Unpublish') }}
				</Button>
			</template>
			<Dropdown
				v-if="isAdmin && batchMenu(tab).length"
				:options="batchMenu(tab)"
				placement="left"
				side="left"
			>
				<template v-slot="{ open }">
					<Button
						variant="ghost"
						:label="__('Batch options')"
						:aria-expanded="open"
					>
						<template #icon>
							<span class="lucide-ellipsis-vertical w-4 h-4" />
						</template>
					</Button>
				</template>
			</Dropdown>
			<HeaderButton
				v-if="tab?.key === 'dashboard' && isAdmin && !isExpired"
				:label="__('Enroll')"
				icon="lucide-plus"
				@click="openStudentForm"
			/>
			<template v-if="tab?.key === 'announcements' && isAdmin && !readOnlyMode">
				<Tooltip
					v-if="!batch.data?.students?.length"
					:text="__('Add students to the batch to make an announcement')"
				>
					<HeaderButton
						:label="__('Make Announcement')"
						icon="lucide-send"
						disabled
					/>
				</Tooltip>
				<HeaderButton
					v-else
					:label="__('Make Announcement')"
					icon="lucide-send"
					@click="openAnnouncementModal"
				/>
			</template>
			<ShortcutTooltip
				v-if="tab?.key === 'settings' && isAdmin"
				:label="__('Save')"
				combo="Mod+S"
			>
				<HeaderButton
					:label="__('Save')"
					variant="solid"
					@click="instance?.submitBatch()"
				/>
			</ShortcutTooltip>
		</template>

		<template #solo>
			<div
				v-if="batch.data?.workflow_state === 'Rejected' && rejectionReason.data && rejectionReason.data.length > 0"
				class="mx-4 sm:mx-10 mt-4 p-4 bg-red-50 text-red-700 rounded-lg border border-red-200"
			>
				<div class="font-semibold text-sm">{{ __('Changes requested by Principal:') }}</div>
				<div class="text-sm mt-1">{{ rejectionReason.data[0].content }}</div>
			</div>
			<BatchOverview v-if="batch.data" :batch="batch" />
			<SkeletonLoader v-else variant="course-page" />
		</template>

		<template #tab-body-discussions>
			<div class="w-[90%] lg:w-[75%] mx-auto mt-5">
				<Discussions
					doctype="LMS Batch"
					:docname="batch.data.name"
					:title="__('Discussions')"
					:key="batch.data.name"
					:singleThread="true"
					:scrollToBottom="false"
				/>
			</div>
		</template>
	</TabbedDetailPage>

	<Dialog
		v-model="showBatchRejectModal"
		:options="{
			title: __('Reject Batch & Request Changes'),
			actions: [
				{
					label: __('Cancel'),
					onClick: () => {
						showBatchRejectModal = false
					},
				},
				{
					label: __('Confirm Rejection / Request Changes'),
					theme: 'red',
					variant: 'solid',
					onClick: confirmBatchReject,
				},
			],
		}"
	>
		<template #body-content>
			<div class="space-y-3 p-4">
				<p class="text-xs text-ink-gray-6">
					{{
						__(
							'Provide feedback or explain the required changes. The batch creator will be notified to revise the batch.'
						)
					}}
				</p>
				<FormControl
					v-model="batchRejectReason"
					type="textarea"
					:label="__('Rejection Reason / Required Changes')"
					:required="true"
					placeholder="Explain the changes required..."
				/>
			</div>
		</template>
	</Dialog>

	<router-view />
</template>
<script setup>
import { computed, inject, markRaw, provide, ref, useTemplateRef, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
	Badge,
	Button,
	createResource,
	Dialog,
	Dropdown,
	FormControl,
	Tooltip,
	toast,
	usePageMeta,
} from 'frappe-ui'
import { sessionStore } from '@/stores/session'
import { useScreenSize } from '@/utils/composables'
import AdminBatchDashboard from '@/pages/Batches/components/AdminBatchDashboard.vue'
import StudentBatchDashboard from '@/pages/Batches/components/BatchDashboard.vue'
import BatchOverview from '@/pages/Batches/BatchOverview.vue'
import LiveClass from '@/pages/Batches/components/LiveClass.vue'
import dayjs from 'dayjs'
import Announcements from '@/pages/Batches/components/Announcements.vue'
import BatchForm from '@/pages/Batches/BatchForm.vue'
import Discussions from '@/components/Discussions.vue'
import HeaderButton from '@/components/HeaderButton.vue'
import ShortcutTooltip from '@/components/ShortcutTooltip.vue'
import SkeletonLoader from '@/components/SkeletonLoader.vue'
import TabbedDetailPage from '@/components/Layouts/TabbedDetailPage.vue'
import { openBatchForm } from '@/composables/useBatchForms'
import { isAuthorizedApprover } from '@/utils/contentRelease'

const router = useRouter()
// Read by every form opener below. TabbedDetailPage still keeps the active tab
// in route.hash (:143, :158), so a form route opened without it re-renders the
// page on its first tab.
const route = useRoute()
const { brand } = sessionStore()
const { isMobile } = useScreenSize()
const user = inject('$user')
const page = useTemplateRef('page')
const readOnlyMode = window.read_only_mode

const props = defineProps({
	batchName: {
		type: String,
		required: true,
	},
})

const batch = createResource({
	url: 'lms.lms.utils.get_batch_details',
	makeParams: () => ({
		batch: props.batchName,
	}),
	auto: true,
	onSuccess: (data) => {
		if (!data) {
			router.push({ name: 'Batches' })
		}
	},
})

// The router reuses this component when you go straight from one batch to
// another (the command palette does exactly that), so setup does not run a
// second time. Without this the page would keep showing the batch you
// arrived on. The `cache` key is gone for the same reason: it was read once at
// setup, so a reload would have written the new batch into the old one's
// entry.
watch(
	() => props.batchName,
	() => batch.reload()
)

// The forms in the <router-view> below change what this endpoint reports —
// enrolling a student moves Seats Left on the overlay. Having no cache key is
// what makes them unable to reach it themselves, so it is handed down.
provide('reloadBatchDetails', () => batch.reload())

const isAdmin = computed(() => {
	return Boolean(user.data?.is_moderator || user.data?.is_evaluator)
})

const isStudent = computed(() => {
	return Boolean(batch.data?.students?.includes(user.data?.name))
})

const tabs = computed(() => {
	const enrolled = isAdmin.value || isStudent.value
	return [
		{
			key: 'overview',
			label: __('Overview'),
			component: markRaw(BatchOverview),
			icon: 'lucide-list',
			when: enrolled,
			flow: true,
		},
		{
			key: 'dashboard',
			label: __('Dashboard'),
			component: markRaw(AdminBatchDashboard),
			icon: 'lucide-trending-up',
			when: isAdmin.value,
		},
		{
			key: 'dashboard',
			label: __('Dashboard'),
			component: markRaw(StudentBatchDashboard),
			icon: 'lucide-clipboard-pen',
			when: !isAdmin.value && isStudent.value,
		},
		{
			key: 'classes',
			label: __('Classes'),
			component: markRaw(LiveClass),
			icon: 'lucide-laptop',
			when: enrolled,
		},
		{
			key: 'announcements',
			label: __('Announcements'),
			component: markRaw(Announcements),
			icon: 'lucide-mail',
			when: enrolled,
		},
		{
			key: 'discussions',
			label: __('Discussions'),
			component: markRaw(Discussions),
			icon: 'lucide-message-circle',
			when: enrolled,
		},
		{
			key: 'settings',
			label: __('Settings'),
			component: markRaw(BatchForm),
			icon: 'lucide-settings-2',
			when: isAdmin.value,
			flow: true,
		},
	]
})

const openAnnouncementModal = () => {
	openBatchForm(router, 'NewAnnouncement', props.batchName, route.hash)
}

const openStudentForm = () => {
	openBatchForm(router, 'NewBatchStudent', props.batchName, route.hash)
}

const publishToggle = createResource({
	url: 'lms.lms.api.process_approval',
	makeParams() {
		const hasPublish = batch.data?.transitions?.includes('Publish')
		const hasUnpublish = batch.data?.transitions?.includes('Unpublish')
		let action = ''
		if (hasPublish) action = 'Publish'
		else if (hasUnpublish) action = 'Unpublish'

		return {
			doctype: 'LMS Batch',
			docname: batch.data?.name,
			action: action,
		}
	},
	onSuccess() {
		toast.success(__('Batch publish status updated'))
		batch.reload()
	},
	onError(err) {
		toast.error(err.messages?.[0] || __('Could not update publish status'))
	},
})

const togglePublishBatch = () => {
	publishToggle.submit()
}

const getWorkflowBadgeTheme = (state) => {
	switch (state) {
		case 'Draft':
			return 'orange'
		case 'Pending Principal Approval':
			return 'blue'
		case 'Approved':
			return 'green'
		case 'Published':
			return 'green'
		case 'Rejected':
			return 'red'
		default:
			return 'gray'
	}
}

const isPrincipalUser = computed(() => isAuthorizedApprover(user))

const canManageBatch = computed(() => {
	if (!batch.data) return false
	if (isPrincipalUser.value) return true
	const roles = user.data?.roles || []
	if (
		roles.includes('Moderator') ||
		roles.includes('Course Creator') ||
		roles.includes('System Manager') ||
		roles.includes('Administrator') ||
		Boolean(user.data?.is_system_manager)
	) return true
	if (batch.data.owner === user.data?.name) return true
	return isAdmin.value
})

const canSubmitForApproval = computed(() => {
	if (!batch.data) return false
	const state = batch.data.workflow_state
	if (state !== 'Draft' && state !== 'Rejected') return false
	return (
		canManageBatch.value ||
		batch.data.transitions?.includes('Submit for Approval') ||
		batch.data.transitions?.includes('Edit and Resubmit')
	)
})

const canPrincipalReviewBatch = computed(() => {
	if (!batch.data) return false
	return isPrincipalUser.value && batch.data.workflow_state === 'Pending Principal Approval'
})

const workflowActionToggle = createResource({
	url: 'lms.lms.api.process_approval',
	makeParams() {
		return {
			doctype: 'LMS Batch',
			docname: batch.data?.name,
			action: batch.data?.workflow_state === 'Rejected' ? 'Edit and Resubmit' : 'Submit for Approval',
		}
	},
	onSuccess() {
		toast.success(__('Submitted for approval'))
		batch.reload()
	},
	onError(err) {
		toast.error(err.messages?.[0] ?? __('Failed to submit'))
	},
})

const submitForApproval = () => {
	workflowActionToggle.submit()
}

const approveActionToggle = createResource({
	url: 'lms.lms.api.process_approval',
	makeParams() {
		return {
			doctype: 'LMS Batch',
			docname: batch.data?.name,
			action: 'Approve',
		}
	},
	onSuccess() {
		toast.success(__('Batch approved and published'))
		batch.reload()
	},
	onError(err) {
		toast.error(err.messages?.[0] ?? __('Failed to approve batch'))
	},
})

const approveBatch = () => {
	approveActionToggle.submit()
}

const showBatchRejectModal = ref(false)
const batchRejectReason = ref('')

const rejectActionToggle = createResource({
	url: 'lms.lms.api.process_approval',
	makeParams() {
		return {
			doctype: 'LMS Batch',
			docname: batch.data?.name,
			action: 'Reject',
			comments: batchRejectReason.value,
		}
	},
	onSuccess() {
		toast.success(__('Batch rejected and returned for revisions'))
		showBatchRejectModal.value = false
		batch.reload()
	},
	onError(err) {
		toast.error(err.messages?.[0] ?? __('Failed to reject batch'))
	},
})

const openBatchRejectModal = () => {
	batchRejectReason.value = ''
	showBatchRejectModal.value = true
}

const confirmBatchReject = () => {
	if (!batchRejectReason.value.trim()) {
		toast.error(__('Please provide a reason or required changes.'))
		return
	}
	rejectActionToggle.submit()
}

const rejectionReason = createResource({
	url: 'frappe.client.get_list',
	auto: true,
	makeParams() {
		return {
			doctype: 'Comment',
			filters: {
				reference_doctype: 'LMS Batch',
				reference_name: props.name,
				comment_type: 'Workflow'
			},
			fields: ['content', 'creation'],
			order_by: 'creation desc',
			limit_page_length: 1
		}
	}
})

const isExpired = computed(() => {
	if (!batch.data?.expiry_date) return false
	return dayjs().isAfter(dayjs(batch.data.expiry_date))
})

const batchMenu = (tab) => {
	const options = []
	if (batch.data?.transitions?.includes('Unpublish')) {
		options.push({
			label: __('Unpublish batch'),
			icon: 'lucide-globe-lock',
			onClick: () => togglePublishBatch(),
		})
	} else if (batch.data?.transitions?.includes('Publish')) {
		options.push({
			label: __('Publish batch'),
			icon: 'lucide-globe',
			onClick: () => togglePublishBatch(),
		})
	}
	if (batch.data?.certification) {
		options.push({
			label: __('Generate Certificates'),
			icon: 'lucide-award',
			onClick: () => {
				openBatchForm(router, 'BulkCertificates', props.batchName, route.hash)
			},
		})
	}
	if (isAdmin.value) {
		options.push({
			label: __('Generate Model Question Paper'),
			icon: 'lucide-file-text',
			onClick: () => {
				router.push({
					name: 'AIQuestionPaperGenerator',
					query: { batch: props.batchName },
				})
			},
		})
	}
	if (tab?.key !== 'settings') return options
	if (isMobile.value) {
		options.push({
			label: batch.data?.published
				? __('Unpublish batch')
				: __('Publish batch'),
			icon: batch.data?.published ? 'lucide-globe-lock' : 'lucide-globe',
			onClick: togglePublishBatch,
		})
	}
	options.push({
		label: __('Delete batch'),
		icon: 'lucide-trash-2',
		theme: 'red',
		onClick: () => page.value?.instanceFor('settings')?.deleteBatch(),
	})
	return options
}

const breadcrumbs = computed(() => {
	const crumbs = [{ label: __('Batches'), route: { name: 'Batches' } }]
	if (batch.data) {
		crumbs.push({
			label: batch.data.title,
			route: { name: 'BatchDetail', params: { batchName: batch.data.name } },
		})
	}
	return crumbs
})

usePageMeta(() => {
	return {
		title: batch?.data?.title,
		icon: brand.favicon,
	}
})
</script>
<style>
.batch-description p {
	margin-bottom: 1rem;
	line-height: 1.7;
}

.batch-description li {
	line-height: 1.7;
}

.batch-description ol {
	list-style: auto;
	margin: revert;
	padding: revert;
}

.batch-description strong {
	font-weight: 600;
	color: theme('colors.gray.900') !important;
}
</style>
