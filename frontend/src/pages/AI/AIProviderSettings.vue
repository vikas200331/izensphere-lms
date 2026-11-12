<template>
	<div class="min-h-screen bg-surface-gray-2 pb-16">
		<PageHeader :title="__('AI Provider Settings')">
			<template #actions>
				<Button
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

		<div class="max-w-4xl mx-auto px-4 sm:px-6 pt-6 space-y-6">
			<!-- Header Intro Banner -->
			<div class="rounded-xl border bg-gradient-to-r from-violet-900 to-indigo-900 text-white p-6 shadow-md flex items-start justify-between gap-4">
				<div class="space-y-2">
					<div class="flex items-center gap-2">
						<span class="lucide-sparkles size-5 text-violet-300"></span>
						<h2 class="text-lg font-bold">{{ __('Dual AI Provider Architecture') }}</h2>
					</div>
					<p class="text-xs text-violet-200 leading-relaxed max-w-2xl">
						{{ __('Izensphere LMS supports both free, self-hosted local AI via Ollama and optional OpenAI cloud models. Seamlessly switch providers without altering your course quizzes or examination blueprints.') }}
					</p>
				</div>
				<Badge :theme="form.provider === 'Ollama' ? 'green' : 'blue'" size="lg" variant="subtle" class="shrink-0 bg-white/10 text-white border-white/20">
					{{ form.provider === 'Ollama' ? __('Free Local AI Active') : __('OpenAI Cloud Active') }}
				</Badge>
			</div>

			<!-- Provider Selector Card -->
			<div class="rounded-xl border bg-surface-base p-6 shadow-sm space-y-4">
				<div class="flex items-center justify-between border-b pb-3">
					<div>
						<h3 class="text-sm font-bold text-ink-gray-9">{{ __('Active AI Provider') }}</h3>
						<p class="text-xs text-ink-gray-6 mt-0.5">{{ __('Select which engine powers quiz and question paper generation.') }}</p>
					</div>
					<label class="flex items-center gap-2 cursor-pointer text-xs font-semibold text-ink-gray-8">
						<input type="checkbox" v-model="form.enable_ai_assessment" :true-value="1" :false-value="0" class="text-violet-600 rounded" />
						<span>{{ __('Enable AI Assessment System') }}</span>
					</label>
				</div>

				<div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
					<!-- Ollama Card -->
					<div
						class="rounded-xl border-2 p-5 cursor-pointer transition-all space-y-3"
						:class="form.provider === 'Ollama' ? 'border-emerald-600 bg-emerald-50/40 dark:bg-emerald-950/20 shadow-sm' : 'border-gray-200 hover:border-gray-300'"
						@click="form.provider = 'Ollama'"
					>
						<div class="flex items-center justify-between">
							<div class="flex items-center gap-2.5">
								<input type="radio" v-model="form.provider" value="Ollama" class="text-emerald-600" />
								<div class="font-bold text-sm text-ink-gray-9">{{ __('Ollama (Free Local AI)') }}</div>
							</div>
							<Badge theme="green" variant="subtle">{{ __('Zero Cost') }}</Badge>
						</div>
						<p class="text-xs text-ink-gray-6">
							{{ __('Runs entirely on your local machine or server. No paid API tokens or subscription required. Compatible with Llama 3, Qwen 2.5, Mistral, and more.') }}
						</p>
					</div>

					<!-- OpenAI Card -->
					<div
						class="rounded-xl border-2 p-5 cursor-pointer transition-all space-y-3"
						:class="form.provider === 'OpenAI' ? 'border-violet-600 bg-violet-50/40 dark:bg-violet-950/20 shadow-sm' : 'border-gray-200 hover:border-gray-300'"
						@click="form.provider = 'OpenAI'"
					>
						<div class="flex items-center justify-between">
							<div class="flex items-center gap-2.5">
								<input type="radio" v-model="form.provider" value="OpenAI" class="text-violet-600" />
								<div class="font-bold text-sm text-ink-gray-9">{{ __('OpenAI API (Optional)') }}</div>
							</div>
							<Badge theme="violet" variant="subtle">{{ __('Cloud API') }}</Badge>
						</div>
						<p class="text-xs text-ink-gray-6">
							{{ __('Requires a paid OpenAI API key. Connects to GPT-4o-mini, GPT-4o, and reasoning models. Best for cloud deployments without local GPU hardware.') }}
						</p>
					</div>
				</div>
			</div>

			<!-- Provider Specific Configuration -->
			<div class="rounded-xl border bg-surface-base p-6 shadow-sm space-y-5">
				<!-- OLLAMA SETTINGS -->
				<div v-if="form.provider === 'Ollama'" class="space-y-4">
					<div class="flex items-center justify-between border-b pb-2">
						<h3 class="text-sm font-bold text-ink-gray-9 flex items-center gap-2">
							<span class="lucide-server size-4 text-emerald-600"></span>
							{{ __('Ollama Local Server Configuration') }}
						</h3>
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
					<div v-if="testResult" class="rounded-lg p-3.5 text-xs border transition-all" :class="testResult.success ? 'bg-emerald-50 border-emerald-200 text-emerald-900' : 'bg-rose-50 border-rose-200 text-rose-900'">
						<div class="flex items-start gap-2.5">
							<span :class="testResult.success ? 'lucide-check-circle text-emerald-600' : 'lucide-alert-circle text-rose-600'" class="size-4 shrink-0 mt-0.5"></span>
							<div class="space-y-1">
								<div class="font-bold">{{ testResult.message }}</div>
								<div v-if="testResult.models && testResult.models.length" class="flex flex-wrap items-center gap-1.5 pt-1">
									<span class="text-ink-gray-7 font-medium">{{ __('Detected Local Models:') }}</span>
									<span
										v-for="m in testResult.models"
										:key="m"
										class="px-2 py-0.5 rounded bg-white dark:bg-gray-800 border text-[11px] font-mono"
									>
										{{ m }}
									</span>
								</div>
							</div>
						</div>
					</div>
				</div>

				<!-- OPENAI SETTINGS -->
				<div v-if="form.provider === 'OpenAI'" class="space-y-4">
					<div class="flex items-center justify-between border-b pb-2">
						<h3 class="text-sm font-bold text-ink-gray-9 flex items-center gap-2">
							<span class="lucide-cloud size-4 text-violet-600"></span>
							{{ __('OpenAI API Configuration') }}
						</h3>
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

					<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
						<div class="md:col-span-2">
							<label class="block text-xs font-semibold text-ink-gray-7 mb-1">{{ __('OpenAI API Key') }}</label>
							<input
								type="password"
								v-model="form.openai_api_key"
								:placeholder="configData.has_openai_key ? '••••••••••••••••••••••••••••••••' : 'sk-proj-...'"
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
					<div v-if="testResult" class="rounded-lg p-3.5 text-xs border transition-all" :class="testResult.success ? 'bg-emerald-50 border-emerald-200 text-emerald-900' : 'bg-rose-50 border-rose-200 text-rose-900'">
						<div class="flex items-center gap-2">
							<span :class="testResult.success ? 'lucide-check-circle text-emerald-600' : 'lucide-alert-circle text-rose-600'" class="size-4 shrink-0"></span>
							<span class="font-bold">{{ testResult.message }}</span>
						</div>
					</div>
				</div>

				<!-- COMMON PARAMETERS -->
				<div class="border-t pt-4 space-y-4">
					<h3 class="text-xs font-bold text-ink-gray-7 uppercase tracking-wider">{{ __('Generation Parameters') }}</h3>

					<div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
						<div>
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

						<div>
							<label class="block text-xs font-semibold text-ink-gray-7 mb-1">{{ __('Max Tokens') }}</label>
							<input
								type="number"
								v-model.number="form.max_tokens"
								class="w-full rounded-md border border-gray-300 px-3 py-1.5 text-sm dark:bg-gray-800 dark:border-gray-700"
							/>
						</div>

						<div>
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
import { ref, reactive, onMounted } from 'vue'
import PageHeader from '@/components/Layouts/PageHeader.vue'
import { Button, Badge, toast, call } from 'frappe-ui'

