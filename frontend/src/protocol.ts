export const FRONTEND_PROTOCOL_VERSION = 3;

export type ProfileRole = "owner" | "editor" | "viewer";

export interface BootstrapResponse {
  frontend_protocol: number;
  backend_version: string;
  panel_path: string;
  authenticated_user_id: string;
  is_admin: boolean;
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
  content_weights: Record<string, number>;
}

export interface NotificationTargetSummary {
  target_id: string;
  profile_id: string;
  device_registry_id: string;
  friendly_name: string;
  platform: string;
  capabilities: Record<string, unknown>;
  shared_device: boolean;
  lockscreen_visibility: "public" | "private" | "secret";
  enabled: boolean;
  minimum_gap_seconds: number | null;
  maximum_notifications_per_hour: number | null;
  daily_push_budget: number | null;
}

export interface NotificationTargetCandidate {
  device_registry_id: string;
  friendly_name: string;
  platform: string;
  route_available: boolean;
  supports_platform_data: boolean;
  configured_target_id: string | null;
}

export interface NotificationTargetPatch {
  friendly_name?: string;
  shared_device?: boolean;
  lockscreen_visibility?: "public" | "private" | "secret";
  enabled?: boolean;
  minimum_gap_seconds?: number | null;
  maximum_notifications_per_hour?: number | null;
  daily_push_budget?: number | null;
}

export interface PackDirection {
  source_language: string;
  target_language: string;
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
  directions: PackDirection[];
}

export interface PackVersionDiff {
  from_pack_version_id: string;
  to_pack_version_id: string;
  added_learning_item_ids: string[];
  removed_learning_item_ids: string[];
  changed_learning_item_ids: string[];
}

export interface DatasetSourceRecord {
  source_id: string;
  name: string;
  provider: string;
  homepage: string;
  license_id: string;
  attribution_template: string;
  adapter_id: string;
  refresh_policy: string;
  commercial_compatible: boolean;
  notes: string;
  upstream_version: string;
  upstream_date: string | null;
  retrieved_at: string;
  source_url: string;
  adapter_version: string;
  provenance_records: number;
  modified_records: number;
  attribution_records: number;
}

export interface DatasetAttributionRecord {
  source_record_id: string | null;
  author: string | null;
  language_tag: string | null;
  modified_from_source: boolean;
  attribution_text: string;
  license_id: string;
  license_scope: string;
}

export interface DatasetLicenseRecord {
  license_id: string;
  license_scope: string;
  spdx_or_internal_id: string;
  name: string;
  version: string;
  commercial_use_allowed: boolean;
  derivatives_allowed: boolean;
  share_alike: boolean;
  attribution_required: boolean;
  source_url: string;
  notes: string;
}

export interface DatasetStatusRecord {
  dataset_id: string;
  name: string;
  state: "error" | "update_available" | "installed" | "available" | "unknown";
  installed_version: string | null;
  available_version: string | null;
  update_available: boolean;
  source_age_days: number | null;
  stale_sources: string[];
  cache_bytes: number;
  error: string | null;
  changelog: string | null;
  release_url: string | null;
  artifact_size: number | null;
  built_at_utc: string | null;
  dataset_version_id: string | null;
  canonical_content_hash: string | null;
  sources: DatasetSourceRecord[];
  licenses: DatasetLicenseRecord[];
  pack_version_ids: string[];
}

export interface DatasetInstallResult {
  dataset_id: string;
  version: string;
  generation_id: string;
  previous_generation_id: string | null;
  statuses: DatasetStatusRecord[];
}

export interface StatsAccuracy {
  correct: number;
  total: number;
  accuracy: number | null;
  window_limit: number;
}

export interface StatsRetention {
  result: string;
  retained: boolean;
  card_key: string;
  created_at_utc: string;
  local_date: string;
}

export interface StatsStateCounts {
  new: number;
  learning: number;
  review: number;
  relearning: number;
  leech: number;
}

export interface StatsMastery {
  value: number | null;
  card_count: number;
  secondary_indicator: boolean;
}

export interface StatsCalibration {
  window_days: number;
  declared_known_cards: number;
  later_verified_cards: number;
  later_verified_correct: number;
  later_verified_wrong: number;
  later_verified_accuracy: number | null;
  awaiting_verified_followup: number;
}

export interface StatsStreak {
  days: number;
  grace_days: number;
  grace_days_used: number;
  goal_fraction: number;
  goal_minimum_cards: number;
  today: {
    due_opening: number;
    treated_due: number;
    target: number;
    status: "neutral" | "success" | "missed";
    timezone_name?: string;
  };
}

export interface ConfusionRecord {
  card_key: string;
  expected_answer_id: string;
  chosen_answer_id: string;
  count: number;
}

