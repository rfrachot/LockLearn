import { describe, expect, it } from "vitest";

import {
  bootstrap,
  FRONTEND_PROTOCOL_VERSION,
  getDashboard,
  listVisibleProfiles,
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
