import { describe, it, expect } from 'vitest'
import {
	computeContentReleaseActions,
	computeBatchReleaseActions,
	isAuthorizedApprover,
} from '@/utils/contentRelease'

describe('Content Release Actions & Roles', () => {
	describe('isAuthorizedApprover', () => {
		it('returns true when user has is_principal flag', () => {
			expect(isAuthorizedApprover({ data: { is_principal: true } })).toBe(true)
		})

		it('returns true when user has Principal role in roles array', () => {
			expect(
				isAuthorizedApprover({ data: { roles: ['Principal', 'LMS Student'] } })
			).toBe(true)
		})

		it('returns false for an Administrator without Principal role', () => {
			expect(
				isAuthorizedApprover({
					data: {
						is_principal: false,
						is_system_manager: true,
						roles: ['System Manager', 'Administrator', 'Course Creator'],
					},
				})
			).toBe(false)
		})

		it('returns false for a Teacher or Course Creator', () => {
			expect(
				isAuthorizedApprover({
					data: {
						is_principal: false,
						is_instructor: true,
						roles: ['Course Creator', 'Teacher'],
					},
				})
			).toBe(false)
		})

		it('returns true for Administrator explicitly granted Principal role', () => {
			expect(
				isAuthorizedApprover({
					data: {
						is_principal: true,
						is_system_manager: true,
						roles: ['System Manager', 'Administrator', 'Principal'],
					},
				})
			).toBe(true)
		})
	})

	describe('Mode A: Principal Approval Required', () => {
		const mode = 'Principal Approval Required'

		describe('Teacher / Creator', () => {
			it('shows Save Draft, Preview, and Submit for Draft content, but hides Publish and Approve', () => {
				const actions = computeContentReleaseActions({
					releaseMode: mode,
					releaseStatus: 'Draft',
					isApprover: false,
					canManage: true,
					contentExists: true,
				})

				expect(actions.canSaveDraft).toBe(true)
				expect(actions.canPreview).toBe(true)
				expect(actions.canSubmit).toBe(true)
				expect(actions.submitLabel).toBe('Submit for Principal Approval')
				expect(actions.canPublish).toBe(false) // MUST BE HIDDEN
				expect(actions.canApprove).toBe(false) // MUST BE HIDDEN
				expect(actions.canReject).toBe(false)
			})

			it('shows Resubmit for Rejected content, but hides direct Publish and Approve', () => {
				const actions = computeContentReleaseActions({
					releaseMode: mode,
					releaseStatus: 'Rejected',
					isApprover: false,
					canManage: true,
					contentExists: true,
				})

				expect(actions.canSubmit).toBe(true)
				expect(actions.submitLabel).toBe('Resubmit for Approval')
				expect(actions.canPublish).toBe(false)
				expect(actions.canApprove).toBe(false)
			})

			it('hides Publish, Submit, and Approve when content is Pending Principal Approval', () => {
				const actions = computeContentReleaseActions({
					releaseMode: mode,
					releaseStatus: 'Pending Principal Approval',
					isApprover: false,
					canManage: true,
					contentExists: true,
				})

				expect(actions.canPublish).toBe(false)
				expect(actions.canSubmit).toBe(false)
				expect(actions.canApprove).toBe(false)
				expect(actions.canReject).toBe(false)
			})

			it('hides all release and approval buttons when content is Released with no edits', () => {
				const actions = computeContentReleaseActions({
					releaseMode: mode,
					releaseStatus: 'Released',
					hasUnreleasedEdits: false,
					isApprover: false,
					canManage: true,
					contentExists: true,
				})

				expect(actions.canPublish).toBe(false)
				expect(actions.canSubmit).toBe(false)
				expect(actions.canApprove).toBe(false)
				expect(actions.canReject).toBe(false)
			})

			it('shows Submit for Released content when unreleased edits exist', () => {
				const actions = computeContentReleaseActions({
					releaseMode: mode,
					releaseStatus: 'Released',
					hasUnreleasedEdits: true,
					isApprover: false,
					canManage: true,
					contentExists: true,
				})

				expect(actions.canSubmit).toBe(true)
				expect(actions.canPublish).toBe(false)
				expect(actions.canApprove).toBe(false)
			})
		})

		describe('Principal / Authorized Approver', () => {
			it('never shows Publish New Content to Students in this mode', () => {
				const actionsDraft = computeContentReleaseActions({
					releaseMode: mode,
					releaseStatus: 'Draft',
					isApprover: true,
					canManage: true,
					contentExists: true,
				})
				expect(actionsDraft.canPublish).toBe(false)

				const actionsPending = computeContentReleaseActions({
					releaseMode: mode,
					releaseStatus: 'Pending Principal Approval',
					isApprover: true,
					canManage: true,
					contentExists: true,
				})
				expect(actionsPending.canPublish).toBe(false)
			})

			it('shows Approve and Publish and Reject ONLY when status is Pending Principal Approval', () => {
				const actions = computeContentReleaseActions({
					releaseMode: mode,
					releaseStatus: 'Pending Principal Approval',
					isApprover: true,
					canManage: true,
					contentExists: true,
				})

				expect(actions.canApprove).toBe(true)
				expect(actions.canReject).toBe(true)
				expect(actions.canPublish).toBe(false)
			})

			it('does NOT show Approve and Publish for Draft content that has not been submitted', () => {
				const actions = computeContentReleaseActions({
					releaseMode: mode,
					releaseStatus: 'Draft',
					isApprover: true,
					canManage: true,
					contentExists: true,
				})

				expect(actions.canApprove).toBe(false)
				expect(actions.canReject).toBe(false)
			})

			it('does NOT show Approve and Publish for Rejected or Released content', () => {
				const actionsRejected = computeContentReleaseActions({
					releaseMode: mode,
					releaseStatus: 'Rejected',
					isApprover: true,
					canManage: true,
					contentExists: true,
				})
				expect(actionsRejected.canApprove).toBe(false)

				const actionsReleased = computeContentReleaseActions({
					releaseMode: mode,
					releaseStatus: 'Released',
					isApprover: true,
					canManage: true,
					contentExists: true,
				})
				expect(actionsReleased.canApprove).toBe(false)
			})
		})

		describe('Administrator', () => {
			it('when NOT explicitly authorized as approver, cannot see Approve or Reject', () => {
				const actions = computeContentReleaseActions({
					releaseMode: mode,
					releaseStatus: 'Pending Principal Approval',
					isApprover: false, // Admin without Principal
					canManage: true,
					contentExists: true,
				})

				expect(actions.canApprove).toBe(false)
				expect(actions.canReject).toBe(false)
				expect(actions.canPublish).toBe(false)
			})

			it('when explicitly authorized, sees Approve ONLY for pending, never direct publish', () => {
				const actions = computeContentReleaseActions({
					releaseMode: mode,
					releaseStatus: 'Pending Principal Approval',
					isApprover: true, // Admin WITH Principal
					canManage: true,
					contentExists: true,
				})

				expect(actions.canApprove).toBe(true)
				expect(actions.canReject).toBe(true)
				expect(actions.canPublish).toBe(false) // Direct publish is never shown
			})
		})
	})

	describe('Mode B: Teacher Can Publish', () => {
		const mode = 'Teacher Can Publish'

		it('shows Publish New Content to Students for ready content, hides Submit and Approve', () => {
			const actions = computeContentReleaseActions({
				releaseMode: mode,
				releaseStatus: 'Draft',
				isApprover: false,
				canManage: true,
				contentExists: true,
			})

			expect(actions.canSaveDraft).toBe(true)
			expect(actions.canPreview).toBe(true)
			expect(actions.canPublish).toBe(true)
			expect(actions.canSubmit).toBe(false)
			expect(actions.canApprove).toBe(false)
			expect(actions.canReject).toBe(false)
		})

		it('hides Approve and Publish even for a Principal in Teacher Can Publish mode', () => {
			const actions = computeContentReleaseActions({
				releaseMode: mode,
				releaseStatus: 'Draft',
				isApprover: true,
				canManage: true,
				contentExists: true,
			})

			expect(actions.canPublish).toBe(true)
			expect(actions.canSubmit).toBe(false)
			expect(actions.canApprove).toBe(false)
		})
	})

	describe('Mode C: Teacher Choice', () => {
		const mode = 'Teacher Choice'

		it('shows both Publish New Content and Submit for Principal Approval to teachers for draft content', () => {
			const actions = computeContentReleaseActions({
				releaseMode: mode,
				releaseStatus: 'Draft',
				isApprover: false,
				canManage: true,
				contentExists: true,
			})

			expect(actions.canPublish).toBe(true)
			expect(actions.canSubmit).toBe(true)
			expect(actions.canApprove).toBe(false)
		})

		it('once submitted (Pending Principal Approval), teacher cannot publish or approve', () => {
			const actions = computeContentReleaseActions({
				releaseMode: mode,
				releaseStatus: 'Pending Principal Approval',
				isApprover: false,
				canManage: true,
				contentExists: true,
			})

			expect(actions.canPublish).toBe(false)
			expect(actions.canSubmit).toBe(false)
			expect(actions.canApprove).toBe(false)
		})

		it('principal sees Approve and Publish only for pending content, not draft content', () => {
			const actionsDraft = computeContentReleaseActions({
				releaseMode: mode,
				releaseStatus: 'Draft',
				isApprover: true,
				canManage: true,
				contentExists: true,
			})
			expect(actionsDraft.canApprove).toBe(false)

			const actionsPending = computeContentReleaseActions({
				releaseMode: mode,
				releaseStatus: 'Pending Principal Approval',
				isApprover: true,
				canManage: true,
				contentExists: true,
			})
			expect(actionsPending.canApprove).toBe(true)
			expect(actionsPending.canReject).toBe(true)
			expect(actionsPending.canPublish).toBe(false)
		})
	})

	describe('Batch Release Actions (Course Outline & Batch Assessments)', () => {
		it('in Principal Approval Required, hides Publish, shows Submit for drafts, shows Approve only when pending > 0', () => {
			const teacherActions = computeBatchReleaseActions({
				releaseMode: 'Principal Approval Required',
				draftCount: 2,
				pendingCount: 0,
				rejectedCount: 0,
				isApprover: false,
				canManage: true,
			})
			expect(teacherActions.canPublish).toBe(false)
			expect(teacherActions.canSubmit).toBe(true)
			expect(teacherActions.canApprove).toBe(false)

			const approverActionsPending = computeBatchReleaseActions({
				releaseMode: 'Principal Approval Required',
				draftCount: 0,
				pendingCount: 2,
				rejectedCount: 0,
				isApprover: true,
				canManage: true,
			})
			expect(approverActionsPending.canPublish).toBe(false)
			expect(approverActionsPending.canApprove).toBe(true)
			expect(approverActionsPending.canReject).toBe(true)

			const approverActionsNoPending = computeBatchReleaseActions({
				releaseMode: 'Principal Approval Required',
				draftCount: 2,
				pendingCount: 0,
				rejectedCount: 0,
				isApprover: true,
				canManage: true,
			})
			expect(approverActionsNoPending.canPublish).toBe(false)
			expect(approverActionsNoPending.canApprove).toBe(false)
		})

		it('in Teacher Can Publish, shows Publish for drafts, hides Submit and Approve', () => {
			const actions = computeBatchReleaseActions({
				releaseMode: 'Teacher Can Publish',
				draftCount: 3,
				pendingCount: 0,
				rejectedCount: 0,
				isApprover: false,
				canManage: true,
			})
			expect(actions.canPublish).toBe(true)
			expect(actions.canSubmit).toBe(false)
			expect(actions.canApprove).toBe(false)
		})

		it('in Teacher Choice, shows both Publish and Submit when drafts exist', () => {
			const actions = computeBatchReleaseActions({
				releaseMode: 'Teacher Choice',
				draftCount: 3,
				pendingCount: 1,
				rejectedCount: 0,
				isApprover: true,
				canManage: true,
			})
			expect(actions.canPublish).toBe(true)
			expect(actions.canSubmit).toBe(true)
			expect(actions.canApprove).toBe(true)
		})
	})
})
