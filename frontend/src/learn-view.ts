import { LitElement, css, html, nothing } from "lit";
import { property, state } from "lit/decorators.js";

import { languageFallback, translate, type UiLanguage } from "./i18n";
import {
  canAnswerProfile,
  isIntroductionQuestion,
  questionAvailableAtMs,
} from "./learn-model";
import {
  answerSession,
  completeSession,
  createCardAnnotation,
  getSession,
  reportQuestion,
  setCardUserState,
  startLearnSession,
  type DashboardResponse,
  type DashboardTrack,
  type HomeAssistantLike,
  type LearnContentBlock,
  type SessionQuestion,
  type SessionState,
  type VisibleProfile,
} from "./protocol";

function nowMs(): number {
  return globalThis.performance?.now() ?? Date.now();
}

export class LockLearnLearnView extends LitElement {
  @property({ attribute: false }) hass?: HomeAssistantLike;
  @property({ attribute: false }) profile?: VisibleProfile;
  @property({ attribute: false }) dashboard?: DashboardResponse;

  @state() private trackId = "";
  @state() private session?: SessionState;
  @state() private loading = false;
  @state() private errorMessage = "";
  @state() private notice = "";
  @state() private revealed = false;
  @state() private hintUsed = false;
  @state() private pendingIdk = false;
  @state() private pendingIdkLatency?: number;
  @state() private mnemonic = "";
  @state() private reportMessage = "";
  @state() private waitingUntil?: string;

  private questionStartedAt = nowMs();
  private questionId: string | null = null;
  private availabilityTimer?: ReturnType<typeof globalThis.setTimeout>;

  static styles = css`
    :host {
      display: block;
      min-width: 0;
      max-width: 100%;
    }

    .learn-shell,
    .learn-card,
    .toolbar,
    .actions,
    .secondary-actions,
    .field-row,
    .annotation,
    label {
      box-sizing: border-box;
      min-width: 0;
      max-width: 100%;
    }

    .learn-shell {
      display: grid;
      gap: 16px;
    }

    .toolbar,
    .actions,
    .secondary-actions,
    .field-row {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 10px;
    }

    .toolbar {
      justify-content: space-between;
      padding: 16px;
      border: 1px solid var(--divider-color);
      border-radius: 12px;
      background: var(--card-background-color, var(--primary-background-color));
    }

    label {
      display: grid;
      gap: 6px;
      color: var(--secondary-text-color);
      font-size: 0.82rem;
    }

    select,
    textarea {
      box-sizing: border-box;
      border: 1px solid var(--divider-color);
      border-radius: 8px;
      color: var(--primary-text-color);
      background: var(--card-background-color, var(--primary-background-color));
      font: inherit;
    }

    select {
      min-width: 220px;
      padding: 9px;
    }

    textarea {
      width: 100%;
      min-height: 82px;
      padding: 10px;
      resize: vertical;
    }

    button {
      box-sizing: border-box;
      max-width: 100%;
      min-height: 42px;
      padding: 9px 14px;
      border: 1px solid var(--divider-color);
      border-radius: 9px;
      color: var(--primary-text-color);
      background: var(--secondary-background-color);
      font: inherit;
      cursor: pointer;
    }

    button.primary {
      border-color: var(--primary-color);
      color: var(--text-primary-color, white);
      background: var(--primary-color);
    }

    button:disabled {
      cursor: not-allowed;
      opacity: 0.55;
    }

    .learn-card {
      display: grid;
      gap: 18px;
      padding: clamp(18px, 4vw, 32px);
      border-radius: 14px;
      background: var(--card-background-color, var(--primary-background-color));
      box-shadow: var(--ha-card-box-shadow, none);
    }

    .progress {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      color: var(--secondary-text-color);
      font-size: 0.85rem;
    }

    .stage {
      color: var(--secondary-text-color);
      font-size: 0.85rem;
      font-weight: 650;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }

    .content {
      display: grid;
      gap: 12px;
    }

    .content-block {
      overflow-wrap: anywhere;
      line-height: 1.5;
    }

    .content-block.primary-content {
      font-size: clamp(2rem, 8vw, 4.25rem);
      line-height: 1.2;
      text-align: center;
    }

    .answer {
      padding-top: 18px;
      border-top: 1px solid var(--divider-color);
    }

    .hint-state,
    .notice,
    .error {
      padding: 10px 12px;
      border-radius: 8px;
      background: var(--secondary-background-color);
    }

    .error {
      color: var(--error-color, var(--primary-text-color));
    }

    .annotation {
      display: grid;
      gap: 8px;
      padding-top: 14px;
      border-top: 1px solid var(--divider-color);
    }

    .secondary-actions button {
      background: transparent;
    }

    @media (max-width: 600px) {
      .toolbar,
      .actions,
      .secondary-actions,
      .field-row {
        align-items: stretch;
        flex-direction: column;
      }

      select,
      button {
        width: 100%;
        min-width: 0;
        max-width: 100%;
      }

      .actions,
      .secondary-actions,
      .field-row {
        width: 100%;
      }

      .progress {
        flex-direction: column;
        gap: 4px;
      }
    }
  `;

