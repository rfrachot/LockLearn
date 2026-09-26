import { LitElement, css, html, nothing } from "lit";
import { property, state } from "lit/decorators.js";

import { languageFallback, translate, type UiLanguage } from "./i18n";
import "./learn-view";
import "./quiz-view";
import { isRouteVisible, visibleNavigation } from "./navigation";
import { defaultProfileId, groupProfiles } from "./profile-switcher";
import {
  bootstrap,
  FRONTEND_PROTOCOL_VERSION,
  getDashboard,
  listVisibleProfiles,
  ProtocolMismatchError,
  type BootstrapResponse,
  type DashboardResponse,
  type HomeAssistantLike,
  type VisibleProfile,
} from "./protocol";
import {
  registrationDecision,
  type LockLearnElementConstructor,
} from "./registration";
import { shouldStartInitialLoad } from "./panel-lifecycle";
import {
  navigateToRoute,
  parseRoute,
  type RouteName,
} from "./router";

type ShellStatus = "loading" | "ready" | "error" | "protocol-mismatch";

const HARD_RELOAD_OVERLAY_ID = "locklearn-hard-reload-required";

export class LockLearnPanel extends LitElement {
  static readonly locklearnFrontendProtocol = FRONTEND_PROTOCOL_VERSION;

  @property({ attribute: false }) hass?: HomeAssistantLike;

  @state() private status: ShellStatus = "loading";
  // Home Assistant assigns its own `route` object to custom panels. Keep the
  // shell's selected route under a distinct name so HA cannot overwrite it.
  @state() private activeRoute: RouteName = parseRoute(
    globalThis.location?.pathname ?? "/locklearn",
  );
  @state() private bootstrapState?: BootstrapResponse;
  @state() private profiles: VisibleProfile[] = [];
  @state() private selectedProfileId: string | null = null;
  @state() private dashboard?: DashboardResponse;
  @state() private dashboardLoading = false;
  @state() private dashboardError = "";
  @state() private errorMessage = "";

  private loadGeneration = 0;
  private dashboardGeneration = 0;
  private initialLoadStarted = false;

