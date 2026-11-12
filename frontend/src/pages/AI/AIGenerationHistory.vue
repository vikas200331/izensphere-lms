<template>
	<div class="flex-1 flex flex-col min-h-0 bg-surface-base overflow-y-auto">
		<PageHeader :breadcrumbs="[{ label: __('Assessments'), route: { name: 'Quizzes' } }, { label: __('AI Generation History') }]">
			<template #actions>
				<Button variant="outline" size="sm" @click="loadHistory()">
					<template #prefix><span class="lucide-refresh-cw size-3.5"></span></template>
					{{ __('Refresh') }}
				</Button>
			</template>
		</PageHeader>

		<div class="max-w-7xl mx-auto w-full p-4 md:p-6 space-y-6">
			<!-- Header Banner -->
			<div class="rounded-xl border bg-gradient-to-r from-slate-900 to-indigo-950 text-white p-6 shadow-sm">
				<div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
					<div>
						<div class="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-xs font-semibold backdrop-blur-sm mb-2">
							<span class="lucide-activity size-3.5 text-indigo-300"></span>
							{{ __('Audit & Transparency') }}
						</div>
						<h1 class="text-2xl font-bold tracking-tight">
							{{ __('AI Generation History & Usage Logs') }}
						</h1>
						<p class="text-sm text-slate-300 mt-1 max-w-2xl">
							{{ __('Transparent audit trail tracking all AI assessment generations, prompt and completion token consumption, estimated API costs, models used, and execution status.') }}
						</p>
					</div>

					<!-- Metrics Cards -->
					<div class="flex items-center gap-4 text-center">
						<div class="bg-white/10 rounded-lg p-3 backdrop-blur-sm min-w-24">
							<div class="text-2xl font-bold">{{ totalGenerations }}</div>
							<div class="text-[11px] text-slate-300 font-medium">{{ __('Total Generations') }}</div>
						</div>
						<div class="bg-white/10 rounded-lg p-3 backdrop-blur-sm min-w-24">
							<div class="text-2xl font-bold">${{ totalEstimatedCost.toFixed(4) }}</div>
							<div class="text-[11px] text-slate-300 font-medium">{{ __('Est. API Cost') }}</div>
						</div>
					</div>
				</div>
			</div>

			<!-- Logs Table -->
			<div class="rounded-xl border bg-surface-base shadow-sm overflow-hidden">
				<div class="p-4 border-b flex items-center justify-between">
					<h3 class="text-sm font-semibold text-ink-gray-9">{{ __('Recent AI Assessment Logs') }}</h3>
					<span class="text-xs text-ink-gray-5">{{ __('Showing up to 50 latest generation records') }}</span>
				</div>

				<div v-if="loading" class="text-center py-16 text-gray-400">
					{{ __('Loading audit logs...') }}
				</div>

				<div v-else-if="!logsList.length" class="text-center py-16 text-gray-500">
					{{ __('No AI generation history recorded yet.') }}
				</div>

				<div v-else class="overflow-x-auto">
					<table class="w-full text-left text-xs border-collapse">
						<thead>
							<tr class="bg-gray-50/80 dark:bg-gray-800/80 text-ink-gray-7 uppercase tracking-wider text-[11px] border-b">
								<th class="p-3 font-semibold">{{ __('Type') }}</th>
								<th class="p-3 font-semibold">{{ __('Status') }}</th>
								<th class="p-3 font-semibold">{{ __('Model') }}</th>
								<th class="p-3 font-semibold">{{ __('Mode') }}</th>
								<th class="p-3 font-semibold">{{ __('Tokens (P / C / Tot)') }}</th>
								<th class="p-3 font-semibold">{{ __('Est. Cost') }}</th>
								<th class="p-3 font-semibold">{{ __('User') }}</th>
								<th class="p-3 font-semibold">{{ __('Timestamp') }}</th>
							</tr>
						</thead>
						<tbody class="divide-y divide-gray-100 dark:divide-gray-800">
							<tr
								v-for="log in logsList"
								:key="log.name"
								class="hover:bg-gray-50/50 dark:hover:bg-gray-800/50 transition-colors"
							>
								<td class="p-3 font-bold text-violet-700">
									{{ log.generation_type }}
								</td>
								<td class="p-3">
									<Badge
										:theme="log.status === 'Success' ? 'green' : 'red'"
										variant="subtle"
										size="sm"
									>
										{{ log.status }}
									</Badge>
								</td>
								<td class="p-3 font-mono text-[11px] text-ink-gray-8">
									{{ log.model }}
								</td>
								<td class="p-3">
									<Badge
										:theme="log.mode === 'Extended Knowledge' ? 'amber' : 'blue'"
										variant="subtle"
										size="sm"
									>
										{{ log.mode }}
									</Badge>
								</td>
								<td class="p-3 text-ink-gray-7 font-mono">
									{{ log.prompt_tokens }} / {{ log.completion_tokens }} / <strong>{{ log.total_tokens }}</strong>
								</td>
								<td class="p-3 font-mono text-emerald-700 font-bold">
									${{ Number(log.estimated_cost || 0).toFixed(4) }}
								</td>
								<td class="p-3 text-ink-gray-6">
									{{ log.user }}
								</td>
								<td class="p-3 text-ink-gray-5">
									{{ log.creation }}
								</td>
							</tr>
						</tbody>
					</table>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import PageHeader from '@/components/Layouts/PageHeader.vue'
import { Button, Badge, call, toast } from 'frappe-ui'

const loading = ref(false)
const logsList = ref([])
const totalGenerations = ref(0)

const totalEstimatedCost = computed(() => {
	return logsList.value.reduce((sum, l) => sum + (Number(l.estimated_cost) || 0), 0)
})

onMounted(() => {
	loadHistory()
})

async function loadHistory() {
	loading.value = true
	try {
		const res = await call('lms.lms.ai.ai_assessment_api.api_get_generation_history', {
			limit: 50,
			start: 0,
		})
		if (res) {
			logsList.value = res.logs || []
			totalGenerations.value = res.total || 0
		}
	} catch (e) {
		toast.error(__('Failed to load generation history.'))
	} finally {
		loading.value = false
	}
}
</script>

