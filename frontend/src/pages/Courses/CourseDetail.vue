<template>
	<TabbedDetailPage
		ref="page"
		:tabs="tabs"
		:breadcrumbs="breadcrumbs"
		:published="Boolean(course.data?.published)"
		:loading="!course.data"
		:doc="course"
		doc-prop="course"
	>
		<template #actions="{ tab }">
			<template v-if="tab?.key === 'settings' && courseFormRef">
				<Badge v-if="courseFormRef.isDirty" theme="orange">
					{{ __('Not Saved') }}
				</Badge>
				<Dropdown
					:options="courseOptions"
					:button="{
						icon: 'lucide-ellipsis',
						variant: 'ghost',
						label: __('Course options'),
					}"
					side="bottom"
					align="end"
				/>
				<Tooltip
					v-if="!courseFormRef.isDirty"
					:text="__('No changes to save')"
					:hoverDelay="0.1"
				>
					<HeaderButton :label="__('Save')" variant="solid" disabled />
				</Tooltip>
				<ShortcutTooltip v-else :label="__('Save')" combo="Mod+S">
					<HeaderButton
						:label="__('Save')"
						variant="solid"
						@click="courseFormRef.submitCourse()"
					/>
				</ShortcutTooltip>
			</template>
			<template v-if="tab?.key === 'editor' && editorSelected">
				<Tooltip
					v-if="courseEditorRef?.lessonHasVideo"
					:text="__('Video Statistics')"
				>
					<Button
						variant="ghost"
						:label="__('Video Statistics')"
						:class="isMobile ? '!size-9' : ''"
						@click="courseEditorRef?.openVideoStats()"
					>
						<template #icon>
							<span class="lucide-trending-up size-4" />
						</template>
					</Button>
				</Tooltip>
				<Tooltip v-if="!isMobile" :text="__('How to edit a lesson')">
					<Button
						variant="ghost"
						class="text-p-base-medium"
						:label="__('How to edit a lesson')"
						@click="showLessonHelp = true"
					>
						<template #icon>
							<span class="lucide-info size-4" />
						</template>
					</Button>
				</Tooltip>
				<router-link
					:to="{
						name: 'Lesson',
						params: {
							courseName: props.courseName,
							chapterNumber: editorSelected.chapterNumber,
							lessonNumber: editorSelected.lessonNumber,
						},
						query: { studentView: 1 },
					}"
				>
					<Tooltip v-if="isMobile" :text="__('Student View')">
						<Button variant="outline" class="!size-9">
							<template #icon>
								<span class="lucide-eye size-4" />
							</template>
						</Button>
					</Tooltip>
					<Button v-else variant="outline">
						<template #prefix>
							<span class="lucide-eye size-4" />
						</template>
						{{ __('Student View') }}
					</Button>
				</router-link>
			</template>
			<Button
				v-if="tab?.key === 'dashboard' && course.data && isMobile && !isExpired"
				variant="outline"
				class="!size-9"
				:tooltip="__('Enroll')"
				@click="openEnrollForm()"
			>
				<template #icon>
					<span class="lucide-plus size-4" />
				</template>
			</Button>
			<Button
				v-else-if="tab?.key === 'dashboard' && course.data && !isExpired"
				variant="outline"
				@click="openEnrollForm()"
			>
				<template #prefix>
					<span class="lucide-plus size-4" />
				</template>
				{{ __('Enroll') }}
			</Button>
			<!-- Course Workflow Actions & Status (always visible when course is loaded) -->
			<template v-if="course.data">
				<Badge
					v-if="course.data.workflow_state"
					:theme="getWorkflowBadgeTheme(course.data.workflow_state)"
					size="sm"
				>
					{{ __(course.data.workflow_state) }}
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
					{{ course.data.workflow_state === 'Rejected' ? __('Resubmit for Approval') : __('Submit for Principal Approval') }}
				</Button>

				<!-- Principal Approve & Publish -->
				<Button
					v-if="canPrincipalReviewCourse"
					variant="solid"
					theme="green"
					size="sm"
					:loading="approveActionToggle.loading"
					@click="approveCourse"
				>
					<template #prefix>
						<span class="lucide-check-check size-3.5" />
					</template>
					{{ __('Approve and Publish') }}
				</Button>

				<!-- Principal Reject / Request Changes -->
				<Button
					v-if="canPrincipalReviewCourse"
					variant="outline"
					theme="red"
					size="sm"
					:loading="rejectActionToggle.loading"
					@click="openCourseRejectModal"
				>
					<template #prefix>
						<span class="lucide-x size-3.5" />
					</template>
					{{ __('Reject / Request Changes') }}
				</Button>

				<!-- Principal / Admin Direct Publish -->
				<Button
					v-if="course.data?.transitions?.includes('Publish')"
					variant="solid"
					theme="green"
					size="sm"
					:loading="publishToggle.loading"
					@click="togglePublishCourse"
				>
					<template #prefix>
						<span class="lucide-send size-3.5" />
					</template>
					{{ __('Publish') }}
				</Button>

				<!-- Principal / Admin Unpublish -->
				<Button
					v-if="course.data?.transitions?.includes('Unpublish')"
					variant="outline"
					theme="gray"
					size="sm"
					:loading="publishToggle.loading"
					@click="togglePublishCourse"
				>
					{{ __('Unpublish') }}
				</Button>
			</template>
		</template>

		<template #solo>
			<div
				v-if="course.data?.workflow_state === 'Rejected' && rejectionReason.data && rejectionReason.data.length > 0"
				class="mx-4 sm:mx-10 mt-4 p-4 bg-red-50 text-red-700 rounded-lg border border-red-200"
			>
				<div class="font-semibold text-sm">{{ __('Changes requested by Principal:') }}</div>
				<div class="text-sm mt-1">{{ rejectionReason.data[0].content }}</div>
			</div>
			<CourseOverview v-if="course.data" :course="course" />
			<SkeletonLoader v-else variant="course-page" />
		</template>

		<template #tab-body-editor>
			<div
				v-if="isMobile && editorSelected"
				class="flex items-center gap-2 border-b bg-surface-base px-5 py-2.5"
			>
				<Button
					variant="subtle"
					class="!size-9"
					:label="__('Previous lesson')"
					:disabled="!courseEditorRef?.hasPrev"
					@click="courseEditorRef?.goPrev()"
				>
					<template #icon>
						<span class="lucide-chevron-left size-4" />
					</template>
				</Button>
				<div
					class="min-w-0 flex-1 text-center text-p-xs font-medium tabular-nums text-ink-gray-5"
				>
					<span v-if="courseEditorRef?.lessonTotal">
						{{ courseEditorRef?.lessonIndex }} /
						{{ courseEditorRef?.lessonTotal }}
					</span>
				</div>
				<Button
					variant="subtle"
					class="!size-9"
					:label="__('Next lesson')"
					:disabled="!courseEditorRef?.hasNext"
					@click="courseEditorRef?.goNext()"
				>
					<template #icon>
						<span class="lucide-chevron-right size-4" />
					</template>
				</Button>
			</div>
			<CourseEditor
				ref="courseEditorRef"
				:course="course"
				v-model:selected="editorSelected"
			/>
		</template>

		<template #overlay="{ tab }">
			<Button
				v-if="isMobile && tab?.key === 'editor'"
				variant="outline"
				size="md"
				class="absolute bottom-4 end-4 z-10 !h-11 !rounded-full !px-4 !shadow-lg"
				@click="courseEditorRef?.openChapters()"
			>
				<template #prefix>
					<span class="lucide-layers size-4" />
				</template>
				{{ __('Chapters') }}
			</Button>

			<div
				v-if="tab?.key === 'editor' && course.data"
				class="pointer-events-none absolute inset-x-0 top-0 z-10 hidden md:flex"
			>
				<div class="w-[70%]" />
				<div
					class="pointer-events-auto flex w-[30%] items-center justify-between gap-x-2 border-s border-b bg-surface-base p-1 px-5"
				>
					<div class="py-2.5 text-base-medium text-ink-gray-9">
						{{ __('Chapters') }}
					</div>
					<Button size="sm" @click="courseEditorRef?.openAddChapter()">
						<template #prefix>
							<span class="lucide-plus size-4" />
						</template>
						{{ __('Add') }}
					</Button>
				</div>
			</div>
		</template>
	</TabbedDetailPage>
	<LessonHelp v-model="showLessonHelp" />

	<Dialog
		v-model="showCourseRejectModal"
		:options="{
			title: __('Reject Course & Request Changes'),
			actions: [
				{
					label: __('Cancel'),
					onClick: () => {
						showCourseRejectModal = false
					},
				},
				{
					label: __('Confirm Rejection / Request Changes'),
					theme: 'red',
					variant: 'solid',
					onClick: confirmCourseReject,
				},
			],
		}"
	>
		<template #body-content>
			<div class="space-y-3 p-4">
				<p class="text-xs text-ink-gray-6">
					{{
						__(
							'Provide feedback or explain the required changes. The course creator will be notified to revise the course.'
						)
					}}
				</p>
				<FormControl
					v-model="courseRejectReason"
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
<script setup lang="ts">
import { computed, inject, markRaw, ref, useTemplateRef, watch } from 'vue'
import type { ComputedRef } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { Router } from 'vue-router'
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
import dayjs from 'dayjs'
import { sessionStore } from '@/stores/session'
import { useScreenSize } from '@/utils/composables'
import { isAuthorizedApprover } from '@/utils/contentRelease'
import TabbedDetailPage from '@/components/Layouts/TabbedDetailPage.vue'
import type { DetailTab } from '@/components/Layouts/TabbedDetailPage.vue'
import CourseOverview from '@/pages/Courses/CourseOverview.vue'
import SkeletonLoader from '@/components/SkeletonLoader.vue'
import CourseDashboard from '@/pages/Courses/CourseDashboard.vue'
import CourseEditor from '@/pages/Courses/CourseEditor.vue'
import CourseForm from '@/pages/Courses/CourseForm.vue'
import LessonHelp from '@/components/LessonHelp.vue'
import ShortcutTooltip from '@/components/ShortcutTooltip.vue'
import HeaderButton from '@/components/HeaderButton.vue'
import { openFormRoute } from '@/composables/useFormRoute'
import type {
	CourseDetails,
	CourseInstructorInfo,
	Resource,
	SessionUser,
} from '@/types'

