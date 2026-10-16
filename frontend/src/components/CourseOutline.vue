<template>
	<div class="p-3 h-full">
		<div
			v-if="!hideHeader && title && (outline.data?.length || allowEdit)"
			class="flex items-center justify-between gap-x-2 mb-4 px-2"
			:class="{
				'sticky top-0 z-10 bg-surface-base border-b px-3 py-2.5 sm:px-5':
					allowEdit,
			}"
		>
			<div
				class="text-lg-semibold leading-5 text-ink-gray-9"
				:class="{ 'font-medium text-p-base': allowEdit }"
			>
				{{ __(title) }}
			</div>
			<Button size="sm" v-if="allowEdit" @click="openChapterForm()">
				<template #prefix>
					<span class="lucide-plus size-4" />
				</template>
				{{ __('Add') }}
			</Button>
		</div>

		<!-- Release Action Banner -->
		<div
			v-if="allowEdit && unreleasedSummary.data && unreleasedSummary.data.total_unreleased > 0"
			class="mb-4 rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-950 shadow-sm"
		>
			<div class="flex flex-col gap-2.5">
				<div class="flex items-start justify-between gap-2">
					<div>
						<div class="font-semibold text-p-sm flex items-center gap-1.5 text-amber-900">
							<span class="lucide-sparkles size-4 text-amber-600 shrink-0" />
							{{ __('New Content Pending Release') }}
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

					<!-- Principal Action: Preview Content -->
					<Button
						v-if="isPrincipal && course.data?.name"
						variant="outline"
						size="sm"
						@click="previewCourse"
					>
						<template #prefix>
							<span class="lucide-eye size-3.5" />
						</template>
						{{ __('Preview Content') }}
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
		<div
			v-if="allowEdit && outline.data && !outline.data.length"
			class="flex flex-col items-center justify-center gap-3 px-6 py-16 text-center text-ink-gray-5 h-full"
		>
			<span class="lucide-book-open size-8" />
			<div class="text-sm">{{ __('No chapters yet') }}</div>
			<Button @click="openChapterForm()">
				<template #prefix>
					<span class="lucide-plus size-4" />
				</template>
				{{ __('Create chapter') }}
			</Button>
		</div>
		<div
			v-else
			:class="{
				'border-2 rounded-md py-2 px-2': showOutline && outline.data?.length,
			}"
		>
			<Draggable
				:list="outline.data"
				:disabled="!allowEdit || chapterRenaming"
				item-key="name"
				group="chapters"
				@end="updateChapterOrder"
			>
				<template #item="{ element: chapter, index }">
					<div class="chapter-item">
						<ChapterRow
							:chapter="chapter"
							:index="index"
							:courseName="courseName"
							:allowEdit="allowEdit"
							:inlineSelect="inlineSelect"
							:editorLinks="editorLinks"
							:selectedLessonNumber="selectedLessonNumber"
							:creatingLesson="creatingLessonChapter === chapter.name"
							@select-lesson="(payload) => emit('select-lesson', payload)"
							@edit-chapter="openChapterForm"
							@rename-chapter="renameChapter"
							@renaming-change="(v) => (chapterRenaming = v)"
							@delete-chapter="trashChapter"
							@delete-lesson="
								({ lesson, chapter: chapterName }) =>
									trashLesson(lesson, chapterName)
							"
							@move-lesson="updateOutline"
							@create-lesson="createLessonInline"
						/>
					</div>
				</template>
			</Draggable>
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

