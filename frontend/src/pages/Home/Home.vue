<template>
	<div class="w-full p-5">
		<!-- iLMS CSS Banner -->
		<div class="mb-6 w-full rounded-2xl overflow-hidden shadow-lg bg-gradient-to-r from-[#0B1528] to-blue-900 text-white p-6 md:p-8 flex flex-col md:flex-row items-center justify-between relative border border-blue-800">
			<!-- Subtle background pattern -->
			<div class="absolute inset-0 opacity-10" style="background-image: radial-gradient(#ffffff 1px, transparent 1px); background-size: 24px 24px;"></div>
			
			<!-- Left Section -->
			<div class="flex flex-col space-y-5 z-10 w-full md:w-2/3">
				<!-- Brand Header -->
				<div class="flex items-center space-x-3">
					<div class="w-12 h-12 rounded-full overflow-hidden border border-blue-400/30 flex items-center justify-center shrink-0 shadow-lg bg-black">
						<img src="/izensphere-logo.png" alt="iZenSphere Logo" class="w-full h-full object-cover" />
					</div>
					<div class="leading-tight flex flex-col">
						<span class="font-semibold text-blue-50 tracking-wide text-sm">iZenSphere Consulting</span>
						<a href="https://www.izensphere.com" target="_blank" class="text-amber-400 text-xs font-medium hover:text-amber-300 hover:underline transition-colors cursor-pointer">www.izensphere.com</a>
					</div>
				</div>
				
				<!-- Main Content -->
				<div class="flex flex-col pt-2">
					<div class="text-amber-400 text-xs md:text-sm tracking-[0.25em] font-bold uppercase mb-2 flex items-center opacity-90">
						<span class="w-12 h-[2px] bg-amber-400 mr-4 rounded-full"></span>
						Smart Learning Solutions
					</div>
					<h1 class="text-5xl md:text-7xl font-black tracking-tighter drop-shadow-lg mb-4">
						<span class="text-transparent bg-clip-text bg-gradient-to-br from-white to-blue-100">i</span><span class="text-transparent bg-clip-text bg-gradient-to-br from-amber-300 to-amber-500">LMS</span>
					</h1>
					<p class="text-blue-50 text-base md:text-lg leading-relaxed max-w-xl font-light opacity-95 border-l-2 border-blue-500/50 pl-4 mt-2">
						A smart and flexible Learning Management System — designed to deliver engaging learning experiences, track progress and build a better future.
					</p>
				</div>
			</div>

			<!-- Right Section (Clean Glassmorphism Graphic) -->
			<div class="hidden md:flex z-10 w-1/3 justify-end items-center relative pr-4">
				<div class="relative flex items-center justify-center">
					<!-- Glow effect -->
					<div class="absolute inset-0 bg-blue-400 rounded-full opacity-20 blur-3xl transform scale-125"></div>
					
					<!-- Center Icon -->
					<div class="bg-white/10 backdrop-blur-md rounded-2xl p-6 border border-white/20 shadow-2xl relative z-10 transition-transform duration-500 hover:scale-105">
						<span class="lucide-graduation-cap size-20 text-white drop-shadow-lg" />
					</div>
					
					<!-- Floating Accents -->
					<div class="absolute -bottom-5 -left-6 bg-amber-500 rounded-xl p-2.5 shadow-xl border border-amber-400/50 z-20">
						<span class="lucide-book-open size-6 text-white" />
					</div>
					<div class="absolute -top-5 -right-5 bg-blue-500 rounded-xl p-2.5 shadow-xl border border-blue-400/50 z-20">
						<span class="lucide-monitor size-6 text-white" />
					</div>
				</div>
			</div>
		</div>
		<div class="space-y-2">
			<div class="flex items-center justify-between">
				<h1 class="text-2xl-bold text-ink-gray-9">
					{{ __('Hey') }}, {{ user.data?.full_name }} 👋
				</h1>
				<div>
					<button
						v-if="!isAdmin"
						type="button"
						@click="showStreakModal = true"
						:aria-label="
							__('View learning streak: {0} days').format(
								streakInfo.data?.current_streak || 0
							)
						"
						class="bg-surface-amber-2 px-2 py-1 rounded-md cursor-pointer"
					>
						<span> 🔥 </span>
						<span class="text-ink-gray-9">
							{{ streakInfo.data?.current_streak }}
						</span>
					</button>
				</div>
			</div>

			<div class="text-lg text-ink-gray-6 leading-6">
				{{ subtitle }}
			</div>
		</div>

		<div
			v-if="isHomeLoading"
			class="flex flex-1 items-center justify-center py-20"
		>
			<LoadingIndicator class="size-5 text-ink-gray-5" />
		</div>
		<AdminHome
			v-else-if="isAdmin && currentTab === 'instructor'"
			:liveClasses="adminLiveClasses"
			:evals="adminEvals"
		/>
		<StudentHome
			v-else-if="currentTab === 'student'"
			:myLiveClasses="myLiveClasses"
		/>
	</div>
	<Streak v-model="showStreakModal" :streakInfo="streakInfo" />
