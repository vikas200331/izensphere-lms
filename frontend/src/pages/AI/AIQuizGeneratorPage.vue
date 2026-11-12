<template>
	<div class="flex-1 flex flex-col min-h-0 bg-surface-base overflow-y-auto">
		<PageHeader
			:breadcrumbs="[
				{ label: __('Assessments'), route: { name: 'Quizzes' } },
				{ label: __('AI Quiz Generator') },
			]"
		>
			<template #actions>
				<Button
					variant="solid"
					theme="violet"
					size="sm"
					@click="showModal = true"
				>
					<template #prefix><span class="lucide-sparkles size-4"></span></template>
					{{ __('Generate Quiz with AI') }}
				</Button>
			</template>
		</PageHeader>

		<div class="max-w-7xl mx-auto w-full p-4 md:p-6 space-y-6">
			<!-- Header Banner -->
			<div class="rounded-xl border bg-gradient-to-r from-violet-900 to-purple-900 text-white p-6 shadow-sm">
				<div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
					<div>
						<div class="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-xs font-semibold backdrop-blur-sm mb-2">
							<span class="lucide-sparkles size-3.5 text-amber-300"></span>
							{{ __('Izensphere AI Assessment') }}
						</div>
						<h1 class="text-2xl font-bold tracking-tight">
							{{ __('AI Quiz Generator') }}
						</h1>
						<p class="text-sm text-purple-200 mt-1 max-w-2xl">
							{{ __('Generate curriculum-grounded quizzes directly from LMS courses, chapters, and lessons. Supports MCQs, Multi-Select, True/False, Fill in Blanks, and Short Answers with granular per-question regeneration.') }}
						</p>
					</div>

					<Button
						variant="solid"
						theme="white"
						size="lg"
						@click="showModal = true"
					>
						<template #prefix><span class="lucide-sparkles size-4 text-violet-700"></span></template>
						<span class="text-violet-900 font-bold">{{ __('Launch Quiz Generator') }}</span>
					</Button>
				</div>
			</div>

			<!-- Quick Actions / Features Cards -->
			<div class="grid grid-cols-1 md:grid-cols-3 gap-6">
				<div class="rounded-xl border bg-surface-base p-5 shadow-sm space-y-2">
					<div class="flex size-10 items-center justify-center rounded-lg bg-violet-100 text-violet-700">
						<span class="lucide-book-open size-5"></span>
					</div>
					<h3 class="font-bold text-ink-gray-9 text-sm">{{ __('Chapter Content Grounding') }}</h3>
					<p class="text-xs text-ink-gray-6">
						{{ __('Questions are synthesized strictly from actual lesson text, Editor.js blocks, and attached course notes. Zero hallucinated trivia.') }}
					</p>
				</div>

				<div class="rounded-xl border bg-surface-base p-5 shadow-sm space-y-2">
					<div class="flex size-10 items-center justify-center rounded-lg bg-emerald-100 text-emerald-700">
						<span class="lucide-refresh-cw size-5"></span>
					</div>
					<h3 class="font-bold text-ink-gray-9 text-sm">{{ __('Individual Question Regeneration') }}</h3>
					<p class="text-xs text-ink-gray-6">
						{{ __('Review generated items and regenerate a single question on demand without disturbing the rest of the generated quiz.') }}
					</p>
				</div>

				<div class="rounded-xl border bg-surface-base p-5 shadow-sm space-y-2">
					<div class="flex size-10 items-center justify-center rounded-lg bg-sky-100 text-sky-700">
						<span class="lucide-shield-check size-5"></span>
					</div>
					<h3 class="font-bold text-ink-gray-9 text-sm">{{ __('Institutional Approval Workflow') }}</h3>
					<p class="text-xs text-ink-gray-6">
						{{ __('Draft &rarr; AI Generated &rarr; Teacher Review &rarr; Principal Approved &rarr; Published to Students.') }}
					</p>
				</div>
			</div>

			<!-- Recent Quizzes List -->
			<div class="rounded-xl border bg-surface-base shadow-sm overflow-hidden space-y-4 p-5">
				<div class="flex items-center justify-between border-b pb-3">
					<div>
						<h2 class="text-base font-semibold text-ink-gray-9">{{ __('Recently Created LMS Quizzes') }}</h2>
						<p class="text-xs text-ink-gray-5">{{ __('Manage and review quiz assessments') }}</p>
					</div>
					<router-link :to="{ name: 'Quizzes' }">
						<Button variant="ghost" size="sm">
							{{ __('View All Quizzes') }} &rarr;
						</Button>
					</router-link>
				</div>

				<div v-if="loading" class="text-center py-12 text-gray-400">
					{{ __('Loading quizzes...') }}
				</div>

				<div v-else-if="!quizzesList.length" class="text-center py-12 text-gray-500">
					{{ __('No quizzes found. Click the button above to generate one!') }}
				</div>

				<div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
					<div
						v-for="q in quizzesList"
						:key="q.name"
						class="rounded-xl border bg-surface-base p-4 shadow-sm hover:border-violet-300 transition-colors space-y-3"
					>
						<div class="flex items-start justify-between gap-2">
							<h3 class="font-bold text-ink-gray-9 text-sm line-clamp-1">{{ q.title }}</h3>
							<Badge
								:theme="q.release_status === 'Released' ? 'green' : (q.release_status === 'Pending Principal Approval' ? 'orange' : 'gray')"
								variant="subtle"
								size="sm"
							>
								{{ q.release_status || 'Released' }}
							</Badge>
						</div>

						<div class="text-xs text-ink-gray-6 space-y-1">
							<div v-if="q.course">{{ __('Course:') }} {{ q.course }}</div>
							<div>{{ __('Total Marks:') }} <strong>{{ q.total_marks }}</strong> &bull; {{ __('Passing:') }} {{ q.passing_percentage }}%</div>
						</div>

						<div class="flex items-center justify-between border-t pt-2 text-xs">
							<router-link :to="{ name: 'QuizForm', params: { quizID: q.name } }">
								<Button size="sm" variant="ghost">
									{{ __('Edit Quiz') }}
								</Button>
							</router-link>

							<router-link :to="{ name: 'AIQuizAnalytics', params: { quizID: q.name } }">
								<Button size="sm" variant="outline">
									<template #prefix><span class="lucide-bar-chart-2 size-3.5"></span></template>
									{{ __('Analytics') }}
								</Button>
							</router-link>
						</div>
					</div>
				</div>
			</div>
		</div>

		<!-- AI Quiz Modal -->
		<AIQuizModal
			v-model="showModal"
			@quiz-saved="loadQuizzes"
		/>
	</div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import PageHeader from '@/components/Layouts/PageHeader.vue'
import AIQuizModal from '@/components/AI/AIQuizModal.vue'
import { Button, Badge, call, toast } from 'frappe-ui'

const showModal = ref(false)
const loading = ref(false)
const quizzesList = ref([])

onMounted(() => {
	loadQuizzes()
})

async function loadQuizzes() {
	loading.value = true
	try {
		const res = await call('frappe.client.get_list', {
			doctype: 'LMS Quiz',
			fields: ['name', 'title', 'course', 'lesson', 'total_marks', 'passing_percentage', 'release_status', 'creation'],
			order_by: 'creation desc',
			limit_page_length: 20,
		})
		quizzesList.value = res || []
	} catch (e) {
		console.error(e)
	} finally {
		loading.value = false
	}
}
</script>