<script setup lang="ts">
import {
	Badge,
	Button,
	createResource,
	Dialog,
	FormControl,
	toast,
} from 'frappe-ui'
import { computed, getCurrentInstance, inject, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Draggable from 'vuedraggable'

import ChapterRow from '@/components/ChapterRow.vue'
import { openFormRoute } from '@/composables/useFormRoute'
import type { OutlineChapter, OutlineLesson, Resource, SessionUser } from '@/types'

interface DraggableEvent {
	item: { __draggable_context: { element: OutlineChapter | OutlineLesson } }
	from: { dataset: { chapter: string } }
	to: { dataset: { chapter: string } }
	newIndex: number
}

interface DialogAction {
	label: string
	theme?: string
	variant?: string
	onClick: (close: () => void) => void
}
type DialogFn = (opts: {
	title: string
	message: string
	actions: DialogAction[]
}) => void

const router = useRouter()
const route = useRoute()
// True while a ChapterRow is in inline-rename mode; locks chapter drag.
const chapterRenaming = ref<boolean>(false)
const { $dialog } = getCurrentInstance()!.appContext.config
	.globalProperties as {
	$dialog: DialogFn
}

const user = inject<SessionUser>('$user')
const showRejectModal = ref(false)
const rejectionReasonInput = ref('')

const emit = defineEmits<{
	'select-lesson': [{ chapterNumber: string; lessonNumber: string }]
	// Keyed delete signals so the parent can match the open lesson precisely. The
	// name is carried per emit (no shared slot), so concurrent deletes can't name
	// the wrong doc and an unrelated reload can't consume the signal.
	'lesson-deleted': [{ lesson: string }]
	'chapter-deleted': [{ chapter: string }]
}>()

// The lesson currently being named inline (its docname), and the chapter whose
// "Add Lesson" button is mid-create (for the button spinner).
const creatingLessonChapter = ref<string>('')

const props = withDefaults(
	defineProps<{
		courseName: string
		showOutline?: boolean
		title?: string
		allowEdit?: boolean
		getProgress?: boolean
		completedLesson?: string | null
		inlineSelect?: boolean
		editorLinks?: boolean
		selectedLessonNumber?: string
		hideHeader?: boolean
	}>(),
	{
		showOutline: false,
		title: '',
		allowEdit: false,
		getProgress: false,
		inlineSelect: false,
		editorLinks: false,
		selectedLessonNumber: '',
		completedLesson: null,
		hideHeader: false,
	}
)

const unreleasedSummary = createResource({
	url: 'lms.lms.api.get_unreleased_content_summary',
	params: { course: props.courseName },
	auto: props.allowEdit,
})

const batchRelease = createResource({
	url: 'lms.lms.api.batch_release_content',
	makeParams(values: { action: string; reason?: string }) {
		return {
			course: props.courseName,
			action: values.action,
			reason: values.reason || '',
		}
	},
	onSuccess(data, values: any) {
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
		outline.reload()
		unreleasedSummary.reload()
	},
	onError(err: any) {
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
	if (!props.allowEdit) return false
	if (isPrincipal.value) return true
	return (
		(releaseMode.value === 'Teacher Can Publish' ||
			releaseMode.value === 'Teacher Choice') &&
		((unreleasedSummary.data?.draft_count ?? 0) > 0 ||
			(unreleasedSummary.data?.rejected_count ?? 0) > 0)
	)
})

const canTeacherSubmit = computed(() => {
	if (!props.allowEdit) return false
	return (
		(releaseMode.value === 'Principal Approval Required' ||
			releaseMode.value === 'Teacher Choice') &&
		((unreleasedSummary.data?.draft_count ?? 0) > 0 ||
			(unreleasedSummary.data?.rejected_count ?? 0) > 0)
	)
})

function confirmPublishAll() {
	$dialog({
		title: __('Publish New Content to Students'),
		message: __(
			'Are you sure you want to release all newly added chapters and lessons? This will make them immediately visible to eligible enrolled students.'
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
}

function confirmSubmitAll() {
	$dialog({
		title: __('Submit for Principal Approval'),
		message: __(
			'Submit newly added content to the Principal for review and publication? Content will remain hidden from students until approved.'
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
}

function confirmApproveAll() {
	$dialog({
		title: __('Approve and Publish'),
		message: __(
			'Approve and publish all pending content? It will become visible to students immediately.'
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
}

function openRejectDialog() {
	rejectionReasonInput.value = ''
	showRejectModal.value = true
}

function submitRejection() {
	batchRelease.submit({
		action: 'reject',
		reason: rejectionReasonInput.value,
	})
	showRejectModal.value = false
}

function previewCourse() {
	if (!props.courseName) return
	window.open(`/courses/${props.courseName}`, '_blank')
}

defineExpose({ openChapterForm, unreleasedSummary })

const outline = createResource({
	url: 'lms.lms.utils.get_course_outline',
	cache: ['course_outline', props.courseName],
	makeParams() {
		return { course: props.courseName, progress: props.getProgress }
	},
	auto: true,
}) as Resource<OutlineChapter[] | null>

watch(
	() => props.courseName,
	() => outline.reload()
)

watch(
	() => props.completedLesson,
	(lessonName) => {
		if (!lessonName || !outline.data) return
		for (const chapter of outline.data) {
			const found = chapter.lessons?.find((l) => l.name === lessonName)
			if (found) {
				found.is_complete = true
				break
			}
		}
	}
)

const deleteLesson = createResource({
	url: 'lms.lms.api.delete_lesson',
	makeParams(values: { lesson: string; chapter: string }) {
		return values
	},
	onSuccess() {
		outline.reload()
		toast.success(__('Lesson deleted successfully'))
	},
	onError(err: { messages?: string[] } | string) {
		toast.error(
			typeof err === 'string' ? err : err.messages?.[0] ?? __('Error')
		)
	},
})

const updateLessonIndex = createResource({
	url: 'lms.lms.api.update_lesson_index',
	makeParams(values: {
		lesson: string
		sourceChapter: string
		targetChapter: string
		idx: number
	}) {
		return values
	},
	onSuccess() {
		outline.reload()
		toast.success(__('Lesson moved successfully'))
	},
})

const updateChapterIndex = createResource({
	url: 'lms.lms.api.update_chapter_index',
	makeParams(values: { chapter: string; course: string; idx: number }) {
		return values
	},
	onSuccess() {
		outline.reload()
		toast.success(__('Chapter moved successfully'))
	},
})

const deleteChapter = createResource({
	url: 'lms.lms.api.delete_chapter',
	makeParams(values: { chapter: string }) {
		return values
	},
	onSuccess() {
		outline.reload()
		toast.success(__('Chapter deleted successfully'))
	},
	onError(err: { messages?: string[] } | string) {
		toast.error(
			typeof err === 'string' ? err : err.messages?.[0] ?? __('Error')
		)
	},
})

const renameChapterResource = createResource({
	url: 'lms.lms.api.upsert_chapter',
	makeParams(values: { chapter: OutlineChapter; title: string }) {
		return {
			name: values.chapter.name,
			title: values.title,
			course: props.courseName,
			is_scorm_package: values.chapter.is_scorm_package ?? 0,
			scorm_package: values.chapter.scorm_package ?? null,
		}
	},
	onSuccess() {
		outline.reload()
		toast.success(__('Chapter renamed successfully'))
	},
	onError(err: { messages?: string[] } | string) {
		outline.reload()
		toast.error(typeof err === 'string' ? err : err.messages?.[0] ?? 'Error')
	},
})

function renameChapter(payload: { chapter: OutlineChapter; title: string }) {
	renameChapterResource.submit(payload)
}

const errorMessage = (err: { messages?: string[] } | string): string =>
	typeof err === 'string' ? err : err.messages?.[0] ?? 'Error'

// Inserts the Course Lesson and its chapter reference in one request, so a
// failure on either rolls back atomically: no orphaned lesson. Returns the
// new lesson's docname.
const addLesson = createResource({
	url: 'lms.lms.api.create_lesson',
	makeParams(values: { chapter: string }) {
		return { chapter: values.chapter }
	},
})

// Create the lesson immediately as "Untitled lesson", then open it in the
// editor so the title is edited inline on the lesson itself.
function createLessonInline(payload: {
	chapter: OutlineChapter
	lessonIdx: number
}) {
	creatingLessonChapter.value = payload.chapter.name
	addLesson.submit(
		{ chapter: payload.chapter.name },
		{
			onSuccess(lessonName: string) {
				creatingLessonChapter.value = ''
				outline.reload().then(() => {
					const created = (outline.data ?? [])
						.flatMap((c) => c.lessons ?? [])
						.find((l) => l.name === lessonName)
					if (created) navigateToLesson(created)
				})
			},
			onError(err: { messages?: string[] } | string) {
				creatingLessonChapter.value = ''
				toast.error(errorMessage(err))
			},
		}
	)
}

function navigateToLesson(lesson: OutlineLesson) {
	const [chapterNumber, lessonNumber] = lesson.number.split('-')
	if (props.inlineSelect) {
		emit('select-lesson', { chapterNumber, lessonNumber })
		return
	}
	if (props.editorLinks) {
		router.push({
			name: 'CourseDetail',
			params: { courseName: props.courseName },
			hash: '#editor',
			query: { editLesson: lesson.number },
		})
	}
}

function trashLesson(lessonName: string, chapterName: string) {
	$dialog({
		title: __('Delete this lesson?'),
		message: __(
			'Deleting this lesson will permanently remove it from the course. This action cannot be undone. Are you sure you want to continue?'
		),
		actions: [
			{
				label: __('Delete'),
				theme: 'red',
				variant: 'solid',
				onClick(close) {
					// Per-call onSuccess closes over this lessonName, so the editor is
					// told exactly which lesson went: no shared slot to drift on
					// concurrent deletes. Runs alongside the resource-level reload.
					deleteLesson.submit(
						{ lesson: lessonName, chapter: chapterName },
						{ onSuccess: () => emit('lesson-deleted', { lesson: lessonName }) }
					)
					close()
				},
			},
		],
	})
}

function trashChapter(chapterName: string) {
	$dialog({
		title: __('Delete this chapter?'),
		message: __(
			'Deleting this chapter will also delete all its lessons and permanently remove it from the course. This action cannot be undone. Are you sure you want to continue?'
		),
		actions: [
			{
				label: __('Delete'),
				theme: 'red',
				variant: 'solid',
				onClick(close) {
					deleteChapter.submit(
						{ chapter: chapterName },
						{
							onSuccess: () =>
								emit('chapter-deleted', { chapter: chapterName }),
						}
					)
					close()
				},
			},
		],
	})
}

// openFormRoute, not a bare router.push: it stamps the history entry so the
// form's own back/Escape pops that one entry instead of replacing to the parent
// and leaving a duplicate behind.
//
// route.hash and route.query travel with it because CourseDetail reads its
// active tab off the hash and CourseEditor reads the open lesson off the query
// (design doc C2). Dropping either would reset the page behind the open form.
function openChapterForm(chapter: OutlineChapter | null = null) {
	openFormRoute(router, {
		name: 'ChapterForm',
		params: {
			courseName: props.courseName,
			chapterName: chapter?.name ?? 'new',
		},
		hash: route.hash,
		query: { ...route.query },
	})
}

function updateOutline(e: DraggableEvent) {
	updateLessonIndex.submit({
		lesson: e.item.__draggable_context.element.name,
		sourceChapter: e.from.dataset.chapter,
		targetChapter: e.to.dataset.chapter,
		idx: e.newIndex,
	})
}

function updateChapterOrder(e: DraggableEvent) {
	updateChapterIndex.submit({
		chapter: e.item.__draggable_context.element.name,
		course: props.courseName,
		idx: e.newIndex,
	})
}
</script>
