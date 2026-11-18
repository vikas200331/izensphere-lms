import { describe, expect, it, vi, beforeEach } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import AIProviderSettings from '@/pages/AI/AIProviderSettings.vue'

const { callMock, toastMock, mockUser } = vi.hoisted(() => ({
	callMock: vi.fn(),
	toastMock: { success: vi.fn(), error: vi.fn(), info: vi.fn() },
	mockUser: {
		value: {
			name: 'Administrator',
			is_system_manager: true,
		} as any,
	},
}))

vi.mock('frappe-ui', () => ({
	call: callMock,
	toast: toastMock,
	Button: {
		props: ['loading', 'variant', 'theme', 'size'],
		emits: ['click'],
		template: `<button type="button" @click="$emit('click')"><slot name="prefix" /><slot /></button>`,
	},
	Badge: {
		props: ['theme', 'size', 'variant'],
		template: `<span><slot /></span>`,
	},
}))

vi.mock('@/components/Layouts/PageHeader.vue', () => ({
	default: {
		props: ['title'],
		template: `<div><h1>{{ title }}</h1><slot name="actions" /></div>`,
	},
}))

vi.mock('@/stores/user', () => ({
	usersStore: () => ({
		userResource: {
			get data() {
				return mockUser.value
			},
			fetch: vi.fn(async () => mockUser.value),
		},
	}),
}))

const defaultConfigResponse = {
	enable_ai_assessment: 1,
	provider: 'Ollama',
	ollama_base_url: 'http://localhost:11434',
	ollama_model: 'llama3.2',
	openai_model: 'gpt-4o-mini',
	openai_base_url: 'https://api.openai.com/v1',
	has_openai_key: true,
	claude_base_url: 'https://api.anthropic.com',
	claude_model: 'claude-sonnet-4-6',
	claude_max_tokens: 4096,
	claude_temperature: 0.7,
	has_claude_key: false,
	temperature: 0.7,
	max_tokens: 4000,
	school_name: 'Izensphere International School',
	default_mode: 'Chapter-Based',
}

describe('AIProviderSettings.vue', () => {
	beforeEach(() => {
		callMock.mockReset()
		toastMock.success.mockReset()
		toastMock.error.mockReset()
		mockUser.value = { name: 'Administrator', is_system_manager: true }
		;(globalThis as any).__ = (s: string) => s
	})

	it('displays all three providers in dropdown and switches cleanly to Claude AI configuration', async () => {
		callMock.mockResolvedValueOnce(defaultConfigResponse)
		const wrapper = mount(AIProviderSettings, {
			global: { mocks: { __: (s: string) => s } },
		})
		await flushPromises()

		const select = wrapper.find('#ai-provider-select')
		expect(select.exists()).toBe(true)
		const options = select.findAll('option').map((o) => o.attributes('value'))
		expect(options).toEqual(['Ollama', 'OpenAI', 'Claude'])

		// Switch to Claude
		await select.setValue('Claude')
		await flushPromises()

		expect(wrapper.text()).toContain('Claude AI (Anthropic) Configuration')
		expect(wrapper.text()).toContain('Test Claude Connection')
		expect(wrapper.text()).toContain('Claude API Base URL')
		expect(wrapper.text()).toContain('Claude API Key')
		expect(wrapper.text()).toContain('Claude Model Name')
	})

	it('tests Claude connection and saves Claude settings without overwriting other providers', async () => {
		callMock
			.mockResolvedValueOnce(defaultConfigResponse) // initial loadConfig
			.mockResolvedValueOnce({
				success: true,
				provider: 'Claude',
				active_model: 'claude-haiku-4-5',
				models: ['claude-sonnet-4-6', 'claude-haiku-4-5'],
				message: 'Connected to Claude AI (Anthropic) successfully.',
			}) // api_test_ai_connection
			.mockResolvedValueOnce({ success: true }) // api_save_ai_settings
			.mockResolvedValueOnce({
				...defaultConfigResponse,
				provider: 'Claude',
				claude_model: 'claude-haiku-4-5',
				has_claude_key: true,
			}) // reload after save

		const wrapper = mount(AIProviderSettings, {
			global: { mocks: { __: (s: string) => s } },
		})
		await flushPromises()

		await wrapper.find('#ai-provider-select').setValue('Claude')
		await flushPromises()

		// Fill Claude API Key and custom model
		const pwdInput = wrapper.find('input[type="password"]')
		await pwdInput.setValue('sk-ant-api03-test-key')

		const modelInput = wrapper.find('input[placeholder="claude-sonnet-4-6"]')
		await modelInput.setValue('claude-haiku-4-5')

		// Click Test Claude Connection
		const testBtn = wrapper
			.findAll('button')
			.find((b) => b.text().includes('Test Claude Connection'))
		expect(testBtn).toBeTruthy()
		await testBtn!.trigger('click')
		await flushPromises()

		expect(callMock).toHaveBeenCalledWith(
			'lms.lms.ai.ai_assessment_api.api_test_ai_connection',
			expect.objectContaining({
				provider: 'Claude',
				base_url: 'https://api.anthropic.com',
				model: 'claude-haiku-4-5',
				api_key: 'sk-ant-api03-test-key',
			})
		)
		expect(wrapper.text()).toContain('Connected to Claude AI (Anthropic) successfully.')

		// Click Save Settings
		const saveBtn = wrapper
			.findAll('button')
			.find((b) => b.text().includes('Save Settings'))
		expect(saveBtn).toBeTruthy()
		await saveBtn!.trigger('click')
		await flushPromises()

		const saveCall = callMock.mock.calls.find(
			(c) => c[0] === 'lms.lms.ai.ai_assessment_api.api_save_ai_settings'
		)
		expect(saveCall).toBeTruthy()
		const savedPayload = JSON.parse(saveCall![1].settings)
		expect(savedPayload.provider).toBe('Claude')
		expect(savedPayload.claude_model).toBe('claude-haiku-4-5')
		expect(savedPayload.claude_api_key).toBe('sk-ant-api03-test-key')
		expect(savedPayload.ollama_model).toBe('llama3.2')
		expect(savedPayload.openai_model).toBe('gpt-4o-mini')
		expect(savedPayload.openai_api_key).toBeUndefined()
	})

	it('restricts access for non-System Manager users', async () => {
		mockUser.value = { name: 'student@example.com', is_system_manager: false }
		const wrapper = mount(AIProviderSettings, {
			global: { mocks: { __: (s: string) => s } },
		})
		await flushPromises()

		expect(wrapper.text()).toContain('Administrator Access Required')
		expect(callMock).not.toHaveBeenCalled()
	})
})