</template>
<script setup lang="ts">
import { computed, inject, onMounted, ref } from 'vue'
import { call, createResource, LoadingIndicator, usePageMeta } from 'frappe-ui'
import { sessionStore } from '@/stores/session'
import StudentHome from '@/pages/Home/StudentHome.vue'
import AdminHome from '@/pages/Home/AdminHome.vue'
import Streak from '@/pages/Home/Streak.vue'

const user = inject<any>('$user')
const { brand } = sessionStore()
const evalCount = ref(0)
const currentTab = ref<'student' | 'instructor'>('student')
const showStreakModal = ref(false)

const fetchEvalCount = () => {
	call('frappe.client.get_count', {
		doctype: 'LMS Certificate Request',
		filters: {
			member: user?.data?.name,
			status: 'Upcoming',
			date: ['>=', inject<any>('$dayjs')().format('YYYY-MM-DD')],
		},
	}).then((data: any) => {
		evalCount.value = data
	})
}

const isAdmin = computed(() => {
	return (
		user.data?.is_moderator ||
		user.data?.is_instructor ||
		user.data?.is_evaluator
	)
})

const isHomeLoading = computed(() => {
	if (isAdmin.value) {
		return (
			(adminLiveClasses.loading && !adminLiveClasses.data) ||
			(adminEvals.loading && !adminEvals.data)
		)
	}
	return myLiveClasses.loading && !myLiveClasses.data
})

onMounted(() => {
	if (isAdmin.value) {
		currentTab.value = 'instructor'
	} else {
		currentTab.value = 'student'
		fetchEvalCount()
	}
})

const myLiveClasses = createResource({
	url: 'lms.lms.api.get_my_live_classes',
	auto: !isAdmin.value ? true : false,
})

const adminLiveClasses = createResource({
	url: 'lms.lms.api.get_admin_live_classes',
	auto: isAdmin.value ? true : false,
})

const adminEvals = createResource({
	url: 'lms.lms.api.get_admin_evals',
	auto: isAdmin.value ? true : false,
})

const streakInfo = createResource({
	url: 'lms.lms.api.get_streak_info',
	auto: true,
})

const subtitle = computed(() => {
	if (isAdmin.value) {
		let liveClassSuffix =
			adminLiveClasses.data?.length > 1 ? __('live classes') : __('live class')
		let evalSuffix =
			adminEvals.data?.length > 1 ? __('evaluations') : __('evaluation')
		if (adminLiveClasses.data?.length > 0 && adminEvals.data?.length > 0) {
			return __('You have {0} upcoming {1} and {2} {3} scheduled.').format(
				adminLiveClasses.data.length,
				liveClassSuffix,
				adminEvals.data.length,
				evalSuffix
			)
		} else if (adminLiveClasses.data?.length > 0) {
			return __('You have {0} upcoming {1}.').format(
				adminLiveClasses.data.length,
				liveClassSuffix
			)
		} else if (adminEvals.data?.length > 0) {
			return __('You have {0} {1} scheduled.').format(
				adminEvals.data.length,
				evalSuffix
			)
		}
		return __('Manage your courses and batches at a glance')
	} else {
		let liveClassSuffix =
			myLiveClasses.data?.length > 1 ? __('live classes') : __('live class')
		let evalSuffix = evalCount.value > 1 ? __('evaluations') : __('evaluation')
		if (myLiveClasses.data?.length > 0 && evalCount.value > 0) {
			return __('You have {0} upcoming {1} and {2} {3} scheduled.').format(
				myLiveClasses.data.length,
				liveClassSuffix,
				evalCount.value,
				evalSuffix
			)
		} else if (myLiveClasses.data?.length > 0) {
			return __('You have {0} upcoming {1}.').format(
				myLiveClasses.data.length,
				liveClassSuffix
			)
		} else if (evalCount.value > 0) {
			return __('You have {0} {1} scheduled.').format(
				evalCount.value,
				evalSuffix
			)
		}
		return __('Resume where you left off')
	}
})

usePageMeta(() => {
	return {
		title: __('Home'),
		icon: brand.favicon,
	}
})
</script>
