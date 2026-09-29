import { LitElement, css, html, nothing } from "lit";
import { property, state } from "lit/decorators.js";

import { interactiveAccessibilityStyles } from "./content-renderer";
import { languageFallback, translate, type UiLanguage } from "./i18n";
import {
  createNotificationTarget,
  createProfile,
  createTrack,
  deleteProfile,
  deleteTrack,
  discoverNotificationTargets,
  integratePackUpdate,
  listPacks,
  listNotificationTargets,
  listProfileMembers,
  listShareTargets,
  listTracks,
  previewPackUpdate,
  previewTrackPlan,
  removeProfileMember,
  setTrackPlan,
  shareProfile,
  testNotificationTarget,
  updateNotificationTarget,
  updateProfile,
  updateTrack,
  type HomeAssistantLike,
  type LearningPlanInput,
  type LoadForecast,
  type NotificationTargetCandidate,
  type NotificationTargetSummary,
  type PackVersionDiff,
  type PackVersionRecord,
  type ProfileMember,
  type ProfileRole,
  type ShareTarget,
  type TrackRecord,
  type VisibleProfile,
} from "./protocol";

export type ManagementRoute = "profiles" | "tracks" | "packs" | "settings";

function asInt(value: FormDataEntryValue | null, fallback: number, min: number): number {
  const parsed = Number.parseInt(String(value ?? ""), 10);
  return Number.isFinite(parsed) && parsed >= min ? parsed : fallback;
}

function asOptionalInt(
  value: FormDataEntryValue | null,
  min: number,
): number | null {
  const raw = String(value ?? "").trim();
  if (raw === "") return null;
  const parsed = Number.parseInt(raw, 10);
  return Number.isFinite(parsed) && parsed >= min ? parsed : null;
}

function asFloat(
  value: FormDataEntryValue | null,
  fallback: number,
  min: number,
  max: number,
): number {
  const parsed = Number.parseFloat(String(value ?? ""));
  return Number.isFinite(parsed) && parsed >= min && parsed <= max ? parsed : fallback;
}

export function errorMessage(error: unknown): string {
  if (error instanceof Error && error.message) return error.message;
  if (typeof error === "string") return error;
  if (typeof error === "object" && error !== null) {
    const record = error as Record<string, unknown>;
    if (typeof record.message === "string" && record.message) return record.message;
    if (typeof record.code === "string" && record.code) return record.code;
    try {
      return JSON.stringify(record);
    } catch {
      return "Unknown error";
    }
  }
  return String(error);
}

export function languageDisplayName(code: string, locale: UiLanguage): string {
  if (code === "ja-Latn") {
    return locale === "fr" ? "Japonais (rōmaji)" : "Japanese (romaji)";
  }
  try {
    const base = code.split("-", 1)[0] ?? code;
    const display = new Intl.DisplayNames([locale], { type: "language" }).of(base);
    return display ?? code;
  } catch {
    return code;
  }
}

function objectSetting(
  settings: Record<string, unknown> | undefined,
  key: string,
): Record<string, unknown> {
  const value = settings?.[key];
  return typeof value === "object" && value !== null
    ? (value as Record<string, unknown>)
    : {};
}

export function canManageProfileRole(role: ProfileRole | undefined): boolean {
  return role === "owner";
}

export function canEditTrackRole(role: ProfileRole | undefined): boolean {
  return role === "owner" || role === "editor";
}

export class LockLearnManagementView extends LitElement {
  @property({ attribute: false }) hass?: HomeAssistantLike;
  @property({ attribute: false }) profile?: VisibleProfile;
  @property({ attribute: false }) route: ManagementRoute = "profiles";

  @state() private tracks: TrackRecord[] = [];
  @state() private packs: PackVersionRecord[] = [];
  @state() private notificationTargets: NotificationTargetSummary[] = [];
  @state() private notificationCandidates: NotificationTargetCandidate[] = [];
  @state() private members: ProfileMember[] = [];
  @state() private shareTargets: ShareTarget[] = [];
  @state() private createTrackPackId = "";
  @state() private createTrackSource = "";
  @state() private forecasts: Record<string, LoadForecast | undefined> = {};
  @state() private forecastPlans: Record<string, LearningPlanInput | undefined> = {};
  @state() private packDiff?: PackVersionDiff;
  @state() private packDiffTrack = "";
  @state() private packDiffTarget = "";
  @state() private loading = false;
  @state() private errorMessage = "";
  @state() private notice = "";