  disconnectedCallback(): void {
    this.clearAvailabilityTimer();
    super.disconnectedCallback();
  }

  protected updated(changed: Map<PropertyKey, unknown>): void {
    if (changed.has("profile") || changed.has("dashboard")) {
      const available = this.tracks();
      if (!available.some((track) => track.track_id === this.trackId)) {
        this.trackId = available[0]?.track_id ?? "";
      }
      if (changed.has("profile")) {
        this.session = undefined;
        this.resetQuestionUi();
      }
    }
  }

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

  private tracks(): DashboardTrack[] {
    return this.dashboard?.tracks ?? [];
  }

  private selectedTrack(): DashboardTrack | undefined {
    return this.tracks().find((track) => track.track_id === this.trackId);
  }

  private setTrack(event: Event): void {
    const target = event.currentTarget;
    if (!(target instanceof HTMLSelectElement)) return;
    this.trackId = target.value;
    this.session = undefined;
    this.errorMessage = "";
    this.notice = "";
    this.resetQuestionUi();
  }

  private resetQuestionUi(): void {
    this.clearAvailabilityTimer();
    this.waitingUntil = undefined;
    this.revealed = false;
    this.hintUsed = false;
    this.pendingIdk = false;
    this.pendingIdkLatency = undefined;
    this.mnemonic = "";
    this.reportMessage = "";
    this.notice = "";
    this.questionStartedAt = nowMs();
    this.questionId = this.session?.current_question?.question_id ?? null;
  }

  private clearAvailabilityTimer(): void {
    if (this.availabilityTimer !== undefined) {
      globalThis.clearTimeout(this.availabilityTimer);
      this.availabilityTimer = undefined;
    }
  }

  private scheduleCurrentQuestionAvailability(): void {
    const availableAt = questionAvailableAtMs(this.session?.current_question);
    if (availableAt === null || availableAt <= Date.now()) return;
    this.waitingUntil = new Date(availableAt).toISOString();
    this.availabilityTimer = globalThis.setTimeout(() => {
      this.availabilityTimer = undefined;
      this.waitingUntil = undefined;
      this.questionStartedAt = nowMs();
    }, availableAt - Date.now());
  }

  private applySession(session: SessionState): void {
    const nextQuestionId = session.current_question?.question_id ?? null;
    const changed = nextQuestionId !== this.questionId;
    this.session = session;
    if (changed) {
      this.resetQuestionUi();
      this.scheduleCurrentQuestionAvailability();
    }
  }

  private elapsedMs(): number {
    return Math.max(0, Math.round(nowMs() - this.questionStartedAt));
  }

  private async start(): Promise<void> {
    if (
      this.hass === undefined ||
      this.profile === undefined ||
      this.trackId === "" ||
      !canAnswerProfile(this.profile)
    ) return;
    this.loading = true;
    this.errorMessage = "";
    this.notice = "";
    try {
      const session = await startLearnSession(
        this.hass,
        this.profile.profile_id,
        this.trackId,
      );
      this.applySession(session);
    } catch (error) {
      this.errorMessage = error instanceof Error ? error.message : String(error);
    } finally {
      this.loading = false;
    }
  }

  private async resume(): Promise<void> {
    const last = this.selectedTrack()?.last_session;
    if (this.hass === undefined || last === null || last === undefined) return;
    this.loading = true;
    this.errorMessage = "";
    try {
      this.applySession(await getSession(this.hass, last.session_id));
    } catch (error) {
      this.errorMessage = error instanceof Error ? error.message : String(error);
    } finally {
      this.loading = false;
    }
  }

