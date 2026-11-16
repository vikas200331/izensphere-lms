<template>
	<div class="flex-1 flex flex-col min-h-0 bg-surface-base overflow-y-auto">
		<PageHeader :breadcrumbs="[{ label: __('Learning') }, { label: __('AI Learning & Practice') }]">
			<template #actions>
				<div class="flex items-center gap-2">
					<button
						class="px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5 border"
						:class="activeView === 'practice' ? 'bg-violet-600 text-white border-violet-600 shadow-xs' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'"
						@click="activeView = 'practice'"
					>
						<span class="lucide-brain size-3.5"></span>
						{{ __('Practice Questions') }}
					</button>

					<button
						class="px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5 border"
						:class="activeView === 'history' ? 'bg-violet-600 text-white border-violet-600 shadow-xs' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'"
						@click="activeView = 'history'; loadPracticeHistory()"
					>
						<span class="lucide-bar-chart-2 size-3.5"></span>
						{{ __('My Performance & History') }}
					</button>
				</div>
			</template>
		</PageHeader>

		<div class="max-w-7xl mx-auto w-full p-4 md:p-6 space-y-6">
			<!-- Header Banner -->
			<div class="rounded-2xl border bg-gradient-to-r from-violet-900 via-indigo-900 to-purple-900 text-white p-6 shadow-sm">
				<div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
					<div class="space-y-1.5">
						<div class="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-xs font-semibold backdrop-blur-sm">
							<span class="lucide-sparkles size-3.5 text-violet-300"></span>
							{{ __('Course-Based Self-Paced Practice') }}
						</div>
						<h1 class="text-2xl font-bold tracking-tight">
							{{ __('AI Learning & Question Practice') }}
						</h1>
						<p class="text-xs md:text-sm text-violet-200 max-w-2xl">
							{{ __('Sharpen your subject mastery by practicing vetted questions from your enrolled courses. Get instant feedback, step-by-step solutions, and AI tutor explanations.') }}
						</p>
					</div>

					<!-- Enrolled Courses Quick Count -->
					<div class="flex items-center gap-3">
						<div class="text-right bg-white/10 px-4 py-2.5 rounded-xl backdrop-blur-sm border border-white/10">
							<div class="text-2xl font-bold text-white">{{ enrolledCourses.length }}</div>
							<div class="text-[11px] text-violet-200 font-medium">{{ __('Enrolled Courses') }}</div>
						</div>
						<div class="text-right bg-white/10 px-4 py-2.5 rounded-xl backdrop-blur-sm border border-white/10">
							<div class="text-2xl font-bold text-white">{{ totalQuestionsInCourse }}</div>
							<div class="text-[11px] text-violet-200 font-medium">{{ __('Course Questions') }}</div>
						</div>
					</div>
				</div>
			</div>

			<!-- Zero Enrollments Warning -->
			<div
				v-if="!loadingCourses && enrolledCourses.length === 0"
				class="rounded-xl border border-amber-200 bg-amber-50 p-8 text-center space-y-3"
			>
				<span class="lucide-alert-circle size-10 text-amber-600 mx-auto"></span>
				<h3 class="text-base font-bold text-amber-900">{{ __('No Active Enrolled Courses Found') }}</h3>
				<p class="text-xs text-amber-800 max-w-md mx-auto">
					{{ __('You are not currently enrolled in any active courses. Please enroll in a course to access its AI Question Bank and interactive practice sessions.') }}
				</p>
			</div>

			<!-- MAIN VIEW: PRACTICE -->
			<div v-else-if="activeView === 'practice'" class="space-y-6">
				<!-- Course Selection Cards / Tabs -->
				<div class="space-y-2">
					<label class="block text-xs font-bold uppercase tracking-wider text-gray-500">
						{{ __('Select Enrolled Course:') }}
					</label>
					<div class="flex items-center gap-3 overflow-x-auto pb-2">
						<button
							v-for="c in enrolledCourses"
							:key="c.name"
							class="flex items-center gap-2.5 px-4 py-2.5 rounded-xl border text-xs font-semibold transition-all shrink-0 shadow-2xs"
							:class="selectedCourse === c.name ? 'border-violet-600 bg-violet-50/80 text-violet-950 ring-2 ring-violet-500/20' : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300 hover:bg-gray-50'"
							@click="onSelectCourse(c.name)"
						>
							<span class="lucide-book-open size-4 text-violet-600 shrink-0"></span>
							<div class="text-left">
								<div class="font-bold line-clamp-1">{{ c.title }}</div>
								<div class="text-[10px] text-gray-500 font-normal">{{ c.total_questions }} {{ __('Approved Questions') }}</div>
							</div>
						</button>
					</div>
				</div>

				<!-- Filtering Controls -->
				<div class="rounded-xl border bg-surface-base p-4 shadow-sm space-y-3">
					<div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-3">
						<!-- Chapter Filter -->
						<div>
							<label class="block text-xs font-medium text-ink-gray-7 mb-1">{{ __('Chapter / Unit') }}</label>
							<select
								v-model="filters.chapter"
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-1.5 text-xs text-gray-900 focus:border-violet-500 focus:ring-1 focus:ring-violet-500"
								@change="fetchQuestions"
							>
								<option value="">{{ __('All Chapters') }}</option>
								<option v-for="ch in currentCourseChapters" :key="ch.name" :value="ch.name">
									{{ ch.title }}
								</option>
							</select>
						</div>

						<!-- Difficulty Filter -->
						<div>
							<label class="block text-xs font-medium text-ink-gray-7 mb-1">{{ __('Difficulty') }}</label>
							<select
								v-model="filters.difficulty"
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-1.5 text-xs text-gray-900 focus:border-violet-500 focus:ring-1 focus:ring-violet-500"
								@change="fetchQuestions"
							>
								<option value="All">{{ __('All Difficulties') }}</option>
								<option value="Easy">{{ __('Easy') }}</option>
								<option value="Medium">{{ __('Medium') }}</option>
								<option value="Hard">{{ __('Hard') }}</option>
							</select>
						</div>

						<!-- Type Filter -->
						<div>
							<label class="block text-xs font-medium text-ink-gray-7 mb-1">{{ __('Question Type') }}</label>
							<select
								v-model="filters.type"
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-1.5 text-xs text-gray-900 focus:border-violet-500 focus:ring-1 focus:ring-violet-500"
								@change="fetchQuestions"
							>
								<option value="All">{{ __('All Types') }}</option>
								<option value="Choices">{{ __('Choices (MCQ)') }}</option>
								<option value="User Input">{{ __('Fill in the Blanks') }}</option>
								<option value="Open Ended">{{ __('Open Ended') }}</option>
							</select>
						</div>

						<!-- Search Box -->
						<div>
							<label class="block text-xs font-medium text-ink-gray-7 mb-1">{{ __('Search Keywords') }}</label>
							<input
								type="text"
								v-model="filters.search_query"
								class="w-full rounded-md border border-gray-300 px-3 py-1.5 text-xs"
								placeholder="Search question..."
								@keyup.enter="fetchQuestions"
							/>
						</div>

						<!-- Filter Action -->
						<div class="flex items-end">
							<Button variant="solid" theme="violet" class="w-full" size="sm" @click="fetchQuestions">
								<template #prefix><span class="lucide-filter size-3.5"></span></template>
								{{ __('Apply Filters') }}
							</Button>
						</div>
					</div>
				</div>

				<!-- Questions Display -->
				<div v-if="loadingQuestions" class="rounded-xl border bg-white p-12 text-center text-gray-500">
					<div class="animate-pulse space-y-3">
						<div class="h-4 bg-gray-200 rounded w-1/3 mx-auto"></div>
						<div class="h-4 bg-gray-100 rounded w-1/2 mx-auto"></div>
					</div>
					<p class="text-xs text-gray-400 mt-4">{{ __('Loading approved questions for your course...') }}</p>
				</div>

				<div v-else-if="questionsList.length === 0" class="rounded-xl border bg-white p-12 text-center text-gray-500 space-y-2">
					<span class="lucide-book-x size-8 text-gray-400 mx-auto"></span>
					<h4 class="font-bold text-gray-800 text-sm">{{ __('No Approved Questions Found') }}</h4>
					<p class="text-xs text-gray-500">{{ __('No questions match your current filters in this course. Try changing chapters or difficulty.') }}</p>
				</div>

				<!-- Active Question Interactive Card -->
				<div v-else class="space-y-4">
					<!-- Pager Bar -->
					<div class="flex items-center justify-between text-xs text-gray-500 bg-white p-3 rounded-xl border shadow-2xs">
						<div class="flex items-center gap-2">
							<span class="font-bold text-gray-800">
								{{ __('Question') }} {{ currentQuestionIndex + 1 }} {{ __('of') }} {{ questionsList.length }}
							</span>
							<Badge v-if="currentQuestion.chapter" variant="subtle" theme="purple" size="sm">
								{{ currentQuestion.chapter }}
							</Badge>
						</div>

						<div class="flex items-center gap-2">
							<Button
								size="xs"
								variant="outline"
								:disabled="currentQuestionIndex === 0"
								@click="goToPrevQuestion"
							>
								<template #prefix><span class="lucide-chevron-left size-3"></span></template>
								{{ __('Previous') }}
							</Button>
							<Button
								size="xs"
								variant="outline"
								:disabled="currentQuestionIndex === questionsList.length - 1"
								@click="goToNextQuestion"
							>
								{{ __('Next') }}
								<template #suffix><span class="lucide-chevron-right size-3"></span></template>
							</Button>
						</div>
					</div>

					<!-- Question Box -->
					<div class="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm space-y-6">
						<!-- Metadata Pill Row -->
						<div class="flex items-center justify-between gap-3 flex-wrap border-b pb-3">
							<div class="flex items-center gap-2 flex-wrap">
								<span class="font-mono text-xs font-bold text-violet-700 bg-violet-50 px-2 py-0.5 rounded">
									{{ currentQuestion.name }}
								</span>
								<Badge
									:theme="currentQuestion.difficulty === 'Easy' ? 'green' : (currentQuestion.difficulty === 'Hard' ? 'red' : 'orange')"
									variant="subtle"
									size="sm"
								>
									{{ currentQuestion.difficulty }}
								</Badge>
								<Badge variant="subtle" theme="blue" size="sm">
									{{ currentQuestion.type }}
								</Badge>
								<Badge variant="subtle" theme="gray" size="sm">
									{{ currentQuestion.marks }} {{ __('Mark(s)') }}
								</Badge>
							</div>

							<!-- Previous status indicator if attempted -->
							<div v-if="practiceResult || currentQuestion.already_attempted">
								<Badge
									:theme="(practiceResult?.is_correct || currentQuestion.previous_attempt?.is_correct) ? 'green' : 'red'"
									variant="solid"
									size="sm"
								>
									{{ (practiceResult?.is_correct || currentQuestion.previous_attempt?.is_correct) ? '✓ ' + __('Practiced: Correct') : '✕ ' + __('Practiced: Needs Review') }}
								</Badge>
							</div>
						</div>

						<!-- Question Statement -->
						<div class="text-base font-semibold text-gray-900 leading-relaxed" v-html="currentQuestion.question"></div>

						<!-- Answering Options (Choices / MCQ) -->
						<div v-if="currentQuestion.type === 'Choices' && currentQuestion.options?.length" class="space-y-2.5">
							<div
								v-for="(opt, optIdx) in currentQuestion.options"
								:key="optIdx"
								class="flex items-center gap-3 p-3.5 rounded-xl border text-sm font-medium transition-all cursor-pointer"
								:class="getOptionClass(opt, optIdx)"
								@click="!isSubmitted && (selectedAnswer = opt)"
							>
								<span
									class="size-6 flex items-center justify-center rounded-full text-xs font-bold shrink-0 transition-colors"
									:class="getOptionBadgeClass(opt, optIdx)"
								>
									{{ String.fromCharCode(65 + optIdx) }}
								</span>
								<span class="flex-1 text-gray-900">{{ opt }}</span>
								<span v-if="isSubmitted && opt === practiceResult?.correct_answer" class="text-xs font-bold text-emerald-700">
									✓ {{ __('Correct Answer') }}
								</span>
							</div>
						</div>

						<!-- Answering Area (User Input / Fill in the Blanks) -->
						<div v-else-if="currentQuestion.type === 'User Input'" class="space-y-2">
							<label class="block text-xs font-semibold text-gray-700">{{ __('Type your answer below:') }}</label>
							<input
								type="text"
								v-model="selectedAnswer"
								:disabled="isSubmitted"
								class="w-full text-sm border border-gray-300 rounded-lg p-3 bg-white focus:border-violet-500 focus:ring-1 focus:ring-violet-500 disabled:bg-gray-50"
								placeholder="Enter your answer..."
								@keyup.enter="submitAnswer"
							/>
						</div>

						<!-- Answering Area (Open Ended) -->
						<div v-else class="space-y-2">
							<label class="block text-xs font-semibold text-gray-700">{{ __('Draft your response / solution notes:') }}</label>
							<textarea
								v-model="selectedAnswer"
								:disabled="isSubmitted"
								rows="4"
								class="w-full text-sm border border-gray-300 rounded-lg p-3 bg-white focus:border-violet-500 focus:ring-1 focus:ring-violet-500 disabled:bg-gray-50"
								placeholder="Write your explanation or key concepts here..."
							></textarea>
						</div>

						<!-- Action Buttons Bar -->
						<div class="flex items-center justify-between gap-3 pt-4 border-t flex-wrap">
							<div class="flex items-center gap-2 flex-wrap">
								<!-- Submit Answer -->
								<Button
									v-if="!isSubmitted"
									variant="solid"
									theme="violet"
									size="md"
									:loading="submitting"
									:disabled="!selectedAnswer"
									@click="submitAnswer"
								>
									<template #prefix><span class="lucide-check size-4"></span></template>
									{{ __('Check Answer') }}
								</Button>

								<Button
									v-else
									variant="outline"
									theme="gray"
									size="md"
									@click="resetCurrentQuestion"
								>
									<template #prefix><span class="lucide-rotate-ccw size-4"></span></template>
									{{ __('Try Again') }}
								</Button>

								<!-- Ask AI Tutor -->
								<Button
									variant="outline"
									theme="purple"
									size="md"
									:loading="loadingAiHelp"
									@click="askAiTutor"
								>
									<template #prefix><span class="lucide-sparkles size-4 text-purple-600"></span></template>
									{{ __('Ask AI Tutor to Explain') }}
								</Button>

								<!-- Practice Similar Question -->
								<Button
									variant="outline"
									theme="indigo"
									size="md"
									:loading="generatingSimilar"
									@click="generateSimilar"
								>
									<template #prefix><span class="lucide-refresh-cw size-4 text-indigo-600"></span></template>
									{{ __('Practice Similar Question') }}
								</Button>
							</div>

							<!-- Next Question Shortcut -->
							<div class="flex items-center gap-2">
								<Button
									size="md"
									variant="ghost"
									:disabled="currentQuestionIndex === questionsList.length - 1"
									@click="goToNextQuestion"
								>
									{{ __('Next Question') }}
									<template #suffix><span class="lucide-arrow-right size-4"></span></template>
								</Button>
							</div>
						</div>

						<!-- Reveal Section (Visible AFTER Submitting Answer) -->
						<div v-if="isSubmitted && practiceResult" class="space-y-3 pt-2">
							<!-- Correct / Incorrect Callout -->
							<div
								class="rounded-xl border p-4 text-sm flex items-start gap-3 shadow-2xs"
								:class="practiceResult.is_correct ? 'border-emerald-300 bg-emerald-50 text-emerald-950' : 'border-red-300 bg-red-50 text-red-950'"
							>
								<span
									class="size-6 flex items-center justify-center rounded-full text-white font-bold shrink-0 mt-0.5"
									:class="practiceResult.is_correct ? 'bg-emerald-600' : 'bg-red-600'"
								>
									{{ practiceResult.is_correct ? '✓' : '✕' }}
								</span>
								<div class="space-y-1">
									<div class="font-bold">
										{{ practiceResult.is_correct ? __('Correct! Well done!') : __('Incorrect. Keep practicing!') }}
										<span class="font-normal ml-2">({{ practiceResult.marks_obtained }} / {{ practiceResult.total_marks }} Mark{{ practiceResult.total_marks > 1 ? 's' : '' }})</span>
									</div>
									<div v-if="!practiceResult.is_correct" class="text-xs">
										<strong>{{ __('Correct Answer:') }}</strong> {{ practiceResult.correct_answer }}
									</div>
								</div>
							</div>

							<!-- Official Detailed Explanation & Rubric -->
							<div class="rounded-xl border border-gray-200 bg-gray-50/70 p-4 space-y-2 text-xs text-gray-800">
								<div class="flex items-center gap-1.5 font-bold uppercase tracking-wider text-gray-700">
									<span class="lucide-book-open size-3.5 text-violet-600"></span>
									{{ __('Detailed Explanation & Rationale:') }}
								</div>
								<div class="whitespace-pre-line leading-relaxed text-gray-900 font-sans">
									{{ practiceResult.explanation }}
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>

			<!-- TAB 2: MY PERFORMANCE & HISTORY -->
			<div v-else-if="activeView === 'history'" class="space-y-6">
				<!-- Performance Overview Cards -->
				<div class="grid grid-cols-2 md:grid-cols-4 gap-4">
					<div class="rounded-xl border bg-white p-4 shadow-sm space-y-1">
						<div class="text-xs font-semibold text-gray-500">{{ __('Questions Attempted') }}</div>
						<div class="text-2xl font-bold text-gray-900">{{ studentStats.total_attempted }}</div>
						<div class="text-[11px] text-gray-400">{{ __('Across enrolled courses') }}</div>
					</div>

					<div class="rounded-xl border bg-white p-4 shadow-sm space-y-1">
						<div class="text-xs font-semibold text-gray-500">{{ __('Correct Answers') }}</div>
						<div class="text-2xl font-bold text-emerald-600">{{ studentStats.total_correct }}</div>
						<div class="text-[11px] text-emerald-700 font-medium">{{ studentStats.accuracy_percentage }}% {{ __('Accuracy') }}</div>
					</div>

					<div class="rounded-xl border bg-white p-4 shadow-sm space-y-1">
						<div class="text-xs font-semibold text-gray-500">{{ __('Total Marks Earned') }}</div>
						<div class="text-2xl font-bold text-violet-700">{{ studentStats.total_marks_earned }}</div>
						<div class="text-[11px] text-violet-800">{{ __('Practice points') }}</div>
					</div>

					<div class="rounded-xl border bg-white p-4 shadow-sm space-y-1">
						<div class="text-xs font-semibold text-gray-500">{{ __('Active Course') }}</div>
						<div class="text-sm font-bold text-gray-800 line-clamp-1">{{ selectedCourseTitle }}</div>
						<div class="text-[11px] text-gray-400">{{ __('Self-paced learning') }}</div>
					</div>
				</div>

				<!-- Chapter Mastery Breakdown -->
				<div v-if="studentStats.chapter_breakdown && Object.keys(studentStats.chapter_breakdown).length" class="rounded-xl border bg-white p-5 shadow-sm space-y-4">
					<h3 class="text-sm font-bold text-gray-900">{{ __('Chapter Mastery Rates') }}</h3>
					<div class="space-y-3">
						<div v-for="(chData, chName) in studentStats.chapter_breakdown" :key="chName" class="space-y-1">
							<div class="flex items-center justify-between text-xs">
								<span class="font-medium text-gray-800">{{ chName }}</span>
								<span class="font-bold text-gray-700">{{ chData.accuracy }}% ({{ chData.correct }}/{{ chData.total }})</span>
							</div>
							<div class="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
								<div
									class="h-2 rounded-full transition-all"
									:class="chData.accuracy >= 75 ? 'bg-emerald-500' : (chData.accuracy >= 50 ? 'bg-amber-500' : 'bg-red-500')"
									:style="{ width: chData.accuracy + '%' }"
								></div>
							</div>
						</div>
					</div>
				</div>

				<!-- Recent Practice Logs -->
				<div class="rounded-xl border bg-white p-5 shadow-sm space-y-3">
					<h3 class="text-sm font-bold text-gray-900">{{ __('Recent Practice Activity') }}</h3>
					<div v-if="!studentStats.recent_logs?.length" class="text-center py-8 text-xs text-gray-400">
						{{ __('No recent practice sessions found. Start answering questions to build your history!') }}
					</div>
					<div v-else class="divide-y text-xs">
						<div
							v-for="log in studentStats.recent_logs"
							:key="log.name"
							class="py-3 flex items-start justify-between gap-3"
						>
							<div class="space-y-1">
								<div class="font-medium text-gray-900">{{ log.question_text }}</div>
								<div class="text-[11px] text-gray-500 flex items-center gap-2">
									<span>{{ log.course }}</span>
									<span v-if="log.chapter">&bull; {{ log.chapter }}</span>
									<span>&bull; {{ log.practice_date ? new Date(log.practice_date).toLocaleString() : '' }}</span>
								</div>
							</div>

							<div class="text-right shrink-0">
								<Badge :theme="log.is_correct ? 'green' : 'red'" variant="subtle" size="sm">
									{{ log.is_correct ? __('Correct') : __('Incorrect') }}
								</Badge>
								<div class="text-[10px] text-gray-400 mt-1">
									{{ log.marks_obtained }} / {{ log.total_marks }} {{ __('Marks') }}
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>

		<!-- MODAL: AI ACADEMIC TUTOR EXPLANATION -->
		<Dialog
			v-model="showAiHelpModal"
			:options="{
				title: __('AI Academic Tutor Breakdown'),
				size: 'lg',
			}"
		>
			<template #body-content>
				<div class="space-y-4 p-2 text-sm">
					<div class="rounded-xl border border-purple-200 bg-purple-50/80 p-3.5 flex items-center gap-3 text-xs text-purple-900">
						<span class="lucide-sparkles size-5 text-purple-600 shrink-0"></span>
						<div>
							<span class="font-bold">{{ __('Interactive Conceptual Tutor:') }}</span>
							{{ __('Personalized pedagogical breakdown to help you master this concept for examinations.') }}
						</div>
					</div>

					<div class="prose prose-sm max-w-none text-gray-800 leading-relaxed whitespace-pre-line bg-white p-4 rounded-xl border border-gray-100 shadow-2xs font-sans text-xs">
						{{ aiHelpText }}
					</div>
				</div>
			</template>
			<template #actions>
				<Button variant="solid" theme="purple" size="sm" @click="showAiHelpModal = false">
					{{ __('Got it, thanks!') }}
				</Button>
			</template>
		</Dialog>

		<!-- MODAL: SIMILAR PRACTICE QUESTION -->
		<Dialog
			v-model="showSimilarModal"
			:options="{
				title: __('Practice Clone Question'),
				size: 'lg',
			}"
		>
			<template #body-content>
				<div v-if="similarQuestion" class="space-y-4 p-2 text-xs">
					<div class="rounded-lg bg-indigo-50 border border-indigo-200 p-3 text-indigo-900 text-xs">
						<span class="font-bold">{{ __('Fresh AI Practice Variation:') }}</span>
						{{ __('Test your understanding on this brand new variation created from the same syllabus concept.') }}
					</div>

					<div class="font-semibold text-sm text-gray-900 leading-relaxed" v-html="similarQuestion.question"></div>

					<div v-if="similarQuestion.options?.length" class="space-y-2">
						<div
							v-for="(sOpt, sIdx) in similarQuestion.options"
							:key="sIdx"
							class="flex items-center gap-2.5 p-3 rounded-lg border cursor-pointer transition-colors"
							:class="similarSelectedAnswer === sOpt ? 'border-indigo-600 bg-indigo-50 font-bold' : 'border-gray-200 bg-white hover:bg-gray-50'"
							@click="!similarSubmitted && (similarSelectedAnswer = sOpt)"
						>
							<span class="size-5 flex items-center justify-center rounded-full text-xs font-bold bg-gray-200">
								{{ String.fromCharCode(65 + sIdx) }}
							</span>
							<span class="flex-1">{{ sOpt }}</span>
						</div>
					</div>

					<!-- Similar Feedback -->
					<div v-if="similarSubmitted" class="p-3 rounded-lg border text-xs" :class="similarIsCorrect ? 'bg-emerald-50 border-emerald-300 text-emerald-900' : 'bg-red-50 border-red-300 text-red-900'">
						<div class="font-bold">{{ similarIsCorrect ? '✓ ' + __('Correct!') : '✕ ' + __('Incorrect.') }}</div>
						<div class="mt-1"><strong>{{ __('Answer:') }}</strong> {{ similarQuestion.correct_answer }}</div>
						<div class="mt-1 text-gray-700 whitespace-pre-line">{{ similarQuestion.explanation }}</div>
					</div>
				</div>
			</template>
			<template #actions>
				<div class="flex items-center gap-2">
					<Button
						v-if="!similarSubmitted"
						variant="solid"
						theme="indigo"
						size="sm"
						:disabled="!similarSelectedAnswer"
						@click="checkSimilarAnswer"
					>
						{{ __('Check Answer') }}
					</Button>
					<Button variant="outline" size="sm" @click="showSimilarModal = false">
						{{ __('Close') }}
					</Button>
				</div>
			</template>
		</Dialog>
	</div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import PageHeader from '@/components/Layouts/PageHeader.vue'