  static styles = css`
    ${interactiveAccessibilityStyles}
    :host, .stack, .grid, .card, .form-grid, .actions, label, input, select, button {
      box-sizing: border-box;
      min-width: 0;
      max-width: 100%;
    }
    :host { display: block; }
    .stack { display: grid; gap: 16px; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit,minmax(280px,1fr)); gap: 14px; }
    .card {
      padding: 18px; border: 1px solid var(--divider-color); border-radius: 12px;
      background: var(--card-background-color,var(--primary-background-color));
    }
    .card h2, .card h3 { margin-top: 0; }
    .form-grid { display: grid; grid-template-columns: repeat(auto-fit,minmax(190px,1fr)); gap: 12px; }
    label { display: grid; gap: 5px; color: var(--secondary-text-color); font-size: .82rem; }
    input, select {
      width: 100%; padding: 9px; border: 1px solid var(--divider-color); border-radius: 8px;
      color: var(--primary-text-color); background: var(--card-background-color,var(--primary-background-color));
      font: inherit;
    }
    button {
      min-height: 40px; padding: 8px 12px; border: 1px solid var(--divider-color);
      border-radius: 8px; color: var(--primary-text-color); background: var(--secondary-background-color);
      font: inherit; cursor: pointer;
    }
    button.primary { border-color: var(--primary-color); color: var(--text-primary-color,white); background: var(--primary-color); }
    button:disabled { cursor: not-allowed; opacity: .55; }
    .actions { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
    .track-form { display: grid; gap: 14px; }
    .section-panel {
      margin-top: 14px;
      border: 1px solid var(--divider-color);
      border-radius: 10px;
      overflow: clip;
      background: var(--secondary-background-color);
    }
    .section-panel > summary {
      display: flex;
      align-items: center;
      gap: 9px;
      padding: 12px 14px;
      cursor: pointer;
      list-style: none;
      font-weight: 650;
      color: var(--primary-text-color);
      background: var(--card-background-color,var(--primary-background-color));
    }
    .section-panel > summary::-webkit-details-marker { display: none; }
    .section-panel > summary::before {
      content: "›";
      display: inline-block;
      font-size: 1.2rem;
      line-height: 1;
      transition: transform 120ms ease;
    }
    .section-panel[open] > summary::before { transform: rotate(90deg); }
    .section-body { padding: 14px; }
    .section-body > :first-child { margin-top: 0; }
    .section-body > :last-child { margin-bottom: 0; }
    .target-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit,minmax(300px,1fr));
      gap: 14px;
      margin-top: 14px;
    }
    .target-card {
      display: grid;
      align-content: start;
      gap: 12px;
      padding: 16px;
      border: 1px solid var(--divider-color);
      border-radius: 10px;
      background: var(--card-background-color,var(--primary-background-color));
    }
    .target-header { display: grid; gap: 3px; }
    .target-header h3 { margin: 0; }
    .target-card .section-panel { margin-top: 0; }
    .check-row {
      display: flex;
      align-items: center;
      gap: 8px;
      color: var(--primary-text-color);
      font-size: .9rem;
    }
    .check-row input { width: auto; }
    .track-summary {
      display: grid;
      gap: 4px;
      margin-bottom: 14px;
    }
    .danger-zone {
      margin-top: 18px;
      padding: 14px;
      border: 1px solid var(--error-color,var(--divider-color));
      border-radius: 9px;
      background: var(--secondary-background-color);
    }
    .danger-zone button {
      border-color: var(--error-color,var(--divider-color));
    }
    .muted, .meta { color: var(--secondary-text-color); }
    .meta { font-size: .82rem; overflow-wrap: anywhere; }
    .notice, .error, .warning { padding: 12px; border-radius: 9px; background: var(--secondary-background-color); line-height: 1.45; }
    .error, .warning { color: var(--error-color,var(--primary-text-color)); }
    dl { display: grid; grid-template-columns: minmax(150px,auto) 1fr; gap: 6px 12px; margin: 0; }
    dt { color: var(--secondary-text-color); }
    dd { margin: 0; overflow-wrap: anywhere; }
    ul { padding-left: 20px; }
    @media (max-width: 600px) {
      .grid, .form-grid, dl { grid-template-columns: 1fr; }
      .actions { flex-direction: column; align-items: stretch; }
      button { width: 100%; }
    }
  `;

  protected updated(changed: Map<PropertyKey, unknown>): void {
    if (changed.has("profile") || changed.has("route")) void this.load();
  }

  private locale(): UiLanguage {
    return languageFallback(
      this.hass?.locale?.language ?? this.hass?.language ?? globalThis.navigator?.language ?? "en",
    );
  }

  private t(key: Parameters<typeof translate>[1]): string {
    return translate(this.locale(), key);
  }

  private isOwner(): boolean {
    return canManageProfileRole(this.profile?.role);
  }

  private canEditTrack(): boolean {
    return canEditTrackRole(this.profile?.role);
  }

  private async load(): Promise<void> {
    if (this.hass === undefined) return;
    if (this.profile === undefined) {
      this.tracks = [];
      this.packs = [];
      this.notificationTargets = [];
      this.notificationCandidates = [];
      this.members = [];
      this.shareTargets = [];
      return;
    }
    this.loading = true;
    this.errorMessage = "";
    try {
      [this.tracks, this.packs] = await Promise.all([
        listTracks(this.hass, this.profile.profile_id),
        listPacks(this.hass),
      ]);
      this.notificationTargets = this.canEditTrack()
        ? await listNotificationTargets(this.hass, this.profile.profile_id)
        : [];
      this.notificationCandidates = this.isOwner() && this.route === "settings"
        ? await discoverNotificationTargets(this.hass, this.profile.profile_id)
        : [];
      if (!this.packs.some((item) => item.pack_version_id === this.createTrackPackId)) {
        this.createTrackPackId = this.packs[0]?.pack_version_id ?? "";
        this.createTrackSource = "";
      }
      if (this.isOwner() && this.route === "profiles") {
        [this.members, this.shareTargets] = await Promise.all([
          listProfileMembers(this.hass, this.profile.profile_id),
          listShareTargets(this.hass, this.profile.profile_id),
        ]);
      } else {
        this.members = [];
        this.shareTargets = [];
      }
    } catch (error) {
      this.errorMessage = errorMessage(error);
    } finally {
      this.loading = false;
    }
  }

  private async mutate(action: () => Promise<unknown>, message: string): Promise<void> {
    this.loading = true;
    this.errorMessage = "";
    try {
      await action();
      await this.load();
      this.notice = message;
      this.dispatchEvent(new CustomEvent("locklearn-refresh", { bubbles: true, composed: true }));
    } catch (error) {
      this.errorMessage = errorMessage(error);
    } finally {
      this.loading = false;
    }
  }

  protected render() {
    if (this.profile === undefined) {
      return html`<section class="stack">
        <h1>${this.t("manage.profiles")}</h1>
        ${this.errorMessage ? html`<div class="error" role="alert">${this.errorMessage}</div>` : nothing}
        ${this.notice ? html`<div class="notice" role="status">${this.notice}</div>` : nothing}
        ${this.renderCreateProfile()}
      </section>`;
    }
    return html`
      <section class="stack">
        <h1>${this.routeTitle()}</h1>
        ${this.errorMessage ? html`<div class="error" role="alert">${this.errorMessage}</div>` : nothing}
        ${this.notice ? html`<div class="notice" role="status">${this.notice}</div>` : nothing}
        ${this.route === "profiles" ? this.renderProfiles()
          : this.route === "tracks" ? this.renderTracks()
          : this.route === "packs" ? this.renderPacks()
          : this.renderSettings()}
      </section>
    `;
  }

  private routeTitle(): string {
    if (this.route === "profiles") return this.t("manage.profiles");
    if (this.route === "tracks") return this.t("manage.tracks");
    if (this.route === "packs") return this.t("manage.packs");
    return this.t("manage.settings");
  }

