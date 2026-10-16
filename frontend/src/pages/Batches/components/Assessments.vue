<template>
	<div>
		<div class="flex items-center justify-between mb-4">
			<h2 class="text-ink-gray-9 font-semibold">
				{{ __('Assessments') }}
			</h2>
			<Button v-if="canAddAssessments()" @click="openAssessmentForm()">
				<template #prefix>
					<span class="lucide-plus h-4 w-4" />
				</template>
				{{ __('Add') }}
			</Button>
		</div>

		<!-- Release Action Banner -->
		<div
			v-if="canAddAssessments() && unreleasedSummary.data && unreleasedSummary.data.total_unreleased > 0"
			class="mb-4 rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-950 shadow-sm"
		>
			<div class="flex flex-col gap-2.5">
				<div class="flex items-start justify-between gap-2">
					<div>
						<div class="font-semibold text-p-sm flex items-center gap-1.5 text-amber-900">
							<span class="lucide-sparkles size-4 text-amber-600 shrink-0" />
							{{ __('New Assessments Pending Release') }}
						</div>
						<div class="text-xs text-amber-800 mt-1 flex flex-wrap gap-x-2">
							<span v-if="unreleasedSummary.data.draft_count">
								<strong>{{ unreleasedSummary.data.draft_count }}</strong> {{ __('in draft') }}
							</span>
							<span v-if="unreleasedSummary.data.pending_count" class="text-blue-800 font-medium">
								&bull; <strong>{{ unreleasedSummary.data.pending_count }}</strong> {{ __('pending approval') }}
							</span>
							<span v-if="unreleasedSummary.data.rejected_count" class="text-red-700 font-medium">
								&bull; <strong>{{ unreleasedSummary.data.rejected_count }}</strong> {{ __('rejected') }}
							</span>
						</div>
					</div>
					<Badge
						variant="subtle"
						theme="gray"
						size="sm"
						:label="releaseModeLabel"
						class="shrink-0"
					/>
				</div>

				<div class="flex items-center gap-2 pt-1 border-t border-amber-200/60 flex-wrap">
					<!-- Option A: Teacher Can Publish -->
					<Button
						v-if="canTeacherPublish"
						variant="solid"
						theme="green"
						size="sm"
						:loading="batchRelease.loading"
						@click="confirmPublishAll"
					>
						<template #prefix>
							<span class="lucide-send size-3.5" />
						</template>
						{{ __('Publish New Content to Students') }}
					</Button>

					<!-- Option B: Submit for Principal Approval -->
					<Button
						v-if="canTeacherSubmit"
						variant="solid"
						theme="blue"
						size="sm"
						:loading="batchRelease.loading"
						@click="confirmSubmitAll"
					>
						<template #prefix>
							<span class="lucide-file-check size-3.5" />
						</template>
						{{
							unreleasedSummary.data.rejected_count > 0 && !unreleasedSummary.data.draft_count
								? __('Resubmit for Approval')
								: __('Submit for Principal Approval')
						}}
					</Button>

					<!-- Principal Action: Approve and Publish -->
					<Button
						v-if="isPrincipal && unreleasedSummary.data.pending_count > 0"
						variant="solid"
						theme="green"
						size="sm"
						:loading="batchRelease.loading"
						@click="confirmApproveAll"
					>
						<template #prefix>
							<span class="lucide-check-check size-3.5" />
						</template>
						{{ __('Approve and Publish') }}
					</Button>

					<!-- Principal Action: Reject / Request Changes -->
					<Button
						v-if="isPrincipal && unreleasedSummary.data.pending_count > 0"
						variant="outline"
						theme="red"
						size="sm"
						:loading="batchRelease.loading"
						@click="openRejectDialog"
					>
						<template #prefix>
							<span class="lucide-x size-3.5" />
						</template>
						{{ __('Reject / Request Changes') }}
					</Button>
				</div>
			</div>
		</div>

		<div v-if="assessments.data?.length" class="text-sm">
			<ResponsiveListView
				:columns="assessmentColumns"
				:rows="assessments.data"
				row-key="name"
				class="sm:border sm:rounded-lg"
				:options="listOptions"
			>
				<template #cell="{ column, value }">
					<span v-if="column.key == 'assessment_type'">
						{{ getAssessmentTypeLabel(value) }}
					</span>
					<Badge
						v-else-if="column.key == 'release_status'"
						variant="subtle"
						:theme="value === 'Released' ? 'green' : value === 'Pending Principal Approval' ? 'blue' : value === 'Rejected' ? 'red' : 'orange'"
					>
						{{ __(value || 'Released') }}
					</Badge>
					<Badge
						v-else-if="column.key == 'status' && isNaN(value)"
						:theme="getStatusTheme(value)"
					>
						{{ value }}
					</Badge>
					<span v-else>{{ value }}</span>
				</template>
				<template #selection-actions="{ unselectAll, selections }">
					<Button
						variant="ghost"
						:label="__('Delete')"
						@click="removeAssessments(selections, unselectAll)"
					>
						<template #icon>
							<span class="lucide-trash-2 size-4" />
						</template>
					</Button>
				</template>
			</ResponsiveListView>
		</div>
		<div v-else class="text-ink-gray-7">
			{{ __('No assessments added to this batch') }}
		</div>

		<!-- Rejection Reason Dialog -->
		<Dialog
			v-model="showRejectModal"
			:options="{
				title: __('Reject / Request Changes'),
				actions: [
					{
						label: __('Cancel'),
						onClick: () => {
							showRejectModal = false
						},
					},
					{
						label: __('Confirm Rejection / Request Changes'),
						theme: 'red',
						variant: 'solid',
						onClick: submitRejection,
					},
				],
			}"
		>
			<template #body-content>
				<p class="text-sm text-ink-gray-7 mb-3">
					{{
						__(
							'Specify the feedback or changes needed. Content will remain hidden until updated and resubmitted:'
						)
					}}
				</p>
				<FormControl
					v-model="rejectionReasonInput"
					type="textarea"
					:label="__('Rejection Reason / Feedback')"
					:placeholder="__('Explain the requested changes...')"
				/>
			</template>
		</Dialog>
	</div>
