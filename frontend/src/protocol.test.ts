import { describe, expect, it } from "vitest";

import {
  bootstrap,
  FRONTEND_PROTOCOL_VERSION,
  answerSession,
  completeSession,
  createCardAnnotation,
  getDashboard,
  getSession,
  listVisibleProfiles,
  reportQuestion,
  setCardUserState,
  startLearnSession,
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