  private renderProfiles() {
    return html`
      <div class="grid">
        <article class="card">
          <h2>${this.profile?.name}</h2>
          <dl>
            <dt>${this.t("manage.role")}</dt><dd>${this.profile?.role}</dd>
            <dt>${this.t("manage.preset")}</dt><dd>${this.profile?.preset}</dd>
            <dt>${this.t("manage.timezone")}</dt><dd>${this.profile?.timezone}</dd>
            <dt>${this.t("manage.status")}</dt><dd>${this.profile?.status}</dd>
          </dl>
          ${this.isOwner() ? this.renderProfileForm() : html`<p class="muted">${this.t("manage.readOnly")}</p>`}
        </article>
        ${this.isOwner() ? this.renderSharing() : nothing}
      </div>
      ${this.renderCreateProfile()}
    `;
  }

  private renderProfileForm() {
    return html`
      <form class="form-grid" @submit=${(event: SubmitEvent) => {
        event.preventDefault();
        const data = new FormData(event.currentTarget as HTMLFormElement);
        if (this.hass === undefined || this.profile === undefined) return;
        void this.mutate(
          () => updateProfile(this.hass!, this.profile!.profile_id, {
            name: String(data.get("name") ?? "").trim(),
            timezone: String(data.get("timezone") ?? "").trim(),
            status: String(data.get("status") ?? "active") as "active" | "archived",
          }),
          this.t("manage.saved"),
        );
      }}>
        <label>${this.t("manage.name")}<input name="name" .value=${this.profile?.name ?? ""} required /></label>
        <label>${this.t("manage.timezone")}<input name="timezone" .value=${this.profile?.timezone ?? "UTC"} required /></label>
        <label>${this.t("manage.status")}
          <select name="status" .value=${this.profile?.status ?? "active"}>
            <option value="active">${this.t("manage.active")}</option>
            <option value="archived">${this.t("manage.archived")}</option>
          </select>
        </label>
        <div class="actions">
          <button class="primary" type="submit">${this.t("manage.save")}</button>
          <button type="button" @click=${() => this.archiveProfile()}>${this.t("manage.archiveProfile")}</button>
          <button type="button" @click=${() => this.deleteProfilePermanently()}>${this.t("manage.deletePermanently")}</button>
        </div>
      </form>
    `;
  }

  private renderSharing() {
    const memberIds = new Set(this.members.map((item) => item.ha_user_id));
    const targets = this.shareTargets.filter((item) => !memberIds.has(item.ha_user_id));
    const ownerCount = this.members.filter((item) => item.role === "owner").length;
    return html`
      <article class="card">
        <h2>${this.t("manage.sharing")}</h2>
        <p class="muted">${this.t("manage.sharingHelp")}</p>
        ${this.members.length === 0 ? html`<p>${this.t("manage.none")}</p>` : html`
          <ul>${this.members.map((member) => html`<li>
            ${member.name}
            <select
              aria-label=${this.t("manage.role")}
              .value=${member.role}
              ?disabled=${member.role === "owner" && ownerCount === 1}
              @change=${(event: Event) => {
                const target = event.currentTarget;
                if (target instanceof HTMLSelectElement) {
                  void this.changeMemberRole(member.ha_user_id, target.value as ProfileRole);
                }
              }}
            >
              <option value="viewer">viewer</option>
              <option value="editor">editor</option>
              <option value="owner">owner</option>
            </select>
            ${member.role === "owner" && ownerCount === 1 ? nothing : html`
              <button @click=${() => this.removeMember(member.ha_user_id)}>${this.t("manage.remove")}</button>`}
          </li>`)}</ul>`}
        ${targets.length === 0 ? nothing : html`
          <form class="form-grid" @submit=${(event: SubmitEvent) => {
            event.preventDefault();
            const data = new FormData(event.currentTarget as HTMLFormElement);
            void this.addMember(
              String(data.get("user") ?? ""),
              String(data.get("role") ?? "viewer") as ProfileRole,
            );
          }}>
            <label>${this.t("manage.user")}<select name="user">
              ${targets.map((target) => html`<option value=${target.ha_user_id}>${target.name}</option>`)}
            </select></label>
            <label>${this.t("manage.role")}<select name="role">
              <option value="viewer">viewer</option><option value="editor">editor</option><option value="owner">owner</option>
            </select></label>
            <div class="actions"><button type="submit">${this.t("manage.share")}</button></div>
          </form>`}
      </article>
    `;
  }

  private async addMember(userId: string, role: ProfileRole): Promise<void> {
    if (!userId || this.hass === undefined || this.profile === undefined) return;
    await this.mutate(() => shareProfile(this.hass!, this.profile!.profile_id, userId, role), this.t("manage.saved"));
  }

  private async removeMember(userId: string): Promise<void> {
    if (this.hass === undefined || this.profile === undefined) return;
    if (!globalThis.confirm?.(this.t("manage.confirmRemoveMember"))) return;
    await this.mutate(() => removeProfileMember(this.hass!, this.profile!.profile_id, userId), this.t("manage.saved"));
  }

  private async changeMemberRole(userId: string, role: ProfileRole): Promise<void> {
    if (this.hass === undefined || this.profile === undefined) return;
    await this.mutate(
      () => shareProfile(this.hass!, this.profile!.profile_id, userId, role),
      this.t("manage.saved"),
    );
  }

  private async archiveProfile(): Promise<void> {
    if (this.hass === undefined || this.profile === undefined) return;
    if (!globalThis.confirm?.(this.t("manage.confirmArchiveProfile"))) return;
    await this.mutate(
      () => deleteProfile(this.hass!, this.profile!.profile_id, "archive"),
      this.t("manage.archivedNotice"),
    );
  }

  private async deleteProfilePermanently(): Promise<void> {
    if (this.hass === undefined || this.profile === undefined) return;
    const expected = `DELETE ${this.profile.profile_id}`;
    const confirmation = globalThis.prompt?.(
      `${this.t("manage.confirmDeletePermanently")} ${expected}`,
    );
    if (confirmation !== expected) return;
    await this.mutate(
      () => deleteProfile(
        this.hass!,
        this.profile!.profile_id,
        "delete_permanently",
        confirmation,
      ),
      this.t("manage.deleted"),
    );
  }

