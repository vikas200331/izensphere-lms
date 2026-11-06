// Centralized content release mode and workflow action visibility logic
// Supports modes: 'None', 'Teacher Can Publish', 'Principal Approval Required', 'Teacher Choice'

export type ReleaseMode =
	| 'None'
	| 'Teacher Can Publish'
	| 'Principal Approval Required'
	| 'Teacher Choice'

export type ReleaseStatus =
	| 'Draft'
	| 'Pending Principal Approval'
	| 'Released'
	| 'Rejected'

export interface ReleaseActionOptions {
	releaseMode?: string | null
	releaseStatus?: string | null
	hasUnreleasedEdits?: boolean
	isApprover?: boolean
	canManage?: boolean
	isDirty?: boolean
	contentExists?: boolean
}

/**
 * Returns true if the user is explicitly authorized as a Principal / Approver.
 * Note: An Administrator or System Manager is NOT an authorized approver unless
 * the account is explicitly granted the Principal role.
 */
export function isAuthorizedApprover(user: any): boolean {
	if (!user) return false
	const data = user.data || user
	if (data.is_principal) return true
	const roles: string[] = data.roles || []
	return roles.includes('Principal')
}

/**
 * Computes individual content item release actions (used in LessonForm, QuizForm, etc.)
 */
export function computeContentReleaseActions(options: ReleaseActionOptions) {
	const mode = (options.releaseMode || 'None') as ReleaseMode
	const status = (options.releaseStatus || 'Draft') as ReleaseStatus
	const hasEdits = Boolean(options.hasUnreleasedEdits)
	const isApprover = Boolean(options.isApprover)
	const canManage = Boolean(options.canManage)
	const isDirty = Boolean(options.isDirty)
	const contentExists =
		options.contentExists !== undefined ? Boolean(options.contentExists) : true

	// Content has pending/staged changes if it is in Draft, Rejected, or has unreleased edits on a Released item
	const isStaged = status === 'Draft' || status === 'Rejected' || hasEdits

	// 1. Save Draft:
	// Shown to authorized managers when content has pending edits or form is dirty.
	const canSaveDraft = canManage && (isStaged || isDirty)

	// 2. Preview Content:
	// Shown when content exists / has been created.
	const canPreview = contentExists

	// 3. Publish New Content to Students:
	// - Mode A (Principal Approval Required): NEVER shown to anyone (teacher, principal, admin).
	// - Mode B (Teacher Can Publish): Shown to managers when content is ready (Draft, Rejected, edits).
	// - Mode C (Teacher Choice): Shown to managers when Draft, Rejected, or has edits.
	// - If content is 'Pending Principal Approval': CANNOT directly publish (must wait for review).
	// - If content is 'Released' with no edits: CANNOT publish (already published).
	const canPublish =
		canManage &&
		mode !== 'Principal Approval Required' &&
		mode !== 'None' &&
		(mode === 'Teacher Can Publish' || mode === 'Teacher Choice') &&
		isStaged &&
		status !== 'Pending Principal Approval'

	// 4. Submit for Principal Approval / Resubmit:
	// - Mode A (Principal Approval Required): Shown to managers when Draft, Rejected, or has edits.
	// - Mode B (Teacher Can Publish): NEVER shown (approval not used).
	// - Mode C (Teacher Choice): Shown to managers when Draft, Rejected, or has edits.
	// - If content is already 'Pending Principal Approval': hidden (already submitted).
	// - If content is 'Released' without edits: hidden.
	const canSubmit =
		canManage &&
		mode !== 'Teacher Can Publish' &&
		mode !== 'None' &&
		(mode === 'Principal Approval Required' || mode === 'Teacher Choice') &&
		isStaged &&
		status !== 'Pending Principal Approval'

	const submitLabel =
		status === 'Rejected' ? 'Resubmit for Approval' : 'Submit for Principal Approval'

	// 5. Approve and Publish:
	// - Shown ONLY to authorized approver (Principal).
	// - Shown ONLY when content status is 'Pending Principal Approval'.
	// - NEVER shown for Draft, Rejected, or already published content!
	// - NEVER shown in 'Teacher Can Publish' or 'None' mode!
	const canApprove =
		isApprover &&
		status === 'Pending Principal Approval' &&
		(mode === 'Principal Approval Required' || mode === 'Teacher Choice')

	// 6. Reject / Request Changes:
	// - Shown ONLY to authorized approver (Principal).
	// - Shown ONLY when content status is 'Pending Principal Approval'.
	// - NEVER shown for Draft, Rejected, or already published content!
	const canReject =
		isApprover &&
		status === 'Pending Principal Approval' &&
		(mode === 'Principal Approval Required' || mode === 'Teacher Choice')

	return {
		canSaveDraft,
		canPreview,
		canPublish,
		canSubmit,
		submitLabel,
		canApprove,
		canReject,
	}
}

export interface BatchReleaseActionOptions {
	releaseMode?: string | null
	draftCount?: number
	pendingCount?: number
	rejectedCount?: number
	isApprover?: boolean
	canManage?: boolean
	hasContainer?: boolean
}

/**
 * Computes batch release actions for Course Outline and Batch Assessments.
 */
export function computeBatchReleaseActions(options: BatchReleaseActionOptions) {
	const mode = (options.releaseMode || 'None') as ReleaseMode
	const draftCount = options.draftCount ?? 0
	const pendingCount = options.pendingCount ?? 0
	const rejectedCount = options.rejectedCount ?? 0
	const isApprover = Boolean(options.isApprover)
	const canManage = Boolean(options.canManage)
	const hasContainer =
		options.hasContainer !== undefined ? Boolean(options.hasContainer) : true

	const hasDraftOrRejected = draftCount > 0 || rejectedCount > 0

	// 1. Publish New Content to Students:
	// NEVER shown in 'Principal Approval Required' mode!
	const canPublish =
		canManage &&
		mode !== 'Principal Approval Required' &&
		mode !== 'None' &&
		(mode === 'Teacher Can Publish' || mode === 'Teacher Choice') &&
		hasDraftOrRejected

	// 2. Submit for Principal Approval:
	// NEVER shown in 'Teacher Can Publish' mode!
	const canSubmit =
		canManage &&
		mode !== 'Teacher Can Publish' &&
		mode !== 'None' &&
		(mode === 'Principal Approval Required' || mode === 'Teacher Choice') &&
		hasDraftOrRejected

	const submitLabel =
		rejectedCount > 0 && !draftCount
			? 'Resubmit for Approval'
			: 'Submit for Principal Approval'

	const canPreview = hasContainer

	// 3. Approve and Publish:
	// Shown ONLY to authorized approvers, ONLY when pending submissions exist (pendingCount > 0).
	const canApprove =
		isApprover &&
		pendingCount > 0 &&
		(mode === 'Principal Approval Required' || mode === 'Teacher Choice')

	// 4. Reject / Request Changes:
	const canReject =
		isApprover &&
		pendingCount > 0 &&
		(mode === 'Principal Approval Required' || mode === 'Teacher Choice')

	return {
		canPublish,
		canSubmit,
		submitLabel,
		canPreview,
		canApprove,
		canReject,
	}
}
