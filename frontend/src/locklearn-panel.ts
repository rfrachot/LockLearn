import { LitElement, css, html } from "lit";
import { property } from "lit/decorators.js";

export class LockLearnPanel extends LitElement {
  @property({ attribute: false }) hass: unknown;

  static styles = css`
    :host {
      display: block;
      padding: 24px;
      color: var(--primary-text-color);
      background: var(--primary-background-color);
      min-height: 100%;
      box-sizing: border-box;
    }

    main {
      max-width: 960px;
      margin: 0 auto;
    }
  `;

  protected render() {
    return html`
      <main>
        <h1>LockLearn</h1>
        <p>P0 bootstrap panel. Product behavior is defined in SPEC_V1.md.</p>
      </main>
    `;
  }
}

// HA can retain the previous module across integration reloads. A different
// module URL cache-busts releases, but the browser still forbids redefining an
// existing custom element; a full browser reload is required for an upgrade.
if (!customElements.get("locklearn-panel")) {
  customElements.define("locklearn-panel", LockLearnPanel);
}

declare global {
  interface HTMLElementTagNameMap {
    "locklearn-panel": LockLearnPanel;
  }
}
