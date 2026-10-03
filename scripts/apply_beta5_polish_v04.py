from __future__ import annotations

from pathlib import Path


def replace(path: str, old: str, new: str, *, count: int = 1) -> None:
    p = Path(path)
    text = p.read_text()
    actual = text.count(old)
    if actual < count:
        raise SystemExit(f"{path}: expected >= {count} matches, found {actual}: {old[:80]!r}")
    text = text.replace(old, new, count)
    p.write_text(text)


# Protocol: route new session traffic through the additive v0.4 endpoints and
# expose exact calibration follow-up operations.
replace(
    "frontend/src/protocol.ts",
    'type: "locklearn/session/start",\n    profile_id: profileId,\n    track_id: trackId,\n    session_type: "quiz",',
    'type: "locklearn/session/start_v04",\n    profile_id: profileId,\n    track_id: trackId,\n    session_type: "quiz",',
)
replace(
    "frontend/src/protocol.ts",
    'type: "locklearn/session/start",\n    profile_id: profileId,\n    track_id: trackId,\n    session_type: "calibration",',
    'type: "locklearn/session/start_v04",\n    profile_id: profileId,\n    track_id: trackId,\n    session_type: "calibration",',
)
replace(
    "frontend/src/protocol.ts",
    'type: "locklearn/quiz/answer",',
    'type: "locklearn/quiz/answer_v04",',
)
replace(
    "frontend/src/protocol.ts",
    'type: "locklearn/session/start",\n    profile_id: profileId,\n    track_id: trackId,\n    session_type: "learn",',
    'type: "locklearn/session/start_v04",\n    profile_id: profileId,\n    track_id: trackId,\n    session_type: "learn",',
)
replace(
    "frontend/src/protocol.ts",
    'type: "locklearn/session/answer",',
    'type: "locklearn/session/answer_v04",',
)
marker = "export async function getSession(\n"
addition = '''export interface CalibrationFollowupStatus {\n  source_session_id: string | null;\n  pending_count: number;\n  card_keys: string[];\n}\n\nexport async function getCalibrationFollowupStatus(\n  hass: HomeAssistantLike,\n  profileId: string,\n  trackId: string,\n  calibrationSessionId?: string,\n): Promise<CalibrationFollowupStatus> {\n  return hass.callWS<CalibrationFollowupStatus>({\n    type: "locklearn/calibration/followup/status",\n    profile_id: profileId,\n    track_id: trackId,\n    ...(calibrationSessionId === undefined ? {} : { calibration_session_id: calibrationSessionId }),\n  });\n}\n\nexport async function startCalibrationFollowup(\n  hass: HomeAssistantLike,\n  profileId: string,\n  trackId: string,\n  calibrationSessionId: string,\n): Promise<SessionState> {\n  return hass.callWS<SessionState>({\n    type: "locklearn/calibration/followup/start",\n    profile_id: profileId,\n    track_id: trackId,\n    calibration_session_id: calibrationSessionId,\n  });\n}\n\n'''
replace("frontend/src/protocol.ts", marker, addition + marker)

