import { describe, expect, it, vi, beforeEach } from 'vitest'

vi.hoisted(() => {
	window.matchMedia ??= (() => ({
		matches: false,
		addEventListener: () => {},
		removeEventListener: () => {},
	})) as unknown as typeof window.matchMedia
})

import { createPinia, setActivePinia } from 'pinia'
import { routes } from '@/routes'
import { getSidebarLinks } from '@/utils'
import { mount } from '@vue/test-utils'
import PreviousYearAnalysisDashboard from '@/components/AI/PreviousYearAnalysisDashboard.vue'

vi.mock('@/stores/user', () => ({
	usersStore: () => ({
		userResource: {
			data: {
				roles: ['System Manager', 'Administrator'],
				is_moderator: true,
				is_instructor: true,
			},
		},
	}),
}))

vi.mock('@/stores/settings', () => ({
	useSettings: () => ({
		settings: {},
		programs: { data: { enrolled: [], published: [] } },
	}),
}))

describe('PreviousYearPapers Route & Navigation', () => {
	beforeEach(() => {
		setActivePinia(createPinia())
	})

	it('registers the /ai-assessment/previous-year-papers route', () => {
		const route = routes.find((r) => r.path === '/ai-assessment/previous-year-papers')
		expect(route).toBeDefined()
		expect(route?.name).toBe('PreviousYearPapers')
	})

	it('includes Previous Year Papers in the sidebar AI Assessments section', () => {
		const sections = getSidebarLinks()
		const aiSection = sections.find((s: any) => s.label === 'AI Assessments')
		expect(aiSection).toBeDefined()

		const pyqpItem = aiSection?.items.find((item: any) => item.to === 'PreviousYearPapers')
		expect(pyqpItem).toBeDefined()
		expect(pyqpItem?.label).toContain('Previous Year Papers')
	})
})

describe('PreviousYearAnalysisDashboard Component', () => {
	it('renders summary statistics and topic importance table', () => {
		const mockData = {
			total_uploaded_papers: 10,
			total_processed_papers: 10,
			total_extracted_questions: 150,
			total_repeated_questions: 25,
			academic_years_covered: '2015 - 2025',
			status: 'Completed',
			topic_importance: [
				{
					topic: 'Object-Oriented Programming',
					questions_count: 35,
					percentage: 23.3,
					total_marks: 140,
					importance: 'High',
					trend: 'Increasing Frequency',
					years_appeared: ['2016', '2018', '2021', '2024'],
				},
				{
					topic: 'Exception Handling',
					questions_count: 15,
					percentage: 10.0,
					total_marks: 60,
					importance: 'Medium',
					trend: 'Consistent',
					years_appeared: ['2017', '2020', '2023'],
				},
			],
			repeated_questions: [
				{
					canonical_question: 'Explain the concept of Polymorphism with suitable examples.',
					topic: 'Object-Oriented Programming',
					frequency: 4,
					distinct_years_count: 4,
					examination_years: ['2016', '2018', '2021', '2024'],
					marks_typical: 5,
					variations: [
						{ question: 'What is polymorphism?', year: '2016', marks: 5 },
						{ question: 'Explain polymorphism with examples.', year: '2021', marks: 5 },
					],
				},
			],
			year_distribution: [
				{ year: '2016', questions_count: 15, total_marks: 60 },
				{ year: '2024', questions_count: 20, total_marks: 80 },
			],
			marks_distribution: {
				'1 Mark': 30,
				'2 Marks': 20,
				'3-5 Marks': 50,
				'6-10 Marks': 30,
				'11+ Marks': 20,
			},
			difficulty_distribution: {
				Easy: 45,
				Medium: 60,
				Hard: 45,
				Easy_pct: 30,
				Medium_pct: 40,
				Hard_pct: 30,
			},
		}

		const wrapper = mount(PreviousYearAnalysisDashboard, {
			props: {
				analysisData: mockData,
			},
			global: {
				mocks: {
					__: (t: string) => t,
				},
				stubs: {
					Button: {
						template: '<button><slot /></button>',
					},
				},
			},
		})

		const text = wrapper.text()
		expect(text).toContain('150')
		expect(text).toContain('25')
		expect(text).toContain('2015 - 2025')
		expect(text).toContain('Object-Oriented Programming')
		expect(text).toContain('High')
		expect(text).toContain('Polymorphism')
	})
})
