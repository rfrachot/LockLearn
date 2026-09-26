export const FRONTEND_PROTOCOL_VERSION = 3;

export type ProfileRole = "owner" | "editor" | "viewer";

export interface BootstrapResponse {
  frontend_protocol: number;
  backend_version: string;
  panel_path: string;
  authenticated_user_id: string;
  personal_profile: VisibleProfile | null;
}

export interface VisibleProfile {
  profile_id: string;
  name: string;
  preset: string;
  timezone: string;
  status: string;
  role: ProfileRole;
  settings?: Record<string, unknown>;
}

export interface Page<T> {
  items: T[];
  cursor: string | null;
}

export interface HomeAssistantLike {
  callWS<T>(message: Record<string, unknown>): Promise<T>;
  language?: string;
  locale?: {
    language?: string;
  };
}

export class ProtocolMismatchError extends Error {
  constructor(
    public readonly frontendProtocol: number,
    public readonly backendProtocol: number,
    public readonly backendVersion: string,
  ) {
    super(
      `LockLearn frontend protocol ${frontendProtocol} does not match backend protocol ${backendProtocol}`,
    );
  }
}

export async function bootstrap(
  hass: HomeAssistantLike,
): Promise<BootstrapResponse> {
  const result = await hass.callWS<BootstrapResponse>({
    type: "locklearn/bootstrap",
  });
  if (result.frontend_protocol !== FRONTEND_PROTOCOL_VERSION) {
    throw new ProtocolMismatchError(
      FRONTEND_PROTOCOL_VERSION,
      result.frontend_protocol,
      result.backend_version,
    );
  }
  return result;
}

export async function listVisibleProfiles(
  hass: HomeAssistantLike,
): Promise<VisibleProfile[]> {
  const profiles: VisibleProfile[] = [];
  let cursor: string | null = null;
  do {
    const page: Page<VisibleProfile> = await hass.callWS<Page<VisibleProfile>>({
      type: "locklearn/profiles/list",
      limit: 100,
      ...(cursor === null ? {} : { cursor }),
    });
    profiles.push(...page.items);
    cursor = page.cursor;
  } while (cursor !== null);
  return profiles;
}


export interface ProfileMember {
  ha_user_id: string;
  name: string;
  role: ProfileRole;
  created_at_utc: string;
}

export interface ShareTarget {
  ha_user_id: string;
  name: string;
}

export interface TrackRecord {
  track_id: string;
  profile_id: string;
  name: string;
  source_language: string | null;
  target_language: string | null;
  status: "active" | "paused" | "archived";
  priority: number;
  settings: Record<string, unknown>;
  pack_version_id: string | null;
  dataset_generation: string | null;
  integrated_at_utc: string | null;
}

export interface PackVersionRecord {
  pack_id: string;
  name: string;
  pack_version_id: string;
  version: string;
  curation_policy_id: string | null;
  generation_id: string;
  total_items: number;
  total_cards: number;
}

export interface PackVersionDiff {
  from_pack_version_id: string;
  to_pack_version_id: string;
  added_learning_item_ids: string[];
  removed_learning_item_ids: string[];
  changed_learning_item_ids: string[];
}

export interface LearningPlanInput {
  max_new_per_day_cards: number;
  max_reviews_per_day_cards: number;
  max_notification_new_teasers: number;
  target_date: string | null;
  target_coverage: number;
  target_retention: number;
}

export interface LoadForecast {
  selected_cards: number;
  introduced_cards: number;
  target_cards: number;
  remaining_target_cards: number;
  required_new_per_day: number;
  planned_new_per_day: number;
  reviews_per_day_in_3_weeks: number;
  reviews_per_day_in_3_months: number;
  due_now: number;
  notification_deliverable_in_3_weeks: number;
  active_session_cards_in_3_weeks: number;
  notification_deliverable_in_3_months: number;
  active_session_cards_in_3_months: number;
  target_date_feasible: boolean;
  review_capacity_feasible_in_3_weeks: boolean;
  review_capacity_feasible_in_3_months: boolean;
  warnings: string[];
  assumptions: string[];
}

async function listPaged<T>(
  hass: HomeAssistantLike,
  type: string,
  extra: Record<string, unknown> = {},
): Promise<T[]> {
  const items: T[] = [];
  let cursor: string | null = null;
  do {
    const page: Page<T> = await hass.callWS<Page<T>>({
      type,
      limit: 100,
      ...extra,
      ...(cursor === null ? {} : { cursor }),
    });
    items.push(...page.items);
    cursor = page.cursor;
  } while (cursor !== null);
  return items;
}

export async function createProfile(
  hass: HomeAssistantLike,
  name: string,
  preset: "child" | "standard" | "intensive" | "custom",
  timezone: string,
): Promise<VisibleProfile> {
  return hass.callWS<VisibleProfile>({
    type: "locklearn/profiles/create",
    name,
    preset,
    timezone,
  });
}