# Existing copy: remove false multi-client attribution and improve action text.
for path in ("frontend/src/i18n.ts",):
    replace(path, '"learn.reloaded": "The session changed on another client. The latest state was reloaded."', '"learn.reloaded": "The session was refreshed. The latest recorded state was reloaded."')
    replace(path, '"quiz.reloaded": "The quiz changed on another client. The latest state was reloaded."', '"quiz.reloaded": "The quiz was refreshed. The latest recorded state was reloaded."')
    replace(path, '"learn.reloaded": "La session a changé sur un autre client. Le dernier état a été rechargé."', '"learn.reloaded": "La session a été actualisée. Le dernier état enregistré a été rechargé."')
    replace(path, '"quiz.reloaded": "Le quiz a changé sur un autre client. Le dernier état a été rechargé."', '"quiz.reloaded": "Le quiz a été actualisé. Le dernier état enregistré a été rechargé."')
    replace(path, '"cards.learnInstead": "Learn it instead"', '"cards.learnInstead": "Return to learning"')
    replace(path, '"cards.learnInstead": "Apprendre finalement"', '"cards.learnInstead": "Remettre à apprendre"')
    replace(path, '"learn.cardsReady": "cards available now"', '"learn.cardsReady": "cards ready to learn"')
    replace(path, '"learn.cardsReady": "cartes disponibles maintenant"', '"learn.cardsReady": "cartes prêtes à apprendre"')
    replace(path, '"quiz.cardsReady": "cards ready now"', '"quiz.cardsReady": "cards ready for quiz"')
    replace(path, '"quiz.cardsReady": "cartes disponibles maintenant"', '"quiz.cardsReady": "cartes prêtes pour un quiz"')