import { Button, Badge, Dialog, toast, call } from 'frappe-ui'

const route = useRoute()

const activeView = ref('practice')
const loadingCourses = ref(true)
const loadingQuestions = ref(false)
const submitting = ref(false)
const loadingAiHelp = ref(false)
const generatingSimilar = ref(false)

const enrolledCourses = ref([])
const selectedCourse = ref('')
const questionsList = ref([])
const currentQuestionIndex = ref(0)
const selectedAnswer = ref('')
const isSubmitted = ref(false)
const practiceResult = ref(null)

const studentStats = ref({
	total_attempted: 0,
	total_correct: 0,
	accuracy_percentage: 0.0,
	total_marks_earned: 0.0,
	chapter_breakdown: {},
	recent_logs: [],
})

const filters = reactive({
	chapter: '',
	difficulty: 'All',
	type: 'All',
	search_query: '',
})

// AI Help Modal State
const showAiHelpModal = ref(false)
const aiHelpText = ref('')

// Similar Question Modal State
const showSimilarModal = ref(false)
const similarQuestion = ref(null)
const similarSelectedAnswer = ref('')
const similarSubmitted = ref(false)
const similarIsCorrect = ref(false)

const currentCourseObj = computed(() => {
	return enrolledCourses.value.find((c) => c.name === selectedCourse.value) || null
})

