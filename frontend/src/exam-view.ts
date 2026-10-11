import { LitElement, css, html, nothing } from "lit";
import { property, state } from "lit/decorators.js";

import type { DashboardResponse, HomeAssistantLike, SessionState, VisibleProfile, ExamResult } from "./protocol";
import { answerExam, finishExam, getExamResult, getSession, startExam } from "./protocol";

export class LockLearnExamView extends LitElement {
  @property({ attribute: false }) hass?: HomeAssistantLike;
  @property({ attribute: false }) profile?: VisibleProfile;
  @property({ attribute: false }) dashboard?: DashboardResponse;

  @state() private trackId = "";
  @state() private count = 20;
  @state() private session?: SessionState;
  @state() private result?: ExamResult;
  @state() private busy = false;
  @state() private error = "";

  static styles = css`
    :host { display: block; color: var(--primary-text-color); }
    section { display: grid; gap: 16px; padding: clamp(16px, 4vw, 28px);
      background: var(--card-background-color, var(--primary-background-color));
      border-radius: 14px; max-width: 760px; margin-inline: auto; }
    button, select, input { font: inherit; min-height: 44px; padding: 8px 12px;
      border: 1px solid var(--divider-color); border-radius: 8px;
      color: var(--primary-text-color); background: var(--secondary-background-color); }
    button { text-align: left; cursor: pointer; }
    button:disabled { opacity: .55; cursor: default; }
    .choices { display: grid; gap: 10px; }
    label { display: grid; gap: 6px; }
    .prompt { font-size: clamp(1.4rem, 4vw, 2rem); text-align: center; padding: 22px 8px; }
    .muted { color: var(--secondary-text-color); }
    .error { color: var(--error-color); }
    .weak { border-inline-start: 3px solid var(--warning-color); padding-inline: 12px; }
  `;

  protected updated(changes: Map<PropertyKey, unknown>): void {
    if (changes.has("profile")) {
      this.session = undefined;
      this.result = undefined;
      this.trackId = this.dashboard?.tracks[0]?.track_id ?? "";
    }
    if (changes.has("dashboard") && !this.trackId) {
      this.trackId = this.dashboard?.tracks[0]?.track_id ?? "";
    }
  }

  private get fr(): boolean {
    const lang = this.hass?.locale?.language ?? this.hass?.language ?? "en";
    return lang.toLowerCase().startsWith("fr");
  }

  private async perform(operation: () => Promise<void>): Promise<void> {
    if (this.busy) return;
    this.busy = true;
    this.error = "";
    try { await operation(); }
    catch (err) { this.error = err instanceof Error ? err.message : String(err); }
    finally { this.busy = false; }
  }

  private begin(): void {
    void this.perform(async () => {
      if (!this.hass || !this.profile || !this.trackId) return;
      this.session = await startExam(this.hass, this.profile.profile_id, this.trackId, this.count);
      this.result = undefined;
    });
  }

  private resume(): void {
    void this.perform(async () => {
      const last = this.dashboard?.tracks.find(t => t.track_id === this.trackId)?.last_session;
      if (!this.hass || last?.session_type !== "exam") return;
      this.session = await getSession(this.hass, last.session_id);
      if (this.session.status === "completed") {
        this.result = await getExamResult(this.hass, this.session.id);
      }
    });
  }

  private answer(selectedAnswerId: string | null): void {
    void this.perform(async () => {
      if (!this.hass || !this.session?.current_question) return;
      this.session = await answerExam(
        this.hass, this.session, this.session.current_question.question_id, selectedAnswerId,
      );
    });
  }

  private finish(): void {
    void this.perform(async () => {
      if (!this.hass || !this.session) return;
      const response = await finishExam(this.hass, this.session);
      this.session = response.session;
      this.result = response.result;
    });
  }

