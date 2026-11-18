<template>
	<div class="min-h-screen bg-surface-gray-2 pb-16">
		<PageHeader :title="__('AI Provider Settings')">
			<template #actions>
				<Button
					v-if="isSystemManager"
					variant="solid"
					theme="violet"
					:loading="saving"
					@click="saveSettings"
				>
					<template #prefix>
						<span class="lucide-save size-4"></span>
					</template>
					{{ __('Save Settings') }}
				</Button>
			</template>
		</PageHeader>

		<!-- Access Denied State for Non-Administrators -->
		<div v-if="userLoaded && !isSystemManager" class="max-w-2xl mx-auto px-4 sm:px-6 pt-12">
			<div class="rounded-xl border border-rose-200 bg-rose-50 dark:bg-rose-950/30 dark:border-rose-800 p-6 text-center space-y-3">
				<div class="mx-auto w-12 h-12 rounded-full bg-rose-100 dark:bg-rose-900/50 flex items-center justify-center">
					<span class="lucide-shield-alert size-6 text-rose-600"></span>
				</div>
				<h2 class="text-base font-bold text-rose-900 dark:text-rose-200">{{ __('Administrator Access Required') }}</h2>
				<p class="text-xs text-rose-700 dark:text-rose-300 max-w-md mx-auto">
					{{ __('Only System Managers or authorized administrators can view and configure AI Provider Settings and API credentials.') }}
				</p>
			</div>
		</div>

		<div v-else class="max-w-4xl mx-auto px-4 sm:px-6 pt-6 space-y-6">
			<!-- Header Intro Banner -->
			<div class="rounded-xl border bg-gradient-to-r from-violet-900 to-indigo-900 text-white p-6 shadow-md flex flex-col sm:flex-row sm:items-start justify-between gap-4">
				<div class="space-y-2">
					<div class="flex items-center gap-2">
						<span class="lucide-sparkles size-5 text-violet-300"></span>
						<h2 class="text-lg font-bold">{{ __('Multi-Provider AI Architecture') }}</h2>
					</div>
					<p class="text-xs text-violet-200 leading-relaxed max-w-2xl">
						{{ __('Izensphere LMS supports local AI via Ollama, OpenAI Cloud AI, and Claude AI (Anthropic). Seamlessly switch providers to power AI Quiz Generation, Question Papers, Question Bank, and AI Learning & Practice without altering your course data.') }}
					</p>
				</div>
				<Badge
					:theme="activeProviderBadgeTheme"
					size="lg"
					variant="subtle"
					class="shrink-0 bg-white/10 text-white border-white/20"
				>
					{{ activeProviderBadgeLabel }}
				</Badge>
			</div>

			<!-- Provider Selector Card -->
			<div class="rounded-xl border bg-surface-base p-6 shadow-sm space-y-4">
				<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b pb-3">
					<div>
						<h3 class="text-sm font-bold text-ink-gray-9">{{ __('Active AI Provider') }}</h3>
						<p class="text-xs text-ink-gray-6 mt-0.5">{{ __('Select which AI engine powers quizzes, question papers, question bank, and student practice.') }}</p>
					</div>
					<label class="flex items-center gap-2 cursor-pointer text-xs font-semibold text-ink-gray-8 shrink-0">
						<input type="checkbox" v-model="form.enable_ai_assessment" :true-value="1" :false-value="0" class="text-violet-600 rounded" />
						<span>{{ __('Enable AI Assessment System') }}</span>
					</label>
				</div>

				<!-- Explicit Provider Dropdown -->
				<div class="max-w-md">
					<label for="ai-provider-select" class="block text-xs font-semibold text-ink-gray-7 mb-1.5">
						{{ __('AI Provider') }} *
					</label>
					<select
						id="ai-provider-select"
						v-model="form.provider"
						class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm font-medium shadow-sm focus:border-violet-500 dark:bg-gray-800 dark:border-gray-700"
					>
						<option value="Ollama">{{ __('Ollama – Free Local AI') }}</option>
						<option value="OpenAI">{{ __('OpenAI – Cloud AI') }}</option>
						<option value="Claude">{{ __('Claude – Anthropic Cloud AI') }}</option>
					</select>
					<p class="text-[11px] text-ink-gray-5 mt-1">
						{{ __('Switching providers preserves all saved configurations for other providers.') }}
					</p>
				</div>

				<!-- 3-Provider Quick Selection Cards -->
				<div class="grid grid-cols-1 md:grid-cols-3 gap-4 pt-1">
					<!-- Ollama Card -->
					<div
						class="rounded-xl border-2 p-4 cursor-pointer transition-all space-y-2.5"
						:class="form.provider === 'Ollama' ? 'border-emerald-600 bg-emerald-50/40 dark:bg-emerald-950/20 shadow-sm' : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'"
						@click="form.provider = 'Ollama'"
					>
						<div class="flex items-center justify-between gap-2">
							<div class="flex items-center gap-2">
								<input type="radio" v-model="form.provider" value="Ollama" class="text-emerald-600" />
								<div class="font-bold text-sm text-ink-gray-9">{{ __('Ollama') }}</div>
							</div>
							<Badge theme="green" variant="subtle">{{ __('Free Local AI') }}</Badge>
						</div>
						<p class="text-xs text-ink-gray-6 leading-relaxed">
							{{ __('Runs locally on your server with zero API cost. Supports Llama 3.2, Qwen 2.5, Mistral, and more.') }}
						</p>
					</div>

					<!-- OpenAI Card -->
					<div
						class="rounded-xl border-2 p-4 cursor-pointer transition-all space-y-2.5"
						:class="form.provider === 'OpenAI' ? 'border-violet-600 bg-violet-50/40 dark:bg-violet-950/20 shadow-sm' : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'"
						@click="form.provider = 'OpenAI'"
					>
						<div class="flex items-center justify-between gap-2">
							<div class="flex items-center gap-2">
								<input type="radio" v-model="form.provider" value="OpenAI" class="text-violet-600" />
								<div class="font-bold text-sm text-ink-gray-9">{{ __('OpenAI') }}</div>
							</div>
							<Badge theme="violet" variant="subtle">{{ __('Cloud AI') }}</Badge>
						</div>
						<p class="text-xs text-ink-gray-6 leading-relaxed">
							{{ __('Connects to OpenAI cloud models such as GPT-4o-mini, GPT-4o, and o3-mini using your OpenAI API key.') }}
						</p>
					</div>

					<!-- Claude Card -->
					<div
						class="rounded-xl border-2 p-4 cursor-pointer transition-all space-y-2.5"
						:class="form.provider === 'Claude' ? 'border-amber-600 bg-amber-50/40 dark:bg-amber-950/20 shadow-sm' : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'"
						@click="form.provider = 'Claude'"
					>
						<div class="flex items-center justify-between gap-2">
							<div class="flex items-center gap-2">
								<input type="radio" v-model="form.provider" value="Claude" class="text-amber-600" />
								<div class="font-bold text-sm text-ink-gray-9">{{ __('Claude AI') }}</div>
							</div>
							<Badge theme="orange" variant="subtle">{{ __('Anthropic Cloud AI') }}</Badge>
						</div>
						<p class="text-xs text-ink-gray-6 leading-relaxed">
							{{ __('Powered by Anthropic Messages API. Supports Claude Sonnet, Claude Haiku, and Claude Opus models.') }}
						</p>
					</div>
				</div>
			</div>

			<!-- Provider Specific Configuration -->
			<div class="rounded-xl border bg-surface-base p-6 shadow-sm space-y-5">
				<!-- OLLAMA SETTINGS -->
				<div v-if="form.provider === 'Ollama'" class="space-y-4">
					<div class="flex flex-wrap items-center justify-between gap-2 border-b pb-2">
						<h3 class="text-sm font-bold text-ink-gray-9 flex items-center gap-2">
							<span class="lucide-server size-4 text-emerald-600"></span>
							{{ __('Ollama Local Server Configuration') }}
						</h3>
						<div class="flex items-center gap-2">
							<Badge v-if="testResult && testResult.provider === 'Ollama'" :theme="testResult.success ? 'green' : 'red'" variant="subtle">
								{{ testResult.success ? __('Connected') : __('Connection Failed') }}
							</Badge>
							<Button
								variant="subtle"
								theme="green"
								size="sm"
								:loading="testingConnection"
								@click="testConnection('Ollama')"
							>
								<template #prefix><span class="lucide-wifi size-3.5"></span></template>
								{{ __('Test Ollama Connection') }}
							</Button>
						</div>
					</div>

					<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
						<div>
							<label class="block text-xs font-semibold text-ink-gray-7 mb-1">{{ __('Ollama Base URL') }} *</label>
							<input
								type="text"
								v-model="form.ollama_base_url"
								placeholder="http://localhost:11434"
								class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-emerald-500 dark:bg-gray-800 dark:border-gray-700"
							/>
							<p class="text-[11px] text-ink-gray-5 mt-1">{{ __('Default local port is 11434.') }}</p>
						</div>

						<div>
							<label class="block text-xs font-semibold text-ink-gray-7 mb-1">{{ __('Model Name') }} *</label>
							<input
								type="text"
								v-model="form.ollama_model"
								placeholder="llama3.2"
								class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-emerald-500 dark:bg-gray-800 dark:border-gray-700"
							/>
							<p class="text-[11px] text-ink-gray-5 mt-1">{{ __('Examples: llama3.2, llama3, qwen2.5, mistral') }}</p>
						</div>
					</div>

					<!-- Connection Test Result Banner -->
					<div v-if="testResult && testResult.provider === 'Ollama'" class="rounded-lg p-3.5 text-xs border transition-all" :class="testResult.success ? 'bg-emerald-50 border-emerald-200 text-emerald-900' : 'bg-rose-50 border-rose-200 text-rose-900'">
						<div class="flex items-start gap-2.5">
							<span :class="testResult.success ? 'lucide-check-circle text-emerald-600' : 'lucide-alert-circle text-rose-600'" class="size-4 shrink-0 mt-0.5"></span>
							<div class="space-y-1">
								<div class="font-bold">{{ testResult.message }}</div>
								<div v-if="testResult.models && testResult.models.length" class="flex flex-wrap items-center gap-1.5 pt-1">
									<span class="text-ink-gray-7 font-medium">{{ __('Detected Local Models:') }}</span>
									<button
										v-for="m in testResult.models"
										:key="m"
										type="button"
										class="px-2 py-0.5 rounded bg-white dark:bg-gray-800 border text-[11px] font-mono hover:border-emerald-500"
										@click="form.ollama_model = m"
									>
										{{ m }}
									</button>
								</div>
							</div>
						</div>
					</div>
				</div>

				<!-- OPENAI SETTINGS -->
				<div v-if="form.provider === 'OpenAI'" class="space-y-4">
					<div class="flex flex-wrap items-center justify-between gap-2 border-b pb-2">
						<h3 class="text-sm font-bold text-ink-gray-9 flex items-center gap-2">
							<span class="lucide-cloud size-4 text-violet-600"></span>
							{{ __('OpenAI API Configuration') }}
						</h3>
						<div class="flex items-center gap-2">
							<Badge v-if="testResult && testResult.provider === 'OpenAI'" :theme="testResult.success ? 'green' : 'red'" variant="subtle">
								{{ testResult.success ? __('Connected') : __('Connection Failed') }}
							</Badge>
							<Button
								variant="subtle"
								theme="violet"
								size="sm"
								:loading="testingConnection"
								@click="testConnection('OpenAI')"
							>
								<template #prefix><span class="lucide-wifi size-3.5"></span></template>
								{{ __('Test OpenAI Connection') }}
							</Button>
						</div>
					</div>

					<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
						<div class="md:col-span-2">
							<div class="flex items-center justify-between mb-1">
								<label class="block text-xs font-semibold text-ink-gray-7">{{ __('OpenAI API Key') }}</label>
								<Badge v-if="configData.has_openai_key" theme="green" variant="subtle" size="sm">
									{{ __('API Key Configured') }}
								</Badge>
							</div>
							<input
								type="password"
								v-model="form.openai_api_key"
								autocomplete="new-password"
								:placeholder="configData.has_openai_key ? '•••••••••••••••••••••••••••••••• (leave blank to keep saved key)' : 'sk-proj-...'"
								class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-violet-500 dark:bg-gray-800 dark:border-gray-700 font-mono"
							/>
							<p class="text-[11px] text-ink-gray-5 mt-1">{{ __('Stored encrypted on backend. Never sent to the client browser.') }}</p>
						</div>

						<div>
							<label class="block text-xs font-semibold text-ink-gray-7 mb-1">{{ __('Model Name') }}</label>
							<select
								v-model="form.openai_model"
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-violet-500 dark:bg-gray-800 dark:border-gray-700"
							>
								<option value="gpt-4o-mini">gpt-4o-mini (Recommended - Fast & Cost-Effective)</option>
								<option value="gpt-4o">gpt-4o (High Accuracy & Complexity)</option>
								<option value="gpt-4-turbo">gpt-4-turbo</option>
								<option value="o3-mini">o3-mini (Reasoning Model)</option>
								<option value="o1">o1 (Full Reasoning)</option>
							</select>
						</div>

						<div>
							<label class="block text-xs font-semibold text-ink-gray-7 mb-1">{{ __('API Base URL') }}</label>
							<input
								type="text"
								v-model="form.openai_base_url"
								placeholder="https://api.openai.com/v1"
								class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-violet-500 dark:bg-gray-800 dark:border-gray-700"
							/>
						</div>
					</div>

					<!-- OpenAI Test Result -->
					<div v-if="testResult && testResult.provider === 'OpenAI'" class="rounded-lg p-3.5 text-xs border transition-all" :class="testResult.success ? 'bg-emerald-50 border-emerald-200 text-emerald-900' : 'bg-rose-50 border-rose-200 text-rose-900'">
						<div class="flex items-center gap-2">
							<span :class="testResult.success ? 'lucide-check-circle text-emerald-600' : 'lucide-alert-circle text-rose-600'" class="size-4 shrink-0"></span>
							<span class="font-bold">{{ testResult.message }}</span>
						</div>
					</div>
				</div>

				<!-- CLAUDE AI (ANTHROPIC) SETTINGS -->
				<div v-if="form.provider === 'Claude'" class="space-y-4">
					<div class="flex flex-wrap items-center justify-between gap-2 border-b pb-2">
						<h3 class="text-sm font-bold text-ink-gray-9 flex items-center gap-2">
							<span class="lucide-sparkles size-4 text-amber-600"></span>
							{{ __('Claude AI (Anthropic) Configuration') }}
						</h3>
						<div class="flex items-center gap-2">
							<Badge v-if="testResult && testResult.provider === 'Claude'" :theme="testResult.success ? 'green' : 'red'" variant="subtle">
								{{ testResult.success ? __('Connected') : __('Connection Failed') }}
							</Badge>
							<Button
								variant="subtle"
								theme="orange"
								size="sm"
								:loading="testingConnection"
								@click="testConnection('Claude')"
							>
								<template #prefix><span class="lucide-wifi size-3.5"></span></template>
								{{ __('Test Claude Connection') }}
							</Button>
						</div>
					</div>

					<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
						<div class="md:col-span-2">
							<div class="flex items-center justify-between mb-1">
								<label class="block text-xs font-semibold text-ink-gray-7">{{ __('Claude API Key') }} *</label>
								<Badge v-if="configData.has_claude_key" theme="green" variant="subtle" size="sm">
									{{ __('API Key Configured') }}
								</Badge>
							</div>
							<input
								type="password"
								v-model="form.claude_api_key"
								autocomplete="new-password"
								:placeholder="configData.has_claude_key ? '•••••••••••••••••••••••••••••••• (leave blank to keep saved key)' : 'sk-ant-api03-...'"
								class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-amber-500 dark:bg-gray-800 dark:border-gray-700 font-mono"
							/>
							<p class="text-[11px] text-ink-gray-5 mt-1">{{ __('Stored securely using Frappe server-side password encryption. Never exposed to the browser, students, or logs.') }}</p>
						</div>

						<div>
							<label class="block text-xs font-semibold text-ink-gray-7 mb-1">{{ __('Claude API Base URL') }}</label>
							<input
								type="text"
								v-model="form.claude_base_url"
								placeholder="https://api.anthropic.com"
								class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-amber-500 dark:bg-gray-800 dark:border-gray-700"
							/>
							<p class="text-[11px] text-ink-gray-5 mt-1">{{ __('Default: https://api.anthropic.com (uses official /v1/messages endpoint).') }}</p>
						</div>

						<div>
							<label class="block text-xs font-semibold text-ink-gray-7 mb-1">{{ __('Quick Select Claude Model') }}</label>
							<select
								:value="selectedClaudePreset"
								@change="onSelectClaudePreset($event.target.value)"
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-amber-500 dark:bg-gray-800 dark:border-gray-700"
							>
								<option v-for="opt in claudeModelOptions" :key="opt.id" :value="opt.id">
									{{ opt.label }}
								</option>
								<option value="__custom__">{{ __('Custom Model ID (enter below)') }}</option>
							</select>
						</div>

						<div class="md:col-span-2">
							<label class="block text-xs font-semibold text-ink-gray-7 mb-1">{{ __('Claude Model Name (Model ID)') }} *</label>
							<input
								type="text"
								v-model="form.claude_model"
								placeholder="claude-sonnet-4-6"
								class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm font-mono shadow-sm focus:border-amber-500 dark:bg-gray-800 dark:border-gray-700"
							/>
							<p class="text-[11px] text-ink-gray-5 mt-1">{{ __('Select a preset above or enter any valid Anthropic model ID (e.g. claude-sonnet-4-6, claude-haiku-4-5, claude-opus-4-6).') }}</p>
						</div>

						<div>
							<label class="block text-xs font-semibold text-ink-gray-7 mb-1">{{ __('Max Tokens') }}</label>
							<input
								type="number"
								min="64"
								max="64000"
								v-model.number="form.claude_max_tokens"
								class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-amber-500 dark:bg-gray-800 dark:border-gray-700"
							/>
							<p class="text-[11px] text-ink-gray-5 mt-1">{{ __('Maximum output tokens per Claude generation request (e.g. 4096).') }}</p>
						</div>

						<div>
							<label class="block text-xs font-semibold text-ink-gray-7 mb-1">{{ __('Temperature') }} ({{ form.claude_temperature }})</label>
							<input
								type="range"
								min="0.0"
								max="1.0"
								step="0.05"
								v-model.number="form.claude_temperature"
								class="w-full text-amber-600 mt-2"
							/>
							<div class="flex justify-between text-[10px] text-ink-gray-5 mt-0.5">
								<span>0.0 (Deterministic)</span>
								<span>0.7 (Balanced)</span>
								<span>1.0 (Creative)</span>
							</div>
						</div>
					</div>

					<!-- Claude Connection Test Result Banner -->
					<div v-if="testResult && testResult.provider === 'Claude'" class="rounded-lg p-3.5 text-xs border transition-all" :class="testResult.success ? 'bg-emerald-50 border-emerald-200 text-emerald-900' : 'bg-rose-50 border-rose-200 text-rose-900'">
						<div class="flex items-start gap-2.5">
							<span :class="testResult.success ? 'lucide-check-circle text-emerald-600' : 'lucide-alert-circle text-rose-600'" class="size-4 shrink-0 mt-0.5"></span>
							<div class="space-y-1.5">
								<div class="font-bold">{{ testResult.message }}</div>
								<div v-if="testResult.models && testResult.models.length" class="flex flex-wrap items-center gap-1.5 pt-1">
									<span class="text-ink-gray-7 font-medium">{{ __('Available Anthropic Models:') }}</span>
									<button
										v-for="m in testResult.models.slice(0, 12)"
										:key="m"
										type="button"
										class="px-2 py-0.5 rounded bg-white dark:bg-gray-800 border text-[11px] font-mono hover:border-amber-500"
										@click="form.claude_model = m"
									>
										{{ m }}
									</button>
								</div>
							</div>
						</div>
					</div>
				</div>

				<!-- COMMON PARAMETERS -->
				<div class="border-t pt-4 space-y-4">
					<h3 class="text-xs font-bold text-ink-gray-7 uppercase tracking-wider">
						{{ form.provider === 'Claude' ? __('Assessment & Institution Defaults') : __('Generation Parameters') }}
					</h3>

					<div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
						<div v-if="form.provider !== 'Claude'">
							<label class="block text-xs font-semibold text-ink-gray-7 mb-1">{{ __('Temperature') }} ({{ form.temperature }})</label>
							<input
								type="range"
								min="0.1"
								max="1.0"
								step="0.05"
								v-model.number="form.temperature"
								class="w-full text-violet-600"
							/>
							<div class="flex justify-between text-[10px] text-ink-gray-5 mt-0.5">
								<span>0.1 (Strict Fact)</span>
								<span>0.7 (Balanced)</span>
								<span>1.0 (Creative)</span>
							</div>
						</div>

						<div v-if="form.provider !== 'Claude'">
							<label class="block text-xs font-semibold text-ink-gray-7 mb-1">{{ __('Max Tokens') }}</label>
							<input
								type="number"
								v-model.number="form.max_tokens"
								class="w-full rounded-md border border-gray-300 px-3 py-1.5 text-sm dark:bg-gray-800 dark:border-gray-700"
							/>
						</div>

						<div :class="form.provider === 'Claude' ? 'sm:col-span-3 md:col-span-1' : ''">
							<label class="block text-xs font-semibold text-ink-gray-7 mb-1">{{ __('Default Generation Mode') }}</label>
							<select
								v-model="form.default_mode"
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm dark:bg-gray-800 dark:border-gray-700"
							>
								<option value="Chapter-Based">{{ __('Mode 1: Chapter-Based (Strict)') }}</option>
								<option value="Extended Knowledge">{{ __('Mode 2: Extended Knowledge') }}</option>
							</select>
						</div>
					</div>

					<div class="pt-2">
						<label class="block text-xs font-semibold text-ink-gray-7 mb-1">{{ __('School / Institution Heading (for PDF headers)') }}</label>
						<input
							type="text"
							v-model="form.school_name"
							placeholder="Izensphere International School"
							class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm dark:bg-gray-800 dark:border-gray-700"
						/>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import PageHeader from '@/components/Layouts/PageHeader.vue'