  private renderCreateProfile() {
    return html`
      <article class="card">
        <h2>${this.t("manage.createProfile")}</h2>
        <form class="form-grid" @submit=${(event: SubmitEvent) => {
          event.preventDefault();
          const data = new FormData(event.currentTarget as HTMLFormElement);
          if (this.hass === undefined) return;
          void this.mutate(
            () => createProfile(
              this.hass!,
              String(data.get("name") ?? "").trim(),
              String(data.get("preset") ?? "standard") as "child" | "standard" | "intensive" | "custom",
              String(data.get("timezone") ?? "UTC").trim(),
            ),
            this.t("manage.created"),
          );
        }}>
          <label>${this.t("manage.name")}<input name="name" required /></label>
          <label>${this.t("manage.preset")}<select name="preset">
            <option value="child">child</option><option value="standard">standard</option>
            <option value="intensive">intensive</option><option value="custom">custom</option>
          </select></label>
          <label>${this.t("manage.timezone")}<input name="timezone" .value=${this.profile?.timezone ?? Intl.DateTimeFormat().resolvedOptions().timeZone ?? "UTC"} required /></label>
          <div class="actions"><button class="primary" type="submit">${this.t("manage.create")}</button></div>
        </form>
      </article>
    `;
  }

  private renderTracks() {
    return html`
      ${this.tracks.length === 0 ? html`<div class="card"><p>${this.t("manage.noTracks")}</p></div>` : html`
        <div class="grid">${this.tracks.map((track) => this.renderTrack(track))}</div>`}
      ${this.canEditTrack() ? this.renderCreateTrack() : html`<div class="card"><p>${this.t("manage.readOnly")}</p></div>`}
    `;
  }

  private packDirections(packVersionId: string) {
    return this.packs.find((pack) => pack.pack_version_id === packVersionId)?.directions ?? [];
  }

  private sourceLanguages(packVersionId: string): string[] {
    return [...new Set(
      this.packDirections(packVersionId).map((direction) => direction.source_language),
    )].sort((left, right) => left.localeCompare(right));
  }

  private targetLanguages(packVersionId: string, sourceLanguage: string): string[] {
    return [...new Set(
      this.packDirections(packVersionId)
        .filter((direction) => direction.source_language === sourceLanguage)
        .map((direction) => direction.target_language),
    )].sort((left, right) => left.localeCompare(right));
  }

  private renderTrack(track: TrackRecord) {
    const scheduler = objectSetting(track.settings, "scheduler");
    const targetIds = Array.isArray(scheduler.target_ids)
      ? scheduler.target_ids.map(String)
      : [];
    const weights = track.content_weights ?? {};
    const sourceLabel = languageDisplayName(track.source_language ?? "", this.locale());
    const targetLabel = languageDisplayName(track.target_language ?? "", this.locale());
    return html`
      <article class="card">
        <div class="track-summary">
          <h2>${track.name}</h2>
          <p class="meta">${sourceLabel} → ${targetLabel} · ${
  track.status === "active"
    ? this.t("manage.active")
    : track.status === "paused"
      ? this.t("manage.paused")
      : this.t("manage.archived")
}</p>
          <p class="meta">${this.t("manage.packVersion")}: ${track.pack_version_id ?? "—"}</p>
        </div>
        ${this.canEditTrack() ? html`
          <form class="track-form" @submit=${(event: SubmitEvent) => {
            event.preventDefault();
            const data = new FormData(event.currentTarget as HTMLFormElement);
            if (this.hass === undefined) return;
            const selectedTargets = data.getAll("notificationTarget").map(String);
            const contentWeights = {
              vocabulary: asFloat(data.get("weightVocabulary"), Number(weights.vocabulary ?? 1), 0, 100),
              kanji: asFloat(data.get("weightKanji"), Number(weights.kanji ?? 1), 0, 100),
              grammar: asFloat(data.get("weightGrammar"), Number(weights.grammar ?? 1), 0, 100),
              expression: asFloat(data.get("weightExpression"), Number(weights.expression ?? 1), 0, 100),
            };
            void this.mutate(() => updateTrack(this.hass!, track.track_id, {
              name: String(data.get("name") ?? track.name),
              source_language: String(data.get("source") ?? track.source_language ?? "").trim(),
              target_language: String(data.get("target") ?? track.target_language ?? "").trim(),
              status: String(data.get("status") ?? track.status),
              priority: asInt(data.get("priority"), track.priority, 1),
              content_weights: contentWeights,
              scheduler_settings: {
                learning_count: asInt(data.get("learningCount"), Number(scheduler.learning_count ?? 0), 0),
                quiz_count: asInt(data.get("quizCount"), Number(scheduler.quiz_count ?? 0), 0),
                ...(selectedTargets.length === 0 ? {} : { target_ids: selectedTargets }),
              },
            }), this.t("manage.saved"));
          }}>
            <div class="form-grid">
              <label>${this.t("manage.name")}<input name="name" .value=${track.name} /></label>
              <label>${this.t("manage.status")}
                <select name="status" .value=${track.status}>
                  <option value="active">${this.t("manage.active")}</option>
                  <option value="paused">${this.t("manage.paused")}</option>
                  <option value="archived">${this.t("manage.archived")}</option>
                </select>
              </label>
              <label>${this.t("manage.sourceLanguage")}
                <select name="source" .value=${track.source_language ?? ""} required>
                  ${this.sourceLanguages(track.pack_version_id ?? "").map((language) => html`
                    <option value=${language}>${languageDisplayName(language, this.locale())}</option>
                  `)}
                </select>
              </label>
              <label>${this.t("manage.targetLanguage")}
                <select name="target" .value=${track.target_language ?? ""} required>
                  ${this.targetLanguages(
                    track.pack_version_id ?? "",
                    track.source_language ?? "",
                  ).map((language) => html`
                    <option value=${language}>${languageDisplayName(language, this.locale())}</option>
                  `)}
                </select>
              </label>
            </div>

            <div class="actions">
              <button class="primary" type="submit">${this.t("manage.save")}</button>
            </div>

            <details class="section-panel">
              <summary>${this.t("manage.advancedTrackSettings")}</summary>
              <div class="section-body">
                <p class="muted">${this.t("manage.advancedTrackSettingsHelp")}</p>
                <div class="form-grid">
                  <label>${this.t("manage.priority")}<input name="priority" type="number" min="1" .value=${String(track.priority)} /></label>
                  <label>${this.t("manage.weightVocabulary")}<input name="weightVocabulary" type="number" min="0" step=".1" .value=${String(weights.vocabulary ?? 1)} /></label>
                  <label>${this.t("manage.weightKanji")}<input name="weightKanji" type="number" min="0" step=".1" .value=${String(weights.kanji ?? 1)} /></label>
                  <label>${this.t("manage.weightGrammar")}<input name="weightGrammar" type="number" min="0" step=".1" .value=${String(weights.grammar ?? 1)} /></label>
                  <label>${this.t("manage.weightExpression")}<input name="weightExpression" type="number" min="0" step=".1" .value=${String(weights.expression ?? 1)} /></label>
                  <label>${this.t("manage.learningNotifications")}<input name="learningCount" type="number" min="0" .value=${String(scheduler.learning_count ?? 0)} /></label>
                  <label>${this.t("manage.quizNotifications")}<input name="quizCount" type="number" min="0" .value=${String(scheduler.quiz_count ?? 0)} /></label>
                  <label>${this.t("manage.notificationTargets")}
                    <select name="notificationTarget" multiple size=${Math.min(4, Math.max(2, this.notificationTargets.length))}>
                      ${this.notificationTargets.map((target) => html`
                        <option value=${target.target_id} ?selected=${targetIds.includes(target.target_id)}>
                          ${target.friendly_name} · ${target.platform}
                        </option>`)}
                    </select>
                    <span class="meta">${this.notificationTargets.length === 0
                      ? this.t("manage.noNotificationTargets")
                      : this.t("manage.notificationTargetsHelp")}</span>
                  </label>
                </div>
              </div>
            </details>
          </form>

          <details class="section-panel">
            <summary>${this.t("manage.plan")}</summary>
            <div class="section-body">${this.renderPlan(track)}</div>
          </details>

          <div class="danger-zone">
            <strong>${this.t("manage.dangerZone")}</strong>
            <p class="muted">${this.t("manage.deleteTrackHelp")}</p>
            <button type="button" @click=${() => this.removeTrack(track.track_id, track.name)}>
              ${this.t("manage.deleteTrack")}
            </button>
          </div>
        ` : nothing}
      </article>
    `;
  }

