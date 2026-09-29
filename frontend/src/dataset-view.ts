import { LitElement, css, html, nothing } from "lit";
import { property, state } from "lit/decorators.js";

import { interactiveAccessibilityStyles } from "./content-renderer";
import { languageFallback, translate, type UiLanguage } from "./i18n";
import {
  installDataset,
  listDatasetAttributions,
  listDatasets,
  refreshDatasets,
  type DatasetAttributionRecord,
  type DatasetStatusRecord,
  type HomeAssistantLike,
} from "./protocol";

export function safeExternalUrl(value: string | null): string | null {
  if (value === null) return null;
  try {
    const url = new URL(value);
    return url.protocol === "https:" || url.protocol === "http:" ? url.href : null;
  } catch {
    return null;
  }
}

export function formatDatasetBytes(value: number): string {
  if (value < 1024) return `${value} B`;
  const units = ["KiB", "MiB", "GiB"];
  let amount = value / 1024;
  let index = 0;
  while (amount >= 1024 && index < units.length - 1) {
    amount /= 1024;
    index += 1;
  }
  return `${amount.toFixed(amount >= 10 ? 1 : 2)} ${units[index]}`;
}

export class LockLearnDatasetView extends LitElement {
  @property({ attribute: false }) hass?: HomeAssistantLike;
  @property({ type: Boolean }) admin = false;

  @state() private datasets: DatasetStatusRecord[] = [];
  @state() private loading = false;
  @state() private errorMessage = "";
  @state() private notice = "";
  @state() private attributionPages: Record<
    string,
    { items: DatasetAttributionRecord[]; cursor: string | null; expanded: boolean; loading: boolean }
  > = {};

  static styles = css`
    ${interactiveAccessibilityStyles}
    :host, .stack, .grid, .card, .actions, button, a { box-sizing: border-box; min-width: 0; max-width: 100%; }
    :host { display: block; }
    .stack { display: grid; gap: 16px; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit,minmax(300px,1fr)); gap: 14px; }
    .card { padding: 18px; border: 1px solid var(--divider-color); border-radius: 12px;
      background: var(--card-background-color,var(--primary-background-color)); overflow-wrap: anywhere; }
    .card h2, .card h3 { margin-top: 0; }
    .meta, .muted { color: var(--secondary-text-color); }
    .meta { font-size: .86rem; }
    .notice, .error, .warning { padding: 12px; border-radius: 9px; background: var(--secondary-background-color); line-height: 1.45; }
    .error, .warning { color: var(--error-color,var(--primary-text-color)); }
    dl { display: grid; grid-template-columns: minmax(150px,auto) 1fr; gap: 6px 12px; margin: 0; }
    dt { color: var(--secondary-text-color); }
    dd { margin: 0; }
    .actions { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
    button { min-height: 40px; padding: 8px 12px; border: 1px solid var(--divider-color); border-radius: 8px;
      color: var(--primary-text-color); background: var(--secondary-background-color); font: inherit; cursor: pointer; }
    button.primary { border-color: var(--primary-color); color: var(--text-primary-color,white); background: var(--primary-color); }
    button:disabled { cursor: not-allowed; opacity: .55; }
    ul { padding-left: 20px; }
    a { color: var(--primary-color); }
    @media (max-width: 600px) {
      .grid, dl { grid-template-columns: 1fr; }
      .actions { flex-direction: column; align-items: stretch; }
      button { width: 100%; }
    }
  `;

  connectedCallback(): void {
    super.connectedCallback();
    void this.load();
  }

  protected updated(changed: Map<PropertyKey, unknown>): void {
    if (changed.has("hass") && this.hass !== undefined) void this.load();
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
    if (this.hass === undefined) return;
    this.loading = true;
    this.errorMessage = "";
    try {
      this.datasets = await listDatasets(this.hass);
    } catch (error) {
      this.errorMessage = error instanceof Error ? error.message : String(error);
    } finally {
      this.loading = false;
    }
  }

  private async refresh(): Promise<void> {
    if (this.hass === undefined || !this.admin) return;
    this.loading = true;
    this.errorMessage = "";
    this.notice = "";
    try {
      this.datasets = await refreshDatasets(this.hass);
      this.notice = this.t("datasets.refreshed");
    } catch (error) {
      this.errorMessage = error instanceof Error ? error.message : String(error);
    } finally {
      this.loading = false;
    }
  }

  private async install(dataset: DatasetStatusRecord): Promise<void> {
    if (this.hass === undefined || !this.admin) return;
    this.loading = true;
    this.errorMessage = "";
    this.notice = "";
    try {
      const result = await installDataset(this.hass, dataset.dataset_id, dataset.available_version);
      this.datasets = result.statuses;
      this.notice = this.t("datasets.installed");
      this.dispatchEvent(new CustomEvent("locklearn-refresh", { bubbles: true, composed: true }));
    } catch (error) {
      this.errorMessage = error instanceof Error ? error.message : String(error);
    } finally {
      this.loading = false;
    }
  }