import { Button, Badge, toast, call } from 'frappe-ui'
import { usersStore } from '@/stores/user'

const { userResource } = usersStore()

const userLoaded = computed(() => Boolean(userResource?.data))
const isSystemManager = computed(() => {
	const u = userResource?.data
	if (!u) return false
	return Boolean(u.is_system_manager || u.name === 'Administrator')
})

const saving = ref(false)
const testingConnection = ref(false)
const testResult = ref(null)
const configData = ref({})

const defaultClaudeModels = [
	{ id: 'claude-sonnet-4-6', label: 'Claude Sonnet 4.6 (Recommended - Balanced)' },
	{ id: 'claude-haiku-4-5', label: 'Claude Haiku 4.5 (Fast & Cost-Effective)' },
	{ id: 'claude-opus-4-6', label: 'Claude Opus 4.6 (Most Capable)' },
	{ id: 'claude-sonnet-4-5-20250929', label: 'Claude Sonnet 4.5 (2025-09-29)' },
	{ id: 'claude-haiku-4-5-20251001', label: 'Claude Haiku 4.5 (2025-10-01)' },
]

const claudeModelOptions = computed(() => {
	return configData.value?.claude_model_options?.length
		? configData.value.claude_model_options
		: defaultClaudeModels
})

const form = reactive({
	enable_ai_assessment: 1,
	provider: 'Ollama',
	ollama_base_url: 'http://localhost:11434',
	ollama_model: 'llama3.2',
	openai_api_key: '',
	openai_model: 'gpt-4o-mini',
	openai_base_url: 'https://api.openai.com/v1',
	claude_base_url: 'https://api.anthropic.com',
	claude_api_key: '',
	claude_model: 'claude-sonnet-4-6',
	claude_max_tokens: 4096,
	claude_temperature: 0.7,
	temperature: 0.7,
	max_tokens: 4000,
	school_name: 'Izensphere International School',
	default_mode: 'Chapter-Based',
})

