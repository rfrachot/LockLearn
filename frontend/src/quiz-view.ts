import { LitElement, css, html, nothing } from "lit";
import { property, state } from "lit/decorators.js";

import { languageFallback, translate, type UiLanguage } from "./i18n";
import {
  canQuizProfile,
  canReportFreeText,
  isChoiceQuiz,
  quizPayload,
} from "./quiz-model";
import {
  completeSession,
  evaluateQuizAnswer,
  getSession,
  reportFreeTextShouldBeAccepted,
  reportQuestion,
  startQuizSession,
  submitQuizAnswer,
  type DashboardResponse,
  type DashboardTrack,
  type HomeAssistantLike,
  type LearnContentBlock,
  type QuizFeedback,
  type QuizFormat,
  type QuizQuestionPayload,
  type SessionQuestion,
  type SessionState,
  type VisibleProfile,
} from "./protocol";

function nowMs(): number {
  return globalThis.performance?.now() ?? Date.now();
}

export class LockLearnQuizView extends LitElement {
  @property({ attribute: false }) hass?: HomeAssistantLike;
  @property({ attribute: false }) profile?: VisibleProfile;
  @property({ attribute: false }) dashboard?: DashboardResponse;

  @state() private trackId = "";
  @state() private format: QuizFormat = "mixed";
  @state() private session?: SessionState;
  @state() private loading = false;
  @state() private errorMessage = "";
  @state() private notice = "";
  @state() private feedback?: QuizFeedback;
  @state() private pendingAnswer?: Record<string, unknown>;
  @state() private pendingSession?: SessionState;
  @state() private freeText = "";
  @state() private hintUsed = false;

  private questionStartedAt = nowMs();
  private questionId: string | null = null;