  protected render() {
    if (!this.profile) return html`<section>${this.fr ? "Aucun profil disponible." : "No profile available."}</section>`;
    const tracks = this.dashboard?.tracks ?? [];
    const last = tracks.find(t => t.track_id === this.trackId)?.last_session;
    const resumable = last?.session_type === "exam" &&
      (last.status === "active" || last.status === "paused" || last.status === "completed");
    const question = this.session?.current_question;
    const quiz = question?.payload.quiz;

    return html`<section>
      <h1>${this.fr ? "Examen" : "Exam"}</h1>
      <p class="muted">${this.fr
        ? "Les réponses sont définitives. Le corrigé et le score apparaissent uniquement à la fin. Aucun changement direct des boxes SRS."
        : "Answers are final. Corrections and score appear only at the end. No direct SRS box promotion."}</p>
      ${!this.session ? html`
        <label>${this.fr ? "Parcours" : "Track"}
          <select .value=${this.trackId} @change=${(e: Event) => { this.trackId = (e.target as HTMLSelectElement).value; }}>
            ${tracks.map(t => html`<option value=${t.track_id}>${t.name}</option>`)}
          </select>
        </label>
        <label>${this.fr ? "Nombre de questions" : "Number of questions"}
          <select .value=${String(this.count)} @change=${(e: Event) => { this.count = Number((e.target as HTMLSelectElement).value); }}>
            ${[10, 20, 30, 40].map(n => html`<option value=${n}>${n}</option>`)}
          </select>
        </label>
        ${this.profile.role === "viewer" ? nothing : html`
          <button @click=${this.begin} ?disabled=${this.busy || !this.trackId}>${this.fr ? "Commencer l'examen" : "Start exam"}</button>
        `}
        ${resumable ? html`<button @click=${this.resume} ?disabled=${this.busy}>${this.fr ? "Reprendre / consulter" : "Resume / review"}</button>` : nothing}
      ` : this.result ? html`
        <h2>${this.result.correct} / ${this.result.total} — ${this.result.percentage}%</h2>
        <h3>${this.fr ? "Revoir mes erreurs" : "Review mistakes"}</h3>
        ${this.result.questions.filter(q => q.result !== "correct").map(q => html`
          <div class="weak">
            <p><strong>${q.prompt}</strong></p>
            <p>${this.fr ? "Votre réponse" : "Your answer"}: ${q.given ?? (this.fr ? "Je ne sais pas" : "I don't know")}</p>
            <p>${this.fr ? "Bonne réponse" : "Correct answer"}: ${q.correct}</p>
            ${q.context ? html`<p class="muted">${q.context}</p>` : nothing}
          </div>
        `)}
        <button @click=${() => { this.session = undefined; this.result = undefined; }}>${this.fr ? "Retour" : "Back"}</button>
      ` : question && quiz ? html`
        <p>${this.fr ? "Question" : "Question"} ${question.position + 1} / ${this.session.question_count}</p>
        <div class="prompt">${quiz.prompt_text}</div>
        <div class="choices">
          ${quiz.options.map(option => html`<button ?disabled=${this.busy || this.profile?.role === "viewer"}
            @click=${() => this.answer(option.answer_id)}>${option.text}</button>`)}
          <button ?disabled=${this.busy || this.profile?.role === "viewer"}
            @click=${() => this.answer(null)}>${this.fr ? "Je ne sais pas" : "I don't know"}</button>
        </div>
        <p class="muted">${this.fr ? "Pas de correction avant la fin." : "No correction until the end."}</p>
      ` : html`
        <p>${this.fr ? "Toutes les réponses sont enregistrées." : "All answers have been recorded."}</p>
        <button @click=${this.finish} ?disabled=${this.busy || this.session?.status !== "active"}>
          ${this.fr ? "Terminer et voir le score" : "Finish and see score"}
        </button>
      `}
      ${this.error ? html`<p class="error" role="alert">${this.error}</p>` : nothing}
    </section>`;
  }
}

customElements.define("locklearn-exam-view", LockLearnExamView);
