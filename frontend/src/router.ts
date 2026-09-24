export const ROUTES = [
  "home",
  "learn",
  "quiz",
  "exam",
  "stats",
  "profiles",
  "tracks",
  "packs",
  "settings",
] as const;

export type RouteName = (typeof ROUTES)[number];

const DEFAULT_ROUTE: RouteName = "home";

export function parseRoute(pathname: string): RouteName {
  const trimmed = pathname.replace(/^\/+|\/+$/g, "");
  const segments = trimmed.split("/").filter(Boolean);
  const candidate =
    segments[0] === "locklearn" ? segments[1] : segments[0];
  return ROUTES.includes(candidate as RouteName)
    ? (candidate as RouteName)
    : DEFAULT_ROUTE;
}

export function routePath(route: RouteName): string {
  return route === "home" ? "/locklearn" : `/locklearn/${route}`;
}

export function navigateToRoute(route: RouteName): void {
  const path = routePath(route);
  if (globalThis.location?.pathname === path) return;
  globalThis.history?.pushState({}, "", path);
  globalThis.dispatchEvent?.(new PopStateEvent("popstate"));
}
