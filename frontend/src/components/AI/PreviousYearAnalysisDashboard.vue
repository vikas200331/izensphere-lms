<template>
	<div class="space-y-6">
		<!-- KPI Summary Cards -->
		<div class="grid grid-cols-2 md:grid-cols-5 gap-4">
			<div class="rounded-xl border bg-white p-4 shadow-sm">
				<div class="text-xs font-semibold text-gray-500 uppercase tracking-wide">
					{{ __('Uploaded Papers') }}
				</div>
				<div class="text-2xl font-bold text-gray-900 mt-1">
					{{ analysisData.total_uploaded_papers || 0 }}
				</div>
				<div class="text-[11px] text-gray-400 mt-1">
					{{ analysisData.total_processed_papers || 0 }} {{ __('processed') }}
				</div>
			</div>

			<div class="rounded-xl border bg-white p-4 shadow-sm">
				<div class="text-xs font-semibold text-gray-500 uppercase tracking-wide">
					{{ __('Extracted Questions') }}
				</div>
				<div class="text-2xl font-bold text-violet-700 mt-1">
					{{ analysisData.total_extracted_questions || 0 }}
				</div>
				<div class="text-[11px] text-gray-400 mt-1">
					{{ __('Across all examination years') }}
				</div>
			</div>

			<div class="rounded-xl border bg-white p-4 shadow-sm">
				<div class="text-xs font-semibold text-gray-500 uppercase tracking-wide">
					{{ __('Repeated Questions') }}
				</div>
				<div class="text-2xl font-bold text-amber-600 mt-1">
					{{ analysisData.total_repeated_questions || 0 }}
				</div>
				<div class="text-[11px] text-gray-400 mt-1">
					{{ (analysisData.repeated_questions || []).length }} {{ __('concept clusters') }}
				</div>
			</div>

			<div class="rounded-xl border bg-white p-4 shadow-sm">
				<div class="text-xs font-semibold text-gray-500 uppercase tracking-wide">
					{{ __('Analysis Period') }}
				</div>
				<div class="text-lg font-bold text-indigo-700 mt-1 truncate">
					{{ analysisData.academic_years_covered || 'Multi-Year' }}
				</div>
				<div class="text-[11px] text-gray-400 mt-1">
					{{ __('Historical timeline') }}
				</div>
			</div>

			<div class="rounded-xl border bg-white p-4 shadow-sm col-span-2 md:col-span-1">
				<div class="text-xs font-semibold text-gray-500 uppercase tracking-wide">
					{{ __('AI Analysis Status') }}
				</div>
				<div class="flex items-center gap-1.5 mt-2">
					<span class="size-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
					<span class="text-sm font-bold text-emerald-700">
						{{ analysisData.status || 'Completed' }}
					</span>
				</div>
				<div class="text-[11px] text-gray-400 mt-1 truncate">
					{{ analysisData.analysis_date ? new Date(analysisData.analysis_date).toLocaleDateString() : 'Active' }}
				</div>
			</div>
		</div>

		<!-- Topic Importance & Weightage Table -->
		<div class="rounded-xl border bg-white shadow-sm overflow-hidden">
			<div class="p-4 border-b bg-gray-50/50 flex flex-col md:flex-row md:items-center justify-between gap-3">
				<div>
					<h3 class="text-sm font-bold text-gray-900">
						{{ __('Topic & Chapter Importance Ranking') }}
					</h3>
					<p class="text-xs text-gray-500">
						{{ __('Ranked by cumulative historical examination frequency, marks allocation, and multi-year occurrence.') }}
					</p>
				</div>

				<div class="flex items-center gap-2">
					<Button
						variant="solid"
						theme="violet"
						size="sm"
						@click="$emit('generate-questions')"
					>
						<template #prefix><span class="lucide-sparkles size-3.5"></span></template>
						{{ __('Generate New Questions') }}
					</Button>
				</div>
			</div>

			<div class="overflow-x-auto">
				<table class="w-full text-left text-xs">
					<thead class="bg-gray-50 text-gray-600 font-semibold uppercase tracking-wider border-b">
						<tr>
							<th class="py-3 px-4">{{ __('Chapter / Topic') }}</th>
							<th class="py-3 px-4 text-center">{{ __('Questions Found') }}</th>
							<th class="py-3 px-4 text-center">{{ __('Total Marks') }}</th>
							<th class="py-3 px-4 text-center">{{ __('Importance') }}</th>
							<th class="py-3 px-4 text-center">{{ __('Trend Across Years') }}</th>
							<th class="py-3 px-4">{{ __('Years Appeared') }}</th>
						</tr>
					</thead>
					<tbody class="divide-y text-gray-700">
						<tr
							v-for="item in (analysisData.topic_importance || [])"
							:key="item.topic"
							class="hover:bg-gray-50/80 transition-colors"
						>
							<td class="py-3 px-4 font-semibold text-gray-900">
								{{ item.topic }}
								<div class="text-[11px] text-gray-400 font-normal">
									{{ item.percentage }}% {{ __('of total historical questions') }}
								</div>
							</td>
							<td class="py-3 px-4 text-center font-bold text-gray-800">
								{{ item.questions_count }}
							</td>
							<td class="py-3 px-4 text-center font-medium text-gray-700">
								{{ item.total_marks }} M
							</td>
							<td class="py-3 px-4 text-center">
								<span
									class="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-bold"
									:class="{
										'bg-rose-100 text-rose-800': item.importance === 'High',
										'bg-amber-100 text-amber-800': item.importance === 'Medium',
										'bg-gray-100 text-gray-700': item.importance === 'Low',
									}"
								>
									{{ item.importance }}
								</span>
							</td>
							<td class="py-3 px-4 text-center">
								<span
									class="inline-flex items-center gap-1 text-[11px] font-medium"
									:class="{
										'text-emerald-700': item.trend === 'Increasing Frequency',
										'text-rose-700': item.trend === 'Decreasing Frequency',
										'text-gray-600': item.trend === 'Consistent',
									}"
								>
									<span v-if="item.trend === 'Increasing Frequency'" class="lucide-trending-up size-3.5"></span>
									<span v-else-if="item.trend === 'Decreasing Frequency'" class="lucide-trending-down size-3.5"></span>
									<span v-else class="lucide-minus size-3.5"></span>
									{{ item.trend }}
								</span>
							</td>
							<td class="py-3 px-4">
								<div class="flex flex-wrap gap-1">
									<span
										v-for="yr in (item.years_appeared || [])"
										:key="yr"
										class="px-1.5 py-0.5 rounded bg-gray-100 text-gray-700 text-[10px] font-medium font-mono"
									>
										{{ yr }}
									</span>
								</div>
							</td>
						</tr>
					</tbody>
				</table>
			</div>
		</div>

		<!-- Repeated Questions & Semantic Variations -->
		<div class="rounded-xl border bg-white shadow-sm overflow-hidden">
			<div class="p-4 border-b bg-gray-50/50 flex items-center justify-between">
				<div>
					<h3 class="text-sm font-bold text-gray-900">
						{{ __('Repeated Questions & Semantic Variations Across Years') }}
					</h3>
					<p class="text-xs text-gray-500">
						{{ __('Questions testing identical underlying concepts repeated across different examination years.') }}
					</p>
				</div>

				<span class="text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-200 px-2.5 py-1 rounded-full">
					{{ (analysisData.repeated_questions || []).length }} {{ __('Clusters Found') }}
				</span>
			</div>

			<div class="divide-y divide-gray-100">
				<div
					v-for="(cluster, cIdx) in (analysisData.repeated_questions || [])"
					:key="cIdx"
					class="p-4 hover:bg-gray-50/50 transition-colors"
				>
					<div class="flex items-start justify-between gap-4">
						<div class="space-y-1.5 flex-1">
							<div class="flex items-center gap-2 flex-wrap">
								<span class="text-xs font-bold text-violet-700 bg-violet-50 px-2 py-0.5 rounded">
									{{ cluster.topic || 'General' }}
								</span>
								<span class="text-xs font-bold text-amber-700 bg-amber-50 px-2 py-0.5 rounded">
									{{ __('Repeated') }} {{ cluster.frequency }} {{ __('times') }}
								</span>
								<span class="text-xs text-gray-500">
									{{ cluster.distinct_years_count }} {{ __('distinct years:') }}
									<strong class="text-gray-800 font-mono">{{ (cluster.examination_years || []).join(', ') }}</strong>
								</span>
							</div>

							<div class="text-sm font-semibold text-gray-900">
								{{ cluster.canonical_question }}
							</div>
						</div>

						<Button
							variant="ghost"
							size="sm"
							@click="toggleClusterExpand(cIdx)"
						>
							{{ expandedClusters[cIdx] ? __('Hide Variations') : __('View Variations') }}
						</Button>
					</div>

					<!-- Expandable variations list -->
					<div
						v-if="expandedClusters[cIdx]"
						class="mt-3 pl-4 border-l-2 border-amber-400 space-y-2 bg-amber-50/30 p-3 rounded-r-lg"
					>
						<div class="text-xs font-bold text-amber-900 uppercase tracking-wide">
							{{ __('Historical Appearances & Phrasing Variations:') }}
						</div>
						<div
							v-for="(v, vIdx) in (cluster.variations || [])"
							:key="vIdx"
							class="text-xs text-gray-800 flex items-start gap-2"
						>
							<span class="font-mono font-bold text-amber-700 flex-shrink-0">[{{ v.year }}]</span>
							<span class="flex-1">{{ v.question }}</span>
							<span class="text-gray-400 text-[10px] flex-shrink-0">({{ v.marks }} Marks)</span>
						</div>
					</div>
				</div>
			</div>
		</div>

		<!-- Distributions Grid -->
		<div class="grid grid-cols-1 md:grid-cols-3 gap-6">
			<!-- Year-wise Question Distribution -->
			<div class="rounded-xl border bg-white p-4 shadow-sm space-y-3">
				<h4 class="text-xs font-bold text-gray-800 uppercase tracking-wide">
					{{ __('Year-Wise Question Volume') }}
				</h4>
				<div class="space-y-2">
					<div
						v-for="yr in (analysisData.year_distribution || [])"
						:key="yr.year"
						class="text-xs space-y-1"
					>
						<div class="flex justify-between font-semibold text-gray-700">
							<span class="font-mono">{{ yr.year }}</span>
							<span>{{ yr.questions_count }} Qs ({{ yr.total_marks }} M)</span>
						</div>
						<div class="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
							<div
								class="bg-violet-600 h-2 rounded-full transition-all"
								:style="{ width: `${Math.min(100, (yr.questions_count / (maxYearCount || 1)) * 100)}%` }"
							></div>
						</div>
					</div>
				</div>
			</div>

			<!-- Marks Distribution -->
			<div class="rounded-xl border bg-white p-4 shadow-sm space-y-3">
				<h4 class="text-xs font-bold text-gray-800 uppercase tracking-wide">
					{{ __('Historical Marks Distribution') }}
				</h4>
				<div class="space-y-2">
					<div
						v-for="(count, band) in (analysisData.marks_distribution || {})"
						:key="band"
						class="text-xs space-y-1"
					>
						<div class="flex justify-between font-semibold text-gray-700">
							<span>{{ band }}</span>
							<span>{{ count }} Qs</span>
						</div>
						<div class="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
							<div
								class="bg-indigo-600 h-2 rounded-full transition-all"
								:style="{ width: `${Math.min(100, (count / (analysisData.total_extracted_questions || 1)) * 100)}%` }"
							></div>
						</div>
					</div>
				</div>
			</div>

			<!-- Difficulty Distribution -->
			<div class="rounded-xl border bg-white p-4 shadow-sm space-y-3">
				<h4 class="text-xs font-bold text-gray-800 uppercase tracking-wide">
					{{ __('Estimated Difficulty Profile') }}
				</h4>
				<div class="space-y-3 pt-2">
					<div>
						<div class="flex justify-between text-xs font-semibold text-emerald-800 mb-1">
							<span>{{ __('Easy (Recall & Definition)') }}</span>
							<span>{{ analysisData.difficulty_distribution?.Easy_pct || 0 }}%</span>
						</div>
						<div class="w-full bg-gray-100 rounded-full h-2.5 overflow-hidden">
							<div
								class="bg-emerald-500 h-2.5 rounded-full"
								:style="{ width: `${analysisData.difficulty_distribution?.Easy_pct || 0}%` }"
							></div>
						</div>
					</div>

					<div>
						<div class="flex justify-between text-xs font-semibold text-amber-800 mb-1">
							<span>{{ __('Medium (Application & Explanation)') }}</span>
							<span>{{ analysisData.difficulty_distribution?.Medium_pct || 0 }}%</span>
						</div>
						<div class="w-full bg-gray-100 rounded-full h-2.5 overflow-hidden">
							<div
								class="bg-amber-500 h-2.5 rounded-full"
								:style="{ width: `${analysisData.difficulty_distribution?.Medium_pct || 0}%` }"
							></div>
						</div>
					</div>

					<div>
						<div class="flex justify-between text-xs font-semibold text-rose-800 mb-1">
							<span>{{ __('Hard (Design & Problem Solving)') }}</span>
							<span>{{ analysisData.difficulty_distribution?.Hard_pct || 0 }}%</span>
						</div>
						<div class="w-full bg-gray-100 rounded-full h-2.5 overflow-hidden">
							<div
								class="bg-rose-500 h-2.5 rounded-full"
								:style="{ width: `${analysisData.difficulty_distribution?.Hard_pct || 0}%` }"
							></div>
						</div>
					</div>
				</div>
			</div>
		</div>

		<!-- Pedagogical Disclaimer Notice -->
		<div class="rounded-xl bg-gray-50 border p-4 text-xs text-gray-500 flex items-start gap-3">
			<span class="lucide-info size-4 text-gray-400 flex-shrink-0 mt-0.5"></span>
			<p>
				{{ __('Historical examination analysis is computed empirically from uploaded examination papers to assist teachers in curriculum coverage, topic weightage, and high-yield revision. AI analysis reflects historical trends and does not present predictions as guaranteed examination questions.') }}
			</p>
		</div>
	</div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Button } from 'frappe-ui'

const props = defineProps<{
	analysisData: any
}>()

defineEmits<{
	(e: 'generate-questions'): void
	(e: 'generate-model-paper'): void
}>()

const expandedClusters = ref<Record<number, boolean>>({})

function toggleClusterExpand(idx: number) {
	expandedClusters.value[idx] = !expandedClusters.value[idx]
}

const maxYearCount = computed(() => {
	const years = props.analysisData?.year_distribution || []
	if (!years.length) return 1
	return Math.max(...years.map((y: any) => y.questions_count || 1))
})
</script>