  static styles = css`
    :host {
      display: block;
      min-width: 0;
      max-width: 100%;
    }

    .quiz-shell,
    .quiz-card,
    .toolbar,
    .actions,
    .options,
    .feedback,
    label {
      box-sizing: border-box;
      min-width: 0;
      max-width: 100%;
    }

    .quiz-shell {
      display: grid;
      gap: 16px;
    }

    .toolbar,
    .actions {
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

    .toolbar-fields {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      min-width: 0;
    }

    label {
      display: grid;
      gap: 6px;
      color: var(--secondary-text-color);
      font-size: 0.82rem;
    }

    select,
    input {
      box-sizing: border-box;
      min-width: 0;
      max-width: 100%;
      border: 1px solid var(--divider-color);
      border-radius: 8px;
      color: var(--primary-text-color);
      background: var(--card-background-color, var(--primary-background-color));
      font: inherit;
    }

    select {
      min-width: 180px;
      padding: 9px;
    }

    input {
      width: 100%;
      padding: 11px;
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

    .quiz-card {
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

    .format-label {
      color: var(--secondary-text-color);
      font-size: 0.85rem;
      font-weight: 650;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }

    .prompt {
      overflow-wrap: anywhere;
      font-size: clamp(1.5rem, 6vw, 3rem);
      line-height: 1.25;
      text-align: center;
    }

    .context,
    .hint,
    .feedback,
    .notice,
    .error {
      padding: 12px;
      border-radius: 9px;
      background: var(--secondary-background-color);
      line-height: 1.5;
    }

    .error {
      color: var(--error-color, var(--primary-text-color));
    }

    .options {
      display: grid;
      gap: 10px;
    }

    .option {
      width: 100%;
      text-align: left;
      overflow-wrap: anywhere;
    }

    .feedback-title {
      margin: 0 0 6px;
      font-weight: 700;
    }

    .feedback-detail {
      margin: 6px 0 0;
    }

    .free-text-form {
      display: grid;
      gap: 10px;
    }

    @media (max-width: 600px) {
      .toolbar,
      .toolbar-fields,
      .actions {
        align-items: stretch;
        flex-direction: column;
        width: 100%;
      }

      select,
      input,
      button {
        width: 100%;
        min-width: 0;
        max-width: 100%;
      }

      .progress {
        flex-direction: column;
        gap: 4px;
      }
    }
  `;

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
    this.resetQuestionUi();
  }

  private setFormat(event: Event): void {
    const target = event.currentTarget;
    if (!(target instanceof HTMLSelectElement)) return;
    this.format = target.value as QuizFormat;
    this.session = undefined;
    this.errorMessage = "";
    this.resetQuestionUi();
  }

  private resetQuestionUi(): void {
    this.feedback = undefined;
    this.pendingAnswer = undefined;
    this.pendingSession = undefined;
    this.freeText = "";
    this.hintUsed = false;
    this.notice = "";
    this.questionStartedAt = nowMs();
    this.questionId = this.session?.current_question?.question_id ?? null;
  }

  private applySession(session: SessionState): void {
    const nextQuestionId = session.current_question?.question_id ?? null;
    const changed = nextQuestionId !== this.questionId;
    this.session = session;
    if (changed) this.resetQuestionUi();
  }

  private elapsedMs(): number {
    return Math.max(0, Math.round(nowMs() - this.questionStartedAt));
  }

  private async start(): Promise<void> {
    if (
      this.hass === undefined ||
      this.profile === undefined ||
      this.trackId === "" ||
      !canQuizProfile(this.profile)
    ) return;
    this.loading = true;
    this.errorMessage = "";
    try {
      this.applySession(
        await startQuizSession(
          this.hass,
          this.profile.profile_id,
          this.trackId,
          10,
          this.format,
        ),
      );
    } catch (error) {
      this.errorMessage = error instanceof Error ? error.message : String(error);
    } finally {
      this.loading = false;
    }
  }

  private async resume(): Promise<void> {
    const last = this.selectedTrack()?.last_session;
    if (
      this.hass === undefined ||
      last === null ||
      last === undefined ||
      last.session_type !== "quiz"
    ) return;
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
        this.notice = this.t("quiz.reloaded");
        return;
      } catch {
        // Preserve the original error.
      }
    }
    this.errorMessage = error instanceof Error ? error.message : String(error);
  }

  private enrichAnswer(answer: Record<string, unknown>): Record<string, unknown> {
    return {
      ...answer,
      kind: "quiz",
      hint_used: this.hintUsed,
      presentation_to_answer_ms: this.elapsedMs(),
    };
  }

  private async evaluateFreeText(answer: Record<string, unknown>): Promise<void> {
    const question = this.session?.current_question;
    if (
      this.hass === undefined ||
      this.session === undefined ||
      question === null ||
      question === undefined
    ) return;
    const enriched = this.enrichAnswer(answer);
    this.loading = true;
    this.errorMessage = "";
    try {
      this.feedback = await evaluateQuizAnswer(
        this.hass,
        this.session.id,
        question.question_id,
        enriched,
      );
      this.pendingAnswer = enriched;
    } catch (error) {
      await this.recover(error);
    } finally {
      this.loading = false;
    }
  }

  private async submitDirect(answer: Record<string, unknown>): Promise<void> {
    const question = this.session?.current_question;
    if (
      this.hass === undefined ||
      this.session === undefined ||
      question === null ||
      question === undefined
    ) return;
    const enriched = this.enrichAnswer(answer);
    this.loading = true;
    this.errorMessage = "";
    try {
      const result = await submitQuizAnswer(
        this.hass,
        this.session,
        question.question_id,
        enriched,
      );
      this.feedback = result.feedback;
      this.pendingAnswer = undefined;
      this.pendingSession = result.session;
    } catch (error) {
      await this.recover(error);
    } finally {
      this.loading = false;
    }
  }

  private async submitProvisional(): Promise<void> {
    const question = this.session?.current_question;
    if (
      this.hass === undefined ||
      this.session === undefined ||
      question === null ||
      question === undefined ||
      this.pendingAnswer === undefined
    ) return;
    this.loading = true;
    this.errorMessage = "";
    try {
      const result = await submitQuizAnswer(
        this.hass,
        this.session,
        question.question_id,
        this.pendingAnswer,
      );
      if (this.feedback?.result === "correct") {
        await this.advanceSession(result.session);
        return;
      }
      this.feedback = result.feedback;
      this.pendingSession = result.session;
    } catch (error) {
      await this.recover(error);
    } finally {
      this.loading = false;
    }
  }

  private async advanceSession(session: SessionState): Promise<void> {
    let next = session;
    if (
      this.hass !== undefined &&
      next.status === "active" &&
      next.current_question === null &&
      next.question_count > 0
    ) {
      next = await completeSession(this.hass, next);
    }
    this.applySession(next);
  }

  private async advanceCommitted(): Promise<void> {
    if (this.pendingSession === undefined) return;
    this.loading = true;
    this.errorMessage = "";
    try {
      await this.advanceSession(this.pendingSession);
    } catch (error) {
      await this.recover(error);
    } finally {
      this.loading = false;
    }
  }

  private async acceptReportedFreeText(): Promise<void> {
    const question = this.session?.current_question;
    if (
      this.hass === undefined ||
      this.profile === undefined ||
      this.session === undefined ||
      this.session.track_id === null ||
      question === null ||
      question === undefined ||
      this.feedback === undefined ||
      this.pendingAnswer === undefined ||
      !canReportFreeText(this.feedback)
    ) return;
    this.loading = true;
    this.errorMessage = "";
    try {
      const receipt = await reportFreeTextShouldBeAccepted(
        this.hass,
        this.profile.profile_id,
        this.session.track_id,
        question,
        this.feedback,
      );
      if (receipt.srs_penalized) {
        throw new Error("unrecognized free-text report unexpectedly penalized SRS");
      }
      const answer = {
        ...this.pendingAnswer,
        should_be_accepted: true,
      };
      const result = await submitQuizAnswer(
        this.hass,
        this.session,
        question.question_id,
        answer,
      );
      await this.advanceSession(result.session);
      this.notice = this.t("quiz.reportAccepted");
    } catch (error) {
      await this.recover(error);
    } finally {
      this.loading = false;
    }
  }

  private async reportCurrentQuestion(): Promise<void> {
    const question = this.session?.current_question;
    if (
      this.hass === undefined ||
      this.profile === undefined ||
      this.session === undefined ||
      this.session.track_id === null ||
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
      );
      this.notice = this.t("quiz.reported");
    } catch (error) {
      this.errorMessage = error instanceof Error ? error.message : String(error);
    } finally {
      this.loading = false;
    }
  }

  private showHint(): void {
    this.hintUsed = true;
  }

  protected render() {
    if (this.profile === undefined) return nothing;
    if (!canQuizProfile(this.profile)) {
      return html`<section class="quiz-card"><p>${this.t("quiz.readOnly")}</p></section>`;
    }
    const tracks = this.tracks();
    if (tracks.length === 0) {
      return html`<section class="quiz-card"><p>${this.t("quiz.noTracks")}</p></section>`;
    }
    const selected = this.selectedTrack();
    const resumable =
      selected?.last_session?.session_type === "quiz" &&
      ["active", "paused"].includes(selected.last_session.status);

    return html`
      <section class="quiz-shell">
        <div class="toolbar">
          <div class="toolbar-fields">
            <label>
              <span>${this.t("quiz.track")}</span>
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
            <label>
              <span>${this.t("quiz.format")}</span>
              <select .value=${this.format} @change=${this.setFormat} ?disabled=${this.loading}>
                <option value="mixed">${this.t("quiz.formatMixed")}</option>
                <option value="mcq">${this.t("quiz.formatMcq")}</option>
                <option value="free_text">${this.t("quiz.formatFreeText")}</option>
                <option value="cloze_mcq">${this.t("quiz.formatCloze")}</option>
              </select>
            </label>
          </div>
          <div class="actions">
            ${resumable
              ? html`<button @click=${this.resume} ?disabled=${this.loading}>
                  ${this.t("quiz.resume")}
                </button>`
              : nothing}
            <button class="primary" @click=${this.start} ?disabled=${this.loading}>
              ${this.t("quiz.start")}
            </button>
          </div>
        </div>
        ${this.errorMessage
          ? html`<div class="error" role="alert">
              <strong>${this.t("quiz.error")}</strong>
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
      return html`<section class="quiz-card"><p>${this.t("quiz.empty")}</p></section>`;
    }
    if (this.session.current_question === null || this.session.status === "completed") {
      return html`
        <section class="quiz-card">
          <h2>${this.t("quiz.completed")}</h2>
          <p>${this.t("quiz.completedBody")}</p>
          <button class="primary" @click=${this.start} ?disabled=${this.loading}>
            ${this.t("quiz.newSession")}
          </button>
        </section>
      `;
    }
    const payload = quizPayload(this.session.current_question);
    if (payload === undefined) {
      return html`<section class="quiz-card"><p>${this.t("quiz.invalidQuestion")}</p></section>`;
    }
    return this.renderQuestion(this.session.current_question, payload);
  }

  private renderQuestion(question: SessionQuestion, payload: QuizQuestionPayload) {
    return html`
      <article class="quiz-card">
        <div class="progress">
          <span>${this.t("quiz.progress")}</span>
          <span>${question.position + 1} / ${this.session?.question_count ?? 0}</span>
        </div>
        <div class="format-label">${this.formatLabel(payload.format)}</div>
        ${payload.context_hint
          ? html`<div class="context">
              <strong>${this.t("quiz.context")}</strong>
              <div>${payload.context_hint}</div>
            </div>`
          : nothing}
        <div class="prompt">${payload.prompt_text}</div>
        ${this.hintUsed
          ? html`<div class="hint" role="status">
              <strong>${this.t("quiz.hintUsed")}</strong>
              ${payload.hint_blocks.map((block) => this.renderBlock(block))}
            </div>`
          : nothing}
        ${this.feedback === undefined
          ? this.renderInput(payload)
          : this.renderFeedback(question, this.feedback)}
        <div class="actions">
          ${this.feedback === undefined && payload.hint_blocks.length > 0
            ? html`<button @click=${this.showHint} ?disabled=${this.loading || this.hintUsed}>
                ${this.t("quiz.hint")}
              </button>`
            : nothing}
          <button @click=${() => void this.reportCurrentQuestion()} ?disabled=${this.loading}>
            ${this.t("quiz.report")}
          </button>
        </div>
      </article>
    `;
  }

  private renderInput(payload: QuizQuestionPayload) {
    if (isChoiceQuiz(payload)) {
      return html`
        <div class="options" aria-label=${this.t("quiz.answers")}>
          ${payload.options.map(
            (option, index) => html`
              <button
                class="option"
                @click=${() =>
                  void this.submitDirect({
                    selected_answer_id: option.answer_id,
                  })}
                ?disabled=${this.loading}
              >
                ${index + 1}. ${option.text}
              </button>
            `,
          )}
          <button
            @click=${() => void this.submitDirect({ selected_answer_id: null })}
            ?disabled=${this.loading}
          >
            ${this.t("quiz.idk")}
          </button>
        </div>
      `;
    }
    return html`
      <form
        class="free-text-form"
        @submit=${(event: SubmitEvent) => {
          event.preventDefault();
          if (this.freeText.trim() !== "") {
            void this.evaluateFreeText({ submitted_text: this.freeText });
          }
        }}
      >
        <label>
          <span>${this.t("quiz.yourAnswer")}</span>
          <input
            autocomplete="off"
            .value=${this.freeText}
            @input=${(event: Event) => {
              const target = event.currentTarget;
              if (target instanceof HTMLInputElement) this.freeText = target.value;
            }}
            ?disabled=${this.loading}
          />
        </label>
        <div class="actions">
          <button
            class="primary"
            type="submit"
            ?disabled=${this.loading || this.freeText.trim() === ""}
          >
            ${this.t("quiz.check")}
          </button>
          <button
            type="button"
            @click=${() => void this.submitDirect({ action: "idk" })}
            ?disabled=${this.loading}
          >
            ${this.t("quiz.idk")}
          </button>
        </div>
      </form>
    `;
  }

  private renderFeedback(question: SessionQuestion, feedback: QuizFeedback) {
    return html`
      <div class="feedback" role="status" aria-live="polite">
        <p class="feedback-title">${this.feedbackLabel(feedback.result)}</p>
        ${feedback.selected_answer
          ? html`<p class="feedback-detail">
              ${this.t("quiz.yourChoice")}: ${feedback.selected_answer}
            </p>`
          : nothing}
        ${feedback.reveal_correct_answer && feedback.correct_answer
          ? html`<p class="feedback-detail">
              ${this.t("quiz.correctAnswer")}: ${feedback.correct_answer}
            </p>`
          : nothing}
        ${feedback.contrastive_feedback
          ? html`<p class="feedback-detail">${this.t("quiz.contrastive")}</p>`
          : nothing}
        <div class="actions">
          ${this.pendingSession !== undefined
            ? html`<button
                class="primary"
                @click=${() => void this.advanceCommitted()}
                ?disabled=${this.loading}
              >
                ${this.t("quiz.continue")}
              </button>`
            : html`<button
                class="primary"
                @click=${() => void this.submitProvisional()}
                ?disabled=${this.loading}
              >
                ${feedback.result === "wrong"
                  ? this.t("quiz.showCorrection")
                  : this.t("quiz.continue")}
              </button>`}
          ${canReportFreeText(feedback)
            ? html`<button
                @click=${() => void this.acceptReportedFreeText()}
                ?disabled=${this.loading}
              >
                ${this.t("quiz.shouldAccept")}
              </button>`
            : nothing}
        </div>
      </div>
    `;
  }

  private formatLabel(format: QuizQuestionPayload["format"]): string {
    if (format === "mcq") return this.t("quiz.formatMcq");
    if (format === "cloze_mcq") return this.t("quiz.formatCloze");
    return this.t("quiz.formatFreeText");
  }

  private feedbackLabel(result: QuizFeedback["result"]): string {
    if (result === "correct") return this.t("quiz.correct");
    if (result === "wrong") return this.t("quiz.wrong");
    if (result === "idk") return this.t("quiz.idkFeedback");
    return this.t("quiz.unrecognized");
  }

  private renderBlock(block: LearnContentBlock) {
    const raw = block.payload.text;
    if (typeof raw !== "string" || raw === "") return nothing;
    return html`<div lang=${block.language_tag ?? nothing}>${raw}</div>`;
  }
}

if (
  globalThis.customElements !== undefined &&
  customElements.get("locklearn-quiz-view") === undefined
) {
  customElements.define("locklearn-quiz-view", LockLearnQuizView);
}

declare global {
  interface HTMLElementTagNameMap {
    "locklearn-quiz-view": LockLearnQuizView;
  }
}
