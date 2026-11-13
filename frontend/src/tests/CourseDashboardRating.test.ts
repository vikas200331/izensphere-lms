/**
 * CourseDashboard.vue: Average Rating metric display.
 *
 * Guards:
 * 1. Average Rating formats the numeric rating using formatRating().
 * 2. Average Rating falls back to '0' when rating is absent or 0.
 * 3. Shows rating_count in the suffix when present.
 */
import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'

vi.hoisted(() => {
	window.matchMedia ??= (() => ({
		matches: false,
		addListener: () => {},
		removeListener: () => {},
		addEventListener: () => {},
		removeEventListener: () => {},
		dispatchEvent: () => false,
	})) as unknown as typeof window.matchMedia
})

import CourseDashboard from '@/pages/Courses/CourseDashboard.vue'

vi.mock('frappe-ui', () => ({
	createResource: () => ({ data: null, reload: vi.fn(), loading: false }),
	createListResource: () => ({ data: [], reload: vi.fn(), loading: false }),
	Avatar: { template: '<div />' },
	Button: { template: '<button><slot /></button>' },
	ECharts: { template: '<div />' },
	FormControl: { template: '<input />' },
	Tooltip: { template: '<div><slot /></div>' },
}))

vi.mock('@/components/Controls/Select.vue', () => ({
	default: { template: '<div />' },
}))
vi.mock('@/components/Layouts/EmptyStateLayout.vue', () => ({
	default: { template: '<div />' },
}))
vi.mock('@/components/ProgressBar.vue', () => ({
	default: { template: '<div />' },
}))
vi.mock('@/components/ResponsiveListView.vue', () => ({
	default: { template: '<div />' },
}))
vi.mock('@/pages/Courses/StudentCourseProgress.vue', () => ({
	default: { template: '<div />' },
}))

vi.stubGlobal('__', (s: string) => s)

const mountDashboard = (courseData: Record<string, unknown> | null) =>
	mount(CourseDashboard, {
		props: {
			course: {
				data: courseData,
				reload: vi.fn(),
				loading: false,
			} as any,
		},
		global: {
			mocks: {
				__: (s: string) => s,
			},
			provide: {
				$dayjs: () => ({ format: () => '' }),
			},
			stubs: {
				LucideStar: true,
			},
		},
	})

describe('CourseDashboard Average Rating', () => {
	it('displays 0 when course has no rating', () => {
		const wrapper = mountDashboard({ name: 'C1', rating: 0, rating_count: 0 })
		const cards = wrapper.findAllComponents({ name: 'NumberChartGraph' })
		const ratingCard = cards.find((c) => c.props('title') === 'Average Rating')
		expect(ratingCard).toBeDefined()
		expect(ratingCard?.props('value')).toBe('0')
	})

	it('formats average rating and shows rating count suffix when present', () => {
		const wrapper = mountDashboard({
			name: 'C1',
			rating: 4.6666,
			rating_count: 12,
		})
		const cards = wrapper.findAllComponents({ name: 'NumberChartGraph' })
		const ratingCard = cards.find((c) => c.props('title') === 'Average Rating')
		expect(ratingCard).toBeDefined()
		expect(ratingCard?.props('value')).toBe('4.7')
		expect(ratingCard?.text()).toContain('(12)')
	})
})