const selectedCourseTitle = computed(() => {
	return currentCourseObj.value?.title || selectedCourse.value || 'None'
})

const totalQuestionsInCourse = computed(() => {
	return currentCourseObj.value?.total_questions || 0
})

const currentCourseChapters = computed(() => {
	return currentCourseObj.value?.chapters || []
})

const currentQuestion = computed(() => {
	return questionsList.value[currentQuestionIndex.value] || {}
})

onMounted(async () => {
	await loadEnrolledCourses()
	if (route.query.course && enrolledCourses.value.some((c) => c.name === route.query.course)) {
		selectedCourse.value = route.query.course
	}
	if (selectedCourse.value) {
		await fetchQuestions()
	}
})

async function loadEnrolledCourses() {
	loadingCourses.value = true
	try {
		const res = await call('lms.lms.ai.student_practice_api.api_get_student_enrolled_courses')
		enrolledCourses.value = res?.courses || []
		if (enrolledCourses.value.length > 0 && !selectedCourse.value) {
			selectedCourse.value = enrolledCourses.value[0].name
		}
	} catch (e) {
		toast.error(e.message || __('Failed to load your enrolled courses.'))
	} finally {
		loadingCourses.value = false
	}
}

async function onSelectCourse(courseName) {
	if (selectedCourse.value === courseName) return
	selectedCourse.value = courseName
	filters.chapter = ''
	currentQuestionIndex.value = 0
	resetCurrentQuestion()
	await fetchQuestions()
}

