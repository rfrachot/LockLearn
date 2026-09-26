import type { ProfileRole, VisibleProfile } from "./protocol";
import type { RouteName } from "./router";

export interface NavigationItem {
  route: RouteName;
  labelKey: string;
}

const READ_ROUTES: NavigationItem[] = [
  { route: "home", labelKey: "nav.home" },
  { route: "learn", labelKey: "nav.learn" },
  { route: "quiz", labelKey: "nav.quiz" },
  { route: "exam", labelKey: "nav.exam" },
  { route: "stats", labelKey: "nav.stats" },
  { route: "profiles", labelKey: "nav.profiles" },
  { route: "tracks", labelKey: "nav.tracks" },
  { route: "packs", labelKey: "nav.packs" },
];

const OWNER_ONLY: NavigationItem[] = [
  { route: "settings", labelKey: "nav.settings" },
];

export function visibleNavigation(
  profiles: VisibleProfile[],
): NavigationItem[] {
  if (profiles.length === 0) return [];
  const roles = new Set<ProfileRole>(profiles.map((profile) => profile.role));
  return roles.has("owner") ? [...READ_ROUTES, ...OWNER_ONLY] : READ_ROUTES;
}

export function isRouteVisible(
  route: RouteName,
  profiles: VisibleProfile[],
): boolean {
  return visibleNavigation(profiles).some((item) => item.route === route);
}