  private attributionKey(datasetId: string, sourceId: string): string {
    return `${datasetId}\u0000${sourceId}`;
  }

  private async toggleAttributions(datasetId: string, sourceId: string): Promise<void> {
    if (this.hass === undefined) return;
    const key = this.attributionKey(datasetId, sourceId);
    const current = this.attributionPages[key];
    if (current !== undefined) {
      this.attributionPages = {
        ...this.attributionPages,
        [key]: { ...current, expanded: !current.expanded },
      };
      return;
    }
    this.attributionPages = {
      ...this.attributionPages,
      [key]: { items: [], cursor: null, expanded: true, loading: true },
    };
    try {
      const page = await listDatasetAttributions(this.hass, datasetId, sourceId);
      this.attributionPages = {
        ...this.attributionPages,
        [key]: { ...page, expanded: true, loading: false },
      };
    } catch (error) {
      this.errorMessage = error instanceof Error ? error.message : String(error);
      this.attributionPages = {
        ...this.attributionPages,
        [key]: { items: [], cursor: null, expanded: true, loading: false },
      };
    }
  }

  private async loadMoreAttributions(datasetId: string, sourceId: string): Promise<void> {
    if (this.hass === undefined) return;
    const key = this.attributionKey(datasetId, sourceId);
    const current = this.attributionPages[key];
    if (current === undefined || current.cursor === null || current.loading) return;
    this.attributionPages = {
      ...this.attributionPages,
      [key]: { ...current, loading: true },
    };
    try {
      const page = await listDatasetAttributions(
        this.hass,
        datasetId,
        sourceId,
        current.cursor,
      );
      this.attributionPages = {
        ...this.attributionPages,
        [key]: {
          items: [...current.items, ...page.items],
          cursor: page.cursor,
          expanded: true,
          loading: false,
        },
      };
    } catch (error) {
      this.errorMessage = error instanceof Error ? error.message : String(error);
      this.attributionPages = {
        ...this.attributionPages,
        [key]: { ...current, loading: false },
      };
    }
  }

  protected render() {
    return html`
      <section class="stack">
        <div>
          <h1>${this.t("datasets.title")}</h1>
          <p class="muted">${this.t("datasets.intro")}</p>
          ${this.admin
            ? html`<div class="actions">
                <button ?disabled=${this.loading} @click=${() => void this.refresh()}>
                  ${this.t("datasets.check")}
                </button>
              </div>`
            : html`<p class="muted">${this.t("datasets.adminOnly")}</p>`}
        </div>
        ${this.errorMessage ? html`<div class="error" role="alert">${this.errorMessage}</div>` : nothing}
        ${this.notice ? html`<div class="notice" role="status">${this.notice}</div>` : nothing}
        ${this.loading && this.datasets.length === 0
          ? html`<p>${this.t("datasets.loading")}</p>`
          : this.datasets.length === 0
            ? html`<p>${this.t("datasets.empty")}</p>`
            : html`<div class="grid">${this.datasets.map((dataset) => this.renderDataset(dataset))}</div>`}
      </section>
    `;
  }