async function fetchQuestions() {
	if (!selectedCourse.value) return
	loadingQuestions.value = true
	try {
		const res = await call('lms.lms.ai.student_practice_api.api_get_student_practice_questions', {
			course: selectedCourse.value,
			chapter: filters.chapter || undefined,
			difficulty: filters.difficulty !== 'All' ? filters.difficulty : undefined,
			question_type: filters.type !== 'All' ? filters.type : undefined,
			search_query: filters.search_query || undefined,
			start: 0,
			page_length: 50,
		})
		questionsList.value = res?.questions || []
		currentQuestionIndex.value = 0
		syncQuestionState()
	} catch (e) {
		toast.error(e.message || __('Failed to load practice questions.'))
	} finally {
		loadingQuestions.value = false
	}
}

function syncQuestionState() {
	const q = currentQuestion.value
	if (q && q.already_attempted && q.previous_attempt) {
		selectedAnswer.value = q.previous_attempt.selected_answer || ''
		isSubmitted.value = true
		practiceResult.value = {
			is_correct: q.previous_attempt.is_correct,
			marks_obtained: q.previous_attempt.marks_obtained,
			total_marks: q.marks,
			correct_answer: q.previous_attempt.correct_answer,
			explanation: __('Previously attempted. Review above or try again.'),
		}
	} else {
		resetCurrentQuestion()
	}
}

