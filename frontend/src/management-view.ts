import { LitElement, css, html, nothing } from "lit";
import { property, state } from "lit/decorators.js";

import { languageFallback, translate, type UiLanguage } from "./i18n";
import {
  createProfile,
  createTrack,
  deleteTrack,
  integratePackUpdate,
  listPacks,
  listProfileMembers,
  listShareTargets,
  listTracks,
  previewPackUpdate,
  previewTrackPlan,
  removeProfileMember,
  setTrackPlan,
  shareProfile,
  updateProfile,
  updateTrack,
  type HomeAssistantLike,
  type LearningPlanInput,
  type LoadForecast,
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

function asFloat(
  value: FormDataEntryValue | null,
  fallback: number,
  min: number,
  max: number,
): number {
  const parsed = Number.parseFloat(String(value ?? ""));
  return Number.isFinite(parsed) && parsed >= min && parsed <= max ? parsed : fallback;
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
  @state() private members: ProfileMember[] = [];
  @state() private shareTargets: ShareTarget[] = [];
  @state() private selectedTrackId = "";
  @state() private forecast?: LoadForecast;
  @state() private forecastPlan?: LearningPlanInput;
  @state() private packDiff?: PackVersionDiff;
  @state() private packDiffTrack = "";
  @state() private packDiffTarget = "";
  @state() private loading = false;
  @state() private errorMessage = "";
  @state() private notice = "";

  static styles = css`
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
    if (this.hass === undefined || this.profile === undefined) return;
    this.loading = true;
    this.errorMessage = "";
    try {
      [this.tracks, this.packs] = await Promise.all([
        listTracks(this.hass, this.profile.profile_id),
        listPacks(this.hass),
      ]);
      if (!this.tracks.some((item) => item.track_id === this.selectedTrackId)) {
        this.selectedTrackId = this.tracks[0]?.track_id ?? "";
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
      this.errorMessage = error instanceof Error ? error.message : String(error);
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
      this.errorMessage = error instanceof Error ? error.message : String(error);
    } finally {
      this.loading = false;
    }
  }

  protected render() {
    if (this.profile === undefined) return nothing;
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
      ${this.isOwner() ? this.renderCreateProfile() : nothing}
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
        <div class="actions"><button class="primary" type="submit">${this.t("manage.save")}</button></div>
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
        ${this.members.length === 0 ? html`<p>${this.t("manage.none")}</p>` : html`
          <ul>${this.members.map((member) => html`<li>
            ${member.name} — ${member.role}
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
    await this.mutate(() => removeProfileMember(this.hass!, this.profile!.profile_id, userId), this.t("manage.saved"));
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
          <label>${this.t("manage.timezone")}<input name="timezone" .value=${this.profile?.timezone ?? "UTC"} required /></label>
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

  private renderTrack(track: TrackRecord) {
    return html`
      <article class="card">
        <h2>${track.name}</h2>
        <p class="meta">${track.source_language} → ${track.target_language} · ${track.status}</p>
        <p class="meta">${this.t("manage.packVersion")}: ${track.pack_version_id ?? "—"}</p>
        ${this.canEditTrack() ? html`
          <form class="form-grid" @submit=${(event: SubmitEvent) => {
            event.preventDefault();
            const data = new FormData(event.currentTarget as HTMLFormElement);
            if (this.hass === undefined) return;
            void this.mutate(() => updateTrack(this.hass!, track.track_id, {
              name: String(data.get("name") ?? track.name),
              status: String(data.get("status") ?? track.status),
              priority: asInt(data.get("priority"), track.priority, 1),
            }), this.t("manage.saved"));
          }}>
            <label>${this.t("manage.name")}<input name="name" .value=${track.name} /></label>
            <label>${this.t("manage.status")}<select name="status" .value=${track.status}>
              <option value="active">${this.t("manage.active")}</option>
              <option value="paused">${this.t("manage.paused")}</option>
              <option value="archived">${this.t("manage.archived")}</option>
            </select></label>
            <label>${this.t("manage.priority")}<input name="priority" type="number" min="1" .value=${String(track.priority)} /></label>
            <div class="actions">
              <button type="submit">${this.t("manage.save")}</button>
              <button type="button" @click=${() => { this.selectedTrackId = track.track_id; this.forecast = undefined; }}>${this.t("manage.plan")}</button>
              <button type="button" @click=${() => this.removeTrack(track.track_id)}>${this.t("manage.delete")}</button>
            </div>
          </form>
          ${this.selectedTrackId === track.track_id ? this.renderPlan(track) : nothing}
        ` : nothing}
      </article>
    `;
  }

  private renderCreateTrack() {
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
            <label>${this.t("manage.pack")}<select name="pack">
              ${this.packs.map((pack) => html`<option value=${pack.pack_version_id}>${pack.name} · ${pack.version}</option>`)}
            </select></label>
            <label>${this.t("manage.sourceLanguage")}<input name="source" placeholder="ja" required /></label>
            <label>${this.t("manage.targetLanguage")}<input name="target" placeholder="fr" required /></label>
            <label>${this.t("manage.priority")}<input name="priority" type="number" min="1" value="1" /></label>
            <div class="actions"><button class="primary" type="submit">${this.t("manage.create")}</button></div>
          </form>`}
      </article>
    `;
  }

  private async removeTrack(trackId: string): Promise<void> {
    if (this.hass === undefined) return;
    await this.mutate(() => deleteTrack(this.hass!, trackId), this.t("manage.deleted"));
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
    return html`
      <div class="stack">
        <h3>${this.t("manage.plan")}</h3>
        <form class="form-grid" @submit=${(event: SubmitEvent) => {
          event.preventDefault();
          if (this.hass === undefined) return;
          const plan = this.planFrom(event.currentTarget as HTMLFormElement);
          this.loading = true;
          void previewTrackPlan(this.hass, track.track_id, plan)
            .then((forecast) => { this.forecast = forecast; this.forecastPlan = plan; })
            .catch((error: unknown) => { this.errorMessage = error instanceof Error ? error.message : String(error); })
            .finally(() => { this.loading = false; });
        }}>
          <label>${this.t("manage.newPerDay")}<input name="new" type="number" min="0" .value=${String(raw.max_new_per_day_cards ?? profileNew)} /></label>
          <label>${this.t("manage.reviewsPerDay")}<input name="reviews" type="number" min="1" .value=${String(raw.max_reviews_per_day_cards ?? 50)} /></label>
          <label>${this.t("manage.notificationTeasers")}<input name="teasers" type="number" min="0" .value=${String(raw.max_notification_new_teasers ?? Math.min(2, profileNew))} /></label>
          <label>${this.t("manage.targetDate")}<input name="date" type="date" .value=${String(raw.target_date ?? "")} /></label>
          <label>${this.t("manage.coverage")}<input name="coverage" type="number" min=".01" max="1" step=".01" .value=${String(raw.target_coverage ?? 1)} /></label>
          <label>${this.t("manage.retention")}<input name="retention" type="number" min=".01" max="1" step=".01" .value=${String(raw.target_retention ?? .9)} /></label>
          <div class="actions"><button class="primary" type="submit">${this.t("manage.preview")}</button></div>
        </form>
        ${this.forecast === undefined ? nothing : this.renderForecast(track)}
      </div>
    `;
  }

  private renderForecast(track: TrackRecord) {
    const forecast = this.forecast!;
    return html`
      <div class=${forecast.warnings.length > 0 ? "warning" : "notice"}>
        <strong>${this.t("manage.forecast")}</strong>
        <dl>
          <dt>${this.t("manage.cardsRemaining")}</dt><dd>${forecast.remaining_target_cards}</dd>
          <dt>${this.t("manage.requiredNew")}</dt><dd>${forecast.required_new_per_day}</dd>
          <dt>${this.t("manage.reviews3Weeks")}</dt><dd>${forecast.reviews_per_day_in_3_weeks}</dd>
          <dt>${this.t("manage.reviews3Months")}</dt><dd>${forecast.reviews_per_day_in_3_months}</dd>
          <dt>${this.t("manage.notifications3Weeks")}</dt><dd>${forecast.notification_deliverable_in_3_weeks}</dd>
          <dt>${this.t("manage.sessionLoad3Weeks")}</dt><dd>${forecast.active_session_cards_in_3_weeks}</dd>
        </dl>
        ${forecast.warnings.length === 0 ? nothing : html`<ul>${forecast.warnings.map((item) => html`<li>${item}</li>`)}</ul>`}
        <div class="actions"><button class="primary" @click=${() => this.applyPlan(track)}>${this.t("manage.applyPlan")}</button></div>
      </div>
    `;
  }

  private async applyPlan(track: TrackRecord): Promise<void> {
    if (this.hass === undefined || this.forecastPlan === undefined) return;
    await this.mutate(() => setTrackPlan(this.hass!, track.track_id, this.forecastPlan!), this.t("manage.saved"));
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
      this.errorMessage = error instanceof Error ? error.message : String(error);
    } finally {
      this.loading = false;
    }
  }

  private async applyPackUpdate(): Promise<void> {
    if (this.hass === undefined || !this.packDiffTrack || !this.packDiffTarget) return;
    await this.mutate(
      () => integratePackUpdate(this.hass!, this.packDiffTrack, this.packDiffTarget),
      this.t("manage.packIntegrated"),
    );
  }

  private renderSettings() {
    if (!this.isOwner()) return html`<div class="card"><p>${this.t("manage.readOnly")}</p></div>`;
    const settings = this.profile?.settings ?? {};
    const quiet = objectSetting(settings, "quiet_hours");
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
            },
          }), this.t("manage.saved"));
        }}>
          <label>${this.t("manage.sessionLength")}<input name="session" type="number" min="1" .value=${String(settings.session_length_cards ?? 20)} /></label>
          <label>${this.t("manage.newPerDay")}<input name="new" type="number" min="0" .value=${String(settings.max_new_per_day_cards ?? 8)} /></label>
          <label>${this.t("manage.pushBudget")}<input name="push" type="number" min="0" .value=${String(settings.daily_push_budget ?? 6)} /></label>
          <label>${this.t("manage.quietStart")}<input name="quietStart" type="time" .value=${String(quiet.start ?? "22:00")} /></label>
          <label>${this.t("manage.quietEnd")}<input name="quietEnd" type="time" .value=${String(quiet.end ?? "08:00")} /></label>
          <div class="actions"><button class="primary" type="submit">${this.t("manage.save")}</button></div>
        </form>
      </article>
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
