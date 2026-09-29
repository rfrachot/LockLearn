import "../src/locklearn-panel";

const now = "2026-09-27T02:00:00+00:00";

const profile = {
  profile_id: "profile-e2e",
  name: "E2E Profile",
  preset: "standard",
  timezone: "Europe/Paris",
  status: "active",
  role: "owner",
};

const track = {
  track_id: "track-ja",
  profile_id: profile.profile_id,
  name: "Japanese Core",
  source_language: "ja",
  target_language: "en",
  status: "active",
  priority: 1,
  settings: {},
  pack_version_id: "pack-v1",
  dataset_generation: "gen-1",
  integrated_at_utc: now,
  content_weights: {},
};

const dashboardTrack = {
  track_id: track.track_id,
  name: track.name,
  source_language: "ja",
  target_language: "en",
  due_today: 2,
  recent_verified_retention: { retained: true, created_at_utc: now },
  recent_verified_accuracy: { correct: 8, total: 10, accuracy: 0.8 },
  states: { new: 3, learning: 1, review: 2, relearning: 0, leech: 0 },
  last_session: null,
  next_notification: null,
};

const presentation = {
  card_key: "card-e2e",
  learning_item_id: "item-e2e",
  content_type: "vocabulary",
  prompt: {
    facet_id: "facet-ja",
    kind: "text",
    facet_key: "prompt",
    language_tag: "ja",
    script: "Jpan",
    blocks: [
      {
        content_block_id: "block-ja",
        position: 0,
        kind: "text",
        role: "prompt",
        reveals_answer: false,
        mask_strategy: "none",
        payload: {
          text: "日本",
          ruby_segments: [
            { text: "日", reading: "に" },
            { text: "本", reading: "ほん" },
          ],
        },
        language_tag: "ja",
        script: "Jpan",
      },
    ],
  },
  answer: {
    facet_id: "facet-en",
    kind: "text",
    facet_key: "answer",
    language_tag: "en",
    script: "Latn",
    blocks: [
      {
        content_block_id: "block-en",
        position: 1,
        kind: "text",
        role: "answer",
        reveals_answer: true,
        mask_strategy: "none",
        payload: { text: "Japan" },
        language_tag: "en",
        script: "Latn",
      },
    ],
  },
  context: [],
  introduction_blocks: [
    {
      content_block_id: "block-ja",
      position: 0,
      kind: "text",
      role: "prompt",
      reveals_answer: false,
      mask_strategy: "none",
      payload: {
        text: "日本",
        ruby_segments: [
          { text: "日", reading: "に" },
          { text: "本", reading: "ほん" },
        ],
      },
      language_tag: "ja",
      script: "Jpan",
    },
  ],
  hint_blocks: [],
  mnemonic_blocks: [],
  example_blocks: [],
};

const learnQuestion = {
  position: 0,
  question_id: "learn-q1",
  card_key: "card-e2e",
  learning_item_id: "item-e2e",
  prompt_facet_id: "facet-ja",
  answer_facet_id: "facet-en",
  status: "presented",
  payload: {
    selection: { progress_state: "new", content_type: "vocabulary" },
    presentation,
  },
};

const quizQuestion = {
  position: 0,
  question_id: "quiz-q1",
  card_key: "card-e2e",
  learning_item_id: "item-e2e",
  prompt_facet_id: "facet-ja",
  answer_facet_id: "facet-en",
  status: "presented",
  payload: {
    quiz: {
      format: "mcq",
      prompt_text: "日本",
      context_hint: null,
      options: [
        { answer_id: "a1", text: "Japan" },
        { answer_id: "a2", text: "river" },
        { answer_id: "a3", text: "teacher" },
        { answer_id: "a4", text: "water" },
      ],
      idk_available: true,
      reportable: true,
      hint_blocks: [],
      content_type: "vocabulary",
    },
  },
};