  private renderDataset(dataset: DatasetStatusRecord) {
    const hasWarning = dataset.error !== null || dataset.stale_sources.length > 0;
    const releaseUrl = safeExternalUrl(dataset.release_url);
    return html`
      <article class="card">
        <h2>${dataset.name}</h2>
        <dl>
          <dt>${this.t("datasets.state")}</dt><dd>${dataset.state}</dd>
          <dt>${this.t("datasets.installedVersion")}</dt><dd>${dataset.installed_version ?? "—"}</dd>
          <dt>${this.t("datasets.availableVersion")}</dt><dd>${dataset.available_version ?? "—"}</dd>
          <dt>${this.t("datasets.sourceAge")}</dt>
          <dd>${dataset.source_age_days === null ? "—" : `${dataset.source_age_days} ${this.t("datasets.days")}`}</dd>
          <dt>${this.t("datasets.disk")}</dt><dd>${formatDatasetBytes(dataset.cache_bytes)}</dd>
          <dt>${this.t("datasets.builtAt")}</dt><dd>${dataset.built_at_utc ?? "—"}</dd>
        </dl>
        ${hasWarning
          ? html`<div class="warning" role="status">
              ${dataset.error ? html`<div>${dataset.error}</div>` : nothing}
              ${dataset.stale_sources.length > 0
                ? html`<div>${this.t("datasets.stale")}: ${dataset.stale_sources.join(", ")}</div>`
                : nothing}
            </div>`
          : nothing}
        ${dataset.changelog
          ? html`<h3>${this.t("datasets.changelog")}</h3><p>${dataset.changelog}</p>`
          : nothing}
        ${releaseUrl
          ? html`<p><a href=${releaseUrl} target="_blank" rel="noopener noreferrer">${this.t("datasets.release")}</a></p>`
          : nothing}
        ${this.admin && (dataset.update_available || dataset.installed_version === null) && dataset.available_version
          ? html`<div class="actions">
              <button class="primary" ?disabled=${this.loading} @click=${() => void this.install(dataset)}>
                ${dataset.installed_version === null ? this.t("datasets.install") : this.t("datasets.update")}
              </button>
            </div>`
          : nothing}
        <h3>${this.t("datasets.sources")}</h3>
        ${dataset.sources.length === 0
          ? html`<p class="muted">${this.t("datasets.noSources")}</p>`
          : html`<ul>${dataset.sources.map((source) => {
              const sourceUrl = safeExternalUrl(source.homepage);
              const key = this.attributionKey(dataset.dataset_id, source.source_id);
              const page = this.attributionPages[key];
              return html`
                <li>
                  <strong>${source.name}</strong> — ${source.provider}
                  <div class="meta">${source.attribution_template}</div>
                  <div class="meta">
                    ${this.t("datasets.upstream")}: ${source.upstream_version}
                    ${source.upstream_date ? html` · ${source.upstream_date}` : nothing}
                    · ${source.provenance_records} ${this.t("datasets.records")}
                    ${source.modified_records > 0 ? html` · ${source.modified_records} ${this.t("datasets.modified")}` : nothing}
                  </div>
                  ${sourceUrl
                    ? html`<a href=${sourceUrl} target="_blank" rel="noopener noreferrer">${this.t("datasets.sourcePage")}</a>`
                    : nothing}
                  ${source.attribution_records > 0
                    ? html`
                        <div class="actions">
                          <button
                            type="button"
                            @click=${() => void this.toggleAttributions(dataset.dataset_id, source.source_id)}
                          >
                            ${page?.expanded
                              ? this.t("datasets.hideAttributions")
                              : this.t("datasets.showAttributions")}
                          </button>
                        </div>
                        ${page?.expanded
                          ? html`
                              <div class="notice">
                                <strong>${this.t("datasets.individualAttributions")}</strong>
                                ${page.loading && page.items.length === 0
                                  ? html`<p>${this.t("datasets.loading")}</p>`
                                  : html`<ul>
                                      ${page.items.map((item) => html`
                                        <li>
                                          ${item.attribution_text}
                                          <div class="meta">
                                            ${item.source_record_id ?? "—"}
                                            ${item.author ? html` · ${item.author}` : nothing}
                                            ${item.language_tag ? html` · ${item.language_tag}` : nothing}
                                            ${item.modified_from_source
                                              ? html` · ${this.t("datasets.modified")}`
                                              : nothing}
                                          </div>
                                        </li>
                                      `)}
                                    </ul>`}
                                ${page.cursor !== null
                                  ? html`<button
                                      type="button"
                                      ?disabled=${page.loading}
                                      @click=${() => void this.loadMoreAttributions(dataset.dataset_id, source.source_id)}
                                    >
                                      ${this.t("datasets.loadMore")}
                                    </button>`
                                  : nothing}
                              </div>`
                          : nothing}
                      `
                    : nothing}
                </li>
              `;
            })}</ul>`}
        <h3>${this.t("datasets.licenses")}</h3>
        ${dataset.licenses.length === 0
          ? html`<p class="muted">${this.t("datasets.noLicenses")}</p>`
          : html`<ul>${dataset.licenses.map((license) => html`
              <li>
                <strong>${license.name}</strong>
                <span class="meta">(${license.license_id} · ${license.license_scope})</span>
                <div class="meta">
                  ${license.attribution_required ? this.t("datasets.attributionRequired") : this.t("datasets.attributionOptional")}
                  · ${license.commercial_use_allowed ? this.t("datasets.commercialAllowed") : this.t("datasets.commercialBlocked")}
                  ${license.share_alike ? html` · ${this.t("datasets.shareAlike")}` : nothing}
                </div>
                ${safeExternalUrl(license.source_url)
                  ? html`<a href=${safeExternalUrl(license.source_url)!} target="_blank" rel="noopener noreferrer">${this.t("datasets.licensePage")}</a>`
                  : nothing}
              </li>
            `)}</ul>`}
      </article>
    `;
  }
}

if (globalThis.customElements !== undefined && customElements.get("locklearn-dataset-view") === undefined) {
  customElements.define("locklearn-dataset-view", LockLearnDatasetView);
}

declare global {
  interface HTMLElementTagNameMap {
    "locklearn-dataset-view": LockLearnDatasetView;
  }
}