  private renderCreateTrack() {
    const selectedPackId = this.createTrackPackId || this.packs[0]?.pack_version_id || "";
    const sources = this.sourceLanguages(selectedPackId);
    const selectedSource = sources.includes(this.createTrackSource)
      ? this.createTrackSource
      : sources[0] ?? "";
    const targets = this.targetLanguages(selectedPackId, selectedSource);
    return html`
      <article class="card">
        <h2>${this.t("manage.createTrack")}</h2>
        ${this.packs.length === 0 ? html`<p>${this.t("manage.noPacks")}</p>` : html`
          <form class="form-grid" @submit=${(event: SubmitEvent) => {
            event.preventDefault();
            const data = new FormData(event.currentTarget as HTMLFormElement);
            if (this.hass === undefined || this.profile === undefined) return;
            void this.mutate(() => createTrack(this.hass!, {
              profile_id: this.profile!.profile_id,
              name: String(data.get("name") ?? "").trim(),
              pack_version_id: String(data.get("pack") ?? ""),
              source_language: String(data.get("source") ?? "").trim(),
              target_language: String(data.get("target") ?? "").trim(),
              priority: asInt(data.get("priority"), 1, 1),
            }), this.t("manage.created"));
          }}>
            <label>${this.t("manage.name")}<input name="name" required /></label>
            <label>${this.t("manage.pack")}
              <select
                name="pack"
                .value=${selectedPackId}
                @change=${(event: Event) => {
                  const target = event.currentTarget;
                  if (!(target instanceof HTMLSelectElement)) return;
                  this.createTrackPackId = target.value;
                  this.createTrackSource = "";
                }}
              >
                ${this.packs.map((pack) => html`
                  <option value=${pack.pack_version_id}>${pack.name} · ${pack.version}</option>
                `)}
              </select>
            </label>
            ${sources.length === 0 ? html`
              <p class="warning">${this.t("manage.noPackDirections")}</p>
            ` : html`
              <label>${this.t("manage.sourceLanguage")}
                <select
                  name="source"
                  .value=${selectedSource}
                  required
                  @change=${(event: Event) => {
                    const target = event.currentTarget;
                    if (target instanceof HTMLSelectElement) {
                      this.createTrackSource = target.value;
                    }
                  }}
                >
                  ${sources.map((language) => html`
                    <option value=${language}>${languageDisplayName(language, this.locale())}</option>
                  `)}
                </select>
              </label>
              <label>${this.t("manage.targetLanguage")}
                <select name="target" required>
                  ${targets.map((language) => html`
                    <option value=${language}>${languageDisplayName(language, this.locale())}</option>
                  `)}
                </select>
              </label>
            `}
            <label>${this.t("manage.priority")}<input name="priority" type="number" min="1" value="1" /></label>
            <div class="actions">
              <button class="primary" type="submit" ?disabled=${sources.length === 0 || targets.length === 0}>
                ${this.t("manage.create")}
              </button>
            </div>
          </form>`}
      </article>
    `;
  }

  private async removeTrack(trackId: string, trackName: string): Promise<void> {
    if (this.hass === undefined) return;
    if (!globalThis.confirm?.(`${this.t("manage.confirmDeleteTrack")} "${trackName}"?`)) return;
    await this.mutate(() => deleteTrack(this.hass!, trackId), this.t("manage.trackDeleted"));
  }

  private planFrom(form: HTMLFormElement): LearningPlanInput {
    const data = new FormData(form);
    return {
      max_new_per_day_cards: asInt(data.get("new"), 0, 0),
      max_reviews_per_day_cards: asInt(data.get("reviews"), 50, 1),
      max_notification_new_teasers: asInt(data.get("teasers"), 2, 0),
      target_date: String(data.get("date") ?? "").trim() || null,
      target_coverage: asFloat(data.get("coverage"), 1, .01, 1),
      target_retention: asFloat(data.get("retention"), .9, .01, 1),
    };
  }