  static styles = css`
    :host {
      display: block;
      min-height: 100%;
      box-sizing: border-box;
      color: var(--primary-text-color);
      background: var(--primary-background-color);
      font-family: var(--paper-font-body1_-_font-family, system-ui, sans-serif);
    }

    .shell {
      min-height: 100vh;
      display: grid;
      grid-template-rows: auto 1fr;
    }

    header {
      position: sticky;
      top: 0;
      z-index: 1;
      display: flex;
      align-items: center;
      gap: 20px;
      min-height: 64px;
      padding: 0 24px;
      border-bottom: 1px solid var(--divider-color);
      background: var(--card-background-color, var(--primary-background-color));
    }

    .brand {
      font-size: 1.15rem;
      font-weight: 700;
      white-space: nowrap;
    }

    .profile-switcher {
      display: grid;
      gap: 2px;
      min-width: 170px;
      color: var(--secondary-text-color);
      font-size: 0.75rem;
    }

    .profile-switcher select {
      min-width: 0;
      padding: 7px 28px 7px 9px;
      border: 1px solid var(--divider-color);
      border-radius: 8px;
      color: var(--primary-text-color);
      background: var(--card-background-color, var(--primary-background-color));
      font: inherit;
      font-size: 0.9rem;
    }

    nav {
      display: flex;
      align-items: center;
      gap: 4px;
      min-width: 0;
      overflow-x: auto;
      scrollbar-width: thin;
    }

    button {
      font: inherit;
    }

    .nav-button,
    .primary-button {
      border: 0;
      border-radius: 8px;
      cursor: pointer;
    }

    .nav-button {
      padding: 9px 11px;
      color: var(--secondary-text-color);
      background: transparent;
      white-space: nowrap;
    }

    .nav-button[aria-current="page"] {
      color: var(--primary-text-color);
      background: var(--secondary-background-color);
      font-weight: 600;
    }

    main {
      width: min(1100px, calc(100% - 32px));
      margin: 0 auto;
      padding: 28px 0 48px;
      box-sizing: border-box;
    }

    .state-card,
    .page {
      padding: 24px;
      border-radius: 12px;
      background: var(--card-background-color, var(--primary-background-color));
      box-shadow: var(--ha-card-box-shadow, none);
    }

    .state-card {
      max-width: 680px;
      margin: 48px auto 0;
    }

    .home-header {
      display: flex;
      align-items: end;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 18px;
    }

    .home-header h1 {
      margin: 0;
    }

    .track-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 16px;
    }

    .track-card {
      padding: 20px;
      border: 1px solid var(--divider-color);
      border-radius: 12px;
      background: var(--card-background-color, var(--primary-background-color));
      box-shadow: var(--ha-card-box-shadow, none);
    }

    .track-card h2 {
      margin: 0;
      font-size: 1.15rem;
    }

    .track-languages {
      margin-top: 4px;
      color: var(--secondary-text-color);
      font-size: 0.85rem;
    }

    .metrics {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
      margin-top: 18px;
    }

    .metric {
      min-width: 0;
      padding: 12px;
      border-radius: 10px;
      background: var(--secondary-background-color);
    }

    .metric-label {
      color: var(--secondary-text-color);
      font-size: 0.78rem;
    }

    .metric-value {
      margin-top: 4px;
      font-weight: 650;
      line-height: 1.25;
    }

    .metric-detail {
      margin-top: 4px;
      color: var(--secondary-text-color);
      font-size: 0.78rem;
      line-height: 1.3;
    }

    .state-card h1,
    .page h1 {
      margin-top: 0;
    }

    .state-card p,
    .page p {
      color: var(--secondary-text-color);
      line-height: 1.5;
    }

    .primary-button {
      margin-top: 8px;
      padding: 10px 14px;
      color: var(--text-primary-color, white);
      background: var(--primary-color);
    }

    .meta {
      margin-top: 18px;
      font-size: 0.85rem;
      color: var(--secondary-text-color);
    }

    @media (max-width: 720px) {
      header {
        align-items: flex-start;
        flex-direction: column;
        gap: 8px;
        padding: 14px 16px 10px;
      }

      .profile-switcher {
        width: 100%;
      }

      .profile-switcher select {
        width: 100%;
      }

      nav {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        width: 100%;
        overflow-x: visible;
      }

      .nav-button {
        width: 100%;
        min-width: 0;
        padding-inline: 8px;
        overflow: hidden;
        text-overflow: ellipsis;
      }

      main {
        width: min(100% - 24px, 1100px);
        padding-top: 18px;
      }
    }
  `;

  connectedCallback(): void {
    super.connectedCallback();
    globalThis.addEventListener?.("popstate", this.handlePopState);
  }

  disconnectedCallback(): void {
    globalThis.removeEventListener?.("popstate", this.handlePopState);
    super.disconnectedCallback();
  }

  protected updated(changed: Map<PropertyKey, unknown>): void {
    if (
      shouldStartInitialLoad(
        this.initialLoadStarted,
        changed.has("hass"),
        this.hass !== undefined,
      )
    ) {
      this.initialLoadStarted = true;
      void this.load();
    }
  }

  private readonly handlePopState = (): void => {
    const next = parseRoute(globalThis.location?.pathname ?? "/locklearn");
    this.activeRoute = isRouteVisible(next, this.profiles) ? next : "home";
  };

  private locale(): UiLanguage {
    const locale =
      this.hass?.locale?.language ??
      this.hass?.language ??
      globalThis.navigator?.language ??
      "en";
    return languageFallback(locale);
  }

  private t(key: Parameters<typeof translate>[1]): string {
    return translate(this.locale(), key);
  }

