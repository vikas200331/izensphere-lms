<template>
	<div class="flex-1 flex flex-col min-h-0 bg-surface-base overflow-y-auto">
		<PageHeader
			:breadcrumbs="[
				{ label: __('Assessments'), route: { name: 'Quizzes' } },
				{ label: __('Quiz Analytics & Performance') },
			]"
		>
			<template #actions>
				<router-link
					v-if="quizID"
					:to="{ name: 'QuizForm', params: { quizID: quizID } }"
				>
					<Button variant="outline" size="sm">
						{{ __('Back to Quiz') }}
					</Button>
				</router-link>
			</template>
		</PageHeader>

		<div class="max-w-7xl mx-auto w-full p-4 md:p-6 space-y-6">
			<!-- Loading state -->
			<div v-if="loading" class="text-center py-20 text-gray-400">
				{{ __('Calculating assessment performance metrics...') }}
			</div>

			<template v-else-if="analytics">
				<!-- Header Title -->
				<div class="rounded-xl border bg-surface-base p-6 shadow-sm space-y-3">
					<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
						<div>
							<Badge variant="subtle" theme="violet" size="sm">{{ __('Assessment Analytics') }}</Badge>
							<h1 class="text-2xl font-bold text-ink-gray-9 mt-1">{{ analytics.quiz_title }}</h1>
							<p class="text-xs text-ink-gray-6">{{ __('Total Marks:') }} {{ analytics.total_marks }}</p>
						</div>

						<div class="flex items-center gap-3">
							<div class="rounded-lg bg-violet-50 dark:bg-violet-950/30 p-3 text-center min-w-24">
								<div class="text-2xl font-bold text-violet-700">{{ analytics.total_submissions }}</div>
								<div class="text-[11px] text-ink-gray-6 font-medium">{{ __('Submissions') }}</div>
							</div>
							<div class="rounded-lg bg-emerald-50 dark:bg-emerald-950/30 p-3 text-center min-w-24">
								<div class="text-2xl font-bold text-emerald-700">{{ analytics.pass_rate }}%</div>
								<div class="text-[11px] text-ink-gray-6 font-medium">{{ __('Pass Rate') }}</div>
							</div>
							<div class="rounded-lg bg-sky-50 dark:bg-sky-950/30 p-3 text-center min-w-24">
								<div class="text-2xl font-bold text-sky-700">{{ analytics.average_score }}</div>
								<div class="text-[11px] text-ink-gray-6 font-medium">{{ __('Avg Score') }}</div>
							</div>
						</div>
					</div>
				</div>

				<!-- Pedagogical Recommendations Card -->
				<div class="rounded-xl border border-violet-200 bg-violet-50/40 p-5 shadow-sm space-y-3">
					<div class="flex items-center gap-2 text-violet-900 font-bold text-sm">
						<span class="lucide-sparkles size-4 text-violet-600"></span>
						{{ __('AI Pedagogical Insights & Remedial Recommendations') }}
					</div>
					<div class="space-y-2 text-xs text-violet-950">
						<div
							v-for="(rec, idx) in analytics.recommendations"
							:key="idx"
							class="flex items-start gap-2.5 p-2 rounded bg-white/70 dark:bg-gray-800/70 border border-violet-100"
						>
							<span class="lucide-arrow-right size-3.5 text-violet-600 mt-0.5 shrink-0"></span>
							<span>{{ rec }}</span>
						</div>
					</div>
				</div>

				<!-- 2-Column Analytics: Difficulty & Weak Topics -->
				<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
					<!-- Difficulty Performance -->
					<div class="rounded-xl border bg-surface-base p-5 shadow-sm space-y-4">
						<h3 class="text-sm font-semibold text-ink-gray-9 flex items-center gap-2">
							<span class="lucide-bar-chart-2 size-4 text-violet-600"></span>
							{{ __('Performance by Question Difficulty') }}
						</h3>
						<div class="space-y-3 text-xs">
							<div
								v-for="(data, diff) in analytics.difficulty_performance"
								:key="diff"
								class="space-y-1"
							>
								<div class="flex items-center justify-between font-medium">
									<span class="text-ink-gray-8">{{ diff }} ({{ data.attempts }} attempts)</span>
									<span class="font-bold" :class="data.accuracy >= 60 ? 'text-emerald-600' : 'text-red-600'">
										{{ data.accuracy }}%
									</span>
								</div>
								<div class="w-full bg-gray-200 rounded-full h-2">
									<div
										class="h-2 rounded-full transition-all"
										:class="data.accuracy >= 60 ? 'bg-emerald-500' : 'bg-red-500'"
										:style="{ width: `${data.accuracy}%` }"
									></div>
								</div>
							</div>
						</div>
					</div>

					<!-- Chapter Performance / Weak Topics -->
					<div class="rounded-xl border bg-surface-base p-5 shadow-sm space-y-4">
						<h3 class="text-sm font-semibold text-ink-gray-9 flex items-center gap-2">
							<span class="lucide-folder-tree size-4 text-violet-600"></span>
							{{ __('Chapter-Wise Topic Mastery') }}
						</h3>
						<div class="space-y-3 text-xs">
							<div
								v-for="(ch, idx) in analytics.chapter_performance"
								:key="idx"
								class="space-y-1"
							>
								<div class="flex items-center justify-between font-medium">
									<span class="text-ink-gray-8 truncate max-w-xs">{{ ch.chapter }}</span>
									<span class="font-bold" :class="ch.accuracy >= 60 ? 'text-emerald-600' : 'text-amber-600'">
										{{ ch.accuracy }}%
									</span>
								</div>
								<div class="w-full bg-gray-200 rounded-full h-2">
									<div
										class="h-2 rounded-full transition-all"
										:class="ch.accuracy >= 60 ? 'bg-emerald-500' : 'bg-amber-500'"
										:style="{ width: `${ch.accuracy}%` }"
									></div>
								</div>
							</div>
						</div>
					</div>
				</div>

				<!-- Question-Wise Performance Table -->
				<div class="rounded-xl border bg-surface-base shadow-sm overflow-hidden">
					<div class="p-4 border-b">
						<h3 class="text-sm font-semibold text-ink-gray-9">
							{{ __('Question-by-Question Accuracy & Error Rate Analysis') }}
						</h3>
					</div>

					<div class="overflow-x-auto">
						<table class="w-full text-left text-xs border-collapse">
							<thead>
								<tr class="bg-gray-50/80 dark:bg-gray-800/80 text-ink-gray-7 uppercase tracking-wider text-[11px] border-b">
									<th class="p-3 font-semibold">{{ __('Question') }}</th>
									<th class="p-3 font-semibold">{{ __('Difficulty') }}</th>
									<th class="p-3 font-semibold">{{ __('Attempts') }}</th>
									<th class="p-3 font-semibold">{{ __('Correct') }}</th>
									<th class="p-3 font-semibold">{{ __('Accuracy') }}</th>
									<th class="p-3 font-semibold">{{ __('Status') }}</th>
								</tr>
							</thead>
							<tbody class="divide-y divide-gray-100 dark:divide-gray-800">
								<tr
									v-for="q in analytics.question_performance"
									:key="q.question_id"
									class="hover:bg-gray-50/50 transition-colors"
								>
									<td class="p-3 font-medium text-ink-gray-9 max-w-md truncate">
										{{ q.question_text }}
									</td>
									<td class="p-3">
										<Badge variant="subtle" size="sm" :theme="q.difficulty === 'Easy' ? 'green' : (q.difficulty === 'Hard' ? 'red' : 'orange')">
											{{ q.difficulty }}
										</Badge>
									</td>
									<td class="p-3 font-mono">{{ q.attempts }}</td>
									<td class="p-3 font-mono text-emerald-700 font-bold">{{ q.correct_count }}</td>
									<td class="p-3 font-mono font-bold" :class="q.accuracy_percentage >= 60 ? 'text-emerald-700' : 'text-red-600'">
										{{ q.accuracy_percentage }}%
									</td>
									<td class="p-3">
										<Badge
											:theme="q.accuracy_percentage >= 70 ? 'green' : (q.accuracy_percentage >= 40 ? 'orange' : 'red')"
											variant="subtle"
											size="sm"
										>
											{{ q.accuracy_percentage >= 70 ? __('Well Understood') : (q.accuracy_percentage >= 40 ? __('Needs Practice') : __('Critical Weakness')) }}
										</Badge>
									</td>
								</tr>
							</tbody>
						</table>
					</div>
				</div>

				<!-- Student Leaderboard / Scores Table -->
				<div class="rounded-xl border bg-surface-base shadow-sm overflow-hidden">
					<div class="p-4 border-b">
						<h3 class="text-sm font-semibold text-ink-gray-9">
							{{ __('Student-Wise Submissions & Scorecard') }}
						</h3>
					</div>

					<div class="overflow-x-auto">
						<table class="w-full text-left text-xs border-collapse">
							<thead>
								<tr class="bg-gray-50/80 dark:bg-gray-800/80 text-ink-gray-7 uppercase tracking-wider text-[11px] border-b">
									<th class="p-3 font-semibold">{{ __('Student') }}</th>
									<th class="p-3 font-semibold">{{ __('Score') }}</th>
									<th class="p-3 font-semibold">{{ __('Percentage') }}</th>
									<th class="p-3 font-semibold">{{ __('Result') }}</th>
									<th class="p-3 font-semibold">{{ __('Submission Date') }}</th>
								</tr>
							</thead>
							<tbody class="divide-y divide-gray-100 dark:divide-gray-800">
								<tr
									v-for="sub in analytics.student_scores"
									:key="sub.name"
									class="hover:bg-gray-50/50 transition-colors"
								>
									<td class="p-3 font-medium text-ink-gray-9">
										{{ sub.member_name || sub.member }}
									</td>
									<td class="p-3 font-mono font-bold">
										{{ sub.score }} / {{ sub.score_out_of }}
									</td>
									<td class="p-3 font-mono font-bold">
										{{ sub.percentage }}%
									</td>
									<td class="p-3">
										<Badge
											:theme="sub.percentage >= sub.passing_percentage ? 'green' : 'red'"
											variant="subtle"
											size="sm"
										>
											{{ sub.percentage >= sub.passing_percentage ? __('Passed') : __('Failed') }}
										</Badge>
									</td>
									<td class="p-3 text-ink-gray-5">
										{{ sub.creation }}
									</td>
								</tr>
							</tbody>
						</table>
					</div>
				</div>
			</template>
		</div>
	</div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import PageHeader from '@/components/Layouts/PageHeader.vue'
import { Button, Badge, call, toast } from 'frappe-ui'

const route = useRoute()
const quizID = ref(route.params.quizID)
const loading = ref(false)
const analytics = ref(null)

onMounted(async () => {
	if (quizID.value) {
		await loadAnalytics(quizID.value)
	}
})

async function loadAnalytics(id) {
	loading.value = true
	try {
		const res = await call('lms.lms.ai.ai_assessment_api.api_get_quiz_analytics', {
			quiz_id: id,
		})
		analytics.value = res
	} catch (e) {
		toast.error(__('Failed to load quiz analytics.'))
	} finally {
		loading.value = false
	}
}
</script>