function resetCurrentQuestion() {
	selectedAnswer.value = ''
	isSubmitted.value = false
	practiceResult.value = null
}

function goToNextQuestion() {
	if (currentQuestionIndex.value < questionsList.value.length - 1) {
		currentQuestionIndex.value++
		syncQuestionState()
	}
}

function goToPrevQuestion() {
	if (currentQuestionIndex.value > 0) {
		currentQuestionIndex.value--
		syncQuestionState()
	}
}

async function submitAnswer() {
	if (!selectedAnswer.value || !currentQuestion.value?.name) return
	submitting.value = true
	try {
		const res = await call('lms.lms.ai.student_practice_api.api_submit_student_practice_answer', {
			question_id: currentQuestion.value.name,
			user_answer: selectedAnswer.value,
			course: selectedCourse.value,
		})
		if (res && res.status === 'success') {
			practiceResult.value = res
			isSubmitted.value = true
			if (res.is_correct) {
				toast.success(__('Correct answer! +{0} marks').format(res.marks_obtained))
			} else {
				toast.error(__('Incorrect. Check explanation below.'))
			}
		}
	} catch (e) {
		toast.error(e.message || __('Failed to submit practice answer.'))
	} finally {
		submitting.value = false
	}
}

function getOptionClass(opt, optIdx) {
	if (isSubmitted.value && practiceResult.value) {
		if (opt === practiceResult.value.correct_answer) {
			return 'border-emerald-500 bg-emerald-50/80 text-emerald-950 font-bold ring-1 ring-emerald-500'
		}
		if (selectedAnswer.value === opt && !practiceResult.value.is_correct) {
			return 'border-red-400 bg-red-50 text-red-950 font-semibold'
		}
		return 'border-gray-200 bg-gray-50 text-gray-500 opacity-60'
	}
	if (selectedAnswer.value === opt) {
		return 'border-violet-600 bg-violet-50 text-violet-950 font-bold ring-2 ring-violet-500/20'
	}
	return 'border-gray-200 bg-white hover:border-gray-300 hover:bg-gray-50/70'
}

