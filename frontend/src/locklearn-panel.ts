import { LitElement, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("locklearn-panel")
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

declare global {
  interface HTMLElementTagNameMap {
    "locklearn-panel": LockLearnPanel;
  }
}