  private async recover(error: unknown): Promise<void> {
    if (this.hass !== undefined && this.session !== undefined) {
      try {
        this.applySession(await getSession(this.hass, this.session.id));
        this.notice = this.t("learn.reloaded");
        return;
      } catch {
        // Preserve the original error below.
      }
    }
    this.errorMessage = error instanceof Error ? error.message : String(error);
  }

  private async finalizeIfDone(session: SessionState): Promise<SessionState> {
    if (
      this.hass !== undefined &&
      session.status === "active" &&
      session.current_question === null &&
      session.question_count > 0
    ) {
      return completeSession(this.hass, session);
    }
    return session;
  }

  private async learningAction(
    action: "introduce" | "known" | "review" | "idk",
    latency?: number,
  ): Promise<void> {
    const question = this.session?.current_question;
    if (this.hass === undefined || this.session === undefined || question === null || question === undefined) return;
    this.loading = true;
    this.errorMessage = "";
    try {
      const answered = await answerSession(
        this.hass,
        this.session,
        question.question_id,
        {
          kind: "learning",
          action,
          hint_used: this.hintUsed,
          presentation_to_answer_ms: latency ?? this.elapsedMs(),
        },
      );
      this.applySession(await this.finalizeIfDone(answered));
    } catch (error) {
      await this.recover(error);
    } finally {
      this.loading = false;
    }
  }

  private reveal(): void {
    this.revealed = true;
  }

  private idk(): void {
    this.pendingIdkLatency = this.elapsedMs();
    this.pendingIdk = true;
    this.revealed = true;
  }

  private showHint(): void {
    this.hintUsed = true;
  }

  private async setUserState(userState: "known_already" | "suspended"): Promise<void> {
    const question = this.session?.current_question;
    if (
      this.hass === undefined ||
      this.profile === undefined ||
      this.session === undefined ||
      question === null ||
      question === undefined ||
      this.session.track_id === null
    ) return;
    this.loading = true;
    this.errorMessage = "";
    try {
      await setCardUserState(
        this.hass,
        this.profile.profile_id,
        this.session.track_id,
        question.card_key,
        userState,
      );
      const advanced = await answerSession(
        this.hass,
        this.session,
        question.question_id,
        { kind: "user_state", action: userState },
      );
      this.applySession(await this.finalizeIfDone(advanced));
    } catch (error) {
      await this.recover(error);
    } finally {
      this.loading = false;
    }
  }

  private async report(): Promise<void> {
    const question = this.session?.current_question;
    if (
      this.hass === undefined ||
      this.profile === undefined ||
      this.session?.track_id === null ||
      this.session === undefined ||
      question === null ||
      question === undefined
    ) return;
    this.loading = true;
    this.errorMessage = "";
    try {
      await reportQuestion(
        this.hass,
        this.profile.profile_id,
        this.session.track_id,
        question,
        this.reportMessage,
      );
      this.notice = this.t("learn.reported");
      this.reportMessage = "";
    } catch (error) {
      this.errorMessage = error instanceof Error ? error.message : String(error);
    } finally {
      this.loading = false;
    }
  }

  private async saveMnemonic(): Promise<void> {
    const question = this.session?.current_question;
    if (
      this.hass === undefined ||
      this.profile === undefined ||
      question === null ||
      question === undefined ||
      this.mnemonic.trim() === ""
    ) return;
    this.loading = true;
    this.errorMessage = "";
    try {
      await createCardAnnotation(
        this.hass,
        this.profile.profile_id,
        question.card_key,
        this.mnemonic,
      );
      this.notice = this.t("learn.mnemonicSaved");
      this.mnemonic = "";
    } catch (error) {
      this.errorMessage = error instanceof Error ? error.message : String(error);
    } finally {
      this.loading = false;
    }
  }

