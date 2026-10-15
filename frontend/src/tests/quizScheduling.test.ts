import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import Quiz from '@/components/Quiz.vue'

const QUIZ_URL = 'lms.lms.utils.get_quiz_with_questions'
const SUBMIT_URL = 'lms.lms.doctype.lms_quiz.lms_quiz.submit_quiz'
const ATTEMPTS_URL = 'frappe.client.get_list'

const submitSpy = vi.fn()
const callSpy = vi.fn()

const question = (name: string) => ({
	name,
	question: `What is ${name}?`,
	type: 'Choices',
	multiple: 0,
	option_1: 'a',
	option_2: 'b',
	is_correct_1: 1,
	is_correct_2: 0,
})

let mockQuizData: any = null

vi.mock('frappe-ui', async () => {
	const { reactive } = await import('vue')

	const createResource = (options: any) => {
		const resource: any = reactive({
			data: null,
			loading: false,
			reload: async () => {
				if (options.url !== QUIZ_URL) return resource.data
				await Promise.resolve()
				const raw = structuredClone(mockQuizData)
				const transformed = options.transform?.(raw)
				resource.data = transformed === undefined ? raw : transformed
				options.onSuccess?.(raw)
				return resource.data
			},
			submit: (values: any, handlers: any) => {
				submitSpy(options.url, values)
				handlers?.onSuccess?.({})
			},
			reset: () => {
				resource.data = null
			},
		})
		resource.fetch = resource.reload
		if (options.auto) void resource.reload()
		return resource
	}

	const passthrough = { template: '<div><slot /></div>' }
	return {
		createResource,
		call: (...args: any[]) => callSpy(...args),
		toast: { warning: vi.fn(), error: vi.fn(), success: vi.fn(), info: vi.fn() },
		Button: {
			emits: ['click'],
			template: `<button @click="$emit('click')"><slot /></button>`,
		},
		Badge: { props: ['label', 'theme'], template: '<span class="badge">{{ label }}</span>' },
		Checkbox: passthrough,
		Dialog: { props: ['open'], template: '<div v-if="open"><slot /></div>' },
		FormControl: passthrough,
		ListView: passthrough,
		LoadingIndicator: passthrough,
		TextEditor: passthrough,
	}
})

vi.mock('@/components/ProgressBar.vue', () => ({
	default: { template: '<div />' },
}))
vi.mock('@/components/ResponsiveListView.vue', () => ({
	default: { template: '<div><slot /></div>' },
}))
vi.mock('@/components/RichTextEditor.vue', () => ({
	default: { template: '<div />' },
}))
vi.mock('@/utils/sanitizeRichHTML', () => ({
	sanitizeRichHTML: (v: string) => v,
}))
vi.mock('@/utils/format', () => ({ timeAgo: (v: string) => v }))

vi.stubGlobal('__', (v: string) => v)
String.prototype.format = function (...args: unknown[]) {
	return this.replace(/\{(\d+)\}/g, (_: string, i: number) => String(args[i]))
}

const mountQuiz = (quizName: string) =>
	mount(Quiz, {
		props: { quizName },
		global: {
			provide: { $user: { data: { name: 'student@example.com' } } },
			mocks: { __: (s: string) => s },
			stubs: { teleport: true },
		},
	})

describe('Quiz.vue Scheduling & Attempt Recovery', () => {
	beforeEach(() => {
		submitSpy.mockClear()
		callSpy.mockClear()
		localStorage.clear()
		vi.useFakeTimers()
	})

	afterEach(() => {
		vi.useRealTimers()
	})

	it('renders upcoming scheduled quiz with banner and without Start button', async () => {
		mockQuizData = {
			quiz: {
				name: 'sched-upcoming',
				title: 'Upcoming Quiz',
				duration: 30,
				enable_quiz_scheduling: 1,
				quiz_start_date: '2026-10-15',
				quiz_start_time: '10:00:00',
				quiz_end_date: '2026-10-16',
				quiz_end_time: '18:00:00',
				show_answers: 0,
				max_attempts: 0,
				questions: [{ question: 'q1' }],
			},
			questions_by_name: { q1: question('q1') },
			schedule_info: {
				is_scheduled: true,
				status: 'upcoming',
				is_available: false,
				can_start: false,
				message: 'Quiz has not started yet.',
				start_datetime: '2026-10-15 10:00:00',
				end_datetime: '2026-10-16 18:00:00',
				duration: 30,
				timezone: 'UTC',
			},
		}

		const wrapper = mountQuiz('sched-upcoming')
		await flushPromises()

		expect(wrapper.text()).toContain('Upcoming')
		expect(wrapper.text()).toContain('Quiz has not started yet')
		expect(wrapper.find('button').exists()).toBe(false)
		wrapper.unmount()
	})

	it('renders expired scheduled quiz with expired message and without Start button', async () => {
		mockQuizData = {
			quiz: {
				name: 'sched-expired',
				title: 'Expired Quiz',
				duration: 30,
				enable_quiz_scheduling: 1,
				quiz_start_date: '2026-10-10',
				quiz_start_time: '10:00:00',
				quiz_end_date: '2026-10-11',
				quiz_end_time: '18:00:00',
				show_answers: 0,
				max_attempts: 0,
				questions: [{ question: 'q1' }],
			},
			questions_by_name: { q1: question('q1') },
			schedule_info: {
				is_scheduled: true,
				status: 'expired',
				is_available: false,
				can_start: false,
				message: 'Quiz has expired.',
				start_datetime: '2026-10-10 10:00:00',
				end_datetime: '2026-10-11 18:00:00',
				duration: 30,
				timezone: 'UTC',
			},
		}

		const wrapper = mountQuiz('sched-expired')
		await flushPromises()

		expect(wrapper.text()).toContain('Closed / Expired')
		expect(wrapper.text()).toContain('Quiz has expired')
		expect(wrapper.find('button').exists()).toBe(false)
		wrapper.unmount()
	})

	it('automatically restores in-progress attempt with correct remaining time on reload', async () => {
		mockQuizData = {
			quiz: {
				name: 'sched-active',
				title: 'Active Quiz',
				duration: 30,
				enable_quiz_scheduling: 1,
				quiz_start_date: '2026-10-14',
				quiz_start_time: '08:00:00',
				quiz_end_date: '2026-10-14',
				quiz_end_time: '20:00:00',
				show_answers: 0,
				max_attempts: 0,
				questions: [{ question: 'q1' }],
			},
			questions_by_name: { q1: question('q1') },
			schedule_info: {
				is_scheduled: true,
				status: 'available',
				is_available: true,
				can_start: true,
				start_datetime: '2026-10-14 08:00:00',
				end_datetime: '2026-10-14 20:00:00',
				duration: 30,
				timezone: 'UTC',
				active_attempt: {
					name: 'QUIZ-ATT-001',
					start_time: '2026-10-14 10:00:00',
					deadline: '2026-10-14 10:30:00',
					remaining_seconds: 750, // 12.5 mins left, NOT 30 mins
					saved_answers: JSON.stringify([{ question_name: 'q1', answer: ['a'] }]),
				},
			},
		}

		const wrapper = mountQuiz('sched-active')
		await flushPromises()

		const vm = wrapper.vm as any
		// The active attempt should be restored automatically
		expect(vm.activeAttempt).toBe('QUIZ-ATT-001')
		expect(vm.timer).toBe(750)
		expect(vm.activeQuestion).toBe(1)

		// Timer should be ticking down from 750, NOT resetting to 1800 (30 mins)
		await vi.advanceTimersByTimeAsync(5_000)
		expect(vm.timer).toBe(745)

		wrapper.unmount()
	})
})