  private renderPlan(track: TrackRecord) {
    const raw = objectSetting(track.settings, "learning_plan");
    const profileNew = Number(this.profile?.settings?.max_new_per_day_cards ?? 8);
    const forecast = this.forecasts[track.track_id];
    return html`
      <div class="stack">
        <p class="muted">${this.t("manage.planHelp")}</p>
        <form class="stack" @submit=${(event: SubmitEvent) => {
          event.preventDefault();
          if (this.hass === undefined) return;
          const plan = this.planFrom(event.currentTarget as HTMLFormElement);
          this.loading = true;
          this.errorMessage = "";
          void previewTrackPlan(this.hass, track.track_id, plan)
            .then((nextForecast) => {
              this.forecasts = { ...this.forecasts, [track.track_id]: nextForecast };
              this.forecastPlans = { ...this.forecastPlans, [track.track_id]: plan };
            })
            .catch((error: unknown) => {
              this.forecasts = { ...this.forecasts, [track.track_id]: undefined };
              this.errorMessage = `${this.t("manage.previewFailed")} ${errorMessage(error)}`;
            })
            .finally(() => { this.loading = false; });
        }}>
          <strong>${this.t("manage.basicPlan")}</strong>
          <div class="form-grid">
            <label>
              ${this.t("manage.newPerDay")}
              <input name="new" type="number" min="0" .value=${String(raw.max_new_per_day_cards ?? profileNew)} />
              <span class="meta">${this.t("manage.newPerDayHelp")}</span>
            </label>
            <label>
              ${this.t("manage.reviewsPerDay")}
              <input name="reviews" type="number" min="1" .value=${String(raw.max_reviews_per_day_cards ?? 50)} />
              <span class="meta">${this.t("manage.reviewsPerDayHelp")}</span>
            </label>
            <label>
              ${this.t("manage.targetDate")}
              <input name="date" type="date" .value=${String(raw.target_date ?? "")} />
              <span class="meta">${this.t("manage.targetDateHelp")}</span>
            </label>
          </div>
          <details class="section-panel">
            <summary>${this.t("manage.advancedPlan")}</summary>
            <div class="section-body form-grid">
              <label>
                ${this.t("manage.notificationTeasers")}
                <input name="teasers" type="number" min="0" .value=${String(raw.max_notification_new_teasers ?? Math.min(2, profileNew))} />
                <span class="meta">${this.t("manage.notificationTeasersHelp")}</span>
              </label>
              <label>
                ${this.t("manage.coverage")}
                <input name="coverage" type="number" min=".01" max="1" step=".01" .value=${String(raw.target_coverage ?? 1)} />
                <span class="meta">${this.t("manage.coverageHelp")}</span>
              </label>
              <label>
                ${this.t("manage.retention")}
                <input name="retention" type="number" min=".01" max="1" step=".01" .value=${String(raw.target_retention ?? .9)} />
                <span class="meta">${this.t("manage.retentionHelp")}</span>
              </label>
            </div>
          </details>
          <p class="muted">${this.t("manage.planPreviewHelp")}</p>
          <div class="actions"><button class="primary" type="submit">${this.t("manage.preview")}</button></div>
        </form>
        ${forecast === undefined ? nothing : this.renderForecast(track, forecast)}
      </div>
    `;
  }

  private forecastWarning(item: string): string {
    if (item === "target_date_requires_more_new_cards_than_daily_quota") {
      return this.t("manage.warningTargetDate");
    }
    if (item === "review_load_exceeds_quota_in_3_weeks") {
      return this.t("manage.warningReviews3Weeks");
    }
    if (item === "review_load_exceeds_quota_in_3_months") {
      return this.t("manage.warningReviews3Months");
    }
    if (item === "current_due_backlog_exceeds_review_quota") {
      return this.t("manage.warningDueBacklog");
    }
    return item;
  }

  private renderForecast(track: TrackRecord, forecast: LoadForecast) {
    const invalidZeroSnapshot = forecast.selected_cards === 0;
    return html`
      <div class=${forecast.warnings.length > 0 || invalidZeroSnapshot ? "warning" : "notice"}>
        <strong>${this.t("manage.forecast")}</strong>
        ${invalidZeroSnapshot ? html`<p>${this.t("manage.forecastZeroWarning")}</p>` : nothing}
        <h3>${this.t("manage.forecastCurrent")}</h3>
        <dl>
          <dt>${this.t("manage.selectedCards")}</dt><dd>${forecast.selected_cards}</dd>
          <dt>${this.t("manage.introducedCards")}</dt><dd>${forecast.introduced_cards}</dd>
          <dt>${this.t("manage.targetCards")}</dt><dd>${forecast.target_cards}</dd>
          <dt>${this.t("manage.cardsRemaining")}</dt><dd>${forecast.remaining_target_cards}</dd>
          <dt>${this.t("manage.dueNow")}</dt><dd>${forecast.due_now}</dd>
          <dt>${this.t("manage.requiredNew")}</dt><dd>${forecast.required_new_per_day}</dd>
          <dt>${this.t("manage.plannedNew")}</dt><dd>${forecast.planned_new_per_day}</dd>
        </dl>
        <h3>${this.t("manage.forecast")}</h3>
        <dl>
          <dt>${this.t("manage.reviews3Weeks")}</dt><dd>${forecast.reviews_per_day_in_3_weeks}</dd>
          <dt>${this.t("manage.reviews3Months")}</dt><dd>${forecast.reviews_per_day_in_3_months}</dd>
          <dt>${this.t("manage.notifications3Weeks")}</dt><dd>${forecast.notification_deliverable_in_3_weeks}</dd>
          <dt>${this.t("manage.notifications3Months")}</dt><dd>${forecast.notification_deliverable_in_3_months}</dd>
          <dt>${this.t("manage.sessionLoad3Weeks")}</dt><dd>${forecast.active_session_cards_in_3_weeks}</dd>
          <dt>${this.t("manage.sessionLoad3Months")}</dt><dd>${forecast.active_session_cards_in_3_months}</dd>
        </dl>
        <details class="section-panel">
          <summary>${this.t("manage.forecastMethod")}</summary>
          <div class="section-body"><p class="muted">${this.t("manage.forecastMethodHelp")}</p></div>
        </details>
        ${forecast.warnings.length === 0 ? nothing : html`<ul>${forecast.warnings.map((item) => html`<li>${this.forecastWarning(item)}</li>`)}</ul>`}
        <div class="actions">
          <button class="primary" @click=${() => this.applyPlan(track)} ?disabled=${invalidZeroSnapshot}>
            ${this.t("manage.applyPlan")}
          </button>
        </div>
      </div>
    `;
  }

