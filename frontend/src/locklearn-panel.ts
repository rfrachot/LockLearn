import { LitElement, css, html, nothing } from "lit";
import { property, state } from "lit/decorators.js";

import { interactiveAccessibilityStyles } from "./content-renderer";
import { languageFallback, translate, type UiLanguage } from "./i18n";
import "./learn-view";
import "./quiz-view";
import "./management-view";
import "./dataset-view";
import "./stats-view";
import type { LockLearnManagementView, ManagementRoute } from "./management-view";
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
  type SessionState,
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
  routePath,
  type RouteName,
} from "./router";

type ShellStatus = "loading" | "ready" | "error" | "protocol-mismatch";
type PendingNavigation =
  | { kind: "route"; route: RouteName }
  | { kind: "profile"; profileId: string };

const HARD_RELOAD_OVERLAY_ID = "locklearn-hard-reload-required";

async function withTimeout<T>(promise: Promise<T>, timeoutMs: number): Promise<T> {
  let timer: ReturnType<typeof globalThis.setTimeout> | undefined;
  try {
    return await Promise.race([
      promise,
      new Promise<T>((_resolve, reject) => {
        timer = globalThis.setTimeout(
          () => reject(new Error("LockLearn initial load timed out")),
          timeoutMs,
        );
      }),
    ]);
  } finally {
    if (timer !== undefined) globalThis.clearTimeout(timer);
  }
}

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
  @state() private handoffSession?: SessionState;
  @state() private managementDirty = false;
  @state() private pendingNavigation?: PendingNavigation;
  @state() private navigationSaving = false;
  @state() private loadFailures = 0;
  @state() private diagnosticNotice = "";
  @state() private online = globalThis.navigator?.onLine ?? true;

  private loadGeneration = 0;
  private dashboardGeneration = 0;
  private initialLoadStarted = false;

  static styles = css`
    ${interactiveAccessibilityStyles}
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

    .guard-backdrop {
      position: fixed;
      inset: 0;
      z-index: 1000;
      display: grid;
      place-items: center;
      padding: 20px;
      background: color-mix(in srgb, var(--primary-text-color) 30%, transparent);
    }

    .guard-dialog {
      width: min(520px, 100%);
      padding: 20px;
      border-radius: 14px;
      background: var(--card-background-color, var(--primary-background-color));
      color: var(--primary-text-color);
      box-shadow: var(--ha-card-box-shadow, 0 12px 36px rgb(0 0 0 / 24%));
    }

    .guard-dialog h2 { margin-top: 0; }

    .connection-banner {
      position: sticky;
      top: 64px;
      z-index: 2;
      padding: 8px 16px;
      text-align: center;
      background: var(--warning-color, var(--secondary-background-color));
      color: var(--primary-text-color);
    }
    .guard-actions { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 18px; }
    .guard-actions button { min-height: 44px; padding: 9px 12px; }

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
    globalThis.addEventListener?.("beforeunload", this.handleBeforeUnload);
    globalThis.addEventListener?.("online", this.handleConnectivity);
    globalThis.addEventListener?.("offline", this.handleConnectivity);
  }

  disconnectedCallback(): void {
    globalThis.removeEventListener?.("popstate", this.handlePopState);
    globalThis.removeEventListener?.("beforeunload", this.handleBeforeUnload);
    globalThis.removeEventListener?.("online", this.handleConnectivity);
    globalThis.removeEventListener?.("offline", this.handleConnectivity);
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
    const parsed = parseRoute(globalThis.location?.pathname ?? "/locklearn");
    const next = isRouteVisible(parsed, this.profiles) ? parsed : "home";
    if (this.managementDirty && next !== this.activeRoute) {
      this.pendingNavigation = { kind: "route", route: next };
      globalThis.history?.replaceState({}, "", routePath(this.activeRoute));
      this.requestUpdate();
      return;
    }
    this.activeRoute = next;
  };

  private readonly handleBeforeUnload = (event: BeforeUnloadEvent): void => {
    if (!this.managementDirty) return;
    event.preventDefault();
    event.returnValue = "";
  };

  private readonly handleConnectivity = (): void => {
    this.online = globalThis.navigator?.onLine ?? true;
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
      const { bootstrapState, profiles } = await withTimeout((async () => {
        const bootstrapState = await bootstrap(this.hass!);
        const profiles = await listVisibleProfiles(this.hass!);
        return { bootstrapState, profiles };
      })(), 10_000);
      if (generation !== this.loadGeneration) return;

      this.bootstrapState = bootstrapState;
      this.profiles = profiles;
      this.selectedProfileId = defaultProfileId(profiles, bootstrapState);
      const requested = parseRoute(globalThis.location?.pathname ?? bootstrapState.panel_path);
      this.activeRoute = isRouteVisible(requested, profiles) ? requested : "home";
      this.status = "ready";
      this.loadFailures = 0;
      this.diagnosticNotice = "";
      void this.loadDashboard();
    } catch (error) {
      if (generation !== this.loadGeneration) return;
      if (error instanceof ProtocolMismatchError) {
        this.bootstrapState = {
          frontend_protocol: error.backendProtocol,
          backend_version: error.backendVersion,
          panel_path: "/locklearn",
          authenticated_user_id: "",
          is_admin: false,
          personal_profile: null,
        };
        this.status = "protocol-mismatch";
        return;
      }
      this.errorMessage = error instanceof Error ? error.message : String(error);
      this.loadFailures += 1;
      this.status = "error";
    }
  }

  private selectRoute(route: RouteName): void {
    if (!isRouteVisible(route, this.profiles) || route === this.activeRoute) return;
    if (this.managementDirty) {
      this.pendingNavigation = { kind: "route", route };
      return;
    }
    this.applyNavigation({ kind: "route", route });
  }

  private selectProfile(event: Event): void {
    const target = event.currentTarget;
    if (!(target instanceof HTMLSelectElement)) return;
    const profileId = target.value;
    if (
      !this.profiles.some((profile) => profile.profile_id === profileId) ||
      profileId === this.selectedProfileId
    ) {
      return;
    }
    if (this.managementDirty) {
      this.pendingNavigation = { kind: "profile", profileId };
      this.requestUpdate();
      return;
    }
    this.applyNavigation({ kind: "profile", profileId });
  }

  private applyNavigation(pending: PendingNavigation): void {
    if (pending.kind === "route") {
      this.activeRoute = pending.route;
      navigateToRoute(pending.route);
      return;
    }
    this.selectedProfileId = pending.profileId;
    this.handoffSession = undefined;
    void this.loadDashboard();
  }

  private handleManagementDirty(event: CustomEvent<{ dirty: boolean }>): void {
    this.managementDirty = Boolean(event.detail?.dirty);
  }

  private managementView(): LockLearnManagementView | null {
    return this.renderRoot.querySelector<LockLearnManagementView>(
      "locklearn-management-view",
    );
  }

  private async saveAndNavigate(): Promise<void> {
    const pending = this.pendingNavigation;
    const management = this.managementView();
    if (pending === undefined || management === null) return;
    this.navigationSaving = true;
    try {
      const saved = await management.saveDirtyScopes();
      if (!saved) return;
      this.managementDirty = false;
      this.pendingNavigation = undefined;
      this.applyNavigation(pending);
    } finally {
      this.navigationSaving = false;
    }
  }

  private discardAndNavigate(): void {
    const pending = this.pendingNavigation;
    if (pending === undefined) return;
    this.managementView()?.discardDirtyScopes();
    this.managementDirty = false;
    this.pendingNavigation = undefined;
    this.applyNavigation(pending);
  }

  private stayOnDirtyForm(): void {
    this.pendingNavigation = undefined;
    this.requestUpdate();
  }

  private openTargetedSession(event: CustomEvent<{ session: SessionState }>): void {
    const session = event.detail?.session;
    if (
      session === undefined ||
      this.selectedProfileId === null ||
      session.profile_id !== this.selectedProfileId
    ) {
      return;
    }
    this.handoffSession = session;
    const route = ["quiz", "calibration"].includes(session.type) ? "quiz" : "learn";
    this.activeRoute = route;
    navigateToRoute(route);
  }

  private clearSessionHandoff(): void {
    this.handoffSession = undefined;
  }

  private async refreshManagement(): Promise<void> {
    if (this.hass === undefined) return;
    const selected = this.selectedProfileId;
    try {
      const profiles = await listVisibleProfiles(this.hass);
      this.profiles = profiles;
      this.selectedProfileId =
        selected !== null && profiles.some((profile) => profile.profile_id === selected)
          ? selected
          : this.bootstrapState === undefined
            ? (profiles[0]?.profile_id ?? null)
            : defaultProfileId(profiles, this.bootstrapState);
      if (!isRouteVisible(this.activeRoute, profiles)) {
        this.activeRoute = "home";
        navigateToRoute("home");
      }
      await this.loadDashboard();
    } catch (error) {
      this.errorMessage = error instanceof Error ? error.message : String(error);
    }
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

  private async copyDiagnostic(): Promise<void> {
    const diagnostic = [
      `LockLearn frontend protocol: ${FRONTEND_PROTOCOL_VERSION}`,
      `route: ${this.activeRoute}`,
      `online: ${this.online}`,
      `failures: ${this.loadFailures}`,
      `error: ${this.errorMessage}`,
    ].join("\n");
    try {
      await globalThis.navigator?.clipboard?.writeText(diagnostic);
      this.diagnosticNotice = this.t("state.diagnosticCopied");
    } catch {
      this.diagnosticNotice = diagnostic;
    }
  }

  private goHome(): void {
    globalThis.location?.assign("/");
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
            <div class="guard-actions">
              <button class="primary-button" @click=${() => void this.load()}>
                ${this.t("state.retry")}
              </button>
              <button @click=${this.goHome}>${this.t("state.home")}</button>
              ${this.loadFailures >= 3
                ? html`<button @click=${() => void this.copyDiagnostic()}>
                    ${this.t("state.copyDiagnostic")}
                  </button>`
                : nothing}
            </div>
            ${this.diagnosticNotice
              ? html`<p class="meta" role="status">${this.diagnosticNotice}</p>`
              : nothing}
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
        ${this.online
          ? nothing
          : html`<div class="connection-banner" role="status">${this.t("state.offline")}</div>`}
        <main>
          ${this.profiles.length === 0
            ? html`<locklearn-management-view
                .hass=${this.hass}
                .profile=${undefined}
                .route=${"profiles" as ManagementRoute}
                @locklearn-refresh=${() => void this.refreshManagement()}
              ></locklearn-management-view>`
            : this.activeRoute === "home"
              ? this.renderHome()
              : this.activeRoute === "learn"
                ? html`<locklearn-learn-view
                    .hass=${this.hass}
                    .profile=${this.profiles.find(
                      (profile) => profile.profile_id === this.selectedProfileId,
                    )}
                    .dashboard=${this.dashboard}
                    .externalSession=${this.handoffSession}
                    @locklearn-session-handoff-consumed=${this.clearSessionHandoff}
                    @locklearn-open-session=${this.openTargetedSession}
                  ></locklearn-learn-view>`
                : this.activeRoute === "quiz"
                  ? html`<locklearn-quiz-view
                      .hass=${this.hass}
                      .profile=${this.profiles.find(
                        (profile) => profile.profile_id === this.selectedProfileId,
                      )}
                      .dashboard=${this.dashboard}
                      .externalSession=${this.handoffSession}
                      @locklearn-session-handoff-consumed=${this.clearSessionHandoff}
                      @locklearn-open-session=${this.openTargetedSession}
                    ></locklearn-quiz-view>`
                  : this.activeRoute === "stats"
                    ? html`<locklearn-stats-view
                        .hass=${this.hass}
                        .profile=${this.profiles.find(
                          (profile) => profile.profile_id === this.selectedProfileId,
                        )}
                        @locklearn-open-session=${this.openTargetedSession}
                      ></locklearn-stats-view>`
                    : this.activeRoute === "sources"
                    ? html`<locklearn-dataset-view
                        .hass=${this.hass}
                        .admin=${this.bootstrapState?.is_admin ?? false}
                        @locklearn-refresh=${() => void this.refreshManagement()}
                      ></locklearn-dataset-view>`
                    : ["profiles", "tracks", "packs", "settings"].includes(this.activeRoute)
                    ? html`<locklearn-management-view
                        .hass=${this.hass}
                        .profile=${this.profiles.find(
                          (profile) => profile.profile_id === this.selectedProfileId,
                        )}
                        .route=${this.activeRoute as ManagementRoute}
                        @locklearn-refresh=${() => void this.refreshManagement()}
                        @locklearn-dirty-state-changed=${this.handleManagementDirty}
                      ></locklearn-management-view>`
                    : html`<section class="page">
                    <h1>${this.routeLabel(this.activeRoute)}</h1>
                    <p>${this.t("route.placeholder")}</p>
                  </section>`}
        </main>
        ${this.pendingNavigation === undefined
          ? nothing
          : html`<div class="guard-backdrop">
              <section
                class="guard-dialog"
                role="dialog"
                aria-modal="true"
                aria-labelledby="unsaved-title"
              >
                <h2 id="unsaved-title">${this.t("form.navigationTitle")}</h2>
                <p>${this.t("form.navigationBody")}</p>
                <div class="guard-actions">
                  <button
                    class="primary-button"
                    @click=${() => void this.saveAndNavigate()}
                    ?disabled=${this.navigationSaving}
                  >
                    ${this.navigationSaving
                      ? this.t("form.saving")
                      : this.t("form.saveAndLeave")}
                  </button>
                  <button
                    @click=${this.discardAndNavigate}
                    ?disabled=${this.navigationSaving}
                  >
                    ${this.t("form.leaveWithoutSaving")}
                  </button>
                  <button
                    @click=${this.stayOnDirtyForm}
                    ?disabled=${this.navigationSaving}
                  >
                    ${this.t("form.stay")}
                  </button>
                </div>
              </section>
            </div>`}
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