export async function updateProfile(
  hass: HomeAssistantLike,
  profileId: string,
  patch: {
    name?: string;
    timezone?: string;
    status?: "active" | "archived";
    settings_patch?: Record<string, unknown>;
  },
): Promise<VisibleProfile> {
  return hass.callWS<VisibleProfile>({
    type: "locklearn/profiles/update",
    profile_id: profileId,
    ...patch,
  });
}

export async function deleteProfile(
  hass: HomeAssistantLike,
  profileId: string,
): Promise<void> {
  await hass.callWS({
    type: "locklearn/profiles/delete",
    profile_id: profileId,
  });
}

export async function listProfileMembers(
  hass: HomeAssistantLike,
  profileId: string,
): Promise<ProfileMember[]> {
  return hass.callWS<ProfileMember[]>({
    type: "locklearn/profiles/members",
    profile_id: profileId,
  });
}

export async function listShareTargets(
  hass: HomeAssistantLike,
  profileId: string,
): Promise<ShareTarget[]> {
  return hass.callWS<ShareTarget[]>({
    type: "locklearn/profiles/share_targets",
    profile_id: profileId,
  });
}

export async function shareProfile(
  hass: HomeAssistantLike,
  profileId: string,
  targetUserId: string,
  role: ProfileRole,
): Promise<void> {
  await hass.callWS({
    type: "locklearn/profiles/share",
    profile_id: profileId,
    target_user_id: targetUserId,
    role,
  });
}

export async function removeProfileMember(
  hass: HomeAssistantLike,
  profileId: string,
  targetUserId: string,
): Promise<void> {
  await hass.callWS({
    type: "locklearn/profiles/share",
    profile_id: profileId,
    target_user_id: targetUserId,
    remove: true,
  });
}

export async function listTracks(
  hass: HomeAssistantLike,
  profileId: string,
): Promise<TrackRecord[]> {
  return listPaged<TrackRecord>(hass, "locklearn/tracks/list", {
    profile_id: profileId,
  });
}

export async function createTrack(
  hass: HomeAssistantLike,
  input: {
    profile_id: string;
    name: string;
    pack_version_id: string;
    source_language: string;
    target_language: string;
    priority: number;
  },
): Promise<TrackRecord> {
  return hass.callWS<TrackRecord>({
    type: "locklearn/tracks/create",
    ...input,
  });
}

export async function updateTrack(
  hass: HomeAssistantLike,
  trackId: string,
  patch: Record<string, unknown>,
): Promise<TrackRecord> {
  return hass.callWS<TrackRecord>({
    type: "locklearn/tracks/update",
    track_id: trackId,
    ...patch,
  });
}

export async function deleteTrack(
  hass: HomeAssistantLike,
  trackId: string,
): Promise<void> {
  await hass.callWS({
    type: "locklearn/tracks/delete",
    track_id: trackId,
  });
}

export async function listPacks(
  hass: HomeAssistantLike,
): Promise<PackVersionRecord[]> {
  return listPaged<PackVersionRecord>(hass, "locklearn/packs/list");
}

export async function previewPackUpdate(
  hass: HomeAssistantLike,
  trackId: string,
  packVersionId: string,
): Promise<PackVersionDiff> {
  return hass.callWS<PackVersionDiff>({
    type: "locklearn/tracks/preview_pack_update",
    track_id: trackId,
    pack_version_id: packVersionId,
  });
}

export async function integratePackUpdate(
  hass: HomeAssistantLike,
  trackId: string,
  packVersionId: string,
): Promise<PackVersionDiff> {
  return hass.callWS<PackVersionDiff>({
    type: "locklearn/tracks/integrate_pack_update",
    track_id: trackId,
    pack_version_id: packVersionId,
  });
}

function planMessage(
  type: "locklearn/tracks/plan_preview" | "locklearn/tracks/plan_set",
  trackId: string,
  plan: LearningPlanInput,
): Record<string, unknown> {
  return {
    type,
    track_id: trackId,
    ...plan,
  };
}

export async function previewTrackPlan(
  hass: HomeAssistantLike,
  trackId: string,
  plan: LearningPlanInput,
): Promise<LoadForecast> {
  return hass.callWS<LoadForecast>(
    planMessage("locklearn/tracks/plan_preview", trackId, plan),
  );
}

export async function setTrackPlan(
  hass: HomeAssistantLike,
  trackId: string,
  plan: LearningPlanInput,
): Promise<LoadForecast> {
  return hass.callWS<LoadForecast>(
    planMessage("locklearn/tracks/plan_set", trackId, plan),
  );
}


export interface DashboardRetention {
  retained: boolean;
  created_at_utc: string;
}

