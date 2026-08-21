<template>
	<DesktopLayout>
		<template #header>
			<PageHeader :title="__('Principal Dashboard')" />
		</template>

		<div class="px-5 pb-5">
			<Tabs v-model="activeTab" :tabs="tabs" class="mb-5">
				<template #tab="{ tab }">
					<div class="flex items-center gap-2">
						<span>{{ __(tab.label) }}</span>
						<Badge v-if="tab.count" theme="gray" size="sm">
							{{ tab.count }}
						</Badge>
					</div>
				</template>
			</Tabs>

			<div v-if="activeTab === 0" class="space-y-4">
				<div v-if="pendingCourses.loading" class="text-ink-gray-5">{{ __('Loading...') }}</div>
				<div v-else-if="!pendingCourses.data?.length" class="text-ink-gray-5">{{ __('No courses pending approval.') }}</div>
				<div v-else class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
					<div v-for="course in pendingCourses.data" :key="course.name" class="p-5 border border-gray-200 rounded-xl bg-white shadow-sm hover:shadow-md transition-shadow">
						<h3 class="text-lg font-medium">{{ course.title }}</h3>
						<p class="text-sm text-ink-gray-5 mt-1">{{ __('Instructor') }}: {{ course.owner }}</p>
						<div class="flex gap-2 mt-4">
							<Button variant="solid" theme="amber" @click="handleAction('LMS Course', course.name, 'Approve')">
								{{ __('Approve & Publish') }}
							</Button>
							<Button variant="outline" theme="red" @click="openRejectModal('LMS Course', course.name)">
								{{ __('Reject') }}
							</Button>
						</div>
					</div>
				</div>
			</div>

			<div v-if="activeTab === 1" class="space-y-4">
				<div v-if="pendingBatches.loading" class="text-ink-gray-5">{{ __('Loading...') }}</div>
				<div v-else-if="!pendingBatches.data?.length" class="text-ink-gray-5">{{ __('No batches pending approval.') }}</div>
				<div v-else class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
					<div v-for="batch in pendingBatches.data" :key="batch.name" class="p-5 border border-gray-200 rounded-xl bg-white shadow-sm hover:shadow-md transition-shadow">
						<h3 class="text-lg font-medium">{{ batch.title }}</h3>
						<p class="text-sm text-ink-gray-5 mt-1">{{ __('Start Date') }}: {{ batch.start_date }}</p>
						<div class="flex gap-2 mt-4">
							<Button variant="solid" theme="amber" @click="handleAction('LMS Batch', batch.name, 'Approve')">
								{{ __('Approve & Publish') }}
							</Button>
							<Button variant="outline" theme="red" @click="openRejectModal('LMS Batch', batch.name)">
								{{ __('Reject') }}
							</Button>
						</div>
					</div>
				</div>
			</div>
		</div>

		<Dialog v-model="showRejectModal" :title="__('Reject Submission')">
			<template #body-content>
				<div class="p-4 space-y-4">
					<p class="text-sm text-ink-gray-7">{{ __('Please provide a reason for rejecting this submission.') }}</p>
					<Textarea v-model="rejectReason" :placeholder="__('Rejection reason')" rows="4" class="w-full" />
				</div>
			</template>
			<template #actions>
				<div class="flex justify-end gap-2 p-4 border-t">
					<Button variant="ghost" @click="showRejectModal = false">{{ __('Cancel') }}</Button>
					<Button variant="solid" theme="red" @click="confirmReject" :loading="isSubmitting">{{ __('Confirm Reject') }}</Button>
				</div>
			</template>
		</Dialog>
	</DesktopLayout>
</template>

<script setup>
import { ref, computed } from 'vue'
import { createResource, Button, Tabs, Badge, Dialog, Textarea, toast, call } from 'frappe-ui'
import DesktopLayout from '@/components/Layouts/DesktopLayout.vue'
import PageHeader from '@/components/Layouts/PageHeader.vue'

const activeTab = ref(0)
const showRejectModal = ref(false)
const rejectReason = ref('')
const rejectTarget = ref(null)
const isSubmitting = ref(false)

const tabs = computed(() => [
	{ label: 'Pending Courses', count: pendingCourses.data?.length || 0 },
	{ label: 'Pending Batches', count: pendingBatches.data?.length || 0 },
])

const pendingCourses = createResource({
	url: 'frappe.client.get_list',
	params: {
		doctype: 'LMS Course',
		filters: { workflow_state: 'Pending Principal Approval' },
		fields: ['name', 'title', 'owner', 'workflow_state']
	},
	auto: true
})

const pendingBatches = createResource({
	url: 'frappe.client.get_list',
	params: {
		doctype: 'LMS Batch',
		filters: { workflow_state: 'Pending Principal Approval' },
		fields: ['name', 'title', 'start_date', 'workflow_state']
	},
	auto: true
})

const handleAction = async (doctype, name, action, comments = '') => {
	try {
		await call('lms.lms.api.process_approval', {
			doctype: doctype,
			docname: name,
			action: action,
			comments: comments
		})
		toast.success(__('Action completed successfully'))
		pendingCourses.reload()
		pendingBatches.reload()
	} catch (error) {
		toast.error(error.message || __('Failed to process action'))
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
	await handleAction(rejectTarget.value.doctype, rejectTarget.value.name, 'Reject', rejectReason.value)
	isSubmitting.value = false
	showRejectModal.value = false
}
</script>