const selectedClaudePreset = computed(() => {
	const found = claudeModelOptions.value.find((opt) => opt.id === form.claude_model)
	return found ? found.id : '__custom__'
})

function onSelectClaudePreset(val) {
	if (val && val !== '__custom__') {
		form.claude_model = val
	}
}

const activeProviderBadgeTheme = computed(() => {
	if (form.provider === 'Ollama') return 'green'
	if (form.provider === 'Claude') return 'orange'
	return 'blue'
})

const activeProviderBadgeLabel = computed(() => {
	if (form.provider === 'Ollama') return __('Ollama – Free Local AI Active')
	if (form.provider === 'Claude') return __('Claude – Anthropic Cloud Active')
	return __('OpenAI – Cloud AI Active')
})

// Clear stale test results when switching providers (does not alter any provider config)
watch(
	() => form.provider,
	(newProvider) => {
		if (testResult.value && testResult.value.provider !== newProvider) {
			testResult.value = null
		}
	}
)

onMounted(async () => {
	if (!userResource.data) {
		try {
			await userResource.fetch()
		} catch (e) {
			// Handled by backend permission check
		}
	}
	if (isSystemManager.value) {
		await loadConfig()
	}
})

async function loadConfig() {
	try {
		const res = await call('lms.lms.ai.ai_assessment_api.api_get_ai_config')
		if (res) {
			configData.value = res
			form.enable_ai_assessment = res.enable_ai_assessment ?? 1
			form.provider = res.provider || 'Ollama'
			form.ollama_base_url = res.ollama_base_url || 'http://localhost:11434'
			form.ollama_model = res.ollama_model || 'llama3.2'
			form.openai_model = res.openai_model || 'gpt-4o-mini'
			form.openai_base_url = res.openai_base_url || 'https://api.openai.com/v1'
			form.claude_base_url = res.claude_base_url || 'https://api.anthropic.com'
			form.claude_model = res.claude_model || 'claude-sonnet-4-6'
			form.claude_max_tokens = res.claude_max_tokens ?? 4096
			form.claude_temperature = res.claude_temperature ?? 0.7
			form.temperature = res.temperature ?? 0.7
			form.max_tokens = res.max_tokens ?? 4000
			form.school_name = res.school_name || 'Izensphere International School'
			form.default_mode = res.default_mode || 'Chapter-Based'
		}
	} catch (e) {
		console.error('Failed to load AI config:', e)
	}
}