  protected render() {
    if (this.profile === undefined) return nothing;
    if (!canAnswerProfile(this.profile)) {
      return html`<section class="learn-card"><p>${this.t("learn.readOnly")}</p></section>`;
    }
    const tracks = this.tracks();
    if (tracks.length === 0) {
      return html`<section class="learn-card"><p>${this.t("learn.noTracks")}</p></section>`;
    }
    const selected = this.selectedTrack();
    const resumable =
      selected?.last_session !== null &&
      selected?.last_session !== undefined &&
      ["active", "paused"].includes(selected.last_session.status);

    return html`
      <section class="learn-shell">
        <div class="toolbar">
          <label>
            <span>${this.t("learn.track")}</span>
            <select .value=${this.trackId} @change=${this.setTrack} ?disabled=${this.loading}>
              ${tracks.map(
                (track) => html`
                  <option value=${track.track_id}>
                    ${track.name} · ${track.source_language} → ${track.target_language}
                  </option>
                `,
              )}
            </select>
          </label>
          <div class="actions">
            ${resumable
              ? html`<button @click=${this.resume} ?disabled=${this.loading}>
                  ${this.t("learn.resume")}
                </button>`
              : nothing}
            <button class="primary" @click=${this.start} ?disabled=${this.loading}>
              ${this.t("learn.start")}
            </button>
          </div>
        </div>
        ${this.loading && this.session === undefined
          ? html`<div class="notice" role="status">${this.t("learn.loading")}</div>`
          : nothing}
        ${this.errorMessage
          ? html`<div class="error" role="alert">
              <strong>${this.t("learn.error")}</strong>
              <div>${this.errorMessage}</div>
            </div>`
          : nothing}
        ${this.notice
          ? html`<div class="notice" role="status" aria-live="polite">${this.notice}</div>`
          : nothing}
        ${this.renderSession()}
      </section>
    `;
  }

  private renderSession() {
    if (this.session === undefined) return nothing;
    if (this.session.question_count === 0) {
      return html`<section class="learn-card"><p>${this.t("learn.empty")}</p></section>`;
    }
    if (this.session.current_question === null || this.session.status === "completed") {
      return html`
        <section class="learn-card">
          <h2>${this.t("learn.completed")}</h2>
          <p>${this.t("learn.completedBody")}</p>
          <button class="primary" @click=${this.start} ?disabled=${this.loading}>
            ${this.t("learn.newSession")}
          </button>
        </section>
      `;
    }
    if (this.waitingUntil !== undefined) {
      return this.renderWaiting(this.session.current_question);
    }
    return isIntroductionQuestion(this.session.current_question)
      ? this.renderIntroduction(this.session.current_question)
      : this.renderRetrieval(this.session.current_question);
  }

  private renderWaiting(question: SessionQuestion) {
    const waitingUntil = this.waitingUntil;
    if (waitingUntil === undefined) return nothing;
    const due = new Date(waitingUntil);
    const formatted = Number.isNaN(due.getTime())
      ? ""
      : new Intl.DateTimeFormat(this.locale(), { timeStyle: "medium" }).format(due);
    return html`
      <article class="learn-card" aria-live="polite">
        ${this.renderProgress(question)}
        <div class="stage">${this.t("learn.waiting")}</div>
        <p>${this.t("learn.waitingBody")}</p>
        <p>
          ${this.t("learn.waitingUntil")}
          <time datetime=${waitingUntil}>${formatted}</time>
        </p>
      </article>
    `;
  }

  private renderProgress(question: SessionQuestion) {
    return html`
      <div class="progress">
        <span>${this.t("learn.progress")}</span>
        <span>${question.position + 1} / ${this.session?.question_count ?? 0}</span>
      </div>
    `;
  }

  private renderIntroduction(question: SessionQuestion) {
    const presentation = question.payload.presentation;
    if (presentation === undefined) return html`<section class="learn-card"></section>`;
    return html`
      <article class="learn-card">
        ${this.renderProgress(question)}
        <div class="stage">${this.t("learn.introduction")}</div>
        <p>${this.t("learn.introductionHelp")}</p>
        <div class="content">
          ${presentation.introduction_blocks.map((block, index) =>
            this.renderBlock(block, index === 0),
          )}
        </div>
        ${this.renderHintState(presentation.hint_blocks, presentation.mnemonic_blocks)}
        <div class="actions">
          <button
            class="primary"
            @click=${() => void this.learningAction("introduce")}
            ?disabled=${this.loading}
          >
            ${this.t("learn.continue")}
          </button>
        </div>
        ${this.renderSecondaryActions(question)}
      </article>
    `;
  }