  private async load(): Promise<void> {
    if (this.hass === undefined) return;
    const generation = ++this.loadGeneration;
    this.status = "loading";
    this.errorMessage = "";

    try {
      const bootstrapState = await bootstrap(this.hass);
      const profiles = await listVisibleProfiles(this.hass);
      if (generation !== this.loadGeneration) return;

      this.bootstrapState = bootstrapState;
      this.profiles = profiles;
      this.selectedProfileId = defaultProfileId(profiles, bootstrapState);
      const requested = parseRoute(globalThis.location?.pathname ?? bootstrapState.panel_path);
      this.activeRoute = isRouteVisible(requested, profiles) ? requested : "home";
      this.status = "ready";
      void this.loadDashboard();
    } catch (error) {
      if (generation !== this.loadGeneration) return;
      if (error instanceof ProtocolMismatchError) {
        this.bootstrapState = {
          frontend_protocol: error.backendProtocol,
          backend_version: error.backendVersion,
          panel_path: "/locklearn",
          authenticated_user_id: "",
          personal_profile: null,
        };
        this.status = "protocol-mismatch";
        return;
      }
      this.errorMessage = error instanceof Error ? error.message : String(error);
      this.status = "error";
    }
  }

  private selectRoute(route: RouteName): void {
    if (!isRouteVisible(route, this.profiles)) return;
    this.activeRoute = route;
    navigateToRoute(route);
  }

  private selectProfile(event: Event): void {
    const target = event.currentTarget;
    if (!(target instanceof HTMLSelectElement)) return;
    const profileId = target.value;
    if (!this.profiles.some((profile) => profile.profile_id === profileId)) return;
    this.selectedProfileId = profileId;
    void this.loadDashboard();
  }

  private async loadDashboard(): Promise<void> {
    if (this.hass === undefined || this.selectedProfileId === null) {
      this.dashboard = undefined;
      this.dashboardError = "";
      return;
    }
    const generation = ++this.dashboardGeneration;
    this.dashboardLoading = true;
    this.dashboardError = "";
    try {
      const dashboard = await getDashboard(this.hass, this.selectedProfileId);
      if (generation !== this.dashboardGeneration) return;
      this.dashboard = dashboard;
    } catch (error) {
      if (generation !== this.dashboardGeneration) return;
      this.dashboard = undefined;
      this.dashboardError = error instanceof Error ? error.message : String(error);
    } finally {
      if (generation === this.dashboardGeneration) {
        this.dashboardLoading = false;
      }
    }
  }

  private hardReload(): void {
    globalThis.location?.reload();
  }