</template>
<script setup>
import { createResource, Button, Badge, Dialog, FormControl, toast } from 'frappe-ui'
import { computed, inject, ref, getCurrentInstance } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { openBatchForm } from '@/composables/useBatchForms'
import ResponsiveListView from '@/components/ResponsiveListView.vue'

const user = inject('$user')
const readOnlyMode = window.read_only_mode

const { $dialog } = getCurrentInstance()?.appContext.config.globalProperties || {}

const showRejectModal = ref(false)
const rejectionReasonInput = ref('')

const props = defineProps({
	batch: {
		type: String,
		required: true,
	},
	rows: {
		type: Array,
	},
	columns: {
		type: Array,
	},
	options: {
		type: Object,
		default: () => ({
			selectable: true,
			totalCount: 0,
			rowCount: 0,
		}),
	},
})

const canAddAssessments = () => {
	if (readOnlyMode) return false
	return Boolean(
		user.data?.is_moderator ||
			user.data?.is_evaluator ||
			user.data?.is_instructor ||
			user.data?.is_principal ||
			user.data?.is_system_manager ||
			user.data?.roles?.includes('Principal')
	)
}

const assessments = createResource({
	url: 'lms.lms.utils.get_assessments',
	params: {
		batch: props.batch,
	},
	auto: true,
	cache: ['batchAssessments', props.batch],
})

const unreleasedSummary = createResource({
	url: 'lms.lms.api.get_unreleased_content_summary',
	params: { batch: props.batch },
	auto: canAddAssessments(),
})

const batchRelease = createResource({
	url: 'lms.lms.api.batch_release_content',
	makeParams(values) {
		return {
			batch: props.batch,
			action: values.action,
			reason: values.reason || '',
		}
	},
	onSuccess(data, values) {
		const action = values?.action
		toast.success(
			action === 'publish'
				? __('New content published to students successfully')
				: action === 'submit'
				? __('Content submitted for Principal approval')
				: action === 'approve'
				? __('Content approved and published successfully')
				: __('Content rejected')
		)
		assessments.reload()
		unreleasedSummary.reload()
	},
	onError(err) {
		toast.error(err?.messages?.[0] || err?.message || __('Action failed'))
	},
})

const releaseMode = computed(
	() => unreleasedSummary.data?.content_release_mode || 'None'
)
const isPrincipal = computed(
	() =>
		Boolean(
			user?.data?.is_principal ||
				user?.data?.is_system_manager ||
				user?.data?.roles?.includes('Principal')
		)
)

const releaseModeLabel = computed(() => {
	const mode = releaseMode.value
	if (mode === 'Principal Approval Required')
		return __('Mode: Principal Approval')
	if (mode === 'Teacher Can Publish') return __('Mode: Teacher Publish')
	if (mode === 'Teacher Choice') return __('Mode: Teacher Choice')
	return __('Mode: Standard')
})

const canTeacherPublish = computed(() => {
	if (!canAddAssessments()) return false
	if (isPrincipal.value) return true
	return (
		(releaseMode.value === 'Teacher Can Publish' ||
			releaseMode.value === 'Teacher Choice') &&
		((unreleasedSummary.data?.draft_count ?? 0) > 0 ||
			(unreleasedSummary.data?.rejected_count ?? 0) > 0)
	)
})

const canTeacherSubmit = computed(() => {
	if (!canAddAssessments()) return false
	return (
		(releaseMode.value === 'Principal Approval Required' ||
			releaseMode.value === 'Teacher Choice') &&
		((unreleasedSummary.data?.draft_count ?? 0) > 0 ||
			(unreleasedSummary.data?.rejected_count ?? 0) > 0)
	)
})