# Learn v0.4 behavior.
replace(
    "frontend/src/learn-view.ts",
    "  getReadyReminderStatus,\n  getSession,",
    "  getReadyReminderStatus,\n  getCalibrationFollowupStatus,\n  getSession,",
)
replace(
    "frontend/src/learn-view.ts",
    "  startCalibrationSession,\n  startLearnSession,",
    "  startCalibrationFollowup,\n  startCalibrationSession,\n  startLearnSession,",
)
replace(
    "frontend/src/learn-view.ts",
    "  type ConcernedCardsFilter,\n  type DashboardResponse,",
    "  type CalibrationFollowupStatus,\n  type ConcernedCardsFilter,\n  type DashboardResponse,",
)
replace(
    "frontend/src/learn-view.ts",
    "  @state() private knownBulkGuardVisible = false;",
    "  @state() private knownBulkGuardVisible = false;\n  @state() private calibrationFollowup?: CalibrationFollowupStatus;",
)
replace(
    "frontend/src/learn-view.ts",
    "      this.hasNotificationTarget = (\n        await listNotificationTargets(this.hass, this.profile.profile_id)\n      ).some((target) => target.enabled);",
    "      this.hasNotificationTarget = (\n        await listNotificationTargets(this.hass, this.profile.profile_id)\n      ).some((target) => target.enabled);\n      this.calibrationFollowup = await getCalibrationFollowupStatus(\n        this.hass,\n        this.profile.profile_id,\n        this.trackId,\n      );",
)
replace(
    "frontend/src/learn-view.ts",
    "      this.availability = undefined;\n      this.readyAlternative = undefined;",
    "      this.availability = undefined;\n      this.readyAlternative = undefined;\n      this.calibrationFollowup = undefined;",
)
replace(
    "frontend/src/learn-view.ts",
    "        ${this.session === undefined && this.calibrationSetup",
    "        ${this.calibrationSetup",
)
replace(
    "frontend/src/learn-view.ts",
    "  private async markKnownAlready(question: SessionQuestion): Promise<void> {\n    this.lastKnownCardKey = question.card_key;\n    await this.learningAction(\"known_already\");\n    this.maybeShowKnownBulkGuard();",
    "  private async markKnownAlready(question: SessionQuestion): Promise<void> {\n    this.lastKnownCardKey = question.card_key;\n    const applied = await this.learningAction(\"known_already\");\n    if (!applied) {\n      this.lastKnownCardKey = undefined;\n      return;\n    }\n    this.maybeShowKnownBulkGuard();",
)
replace(
    "frontend/src/learn-view.ts",
    "  ): Promise<void> {\n    const question = this.session?.current_question;",
    "  ): Promise<boolean> {\n    const question = this.session?.current_question;",
)
replace(
    "frontend/src/learn-view.ts",
    "    if (this.hass === undefined || this.session === undefined || question === null || question === undefined) return;",
    "    if (this.hass === undefined || this.session === undefined || question === null || question === undefined) return false;",
)
replace(
    "frontend/src/learn-view.ts",
    "      this.applySession(await this.finalizeIfDone(answered));\n      await this.refreshAvailability();\n    } catch (error) {\n      await this.recover(error);\n    } finally {",
    "      this.applySession(await this.finalizeIfDone(answered));\n      await this.refreshAvailability();\n      return true;\n    } catch (error) {\n      await this.recover(error);\n      return false;\n    } finally {",
)
# Targeted follow-up action.
insert_at = "  private blockerFilter(code: string): ConcernedCardsFilter {\n"
follow_method = '''  private async startCalibrationFollowup(): Promise<void> {\n    if (\n      this.hass === undefined ||\n      this.profile === undefined ||\n      this.calibrationFollowup?.source_session_id === null ||\n      this.calibrationFollowup?.source_session_id === undefined\n    ) return;\n    this.loading = true;\n    this.errorMessage = "";\n    try {\n      const session = await startCalibrationFollowup(\n        this.hass,\n        this.profile.profile_id,\n        this.trackId,\n        this.calibrationFollowup.source_session_id,\n      );\n      this.applySession(session);\n      await this.refreshAvailability();\n    } catch (error) {\n      this.errorMessage = error instanceof Error ? error.message : String(error);\n    } finally {\n      this.loading = false;\n    }\n  }\n\n  private blockerTitle(code: string): string {\n    const fr = this.locale() === "fr";\n    const labels: Record<string, [string, string]> = {\n      scheduled_step: ["Next scheduled recall", "Prochain rappel planifié"],\n      known_already_verification: ["Already-known cards to verify", "Cartes déjà connues à vérifier"],\n      new_quota: ["New-card limit reached", "Limite de nouvelles cartes atteinte"],\n      sibling_gap: ["Similar cards are spaced", "Cartes similaires espacées"],\n      confusable_gap: ["Similar cards are spaced", "Cartes similaires espacées"],\n      buried: ["Cards temporarily set aside", "Cartes mises de côté temporairement"],\n      prerequisite: ["Prerequisites first", "Prérequis à apprendre d’abord"],\n      suspended: ["Suspended cards", "Cartes suspendues"],\n    };\n    const pair = labels[code] ?? ["Unavailable for now", "Indisponible pour le moment"];\n    return pair[fr ? 1 : 0];\n  }\n\n  private blockerBody(code: string, count: number): string {\n    const fr = this.locale() === "fr";\n    if (code === "scheduled_step") return fr ? `${count} carte(s) attendent leur prochaine étape d’apprentissage.` : `${count} card(s) are waiting for their next learning step.`;\n    if (code === "known_already_verification") return fr ? `${count} carte(s) marquées comme déjà connues seront vérifiées plus tard.` : `${count} already-known card(s) will be verified later.`;\n    if (code === "new_quota") return fr ? `${count} carte(s) attendent le prochain quota de nouvelles cartes.` : `${count} card(s) are waiting for the next new-card quota.`;\n    if (code === "sibling_gap" || code === "confusable_gap") return fr ? `${count} carte(s) similaires sont espacées pour limiter les confusions.` : `${count} similar card(s) are spaced to reduce confusion.`;\n    if (code === "prerequisite") return fr ? `${count} carte(s) attendent un prérequis.` : `${count} card(s) are waiting for a prerequisite.`;\n    if (code === "suspended") return fr ? `${count} carte(s) sont suspendues.` : `${count} card(s) are suspended.`;\n    if (code === "buried") return fr ? `${count} carte(s) sont temporairement mises de côté.` : `${count} card(s) are temporarily set aside.`;\n    return fr ? `${count} carte(s) ne sont pas disponibles pour le moment.` : `${count} card(s) are not available yet.`;\n  }\n\n'''
replace("frontend/src/learn-view.ts", insert_at, follow_method + insert_at)
# No-dead-end action: targeted follow-up first and calibration suppressed while pending.
replace(
    "frontend/src/learn-view.ts",
    "        ${availability.new_cards > 0\n          ? html`<button @click=${this.openCalibrationSetup} ?disabled=${this.loading}>\n              ${this.t(\"learn.quickCalibration\")}\n            </button>`\n          : nothing}",
    "        ${(this.calibrationFollowup?.pending_count ?? 0) > 0\n          ? html`<button class=\"primary\" @click=${() => void this.startCalibrationFollowup()} ?disabled=${this.loading}>\n              ${this.locale() === \"fr\" ? \"Apprendre les cartes identifiées par la calibration\" : \"Learn the cards identified by calibration\"}\n            </button>`\n          : availability.new_cards > 0\n            ? html`<button @click=${this.openCalibrationSetup} ?disabled=${this.loading}>\n                ${this.t(\"learn.quickCalibration\")}\n              </button>`\n            : nothing}",
)
replace(
    "frontend/src/learn-view.ts",
    "                  <dt>${blocker.code}</dt>\n                  <dd>\n                    ${blocker.count}",
    "                  <dt>${this.blockerTitle(blocker.code)}</dt>\n                  <dd>\n                    ${this.blockerBody(blocker.code, blocker.count)}",
)
# Intro CTA and mental-answer instruction.
replace(
    "frontend/src/learn-view.ts",
    '${this.t("learn.continue")}\n          </button>\n        </div>\n        ${this.renderSecondaryActions(question, true)}',
    '${question.position + 1 < (this.session?.question_count ?? 0)\n              ? (this.locale() === "fr" ? "Passer à la carte suivante" : "Go to the next card")\n              : (this.locale() === "fr" ? "Continuer la session" : "Continue the session")}\n          </button>\n        </div>\n        ${this.renderSecondaryActions(question, true)}',
)
replace(
    "frontend/src/learn-view.ts",
    "        <div class=\"actions\">\n          ${!this.revealed",
    "        ${!this.revealed\n          ? html`<p class=\"muted\">${this.locale() === \"fr\" ? \"Répondez mentalement, puis révélez la réponse pour vous évaluer.\" : \"Answer mentally, then reveal the answer to evaluate yourself.\"}</p>`\n          : nothing}\n        <div class=\"actions\">\n          ${!this.revealed",
)
replace(
    "frontend/src/learn-view.ts",
    '${this.t("learn.continue")}\n                </button>`\n              : html`',
    '${this.locale() === "fr" ? "Continuer la session" : "Continue the session"}\n                </button>`\n              : html`',
)
# Availability wording when a resumable session exists.
replace(
    "frontend/src/learn-view.ts",
    "? html`<div>${this.availability.available_now} ${this.t(\"learn.cardsReady\")}</div>`",
    "? html`<div>${this.availability.available_now} ${resumable\n                  ? (this.locale() === \"fr\" ? \"autre(s) carte(s) prêtes après la session en cours\" : \"other card(s) ready after the current session\")\n                  : this.t(\"learn.cardsReady\")}</div>`",
)
# Pass Profile timezone to concerned cards.
replace(
    "frontend/src/learn-view.ts",
    ".language=${this.locale()}\n              @locklearn-concerned-cards-close",
    ".language=${this.locale()}\n              .timeZone=${this.profile.timezone}\n              @locklearn-concerned-cards-close",
)