type Brand = { name?: string; logo?: string; favicon?: string }

const { brand } = sessionStore() as { brand: Brand }
const router: Router = useRouter()
const route = useRoute()
const user = inject<SessionUser>('$user')!
const { isMobile } = useScreenSize()

interface EditorSelection {
	chapterNumber: string
	lessonNumber: string
	number: string
	title?: string
}

const editorSelected = ref<EditorSelection | null>(null)
const showLessonHelp = ref(false)

type CourseMenuItem = {
	label: string
	icon: string
	theme?: string
	onClick: () => void
}
type CourseFormApi = {
	isDirty: boolean
	submitCourse: () => void
	courseMenu: CourseMenuItem[]
}
const page = useTemplateRef('page')

const courseFormRef = computed<CourseFormApi | null>(
	() => (page.value?.instanceFor('settings') ?? null) as CourseFormApi | null
)

type CourseEditorApi = {
	saveSelectedLesson: () => void
	isDirty: ComputedRef<boolean>
	lessonHasVideo: ComputedRef<boolean>
	openVideoStats: () => void
	openAddChapter: () => void
	lessonIndex: ComputedRef<number>
	lessonTotal: ComputedRef<number>
	hasPrev: ComputedRef<boolean>
	hasNext: ComputedRef<boolean>
	goPrev: () => void
	goNext: () => void
	openChapters: () => void
}
const courseEditorRef = ref<CourseEditorApi | null>(null)

