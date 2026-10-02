import { LitElement, css, html, nothing } from "lit";
import { property, state } from "lit/decorators.js";

import "./concerned-cards";

import {
  contentRendererStyles,
  interactiveAccessibilityStyles,
  renderContentBlock,
} from "./content-renderer";
import { languageFallback, translate, type UiLanguage } from "./i18n";
import { findReadyAlternative, type ReadyAlternative } from "./next-action";
import { navigateToRoute } from "./router";
import {
  canAnswerProfile,
  isIntroductionQuestion,
  isResumableLearnSession,
  questionAvailableAtMs,
  shouldShowKnownAlreadyBulkGuard,
} from "./learn-model";
import {
  answerSession,
  armReadyReminder,
  cancelReadyReminder,
  completeSession,
  createCardAnnotation,
  getReadyReminderStatus,
  getSession,
  getSessionAvailability,
  listNotificationTargets,
  reportQuestion,
  setCardUserState,
  startCalibrationSession,
  startLearnSession,
  startQuizSession,
  undoLastProgress,
  type ConcernedCardsFilter,
  type DashboardResponse,
  type DashboardTrack,
  type HomeAssistantLike,
  type LearnContentBlock,
  type ReadyReminderStatus,
  type SessionAvailability,
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
  @property({ attribute: false }) externalSession?: SessionState;

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
  @state() private availability?: SessionAvailability;
  @state() private forceEarlyCurrent = false;
  @state() private reminder?: ReadyReminderStatus;
  @state() private submissionSlow = false;
  @state() private retryRequest?: {
    session: SessionState;
    questionId: string;
    answer: Record<string, unknown>;
  };
  @state() private lastKnownCardKey?: string;
  @state() private knownNoticeVisible = false;
  @state() private concernedFilter?: ConcernedCardsFilter;
  @state() private readyAlternative?: ReadyAlternative;
  @state() private calibrationSetup = false;
  @state() private calibrationSize = 20;
  @state() private hasNotificationTarget = false;
  @state() private knownBulkGuardVisible = false;

  private questionStartedAt = nowMs();
  private questionId: string | null = null;
  private availabilityTimer?: ReturnType<typeof globalThis.setTimeout>;
  private nextDueTimer?: ReturnType<typeof globalThis.setTimeout>;
  private submissionTimer?: ReturnType<typeof globalThis.setTimeout>;
  private knownUndoTimer?: ReturnType<typeof globalThis.setTimeout>;
  private readonly refreshOnReturn = () => {
    if (document.visibilityState === "visible") void this.refreshAvailability();
  };

  static styles = css`
    ${contentRendererStyles}
    ${interactiveAccessibilityStyles}

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

    dl {
      display: grid;
      grid-template-columns: minmax(170px, auto) 1fr;
      gap: 6px 12px;
      margin: 12px 0 0;
    }

    dt {
      color: var(--secondary-text-color);
    }

    dd {
      margin: 0;
      font-weight: 650;
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

    .bulk-guard {
      position: fixed;
      z-index: 1200;
      inset: 0;
      display: grid;
      place-items: center;
      padding: 20px;
      background: rgb(0 0 0 / 45%);
    }

    .bulk-guard-card {
      width: min(520px, 100%);
      display: grid;
      gap: 14px;
      padding: 20px;
      border-radius: 14px;
      background: var(--card-background-color, var(--primary-background-color));
      box-shadow: var(--ha-card-box-shadow, 0 12px 36px rgb(0 0 0 / 30%));
    }

    .known-snackbar {
      position: fixed;
      z-index: 1100;
      inset-inline: 16px;
      bottom: max(16px, env(safe-area-inset-bottom));
      width: min(560px, calc(100% - 32px));
      margin-inline: auto;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 12px 14px;
      border-radius: 12px;
      background: var(--card-background-color, var(--primary-background-color));
      color: var(--primary-text-color);
      box-shadow: var(--ha-card-box-shadow, 0 8px 28px rgb(0 0 0 / 24%));
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

  connectedCallback(): void {
    super.connectedCallback();
    globalThis.addEventListener("focus", this.refreshOnReturn);
    globalThis.addEventListener("online", this.refreshOnReturn);
    globalThis.addEventListener("pageshow", this.refreshOnReturn);
    document.addEventListener("visibilitychange", this.refreshOnReturn);
  }

  disconnectedCallback(): void {
    this.clearAvailabilityTimer();
    if (this.nextDueTimer !== undefined) globalThis.clearTimeout(this.nextDueTimer);
    if (this.submissionTimer !== undefined) globalThis.clearTimeout(this.submissionTimer);
    if (this.knownUndoTimer !== undefined) globalThis.clearTimeout(this.knownUndoTimer);
    globalThis.removeEventListener("focus", this.refreshOnReturn);
    globalThis.removeEventListener("online", this.refreshOnReturn);
    globalThis.removeEventListener("pageshow", this.refreshOnReturn);
    document.removeEventListener("visibilitychange", this.refreshOnReturn);
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
      void this.refreshAvailability();
    }
    if (
      changed.has("externalSession") &&
      this.externalSession !== undefined &&
      this.profile !== undefined &&
      this.externalSession.profile_id === this.profile.profile_id
    ) {
      this.trackId = this.externalSession.track_id ?? this.trackId;
      this.applySession(this.externalSession);
      this.notice = this.t("learn.targetedSession");
      this.dispatchEvent(
        new CustomEvent("locklearn-session-handoff-consumed", {
          bubbles: true,
          composed: true,
        }),
      );
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
    void this.refreshAvailability();
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
    this.forceEarlyCurrent = false;
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

  private async refreshAvailability(): Promise<void> {
    if (
      this.hass === undefined ||
      this.profile === undefined ||
      this.trackId === ""
    ) {
      this.availability = undefined;
      return;
    }
    try {
      this.availability = await getSessionAvailability(
        this.hass,
        this.profile.profile_id,
        this.trackId,
        "learn",
      );
      this.readyAlternative = this.availability.available_now === 0
        ? await findReadyAlternative(this.hass, this.dashboard, this.trackId, "learn")
        : undefined;
      this.reminder = await getReadyReminderStatus(
        this.hass,
        this.profile.profile_id,
        this.trackId,
        "learn",
      );
      this.hasNotificationTarget = (
        await listNotificationTargets(this.hass, this.profile.profile_id)
      ).some((target) => target.enabled);
      if (this.nextDueTimer !== undefined) globalThis.clearTimeout(this.nextDueTimer);
      const nextAvailable = this.availability.next_available_at_utc;
      if (nextAvailable !== null) {
        const delay = Date.parse(nextAvailable) - Date.now();
        if (delay > 0 && delay < 2_147_000_000) {
          this.nextDueTimer = globalThis.setTimeout(() => {
            this.nextDueTimer = undefined;
            void this.refreshAvailability();
          }, delay + 250);
        }
      }
    } catch {
      this.availability = undefined;
      this.readyAlternative = undefined;
    }
  }

  private async openReadyAlternative(): Promise<void> {
    if (
      this.hass === undefined ||
      this.profile === undefined ||
      this.readyAlternative === undefined
    ) return;
    const alternative = this.readyAlternative;
    this.loading = true;
    this.errorMessage = "";
    try {
      if (alternative.mode === "learn") {
        this.trackId = alternative.trackId;
        this.session = undefined;
        this.resetQuestionUi();
        this.applySession(await startLearnSession(
          this.hass,
          this.profile.profile_id,
          alternative.trackId,
        ));
        await this.refreshAvailability();
        return;
      }
      const session = await startQuizSession(
        this.hass,
        this.profile.profile_id,
        alternative.trackId,
      );
      this.dispatchEvent(new CustomEvent("locklearn-open-session", {
        detail: { session },
        bubbles: true,
        composed: true,
      }));
    } catch (error) {
      this.errorMessage = error instanceof Error ? error.message : String(error);
    } finally {
      this.loading = false;
    }
  }

  private dueLabel(value: string | null): string {
    if (value === null) return "";
    const due = new Date(value);
    if (Number.isNaN(due.getTime())) return "";
    const minutes = Math.max(1, Math.ceil((due.getTime() - Date.now()) / 60_000));
    const time = new Intl.DateTimeFormat(this.locale(), { timeStyle: "short" }).format(due);
    return `${time} · ${this.t("learn.inAbout")} ${minutes} min`;
  }

  private continueCurrentEarly(): void {
    this.clearAvailabilityTimer();
    this.waitingUntil = undefined;
    this.forceEarlyCurrent = true;
    this.questionStartedAt = nowMs();
  }

  private elapsedMs(): number {
    return Math.max(0, Math.round(nowMs() - this.questionStartedAt));
  }

  private beginSubmissionWatch(): void {
    this.submissionSlow = false;
    if (this.submissionTimer !== undefined) globalThis.clearTimeout(this.submissionTimer);
    this.submissionTimer = globalThis.setTimeout(() => {
      this.submissionTimer = undefined;
      this.submissionSlow = true;
    }, 8000);
  }

  private endSubmissionWatch(): void {
    if (this.submissionTimer !== undefined) globalThis.clearTimeout(this.submissionTimer);
    this.submissionTimer = undefined;
    this.submissionSlow = false;
  }

  private async verifySubmission(): Promise<void> {
    if (this.hass === undefined || this.session === undefined) return;
    try {
      const basis = this.retryRequest?.session ?? this.session;
      const canonical = await getSession(this.hass, basis.id);
      const advanced =
        canonical.version !== basis.version ||
        canonical.current_question?.question_id !== basis.current_question?.question_id;
      this.applySession(canonical);
      if (advanced) {
        this.loading = false;
        this.retryRequest = undefined;
        this.endSubmissionWatch();
        this.notice = this.t("learn.answerApplied");
      } else {
        this.loading = false;
        this.submissionSlow = true;
        this.notice = this.t("learn.answerNotConfirmed");
      }
    } catch (error) {
      this.errorMessage = error instanceof Error ? error.message : String(error);
    }
  }

  private async retrySubmission(): Promise<void> {
    if (this.hass === undefined || this.retryRequest === undefined) return;
    const request = this.retryRequest;
    this.loading = true;
    this.errorMessage = "";
    try {
      const canonical = await getSession(this.hass, request.session.id);
      const stillCurrent =
        canonical.version === request.session.version &&
        canonical.current_question?.question_id === request.questionId;
      if (!stillCurrent) {
        this.applySession(canonical);
        this.retryRequest = undefined;
        this.endSubmissionWatch();
        this.notice = this.t("learn.answerApplied");
        return;
      }
      this.applySession(await answerSession(
        this.hass,
        request.session,
        request.questionId,
        request.answer,
      ));
      this.retryRequest = undefined;
      this.endSubmissionWatch();
      await this.refreshAvailability();
    } catch (error) {
      await this.recover(error);
    } finally {
      this.loading = false;
    }
  }

  private async armReminder(): Promise<void> {
    if (this.hass === undefined || this.profile === undefined || this.trackId === "") return;
    this.loading = true;
    this.errorMessage = "";
    try {
      this.reminder = await armReadyReminder(this.hass, this.profile.profile_id, this.trackId, "learn");
      this.notice = this.t("learn.reminderArmed");
    } catch (error) {
      this.errorMessage = error instanceof Error ? error.message : String(error);
    } finally {
      this.loading = false;
    }
  }

  private async cancelReminder(): Promise<void> {
    if (this.hass === undefined || this.profile === undefined || this.trackId === "") return;
    this.loading = true;
    try {
      this.reminder = await cancelReadyReminder(this.hass, this.profile.profile_id, this.trackId, "learn");
      this.notice = this.t("learn.reminderCancelled");
    } finally {
      this.loading = false;
    }
  }

  private openCalibrationSetup(): void {
    this.calibrationSetup = true;
  }

  private closeCalibrationSetup(): void {
    this.calibrationSetup = false;
  }

  private setCalibrationSize(event: Event): void {
    const target = event.currentTarget;
    if (!(target instanceof HTMLSelectElement)) return;
    const value = Number.parseInt(target.value, 10);
    if ([20, 30, 40].includes(value)) this.calibrationSize = value;
  }

  private async startCalibration(): Promise<void> {
    if (this.hass === undefined || this.profile === undefined || this.trackId === "") return;
    this.loading = true;
    this.errorMessage = "";
    try {
      const session = await startCalibrationSession(
        this.hass,
        this.profile.profile_id,
        this.trackId,
        this.calibrationSize,
      );
      this.calibrationSetup = false;
      this.dispatchEvent(new CustomEvent("locklearn-open-session", {
        detail: { session },
        bubbles: true,
        composed: true,
      }));
    } catch (error) {
      this.errorMessage = error instanceof Error ? error.message : String(error);
    } finally {
      this.loading = false;
    }
  }

  private bulkGuardStorageKey(sessionId: string): string {
    return `locklearn:known-bulk-guard:${sessionId}`;
  }

  private maybeShowKnownBulkGuard(): void {
    if (this.session === undefined) return;
    if (!shouldShowKnownAlreadyBulkGuard(this.session.answers)) return;
    const key = this.bulkGuardStorageKey(this.session.id);
    if (globalThis.localStorage?.getItem(key) === "shown") return;
    globalThis.localStorage?.setItem(key, "shown");
    this.knownBulkGuardVisible = true;
  }

  private dismissKnownBulkGuard(): void {
    this.knownBulkGuardVisible = false;
  }

  private startCalibrationFromBulkGuard(): void {
    this.knownBulkGuardVisible = false;
    this.calibrationSetup = true;
  }

  private async markKnownAlready(question: SessionQuestion): Promise<void> {
    this.lastKnownCardKey = question.card_key;
    await this.learningAction("known_already");
    this.maybeShowKnownBulkGuard();
    if (this.lastKnownCardKey !== question.card_key) return;
    this.notice = "";
    this.knownNoticeVisible = true;
    if (this.knownUndoTimer !== undefined) globalThis.clearTimeout(this.knownUndoTimer);
    this.knownUndoTimer = globalThis.setTimeout(() => {
      this.knownUndoTimer = undefined;
      this.knownNoticeVisible = false;
      this.lastKnownCardKey = undefined;
    }, 8000);
  }

  private async undoKnownAlready(): Promise<void> {
    if (
      this.hass === undefined || this.profile === undefined || this.session === undefined ||
      this.session.track_id === null || this.lastKnownCardKey === undefined
    ) return;
    this.loading = true;
    try {
      await undoLastProgress(this.hass, this.profile.profile_id, this.session.track_id, this.lastKnownCardKey);
      this.lastKnownCardKey = undefined;
      this.knownNoticeVisible = false;
      if (this.knownUndoTimer !== undefined) globalThis.clearTimeout(this.knownUndoTimer);
      this.knownUndoTimer = undefined;
      this.notice = this.t("learn.knownUndone");
      await this.refreshAvailability();
    } catch (error) {
      this.errorMessage = error instanceof Error ? error.message : String(error);
    } finally {
      this.loading = false;
    }
  }
  private async start(allowEarlyLearning = false): Promise<void> {
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
        undefined,
        allowEarlyLearning,
      );
      this.applySession(session);
      await this.refreshAvailability();
    } catch (error) {
      this.errorMessage = error instanceof Error ? error.message : String(error);
    } finally {
      this.loading = false;
    }
  }

  private async resume(): Promise<void> {
    const last = this.selectedTrack()?.last_session;
    if (this.hass === undefined || !isResumableLearnSession(last)) return;
    this.loading = true;
    this.errorMessage = "";
    try {
      this.applySession(await getSession(this.hass, last.session_id));
      await this.refreshAvailability();
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
    action: "introduce" | "known_already" | "known" | "review" | "idk",
    latency?: number,
  ): Promise<void> {
    const question = this.session?.current_question;
    if (this.hass === undefined || this.session === undefined || question === null || question === undefined) return;
    const requestSession = this.session;
    const requestAnswer = {
      kind: "learning",
      action,
      hint_used: this.hintUsed,
      presentation_to_answer_ms: latency ?? this.elapsedMs(),
      ...(this.forceEarlyCurrent ? { force_early: true } : {}),
    };
    this.retryRequest = {
      session: requestSession,
      questionId: question.question_id,
      answer: requestAnswer,
    };
    this.loading = true;
    this.errorMessage = "";
    this.beginSubmissionWatch();
    try {
      const answered = await answerSession(
        this.hass,
        requestSession,
        question.question_id,
        requestAnswer,
      );
      this.retryRequest = undefined;
      this.applySession(await this.finalizeIfDone(answered));
      await this.refreshAvailability();
    } catch (error) {
      await this.recover(error);
    } finally {
      this.loading = false;
      this.endSubmissionWatch();
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

  private async setUserState(userState: "suspended"): Promise<void> {
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
      await this.refreshAvailability();
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
    const resumable = isResumableLearnSession(selected?.last_session);

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
            ${this.session === undefined && resumable
              ? html`<button class="primary" @click=${this.resume} ?disabled=${this.loading}>
                  ${this.t("learn.resume")}
                </button>`
              : this.session === undefined ? html`<button class="primary" @click=${() => void this.start()} ?disabled=${this.loading}>
                  ${this.t("learn.start")}
                </button>` : nothing}
          </div>
          ${this.session === undefined ? html`<p class="muted">
            ${resumable ? this.t("learn.resumeHelp") : this.t("learn.startHelp")}
          </p>` : nothing}
        </div>
        ${this.session === undefined && this.availability !== undefined ? html`
          <div class="notice" role="status">
            <strong>${this.t("learn.readiness")}</strong>
            ${this.availability.available_now > 0
              ? html`<div>${this.availability.available_now} ${this.t("learn.cardsReady")}</div>`
              : html`
                  <div>${this.t("learn.noCardsReady")}</div>
                  <dl>
                    <dt>${this.t("learn.startedCards")}</dt><dd>${this.availability.introduced_cards}</dd>
                    <dt>${this.t("learn.unstartedCards")}</dt><dd>${this.availability.new_cards}</dd>
                    <dt>${this.t("learn.newQuotaRemaining")}</dt><dd>${this.availability.remaining_new_quota}</dd>
                  </dl>
                  ${this.availability.next_available_at_utc === null
                    ? html`<div class="muted">${this.t("learn.noExactTime")}</div>`
                    : html`
                        <div>
                          <strong>${this.t(
                            this.availability.next_available_reason === "new_quota"
                              ? "learn.quotaReset"
                              : "learn.nextAvailable",
                          )}:</strong>
                          ${this.dueLabel(this.availability.next_available_at_utc)}
                        </div>
                      `}
                  ${this.availability.forceable_early > 0 ? html`
                    <p class="muted">
                      ${this.availability.forceable_new > 0
                        ? this.t("learn.overrideNewHelp")
                        : this.t("learn.continueEarlyHelp")}
                    </p>
                    <button class="primary" @click=${() => void this.start(true)} ?disabled=${this.loading}>
                      ${this.t("learn.continueNow")}
                    </button>
                  ` : nothing}
                `}
          </div>
        ` : nothing}
        ${this.session === undefined ? this.renderNoDeadEndActions() : nothing}
        ${this.session === undefined && this.calibrationSetup
          ? html`
              <section class="learn-card" role="dialog" aria-labelledby="calibration-title">
                <h2 id="calibration-title">${this.t("learn.calibrationTitle")}</h2>
                <p>${this.t("learn.calibrationHelp")}</p>
                <label>
                  <span>${this.t("learn.calibrationSize")}</span>
                  <select .value=${String(this.calibrationSize)} @change=${this.setCalibrationSize}>
                    <option value="20">20</option>
                    <option value="30">30</option>
                    <option value="40">40</option>
                  </select>
                </label>
                <div class="actions">
                  <button class="primary" @click=${() => void this.startCalibration()} ?disabled=${this.loading}>
                    ${this.t("learn.calibrationStart")}
                  </button>
                  <button @click=${this.closeCalibrationSetup} ?disabled=${this.loading}>
                    ${this.t("common.close")}
                  </button>
                </div>
              </section>
            `
          : nothing}
        ${this.loading && this.session === undefined
          ? html`<div class="notice" role="status">${this.t("learn.loading")}</div>`
          : nothing}
        ${this.errorMessage
          ? html`<div class="error" role="alert">
              <strong>${this.t("learn.error")}</strong>
              <div>${this.errorMessage}</div>
            </div>`
          : nothing}
        ${this.submissionSlow
          ? html`<div class="notice" role="status" aria-live="polite">
              <strong>${this.t("learn.answerUnconfirmed")}</strong>
              <button @click=${() => void this.verifySubmission()}>${this.t("learn.verify")}</button>
              ${this.retryRequest === undefined
                ? nothing
                : html`<button @click=${() => void this.retrySubmission()}>${this.t("learn.retryAnswer")}</button>`}
            </div>`
          : nothing}
        ${this.notice
          ? html`<div class="notice" role="status" aria-live="polite">${this.notice}</div>`
          : nothing}
        ${this.renderSession()}
        ${this.knownBulkGuardVisible
          ? html`<div class="bulk-guard" role="presentation">
              <section class="bulk-guard-card" role="dialog" aria-modal="true" aria-labelledby="known-bulk-title">
                <h2 id="known-bulk-title">${this.t("learn.bulkGuardTitle")}</h2>
                <p>${this.t("learn.bulkGuardBody")}</p>
                <div class="actions">
                  <button class="primary" @click=${this.startCalibrationFromBulkGuard}>
                    ${this.t("learn.bulkGuardCalibrate")}
                  </button>
                  <button @click=${this.dismissKnownBulkGuard}>
                    ${this.t("learn.bulkGuardContinue")}
                  </button>
                </div>
              </section>
            </div>`
          : nothing}
        ${this.knownNoticeVisible && this.lastKnownCardKey !== undefined
          ? html`<div class="known-snackbar" role="status" aria-live="polite">
              <span>${this.t("learn.knownPending")}</span>
              <button @click=${() => void this.undoKnownAlready()} ?disabled=${this.loading}>
                ${this.t("learn.undo")}
              </button>
            </div>`
          : nothing}
        ${this.concernedFilter === undefined
          ? nothing
          : html`<locklearn-concerned-cards
              .hass=${this.hass}
              .profileId=${this.profile.profile_id}
              .trackId=${this.trackId}
              .filter=${this.concernedFilter}
              .mode=${"learn"}
              .language=${this.locale()}
              @locklearn-concerned-cards-close=${this.closeConcerned}
              @locklearn-concerned-cards-changed=${() => void this.refreshAvailability()}
            ></locklearn-concerned-cards>`}
      </section>
    `;
  }

  private blockerFilter(code: string): ConcernedCardsFilter {
    if (code === "known_already_verification") return "known_pending";
    if (code === "suspended") return "suspended";
    if (code === "buried") return "buried";
    if (code === "prerequisite") return "prerequisite_support";
    return "current_waiting_context";
  }

  private openConcerned(filter: ConcernedCardsFilter): void {
    this.concernedFilter = filter;
  }

  private closeConcerned(): void {
    this.concernedFilter = undefined;
  }

  private renderNoDeadEndActions() {
    const availability = this.availability;
    if (availability === undefined) return nothing;
    const canRemind =
      availability.available_now === 0 && availability.next_available_at_utc !== null;
    return html`
      <div class="actions">
        ${availability.new_cards > 0
          ? html`<button @click=${this.openCalibrationSetup} ?disabled=${this.loading}>
              ${this.t("learn.quickCalibration")}
            </button>`
          : nothing}
        ${this.readyAlternative === undefined
          ? nothing
          : html`<button @click=${() => void this.openReadyAlternative()} ?disabled=${this.loading}>
              ${this.t("learn.readyAlternative")
                .replace("{track}", this.readyAlternative.trackName)
                .replace("{mode}", this.readyAlternative.mode === "learn"
                  ? this.t("learn.title")
                  : this.t("quiz.title"))}
            </button>`}
        ${canRemind
          ? !this.hasNotificationTarget
            ? html`<button @click=${() => navigateToRoute("settings")}>${this.t("learn.configureNotifications")}</button>`
            : this.reminder?.active
              ? html`<button @click=${() => void this.cancelReminder()} ?disabled=${this.loading}>
                  ${this.t("learn.cancelReminder")}
                </button>`
              : html`<button @click=${() => void this.armReminder()} ?disabled=${this.loading}>
                  ${this.t("learn.remindMe")}
                </button>`
          : nothing}
      </div>
      ${availability.blockers.length > 0
        ? html`<details>
            <summary>${this.t("learn.conditionsTitle")}</summary>
            <dl>
              ${availability.blockers.map(
                (blocker) => html`
                  <dt>${blocker.code}</dt>
                  <dd>
                    ${blocker.count}
                    ${blocker.until_utc === null ? nothing : html` · ${this.dueLabel(blocker.until_utc)}`}
                    <button
                      @click=${() => this.openConcerned(this.blockerFilter(blocker.code))}
                      ?disabled=${this.loading}
                    >
                      ${this.t("learn.viewCards")}
                    </button>
                  </dd>
                `,
              )}
            </dl>
          </details>`
        : nothing}
    `;
  }
  private renderSession() {
    if (this.session === undefined) return nothing;
    if (this.session.question_count === 0) {
      const nextAvailable = this.availability?.next_available_at_utc ?? null;
      const nextReason = this.availability?.next_available_reason ?? null;
      const canContinue = (this.availability?.forceable_early ?? 0) > 0;
      const readyNow = this.availability?.available_now ?? 0;
      if (readyNow > 0) {
        return html`
          <section class="learn-card">
            <h2>${this.t("learn.readyTitle")}</h2>
            <p>${this.t("learn.readyFromEmpty").replace("{count}", String(readyNow))}</p>
            <button class="primary" @click=${() => void this.start()} ?disabled=${this.loading}>
              ${this.t("learn.start")}
            </button>
          </section>
        `;
      }
      return html`
        <section class="learn-card">
          <h2>${this.t("learn.pauseTitle")}</h2>
          <p>${this.t("learn.emptyExplain")}</p>
          <dl>
            <dt>${this.t("learn.startedCards")}</dt><dd>${this.availability?.introduced_cards ?? 0}</dd>
            <dt>${this.t("learn.unstartedCards")}</dt><dd>${this.availability?.new_cards ?? 0}</dd>
            <dt>${this.t("learn.newQuotaRemaining")}</dt><dd>${this.availability?.remaining_new_quota ?? 0}</dd>
          </dl>
          ${nextAvailable === null
            ? html`<p class="muted">${this.t("learn.noExactTime")}</p>`
            : html`
                <p>
                  <strong>${this.t(
                    nextReason === "new_quota" ? "learn.quotaReset" : "learn.nextAvailable",
                  )}:</strong>
                  ${this.dueLabel(nextAvailable)}
                </p>
              `}
          ${canContinue ? html`
            <p class="muted">
              ${(this.availability?.forceable_new ?? 0) > 0
                ? this.t("learn.overrideNewHelp")
                : this.t("learn.continueEarlyHelp")}
            </p>
            <button class="primary" @click=${() => void this.start(true)} ?disabled=${this.loading}>
              ${this.t("learn.continueNow")}
            </button>
          ` : nothing}
        </section>
      `;
    }
    if (this.session.current_question === null || this.session.status === "completed") {
      const nextAvailable = this.availability?.next_available_at_utc ?? null;
      const nextReason = this.availability?.next_available_reason ?? null;
      const canContinue = (this.availability?.forceable_early ?? 0) > 0;
      return html`
        <section class="learn-card">
          <h2>${this.t("learn.completed")}</h2>
          <p>${this.t("learn.completedBody")}</p>
          ${nextAvailable === null ? nothing : html`
            <p>
              <strong>${this.t(
                nextReason === "new_quota" ? "learn.quotaReset" : "learn.nextAvailable",
              )}:</strong>
              ${this.dueLabel(nextAvailable)}
            </p>
          `}
          ${canContinue ? html`
            <p class="muted">${this.t("learn.continueEarlyHelp")}</p>
            <button class="primary" @click=${() => void this.start(true)} ?disabled=${this.loading}>
              ${this.t("learn.continueNow")}
            </button>
          ` : nothing}
          <button @click=${() => void this.start()} ?disabled=${this.loading}>
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
        <p class="muted">${this.t("learn.waitingExplain")}</p>
        <button class="primary" @click=${this.continueCurrentEarly} ?disabled=${this.loading}>
          ${this.t("learn.continueNow")}
        </button>
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
        ${this.renderSecondaryActions(question, true)}
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

  private renderSecondaryActions(question: SessionQuestion, allowKnownAlready = false) {
    return html`
      <div class="secondary-actions">
        ${allowKnownAlready
          ? html`<button
              @click=${() => void this.markKnownAlready(question)}
              ?disabled=${this.loading}
            >
              ${this.t("learn.knownAlready")}
            </button>`
          : nothing}
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

  private renderBlock(block: Parameters<typeof renderContentBlock>[0], primary: boolean) {
    return renderContentBlock(block, primary);
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