export interface DashboardAccuracy {
  correct: number;
  total: number;
  accuracy: number | null;
}

export interface DashboardSession {
  session_id: string;
  session_type: string;
  status: string;
  question_count: number;
  answered_count: number;
  started_at_utc: string;
  last_activity_at_utc: string;
  completed_at_utc: string | null;
}

export interface DashboardNotification {
  slot_type: string;
  status: string;
  effective_for_utc: string;
}

export interface DashboardTrack {
  track_id: string;
  name: string;
  source_language: string;
  target_language: string;
  due_today: number;
  recent_verified_retention: DashboardRetention | null;
  recent_verified_accuracy: DashboardAccuracy;
  states: Record<string, number>;
  last_session: DashboardSession | null;
  next_notification: DashboardNotification | null;
}

export interface DashboardResponse {
  profile: {
    profile_id: string;
    name: string;
    preset: string;
    timezone: string;
  };
  generated_at_utc: string;
  tracks: DashboardTrack[];
}

export async function getDashboard(
  hass: HomeAssistantLike,
  profileId: string,
): Promise<DashboardResponse> {
  return hass.callWS<DashboardResponse>({
    type: "locklearn/dashboard/get",
    profile_id: profileId,
  });
}


export interface LearnContentBlock {
  content_block_id: string;
  position: number;
  kind: string;
  role: string;
  reveals_answer: boolean;
  mask_strategy: string;
  payload: Record<string, unknown>;
  language_tag?: string;
  script?: string | null;
}

export interface LearnFacetPresentation {
  facet_id: string;
  kind: string;
  facet_key: string;
  language_tag: string;
  script: string | null;
  blocks: LearnContentBlock[];
}

export interface LearnCardPresentation {
  card_key: string;
  learning_item_id: string;
  content_type: string;
  prompt: LearnFacetPresentation;
  answer: LearnFacetPresentation;
  context: LearnFacetPresentation[];
  introduction_blocks: LearnContentBlock[];
  hint_blocks: LearnContentBlock[];
  mnemonic_blocks: LearnContentBlock[];
  example_blocks: LearnContentBlock[];
}

export interface SessionQuestion {
  position: number;
  question_id: string;
  card_key: string;
  learning_item_id: string;
  prompt_facet_id: string;
  answer_facet_id: string;
  status: string;
  payload: {
    selection?: {
      content_type?: string;
      progress_state?: string;
      reason?: string;
      pack_position?: number;
      content_weight?: number;
    };
    presentation?: LearnCardPresentation;
    quiz?: QuizQuestionPayload;
    [key: string]: unknown;
  };
}

export interface SessionState {
  id: string;
  profile_id: string;
  track_id: string | null;
  type: string;
  strategy: string;
  status: string;
  version: number;
  current_position: number;
  started_at_utc: string;
  last_activity_at_utc: string;
  completed_at_utc: string | null;
  question_count: number;
  settings: Record<string, unknown>;
  items: SessionQuestion[];
  answers: Array<{
    id: number;
    question_id: string;
    answer: unknown;
    resulting_version: number;
    created_at_utc: string;
  }>;
  current_question: SessionQuestion | null;
  fatigue_advice?: Record<string, unknown>;
}


export type QuizFormat = "mixed" | "mcq" | "free_text" | "cloze_mcq";

export interface QuizOption {
  answer_id: string;
  text: string;
}

export interface QuizQuestionPayload {
  format: Exclude<QuizFormat, "mixed">;
  prompt_text: string;
  context_hint: string | null;
  options: QuizOption[];
  idk_available: boolean;
  reportable: boolean;
  hint_blocks: LearnContentBlock[];
  content_type: string;
}

export interface QuizFeedback {
  format: Exclude<QuizFormat, "mixed">;
  result: "correct" | "wrong" | "idk" | "unrecognized";
  immediate: boolean;
  reveal_correct_answer: boolean;
  correct_answer: string | null;
  contrastive_feedback: string | null;
  selected_answer_id?: string | null;
  selected_answer?: string | null;
  submitted_text?: string | null;
  normalized_submission?: string | null;
  reportable: boolean;
  grading_policy_kind?: "exact" | "any_of" | "fuzzy_normalized";
  grading_policy_version?: number;
  normalization_version?: number;
  grading_reason?: string;
  hint_used: boolean;
  presentation_to_answer_ms?: number | null;
}

export async function startQuizSession(
  hass: HomeAssistantLike,
  profileId: string,
  trackId: string,
  requestedCards = 10,
  quizFormat: QuizFormat = "mixed",
): Promise<SessionState> {
  return hass.callWS<SessionState>({
    type: "locklearn/session/start",
    profile_id: profileId,
    track_id: trackId,
    session_type: "quiz",
    strategy: "default",
    settings: {
      requested_cards: requestedCards,
      quiz_format: quizFormat,
      option_count: 4,
    },
  });
}