async function testConnection(targetProvider) {
	testingConnection.value = true
	testResult.value = null
	try {
		let baseUrl
		let model
		let apiKey

		if (targetProvider === 'Ollama') {
			baseUrl = form.ollama_base_url
			model = form.ollama_model
		} else if (targetProvider === 'OpenAI') {
			baseUrl = form.openai_base_url
			model = form.openai_model
			apiKey = form.openai_api_key || undefined
		} else if (targetProvider === 'Claude') {
			baseUrl = form.claude_base_url
			model = form.claude_model
			apiKey = form.claude_api_key || undefined
		}

		const res = await call('lms.lms.ai.ai_assessment_api.api_test_ai_connection', {
			provider: targetProvider,
			base_url: baseUrl,
			model: model,
			api_key: apiKey,
		})
		testResult.value = res
		if (res?.success) {
			toast.success(res.message)
		} else {
			toast.error(res?.message || __('Connection failed.'))
		}
	} catch (e) {
		testResult.value = {
			success: false,
			provider: targetProvider,
			message: String(e.message || e),
		}
		toast.error(testResult.value.message)
	} finally {
		testingConnection.value = false
	}
}

async function saveSettings() {
	saving.value = true
	try {
		const payload = {
			enable_ai_assessment: form.enable_ai_assessment,
			provider: form.provider,
			ollama_base_url: form.ollama_base_url,
			ollama_model: form.ollama_model,
			openai_model: form.openai_model,
			openai_base_url: form.openai_base_url,
			claude_base_url: form.claude_base_url,
			claude_model: form.claude_model,
			claude_max_tokens: form.claude_max_tokens,
			claude_temperature: form.claude_temperature,
			temperature: form.temperature,
			max_tokens: form.max_tokens,
			school_name: form.school_name,
			default_mode: form.default_mode,
		}
		if (form.openai_api_key) {
			payload.openai_api_key = form.openai_api_key
		}
		if (form.claude_api_key) {
			payload.claude_api_key = form.claude_api_key
		}

		await call('lms.lms.ai.ai_assessment_api.api_save_ai_settings', {
			settings: JSON.stringify(payload),
		})
		toast.success(__('AI Provider Settings saved successfully.'))
		await loadConfig()
		form.openai_api_key = '' // Clear password inputs after saving
		form.claude_api_key = ''
	} catch (e) {
		toast.error(e.message || __('Failed to save AI settings.'))
	} finally {
		saving.value = false
	}
}
</script>