# Quiz: targeted calibration follow-up, geometry and availability grouping/timezone.
replace(
    "frontend/src/quiz-view.ts",
    "  startLearnSession,\n  startQuizSession,",
    "  startCalibrationFollowup,\n  startLearnSession,\n  startQuizSession,",
)
replace(
    "frontend/src/quiz-view.ts",
    "      const session = await startLearnSession(\n        this.hass,\n        this.profile.profile_id,\n        this.session.track_id,\n      );",
    "      const session = await startCalibrationFollowup(\n        this.hass,\n        this.profile.profile_id,\n        this.session.track_id,\n        this.session.id,\n      );",
)
replace(
    "frontend/src/quiz-view.ts",
    "    .prompt {\n      overflow-wrap: anywhere;",
    "    .prompt {\n      min-height: 110px;\n      display: grid;\n      place-items: center;\n      overflow-wrap: anywhere;",
)
replace(
    "frontend/src/quiz-view.ts",
    "    .options {\n      display: grid;",
    "    .options {\n      min-height: 190px;\n      align-content: start;\n      display: grid;",
)
replace(
    "frontend/src/quiz-view.ts",
    "    .free-text-form {\n      display: grid;",
    "    .free-text-form {\n      min-height: 190px;\n      align-content: start;\n      display: grid;",
)
replace(
    "frontend/src/quiz-view.ts",
    "    .feedback-title {",
    "    .feedback {\n      min-height: 190px;\n      align-content: start;\n    }\n\n    .availability-card {\n      display: grid;\n      gap: 16px;\n    }\n\n    .availability-actions {\n      display: flex;\n      flex-wrap: wrap;\n      gap: 10px;\n      padding-top: 4px;\n    }\n\n    .feedback-title {",
)
replace(
    "frontend/src/quiz-view.ts",
    "      .progress {\n        flex-direction: column;",
    "      .prompt { min-height: 80px; }\n      .options, .free-text-form, .feedback { min-height: 150px; }\n\n      .progress {\n        flex-direction: column;",
)
replace(
    "frontend/src/quiz-view.ts",
    '<div class="notice" role="status">\n            <strong>${this.t("quiz.howItWorks")}</strong>',
    '<div class="notice availability-card" role="status">\n            <strong>${this.t("quiz.howItWorks")}</strong>',
)
# Wrap trailing availability buttons in a spaced group.
replace(
    "frontend/src/quiz-view.ts",
    "            ${this.availability.blockers.length > 0\n              ? html`<button",
    "            <div class=\"availability-actions\">\n            ${this.availability.blockers.length > 0\n              ? html`<button",
)
replace(
    "frontend/src/quiz-view.ts",
    "            ${this.renderReminderButton()}\n          </div>\n        ` : nothing}",
    "            ${this.renderReminderButton()}\n            </div>\n          </div>\n        ` : nothing}",
)
replace(
    "frontend/src/quiz-view.ts",
    ".language=${this.locale()}\n              @locklearn-concerned-cards-close",
    ".language=${this.locale()}\n              .timeZone=${this.profile.timezone}\n              @locklearn-concerned-cards-close",
)