function session(type: "learn" | "quiz") {
  const question = type === "learn" ? learnQuestion : quizQuestion;
  return {
    id: `${type}-session`,
    profile_id: profile.profile_id,
    track_id: track.track_id,
    type,
    strategy: "default",
    status: "active",
    version: 1,
    current_position: 0,
    started_at_utc: now,
    last_activity_at_utc: now,
    completed_at_utc: null,
    question_count: 1,
    settings: {},
    items: [question],
    answers: [],
    current_question: question,
  };
}

const hass = {
  locale: { language: "en-GB" },
  language: "en",
  callWS: async (message: Record<string, unknown>) => {
    switch (message.type) {
      case "locklearn/bootstrap":
        return {
          frontend_protocol: 3,
          backend_version: "0.0.2",
          panel_path: "/locklearn",
          authenticated_user_id: "user-e2e",
          is_admin: true,
          personal_profile: { profile_id: profile.profile_id },
        };
      case "locklearn/profiles/list":
        return { items: [profile], cursor: null };
      case "locklearn/dashboard/get":
        return {
          profile: {
            profile_id: profile.profile_id,
            name: profile.name,
            preset: profile.preset,
            timezone: profile.timezone,
          },
          generated_at_utc: now,
          tracks: [dashboardTrack],
        };
      case "locklearn/tracks/list":
        return { items: [track], cursor: null };
      case "locklearn/session/start":
        return session(message.session_type === "quiz" ? "quiz" : "learn");
      case "locklearn/session/get":
        return session(String(message.session_id).startsWith("quiz") ? "quiz" : "learn");
      case "locklearn/session/answer":
        return { ...session("learn"), version: 2 };
      case "locklearn/session/complete":
        return { ...session("learn"), status: "completed", current_question: null, version: 2 };
      case "locklearn/quiz/answer":
        return {
          feedback: {
            format: "mcq",
            result: message.answer && (message.answer as Record<string, unknown>).selected_answer_id === "a1"
              ? "correct"
              : "wrong",
            immediate: true,
            reveal_correct_answer: true,
            correct_answer: "Japan",
            contrastive_feedback: null,
            selected_answer_id: (message.answer as Record<string, unknown>)?.selected_answer_id ?? null,
            selected_answer: "Japan",
            reportable: true,
            hint_used: false,
          },
          session: { ...session("quiz"), version: 2, current_question: null },
        };
      case "locklearn/stats/get":
        return {
          profile_id: profile.profile_id,
          track_id: null,
          generated_at_utc: now,
          local_date: "2026-09-27",
          due_today: 2,
          states: { new: 3, learning: 1, review: 2, relearning: 0, leech: 0 },
          latest_verified_retention: {
            result: "correct",
            retained: true,
            card_key: "card-e2e",
            created_at_utc: now,
            local_date: "2026-09-27",
          },
          recent_verified_accuracy: { correct: 8, total: 10, accuracy: 0.8, window_limit: 30 },
          mastery: { value: 0.72, card_count: 6, secondary_indicator: true },
          calibration: {
            window_days: 7,
            declared_known_cards: 2,
            later_verified_cards: 2,
            later_verified_correct: 1,
            later_verified_wrong: 1,
            later_verified_accuracy: 0.5,
            awaiting_verified_followup: 0,
          },
          streak: {
            days: 3,
            grace_days: 1,
            grace_days_used: 0,
            goal_fraction: 0.8,
            goal_minimum_cards: 1,
            today: { due_opening: 2, treated_due: 1, target: 2, status: "missed" },
          },
          confusions: [],
          daily: [],
        };
      case "locklearn/difficulties/list":
        return { items: [] };
      case "locklearn/packs/list":
      case "locklearn/targets/list":
      case "locklearn/datasets/list":
        return { items: [], cursor: null };
      case "locklearn/profiles/members":
      case "locklearn/profiles/share_targets":
        return [];
      default:
        return {};
    }
  },
};

const panel = document.createElement("locklearn-panel") as HTMLElement & {
  hass?: typeof hass;
};
panel.hass = hass;
document.body.append(panel);

Object.assign(globalThis, { __LOCKLEARN_E2E_HASS__: hass });
