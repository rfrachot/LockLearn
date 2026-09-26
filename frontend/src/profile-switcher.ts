import type { BootstrapResponse, VisibleProfile } from "./protocol";

export interface ProfileGroups {
  mine: VisibleProfile[];
  shared: VisibleProfile[];
}

export function groupProfiles(profiles: VisibleProfile[]): ProfileGroups {
  return {
    mine: profiles.filter((profile) => profile.role === "owner"),
    shared: profiles.filter((profile) => profile.role !== "owner"),
  };
}

export function defaultProfileId(
  profiles: VisibleProfile[],
  bootstrapState: BootstrapResponse,
): string | null {
  const personalId = bootstrapState.personal_profile?.profile_id;
  if (
    personalId !== undefined &&
    profiles.some((profile) => profile.profile_id === personalId)
  ) {
    return personalId;
  }
  const owned = profiles.find((profile) => profile.role === "owner");
  if (owned !== undefined) return owned.profile_id;
  return profiles[0]?.profile_id ?? null;
}