function confirmPublishAll() {
	if ($dialog) {
		$dialog({
			title: __('Publish New Content to Students'),
			message: __(
				'Are you sure you want to release all newly added batch assessments? This will make them immediately visible to eligible enrolled students.'
			),
			actions: [
				{
					label: __('Cancel'),
					variant: 'outline',
					onClick: (close) => close(),
				},
				{
					label: __('Publish Now'),
					variant: 'solid',
					theme: 'green',
					onClick: (close) => {
						batchRelease.submit({ action: 'publish' })
						close()
					},
				},
			],
		})
	} else {
		batchRelease.submit({ action: 'publish' })
	}
}

function confirmSubmitAll() {
	if ($dialog) {
		$dialog({
			title: __('Submit for Principal Approval'),
			message: __(
				'Submit newly added assessments to the Principal for review and publication? Content will remain hidden from students until approved.'
			),
			actions: [
				{
					label: __('Cancel'),
					variant: 'outline',
					onClick: (close) => close(),
				},
				{
					label: __('Submit for Approval'),
					variant: 'solid',
					theme: 'blue',
					onClick: (close) => {
						batchRelease.submit({ action: 'submit' })
						close()
					},
				},
			],
		})
	} else {
		batchRelease.submit({ action: 'submit' })
	}
}

function confirmApproveAll() {
	if ($dialog) {
		$dialog({
			title: __('Approve and Publish'),
			message: __(
				'Approve and publish all pending batch assessments? They will become visible to students immediately.'
			),
			actions: [
				{
					label: __('Cancel'),
					variant: 'outline',
					onClick: (close) => close(),
				},
				{
					label: __('Approve & Publish'),
					variant: 'solid',
					theme: 'green',
					onClick: (close) => {
						batchRelease.submit({ action: 'approve' })
						close()
					},
				},
			],
		})
	} else {
		batchRelease.submit({ action: 'approve' })
	}
}

function openRejectDialog() {
	rejectionReasonInput.value = ''
	showRejectModal.value = true
}

function submitRejection() {
	showRejectModal.value = false
	batchRelease.submit({ action: 'reject', reason: rejectionReasonInput.value })
}

const route = useRoute()
const router = useRouter()

const openAssessmentForm = () => {
	openBatchForm(router, 'NewAssessment', props.batch, route.hash)
}

const deleteAssessments = createResource({
	url: 'lms.lms.api.delete_documents',
	makeParams(values) {
		return {
			doctype: 'LMS Assessment',
			documents: values.assessments,
		}
	},
})

const removeAssessments = (selections, unselectAll) => {
	deleteAssessments.submit(
		{ assessments: Array.from(selections) },
		{
			onSuccess(data) {
				assessments.reload()
				unselectAll()
			},
		}
	)
}

const getRowRoute = (row) => {
	if (row.assessment_type == 'LMS Assignment') {
		if (row.submission) {
			return {
				name: 'AssignmentSubmission',
				params: {
					assignmentID: row.assessment_name,
					submissionName: row.submission.name,
				},
			}
		} else {
			return {
				name: 'AssignmentSubmission',
				params: {
					assignmentID: row.assessment_name,
					submissionName: 'new',
				},
			}
		}
	} else if (row.assessment_type == 'LMS Programming Exercise') {
		if (row.submission) {
			return {
				name: 'ProgrammingExerciseSubmission',
				params: {
					exerciseID: row.assessment_name,
					submissionID: row.submission.name,
				},
			}
		} else {
			return {
				name: 'ProgrammingExerciseSubmission',
				params: {
					exerciseID: row.assessment_name,
					submissionID: 'new',
				},
			}
		}
	} else {
		return {
			name: 'QuizPage',
			params: {
				quizID: row.assessment_name,
			},
		}
	}
}

const assessmentColumns = computed(() => {
	let columns = [
		{
			label: __('Assessment'),
			key: 'title',
		},
		{
			label: __('Type'),
			key: 'assessment_type',
			width: '10rem',
		},
	]

	if (canAddAssessments()) {
		columns.push({
			label: __('Release Status'),
			key: 'release_status',
			width: '12rem',
		})
	}

	if (!user.data?.is_moderator) {
		columns.push({
			label: __('Status/Percentage'),
			key: 'status',
			align: 'left',
			width: '10rem',
		})
	}
	return columns
})

const listOptions = computed(() => ({
	showTooltip: false,
	getRowRoute: (row) => getRowRoute(row),
	selectable: user.data?.is_student ? false : true,
}))

const getStatusTheme = (status) => {
	if (status === 'Pass' || status === 'Passed') {
		return 'green'
	} else if (status === 'Not Graded') {
		return 'orange'
	} else {
		return 'red'
	}
}

const getAssessmentTypeLabel = (type) => {
	if (type == 'LMS Assignment') {
		return __('Assignment')
	} else if (type == 'LMS Quiz') {
		return __('Quiz')
	} else if (type == 'LMS Programming Exercise') {
		return __('Programming Exercise')
	}
}
</script>