const saving = ref(false)
const testingConnection = ref(false)
const testResult = ref(null)
const configData = ref({})

const form = reactive({
	enable_ai_assessment: 1,
	provider: 'Ollama',
	ollama_base_url: 'http://localhost:11434',
	ollama_model: 'llama3.2',
	openai_api_key: '',
	openai_model: 'gpt-4o-mini',
	openai_base_url: 'https://api.openai.com/v1',
	temperature: 0.7,
	max_tokens: 4000,
	school_name: 'Izensphere International School',
	default_mode: 'Chapter-Based',
})

onMounted(async () => {
	await loadConfig()
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
		const res = await call('lms.lms.ai.ai_assessment_api.api_test_ai_connection', {
			provider: targetProvider,
			base_url: targetProvider === 'Ollama' ? form.ollama_base_url : form.openai_base_url,
			model: targetProvider === 'Ollama' ? form.ollama_model : form.openai_model,
			api_key: targetProvider === 'OpenAI' ? (form.openai_api_key || undefined) : undefined,
		})
		testResult.value = res
		if (res?.success) {
			toast.success(res.message)
		} else {
			toast.error(res.message || __('Connection failed.'))
		}
	} catch (e) {
		testResult.value = {
			success: false,
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
			temperature: form.temperature,
			max_tokens: form.max_tokens,
			school_name: form.school_name,
			default_mode: form.default_mode,
		}
		if (form.openai_api_key) {
			payload.openai_api_key = form.openai_api_key
		}

		await call('lms.lms.ai.ai_assessment_api.api_save_ai_settings', {
			settings: JSON.stringify(payload),
		})
		toast.success(__('AI Provider Settings saved successfully.'))
		await loadConfig()
		form.openai_api_key = '' // Clear input
	} catch (e) {
		toast.error(e.message || __('Failed to save AI settings.'))
	} finally {
		saving.value = false
	}
}
</script>

