import { describe, expect, it } from "vitest";

import {
  bootstrap,
  FRONTEND_PROTOCOL_VERSION,
  answerSession,
  completeSession,
  createCardAnnotation,
  getDashboard,
  getSession,
  installDataset,
  listDatasetAttributions,
  listDatasets,
  listProfileMembers,
  listShareTargets,
  listTracks,
  listPacks,
  listNotificationTargets,
  previewPackUpdate,
  previewTrackPlan,
  refreshDatasets,
  setTrackPlan,
  listVisibleProfiles,
  reportQuestion,
  reportFreeTextShouldBeAccepted,
  setCardUserState,
  startLearnSession,
  startQuizSession,
  submitQuizAnswer,
  evaluateQuizAnswer,
  ProtocolMismatchError,
  type HomeAssistantLike,
} from "./protocol";

describe("frontend protocol", () => {
  it("bootstraps over Home Assistant WebSocket only", async () => {
    const messages: Record<string, unknown>[] = [];
    const hass: HomeAssistantLike = {
      callWS: async <T>(message: Record<string, unknown>): Promise<T> => {
        messages.push(message);
        return {
          frontend_protocol: FRONTEND_PROTOCOL_VERSION,
          backend_version: "0.0.2",
          panel_path: "/locklearn",
          authenticated_user_id: "user-1",
          is_admin: true,
          personal_profile: null,
        } as unknown as T;
      },
    };

    const result = await bootstrap(hass);
    expect(result.backend_version).toBe("0.0.2");
    expect(messages).toEqual([{ type: "locklearn/bootstrap" }]);
  });

  it("fails closed on a protocol mismatch", async () => {
    const hass: HomeAssistantLike = {
      callWS: async <T>(): Promise<T> =>
        ({
          frontend_protocol: FRONTEND_PROTOCOL_VERSION + 1,
          backend_version: "9.9.9",
          panel_path: "/locklearn",
          authenticated_user_id: "user-1",
          is_admin: true,
          personal_profile: null,
        }) as T,
    };

    await expect(bootstrap(hass)).rejects.toBeInstanceOf(ProtocolMismatchError);
  });

  it("requests one Profile dashboard without widening the scope", async () => {
    const messages: Record<string, unknown>[] = [];
    const hass: HomeAssistantLike = {
      callWS: async <T>(message: Record<string, unknown>): Promise<T> => {
        messages.push(message);
        return {
          profile: {
            profile_id: "p1",
            name: "One",
            preset: "standard",
            timezone: "Europe/Paris",
          },
          generated_at_utc: "2026-09-26T20:00:00+00:00",
          tracks: [],
        } as unknown as T;
      },
    };

    const result = await getDashboard(hass, "p1");
    expect(result.profile.profile_id).toBe("p1");
    expect(messages).toEqual([
      { type: "locklearn/dashboard/get", profile_id: "p1" },
    ]);
  });

  it("uses explicit Learn session and mutation contracts", async () => {
    const messages: Record<string, unknown>[] = [];
    const session = {
      id: "s1",
      profile_id: "p1",
      track_id: "t1",
      type: "learn",
      strategy: "default",
      status: "active",
      version: 3,
      current_position: 0,
      started_at_utc: "2026-09-26T20:00:00+00:00",
      last_activity_at_utc: "2026-09-26T20:00:00+00:00",
      completed_at_utc: null,
      question_count: 1,
      settings: {},
      items: [],
      answers: [],
      current_question: null,
    };
    const hass: HomeAssistantLike = {
      callWS: async <T>(message: Record<string, unknown>): Promise<T> => {
        messages.push(message);
        return session as unknown as T;
      },
    };

    await startLearnSession(hass, "p1", "t1", 12);
    await getSession(hass, "s1");
    await answerSession(hass, session, "q1", {
      kind: "learning",
      action: "known",
      hint_used: true,
    });
    await completeSession(hass, session);
    await setCardUserState(hass, "p1", "t1", "card", "suspended");
    await createCardAnnotation(hass, "p1", "card", "remember me");
    await reportQuestion(
      hass,
      "p1",
      "t1",
      {
        position: 0,
        question_id: "q1",
        card_key: "card",
        learning_item_id: "item",
        prompt_facet_id: "prompt",
        answer_facet_id: "answer",
        status: "presented",
        payload: {},
      },
      "ambiguous",
    );

    expect(messages).toEqual([
      {
        type: "locklearn/session/start",
        profile_id: "p1",
        track_id: "t1",
        session_type: "learn",
        strategy: "default",
        settings: { requested_cards: 12 },
      },
      { type: "locklearn/session/get", session_id: "s1" },
      {
        type: "locklearn/session/answer",
        session_id: "s1",
        expected_version: 3,
        question_id: "q1",
        answer: { kind: "learning", action: "known", hint_used: true },
      },
      {
        type: "locklearn/session/complete",
        session_id: "s1",
        expected_version: 3,
      },
      {
        type: "locklearn/progress/set_user_state",
        profile_id: "p1",
        track_id: "t1",
        card_key: "card",
        user_state: "suspended",
      },
      {
        type: "locklearn/annotations/create",
        profile_id: "p1",
        card_key: "card",
        note: "remember me",
      },
      {
        type: "locklearn/content/report_question",
        profile_id: "p1",
        track_id: "t1",
        card_key: "card",
        learning_item_id: "item",
        prompt_facet_id: "prompt",
        answer_facet_id: "answer",
        reason: "user_reported_question",
        message: "ambiguous",
      },
    ]);
  });

  it("uses explicit Quiz evaluate/report/session contracts", async () => {
    const messages: Record<string, unknown>[] = [];
    const session = {
      id: "quiz-1",
      profile_id: "p1",
      track_id: "t1",
      type: "quiz",
      strategy: "default",
      status: "active",
      version: 2,
      current_position: 0,
      started_at_utc: "2026-09-26T20:00:00+00:00",
      last_activity_at_utc: "2026-09-26T20:00:00+00:00",
      completed_at_utc: null,
      question_count: 1,
      settings: {},
      items: [],
      answers: [],
      current_question: null,
    };
    const hass: HomeAssistantLike = {
      callWS: async <T>(message: Record<string, unknown>): Promise<T> => {
        messages.push(message);
        if (message.type === "locklearn/quiz/evaluate") {
          return {
            format: "free_text",
            result: "wrong",
            immediate: true,
            reveal_correct_answer: true,
            correct_answer: "answer",
            contrastive_feedback: null,
            submitted_text: "answr",
            normalized_submission: null,
            reportable: true,
            grading_policy_kind: "exact",
            grading_policy_version: 1,
            normalization_version: 1,
            hint_used: false,
          } as T;
        }
        if (message.type === "locklearn/content/report") {
          return {
            report_id: 1,
            grading_result: "unrecognized",
            srs_penalized: false,
          } as T;
        }
        return session as unknown as T;
      },
    };

    await startQuizSession(hass, "p1", "t1", 7, "mixed");
    const feedback = await evaluateQuizAnswer(hass, "quiz-1", "q1", {
      kind: "quiz",
      submitted_text: "answr",
    });
    await submitQuizAnswer(hass, session, "q1", {
      kind: "quiz",
      selected_answer_id: "a1",
    });
    await reportFreeTextShouldBeAccepted(
      hass,
      "p1",
      "t1",
      {
        position: 0,
        question_id: "q1",
        card_key: "card",
        learning_item_id: "item",
        prompt_facet_id: "prompt",
        answer_facet_id: "answer",
        status: "presented",
        payload: {},
      },
      feedback,
    );

    expect(messages).toEqual([
      {
        type: "locklearn/session/start",
        profile_id: "p1",
        track_id: "t1",
        session_type: "quiz",
        strategy: "default",
        settings: { requested_cards: 7, quiz_format: "mixed", option_count: 4 },
      },
      {
        type: "locklearn/quiz/evaluate",
        session_id: "quiz-1",
        question_id: "q1",
        answer: { kind: "quiz", submitted_text: "answr" },
      },
      {
        type: "locklearn/quiz/answer",
        session_id: "quiz-1",
        expected_version: 2,
        question_id: "q1",
        answer: { kind: "quiz", selected_answer_id: "a1" },
      },
      {
        type: "locklearn/content/report",
        profile_id: "p1",
        track_id: "t1",
        card_key: "card",
        learning_item_id: "item",
        prompt_facet_id: "prompt",
        answer_facet_id: "answer",
        submitted_text: "answr",
        normalized_submission: null,
        grading_policy_kind: "exact",
        grading_policy_version: 1,
        normalization_version: 1,
      },
    ]);
  });

  it("uses explicit P5.5 management preview contracts", async () => {
    const messages: Record<string, unknown>[] = [];
    const hass: HomeAssistantLike = {
      callWS: async <T>(message: Record<string, unknown>): Promise<T> => {
        messages.push(message);
        if (message.type === "locklearn/profiles/members") return [] as T;
        if (message.type === "locklearn/profiles/share_targets") return [] as T;
        if (
          message.type === "locklearn/tracks/list" ||
          message.type === "locklearn/packs/list" ||
          message.type === "locklearn/targets/list"
        ) {
          return { items: [], cursor: null } as T;
        }
        if (message.type === "locklearn/tracks/preview_pack_update") {
          return {
            from_pack_version_id: "v1",
            to_pack_version_id: "v2",
            added_learning_item_ids: [],
            removed_learning_item_ids: [],
            changed_learning_item_ids: [],
          } as T;
        }
        return {
          selected_cards: 0,
          introduced_cards: 0,
          target_cards: 0,
          remaining_target_cards: 0,
          required_new_per_day: 0,
          planned_new_per_day: 0,
          reviews_per_day_in_3_weeks: 0,
          reviews_per_day_in_3_months: 0,
          due_now: 0,
          notification_deliverable_in_3_weeks: 0,
          active_session_cards_in_3_weeks: 0,
          notification_deliverable_in_3_months: 0,
          active_session_cards_in_3_months: 0,
          target_date_feasible: true,
          review_capacity_feasible_in_3_weeks: true,
          review_capacity_feasible_in_3_months: true,
          warnings: [],
          assumptions: [],
        } as T;
      },
    };
    const plan = {
      max_new_per_day_cards: 4,
      max_reviews_per_day_cards: 30,
      max_notification_new_teasers: 2,
      target_date: null,
      target_coverage: 1,
      target_retention: 0.9,
    };

    await listProfileMembers(hass, "p1");
    await listShareTargets(hass, "p1");
    await listTracks(hass, "p1");
    await listPacks(hass);
    await listNotificationTargets(hass, "p1");
    await previewPackUpdate(hass, "t1", "v2");
    await previewTrackPlan(hass, "t1", plan);
    await setTrackPlan(hass, "t1", plan);

    expect(messages).toEqual([
      { type: "locklearn/profiles/members", profile_id: "p1" },
      { type: "locklearn/profiles/share_targets", profile_id: "p1" },
      { type: "locklearn/tracks/list", limit: 100, profile_id: "p1" },
      { type: "locklearn/packs/list", limit: 100 },
      { type: "locklearn/targets/list", limit: 100, profile_id: "p1" },
      {
        type: "locklearn/tracks/preview_pack_update",
        track_id: "t1",
        pack_version_id: "v2",
      },
      { type: "locklearn/tracks/plan_preview", track_id: "t1", ...plan },
      { type: "locklearn/tracks/plan_set", track_id: "t1", ...plan },
    ]);
  });

  it("uses global dataset status and admin update contracts", async () => {
    const messages: Record<string, unknown>[] = [];
    const status = {
      dataset_id: "locklearn:starter",
      name: "Starter",
      state: "update_available",
      installed_version: "1.0.0",
      available_version: "1.1.0",
      update_available: true,
      source_age_days: 4,
      stale_sources: [],
      cache_bytes: 4096,
      error: null,
      changelog: "Updated content",
      release_url: "https://example.invalid/releases/1.1.0",
      artifact_size: 1024,
      built_at_utc: "2026-09-26T20:00:00+00:00",
      dataset_version_id: "dataset-version",
      canonical_content_hash: "a".repeat(64),
      sources: [],
      licenses: [],
      pack_version_ids: ["pack-v1"],
    };
    const hass: HomeAssistantLike = {
      callWS: async <T>(message: Record<string, unknown>): Promise<T> => {
        messages.push(message);
        if (message.type === "locklearn/datasets/list") {
          return { items: [status], cursor: null } as T;
        }
        if (message.type === "locklearn/datasets/refresh") {
          return { items: [status] } as T;
        }
        if (message.type === "locklearn/datasets/attributions") {
          return {
            items: [{
              source_record_id: "42",
              author: "Contributor",
              language_tag: "ja",
              modified_from_source: false,
              attribution_text: "Contributor / source",
              license_id: "CC-BY-2.0-FR",
              license_scope: "dataset",
            }],
            cursor: null,
          } as T;
        }
        return {
          dataset_id: status.dataset_id,
          version: "1.1.0",
          generation_id: "generation-2",
          previous_generation_id: "generation-1",
          statuses: [{ ...status, installed_version: "1.1.0", update_available: false }],
        } as T;
      },
    };

    expect((await listDatasets(hass))[0]?.dataset_id).toBe(status.dataset_id);
    expect(
      (await listDatasetAttributions(hass, status.dataset_id, "tatoeba")).items[0]
        ?.attribution_text,
    ).toBe("Contributor / source");
    expect((await refreshDatasets(hass))[0]?.available_version).toBe("1.1.0");
    expect((await installDataset(hass, status.dataset_id, "1.1.0")).version).toBe("1.1.0");
    expect(messages).toEqual([
      { type: "locklearn/datasets/list", limit: 100 },
      {
        type: "locklearn/datasets/attributions",
        dataset_id: "locklearn:starter",
        source_id: "tatoeba",
        limit: 50,
      },
      { type: "locklearn/datasets/refresh" },
      {
        type: "locklearn/datasets/install",
        dataset_id: "locklearn:starter",
        version: "1.1.0",
      },
    ]);
  });

  it("loads every visible profile page", async () => {
    const messages: Record<string, unknown>[] = [];
    const hass: HomeAssistantLike = {
      callWS: async <T>(message: Record<string, unknown>): Promise<T> => {
        messages.push(message);
        const cursor = message.cursor;
        if (cursor === undefined) {
          return {
            items: [
              {
                profile_id: "p1",
                name: "One",
                preset: "standard",
                timezone: "Europe/Paris",
                status: "active",
                role: "owner",
              },
            ],
            cursor: "1",
          } as unknown as T;
        }
        return {
          items: [
            {
              profile_id: "p2",
              name: "Two",
              preset: "standard",
              timezone: "Europe/Paris",
              status: "active",
              role: "viewer",
            },
          ],
          cursor: null,
        } as unknown as T;
      },
    };

    const profiles = await listVisibleProfiles(hass);
    expect(profiles.map((profile) => profile.profile_id)).toEqual(["p1", "p2"]);
    expect(messages).toEqual([
      { type: "locklearn/profiles/list", limit: 100 },
      { type: "locklearn/profiles/list", limit: 100, cursor: "1" },
    ]);
  });
});