  private renderRetrieval(question: SessionQuestion) {
    const presentation = question.payload.presentation;
    if (presentation === undefined) return html`<section class="learn-card"></section>`;
    const hintBlocks = [...presentation.hint_blocks, ...presentation.mnemonic_blocks];
    return html`
      <article class="learn-card">
        ${this.renderProgress(question)}
        <div class="stage">${this.t("learn.prompt")}</div>
        <div class="content">
          ${presentation.context.flatMap((facet) =>
            facet.blocks.map((block) => this.renderBlock(block, false)),
          )}
          ${presentation.prompt.blocks.map((block) => this.renderBlock(block, true))}
        </div>
        ${this.hintUsed
          ? html`
              <div class="hint-state" role="status">
                ${this.t("learn.hintUsed")}
                ${hintBlocks.map((block) => this.renderBlock(block, false))}
              </div>
            `
          : nothing}
        ${this.revealed
          ? html`
              <div class="answer">
                <div class="stage">${this.t("learn.answer")}</div>
                ${presentation.answer.blocks.map((block) => this.renderBlock(block, true))}
                ${this.pendingIdk
                  ? html`<p>${this.t("learn.feedbackIdk")}</p>`
                  : nothing}
              </div>
            `
          : nothing}
        <div class="actions">
          ${!this.revealed
            ? html`
                <button class="primary" @click=${this.reveal} ?disabled=${this.loading}>
                  ${this.t("learn.reveal")}
                </button>
                <button @click=${this.idk} ?disabled=${this.loading}>
                  ${this.t("learn.idk")}
                </button>
                ${hintBlocks.length > 0
                  ? html`<button @click=${this.showHint} ?disabled=${this.loading || this.hintUsed}>
                      ${this.t("learn.hint")}
                    </button>`
                  : nothing}
              `
            : this.pendingIdk
              ? html`<button
                  class="primary"
                  @click=${() =>
                    void this.learningAction("idk", this.pendingIdkLatency)}
                  ?disabled=${this.loading}
                >
                  ${this.t("learn.continue")}
                </button>`
              : html`
                  <button
                    @click=${() => void this.learningAction("review")}
                    ?disabled=${this.loading}
                  >
                    ${this.t("learn.review")}
                  </button>
                  <button
                    class="primary"
                    @click=${() => void this.learningAction("known")}
                    ?disabled=${this.loading}
                  >
                    ${this.t("learn.known")}
                  </button>
                `}
        </div>
        ${this.renderSecondaryActions(question)}
      </article>
    `;
  }

  private renderHintState(
    hintBlocks: LearnContentBlock[],
    mnemonicBlocks: LearnContentBlock[],
  ) {
    if (!this.hintUsed) return nothing;
    const blocks = [...hintBlocks, ...mnemonicBlocks];
    if (blocks.length === 0) return nothing;
    return html`
      <div class="hint-state" role="status">
        ${this.t("learn.hintUsed")}
        ${blocks.map((block) => this.renderBlock(block, false))}
      </div>
    `;
  }

  private renderSecondaryActions(question: SessionQuestion) {
    return html`
      <div class="secondary-actions">
        <button
          @click=${() => void this.setUserState("known_already")}
          ?disabled=${this.loading}
        >
          ${this.t("learn.knownAlready")}
        </button>
        <button
          @click=${() => void this.setUserState("suspended")}
          ?disabled=${this.loading}
        >
          ${this.t("learn.suspend")}
        </button>
        <button @click=${() => void this.report()} ?disabled=${this.loading}>
          ${this.t("learn.report")}
        </button>
      </div>
      <div class="annotation">
        <label>
          <span>${this.t("learn.mnemonic")}</span>
          <textarea
            .value=${this.mnemonic}
            placeholder=${this.t("learn.mnemonicPlaceholder")}
            @input=${(event: Event) => {
              const target = event.currentTarget;
              if (target instanceof HTMLTextAreaElement) this.mnemonic = target.value;
            }}
          ></textarea>
        </label>
        <div class="field-row">
          <button
            @click=${() => void this.saveMnemonic()}
            ?disabled=${this.loading || this.mnemonic.trim() === ""}
          >
            ${this.t("learn.saveMnemonic")}
          </button>
        </div>
      </div>
    `;
  }

  private renderBlock(block: LearnContentBlock, primary: boolean) {
    const raw = block.payload.text;
    if (typeof raw !== "string" || raw === "") return nothing;
    const language = block.language_tag ?? undefined;
    return html`
      <div
        class="content-block ${primary ? "primary-content" : ""}"
        lang=${language ?? nothing}
      >
        ${raw}
      </div>
    `;
  }
}

if (
  globalThis.customElements !== undefined &&
  customElements.get("locklearn-learn-view") === undefined
) {
  customElements.define("locklearn-learn-view", LockLearnLearnView);
}

declare global {
  interface HTMLElementTagNameMap {
    "locklearn-learn-view": LockLearnLearnView;
  }
}