const publishToggle = createResource({
	url: 'lms.lms.api.process_approval',
	makeParams() {
		// Use the correct action depending on current state, which we know from transitions
		const hasPublish = course.data?.transitions?.includes('Publish')
		const hasUnpublish = course.data?.transitions?.includes('Unpublish')
		let action = ''
		if (hasPublish) action = 'Publish'
		else if (hasUnpublish) action = 'Unpublish'

		return {
			doctype: 'LMS Course',
			docname: course.data?.name,
			action: action,
		}
	},
	onSuccess() {
		toast.success(__('Course publish status updated'))
		course.reload()
	},
	onError(err: { messages?: string[] } | string) {
		const msg =
			typeof err === 'string'
				? err
				: err.messages?.[0] ?? __('Could not update publish status')
		toast.error(msg)
	},
}) as Resource<unknown>

// On a phone the publish toggle joins the ... menu, where it keeps a written
// label. An icon-only globe gave no hint that it publishes the course.
const courseOptions = computed<CourseMenuItem[]>(() => {
	const menu = courseFormRef.value?.courseMenu ?? []
	if (!isMobile.value || !user.data?.is_principal) return menu
	
	const options = []
	if (course.data?.transitions?.includes('Unpublish')) {
		options.push({
			label: __('Unpublish course'),
			icon: 'lucide-globe-lock',
			onClick: () => togglePublishCourse(),
		})
	} else if (course.data?.transitions?.includes('Publish')) {
		options.push({
			label: __('Publish course'),
			icon: 'lucide-globe',
			onClick: () => togglePublishCourse(),
		})
	}
	
	return [
		...options,
		...menu,
	]
})

