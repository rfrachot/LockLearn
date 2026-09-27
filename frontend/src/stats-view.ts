import { LitElement, css, html, nothing } from "lit";
import { property, state } from "lit/decorators.js";

import { languageFallback, translate, type UiLanguage } from "./i18n";
import {
  getStats,
  listDifficulties,
  listTracks,
  type DifficultyRecord,
  type HomeAssistantLike,
  type StatsDailyRecord,
  type StatsResponse,
  type TrackRecord,
  type VisibleProfile,
} from "./protocol";

export function formatPercent(value: number | null): string {
  return value === null ? "—" : `${Math.round(value * 100)}%`;
}

export function recentDaily(rows: StatsDailyRecord[], limit = 14): StatsDailyRecord[] {
  return rows.slice(-Math.max(0, limit)).reverse();
}

export class LockLearnStatsView extends LitElement {
  @property({ attribute: false }) hass?: HomeAssistantLike;
  @property({ attribute: false }) profile?: VisibleProfile;

  @state() private stats?: StatsResponse;
  @state() private difficulties: DifficultyRecord[] = [];
  @state() private tracks: TrackRecord[] = [];
  @state() private selectedTrackId = "";
  @state() private loading = false;
  @state() private errorMessage = "";

  static styles = css`
    :host, section, article, div, select { box-sizing: border-box; min-width: 0; max-width: 100%; }
    :host { display: block; }
    .stack { display: grid; gap: 18px; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit,minmax(190px,1fr)); gap: 12px; }
    .card { padding: 16px; border: 1px solid var(--divider-color); border-radius: 12px;
      background: var(--card-background-color,var(--primary-background-color)); overflow-wrap: anywhere; }
    .metric strong { display: block; font-size: 1.55rem; margin-top: 4px; }
    .muted, .meta { color: var(--secondary-text-color); }
    .meta { font-size: .86rem; }
    .verified { border-inline-start: 4px solid var(--primary-color); }
    .secondary { opacity: .92; }
    .error { padding: 12px; border-radius: 9px; background: var(--secondary-background-color);
      color: var(--error-color,var(--primary-text-color)); }
    .toolbar { display: flex; flex-wrap: wrap; gap: 10px; align-items: end; }
    label { display: grid; gap: 5px; }
    select { min-height: 40px; padding: 7px; border: 1px solid var(--divider-color);
      border-radius: 8px; color: var(--primary-text-color);
      background: var(--card-background-color,var(--primary-background-color)); }
    table { width: 100%; border-collapse: collapse; font-size: .9rem; }
    th, td { padding: 7px 8px; text-align: left; border-bottom: 1px solid var(--divider-color); }
    .table-wrap { overflow-x: auto; }
    ul { padding-left: 20px; }
    h1, h2, h3, p { overflow-wrap: anywhere; }
    @media (max-width: 600px) {
      .grid { grid-template-columns: 1fr; }
      .toolbar, label, select { width: 100%; }
    }
  `;

  connectedCallback(): void {
    super.connectedCallback();
    void this.load();
  }

  protected updated(changed: Map<PropertyKey, unknown>): void {
    if (changed.has("hass") || changed.has("profile")) void this.load();
  }

  private locale(): UiLanguage {
    return languageFallback(
      this.hass?.locale?.language ?? this.hass?.language ?? globalThis.navigator?.language ?? "en",
    );
  }

  private t(key: Parameters<typeof translate>[1]): string {
    return translate(this.locale(), key);
  }

  private async load(): Promise<void> {
    if (this.hass === undefined || this.profile === undefined) {
      this.stats = undefined;
      this.difficulties = [];
      this.tracks = [];
      return;
    }
    this.loading = true;
    this.errorMessage = "";
    try {
      const tracks = await listTracks(this.hass, this.profile.profile_id);
      const selected =
        this.selectedTrackId && tracks.some((track) => track.track_id === this.selectedTrackId)
          ? this.selectedTrackId
          : "";
      const [stats, difficulties] = await Promise.all([
        getStats(this.hass, this.profile.profile_id, selected || null),
        listDifficulties(this.hass, this.profile.profile_id, selected || null),
      ]);
      this.tracks = tracks;
      this.selectedTrackId = selected;
      this.stats = stats;
      this.difficulties = difficulties;
    } catch (error) {
      this.errorMessage = error instanceof Error ? error.message : String(error);
    } finally {
      this.loading = false;
    }
  }

