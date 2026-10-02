import {
  getSessionAvailability,
  type DashboardResponse,
  type DashboardTrack,
  type HomeAssistantLike,
} from "./protocol";

export type ReadyMode = "learn" | "quiz";

export interface ReadyAlternative {
  trackId: string;
  trackName: string;
  mode: ReadyMode;
  availableNow: number;
}

function ranked(
  candidates: Array<{ track: DashboardTrack; availableNow: number }>,
): Array<{ track: DashboardTrack; availableNow: number }> {
  return candidates.sort(
    (left, right) =>
      left.track.priority - right.track.priority ||
      right.availableNow - left.availableNow ||
      left.track.track_id.localeCompare(right.track.track_id),
  );
}

async function availableFor(
  hass: HomeAssistantLike,
  profileId: string,
  tracks: DashboardTrack[],
  mode: ReadyMode,
): Promise<Array<{ track: DashboardTrack; availableNow: number }>> {
  const results = await Promise.all(
    tracks.map(async (track) => {
      const availability = await getSessionAvailability(
        hass,
        profileId,
        track.track_id,
        mode,
      );
      return { track, availableNow: availability.available_now };
    }),
  );
  return ranked(results.filter((candidate) => candidate.availableNow > 0));
}

export async function findReadyAlternative(
  hass: HomeAssistantLike,
  dashboard: DashboardResponse | undefined,
  currentTrackId: string,
  currentMode: ReadyMode,
): Promise<ReadyAlternative | undefined> {
  if (dashboard === undefined || currentTrackId === "") return undefined;
  const current = dashboard.tracks.find((track) => track.track_id === currentTrackId);
  if (current === undefined) return undefined;
  const otherMode: ReadyMode = currentMode === "learn" ? "quiz" : "learn";
  const profileId = dashboard.profile.profile_id;

  const sameTrackOtherMode = await getSessionAvailability(
    hass,
    profileId,
    currentTrackId,
    otherMode,
  );
  if (sameTrackOtherMode.available_now > 0) {
    return {
      trackId: current.track_id,
      trackName: current.name,
      mode: otherMode,
      availableNow: sameTrackOtherMode.available_now,
    };
  }

  const others = dashboard.tracks.filter((track) => track.track_id !== currentTrackId);
  const sameMode = await availableFor(hass, profileId, others, currentMode);
  if (sameMode.length > 0) {
    const winner = sameMode[0];
    return {
      trackId: winner.track.track_id,
      trackName: winner.track.name,
      mode: currentMode,
      availableNow: winner.availableNow,
    };
  }

  const otherModeCandidates = await availableFor(hass, profileId, others, otherMode);
  if (otherModeCandidates.length === 0) return undefined;
  const winner = otherModeCandidates[0];
  return {
    trackId: winner.track.track_id,
    trackName: winner.track.name,
    mode: otherMode,
    availableNow: winner.availableNow,
  };
}