function togglePublishCourse() {
	publishToggle.submit()
}

// The enrollment form is a child route now, not a modal the dashboard tab owned,
// so the button navigates instead of reaching into the tab instance. Hash and
// query both travel: the hash names the tab this page returns to, and the query
// holds CourseEditor's open lesson.
function openEnrollForm() {
	openFormRoute(router, {
		name: 'NewCourseEnrollment',
		params: { courseName: props.courseName },
		hash: route.hash,
		query: { ...route.query },
	})
}

const props = defineProps<{
	courseName: string
}>()

// No `cache` key: it would be read once at setup, so the reload below (this
// component is reused when you jump straight from one course to another) would
// file the new course's data under the course you arrived on.
const course = createResource({
	url: 'lms.lms.utils.get_course_details',
	makeParams() {
		return {
			course: props.courseName,
		}
	},
	auto: true,
}) as Resource<CourseDetails | null>

const isExpired = computed(() => {
	if (!course.data?.expiry_date) return false
	return dayjs().isAfter(dayjs(course.data.expiry_date))
})

const tabs = computed<DetailTab[]>(() => [
	{
		key: 'overview',
		label: __('Overview'),
		component: markRaw(CourseOverview),
		icon: 'lucide-list',
		when: isAdmin.value,
		flow: true,
	},
	{
		key: 'dashboard',
		label: __('Dashboard'),
		component: markRaw(CourseDashboard),
		icon: 'lucide-trending-up',
		when: isAdmin.value,
	},
	{
		key: 'editor',
		label: __('Course editor'),
		shortLabel: __('Editor'),
		component: markRaw(CourseEditor),
		icon: 'lucide-book-open',
		when: isAdmin.value,
	},
	{
		key: 'settings',
		label: __('Settings'),
		component: markRaw(CourseForm),
		icon: 'lucide-settings-2',
		when: isAdmin.value,
		flow: true,
	},
])

watch(
	() => props.courseName,
	() => {
		course.reload()
	}
)

watch(course, () => {
	if (!isAdmin.value && !course.data?.published && !course.data?.upcoming) {
		router.push({
			name: 'Courses',
		})
	}
})