  private async selectTrack(event: Event): Promise<void> {
    this.selectedTrackId = (event.currentTarget as HTMLSelectElement).value;
    await this.load();
  }

  protected render() {
    if (this.profile === undefined) return nothing;
    return html`
      <section class="stack">
        <div>
          <h1>${this.t("stats.title")}</h1>
          <p class="muted">${this.t("stats.intro")}</p>
          <div class="toolbar">
            <label>
              <span>${this.t("stats.track")}</span>
              <select .value=${this.selectedTrackId} @change=${this.selectTrack}>
                <option value="">${this.t("stats.allTracks")}</option>
                ${this.tracks.map(
                  (track) => html`<option value=${track.track_id}>${track.name}</option>`,
                )}
              </select>
            </label>
          </div>
        </div>

        ${this.errorMessage
          ? html`<div class="error" role="alert">${this.errorMessage}</div>`
          : nothing}
        ${this.loading && this.stats === undefined
          ? html`<p>${this.t("stats.loading")}</p>`
          : this.stats === undefined
            ? nothing
            : this.renderStats(this.stats)}
      </section>
    `;
  }

  private renderStats(stats: StatsResponse) {
    const accuracy = stats.recent_verified_accuracy;
    const calibration = stats.calibration;
    const daily = recentDaily(stats.daily);
    const exposureTotal = daily.reduce((sum, row) => sum + row.learning_exposures, 0);
    const verifiedTotal = daily.reduce((sum, row) => sum + row.verified_retrievals, 0);

    return html`
      <section class="grid" aria-label=${this.t("stats.verifiedGroup")}>
        <article class="card metric verified">
          <span>${this.t("stats.dueToday")}</span>
          <strong>${stats.due_today}</strong>
        </article>
        <article class="card metric verified">
          <span>${this.t("stats.verifiedAccuracy")}</span>
          <strong>${formatPercent(accuracy.accuracy)}</strong>
          <div class="meta">${accuracy.correct}/${accuracy.total} · ${this.t("stats.verifiedOnly")}</div>
        </article>
        <article class="card metric verified">
          <span>${this.t("stats.latestRetention")}</span>
          <strong>${stats.latest_verified_retention === null
            ? "—"
            : stats.latest_verified_retention.retained
              ? this.t("stats.retained")
              : this.t("stats.notRetained")}</strong>
        </article>
        <article class="card metric">
          <span>${this.t("stats.streak")}</span>
          <strong>${stats.streak.days}</strong>
          <div class="meta">${this.t("stats.days")}</div>
        </article>
      </section>

      <article class="card">
        <h2>${this.t("stats.states")}</h2>
        <div class="grid">
          ${this.stateMetric("stats.stateNew", stats.states.new)}
          ${this.stateMetric("stats.stateLearning", stats.states.learning)}
          ${this.stateMetric("stats.stateReview", stats.states.review)}
          ${this.stateMetric("stats.stateRelearning", stats.states.relearning)}
          ${this.stateMetric("stats.stateLeech", stats.states.leech)}
        </div>
      </article>

      <article class="card verified">
        <h2>${this.t("stats.evidence")}</h2>
        <p>${this.t("stats.evidenceExplain")}</p>
        <div class="grid">
          <div class="metric">
            <span>${this.t("stats.exposures")}</span>
            <strong>${exposureTotal}</strong>
            <div class="meta">${this.t("stats.notAccuracy")}</div>
          </div>
          <div class="metric">
            <span>${this.t("stats.verifiedRetrievals")}</span>
            <strong>${verifiedTotal}</strong>
            <div class="meta">${this.t("stats.countsAccuracy")}</div>
          </div>
        </div>
      </article>

      <article class="card">
        <h2>${this.t("stats.calibration")}</h2>
        <p>${this.t("stats.calibrationExplain")}</p>
        <div class="grid">
          ${this.stateMetric("stats.declaredKnown", calibration.declared_known_cards)}
          ${this.stateMetric("stats.verifiedLater", calibration.later_verified_cards)}
          ${this.stateMetric("stats.verifiedCorrectLater", calibration.later_verified_correct)}
          ${this.stateMetric("stats.verifiedWrongLater", calibration.later_verified_wrong)}
          ${this.stateMetric("stats.awaitingVerification", calibration.awaiting_verified_followup)}
          <div class="metric">
            <span>${this.t("stats.calibrationAccuracy")}</span>
            <strong>${formatPercent(calibration.later_verified_accuracy)}</strong>
          </div>
        </div>
      </article>

      <article class="card secondary">
        <h2>${this.t("stats.mastery")}</h2>
        <div class="metric">
          <strong>${formatPercent(stats.mastery.value)}</strong>
          <div class="meta">${stats.mastery.card_count} ${this.t("stats.cards")}</div>
        </div>
        <p>${this.t("stats.masteryExplain")}</p>
      </article>

      <article class="card">
        <h2>${this.t("stats.difficulties")}</h2>
        ${this.difficulties.length === 0
          ? html`<p class="muted">${this.t("stats.noDifficulties")}</p>`
          : html`<ul>
              ${this.difficulties.map(
                (item) => html`
                  <li>
                    <strong>${item.card_key}</strong>
                    — ${this.t("stats.leechScore")} ${item.leech_score}
                    <div class="meta">
                      ${item.verified_correct_count} ${this.t("stats.correct")} ·
                      ${item.verified_wrong_count} ${this.t("stats.wrong")} ·
                      ${item.annotations.length > 0
                        ? this.t("stats.mnemonicPresent")
                        : this.t("stats.mnemonicSuggested")}
                    </div>
                  </li>
                `,
              )}
            </ul>`}
      </article>

      <article class="card">
        <h2>${this.t("stats.confusions")}</h2>
        ${stats.confusions.length === 0
          ? html`<p class="muted">${this.t("stats.noConfusions")}</p>`
          : html`<ul>
              ${stats.confusions.map(
                (item) => html`
                  <li>
                    <strong>${item.card_key}</strong>
                    <div class="meta">
                      ${this.t("stats.expected")} ${item.expected_answer_id} →
                      ${this.t("stats.chosen")} ${item.chosen_answer_id} ·
                      ${item.count}×
                    </div>
                  </li>
                `,
              )}
            </ul>`}
      </article>

      <article class="card">
        <h2>${this.t("stats.recentActivity")}</h2>
        ${daily.length === 0
          ? html`<p class="muted">${this.t("stats.noActivity")}</p>`
          : html`<div class="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>${this.t("stats.date")}</th>
                    <th>${this.t("stats.exposures")}</th>
                    <th>${this.t("stats.verifiedRetrievals")}</th>
                    <th>${this.t("stats.correct")}</th>
                    <th>${this.t("stats.wrong")}</th>
                    <th>${this.t("stats.new")}</th>
                    <th>${this.t("stats.reviewed")}</th>
                    <th>${this.t("stats.relearning")}</th>
                  </tr>
                </thead>
                <tbody>
                  ${daily.map(
                    (row) => html`
                      <tr>
                        <td>${row.local_date}</td>
                        <td>${row.learning_exposures}</td>
                        <td>${row.verified_retrievals}</td>
                        <td>${row.verified_correct}</td>
                        <td>${row.verified_wrong}</td>
                        <td>${row.new_cards}</td>
                        <td>${row.reviewed_cards}</td>
                        <td>${row.relearning_cards}</td>
                      </tr>
                    `,
                  )}
                </tbody>
              </table>
            </div>`}
      </article>
    `;
  }

  private stateMetric(key: Parameters<typeof translate>[1], value: number) {
    return html`<div class="metric"><span>${this.t(key)}</span><strong>${value}</strong></div>`;
  }
}

if (globalThis.customElements !== undefined && customElements.get("locklearn-stats-view") === undefined) {
  customElements.define("locklearn-stats-view", LockLearnStatsView);
}

declare global {
  interface HTMLElementTagNameMap {
    "locklearn-stats-view": LockLearnStatsView;
  }
}