# Concerned-cards sheet: contextual user-facing copy, locale/timezone and help.
replace(
    "frontend/src/concerned-cards.ts",
    "      .sheet {\n        position: absolute;\n        inset-inline: 0;",
    "      .sheet {\n        position: absolute;\n        left: 50%;\n        transform: translateX(-50%);\n        width: min(960px, calc(100% - 24px));",
)
replace(
    "frontend/src/concerned-cards.ts",
    "  @property() language: UiLanguage = \"en\";",
    "  @property() language: UiLanguage = \"en\";\n  @property() timeZone = \"UTC\";",
)
insert = "  private async refresh(): Promise<void> {\n"
methods = '''  private filterCopy(): { title: string; body: string } {\n    const fr = this.language === "fr";\n    const copy: Record<ConcernedCardsFilter, { en: [string, string]; fr: [string, string] }> = {\n      known_pending: { en: ["Already-known cards to verify", "These cards were marked as already known and will be verified later."], fr: ["Cartes déjà connues à vérifier", "Ces cartes ont été marquées comme déjà connues et seront vérifiées plus tard."] },\n      suspended: { en: ["Suspended cards", "These cards are excluded until you reactivate them."], fr: ["Cartes suspendues", "Ces cartes restent exclues tant que vous ne les réactivez pas."] },\n      buried: { en: ["Cards temporarily set aside", "These cards are temporarily hidden from normal sessions."], fr: ["Cartes mises de côté temporairement", "Ces cartes sont temporairement retirées des sessions normales."] },\n      prerequisite_support: { en: ["Prerequisites to learn first", "These prerequisite cards currently block other material."], fr: ["Prérequis à apprendre d’abord", "Ces cartes prérequises bloquent actuellement d’autres contenus."] },\n      current_waiting_context: { en: ["Cards currently waiting", "These cards explain why the current mode is not ready yet."], fr: ["Cartes actuellement en attente", "Ces cartes expliquent pourquoi ce mode n’est pas encore disponible."] },\n    };\n    const selected = copy[this.filter];\n    const pair = selected[fr ? "fr" : "en"];\n    return { title: pair[0], body: pair[1] };\n  }\n\n  private stateLabel(state: string): string {\n    const fr = this.language === "fr";\n    const labels: Record<string, [string, string]> = {\n      known_already: ["Marked as already known", "Marquée comme déjà connue"],\n      suspended: ["Suspended", "Suspendue"],\n      buried: ["Temporarily set aside", "Mise de côté temporairement"],\n      active: ["Active", "Active"],\n      new: ["Not learned yet", "Pas encore apprise"],\n      learning: ["Learning", "En apprentissage"],\n      review: ["Review", "En révision"],\n      relearning: ["Relearning", "En réapprentissage"],\n    };\n    const pair = labels[state] ?? ["Waiting", "En attente"];\n    return pair[fr ? 1 : 0];\n  }\n\n  private horizonLabel(value: string): string {\n    const date = new Date(value);\n    if (Number.isNaN(date.getTime())) return "";\n    return new Intl.DateTimeFormat(this.language, {\n      dateStyle: "medium",\n      timeStyle: "short",\n      timeZone: this.timeZone,\n    }).format(date);\n  }\n\n'''
replace("frontend/src/concerned-cards.ts", insert, methods + insert)
replace(
    "frontend/src/concerned-cards.ts",
    "          ${card.user_state}\n          ${card.horizon_utc === null ? nothing : html` · ${new Date(card.horizon_utc).toLocaleString()}`}",
    "          ${this.stateLabel(card.user_state)}\n          ${card.horizon_utc === null ? nothing : html` · ${this.horizonLabel(card.horizon_utc)}`}",
)
replace(
    "frontend/src/concerned-cards.ts",
    "                </button>\n              </div>",
    "                </button>\n                ${card.action === \"learn_instead\"\n                  ? html`<span class=\"meta\">${this.language === \"fr\"\n                      ? \"Annule le marquage « déjà connue » et remet cette carte dans l’apprentissage normal.\"\n                      : \"Cancels the already-known mark and returns this card to normal learning.\"}</span>`\n                  : card.action === \"reactivate\"\n                    ? html`<span class=\"meta\">${this.language === \"fr\" ? \"Remet cette carte dans les sessions normales.\" : \"Returns this card to normal sessions.\"}</span>`\n                    : nothing}\n              </div>",
)
replace(
    "frontend/src/concerned-cards.ts",
    '<h2 id="concerned-title">${this.tr("cards.concernedTitle")}</h2>',
    '<h2 id="concerned-title">${this.filterCopy().title}</h2>',
)
replace(
    "frontend/src/concerned-cards.ts",
    "        </header>\n        ${this.loading",
    "        </header>\n        <p class=\"meta\">${this.filterCopy().body}</p>\n        ${this.loading",
)

# User-visible changelog note.
replace(
    "CHANGELOG.md",
    "### Added\n",
    "### Added\n- Add beta.5 field-polish follow-up: exact calibration remediation sessions, replay-safe resume reconciliation, deterministic per-session ordering variation, blocker copy and final Learn/Quiz UI polish.\n",
)

print("beta5 field-polish transforms applied")