  private async applyPlan(track: TrackRecord): Promise<void> {
    const plan = this.forecastPlans[track.track_id];
    if (this.hass === undefined || plan === undefined) return;
    await this.mutate(() => setTrackPlan(this.hass!, track.track_id, plan), this.t("manage.saved"));
  }

  private renderPacks() {
    return html`
      <div class="grid">${this.packs.map((pack) => html`
        <article class="card">
          <h2>${pack.name}</h2><p>${pack.version}</p>
          <p class="meta">${pack.total_items} items · ${pack.total_cards} cards</p>
        </article>`)}</div>
      ${this.canEditTrack() ? this.renderPackUpdates() : nothing}
    `;
  }

  private renderPackUpdates() {
    const candidates = this.tracks.flatMap((track) => {
      const current = this.packs.find((pack) => pack.pack_version_id === track.pack_version_id);
      if (current === undefined) return [];
      return this.packs
        .filter((pack) => pack.pack_id === current.pack_id && pack.pack_version_id !== current.pack_version_id)
        .map((pack) => ({ track, pack }));
    });
    return html`
      <article class="card">
        <h2>${this.t("manage.packUpdates")}</h2>
        ${candidates.length === 0 ? html`<p>${this.t("manage.noPackUpdates")}</p>` : html`
          <ul>${candidates.map(({ track, pack }) => html`<li>
            ${track.name}: ${track.pack_version_id} → ${pack.pack_version_id}
            <button @click=${() => this.previewUpdate(track, pack)}>${this.t("manage.preview")}</button>
          </li>`)}</ul>`}
        ${this.packDiff === undefined ? nothing : html`
          <div class="notice">
            <strong>${this.t("manage.packDiff")}</strong>
            <p>+ ${this.packDiff.added_learning_item_ids.length} · − ${this.packDiff.removed_learning_item_ids.length} · ~ ${this.packDiff.changed_learning_item_ids.length}</p>
            <button class="primary" @click=${() => this.applyPackUpdate()}>${this.t("manage.integrate")}</button>
          </div>`}
      </article>
    `;
  }

  private async previewUpdate(track: TrackRecord, pack: PackVersionRecord): Promise<void> {
    if (this.hass === undefined) return;
    this.loading = true;
    try {
      this.packDiff = await previewPackUpdate(this.hass, track.track_id, pack.pack_version_id);
      this.packDiffTrack = track.track_id;
      this.packDiffTarget = pack.pack_version_id;
    } catch (error) {
      this.errorMessage = errorMessage(error);
    } finally {
      this.loading = false;
    }
  }

  private async applyPackUpdate(): Promise<void> {
    if (this.hass === undefined || !this.packDiffTrack || !this.packDiffTarget) return;
    const trackId = this.packDiffTrack;
    const targetId = this.packDiffTarget;
    await this.mutate(
      () => integratePackUpdate(this.hass!, trackId, targetId),
      this.t("manage.packIntegrated"),
    );
    if (this.errorMessage === "") {
      this.packDiff = undefined;
      this.packDiffTrack = "";
      this.packDiffTarget = "";
    }
  }