export interface StatsDailyRecord {
  profile_id: string;
  track_id: string;
  local_date: string;
  timezone_name: string;
  utc_offset_minutes: number;
  policy_version: string;
  learning_exposures: number;
  verified_retrievals: number;
  self_known: number;
  verified_correct: number;
  verified_wrong: number;
  quiz_total: number;
  free_text_total: number;
  hints_used: number;
  new_cards: number;
  reviewed_cards: number;
  relearning_cards: number;
  leech_cards: number;
  active_seconds: number;
}

export interface StatsResponse {
  profile_id: string;
  track_id: string | null;
  generated_at_utc: string;
  local_date: string;
  due_today: number;
  states: StatsStateCounts;
  latest_verified_retention: StatsRetention | null;
  recent_verified_accuracy: StatsAccuracy;
  mastery: StatsMastery;
  calibration: StatsCalibration;
  streak: StatsStreak;
  confusions: ConfusionRecord[];
  daily: StatsDailyRecord[];
}

export interface DifficultyAnnotation {
  annotation_id: string;
  profile_id: string;
  learning_item_id: string | null;
  card_key: string | null;
  note: string;
  created_at_utc: string;
  updated_at_utc: string;
}

export interface DifficultyRecord {
  profile_id: string;
  track_id: string;
  card_key: string;
  learning_item_id: string;
  prompt_facet_id: string;
  answer_facet_id: string;
  mastery: number;
  box: number;
  seen_count: number;
  verified_correct_count: number;
  verified_wrong_count: number;
  next_due_at_utc: string | null;
  leech_score: number;
  difficulty_factor: number;
  user_state: string;
  content_status: string;
  policy_version: string;
  updated_at_utc: string;
  confusions: ConfusionRecord[];
  annotations: DifficultyAnnotation[];
  recommended_remediation: "create_personal_mnemonic" | "edit_personal_mnemonic";
  targeted_session_settings: {
    leeches_only: boolean;
    requested_cards: number;
  };
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
  action: "archive" | "delete_permanently",
  confirmation?: string,
): Promise<void> {
  await hass.callWS({
    type: "locklearn/profiles/delete",
    profile_id: profileId,
    action,
    ...(confirmation === undefined ? {} : { confirmation }),
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

export async function listNotificationTargets(
  hass: HomeAssistantLike,
  profileId: string,
): Promise<NotificationTargetSummary[]> {
  return listPaged<NotificationTargetSummary>(hass, "locklearn/targets/list", {
    profile_id: profileId,
  });
}

export async function discoverNotificationTargets(
  hass: HomeAssistantLike,
  profileId: string,
): Promise<NotificationTargetCandidate[]> {
  return listPaged<NotificationTargetCandidate>(hass, "locklearn/targets/discover", {
    profile_id: profileId,
  });
}

export async function createNotificationTarget(
  hass: HomeAssistantLike,
  profileId: string,
  deviceRegistryId: string,
): Promise<NotificationTargetSummary> {
  return hass.callWS<NotificationTargetSummary>({
    type: "locklearn/targets/create",
    profile_id: profileId,
    device_registry_id: deviceRegistryId,
  });
}

export async function updateNotificationTarget(
  hass: HomeAssistantLike,
  profileId: string,
  targetId: string,
  patch: NotificationTargetPatch,
): Promise<NotificationTargetSummary> {
  return hass.callWS<NotificationTargetSummary>({
    type: "locklearn/targets/update",
    profile_id: profileId,
    target_id: targetId,
    ...patch,
  });
}

export async function testNotificationTarget(
  hass: HomeAssistantLike,
  profileId: string,
  targetId: string,
): Promise<{ target_id: string; service: string }> {
  return hass.callWS({
    type: "locklearn/targets/test",
    profile_id: profileId,
    target_id: targetId,
  });
}

export async function getStats(
  hass: HomeAssistantLike,
  profileId: string,
  trackId?: string | null,
): Promise<StatsResponse> {
  return hass.callWS<StatsResponse>({
    type: "locklearn/stats/get",
    profile_id: profileId,
    recent_verified_limit: 30,
    calibration_days: 7,
    confusion_limit: 20,
    ...(trackId ? { track_id: trackId } : {}),
  });
}

export async function listDifficulties(
  hass: HomeAssistantLike,
  profileId: string,
  trackId?: string | null,
): Promise<DifficultyRecord[]> {
  const result = await hass.callWS<{ items: DifficultyRecord[] }>({
    type: "locklearn/difficulties/list",
    profile_id: profileId,
    ...(trackId ? { track_id: trackId } : {}),
  });
  return result.items;
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
    content_weights?: Record<string, number>;
    scheduler_settings?: {
      learning_count: number;
      quiz_count: number;
      target_ids?: string[];
    };
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

export async function listDatasets(
  hass: HomeAssistantLike,
): Promise<DatasetStatusRecord[]> {
  return listPaged<DatasetStatusRecord>(hass, "locklearn/datasets/list");
}

export async function listDatasetAttributions(
  hass: HomeAssistantLike,
  datasetId: string,
  sourceId: string,
  cursor?: string | null,
): Promise<{ items: DatasetAttributionRecord[]; cursor: string | null }> {
  return hass.callWS({
    type: "locklearn/datasets/attributions",
    dataset_id: datasetId,
    source_id: sourceId,
    limit: 50,
    ...(cursor ? { cursor } : {}),
  });
}

export async function refreshDatasets(
  hass: HomeAssistantLike,
): Promise<DatasetStatusRecord[]> {
  const result = await hass.callWS<{ items: DatasetStatusRecord[] }>({
    type: "locklearn/datasets/refresh",
  });
  return result.items;
}

export async function installDataset(
  hass: HomeAssistantLike,
  datasetId: string,
  version?: string | null,
): Promise<DatasetInstallResult> {
  return hass.callWS<DatasetInstallResult>({
    type: "locklearn/datasets/install",
    dataset_id: datasetId,
    ...(version ? { version } : {}),
  });
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
  priority: number;
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
  calibration_summary?: {
    known: number;
    needs_learning: number;
    answered: number;
  };
}


export type AvailabilityBlockerCode =
  | "scheduled_step"
  | "known_already_verification"
  | "new_quota"
  | "sibling_gap"
  | "confusable_gap"
  | "buried"
  | "prerequisite"
  | "suspended";

export interface AvailabilityBlocker {
  code: AvailabilityBlockerCode;
  count: number;
  until_utc: string | null;
  forceable: boolean;
}

export interface SessionAvailability {
  profile_id: string;
  track_id: string;
  session_type: string;
  available_now: number;
  selected_cards: number;
  introduced_cards: number;
  new_cards: number;
  due_now_total: number;
  known_already_cards: number;
  known_already_pending_verification: number;
  suspended_cards: number;
  buried_cards: number;
  temporarily_blocked_cards: number;
  prerequisite_blocked_cards: number;
  session_capacity: number;
  remaining_new_quota: number;
  forceable_new: number;
  forceable_early: number;
  next_due_at_utc: string | null;
  next_available_at_utc: string | null;
  next_available_reason: "scheduled_step" | "known_already_verification" | "new_quota" | null;
  blockers: AvailabilityBlocker[];
}

export async function getSessionAvailability(
  hass: HomeAssistantLike,
  profileId: string,
  trackId: string,
  sessionType: "learn" | "quiz" | "calibration",
  settings: Record<string, unknown> = {},
): Promise<SessionAvailability> {
  return hass.callWS<SessionAvailability>({
    type: "locklearn/session/availability",
    profile_id: profileId,
    track_id: trackId,
    session_type: sessionType,
    settings,
  });
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
  requestedCards?: number,
  quizFormat: QuizFormat = "mixed",
): Promise<SessionState> {
  return hass.callWS<SessionState>({
    type: "locklearn/session/start_v04",
    profile_id: profileId,
    track_id: trackId,
    session_type: "quiz",
    strategy: "default",
    settings: {
      ...(requestedCards === undefined ? {} : { requested_cards: requestedCards }),
      quiz_format: quizFormat,
      option_count: 4,
    },
  });
}


export async function startCalibrationSession(
  hass: HomeAssistantLike,
  profileId: string,
  trackId: string,
  requestedCards = 20,
): Promise<SessionState> {
  return hass.callWS<SessionState>({
    type: "locklearn/session/start_v04",
    profile_id: profileId,
    track_id: trackId,
    session_type: "calibration",
    strategy: "calibration",
    settings: {
      requested_cards: requestedCards,
      quiz_format: "mixed",
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
    type: "locklearn/quiz/answer_v04",
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
  requestedCards?: number,
  allowEarlyLearning = false,
): Promise<SessionState> {
  return hass.callWS<SessionState>({
    type: "locklearn/session/start_v04",
    profile_id: profileId,
    track_id: trackId,
    session_type: "learn",
    strategy: "default",
    settings: {
      ...(requestedCards === undefined ? {} : { requested_cards: requestedCards }),
      ...(allowEarlyLearning ? { allow_early_learning: true } : {}),
    },
  });
}

export interface CalibrationFollowupStatus {
  source_session_id: string | null;
  pending_count: number;
  card_keys: string[];
}

export async function getCalibrationFollowupStatus(
  hass: HomeAssistantLike,
  profileId: string,
  trackId: string,
  calibrationSessionId?: string,
): Promise<CalibrationFollowupStatus> {
  return hass.callWS<CalibrationFollowupStatus>({
    type: "locklearn/calibration/followup/status",
    profile_id: profileId,
    track_id: trackId,
    ...(calibrationSessionId === undefined ? {} : { calibration_session_id: calibrationSessionId }),
  });
}

export async function startCalibrationFollowup(
  hass: HomeAssistantLike,
  profileId: string,
  trackId: string,
  calibrationSessionId: string,
): Promise<SessionState> {
  return hass.callWS<SessionState>({
    type: "locklearn/calibration/followup/start",
    profile_id: profileId,
    track_id: trackId,
    calibration_session_id: calibrationSessionId,
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
    type: "locklearn/session/answer_v04",
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
  userState: "active" | "suspended" | "buried",
): Promise<Record<string, unknown>> {
  return hass.callWS<Record<string, unknown>>({
    type: "locklearn/progress/set_user_state",
    profile_id: profileId,
    track_id: trackId,
    card_key: cardKey,
    user_state: userState,
  });
}

export type ConcernedCardsFilter =
  | "known_pending"
  | "suspended"
  | "buried"
  | "prerequisite_support"
  | "current_waiting_context";

export interface ConcernedCard {
  card_key: string;
  prompt: LearnFacetPresentation;
  state: string;
  user_state: string;
  horizon_utc: string | null;
  action: "learn_instead" | "reactivate" | null;
}

export interface ConcernedCardsResponse {
  profile_id: string;
  track_id: string;
  filter: ConcernedCardsFilter;
  cards: ConcernedCard[];
}

export async function getConcernedCards(
  hass: HomeAssistantLike,
  profileId: string,
  trackId: string,
  filter: ConcernedCardsFilter,
  mode: "learn" | "quiz",
): Promise<ConcernedCardsResponse> {
  return hass.callWS<ConcernedCardsResponse>({
    type: "locklearn/cards/concerned/list",
    profile_id: profileId,
    track_id: trackId,
    filter,
    mode,
  });
}

export async function learnCardInstead(
  hass: HomeAssistantLike,
  profileId: string,
  trackId: string,
  cardKey: string,
): Promise<Record<string, unknown>> {
  return hass.callWS<Record<string, unknown>>({
    type: "locklearn/cards/learn_instead",
    profile_id: profileId,
    track_id: trackId,
    card_key: cardKey,
  });
}

export interface ReadyReminderStatus {
  active: boolean;
  mode: "learn" | "quiz";
  scheduled_for_utc: string | null;
  target_available: boolean;
}

export async function getReadyReminderStatus(
  hass: HomeAssistantLike, profileId: string, trackId: string, mode: "learn" | "quiz",
): Promise<ReadyReminderStatus> {
  return hass.callWS<ReadyReminderStatus>({
    type: "locklearn/reminders/ready/status", profile_id: profileId, track_id: trackId, mode,
  });
}

export async function armReadyReminder(
  hass: HomeAssistantLike, profileId: string, trackId: string, mode: "learn" | "quiz",
): Promise<ReadyReminderStatus> {
  return hass.callWS<ReadyReminderStatus>({
    type: "locklearn/reminders/ready/arm", profile_id: profileId, track_id: trackId, mode,
  });
}

export async function cancelReadyReminder(
  hass: HomeAssistantLike, profileId: string, trackId: string, mode: "learn" | "quiz",
): Promise<ReadyReminderStatus> {
  return hass.callWS<ReadyReminderStatus>({
    type: "locklearn/reminders/ready/cancel", profile_id: profileId, track_id: trackId, mode,
  });
}

export async function undoLastProgress(
  hass: HomeAssistantLike, profileId: string, trackId: string, cardKey: string,
): Promise<Record<string, unknown>> {
  return hass.callWS<Record<string, unknown>>({
    type: "locklearn/progress/undo_last", profile_id: profileId, track_id: trackId, card_key: cardKey,
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
): Promise<DifficultyAnnotation> {
  return hass.callWS<DifficultyAnnotation>({
    type: "locklearn/annotations/create",
    profile_id: profileId,
    card_key: cardKey,
    note: note.trim(),
  });
}

export async function updateCardAnnotation(
  hass: HomeAssistantLike,
  profileId: string,
  annotationId: string,
  note: string,
): Promise<DifficultyAnnotation> {
  return hass.callWS<DifficultyAnnotation>({
    type: "locklearn/annotations/update",
    profile_id: profileId,
    annotation_id: annotationId,
    note: note.trim(),
  });
}

export async function reactivateLeech(
  hass: HomeAssistantLike,
  profileId: string,
  trackId: string,
  cardKey: string,
): Promise<Record<string, unknown>> {
  return hass.callWS<Record<string, unknown>>({
    type: "locklearn/leeches/reactivate",
    profile_id: profileId,
    track_id: trackId,
    card_key: cardKey,
  });
}

export async function startLeechSession(
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
    settings: {
      requested_cards: requestedCards,
      leeches_only: true,
    },
  });
}