  protected render() {
    if (this.status === "loading") {
      return this.renderState(this.t("state.loading"));
    }
    if (this.status === "protocol-mismatch") {
      return html`
        <main>
          <section class="state-card" role="alert">
            <h1>${this.t("state.protocol.title")}</h1>
            <p>${this.t("state.protocol.body")}</p>
            <button class="primary-button" @click=${this.hardReload}>
              ${this.t("state.protocol.reload")}
            </button>
            <div class="meta">
              frontend protocol ${FRONTEND_PROTOCOL_VERSION} · backend protocol
              ${this.bootstrapState?.frontend_protocol ?? "?"} · backend
              ${this.bootstrapState?.backend_version ?? "?"}
            </div>
          </section>
        </main>
      `;
    }
    if (this.status === "error") {
      return html`
        <main>
          <section class="state-card" role="alert">
            <h1>${this.t("state.error")}</h1>
            <p>${this.errorMessage}</p>
            <button class="primary-button" @click=${() => void this.load()}>
              ${this.t("state.retry")}
            </button>
          </section>
        </main>
      `;
    }

    const navigation = visibleNavigation(this.profiles);
    const groups = groupProfiles(this.profiles);
    return html`
      <div class="shell">
        <header>
          <div class="brand">${this.t("app.title")}</div>
          ${this.profiles.length === 0
            ? nothing
            : html`<label class="profile-switcher">
                <span>${this.t("profile.select")}</span>
                <select
                  .value=${this.selectedProfileId ?? ""}
                  @change=${this.selectProfile}
                >
                  ${groups.mine.length === 0
                    ? nothing
                    : html`<optgroup label=${this.t("profile.mine")}>
                        ${groups.mine.map(
                          (profile) =>
                            html`<option value=${profile.profile_id}>${profile.name}</option>`,
                        )}
                      </optgroup>`}
                  ${groups.shared.length === 0
                    ? nothing
                    : html`<optgroup label=${this.t("profile.shared")}>
                        ${groups.shared.map(
                          (profile) =>
                            html`<option value=${profile.profile_id}>${profile.name}</option>`,
                        )}
                      </optgroup>`}
                </select>
              </label>`}
          <nav aria-label="LockLearn">
            ${navigation.map(
              (item) => html`
                <button
                  class="nav-button"
                  aria-current=${this.activeRoute === item.route ? "page" : nothing}
                  @click=${() => this.selectRoute(item.route)}
                >
                  ${this.t(item.labelKey as Parameters<typeof translate>[1])}
                </button>
              `,
            )}
          </nav>
        </header>
        <main>
          ${this.profiles.length === 0
            ? html`<section class="state-card">
                <h1>${this.t("app.title")}</h1>
                <p>${this.t("state.noProfiles")}</p>
              </section>`
            : this.activeRoute === "home"
              ? this.renderHome()
              : this.activeRoute === "learn"
                ? html`<locklearn-learn-view
                    .hass=${this.hass}
                    .profile=${this.profiles.find(
                      (profile) => profile.profile_id === this.selectedProfileId,
                    )}
                    .dashboard=${this.dashboard}
                  ></locklearn-learn-view>`
                : this.activeRoute === "quiz"
                  ? html`<locklearn-quiz-view
                      .hass=${this.hass}
                      .profile=${this.profiles.find(
                        (profile) => profile.profile_id === this.selectedProfileId,
                      )}
                      .dashboard=${this.dashboard}
                    ></locklearn-quiz-view>`
                  : html`<section class="page">
                  <h1>${this.routeLabel(this.activeRoute)}</h1>
                  <p>${this.t("route.placeholder")}</p>
                </section>`}
        </main>
      </div>
    `;
  }

  private renderHome() {
    if (this.dashboardLoading) {
      return html`<section class="page"><p>${this.t("dashboard.loading")}</p></section>`;
    }
    if (this.dashboardError) {
      return html`<section class="page" role="alert">
        <h1>${this.t("dashboard.error")}</h1>
        <p>${this.dashboardError}</p>
      </section>`;
    }
    if (this.dashboard === undefined) {
      return html`<section class="page"><p>${this.t("dashboard.noTracks")}</p></section>`;
    }
    return html`
      <section>
        <div class="home-header">
          <h1>${this.dashboard.profile.name}</h1>
        </div>
        ${this.dashboard.tracks.length === 0
          ? html`<section class="page"><p>${this.t("dashboard.noTracks")}</p></section>`
          : html`<div class="track-grid">
              ${this.dashboard.tracks.map((track) => html`
                <article class="track-card">
                  <h2>${track.name}</h2>
                  <div class="track-languages">
                    ${track.source_language} → ${track.target_language}
                  </div>
                  <div class="metrics">
                    <div class="metric">
                      <div class="metric-label">${this.t("dashboard.dueToday")}</div>
                      <div class="metric-value">${track.due_today}</div>
                    </div>
                    <div class="metric">
                      <div class="metric-label">${this.t("dashboard.accuracy")}</div>
                      <div class="metric-value">${this.formatAccuracy(track.recent_verified_accuracy.accuracy)}</div>
                      <div class="metric-detail">
                        ${track.recent_verified_accuracy.correct}/${track.recent_verified_accuracy.total}
                      </div>
                    </div>
                    <div class="metric">
                      <div class="metric-label">${this.t("dashboard.latestVerified")}</div>
                      <div class="metric-value">
                        ${track.recent_verified_retention === null
                          ? this.t("dashboard.noVerified")
                          : track.recent_verified_retention.retained
                            ? this.t("dashboard.retained")
                            : this.t("dashboard.notRetained")}
                      </div>
                      ${track.recent_verified_retention === null
                        ? nothing
                        : html`<div class="metric-detail">
                            ${this.formatDateTime(
                              track.recent_verified_retention.created_at_utc,
                              this.dashboard?.profile.timezone,
                            )}
                          </div>`}
                    </div>
                    <div class="metric">
                      <div class="metric-label">${this.t("dashboard.lastSession")}</div>
                      <div class="metric-value">
                        ${track.last_session === null
                          ? this.t("dashboard.noSession")
                          : `${track.last_session.answered_count}/${track.last_session.question_count} ${this.t("dashboard.answered")}`}
                      </div>
                      ${track.last_session === null
                        ? nothing
                        : html`<div class="metric-detail">
                            ${this.formatDateTime(
                              track.last_session.completed_at_utc ??
                                track.last_session.last_activity_at_utc,
                              this.dashboard?.profile.timezone,
                            )}
                          </div>`}
                    </div>
                    <div class="metric">
                      <div class="metric-label">${this.t("dashboard.nextNotification")}</div>
                      <div class="metric-value">
                        ${track.next_notification === null
                          ? this.t("dashboard.noNotification")
                          : this.formatDateTime(
                              track.next_notification.effective_for_utc,
                              this.dashboard?.profile.timezone,
                            )}
                      </div>
                    </div>
                  </div>
                </article>
              `)}
            </div>`}
      </section>
    `;
  }

