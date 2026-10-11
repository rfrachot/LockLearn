import { LitElement, css, html, nothing } from "lit";
import { property, state } from "lit/decorators.js";

import type {
  DashboardResponse,
  ExamAttemptSummary,
  ExamResult,
  HomeAssistantLike,
  SessionState,
  VisibleProfile,
} from "./protocol";
import {
  answerExam,
  finishExam,
  getExamHistory,
  getExamResult,
  getSession,
  setExamPaused,
  startExam,
} from "./protocol";

export class LockLearnExamView extends LitElement {
  @property({ attribute: false }) hass?: HomeAssistantLike;
  @property({ attribute: false }) profile?: VisibleProfile;
  @property({ attribute: false }) dashboard?: DashboardResponse;

  @state() private trackId = "";
  @state() private count = 20;
  @state() private contentTypes: string[] = [];
  @state() private direction: "any" | "forward" | "reverse" = "any";
  @state() private packId = "";
  @state() private level = "";
  @state() private tags = "";
  @state() private shuffle = true;
  @state() private optionCount = 4;
  @state() private session?: SessionState;
  @state() private result?: ExamResult;
  @state() private history: ExamAttemptSummary[] = [];
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
    fieldset { display: grid; gap: 6px; border: 1px solid var(--divider-color); border-radius: 8px; }
    fieldset label { display: block; }
    .history { font-size: .95rem; }
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
      this.history = [];
      if (this.hass && this.profile) void this.loadHistory(this.profile.profile_id);
    }
    if (changes.has("dashboard") && !this.trackId) {
      this.trackId = this.dashboard?.tracks[0]?.track_id ?? "";
    }
  }

  private async loadHistory(profileId: string): Promise<void> {
    try {
      const response = await getExamHistory(this.hass!, profileId);
      if (this.profile?.profile_id === profileId) this.history = response.items;
    } catch {
      // History is supplementary; the active/resumable session remains usable.
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
      this.session = await startExam(this.hass, this.profile.profile_id, this.trackId, {
        requestedCards: this.count,
        contentTypes: this.contentTypes.length ? this.contentTypes : undefined,
        direction: this.direction,
        packId: this.packId.trim() || undefined,
        levels: this.level.trim() ? [this.level.trim()] : undefined,
        tags: this.tags.split(",").map(tag => tag.trim()).filter(Boolean),
        shuffle: this.shuffle,
        optionCount: this.optionCount,
      });
      this.result = undefined;
      await this.loadHistory(this.profile.profile_id);
    });
  }

  private pause(): void {
    void this.perform(async () => {
      if (!this.hass || !this.session || this.session.status !== "active") return;
      this.session = await setExamPaused(this.hass, this.session, true);
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

  private resumePaused(): void {
    void this.perform(async () => {
      if (!this.hass || !this.session || this.session.status !== "paused") return;
      this.session = await this.hass.callWS<SessionState>({
        type: "locklearn/session/pause",
        session_id: this.session.id,
        expected_version: this.session.version,
        paused: false,
      });
    });
  }

  private openHistory(attempt: ExamAttemptSummary): void {
    void this.perform(async () => {
      if (!this.hass) return;
      const session = await getSession(this.hass, attempt.attempt_id);
      this.session = session;
      this.result = attempt.status === "completed"
        ? await getExamResult(this.hass, attempt.attempt_id)
        : undefined;
      if (session.track_id) this.trackId = session.track_id;
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
      await this.loadHistory(this.profile?.profile_id ?? "");
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
        <fieldset>
          <legend>${this.fr ? "Types de contenu" : "Content types"}</legend>
          ${["vocabulary", "kanji", "grammar", "expression", "sentence"].map(type => html`
            <label><input type="checkbox" .checked=${this.contentTypes.includes(type)}
              @change=${(e: Event) => {
                const checked = (e.target as HTMLInputElement).checked;
                this.contentTypes = checked
                  ? [...this.contentTypes, type]
                  : this.contentTypes.filter(value => value !== type);
              }} /> ${type}</label>
          `)}
        </fieldset>
        <label>${this.fr ? "Direction" : "Direction"}
          <select .value=${this.direction} @change=${(e: Event) => {
            this.direction = (e.target as HTMLSelectElement).value as typeof this.direction;
          }}>
            <option value="any">${this.fr ? "Les deux" : "Any"}</option>
            <option value="forward">${this.fr ? "Source → cible" : "Source → target"}</option>
            <option value="reverse">${this.fr ? "Cible → source" : "Target → source"}</option>
          </select>
        </label>
        <label>${this.fr ? "Pack (identifiant, optionnel)" : "Pack (optional id)"}
          <input .value=${this.packId} @input=${(e: Event) => {
            this.packId = (e.target as HTMLInputElement).value;
          }} />
        </label>
        <label>${this.fr ? "Niveau (tag level, optionnel)" : "Level (optional level tag)"}
          <input .value=${this.level} @input=${(e: Event) => {
            this.level = (e.target as HTMLInputElement).value;
          }} />
        </label>
        <label>${this.fr ? "Tags (séparés par des virgules)" : "Tags (comma-separated)"}
          <input .value=${this.tags} @input=${(e: Event) => {
            this.tags = (e.target as HTMLInputElement).value;
          }} />
        </label>
        <label><input type="checkbox" .checked=${this.shuffle}
          @change=${(e: Event) => { this.shuffle = (e.target as HTMLInputElement).checked; }} />
          ${this.fr ? "Mélanger les questions" : "Shuffle questions"}</label>
        <label>${this.fr ? "Nombre d'options par QCM" : "Options per MCQ"}
          <select .value=${String(this.optionCount)} @change=${(e: Event) => {
            this.optionCount = Number((e.target as HTMLSelectElement).value);
          }}>
            ${[2, 3, 4, 5, 6].map(n => html`<option value=${n}>${n}</option>`)}
          </select>
        </label>
        ${this.profile.role === "viewer" ? nothing : html`
          <button @click=${this.begin} ?disabled=${this.busy || !this.trackId}>${this.fr ? "Commencer l'examen" : "Start exam"}</button>
        `}
        ${resumable ? html`<button @click=${this.resume} ?disabled=${this.busy}>${this.fr ? "Reprendre / consulter" : "Resume / review"}</button>` : nothing}
        ${this.history.length ? html`
          <h2>${this.fr ? "Examens précédents" : "Previous exams"}</h2>
          ${this.history.map(attempt => html`<button class="history" @click=${() => this.openHistory(attempt)}>
            ${new Date(attempt.started_at_utc).toLocaleString()} —
            ${attempt.status === "completed" ? `${attempt.correct_count}/${attempt.question_count}` : attempt.status}
          </button>`)}
        ` : nothing}
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
      ` : this.session.status === "paused" ? html`
        <p>${this.fr ? "Examen en pause." : "Exam paused."}</p>
        <button @click=${this.resumePaused} ?disabled=${this.busy}>${this.fr ? "Reprendre" : "Resume"}</button>
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
        <button @click=${this.pause} ?disabled=${this.busy}>${this.fr ? "Mettre en pause" : "Pause exam"}</button>
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