export interface QuizAnswerResponse {
  feedback: QuizFeedback;
  session: SessionState;
}

export async function submitQuizAnswer(
  hass: HomeAssistantLike,
  session: SessionState,
  questionId: string,
  answer: Record<string, unknown>,
): Promise<QuizAnswerResponse> {
  return hass.callWS<QuizAnswerResponse>({
    type: "locklearn/quiz/answer",
    session_id: session.id,
    expected_version: session.version,
    question_id: questionId,
    answer,
  });
}

export async function evaluateQuizAnswer(
  hass: HomeAssistantLike,
  sessionId: string,
  questionId: string,
  answer: Record<string, unknown>,
): Promise<QuizFeedback> {
  return hass.callWS<QuizFeedback>({
    type: "locklearn/quiz/evaluate",
    session_id: sessionId,
    question_id: questionId,
    answer,
  });
}

export async function reportFreeTextShouldBeAccepted(
  hass: HomeAssistantLike,
  profileId: string,
  trackId: string,
  question: SessionQuestion,
  feedback: QuizFeedback,
): Promise<{ report_id: number; grading_result: string; srs_penalized: boolean }> {
  if (
    typeof feedback.submitted_text !== "string" ||
    feedback.grading_policy_kind === undefined ||
    feedback.grading_policy_version === undefined ||
    feedback.normalization_version === undefined
  ) {
    throw new Error("free-text report metadata is incomplete");
  }
  return hass.callWS({
    type: "locklearn/content/report",
    profile_id: profileId,
    track_id: trackId,
    card_key: question.card_key,
    learning_item_id: question.learning_item_id,
    prompt_facet_id: question.prompt_facet_id,
    answer_facet_id: question.answer_facet_id,
    submitted_text: feedback.submitted_text,
    normalized_submission: feedback.normalized_submission ?? null,
    grading_policy_kind: feedback.grading_policy_kind,
    grading_policy_version: feedback.grading_policy_version,
    normalization_version: feedback.normalization_version,
  });
}

export async function startLearnSession(
  hass: HomeAssistantLike,
  profileId: string,
  trackId: string,
  requestedCards = 20,
): Promise<SessionState> {
  return hass.callWS<SessionState>({
    type: "locklearn/session/start",
    profile_id: profileId,
    track_id: trackId,
    session_type: "learn",
    strategy: "default",
    settings: { requested_cards: requestedCards },
  });
}

export async function getSession(
  hass: HomeAssistantLike,
  sessionId: string,
): Promise<SessionState> {
  return hass.callWS<SessionState>({
    type: "locklearn/session/get",
    session_id: sessionId,
  });
}

export async function answerSession(
  hass: HomeAssistantLike,
  session: SessionState,
  questionId: string,
  answer: Record<string, unknown>,
): Promise<SessionState> {
  return hass.callWS<SessionState>({
    type: "locklearn/session/answer",
    session_id: session.id,
    expected_version: session.version,
    question_id: questionId,
    answer,
  });
}

export async function completeSession(
  hass: HomeAssistantLike,
  session: SessionState,
): Promise<SessionState> {
  return hass.callWS<SessionState>({
    type: "locklearn/session/complete",
    session_id: session.id,
    expected_version: session.version,
  });
}

export async function setCardUserState(
  hass: HomeAssistantLike,
  profileId: string,
  trackId: string,
  cardKey: string,
  userState: "known_already" | "suspended",
): Promise<Record<string, unknown>> {
  return hass.callWS<Record<string, unknown>>({
    type: "locklearn/progress/set_user_state",
    profile_id: profileId,
    track_id: trackId,
    card_key: cardKey,
    user_state: userState,
  });
}

export async function reportQuestion(
  hass: HomeAssistantLike,
  profileId: string,
  trackId: string,
  question: SessionQuestion,
  message?: string,
): Promise<{ report_id: number; srs_penalized: boolean }> {
  return hass.callWS({
    type: "locklearn/content/report_question",
    profile_id: profileId,
    track_id: trackId,
    card_key: question.card_key,
    learning_item_id: question.learning_item_id,
    prompt_facet_id: question.prompt_facet_id,
    answer_facet_id: question.answer_facet_id,
    reason: "user_reported_question",
    ...(message === undefined || message.trim() === "" ? {} : { message: message.trim() }),
  });
}

export async function createCardAnnotation(
  hass: HomeAssistantLike,
  profileId: string,
  cardKey: string,
  note: string,
): Promise<Record<string, unknown>> {
  return hass.callWS<Record<string, unknown>>({
    type: "locklearn/annotations/create",
    profile_id: profileId,
    card_key: cardKey,
    note: note.trim(),
  });
}