function getOptionBadgeClass(opt, optIdx) {
	if (isSubmitted.value && practiceResult.value) {
		if (opt === practiceResult.value.correct_answer) {
			return 'bg-emerald-600 text-white'
		}
		if (selectedAnswer.value === opt && !practiceResult.value.is_correct) {
			return 'bg-red-600 text-white'
		}
	}
	if (selectedAnswer.value === opt) {
		return 'bg-violet-600 text-white'
	}
	return 'bg-gray-100 text-gray-700'
}

async function askAiTutor() {
	if (!currentQuestion.value?.name) return
	loadingAiHelp.value = true
	try {
		const res = await call('lms.lms.ai.student_practice_api.api_ask_ai_question_help', {
			question_id: currentQuestion.value.name,
			course: selectedCourse.value,
		})
		if (res && res.ai_explanation) {
			aiHelpText.value = res.ai_explanation
			showAiHelpModal.value = true
		}
	} catch (e) {
		toast.error(e.message || __('Failed to get AI Tutor guidance.'))
	} finally {
		loadingAiHelp.value = false
	}
}

async function generateSimilar() {
	if (!currentQuestion.value?.name) return
	generatingSimilar.value = true
	try {
		const res = await call('lms.lms.ai.student_practice_api.api_generate_similar_practice_question', {
			question_id: currentQuestion.value.name,
			course: selectedCourse.value,
		})
		if (res && res.similar_question) {
			similarQuestion.value = res.similar_question
			similarSelectedAnswer.value = ''
			similarSubmitted.value = false
			similarIsCorrect.value = false
			showSimilarModal.value = true
		}
	} catch (e) {
		toast.error(e.message || __('Failed to generate similar question.'))
	} finally {
		generatingSimilar.value = false
	}
}

function checkSimilarAnswer() {
	if (!similarSelectedAnswer.value || !similarQuestion.value) return
	const correct = String(similarQuestion.value.correct_answer).trim().toLowerCase()
	const userAns = String(similarSelectedAnswer.value).trim().toLowerCase()
	similarIsCorrect.value = correct === userAns || correct.includes(userAns)
	similarSubmitted.value = true
}

async function loadPracticeHistory() {
	try {
		const res = await call('lms.lms.ai.student_practice_api.api_get_student_practice_history', {
			course: selectedCourse.value || undefined,
		})
		if (res) {
			studentStats.value = res
		}
	} catch (e) {
		console.error(e)
	}
}
</script>
