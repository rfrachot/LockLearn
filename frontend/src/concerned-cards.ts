import { LitElement, css, html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import { contentRendererStyles, interactiveAccessibilityStyles, renderContentBlock } from "./content-renderer";
import {
  getConcernedCards,
  learnCardInstead,
  setCardUserState,
  type ConcernedCard,
  type ConcernedCardsFilter,
  type HomeAssistantLike,
} from "./protocol";
import { translate as t, type TranslationKey, type UiLanguage } from "./i18n";

@customElement("locklearn-concerned-cards")
export class LockLearnConcernedCards extends LitElement {
  static styles = [
    contentRendererStyles,
    interactiveAccessibilityStyles,
    css`
      :host {
        position: fixed;
        inset: 0;
        z-index: 1000;
        display: block;
      }

      .backdrop {
        position: absolute;
        inset: 0;
        background: color-mix(in srgb, var(--primary-text-color) 28%, transparent);
      }

      .sheet {
        position: absolute;
        left: 50%;
        transform: translateX(-50%);
        width: min(960px, calc(100% - 24px));
        bottom: 0;
        max-height: min(78vh, 720px);
        overflow: auto;
        background: var(--card-background-color);
        color: var(--primary-text-color);
        border-radius: 18px 18px 0 0;
        padding: 20px max(18px, env(safe-area-inset-right))
          max(20px, env(safe-area-inset-bottom))
          max(18px, env(safe-area-inset-left));
        box-shadow: var(--ha-card-box-shadow, 0 -8px 28px rgb(0 0 0 / 18%));
      }

      header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 16px;
        margin-bottom: 16px;
      }

      h2 {
        margin: 0;
        font-size: 1.2rem;
      }

      button {
        min-height: 44px;
        min-width: 44px;
        border-radius: 10px;
        border: 1px solid var(--divider-color);
        background: var(--card-background-color);
        color: var(--primary-text-color);
        padding: 0.55rem 0.8rem;
        cursor: pointer;
      }

      button.primary {
        background: var(--primary-color);
        color: var(--text-primary-color, white);
        border-color: var(--primary-color);
      }

      ul {
        list-style: none;
        margin: 0;
        padding: 0;
        display: grid;
        gap: 12px;
      }

      li {
        border: 1px solid var(--divider-color);
        border-radius: 14px;
        padding: 14px;
        display: grid;
        gap: 10px;
      }

      .meta {
        color: var(--secondary-text-color);
        font-size: 0.9rem;
      }

      .actions {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
      }

      .error {
        color: var(--error-color);
      }
    `,
  ];

  @property({ attribute: false }) hass?: HomeAssistantLike;
  @property() profileId = "";
  @property() trackId = "";
  @property() filter: ConcernedCardsFilter = "current_waiting_context";
  @property() mode: "learn" | "quiz" = "learn";
  @property() language: UiLanguage = "en";
  @property() timeZone = "UTC";

  @state() private cards: ConcernedCard[] = [];
  @state() private loading = true;
  @state() private errorMessage = "";

  connectedCallback(): void {
    super.connectedCallback();
    void this.refresh();
  }

  protected updated(changed: Map<string, unknown>): void {
    if (
      changed.has("profileId") ||
      changed.has("trackId") ||
      changed.has("filter") ||
      changed.has("mode")
    ) {
      void this.refresh();
    }
  }

  private tr(key: TranslationKey): string {
    return t(this.language, key);
  }

  private filterCopy(): { title: string; body: string } {
    const fr = this.language === "fr";
    const copy: Record<ConcernedCardsFilter, { en: [string, string]; fr: [string, string] }> = {
      known_pending: { en: ["Already-known cards to verify", "These cards were marked as already known and will be verified later."], fr: ["Cartes déjà connues à vérifier", "Ces cartes ont été marquées comme déjà connues et seront vérifiées plus tard."] },
      suspended: { en: ["Suspended cards", "These cards are excluded until you reactivate them."], fr: ["Cartes suspendues", "Ces cartes restent exclues tant que vous ne les réactivez pas."] },
      buried: { en: ["Cards temporarily set aside", "These cards are temporarily hidden from normal sessions."], fr: ["Cartes mises de côté temporairement", "Ces cartes sont temporairement retirées des sessions normales."] },
      prerequisite_support: { en: ["Prerequisites to learn first", "These prerequisite cards currently block other material."], fr: ["Prérequis à apprendre d’abord", "Ces cartes prérequises bloquent actuellement d’autres contenus."] },
      current_waiting_context: { en: ["Cards currently waiting", "These cards explain why the current mode is not ready yet."], fr: ["Cartes actuellement en attente", "Ces cartes expliquent pourquoi ce mode n’est pas encore disponible."] },
    };
    const selected = copy[this.filter];
    const pair = selected[fr ? "fr" : "en"];
    return { title: pair[0], body: pair[1] };
  }

  private stateLabel(state: string): string {
    const fr = this.language === "fr";
    const labels: Record<string, [string, string]> = {
      known_already: ["Marked as already known", "Marquée comme déjà connue"],
      suspended: ["Suspended", "Suspendue"],
      buried: ["Temporarily set aside", "Mise de côté temporairement"],
      active: ["Active", "Active"],
      new: ["Not learned yet", "Pas encore apprise"],
      learning: ["Learning", "En apprentissage"],
      review: ["Review", "En révision"],
      relearning: ["Relearning", "En réapprentissage"],
    };
    const pair = labels[state] ?? ["Waiting", "En attente"];
    return pair[fr ? 1 : 0];
  }

  private horizonLabel(value: string): string {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "";
    return new Intl.DateTimeFormat(this.language, {
      dateStyle: "medium",
      timeStyle: "short",
      timeZone: this.timeZone,
    }).format(date);
  }

  private async refresh(): Promise<void> {
    if (this.hass === undefined || this.profileId === "" || this.trackId === "") return;
    this.loading = true;
    this.errorMessage = "";
    try {
      const response = await getConcernedCards(
        this.hass,
        this.profileId,
        this.trackId,
        this.filter,
        this.mode,
      );
      this.cards = response.cards;
    } catch (error) {
      this.errorMessage = error instanceof Error ? error.message : String(error);
    } finally {
      this.loading = false;
    }
  }

  private close(): void {
    this.dispatchEvent(new CustomEvent("locklearn-concerned-cards-close", {
      bubbles: true,
      composed: true,
    }));
  }

  private async apply(card: ConcernedCard): Promise<void> {
    if (this.hass === undefined) return;
    this.loading = true;
    this.errorMessage = "";
    try {
      if (card.action === "learn_instead") {
        await learnCardInstead(this.hass, this.profileId, this.trackId, card.card_key);
      } else if (card.action === "reactivate") {
        await setCardUserState(this.hass, this.profileId, this.trackId, card.card_key, "active");
      }
      await this.refresh();
      this.dispatchEvent(new CustomEvent("locklearn-concerned-cards-changed", {
        bubbles: true,
        composed: true,
      }));
    } catch (error) {
      this.errorMessage = error instanceof Error ? error.message : String(error);
      this.loading = false;
    }
  }

  private renderCard(card: ConcernedCard) {
    return html`
      <li>
        <div>
          ${card.prompt.blocks.map((block, index) => renderContentBlock(block, index === 0))}
        </div>
        <div class="meta">
          ${this.stateLabel(card.user_state)}
          ${card.horizon_utc === null ? nothing : html` · ${this.horizonLabel(card.horizon_utc)}`}
        </div>
        ${card.action === null
          ? nothing
          : html`
              <div class="actions">
                <button class="primary" @click=${() => void this.apply(card)} ?disabled=${this.loading}>
                  ${card.action === "learn_instead"
                    ? this.tr("cards.learnInstead")
                    : this.tr("cards.reactivate")}
                </button>
                ${card.action === "learn_instead"
                  ? html`<span class="meta">${this.language === "fr"
                      ? "Annule le marquage « déjà connue » et remet cette carte dans l’apprentissage normal."
                      : "Cancels the already-known mark and returns this card to normal learning."}</span>`
                  : card.action === "reactivate"
                    ? html`<span class="meta">${this.language === "fr" ? "Remet cette carte dans les sessions normales." : "Returns this card to normal sessions."}</span>`
                    : nothing}
              </div>
            `}
      </li>
    `;
  }

  render() {
    return html`
      <div class="backdrop" @click=${this.close}></div>
      <section class="sheet" role="dialog" aria-modal="true" aria-labelledby="concerned-title">
        <header>
          <h2 id="concerned-title">${this.filterCopy().title}</h2>
          <button @click=${this.close} aria-label=${this.tr("common.close")}>×</button>
        </header>
        <p class="meta">${this.filterCopy().body}</p>
        ${this.loading && this.cards.length === 0
          ? html`<p role="status">${this.tr("common.loading")}</p>`
          : nothing}
        ${this.errorMessage === ""
          ? nothing
          : html`<p class="error" role="alert">${this.errorMessage}</p>`}
        ${!this.loading && this.cards.length === 0
          ? html`<p>${this.tr("cards.noneConcerned")}</p>`
          : html`<ul>${this.cards.map((card) => this.renderCard(card))}</ul>`}
      </section>
    `;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "locklearn-concerned-cards": LockLearnConcernedCards;
  }
}