  private formatAccuracy(value: number | null): string {
    if (value === null) return "—";
    return new Intl.NumberFormat(this.locale(), {
      style: "percent",
      maximumFractionDigits: 0,
    }).format(value);
  }

  private formatDateTime(value: string, timeZone?: string): string {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "—";
    return new Intl.DateTimeFormat(this.locale(), {
      dateStyle: "short",
      timeStyle: "short",
      ...(timeZone === undefined ? {} : { timeZone }),
    }).format(date);
  }

  private renderState(message: string) {
    return html`<main><section class="state-card"><p>${message}</p></section></main>`;
  }

  private routeLabel(route: RouteName): string {
    const item = visibleNavigation(this.profiles).find((candidate) => candidate.route === route);
    return item === undefined
      ? this.t("nav.home")
      : this.t(item.labelKey as Parameters<typeof translate>[1]);
  }
}

function showHardReloadOverlay(
  existingProtocol: number | null,
): void {
  if (typeof document === "undefined") return;
  if (document.getElementById(HARD_RELOAD_OVERLAY_ID) !== null) return;

  const overlay = document.createElement("div");
  overlay.id = HARD_RELOAD_OVERLAY_ID;
  overlay.setAttribute("role", "alert");
  overlay.style.cssText =
    "position:fixed;inset:0;z-index:2147483647;display:grid;place-items:center;" +
    "padding:24px;background:var(--primary-background-color,#fff);" +
    "color:var(--primary-text-color,#111);font-family:system-ui,sans-serif";

  const card = document.createElement("div");
  card.style.cssText =
    "max-width:680px;padding:24px;border:1px solid var(--divider-color,#ddd);" +
    "border-radius:12px;background:var(--card-background-color,#fff)";

  const title = document.createElement("h1");
  title.textContent = "LockLearn was updated";
  const body = document.createElement("p");
  body.textContent =
    "An older LockLearn panel is still loaded in this browser. Perform a full browser reload before continuing.";
  const meta = document.createElement("p");
  meta.textContent =
    `loaded protocol ${existingProtocol ?? "unknown"} · current protocol ${FRONTEND_PROTOCOL_VERSION}`;
  const button = document.createElement("button");
  button.textContent = "Reload now";
  button.addEventListener("click", () => globalThis.location?.reload());

  card.append(title, body, meta, button);
  overlay.append(card);
  document.body.append(overlay);
}

const existing = customElements.get(
  "locklearn-panel",
) as LockLearnElementConstructor | undefined;
const registration = registrationDecision(existing);

if (registration.kind === "define") {
  customElements.define("locklearn-panel", LockLearnPanel);
} else if (registration.kind === "reload") {
  showHardReloadOverlay(registration.existingProtocol);
}

declare global {
  interface HTMLElementTagNameMap {
    "locklearn-panel": LockLearnPanel;
  }
}
