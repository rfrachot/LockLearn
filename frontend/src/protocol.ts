export const FRONTEND_PROTOCOL_VERSION = 1;

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