const getWorkflowBadgeTheme = (state: string) => {
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

const isInstructor = (): boolean => {
	let user_is_instructor = false
	course.data?.instructors.forEach((instructor: CourseInstructorInfo) => {
		if (!user_is_instructor && instructor.name == user.data?.name) {
			user_is_instructor = true
		}
	})
	return user_is_instructor
}

const isPrincipalUser = computed(() => isAuthorizedApprover(user))

const canManageCourse = computed(() => {
	if (!course.data) return false
	if (isPrincipalUser.value) return true
	const roles = user.data?.roles || []
	if (
		roles.includes('Moderator') ||
		roles.includes('Course Creator') ||
		roles.includes('System Manager') ||
		roles.includes('Administrator') ||
		Boolean(user.data?.is_system_manager)
	) return true
	if (course.data.owner === user.data?.name) return true
	return isInstructor()
})

const canSubmitForApproval = computed(() => {
	if (!course.data) return false
	const state = course.data.workflow_state
	if (state !== 'Draft' && state !== 'Rejected') return false
	return (
		canManageCourse.value ||
		course.data.transitions?.includes('Submit for Approval') ||
		course.data.transitions?.includes('Edit and Resubmit')
	)
})

const canPrincipalReviewCourse = computed(() => {
	if (!course.data) return false
	return isPrincipalUser.value && course.data.workflow_state === 'Pending Principal Approval'
})

const workflowActionToggle = createResource({
	url: 'lms.lms.api.process_approval',
	makeParams() {
		return {
			doctype: 'LMS Course',
			docname: course.data?.name,
			action: course.data?.workflow_state === 'Rejected' ? 'Edit and Resubmit' : 'Submit for Approval',
		}
	},
	onSuccess() {
		toast.success(__('Submitted for approval'))
		course.reload()
	},
	onError(err: any) {
		toast.error(err.messages?.[0] ?? __('Failed to submit'))
	},
}) as Resource<unknown>

function submitForApproval() {
	workflowActionToggle.submit()
}

const approveActionToggle = createResource({
	url: 'lms.lms.api.process_approval',
	makeParams() {
		return {
			doctype: 'LMS Course',
			docname: course.data?.name,
			action: 'Approve',
		}
	},
	onSuccess() {
		toast.success(__('Course approved and published'))
		course.reload()
	},
	onError(err: any) {
		toast.error(err.messages?.[0] ?? __('Failed to approve course'))
	},
}) as Resource<unknown>

function approveCourse() {
	approveActionToggle.submit()
}

const showCourseRejectModal = ref(false)
const courseRejectReason = ref('')

const rejectActionToggle = createResource({
	url: 'lms.lms.api.process_approval',
	makeParams() {
		return {
			doctype: 'LMS Course',
			docname: course.data?.name,
			action: 'Reject',
			comments: courseRejectReason.value,
		}
	},
	onSuccess() {
		toast.success(__('Course rejected and returned for revisions'))
		showCourseRejectModal.value = false
		course.reload()
	},
	onError(err: any) {
		toast.error(err.messages?.[0] ?? __('Failed to reject course'))
	},
}) as Resource<unknown>

function openCourseRejectModal() {
	courseRejectReason.value = ''
	showCourseRejectModal.value = true
}

function confirmCourseReject() {
	if (!courseRejectReason.value.trim()) {
		toast.error(__('Please provide a reason or required changes.'))
		return
	}
	rejectActionToggle.submit()
}

const rejectionReason = createResource({
	url: 'lms.lms.api.get_rejection_reason',
	auto: true,
	makeParams() {
		return {
			course: props.courseName,
		}
	},
}) as Resource<unknown>

const isAdmin = computed<boolean>(() => {
	return Boolean(user.data?.is_moderator) || isInstructor() || canManageCourse.value
})

const breadcrumbs = computed(() => {
	const crumbs: {
		label: string
		route: { name: string; params?: Record<string, string> }
	}[] = [{ label: __('Courses'), route: { name: 'Courses' } }]
	if (course.data) {
		crumbs.push({
			label: course.data.title,
			route: { name: 'CourseDetail', params: { courseName: course.data.name } },
		})
	}
	return crumbs
})

usePageMeta(() => {
	return {
		title: course.data?.title,
		icon: brand.favicon,
	}
})
</script>