  private renderNotificationTargets() {
    const available = this.notificationCandidates.filter(
      (candidate) => candidate.configured_target_id === null,
    );
    return html`
      <article class="card">
        <h2>${this.t("manage.notificationTargetSettings")}</h2>
        <p class="muted">${this.t("manage.notificationTargetSettingsHelp")}</p>

        <div class="section-panel">
          <div class="section-body">
            ${available.length === 0 ? html`
              <p class="muted">${this.t("manage.noAvailableNotificationDevices")}</p>
            ` : html`
              <form class="form-grid" @submit=${(event: SubmitEvent) => {
                event.preventDefault();
                const data = new FormData(event.currentTarget as HTMLFormElement);
                const deviceId = String(data.get("device") ?? "");
                if (!deviceId || this.hass === undefined || this.profile === undefined) return;
                void this.mutate(
                  () => createNotificationTarget(this.hass!, this.profile!.profile_id, deviceId),
                  this.t("manage.notificationTargetCreated"),
                );
              }}>
                <label>${this.t("manage.availableNotificationDevice")}
                  <select name="device" required>
                    ${available.map((candidate) => html`
                      <option value=${candidate.device_registry_id}>
                        ${candidate.friendly_name} · ${candidate.platform}
                        ${candidate.route_available ? "" : ` · ${this.t("manage.routeUnavailable")}`}
                      </option>
                    `)}
                  </select>
                </label>
                <div class="actions">
                  <button class="primary" type="submit">${this.t("manage.addNotificationTarget")}</button>
                </div>
              </form>
            `}
          </div>
        </div>

        ${this.notificationTargets.length === 0 ? html`
          <p>${this.t("manage.noNotificationTargets")}</p>
        ` : html`
          <div class="target-grid">
            ${this.notificationTargets.map((target) => html`
              <form class="target-card" @submit=${(event: SubmitEvent) => {
                event.preventDefault();
                const data = new FormData(event.currentTarget as HTMLFormElement);
                if (this.hass === undefined || this.profile === undefined) return;
                void this.mutate(
                  () => updateNotificationTarget(
                    this.hass!,
                    this.profile!.profile_id,
                    target.target_id,
                    {
                      friendly_name: String(data.get("friendlyName") ?? "").trim(),
                      shared_device: data.get("sharedDevice") === "on",
                      lockscreen_visibility: String(
                        data.get("lockscreenVisibility") ?? "private",
                      ) as "public" | "private" | "secret",
                      enabled: data.get("enabled") === "on",
                      minimum_gap_seconds: asOptionalInt(data.get("minimumGap"), 0),
                      maximum_notifications_per_hour: asOptionalInt(data.get("maxPerHour"), 1),
                      daily_push_budget: asOptionalInt(data.get("targetBudget"), 0),
                    },
                  ),
                  this.t("manage.notificationTargetUpdated"),
                );
              }}>
                <div class="target-header">
                  <h3>${target.friendly_name}</h3>
                  <span class="meta">${target.platform} · ${target.enabled ? this.t("manage.active") : this.t("manage.paused")}</span>
                </div>

                <div class="form-grid">
                  <label>${this.t("manage.name")}
                    <input name="friendlyName" .value=${target.friendly_name} required />
                  </label>
                  <label class="check-row">
                    <input name="enabled" type="checkbox" .checked=${target.enabled} />
                    ${this.t("manage.targetEnabled")}
                  </label>
                  <label class="check-row">
                    <input name="sharedDevice" type="checkbox" .checked=${target.shared_device} />
                    ${this.t("manage.sharedDevice")}
                  </label>
                </div>

                <details class="section-panel">
                  <summary>${this.t("manage.advancedTargetSettings")}</summary>
                  <div class="section-body">
                    <div class="form-grid">
                      <label>${this.t("manage.lockscreenVisibility")}
                        <select name="lockscreenVisibility" .value=${target.lockscreen_visibility}>
                          <option value="public">public</option>
                          <option value="private">private</option>
                          <option value="secret">secret</option>
                        </select>
                      </label>
                      <label>${this.t("manage.minimumGapSeconds")}
                        <input name="minimumGap" type="number" min="0" .value=${target.minimum_gap_seconds === null ? "" : String(target.minimum_gap_seconds)} />
                      </label>
                      <label>${this.t("manage.maximumPerHour")}
                        <input name="maxPerHour" type="number" min="1" .value=${target.maximum_notifications_per_hour === null ? "" : String(target.maximum_notifications_per_hour)} />
                      </label>
                      <label>${this.t("manage.targetPushBudget")}
                        <input name="targetBudget" type="number" min="0" .value=${target.daily_push_budget === null ? "" : String(target.daily_push_budget)} />
                      </label>
                    </div>
                    <p class="meta">
                      ${this.t("manage.capabilitiesConservative")} · ${target.device_registry_id}
                    </p>
                  </div>
                </details>

                <div class="actions">
                  <button class="primary" type="submit">${this.t("manage.save")}</button>
                  <button
                    type="button"
                    @click=${() => {
                      if (this.hass === undefined || this.profile === undefined) return;
                      void this.mutate(
                        () => testNotificationTarget(
                          this.hass!,
                          this.profile!.profile_id,
                          target.target_id,
                        ),
                        this.t("manage.notificationTestSent"),
                      );
                    }}
                  >
                    ${this.t("manage.testNotification")}
                  </button>
                </div>
              </form>
            `)}
          </div>
        `}
      </article>
    `;
  }

  private renderSettings() {
    if (!this.isOwner()) return html`<div class="card"><p>${this.t("manage.readOnly")}</p></div>`;
    const settings = this.profile?.settings ?? {};
    const quiet = objectSetting(settings, "quiet_hours");
    const scheduler = objectSetting(settings, "scheduler");
    const windows = Array.isArray(scheduler.active_windows)
      ? scheduler.active_windows
      : [];
    const firstWindow = typeof windows[0] === "object" && windows[0] !== null
      ? windows[0] as Record<string, unknown>
      : {};
    return html`
      <article class="card">
        <h2>${this.t("manage.profileSettings")}</h2>
        <p class="muted">${this.t("manage.presetInitialOnly")}: ${this.profile?.preset}</p>
        <form class="form-grid" @submit=${(event: SubmitEvent) => {
          event.preventDefault();
          const data = new FormData(event.currentTarget as HTMLFormElement);
          if (this.hass === undefined || this.profile === undefined) return;
          void this.mutate(() => updateProfile(this.hass!, this.profile!.profile_id, {
            settings_patch: {
              session_length_cards: asInt(data.get("session"), 20, 1),
              max_new_per_day_cards: asInt(data.get("new"), 8, 0),
              daily_push_budget: asInt(data.get("push"), 6, 0),
              quiet_hours: {
                start: String(data.get("quietStart") ?? "22:00"),
                end: String(data.get("quietEnd") ?? "08:00"),
              },
              scheduler: {
                ...scheduler,
                active_windows: [{
                  start: String(data.get("activeStart") ?? "08:00"),
                  end: String(data.get("activeEnd") ?? "20:00"),
                }],
              },
            },
          }), this.t("manage.saved"));
        }}>
          <label>${this.t("manage.sessionLength")}<input name="session" type="number" min="1" .value=${String(settings.session_length_cards ?? 20)} /></label>
          <label>${this.t("manage.newPerDay")}<input name="new" type="number" min="0" .value=${String(settings.max_new_per_day_cards ?? 8)} /></label>
          <label>${this.t("manage.pushBudget")}<input name="push" type="number" min="0" .value=${String(settings.daily_push_budget ?? 6)} /></label>
          <label>${this.t("manage.quietStart")}<input name="quietStart" type="time" .value=${String(quiet.start ?? "22:00")} /></label>
          <label>${this.t("manage.quietEnd")}<input name="quietEnd" type="time" .value=${String(quiet.end ?? "08:00")} /></label>
          <label>${this.t("manage.activeStart")}<input name="activeStart" type="time" .value=${String(firstWindow.start ?? "08:00")} /></label>
          <label>${this.t("manage.activeEnd")}<input name="activeEnd" type="time" .value=${String(firstWindow.end ?? "20:00")} /></label>
          <div class="actions"><button class="primary" type="submit">${this.t("manage.save")}</button></div>
        </form>
      </article>
      ${this.renderNotificationTargets()}
    `;
  }
}

if (globalThis.customElements !== undefined && customElements.get("locklearn-management-view") === undefined) {
  customElements.define("locklearn-management-view", LockLearnManagementView);
}

declare global {
  interface HTMLElementTagNameMap {
    "locklearn-management-view": LockLearnManagementView;
  }
}
