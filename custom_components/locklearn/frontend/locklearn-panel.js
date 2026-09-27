const se = globalThis, ye = se.ShadowRoot && (se.ShadyCSS === void 0 || se.ShadyCSS.nativeShadow) && "adoptedStyleSheets" in Document.prototype && "replace" in CSSStyleSheet.prototype, $e = /* @__PURE__ */ Symbol(), Pe = /* @__PURE__ */ new WeakMap();
let et = class {
  constructor(e, t, i) {
    if (this._$cssResult$ = !0, i !== $e) throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");
    this.cssText = e, this.t = t;
  }
  get styleSheet() {
    let e = this.o;
    const t = this.t;
    if (ye && e === void 0) {
      const i = t !== void 0 && t.length === 1;
      i && (e = Pe.get(t)), e === void 0 && ((this.o = e = new CSSStyleSheet()).replaceSync(this.cssText), i && Pe.set(t, e));
    }
    return e;
  }
  toString() {
    return this.cssText;
  }
};
const gt = (a) => new et(typeof a == "string" ? a : a + "", void 0, $e), M = (a, ...e) => {
  const t = a.length === 1 ? a[0] : e.reduce((i, s, n) => i + ((o) => {
    if (o._$cssResult$ === !0) return o.cssText;
    if (typeof o == "number") return o;
    throw Error("Value passed to 'css' function must be a 'css' function result: " + o + ". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.");
  })(s) + a[n + 1], a[0]);
  return new et(t, a, $e);
}, mt = (a, e) => {
  if (ye) a.adoptedStyleSheets = e.map((t) => t instanceof CSSStyleSheet ? t : t.styleSheet);
  else for (const t of e) {
    const i = document.createElement("style"), s = se.litNonce;
    s !== void 0 && i.setAttribute("nonce", s), i.textContent = t.cssText, a.appendChild(i);
  }
}, Ee = ye ? (a) => a : (a) => a instanceof CSSStyleSheet ? ((e) => {
  let t = "";
  for (const i of e.cssRules) t += i.cssText;
  return gt(t);
})(a) : a;
const { is: ft, defineProperty: vt, getOwnPropertyDescriptor: bt, getOwnPropertyNames: yt, getOwnPropertySymbols: $t, getPrototypeOf: _t } = Object, le = globalThis, Me = le.trustedTypes, kt = Me ? Me.emptyScript : "", wt = le.reactiveElementPolyfillSupport, B = (a, e) => a, ae = { toAttribute(a, e) {
  switch (e) {
    case Boolean:
      a = a ? kt : null;
      break;
    case Object:
    case Array:
      a = a == null ? a : JSON.stringify(a);
  }
  return a;
}, fromAttribute(a, e) {
  let t = a;
  switch (e) {
    case Boolean:
      t = a !== null;
      break;
    case Number:
      t = a === null ? null : Number(a);
      break;
    case Object:
    case Array:
      try {
        t = JSON.parse(a);
      } catch {
        t = null;
      }
  }
  return t;
} }, _e = (a, e) => !ft(a, e), Ce = { attribute: !0, type: String, converter: ae, reflect: !1, useDefault: !1, hasChanged: _e };
Symbol.metadata ??= /* @__PURE__ */ Symbol("metadata"), le.litPropertyMetadata ??= /* @__PURE__ */ new WeakMap();
let U = class extends HTMLElement {
  static addInitializer(e) {
    this._$Ei(), (this.l ??= []).push(e);
  }
  static get observedAttributes() {
    return this.finalize(), this._$Eh && [...this._$Eh.keys()];
  }
  static createProperty(e, t = Ce) {
    if (t.state && (t.attribute = !1), this._$Ei(), this.prototype.hasOwnProperty(e) && ((t = Object.create(t)).wrapped = !0), this.elementProperties.set(e, t), !t.noAccessor) {
      const i = /* @__PURE__ */ Symbol(), s = this.getPropertyDescriptor(e, i, t);
      s !== void 0 && vt(this.prototype, e, s);
    }
  }
  static getPropertyDescriptor(e, t, i) {
    const { get: s, set: n } = bt(this.prototype, e) ?? { get() {
      return this[t];
    }, set(o) {
      this[t] = o;
    } };
    return { get: s, set(o) {
      const d = s?.call(this);
      n?.call(this, o), this.requestUpdate(e, d, i);
    }, configurable: !0, enumerable: !0 };
  }
  static getPropertyOptions(e) {
    return this.elementProperties.get(e) ?? Ce;
  }
  static _$Ei() {
    if (this.hasOwnProperty(B("elementProperties"))) return;
    const e = _t(this);
    e.finalize(), e.l !== void 0 && (this.l = [...e.l]), this.elementProperties = new Map(e.elementProperties);
  }
  static finalize() {
    if (this.hasOwnProperty(B("finalized"))) return;
    if (this.finalized = !0, this._$Ei(), this.hasOwnProperty(B("properties"))) {
      const t = this.properties, i = [...yt(t), ...$t(t)];
      for (const s of i) this.createProperty(s, t[s]);
    }
    const e = this[Symbol.metadata];
    if (e !== null) {
      const t = litPropertyMetadata.get(e);
      if (t !== void 0) for (const [i, s] of t) this.elementProperties.set(i, s);
    }
    this._$Eh = /* @__PURE__ */ new Map();
    for (const [t, i] of this.elementProperties) {
      const s = this._$Eu(t, i);
      s !== void 0 && this._$Eh.set(s, t);
    }
    this.elementStyles = this.finalizeStyles(this.styles);
  }
  static finalizeStyles(e) {
    const t = [];
    if (Array.isArray(e)) {
      const i = new Set(e.flat(1 / 0).reverse());
      for (const s of i) t.unshift(Ee(s));
    } else e !== void 0 && t.push(Ee(e));
    return t;
  }
  static _$Eu(e, t) {
    const i = t.attribute;
    return i === !1 ? void 0 : typeof i == "string" ? i : typeof e == "string" ? e.toLowerCase() : void 0;
  }
  constructor() {
    super(), this._$Ep = void 0, this.isUpdatePending = !1, this.hasUpdated = !1, this._$Em = null, this._$Ev();
  }
  _$Ev() {
    this._$ES = new Promise((e) => this.enableUpdating = e), this._$AL = /* @__PURE__ */ new Map(), this._$E_(), this.requestUpdate(), this.constructor.l?.forEach((e) => e(this));
  }
  addController(e) {
    (this._$EO ??= /* @__PURE__ */ new Set()).add(e), this.renderRoot !== void 0 && this.isConnected && e.hostConnected?.();
  }
  removeController(e) {
    this._$EO?.delete(e);
  }
  _$E_() {
    const e = /* @__PURE__ */ new Map(), t = this.constructor.elementProperties;
    for (const i of t.keys()) this.hasOwnProperty(i) && (e.set(i, this[i]), delete this[i]);
    e.size > 0 && (this._$Ep = e);
  }
  createRenderRoot() {
    const e = this.shadowRoot ?? this.attachShadow(this.constructor.shadowRootOptions);
    return mt(e, this.constructor.elementStyles), e;
  }
  connectedCallback() {
    this.renderRoot ??= this.createRenderRoot(), this.enableUpdating(!0), this._$EO?.forEach((e) => e.hostConnected?.());
  }
  enableUpdating(e) {
  }
  disconnectedCallback() {
    this._$EO?.forEach((e) => e.hostDisconnected?.());
  }
  attributeChangedCallback(e, t, i) {
    this._$AK(e, i);
  }
  _$ET(e, t) {
    const i = this.constructor.elementProperties.get(e), s = this.constructor._$Eu(e, i);
    if (s !== void 0 && i.reflect === !0) {
      const n = (i.converter?.toAttribute !== void 0 ? i.converter : ae).toAttribute(t, i.type);
      this._$Em = e, n == null ? this.removeAttribute(s) : this.setAttribute(s, n), this._$Em = null;
    }
  }
  _$AK(e, t) {
    const i = this.constructor, s = i._$Eh.get(e);
    if (s !== void 0 && this._$Em !== s) {
      const n = i.getPropertyOptions(s), o = typeof n.converter == "function" ? { fromAttribute: n.converter } : n.converter?.fromAttribute !== void 0 ? n.converter : ae;
      this._$Em = s;
      const d = o.fromAttribute(t, n.type);
      this[s] = d ?? this._$Ej?.get(s) ?? d, this._$Em = null;
    }
  }
  requestUpdate(e, t, i, s = !1, n) {
    if (e !== void 0) {
      const o = this.constructor;
      if (s === !1 && (n = this[e]), i ??= o.getPropertyOptions(e), !((i.hasChanged ?? _e)(n, t) || i.useDefault && i.reflect && n === this._$Ej?.get(e) && !this.hasAttribute(o._$Eu(e, i)))) return;
      this.C(e, t, i);
    }
    this.isUpdatePending === !1 && (this._$ES = this._$EP());
  }
  C(e, t, { useDefault: i, reflect: s, wrapped: n }, o) {
    i && !(this._$Ej ??= /* @__PURE__ */ new Map()).has(e) && (this._$Ej.set(e, o ?? t ?? this[e]), n !== !0 || o !== void 0) || (this._$AL.has(e) || (this.hasUpdated || i || (t = void 0), this._$AL.set(e, t)), s === !0 && this._$Em !== e && (this._$Eq ??= /* @__PURE__ */ new Set()).add(e));
  }
  async _$EP() {
    this.isUpdatePending = !0;
    try {
      await this._$ES;
    } catch (t) {
      Promise.reject(t);
    }
    const e = this.scheduleUpdate();
    return e != null && await e, !this.isUpdatePending;
  }
  scheduleUpdate() {
    return this.performUpdate();
  }
  performUpdate() {
    if (!this.isUpdatePending) return;
    if (!this.hasUpdated) {
      if (this.renderRoot ??= this.createRenderRoot(), this._$Ep) {
        for (const [s, n] of this._$Ep) this[s] = n;
        this._$Ep = void 0;
      }
      const i = this.constructor.elementProperties;
      if (i.size > 0) for (const [s, n] of i) {
        const { wrapped: o } = n, d = this[s];
        o !== !0 || this._$AL.has(s) || d === void 0 || this.C(s, void 0, n, d);
      }
    }
    let e = !1;
    const t = this._$AL;
    try {
      e = this.shouldUpdate(t), e ? (this.willUpdate(t), this._$EO?.forEach((i) => i.hostUpdate?.()), this.update(t)) : this._$EM();
    } catch (i) {
      throw e = !1, this._$EM(), i;
    }
    e && this._$AE(t);
  }
  willUpdate(e) {
  }
  _$AE(e) {
    this._$EO?.forEach((t) => t.hostUpdated?.()), this.hasUpdated || (this.hasUpdated = !0, this.firstUpdated(e)), this.updated(e);
  }
  _$EM() {
    this._$AL = /* @__PURE__ */ new Map(), this.isUpdatePending = !1;
  }
  get updateComplete() {
    return this.getUpdateComplete();
  }
  getUpdateComplete() {
    return this._$ES;
  }
  shouldUpdate(e) {
    return !0;
  }
  update(e) {
    this._$Eq &&= this._$Eq.forEach((t) => this._$ET(t, this[t])), this._$EM();
  }
  updated(e) {
  }
  firstUpdated(e) {
  }
};
U.elementStyles = [], U.shadowRootOptions = { mode: "open" }, U[B("elementProperties")] = /* @__PURE__ */ new Map(), U[B("finalized")] = /* @__PURE__ */ new Map(), wt?.({ ReactiveElement: U }), (le.reactiveElementVersions ??= []).push("2.1.2");
const ke = globalThis, Re = (a) => a, re = ke.trustedTypes, De = re ? re.createPolicy("lit-html", { createHTML: (a) => a }) : void 0, tt = "$lit$", E = `lit$${Math.random().toFixed(9).slice(2)}$`, it = "?" + E, xt = `<${it}>`, D = document, K = () => D.createComment(""), Q = (a) => a === null || typeof a != "object" && typeof a != "function", we = Array.isArray, St = (a) => we(a) || typeof a?.[Symbol.iterator] == "function", he = `[ 	
\f\r]`, V = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, Ie = /-->/g, Ne = />/g, C = RegExp(`>|${he}(?:([^\\s"'>=/]+)(${he}*=${he}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`, "g"), Le = /'/g, Ue = /"/g, st = /^(?:script|style|textarea|title)$/i, qt = (a) => (e, ...t) => ({ _$litType$: a, strings: e, values: t }), r = qt(1), O = /* @__PURE__ */ Symbol.for("lit-noChange"), l = /* @__PURE__ */ Symbol.for("lit-nothing"), Oe = /* @__PURE__ */ new WeakMap(), R = D.createTreeWalker(D, 129);
function at(a, e) {
  if (!we(a) || !a.hasOwnProperty("raw")) throw Error("invalid template strings array");
  return De !== void 0 ? De.createHTML(e) : e;
}
const At = (a, e) => {
  const t = a.length - 1, i = [];
  let s, n = e === 2 ? "<svg>" : e === 3 ? "<math>" : "", o = V;
  for (let d = 0; d < t; d++) {
    const h = a[d];
    let u, b, p = -1, z = 0;
    for (; z < h.length && (o.lastIndex = z, b = o.exec(h), b !== null); ) z = o.lastIndex, o === V ? b[1] === "!--" ? o = Ie : b[1] !== void 0 ? o = Ne : b[2] !== void 0 ? (st.test(b[2]) && (s = RegExp("</" + b[2], "g")), o = C) : b[3] !== void 0 && (o = C) : o === C ? b[0] === ">" ? (o = s ?? V, p = -1) : b[1] === void 0 ? p = -2 : (p = o.lastIndex - b[2].length, u = b[1], o = b[3] === void 0 ? C : b[3] === '"' ? Ue : Le) : o === Ue || o === Le ? o = C : o === Ie || o === Ne ? o = V : (o = C, s = void 0);
    const P = o === C && a[d + 1].startsWith("/>") ? " " : "";
    n += o === V ? h + xt : p >= 0 ? (i.push(u), h.slice(0, p) + tt + h.slice(p) + E + P) : h + E + (p === -2 ? d : P);
  }
  return [at(a, n + (a[t] || "<?>") + (e === 2 ? "</svg>" : e === 3 ? "</math>" : "")), i];
};
class G {
  constructor({ strings: e, _$litType$: t }, i) {
    let s;
    this.parts = [];
    let n = 0, o = 0;
    const d = e.length - 1, h = this.parts, [u, b] = At(e, t);
    if (this.el = G.createElement(u, i), R.currentNode = this.el.content, t === 2 || t === 3) {
      const p = this.el.content.firstChild;
      p.replaceWith(...p.childNodes);
    }
    for (; (s = R.nextNode()) !== null && h.length < d; ) {
      if (s.nodeType === 1) {
        if (s.hasAttributes()) for (const p of s.getAttributeNames()) if (p.endsWith(tt)) {
          const z = b[o++], P = s.getAttribute(p).split(E), Y = /([.?@])?(.*)/.exec(z);
          h.push({ type: 1, index: n, name: Y[2], strings: P, ctor: Y[1] === "." ? zt : Y[1] === "?" ? Pt : Y[1] === "@" ? Et : ce }), s.removeAttribute(p);
        } else p.startsWith(E) && (h.push({ type: 6, index: n }), s.removeAttribute(p));
        if (st.test(s.tagName)) {
          const p = s.textContent.split(E), z = p.length - 1;
          if (z > 0) {
            s.textContent = re ? re.emptyScript : "";
            for (let P = 0; P < z; P++) s.append(p[P], K()), R.nextNode(), h.push({ type: 2, index: ++n });
            s.append(p[z], K());
          }
        }
      } else if (s.nodeType === 8) if (s.data === it) h.push({ type: 2, index: n });
      else {
        let p = -1;
        for (; (p = s.data.indexOf(E, p + 1)) !== -1; ) h.push({ type: 7, index: n }), p += E.length - 1;
      }
      n++;
    }
  }
  static createElement(e, t) {
    const i = D.createElement("template");
    return i.innerHTML = e, i;
  }
}
function j(a, e, t = a, i) {
  if (e === O) return e;
  let s = i !== void 0 ? t._$Co?.[i] : t._$Cl;
  const n = Q(e) ? void 0 : e._$litDirective$;
  return s?.constructor !== n && (s?._$AO?.(!1), n === void 0 ? s = void 0 : (s = new n(a), s._$AT(a, t, i)), i !== void 0 ? (t._$Co ??= [])[i] = s : t._$Cl = s), s !== void 0 && (e = j(a, s._$AS(a, e.values), s, i)), e;
}
class Tt {
  constructor(e, t) {
    this._$AV = [], this._$AN = void 0, this._$AD = e, this._$AM = t;
  }
  get parentNode() {
    return this._$AM.parentNode;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  u(e) {
    const { el: { content: t }, parts: i } = this._$AD, s = (e?.creationScope ?? D).importNode(t, !0);
    R.currentNode = s;
    let n = R.nextNode(), o = 0, d = 0, h = i[0];
    for (; h !== void 0; ) {
      if (o === h.index) {
        let u;
        h.type === 2 ? u = new J(n, n.nextSibling, this, e) : h.type === 1 ? u = new h.ctor(n, h.name, h.strings, this, e) : h.type === 6 && (u = new Mt(n, this, e)), this._$AV.push(u), h = i[++d];
      }
      o !== h?.index && (n = R.nextNode(), o++);
    }
    return R.currentNode = D, s;
  }
  p(e) {
    let t = 0;
    for (const i of this._$AV) i !== void 0 && (i.strings !== void 0 ? (i._$AI(e, i, t), t += i.strings.length - 2) : i._$AI(e[t])), t++;
  }
}
class J {
  get _$AU() {
    return this._$AM?._$AU ?? this._$Cv;
  }
  constructor(e, t, i, s) {
    this.type = 2, this._$AH = l, this._$AN = void 0, this._$AA = e, this._$AB = t, this._$AM = i, this.options = s, this._$Cv = s?.isConnected ?? !0;
  }
  get parentNode() {
    let e = this._$AA.parentNode;
    const t = this._$AM;
    return t !== void 0 && e?.nodeType === 11 && (e = t.parentNode), e;
  }
  get startNode() {
    return this._$AA;
  }
  get endNode() {
    return this._$AB;
  }
  _$AI(e, t = this) {
    e = j(this, e, t), Q(e) ? e === l || e == null || e === "" ? (this._$AH !== l && this._$AR(), this._$AH = l) : e !== this._$AH && e !== O && this._(e) : e._$litType$ !== void 0 ? this.$(e) : e.nodeType !== void 0 ? this.T(e) : St(e) ? this.k(e) : this._(e);
  }
  O(e) {
    return this._$AA.parentNode.insertBefore(e, this._$AB);
  }
  T(e) {
    this._$AH !== e && (this._$AR(), this._$AH = this.O(e));
  }
  _(e) {
    this._$AH !== l && Q(this._$AH) ? this._$AA.nextSibling.data = e : this.T(D.createTextNode(e)), this._$AH = e;
  }
  $(e) {
    const { values: t, _$litType$: i } = e, s = typeof i == "number" ? this._$AC(e) : (i.el === void 0 && (i.el = G.createElement(at(i.h, i.h[0]), this.options)), i);
    if (this._$AH?._$AD === s) this._$AH.p(t);
    else {
      const n = new Tt(s, this), o = n.u(this.options);
      n.p(t), this.T(o), this._$AH = n;
    }
  }
  _$AC(e) {
    let t = Oe.get(e.strings);
    return t === void 0 && Oe.set(e.strings, t = new G(e)), t;
  }
  k(e) {
    we(this._$AH) || (this._$AH = [], this._$AR());
    const t = this._$AH;
    let i, s = 0;
    for (const n of e) s === t.length ? t.push(i = new J(this.O(K()), this.O(K()), this, this.options)) : i = t[s], i._$AI(n), s++;
    s < t.length && (this._$AR(i && i._$AB.nextSibling, s), t.length = s);
  }
  _$AR(e = this._$AA.nextSibling, t) {
    for (this._$AP?.(!1, !0, t); e !== this._$AB; ) {
      const i = Re(e).nextSibling;
      Re(e).remove(), e = i;
    }
  }
  setConnected(e) {
    this._$AM === void 0 && (this._$Cv = e, this._$AP?.(e));
  }
}
class ce {
  get tagName() {
    return this.element.tagName;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  constructor(e, t, i, s, n) {
    this.type = 1, this._$AH = l, this._$AN = void 0, this.element = e, this.name = t, this._$AM = s, this.options = n, i.length > 2 || i[0] !== "" || i[1] !== "" ? (this._$AH = Array(i.length - 1).fill(new String()), this.strings = i) : this._$AH = l;
  }
  _$AI(e, t = this, i, s) {
    const n = this.strings;
    let o = !1;
    if (n === void 0) e = j(this, e, t, 0), o = !Q(e) || e !== this._$AH && e !== O, o && (this._$AH = e);
    else {
      const d = e;
      let h, u;
      for (e = n[0], h = 0; h < n.length - 1; h++) u = j(this, d[i + h], t, h), u === O && (u = this._$AH[h]), o ||= !Q(u) || u !== this._$AH[h], u === l ? e = l : e !== l && (e += (u ?? "") + n[h + 1]), this._$AH[h] = u;
    }
    o && !s && this.j(e);
  }
  j(e) {
    e === l ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, e ?? "");
  }
}
class zt extends ce {
  constructor() {
    super(...arguments), this.type = 3;
  }
  j(e) {
    this.element[this.name] = e === l ? void 0 : e;
  }
}
class Pt extends ce {
  constructor() {
    super(...arguments), this.type = 4;
  }
  j(e) {
    this.element.toggleAttribute(this.name, !!e && e !== l);
  }
}
class Et extends ce {
  constructor(e, t, i, s, n) {
    super(e, t, i, s, n), this.type = 5;
  }
  _$AI(e, t = this) {
    if ((e = j(this, e, t, 0) ?? l) === O) return;
    const i = this._$AH, s = e === l && i !== l || e.capture !== i.capture || e.once !== i.once || e.passive !== i.passive, n = e !== l && (i === l || s);
    s && this.element.removeEventListener(this.name, this, i), n && this.element.addEventListener(this.name, this, e), this._$AH = e;
  }
  handleEvent(e) {
    typeof this._$AH == "function" ? this._$AH.call(this.options?.host ?? this.element, e) : this._$AH.handleEvent(e);
  }
}
class Mt {
  constructor(e, t, i) {
    this.element = e, this.type = 6, this._$AN = void 0, this._$AM = t, this.options = i;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AI(e) {
    j(this, e);
  }
}
const Ct = ke.litHtmlPolyfillSupport;
Ct?.(G, J), (ke.litHtmlVersions ??= []).push("3.3.3");
const Rt = (a, e, t) => {
  const i = t?.renderBefore ?? e;
  let s = i._$litPart$;
  if (s === void 0) {
    const n = t?.renderBefore ?? null;
    i._$litPart$ = s = new J(e.insertBefore(K(), n), n, void 0, t ?? {});
  }
  return s._$AI(a), s;
};
const xe = globalThis;
class A extends U {
  constructor() {
    super(...arguments), this.renderOptions = { host: this }, this._$Do = void 0;
  }
  createRenderRoot() {
    const e = super.createRenderRoot();
    return this.renderOptions.renderBefore ??= e.firstChild, e;
  }
  update(e) {
    const t = this.render();
    this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(e), this._$Do = Rt(t, this.renderRoot, this.renderOptions);
  }
  connectedCallback() {
    super.connectedCallback(), this._$Do?.setConnected(!0);
  }
  disconnectedCallback() {
    super.disconnectedCallback(), this._$Do?.setConnected(!1);
  }
  render() {
    return O;
  }
}
A._$litElement$ = !0, A.finalized = !0, xe.litElementHydrateSupport?.({ LitElement: A });
const Dt = xe.litElementPolyfillSupport;
Dt?.({ LitElement: A });
(xe.litElementVersions ??= []).push("4.2.2");
const It = { attribute: !0, type: String, converter: ae, reflect: !1, hasChanged: _e }, Nt = (a = It, e, t) => {
  const { kind: i, metadata: s } = t;
  let n = globalThis.litPropertyMetadata.get(s);
  if (n === void 0 && globalThis.litPropertyMetadata.set(s, n = /* @__PURE__ */ new Map()), i === "setter" && ((a = Object.create(a)).wrapped = !0), n.set(t.name, a), i === "accessor") {
    const { name: o } = t;
    return { set(d) {
      const h = e.get.call(this);
      e.set.call(this, d), this.requestUpdate(o, h, a, !0, d);
    }, init(d) {
      return d !== void 0 && this.C(o, void 0, a, d), d;
    } };
  }
  if (i === "setter") {
    const { name: o } = t;
    return function(d) {
      const h = this[o];
      e.call(this, d), this.requestUpdate(o, h, a, !0, d);
    };
  }
  throw Error("Unsupported decorator location: " + i);
};
function y(a) {
  return (e, t) => typeof t == "object" ? Nt(a, e, t) : ((i, s, n) => {
    const o = s.hasOwnProperty(n);
    return s.constructor.createProperty(n, i), o ? Object.getOwnPropertyDescriptor(s, n) : void 0;
  })(a, e, t);
}
function c(a) {
  return y({ ...a, state: !0, attribute: !1 });
}
const rt = M`
  .content-block {
    min-width: 0;
    max-width: 100%;
    overflow-wrap: anywhere;
    word-break: normal;
    line-height: 1.55;
  }

  .content-block:lang(ja) {
    font-family:
      "Hiragino Sans",
      "Hiragino Kaku Gothic ProN",
      "Yu Gothic",
      "YuGothic",
      "Noto Sans CJK JP",
      "Noto Sans JP",
      Meiryo,
      sans-serif;
    font-size: max(1.125rem, 1em);
    line-height: 1.75;
    text-autospace: normal;
  }

  .content-block ruby {
    ruby-position: over;
    ruby-align: center;
  }

  .content-block rt {
    font-size: 0.55em;
    line-height: 1;
    font-weight: 400;
  }

  .content-block p {
    margin: 0.35em 0;
  }

  .content-block code {
    font-family: ui-monospace, "SFMono-Regular", Consolas, monospace;
    overflow-wrap: anywhere;
  }
`, H = M`
  :where(button, a, input, select, textarea):focus-visible {
    outline: 3px solid var(--primary-color, currentColor);
    outline-offset: 2px;
  }

  :where(button, a, input, select, textarea) {
    max-width: 100%;
  }

  :where(a, label, p, li, dd, dt, button) {
    overflow-wrap: anywhere;
  }
`;
function Lt(a, e) {
  const t = a.ruby_segments;
  if (!Array.isArray(t) || t.length === 0) return null;
  const i = [];
  for (const s of t) {
    if (typeof s != "object" || s === null) return null;
    const n = s;
    if (typeof n.text != "string" || n.text === "") return null;
    const o = n.reading === void 0 || n.reading === null ? null : typeof n.reading == "string" && n.reading !== "" ? n.reading : void 0;
    if (o === void 0) return null;
    i.push({ text: n.text, reading: o });
  }
  return i.map((s) => s.text).join("") !== e ? null : i;
}
function Ut(a) {
  return r`${a.map(
    (e) => e.reading === null ? e.text : r`<ruby>${e.text}<rp>(</rp><rt>${e.reading}</rt><rp>)</rp></ruby>`
  )}`;
}
function nt(a, e = 0) {
  if (e > 16 || typeof a != "object" || a === null) return l;
  const t = a;
  if ((t.type === "text" || t.type === "inline_code") && typeof t.text == "string")
    return t.type === "inline_code" ? r`<code>${t.text}</code>` : t.text;
  if (t.type === "line_break") return r`<br />`;
  if (t.type === "ruby" && typeof t.text == "string" && t.text !== "" && typeof t.reading == "string" && t.reading !== "")
    return r`<ruby>${t.text}<rp>(</rp><rt>${t.reading}</rt><rp>)</rp></ruby>`;
  if ((t.type === "paragraph" || t.type === "emphasis" || t.type === "strong") && Array.isArray(t.children)) {
    const i = t.children.map((s) => nt(s, e + 1));
    return t.type === "paragraph" ? r`<p>${i}</p>` : t.type === "emphasis" ? r`<em>${i}</em>` : r`<strong>${i}</strong>`;
  }
  return l;
}
function Ot(a) {
  const e = a.payload.text;
  if (typeof e == "string" && e !== "") {
    const t = Lt(a.payload, e);
    return t === null ? e : Ut(t);
  }
  return a.kind === "rich_text" && a.payload.type === "document" && Array.isArray(a.payload.children) ? r`${a.payload.children.map((t) => nt(t, 1))}` : l;
}
function ot(a, e = !1) {
  const t = Ot(a);
  return t === l ? l : r`
    <div
      class="content-block ${e ? "primary-content" : ""}"
      lang=${a.language_tag ?? l}
    >
      ${t}
    </div>
  `;
}
const je = ["en", "fr"], He = {
  en: {
    "app.title": "LockLearn",
    "state.loading": "Loading LockLearn…",
    "state.error": "LockLearn could not be loaded.",
    "state.retry": "Retry",
    "state.protocol.title": "LockLearn was updated",
    "state.protocol.body": "The frontend and backend versions no longer match. Perform a full browser reload to load the current panel.",
    "state.protocol.reload": "Reload now",
    "state.noProfiles": "No LockLearn profile is available for this Home Assistant user.",
    "profile.mine": "My profiles",
    "profile.shared": "Shared with me",
    "profile.select": "Profile",
    "dashboard.loading": "Loading dashboard…",
    "dashboard.error": "Dashboard could not be loaded.",
    "dashboard.noTracks": "No active Track is available for this Profile.",
    "dashboard.dueToday": "Due today",
    "dashboard.latestVerified": "Last verified retrieval",
    "dashboard.retained": "Retained",
    "dashboard.notRetained": "Not retained",
    "dashboard.noVerified": "No verified retrieval yet",
    "dashboard.accuracy": "Recent verified accuracy",
    "dashboard.lastSession": "Last session",
    "dashboard.noSession": "No session yet",
    "dashboard.nextNotification": "Next notification",
    "dashboard.noNotification": "No notification scheduled",
    "dashboard.answered": "answered",
    "route.placeholder": "This section will be implemented in a later P5 milestone.",
    "learn.title": "Learn",
    "learn.track": "Track",
    "learn.start": "Start learning",
    "learn.resume": "Resume session",
    "learn.loading": "Loading learning session…",
    "learn.waiting": "First retrieval scheduled",
    "learn.waitingBody": "The answer stays hidden until this learning step is due.",
    "learn.waitingUntil": "Available at",
    "learn.noTracks": "No active Track is available for learning.",
    "learn.readOnly": "This Profile is read-only for your Home Assistant user.",
    "learn.empty": "No card is currently available for this Track.",
    "learn.progress": "Session progress",
    "learn.introduction": "New card · introduction",
    "learn.introductionHelp": "Study the complete context before the first retrieval attempt.",
    "learn.continue": "Continue",
    "learn.reveal": "Reveal",
    "learn.idk": "I don’t know",
    "learn.known": "I knew it",
    "learn.review": "Review again",
    "learn.hint": "Hint",
    "learn.hintUsed": "Hint used — this will be persisted with your answer.",
    "learn.knownAlready": "I already know this card",
    "learn.suspend": "Suspend this card",
    "learn.report": "Report this question",
    "learn.reported": "Question reported. No SRS penalty was applied.",
    "learn.mnemonic": "Personal mnemonic",
    "learn.mnemonicPlaceholder": "Add a private mnemonic for this card",
    "learn.saveMnemonic": "Save mnemonic",
    "learn.mnemonicSaved": "Mnemonic saved.",
    "learn.answer": "Answer",
    "learn.prompt": "Prompt",
    "learn.feedbackIdk": "Here is the answer. Review it before continuing.",
    "learn.completed": "Session complete",
    "learn.completedBody": "This learning session is finished.",
    "learn.newSession": "Start another session",
    "learn.error": "The learning session could not be updated.",
    "learn.reloaded": "The session changed on another client. The latest state was reloaded.",
    "learn.targetedSession": "Targeted difficulty session started.",
    "quiz.title": "Quiz",
    "quiz.track": "Track",
    "quiz.format": "Format",
    "quiz.formatMixed": "Mixed",
    "quiz.formatMcq": "Multiple choice",
    "quiz.formatFreeText": "Free text",
    "quiz.formatCloze": "Cloze multiple choice",
    "quiz.start": "Start quiz",
    "quiz.resume": "Resume quiz",
    "quiz.noTracks": "No active Track is available for quiz.",
    "quiz.readOnly": "This Profile is read-only for your Home Assistant user.",
    "quiz.empty": "No introduced card is currently due for this quiz.",
    "quiz.progress": "Quiz progress",
    "quiz.context": "Context",
    "quiz.answers": "Answer choices",
    "quiz.yourAnswer": "Your answer",
    "quiz.yourChoice": "Your choice",
    "quiz.check": "Check answer",
    "quiz.idk": "I don’t know",
    "quiz.hint": "Hint",
    "quiz.hintUsed": "Hint used — the quiz signal will record it.",
    "quiz.correct": "Correct",
    "quiz.wrong": "Not correct",
    "quiz.idkFeedback": "Not recalled",
    "quiz.unrecognized": "Answer not recognized",
    "quiz.correctAnswer": "Correct answer",
    "quiz.contrastive": "Known confusion: compare your choice with the correct answer.",
    "quiz.continue": "Continue",
    "quiz.showCorrection": "Show correction",
    "quiz.shouldAccept": "This answer should be accepted",
    "quiz.report": "Report this question",
    "quiz.reported": "Question reported. No SRS penalty was applied.",
    "quiz.reportAccepted": "Answer reported for review. No automatic SRS failure was applied.",
    "quiz.completed": "Quiz complete",
    "quiz.completedBody": "This quiz session is finished.",
    "quiz.newSession": "Start another quiz",
    "quiz.invalidQuestion": "This quiz question cannot be rendered safely.",
    "quiz.error": "The quiz could not be updated.",
    "quiz.reloaded": "The quiz changed on another client. The latest state was reloaded.",
    "manage.profiles": "Profiles",
    "manage.tracks": "Tracks",
    "manage.packs": "Packs",
    "manage.settings": "Settings",
    "manage.role": "Role",
    "manage.preset": "Preset",
    "manage.timezone": "Timezone",
    "manage.status": "Status",
    "manage.readOnly": "This Profile is read-only for your role.",
    "manage.name": "Name",
    "manage.active": "Active",
    "manage.archived": "Archived",
    "manage.paused": "Paused",
    "manage.save": "Save",
    "manage.saved": "Saved.",
    "manage.sharing": "Sharing",
    "manage.none": "None",
    "manage.remove": "Remove",
    "manage.user": "Home Assistant user",
    "manage.share": "Share",
    "manage.createProfile": "Create Profile",
    "manage.created": "Created.",
    "manage.create": "Create",
    "manage.noTracks": "No Track is configured for this Profile.",
    "manage.packVersion": "Pack version",
    "manage.priority": "Priority",
    "manage.plan": "Learning plan",
    "manage.delete": "Delete",
    "manage.deleteProfile": "Delete Profile",
    "manage.confirmDeleteProfile": "Delete this Profile and its LockLearn data?",
    "manage.deleted": "Deleted.",
    "manage.createTrack": "Create Track",
    "manage.noPacks": "No installed PackVersion is available.",
    "manage.pack": "Pack",
    "manage.sourceLanguage": "Source language",
    "manage.targetLanguage": "Target language",
    "manage.newPerDay": "New cards / day",
    "manage.reviewsPerDay": "Reviews / day",
    "manage.notificationTeasers": "New notification teasers / day",
    "manage.targetDate": "Target date",
    "manage.coverage": "Target coverage",
    "manage.retention": "Target retention",
    "manage.preview": "Preview",
    "manage.forecast": "Workload forecast",
    "manage.cardsRemaining": "Cards remaining",
    "manage.requiredNew": "Required new / day",
    "manage.reviews3Weeks": "Reviews / day in 3 weeks",
    "manage.reviews3Months": "Reviews / day in 3 months",
    "manage.notifications3Weeks": "Notifications / day in 3 weeks",
    "manage.sessionLoad3Weeks": "Active-session cards / day in 3 weeks",
    "manage.applyPlan": "Apply this plan",
    "manage.packUpdates": "Pack updates",
    "manage.noPackUpdates": "No alternate PackVersion is available for these Tracks.",
    "manage.packDiff": "Pack change preview",
    "manage.integrate": "Integrate update",
    "manage.packIntegrated": "Pack update integrated.",
    "manage.profileSettings": "Profile settings",
    "manage.presetInitialOnly": "The preset supplies initial defaults only",
    "manage.sessionLength": "Session length (cards)",
    "manage.pushBudget": "Daily push budget",
    "manage.weightVocabulary": "Vocabulary weight",
    "manage.weightKanji": "Kanji weight",
    "manage.weightGrammar": "Grammar weight",
    "manage.weightExpression": "Expression weight",
    "manage.learningNotifications": "Learning notifications / day",
    "manage.quizNotifications": "Quiz notifications / day",
    "manage.notificationTargets": "Notification targets",
    "manage.notificationTargetsHelp": "No selection means all enabled Profile targets.",
    "manage.noNotificationTargets": "No enabled notification target is configured for this Profile.",
    "manage.activeStart": "Active window start",
    "manage.activeEnd": "Active window end",
    "manage.notifications3Months": "Notifications / day in 3 months",
    "manage.sessionLoad3Months": "Active-session cards / day in 3 months",
    "manage.quietStart": "Quiet hours start",
    "manage.quietEnd": "Quiet hours end",
    "datasets.title": "Sources & Licences",
    "datasets.intro": "Installed dataset versions, update state, provenance, attribution and licence details.",
    "datasets.adminOnly": "Dataset update actions are available to Home Assistant administrators only.",
    "datasets.check": "Check for updates",
    "datasets.refreshed": "Dataset update information refreshed.",
    "datasets.installed": "Dataset installed and activated.",
    "datasets.loading": "Loading dataset information…",
    "datasets.empty": "No official dataset definition is available.",
    "datasets.state": "State",
    "datasets.installedVersion": "Installed version",
    "datasets.availableVersion": "Available version",
    "datasets.sourceAge": "Source age",
    "datasets.days": "days",
    "datasets.disk": "Disk cache",
    "datasets.builtAt": "Built at",
    "datasets.stale": "Stale sources",
    "datasets.changelog": "Changelog",
    "datasets.release": "Release details",
    "datasets.install": "Install",
    "datasets.update": "Update",
    "datasets.sources": "Sources & attribution",
    "datasets.noSources": "No provenance source is recorded for this dataset.",
    "datasets.upstream": "Upstream",
    "datasets.records": "provenance records",
    "datasets.modified": "modified",
    "datasets.sourcePage": "Source website",
    "datasets.showAttributions": "View individual attributions",
    "datasets.hideAttributions": "Hide individual attributions",
    "datasets.individualAttributions": "Individual attributions",
    "datasets.loadMore": "Load more",
    "datasets.licenses": "Licences",
    "datasets.noLicenses": "No dataset licence is recorded.",
    "datasets.attributionRequired": "attribution required",
    "datasets.attributionOptional": "attribution not required",
    "datasets.commercialAllowed": "commercial use allowed",
    "datasets.commercialBlocked": "commercial use not allowed",
    "datasets.shareAlike": "share-alike",
    "datasets.licensePage": "Licence text",
    "stats.title": "Stats & difficulties",
    "stats.intro": "Verified learning evidence, SRS state, metacognitive calibration and recurring difficulties.",
    "stats.track": "Track",
    "stats.allTracks": "All active tracks",
    "stats.loading": "Loading statistics…",
    "stats.verifiedGroup": "Verified learning indicators",
    "stats.dueToday": "Due today",
    "stats.verifiedAccuracy": "Verified accuracy",
    "stats.verifiedOnly": "trusted verified retrievals only",
    "stats.latestRetention": "Latest verified retention",
    "stats.retained": "Retained",
    "stats.notRetained": "Not retained",
    "stats.streak": "Due-queue streak",
    "stats.days": "days",
    "stats.states": "Current SRS states",
    "stats.stateNew": "New",
    "stats.stateLearning": "Learning",
    "stats.stateReview": "Review",
    "stats.stateRelearning": "Relearning",
    "stats.stateLeech": "Leech",
    "stats.evidence": "Exposure vs verified retrieval",
    "stats.evidenceExplain": "Seeing an answer is exposure, not proof of recall. Accuracy below is built only from trusted verified retrievals.",
    "stats.exposures": "Learning exposures",
    "stats.notAccuracy": "not counted as verified accuracy",
    "stats.verifiedRetrievals": "Verified retrievals",
    "stats.countsAccuracy": "eligible for verified accuracy",
    "stats.calibration": "What I thought I knew vs what was verified",
    "stats.calibrationExplain": "Each card is counted once from its first known declaration, then compared with the first later trusted verified retrieval.",
    "stats.declaredKnown": "Declared known",
    "stats.verifiedLater": "Verified later",
    "stats.verifiedCorrectLater": "Verified correct later",
    "stats.verifiedWrongLater": "Verified wrong / IDK later",
    "stats.awaitingVerification": "Awaiting verification",
    "stats.calibrationAccuracy": "Later verified accuracy",
    "stats.mastery": "Mastery estimate",
    "stats.cards": "cards",
    "stats.masteryExplain": "Secondary synthetic indicator only. It decays with time according to the review policy and never replaces due dates or verified retrieval evidence.",
    "stats.difficulties": "Persistent difficulties",
    "stats.noDifficulties": "No current leech cards.",
    "stats.leechScore": "leech score",
    "stats.correct": "correct",
    "stats.wrong": "wrong / IDK",
    "stats.mnemonicPresent": "personal mnemonic available",
    "stats.mnemonicSuggested": "personal mnemonic suggested",
    "stats.confusions": "Recurring confusions",
    "stats.noConfusions": "No recurring confusion has been recorded.",
    "stats.expected": "expected",
    "stats.chosen": "chosen",
    "stats.recentActivity": "Recent daily activity",
    "stats.noActivity": "No recent learning activity.",
    "stats.date": "Date",
    "stats.new": "New",
    "stats.reviewed": "Reviewed",
    "stats.relearning": "Relearning",
    "stats.personalMnemonic": "Personal mnemonic",
    "stats.createMnemonic": "Create mnemonic",
    "stats.updateMnemonic": "Update mnemonic",
    "stats.mnemonicSaved": "Personal mnemonic saved.",
    "stats.targetedSession": "Start targeted session",
    "stats.reactivate": "Reactivate card",
    "stats.reactivateConfirm": "Reactivate this leech and return it to normal review?",
    "stats.reactivated": "Card reactivated.",
    "stats.readOnlyDifficulty": "This shared Profile is read-only; difficulty actions are unavailable.",
    "nav.home": "Home",
    "nav.learn": "Learn",
    "nav.quiz": "Quiz",
    "nav.exam": "Exam",
    "nav.stats": "Stats",
    "nav.profiles": "Profiles",
    "nav.tracks": "Tracks",
    "nav.packs": "Packs",
    "nav.sources": "Sources & Licences",
    "nav.settings": "Settings"
  },
  fr: {
    "app.title": "LockLearn",
    "state.loading": "Chargement de LockLearn…",
    "state.error": "Impossible de charger LockLearn.",
    "state.retry": "Réessayer",
    "state.protocol.title": "LockLearn a été mis à jour",
    "state.protocol.body": "Les versions du frontend et du backend ne correspondent plus. Effectuez un rechargement complet du navigateur pour charger le panneau actuel.",
    "state.protocol.reload": "Recharger",
    "state.noProfiles": "Aucun profil LockLearn n’est accessible à cet utilisateur Home Assistant.",
    "profile.mine": "Mes profils",
    "profile.shared": "Partagés avec moi",
    "profile.select": "Profil",
    "dashboard.loading": "Chargement du tableau de bord…",
    "dashboard.error": "Impossible de charger le tableau de bord.",
    "dashboard.noTracks": "Aucun parcours actif n’est disponible pour ce profil.",
    "dashboard.dueToday": "À revoir aujourd’hui",
    "dashboard.latestVerified": "Dernière récupération vérifiée",
    "dashboard.retained": "Retenue",
    "dashboard.notRetained": "Non retenue",
    "dashboard.noVerified": "Aucune récupération vérifiée",
    "dashboard.accuracy": "Précision vérifiée récente",
    "dashboard.lastSession": "Dernière session",
    "dashboard.noSession": "Aucune session",
    "dashboard.nextNotification": "Prochaine notification",
    "dashboard.noNotification": "Aucune notification planifiée",
    "dashboard.answered": "répondues",
    "route.placeholder": "Cette section sera implémentée dans une étape P5 ultérieure.",
    "learn.title": "Apprendre",
    "learn.track": "Parcours",
    "learn.start": "Commencer",
    "learn.resume": "Reprendre la session",
    "learn.loading": "Chargement de la session d’apprentissage…",
    "learn.waiting": "Première récupération planifiée",
    "learn.waitingBody": "La réponse reste masquée jusqu’à l’échéance de cette étape d’apprentissage.",
    "learn.waitingUntil": "Disponible à",
    "learn.noTracks": "Aucun parcours actif n’est disponible pour l’apprentissage.",
    "learn.readOnly": "Ce profil est en lecture seule pour votre utilisateur Home Assistant.",
    "learn.empty": "Aucune carte n’est disponible actuellement pour ce parcours.",
    "learn.progress": "Progression de la session",
    "learn.introduction": "Nouvelle carte · introduction",
    "learn.introductionHelp": "Étudiez le contexte complet avant la première tentative de rappel.",
    "learn.continue": "Continuer",
    "learn.reveal": "Révéler",
    "learn.idk": "Je ne sais pas",
    "learn.known": "Je savais",
    "learn.review": "À revoir",
    "learn.hint": "Indice",
    "learn.hintUsed": "Indice utilisé — cette information sera enregistrée avec votre réponse.",
    "learn.knownAlready": "Je connais déjà cette carte",
    "learn.suspend": "Suspendre cette carte",
    "learn.report": "Signaler cette question",
    "learn.reported": "Question signalée. Aucune pénalité SRS n’a été appliquée.",
    "learn.mnemonic": "Mnémotechnique personnel",
    "learn.mnemonicPlaceholder": "Ajouter un mnémotechnique privé pour cette carte",
    "learn.saveMnemonic": "Enregistrer le mnémotechnique",
    "learn.mnemonicSaved": "Mnémotechnique enregistré.",
    "learn.answer": "Réponse",
    "learn.prompt": "Question",
    "learn.feedbackIdk": "Voici la réponse. Relisez-la avant de continuer.",
    "learn.completed": "Session terminée",
    "learn.completedBody": "Cette session d’apprentissage est terminée.",
    "learn.newSession": "Commencer une autre session",
    "learn.error": "Impossible de mettre à jour la session d’apprentissage.",
    "learn.reloaded": "La session a changé sur un autre client. Le dernier état a été rechargé.",
    "learn.targetedSession": "Session ciblée sur les difficultés démarrée.",
    "quiz.title": "Quiz",
    "quiz.track": "Parcours",
    "quiz.format": "Format",
    "quiz.formatMixed": "Mixte",
    "quiz.formatMcq": "QCM",
    "quiz.formatFreeText": "Réponse libre",
    "quiz.formatCloze": "Texte à trous — QCM",
    "quiz.start": "Commencer le quiz",
    "quiz.resume": "Reprendre le quiz",
    "quiz.noTracks": "Aucun parcours actif n’est disponible pour le quiz.",
    "quiz.readOnly": "Ce profil est en lecture seule pour votre utilisateur Home Assistant.",
    "quiz.empty": "Aucune carte déjà introduite n’est actuellement due pour ce quiz.",
    "quiz.progress": "Progression du quiz",
    "quiz.context": "Contexte",
    "quiz.answers": "Choix de réponse",
    "quiz.yourAnswer": "Votre réponse",
    "quiz.yourChoice": "Votre choix",
    "quiz.check": "Vérifier",
    "quiz.idk": "Je ne sais pas",
    "quiz.hint": "Indice",
    "quiz.hintUsed": "Indice utilisé — le signal du quiz l’enregistrera.",
    "quiz.correct": "Correct",
    "quiz.wrong": "Incorrect",
    "quiz.idkFeedback": "Non rappelé",
    "quiz.unrecognized": "Réponse non reconnue",
    "quiz.correctAnswer": "Bonne réponse",
    "quiz.contrastive": "Confusion connue : comparez votre choix à la bonne réponse.",
    "quiz.continue": "Continuer",
    "quiz.showCorrection": "Afficher la correction",
    "quiz.shouldAccept": "Cette réponse devrait être acceptée",
    "quiz.report": "Signaler cette question",
    "quiz.reported": "Question signalée. Aucune pénalité SRS n’a été appliquée.",
    "quiz.reportAccepted": "Réponse signalée pour vérification. Aucun échec SRS automatique n’a été appliqué.",
    "quiz.completed": "Quiz terminé",
    "quiz.completedBody": "Cette session de quiz est terminée.",
    "quiz.newSession": "Commencer un autre quiz",
    "quiz.invalidQuestion": "Cette question de quiz ne peut pas être affichée de façon sûre.",
    "quiz.error": "Impossible de mettre à jour le quiz.",
    "quiz.reloaded": "Le quiz a changé sur un autre client. Le dernier état a été rechargé.",
    "manage.profiles": "Profils",
    "manage.tracks": "Parcours",
    "manage.packs": "Packs",
    "manage.settings": "Réglages",
    "manage.role": "Rôle",
    "manage.preset": "Préréglage",
    "manage.timezone": "Fuseau horaire",
    "manage.status": "Statut",
    "manage.readOnly": "Ce profil est en lecture seule pour votre rôle.",
    "manage.name": "Nom",
    "manage.active": "Actif",
    "manage.archived": "Archivé",
    "manage.paused": "En pause",
    "manage.save": "Enregistrer",
    "manage.saved": "Enregistré.",
    "manage.sharing": "Partage",
    "manage.none": "Aucun",
    "manage.remove": "Retirer",
    "manage.user": "Utilisateur Home Assistant",
    "manage.share": "Partager",
    "manage.createProfile": "Créer un profil",
    "manage.created": "Créé.",
    "manage.create": "Créer",
    "manage.noTracks": "Aucun parcours n’est configuré pour ce profil.",
    "manage.packVersion": "Version du pack",
    "manage.priority": "Priorité",
    "manage.plan": "Plan de charge",
    "manage.delete": "Supprimer",
    "manage.deleteProfile": "Supprimer le profil",
    "manage.confirmDeleteProfile": "Supprimer ce profil et ses données LockLearn ?",
    "manage.deleted": "Supprimé.",
    "manage.createTrack": "Créer un parcours",
    "manage.noPacks": "Aucune PackVersion installée n’est disponible.",
    "manage.pack": "Pack",
    "manage.sourceLanguage": "Langue source",
    "manage.targetLanguage": "Langue cible",
    "manage.newPerDay": "Nouvelles cartes / jour",
    "manage.reviewsPerDay": "Révisions / jour",
    "manage.notificationTeasers": "Teasers de nouvelles cartes / jour",
    "manage.targetDate": "Date cible",
    "manage.coverage": "Couverture cible",
    "manage.retention": "Rétention cible",
    "manage.preview": "Prévisualiser",
    "manage.forecast": "Prévision de charge",
    "manage.cardsRemaining": "Cartes restantes",
    "manage.requiredNew": "Nouvelles requises / jour",
    "manage.reviews3Weeks": "Révisions / jour à 3 semaines",
    "manage.reviews3Months": "Révisions / jour à 3 mois",
    "manage.notifications3Weeks": "Notifications / jour à 3 semaines",
    "manage.sessionLoad3Weeks": "Cartes en session / jour à 3 semaines",
    "manage.applyPlan": "Appliquer ce plan",
    "manage.packUpdates": "Mises à jour de pack",
    "manage.noPackUpdates": "Aucune autre PackVersion n’est disponible pour ces parcours.",
    "manage.packDiff": "Prévisualisation des changements du pack",
    "manage.integrate": "Intégrer la mise à jour",
    "manage.packIntegrated": "Mise à jour du pack intégrée.",
    "manage.profileSettings": "Réglages du profil",
    "manage.presetInitialOnly": "Le préréglage fournit uniquement les valeurs initiales",
    "manage.sessionLength": "Taille de session (cartes)",
    "manage.pushBudget": "Budget push quotidien",
    "manage.weightVocabulary": "Poids vocabulaire",
    "manage.weightKanji": "Poids kanji",
    "manage.weightGrammar": "Poids grammaire",
    "manage.weightExpression": "Poids expressions",
    "manage.learningNotifications": "Notifications apprentissage / jour",
    "manage.quizNotifications": "Notifications quiz / jour",
    "manage.notificationTargets": "Cibles de notification",
    "manage.notificationTargetsHelp": "Aucune sélection signifie toutes les cibles actives du profil.",
    "manage.noNotificationTargets": "Aucune cible de notification active n’est configurée pour ce profil.",
    "manage.activeStart": "Début de la fenêtre active",
    "manage.activeEnd": "Fin de la fenêtre active",
    "manage.notifications3Months": "Notifications / jour à 3 mois",
    "manage.sessionLoad3Months": "Cartes en session / jour à 3 mois",
    "manage.quietStart": "Début des heures calmes",
    "manage.quietEnd": "Fin des heures calmes",
    "datasets.title": "Sources & licences",
    "datasets.intro": "Versions des datasets installés, état des mises à jour, provenance, attribution et détails de licence.",
    "datasets.adminOnly": "Les actions de mise à jour des datasets sont réservées aux administrateurs Home Assistant.",
    "datasets.check": "Vérifier les mises à jour",
    "datasets.refreshed": "Informations de mise à jour des datasets actualisées.",
    "datasets.installed": "Dataset installé et activé.",
    "datasets.loading": "Chargement des informations des datasets…",
    "datasets.empty": "Aucune définition de dataset officiel n’est disponible.",
    "datasets.state": "État",
    "datasets.installedVersion": "Version installée",
    "datasets.availableVersion": "Version disponible",
    "datasets.sourceAge": "Âge des sources",
    "datasets.days": "jours",
    "datasets.disk": "Cache disque",
    "datasets.builtAt": "Construit le",
    "datasets.stale": "Sources obsolètes",
    "datasets.changelog": "Changelog",
    "datasets.release": "Détails de la release",
    "datasets.install": "Installer",
    "datasets.update": "Mettre à jour",
    "datasets.sources": "Sources & attribution",
    "datasets.noSources": "Aucune source de provenance n’est enregistrée pour ce dataset.",
    "datasets.upstream": "Amont",
    "datasets.records": "enregistrements de provenance",
    "datasets.modified": "modifiés",
    "datasets.sourcePage": "Site de la source",
    "datasets.showAttributions": "Voir les attributions individuelles",
    "datasets.hideAttributions": "Masquer les attributions individuelles",
    "datasets.individualAttributions": "Attributions individuelles",
    "datasets.loadMore": "Afficher la suite",
    "datasets.licenses": "Licences",
    "datasets.noLicenses": "Aucune licence de dataset n’est enregistrée.",
    "datasets.attributionRequired": "attribution requise",
    "datasets.attributionOptional": "attribution non requise",
    "datasets.commercialAllowed": "usage commercial autorisé",
    "datasets.commercialBlocked": "usage commercial interdit",
    "datasets.shareAlike": "partage dans les mêmes conditions",
    "datasets.licensePage": "Texte de la licence",
    "stats.title": "Stats & difficultés",
    "stats.intro": "Preuves d’apprentissage vérifiées, état SRS, calibration métacognitive et difficultés récurrentes.",
    "stats.track": "Parcours",
    "stats.allTracks": "Tous les parcours actifs",
    "stats.loading": "Chargement des statistiques…",
    "stats.verifiedGroup": "Indicateurs d’apprentissage vérifiés",
    "stats.dueToday": "À revoir aujourd’hui",
    "stats.verifiedAccuracy": "Précision vérifiée",
    "stats.verifiedOnly": "récupérations vérifiées fiables uniquement",
    "stats.latestRetention": "Dernière rétention vérifiée",
    "stats.retained": "Retenu",
    "stats.notRetained": "Non retenu",
    "stats.streak": "Série de file à réviser",
    "stats.days": "jours",
    "stats.states": "États SRS actuels",
    "stats.stateNew": "Nouveau",
    "stats.stateLearning": "Apprentissage",
    "stats.stateReview": "Révision",
    "stats.stateRelearning": "Réapprentissage",
    "stats.stateLeech": "Difficulté persistante",
    "stats.evidence": "Exposition vs récupération vérifiée",
    "stats.evidenceExplain": "Voir une réponse est une exposition, pas une preuve de rappel. La précision affichée est calculée uniquement à partir de récupérations vérifiées fiables.",
    "stats.exposures": "Expositions d’apprentissage",
    "stats.notAccuracy": "non comptées dans la précision vérifiée",
    "stats.verifiedRetrievals": "Récupérations vérifiées",
    "stats.countsAccuracy": "prises en compte dans la précision vérifiée",
    "stats.calibration": "Ce que je pensais savoir vs ce qui a été vérifié",
    "stats.calibrationExplain": "Chaque carte est comptée une fois depuis sa première déclaration « connue », puis comparée à la première récupération vérifiée fiable ultérieure.",
    "stats.declaredKnown": "Déclarées connues",
    "stats.verifiedLater": "Vérifiées ensuite",
    "stats.verifiedCorrectLater": "Correctes à la vérification",
    "stats.verifiedWrongLater": "Fausses / Je ne sais pas ensuite",
    "stats.awaitingVerification": "En attente de vérification",
    "stats.calibrationAccuracy": "Précision vérifiée ultérieure",
    "stats.mastery": "Estimation de maîtrise",
    "stats.cards": "cartes",
    "stats.masteryExplain": "Indicateur synthétique secondaire uniquement. Il décroît avec le temps selon la politique de révision et ne remplace jamais les échéances ni les preuves de récupération vérifiée.",
    "stats.difficulties": "Difficultés persistantes",
    "stats.noDifficulties": "Aucune carte actuellement en difficulté persistante.",
    "stats.leechScore": "score de difficulté",
    "stats.correct": "correct",
    "stats.wrong": "faux / Je ne sais pas",
    "stats.mnemonicPresent": "mnémotechnique personnel disponible",
    "stats.mnemonicSuggested": "mnémotechnique personnel conseillé",
    "stats.confusions": "Confusions récurrentes",
    "stats.noConfusions": "Aucune confusion récurrente enregistrée.",
    "stats.expected": "attendu",
    "stats.chosen": "choisi",
    "stats.recentActivity": "Activité quotidienne récente",
    "stats.noActivity": "Aucune activité d’apprentissage récente.",
    "stats.date": "Date",
    "stats.new": "Nouvelles",
    "stats.reviewed": "Révisées",
    "stats.relearning": "Réapprentissage",
    "stats.personalMnemonic": "Mnémotechnique personnel",
    "stats.createMnemonic": "Créer le mnémotechnique",
    "stats.updateMnemonic": "Modifier le mnémotechnique",
    "stats.mnemonicSaved": "Mnémotechnique personnel enregistré.",
    "stats.targetedSession": "Lancer une session ciblée",
    "stats.reactivate": "Réactiver la carte",
    "stats.reactivateConfirm": "Réactiver cette difficulté persistante et la remettre en révision normale ?",
    "stats.reactivated": "Carte réactivée.",
    "stats.readOnlyDifficulty": "Ce profil partagé est en lecture seule ; les actions sur les difficultés sont indisponibles.",
    "nav.home": "Accueil",
    "nav.learn": "Apprendre",
    "nav.quiz": "Quiz",
    "nav.exam": "Examen",
    "nav.stats": "Stats",
    "nav.profiles": "Profils",
    "nav.tracks": "Parcours",
    "nav.packs": "Packs",
    "nav.sources": "Sources & licences",
    "nav.settings": "Réglages"
  }
};
function W(a) {
  const e = a.trim().toLowerCase().replaceAll("_", "-");
  if (je.includes(e))
    return e;
  const t = e.split("-", 1)[0];
  return je.includes(t) ? t : "en";
}
function F(a, e) {
  return He[a][e] ?? He.en[e];
}
function jt(a) {
  return a?.payload.selection?.progress_state === "new";
}
function Ht(a) {
  const e = a?.payload.available_at_utc;
  if (typeof e != "string") return null;
  const t = Date.parse(e);
  return Number.isNaN(t) ? null : t;
}
function We(a) {
  return a !== void 0 && a.role !== "viewer";
}
const I = 3;
class lt extends Error {
  constructor(e, t, i) {
    super(
      `LockLearn frontend protocol ${e} does not match backend protocol ${t}`
    ), this.frontendProtocol = e, this.backendProtocol = t, this.backendVersion = i;
  }
}
async function Wt(a) {
  const e = await a.callWS({
    type: "locklearn/bootstrap"
  });
  if (e.frontend_protocol !== I)
    throw new lt(
      I,
      e.frontend_protocol,
      e.backend_version
    );
  return e;
}
async function Fe(a) {
  const e = [];
  let t = null;
  do {
    const i = await a.callWS({
      type: "locklearn/profiles/list",
      limit: 100,
      ...t === null ? {} : { cursor: t }
    });
    e.push(...i.items), t = i.cursor;
  } while (t !== null);
  return e;
}
async function de(a, e, t = {}) {
  const i = [];
  let s = null;
  do {
    const n = await a.callWS({
      type: e,
      limit: 100,
      ...t,
      ...s === null ? {} : { cursor: s }
    });
    i.push(...n.items), s = n.cursor;
  } while (s !== null);
  return i;
}
async function Ft(a, e, t, i) {
  return a.callWS({
    type: "locklearn/profiles/create",
    name: e,
    preset: t,
    timezone: i
  });
}
async function Ve(a, e, t) {
  return a.callWS({
    type: "locklearn/profiles/update",
    profile_id: e,
    ...t
  });
}
async function Vt(a, e) {
  await a.callWS({
    type: "locklearn/profiles/delete",
    profile_id: e
  });
}
async function Bt(a, e) {
  return a.callWS({
    type: "locklearn/profiles/members",
    profile_id: e
  });
}
async function Kt(a, e) {
  return a.callWS({
    type: "locklearn/profiles/share_targets",
    profile_id: e
  });
}
async function Be(a, e, t, i) {
  await a.callWS({
    type: "locklearn/profiles/share",
    profile_id: e,
    target_user_id: t,
    role: i
  });
}
async function Qt(a, e, t) {
  await a.callWS({
    type: "locklearn/profiles/share",
    profile_id: e,
    target_user_id: t,
    remove: !0
  });
}
async function ct(a, e) {
  return de(a, "locklearn/tracks/list", {
    profile_id: e
  });
}
async function Gt(a, e) {
  return de(a, "locklearn/targets/list", {
    profile_id: e
  });
}
async function Jt(a, e, t) {
  return a.callWS({
    type: "locklearn/stats/get",
    profile_id: e,
    recent_verified_limit: 30,
    calibration_days: 7,
    confusion_limit: 20,
    ...t ? { track_id: t } : {}
  });
}
async function Yt(a, e, t) {
  return (await a.callWS({
    type: "locklearn/difficulties/list",
    profile_id: e,
    ...t ? { track_id: t } : {}
  })).items;
}
async function Zt(a, e) {
  return a.callWS({
    type: "locklearn/tracks/create",
    ...e
  });
}
async function Xt(a, e, t) {
  return a.callWS({
    type: "locklearn/tracks/update",
    track_id: e,
    ...t
  });
}
async function ei(a, e) {
  await a.callWS({
    type: "locklearn/tracks/delete",
    track_id: e
  });
}
async function ti(a) {
  return de(a, "locklearn/packs/list");
}
async function ii(a) {
  return de(a, "locklearn/datasets/list");
}
async function Ke(a, e, t, i) {
  return a.callWS({
    type: "locklearn/datasets/attributions",
    dataset_id: e,
    source_id: t,
    limit: 50,
    ...i ? { cursor: i } : {}
  });
}
async function si(a) {
  return (await a.callWS({
    type: "locklearn/datasets/refresh"
  })).items;
}
async function ai(a, e, t) {
  return a.callWS({
    type: "locklearn/datasets/install",
    dataset_id: e,
    ...t ? { version: t } : {}
  });
}
async function ri(a, e, t) {
  return a.callWS({
    type: "locklearn/tracks/preview_pack_update",
    track_id: e,
    pack_version_id: t
  });
}
async function ni(a, e, t) {
  return a.callWS({
    type: "locklearn/tracks/integrate_pack_update",
    track_id: e,
    pack_version_id: t
  });
}
function dt(a, e, t) {
  return {
    type: a,
    track_id: e,
    ...t
  };
}
async function oi(a, e, t) {
  return a.callWS(
    dt("locklearn/tracks/plan_preview", e, t)
  );
}
async function li(a, e, t) {
  return a.callWS(
    dt("locklearn/tracks/plan_set", e, t)
  );
}
async function ci(a, e) {
  return a.callWS({
    type: "locklearn/dashboard/get",
    profile_id: e
  });
}
async function di(a, e, t, i = 10, s = "mixed") {
  return a.callWS({
    type: "locklearn/session/start",
    profile_id: e,
    track_id: t,
    session_type: "quiz",
    strategy: "default",
    settings: {
      requested_cards: i,
      quiz_format: s,
      option_count: 4
    }
  });
}
async function ue(a, e, t, i) {
  return a.callWS({
    type: "locklearn/quiz/answer",
    session_id: e.id,
    expected_version: e.version,
    question_id: t,
    answer: i
  });
}
async function hi(a, e, t, i) {
  return a.callWS({
    type: "locklearn/quiz/evaluate",
    session_id: e,
    question_id: t,
    answer: i
  });
}
async function ui(a, e, t, i, s) {
  if (typeof s.submitted_text != "string" || s.grading_policy_kind === void 0 || s.grading_policy_version === void 0 || s.normalization_version === void 0)
    throw new Error("free-text report metadata is incomplete");
  return a.callWS({
    type: "locklearn/content/report",
    profile_id: e,
    track_id: t,
    card_key: i.card_key,
    learning_item_id: i.learning_item_id,
    prompt_facet_id: i.prompt_facet_id,
    answer_facet_id: i.answer_facet_id,
    submitted_text: s.submitted_text,
    normalized_submission: s.normalized_submission ?? null,
    grading_policy_kind: s.grading_policy_kind,
    grading_policy_version: s.grading_policy_version,
    normalization_version: s.normalization_version
  });
}
async function pi(a, e, t, i = 20) {
  return a.callWS({
    type: "locklearn/session/start",
    profile_id: e,
    track_id: t,
    session_type: "learn",
    strategy: "default",
    settings: { requested_cards: i }
  });
}
async function ne(a, e) {
  return a.callWS({
    type: "locklearn/session/get",
    session_id: e
  });
}
async function Qe(a, e, t, i) {
  return a.callWS({
    type: "locklearn/session/answer",
    session_id: e.id,
    expected_version: e.version,
    question_id: t,
    answer: i
  });
}
async function ht(a, e) {
  return a.callWS({
    type: "locklearn/session/complete",
    session_id: e.id,
    expected_version: e.version
  });
}
async function gi(a, e, t, i, s) {
  return a.callWS({
    type: "locklearn/progress/set_user_state",
    profile_id: e,
    track_id: t,
    card_key: i,
    user_state: s
  });
}
async function ut(a, e, t, i, s) {
  return a.callWS({
    type: "locklearn/content/report_question",
    profile_id: e,
    track_id: t,
    card_key: i.card_key,
    learning_item_id: i.learning_item_id,
    prompt_facet_id: i.prompt_facet_id,
    answer_facet_id: i.answer_facet_id,
    reason: "user_reported_question",
    ...s === void 0 || s.trim() === "" ? {} : { message: s.trim() }
  });
}
async function pt(a, e, t, i) {
  return a.callWS({
    type: "locklearn/annotations/create",
    profile_id: e,
    card_key: t,
    note: i.trim()
  });
}
async function mi(a, e, t, i) {
  return a.callWS({
    type: "locklearn/annotations/update",
    profile_id: e,
    annotation_id: t,
    note: i.trim()
  });
}
async function fi(a, e, t, i) {
  return a.callWS({
    type: "locklearn/leeches/reactivate",
    profile_id: e,
    track_id: t,
    card_key: i
  });
}
async function vi(a, e, t, i = 20) {
  return a.callWS({
    type: "locklearn/session/start",
    profile_id: e,
    track_id: t,
    session_type: "learn",
    strategy: "default",
    settings: {
      requested_cards: i,
      leeches_only: !0
    }
  });
}
var bi = Object.defineProperty, $ = (a, e, t, i) => {
  for (var s = void 0, n = a.length - 1, o; n >= 0; n--)
    (o = a[n]) && (s = o(e, t, s) || s);
  return s && bi(e, t, s), s;
};
function Z() {
  return globalThis.performance?.now() ?? Date.now();
}
const Se = class Se extends A {
  constructor() {
    super(...arguments), this.trackId = "", this.loading = !1, this.errorMessage = "", this.notice = "", this.revealed = !1, this.hintUsed = !1, this.pendingIdk = !1, this.mnemonic = "", this.reportMessage = "", this.questionStartedAt = Z(), this.questionId = null;
  }
  disconnectedCallback() {
    this.clearAvailabilityTimer(), super.disconnectedCallback();
  }
  updated(e) {
    if (e.has("profile") || e.has("dashboard")) {
      const t = this.tracks();
      t.some((i) => i.track_id === this.trackId) || (this.trackId = t[0]?.track_id ?? ""), e.has("profile") && (this.session = void 0, this.resetQuestionUi());
    }
    e.has("externalSession") && this.externalSession !== void 0 && this.profile !== void 0 && this.externalSession.profile_id === this.profile.profile_id && (this.trackId = this.externalSession.track_id ?? this.trackId, this.applySession(this.externalSession), this.notice = this.t("learn.targetedSession"), this.dispatchEvent(
      new CustomEvent("locklearn-session-handoff-consumed", {
        bubbles: !0,
        composed: !0
      })
    ));
  }
  locale() {
    const e = this.hass?.locale?.language ?? this.hass?.language ?? globalThis.navigator?.language ?? "en";
    return W(e);
  }
  t(e) {
    return F(this.locale(), e);
  }
  tracks() {
    return this.dashboard?.tracks ?? [];
  }
  selectedTrack() {
    return this.tracks().find((e) => e.track_id === this.trackId);
  }
  setTrack(e) {
    const t = e.currentTarget;
    t instanceof HTMLSelectElement && (this.trackId = t.value, this.session = void 0, this.errorMessage = "", this.notice = "", this.resetQuestionUi());
  }
  resetQuestionUi() {
    this.clearAvailabilityTimer(), this.waitingUntil = void 0, this.revealed = !1, this.hintUsed = !1, this.pendingIdk = !1, this.pendingIdkLatency = void 0, this.mnemonic = "", this.reportMessage = "", this.notice = "", this.questionStartedAt = Z(), this.questionId = this.session?.current_question?.question_id ?? null;
  }
  clearAvailabilityTimer() {
    this.availabilityTimer !== void 0 && (globalThis.clearTimeout(this.availabilityTimer), this.availabilityTimer = void 0);
  }
  scheduleCurrentQuestionAvailability() {
    const e = Ht(this.session?.current_question);
    e === null || e <= Date.now() || (this.waitingUntil = new Date(e).toISOString(), this.availabilityTimer = globalThis.setTimeout(() => {
      this.availabilityTimer = void 0, this.waitingUntil = void 0, this.questionStartedAt = Z();
    }, e - Date.now()));
  }
  applySession(e) {
    const i = (e.current_question?.question_id ?? null) !== this.questionId;
    this.session = e, i && (this.resetQuestionUi(), this.scheduleCurrentQuestionAvailability());
  }
  elapsedMs() {
    return Math.max(0, Math.round(Z() - this.questionStartedAt));
  }
  async start() {
    if (!(this.hass === void 0 || this.profile === void 0 || this.trackId === "" || !We(this.profile))) {
      this.loading = !0, this.errorMessage = "", this.notice = "";
      try {
        const e = await pi(
          this.hass,
          this.profile.profile_id,
          this.trackId
        );
        this.applySession(e);
      } catch (e) {
        this.errorMessage = e instanceof Error ? e.message : String(e);
      } finally {
        this.loading = !1;
      }
    }
  }
  async resume() {
    const e = this.selectedTrack()?.last_session;
    if (!(this.hass === void 0 || e === null || e === void 0)) {
      this.loading = !0, this.errorMessage = "";
      try {
        this.applySession(await ne(this.hass, e.session_id));
      } catch (t) {
        this.errorMessage = t instanceof Error ? t.message : String(t);
      } finally {
        this.loading = !1;
      }
    }
  }
  async recover(e) {
    if (this.hass !== void 0 && this.session !== void 0)
      try {
        this.applySession(await ne(this.hass, this.session.id)), this.notice = this.t("learn.reloaded");
        return;
      } catch {
      }
    this.errorMessage = e instanceof Error ? e.message : String(e);
  }
  async finalizeIfDone(e) {
    return this.hass !== void 0 && e.status === "active" && e.current_question === null && e.question_count > 0 ? ht(this.hass, e) : e;
  }
  async learningAction(e, t) {
    const i = this.session?.current_question;
    if (!(this.hass === void 0 || this.session === void 0 || i === null || i === void 0)) {
      this.loading = !0, this.errorMessage = "";
      try {
        const s = await Qe(
          this.hass,
          this.session,
          i.question_id,
          {
            kind: "learning",
            action: e,
            hint_used: this.hintUsed,
            presentation_to_answer_ms: t ?? this.elapsedMs()
          }
        );
        this.applySession(await this.finalizeIfDone(s));
      } catch (s) {
        await this.recover(s);
      } finally {
        this.loading = !1;
      }
    }
  }
  reveal() {
    this.revealed = !0;
  }
  idk() {
    this.pendingIdkLatency = this.elapsedMs(), this.pendingIdk = !0, this.revealed = !0;
  }
  showHint() {
    this.hintUsed = !0;
  }
  async setUserState(e) {
    const t = this.session?.current_question;
    if (!(this.hass === void 0 || this.profile === void 0 || this.session === void 0 || t === null || t === void 0 || this.session.track_id === null)) {
      this.loading = !0, this.errorMessage = "";
      try {
        await gi(
          this.hass,
          this.profile.profile_id,
          this.session.track_id,
          t.card_key,
          e
        );
        const i = await Qe(
          this.hass,
          this.session,
          t.question_id,
          { kind: "user_state", action: e }
        );
        this.applySession(await this.finalizeIfDone(i));
      } catch (i) {
        await this.recover(i);
      } finally {
        this.loading = !1;
      }
    }
  }
  async report() {
    const e = this.session?.current_question;
    if (!(this.hass === void 0 || this.profile === void 0 || this.session?.track_id === null || this.session === void 0 || e === null || e === void 0)) {
      this.loading = !0, this.errorMessage = "";
      try {
        await ut(
          this.hass,
          this.profile.profile_id,
          this.session.track_id,
          e,
          this.reportMessage
        ), this.notice = this.t("learn.reported"), this.reportMessage = "";
      } catch (t) {
        this.errorMessage = t instanceof Error ? t.message : String(t);
      } finally {
        this.loading = !1;
      }
    }
  }
  async saveMnemonic() {
    const e = this.session?.current_question;
    if (!(this.hass === void 0 || this.profile === void 0 || e === null || e === void 0 || this.mnemonic.trim() === "")) {
      this.loading = !0, this.errorMessage = "";
      try {
        await pt(
          this.hass,
          this.profile.profile_id,
          e.card_key,
          this.mnemonic
        ), this.notice = this.t("learn.mnemonicSaved"), this.mnemonic = "";
      } catch (t) {
        this.errorMessage = t instanceof Error ? t.message : String(t);
      } finally {
        this.loading = !1;
      }
    }
  }
  render() {
    if (this.profile === void 0) return l;
    if (!We(this.profile))
      return r`<section class="learn-card"><p>${this.t("learn.readOnly")}</p></section>`;
    const e = this.tracks();
    if (e.length === 0)
      return r`<section class="learn-card"><p>${this.t("learn.noTracks")}</p></section>`;
    const t = this.selectedTrack(), i = t?.last_session !== null && t?.last_session !== void 0 && ["active", "paused"].includes(t.last_session.status);
    return r`
      <section class="learn-shell">
        <div class="toolbar">
          <label>
            <span>${this.t("learn.track")}</span>
            <select .value=${this.trackId} @change=${this.setTrack} ?disabled=${this.loading}>
              ${e.map(
      (s) => r`
                  <option value=${s.track_id}>
                    ${s.name} · ${s.source_language} → ${s.target_language}
                  </option>
                `
    )}
            </select>
          </label>
          <div class="actions">
            ${i ? r`<button @click=${this.resume} ?disabled=${this.loading}>
                  ${this.t("learn.resume")}
                </button>` : l}
            <button class="primary" @click=${this.start} ?disabled=${this.loading}>
              ${this.t("learn.start")}
            </button>
          </div>
        </div>
        ${this.loading && this.session === void 0 ? r`<div class="notice" role="status">${this.t("learn.loading")}</div>` : l}
        ${this.errorMessage ? r`<div class="error" role="alert">
              <strong>${this.t("learn.error")}</strong>
              <div>${this.errorMessage}</div>
            </div>` : l}
        ${this.notice ? r`<div class="notice" role="status" aria-live="polite">${this.notice}</div>` : l}
        ${this.renderSession()}
      </section>
    `;
  }
  renderSession() {
    return this.session === void 0 ? l : this.session.question_count === 0 ? r`<section class="learn-card"><p>${this.t("learn.empty")}</p></section>` : this.session.current_question === null || this.session.status === "completed" ? r`
        <section class="learn-card">
          <h2>${this.t("learn.completed")}</h2>
          <p>${this.t("learn.completedBody")}</p>
          <button class="primary" @click=${this.start} ?disabled=${this.loading}>
            ${this.t("learn.newSession")}
          </button>
        </section>
      ` : this.waitingUntil !== void 0 ? this.renderWaiting(this.session.current_question) : jt(this.session.current_question) ? this.renderIntroduction(this.session.current_question) : this.renderRetrieval(this.session.current_question);
  }
  renderWaiting(e) {
    const t = this.waitingUntil;
    if (t === void 0) return l;
    const i = new Date(t), s = Number.isNaN(i.getTime()) ? "" : new Intl.DateTimeFormat(this.locale(), { timeStyle: "medium" }).format(i);
    return r`
      <article class="learn-card" aria-live="polite">
        ${this.renderProgress(e)}
        <div class="stage">${this.t("learn.waiting")}</div>
        <p>${this.t("learn.waitingBody")}</p>
        <p>
          ${this.t("learn.waitingUntil")}
          <time datetime=${t}>${s}</time>
        </p>
      </article>
    `;
  }
  renderProgress(e) {
    return r`
      <div class="progress">
        <span>${this.t("learn.progress")}</span>
        <span>${e.position + 1} / ${this.session?.question_count ?? 0}</span>
      </div>
    `;
  }
  renderIntroduction(e) {
    const t = e.payload.presentation;
    return t === void 0 ? r`<section class="learn-card"></section>` : r`
      <article class="learn-card">
        ${this.renderProgress(e)}
        <div class="stage">${this.t("learn.introduction")}</div>
        <p>${this.t("learn.introductionHelp")}</p>
        <div class="content">
          ${t.introduction_blocks.map(
      (i, s) => this.renderBlock(i, s === 0)
    )}
        </div>
        ${this.renderHintState(t.hint_blocks, t.mnemonic_blocks)}
        <div class="actions">
          <button
            class="primary"
            @click=${() => {
      this.learningAction("introduce");
    }}
            ?disabled=${this.loading}
          >
            ${this.t("learn.continue")}
          </button>
        </div>
        ${this.renderSecondaryActions(e)}
      </article>
    `;
  }
  renderRetrieval(e) {
    const t = e.payload.presentation;
    if (t === void 0) return r`<section class="learn-card"></section>`;
    const i = [...t.hint_blocks, ...t.mnemonic_blocks];
    return r`
      <article class="learn-card">
        ${this.renderProgress(e)}
        <div class="stage">${this.t("learn.prompt")}</div>
        <div class="content">
          ${t.context.flatMap(
      (s) => s.blocks.map((n) => this.renderBlock(n, !1))
    )}
          ${t.prompt.blocks.map((s) => this.renderBlock(s, !0))}
        </div>
        ${this.hintUsed ? r`
              <div class="hint-state" role="status">
                ${this.t("learn.hintUsed")}
                ${i.map((s) => this.renderBlock(s, !1))}
              </div>
            ` : l}
        ${this.revealed ? r`
              <div class="answer">
                <div class="stage">${this.t("learn.answer")}</div>
                ${t.answer.blocks.map((s) => this.renderBlock(s, !0))}
                ${this.pendingIdk ? r`<p>${this.t("learn.feedbackIdk")}</p>` : l}
              </div>
            ` : l}
        <div class="actions">
          ${this.revealed ? this.pendingIdk ? r`<button
                  class="primary"
                  @click=${() => {
      this.learningAction("idk", this.pendingIdkLatency);
    }}
                  ?disabled=${this.loading}
                >
                  ${this.t("learn.continue")}
                </button>` : r`
                  <button
                    @click=${() => {
      this.learningAction("review");
    }}
                    ?disabled=${this.loading}
                  >
                    ${this.t("learn.review")}
                  </button>
                  <button
                    class="primary"
                    @click=${() => {
      this.learningAction("known");
    }}
                    ?disabled=${this.loading}
                  >
                    ${this.t("learn.known")}
                  </button>
                ` : r`
                <button class="primary" @click=${this.reveal} ?disabled=${this.loading}>
                  ${this.t("learn.reveal")}
                </button>
                <button @click=${this.idk} ?disabled=${this.loading}>
                  ${this.t("learn.idk")}
                </button>
                ${i.length > 0 ? r`<button @click=${this.showHint} ?disabled=${this.loading || this.hintUsed}>
                      ${this.t("learn.hint")}
                    </button>` : l}
              `}
        </div>
        ${this.renderSecondaryActions(e)}
      </article>
    `;
  }
  renderHintState(e, t) {
    if (!this.hintUsed) return l;
    const i = [...e, ...t];
    return i.length === 0 ? l : r`
      <div class="hint-state" role="status">
        ${this.t("learn.hintUsed")}
        ${i.map((s) => this.renderBlock(s, !1))}
      </div>
    `;
  }
  renderSecondaryActions(e) {
    return r`
      <div class="secondary-actions">
        <button
          @click=${() => {
      this.setUserState("known_already");
    }}
          ?disabled=${this.loading}
        >
          ${this.t("learn.knownAlready")}
        </button>
        <button
          @click=${() => {
      this.setUserState("suspended");
    }}
          ?disabled=${this.loading}
        >
          ${this.t("learn.suspend")}
        </button>
        <button @click=${() => {
      this.report();
    }} ?disabled=${this.loading}>
          ${this.t("learn.report")}
        </button>
      </div>
      <div class="annotation">
        <label>
          <span>${this.t("learn.mnemonic")}</span>
          <textarea
            .value=${this.mnemonic}
            placeholder=${this.t("learn.mnemonicPlaceholder")}
            @input=${(t) => {
      const i = t.currentTarget;
      i instanceof HTMLTextAreaElement && (this.mnemonic = i.value);
    }}
          ></textarea>
        </label>
        <div class="field-row">
          <button
            @click=${() => {
      this.saveMnemonic();
    }}
            ?disabled=${this.loading || this.mnemonic.trim() === ""}
          >
            ${this.t("learn.saveMnemonic")}
          </button>
        </div>
      </div>
    `;
  }
  renderBlock(e, t) {
    return ot(e, t);
  }
};
Se.styles = M`
    ${rt}
    ${H}

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
let m = Se;
$([
  y({ attribute: !1 })
], m.prototype, "hass");
$([
  y({ attribute: !1 })
], m.prototype, "profile");
$([
  y({ attribute: !1 })
], m.prototype, "dashboard");
$([
  y({ attribute: !1 })
], m.prototype, "externalSession");
$([
  c()
], m.prototype, "trackId");
$([
  c()
], m.prototype, "session");
$([
  c()
], m.prototype, "loading");
$([
  c()
], m.prototype, "errorMessage");
$([
  c()
], m.prototype, "notice");
$([
  c()
], m.prototype, "revealed");
$([
  c()
], m.prototype, "hintUsed");
$([
  c()
], m.prototype, "pendingIdk");
$([
  c()
], m.prototype, "pendingIdkLatency");
$([
  c()
], m.prototype, "mnemonic");
$([
  c()
], m.prototype, "reportMessage");
$([
  c()
], m.prototype, "waitingUntil");
globalThis.customElements !== void 0 && customElements.get("locklearn-learn-view") === void 0 && customElements.define("locklearn-learn-view", m);
function Ge(a) {
  return a !== void 0 && a.role !== "viewer";
}
function yi(a) {
  return a?.payload.quiz;
}
function $i(a) {
  return a?.format === "mcq" || a?.format === "cloze_mcq";
}
function Je(a) {
  return a?.format === "free_text" && a.result === "wrong" && a.reportable && typeof a.submitted_text == "string" && a.grading_policy_kind !== void 0 && a.grading_policy_version !== void 0 && a.normalization_version !== void 0;
}
var _i = Object.defineProperty, w = (a, e, t, i) => {
  for (var s = void 0, n = a.length - 1, o; n >= 0; n--)
    (o = a[n]) && (s = o(e, t, s) || s);
  return s && _i(e, t, s), s;
};
function pe() {
  return globalThis.performance?.now() ?? Date.now();
}
const qe = class qe extends A {
  constructor() {
    super(...arguments), this.trackId = "", this.format = "mixed", this.loading = !1, this.errorMessage = "", this.notice = "", this.freeText = "", this.hintUsed = !1, this.questionStartedAt = pe(), this.questionId = null;
  }
  updated(e) {
    if (e.has("profile") || e.has("dashboard")) {
      const t = this.tracks();
      t.some((i) => i.track_id === this.trackId) || (this.trackId = t[0]?.track_id ?? ""), e.has("profile") && (this.session = void 0, this.resetQuestionUi());
    }
  }
  locale() {
    const e = this.hass?.locale?.language ?? this.hass?.language ?? globalThis.navigator?.language ?? "en";
    return W(e);
  }
  t(e) {
    return F(this.locale(), e);
  }
  tracks() {
    return this.dashboard?.tracks ?? [];
  }
  selectedTrack() {
    return this.tracks().find((e) => e.track_id === this.trackId);
  }
  setTrack(e) {
    const t = e.currentTarget;
    t instanceof HTMLSelectElement && (this.trackId = t.value, this.session = void 0, this.errorMessage = "", this.resetQuestionUi());
  }
  setFormat(e) {
    const t = e.currentTarget;
    t instanceof HTMLSelectElement && (this.format = t.value, this.session = void 0, this.errorMessage = "", this.resetQuestionUi());
  }
  resetQuestionUi() {
    this.feedback = void 0, this.pendingAnswer = void 0, this.pendingSession = void 0, this.freeText = "", this.hintUsed = !1, this.notice = "", this.questionStartedAt = pe(), this.questionId = this.session?.current_question?.question_id ?? null;
  }
  applySession(e) {
    const i = (e.current_question?.question_id ?? null) !== this.questionId;
    this.session = e, i && this.resetQuestionUi();
  }
  elapsedMs() {
    return Math.max(0, Math.round(pe() - this.questionStartedAt));
  }
  async start() {
    if (!(this.hass === void 0 || this.profile === void 0 || this.trackId === "" || !Ge(this.profile))) {
      this.loading = !0, this.errorMessage = "";
      try {
        this.applySession(
          await di(
            this.hass,
            this.profile.profile_id,
            this.trackId,
            10,
            this.format
          )
        );
      } catch (e) {
        this.errorMessage = e instanceof Error ? e.message : String(e);
      } finally {
        this.loading = !1;
      }
    }
  }
  async resume() {
    const e = this.selectedTrack()?.last_session;
    if (!(this.hass === void 0 || e === null || e === void 0 || e.session_type !== "quiz")) {
      this.loading = !0, this.errorMessage = "";
      try {
        this.applySession(await ne(this.hass, e.session_id));
      } catch (t) {
        this.errorMessage = t instanceof Error ? t.message : String(t);
      } finally {
        this.loading = !1;
      }
    }
  }
  async recover(e) {
    if (this.hass !== void 0 && this.session !== void 0)
      try {
        this.applySession(await ne(this.hass, this.session.id)), this.notice = this.t("quiz.reloaded");
        return;
      } catch {
      }
    this.errorMessage = e instanceof Error ? e.message : String(e);
  }
  enrichAnswer(e) {
    return {
      ...e,
      kind: "quiz",
      hint_used: this.hintUsed,
      presentation_to_answer_ms: this.elapsedMs()
    };
  }
  async evaluateFreeText(e) {
    const t = this.session?.current_question;
    if (this.hass === void 0 || this.session === void 0 || t === null || t === void 0) return;
    const i = this.enrichAnswer(e);
    this.loading = !0, this.errorMessage = "";
    try {
      this.feedback = await hi(
        this.hass,
        this.session.id,
        t.question_id,
        i
      ), this.pendingAnswer = i;
    } catch (s) {
      await this.recover(s);
    } finally {
      this.loading = !1;
    }
  }
  async submitDirect(e) {
    const t = this.session?.current_question;
    if (this.hass === void 0 || this.session === void 0 || t === null || t === void 0) return;
    const i = this.enrichAnswer(e);
    this.loading = !0, this.errorMessage = "";
    try {
      const s = await ue(
        this.hass,
        this.session,
        t.question_id,
        i
      );
      this.feedback = s.feedback, this.pendingAnswer = void 0, this.pendingSession = s.session;
    } catch (s) {
      await this.recover(s);
    } finally {
      this.loading = !1;
    }
  }
  async submitProvisional() {
    const e = this.session?.current_question;
    if (!(this.hass === void 0 || this.session === void 0 || e === null || e === void 0 || this.pendingAnswer === void 0)) {
      this.loading = !0, this.errorMessage = "";
      try {
        const t = await ue(
          this.hass,
          this.session,
          e.question_id,
          this.pendingAnswer
        );
        if (this.feedback?.result === "correct") {
          await this.advanceSession(t.session);
          return;
        }
        this.feedback = t.feedback, this.pendingSession = t.session;
      } catch (t) {
        await this.recover(t);
      } finally {
        this.loading = !1;
      }
    }
  }
  async advanceSession(e) {
    let t = e;
    this.hass !== void 0 && t.status === "active" && t.current_question === null && t.question_count > 0 && (t = await ht(this.hass, t)), this.applySession(t);
  }
  async advanceCommitted() {
    if (this.pendingSession !== void 0) {
      this.loading = !0, this.errorMessage = "";
      try {
        await this.advanceSession(this.pendingSession);
      } catch (e) {
        await this.recover(e);
      } finally {
        this.loading = !1;
      }
    }
  }
  async acceptReportedFreeText() {
    const e = this.session?.current_question;
    if (!(this.hass === void 0 || this.profile === void 0 || this.session === void 0 || this.session.track_id === null || e === null || e === void 0 || this.feedback === void 0 || this.pendingAnswer === void 0 || !Je(this.feedback))) {
      this.loading = !0, this.errorMessage = "";
      try {
        if ((await ui(
          this.hass,
          this.profile.profile_id,
          this.session.track_id,
          e,
          this.feedback
        )).srs_penalized)
          throw new Error("unrecognized free-text report unexpectedly penalized SRS");
        const i = {
          ...this.pendingAnswer,
          should_be_accepted: !0
        }, s = await ue(
          this.hass,
          this.session,
          e.question_id,
          i
        );
        await this.advanceSession(s.session), this.notice = this.t("quiz.reportAccepted");
      } catch (t) {
        await this.recover(t);
      } finally {
        this.loading = !1;
      }
    }
  }
  async reportCurrentQuestion() {
    const e = this.session?.current_question;
    if (!(this.hass === void 0 || this.profile === void 0 || this.session === void 0 || this.session.track_id === null || e === null || e === void 0)) {
      this.loading = !0, this.errorMessage = "";
      try {
        await ut(
          this.hass,
          this.profile.profile_id,
          this.session.track_id,
          e
        ), this.notice = this.t("quiz.reported");
      } catch (t) {
        this.errorMessage = t instanceof Error ? t.message : String(t);
      } finally {
        this.loading = !1;
      }
    }
  }
  showHint() {
    this.hintUsed = !0;
  }
  render() {
    if (this.profile === void 0) return l;
    if (!Ge(this.profile))
      return r`<section class="quiz-card"><p>${this.t("quiz.readOnly")}</p></section>`;
    const e = this.tracks();
    if (e.length === 0)
      return r`<section class="quiz-card"><p>${this.t("quiz.noTracks")}</p></section>`;
    const t = this.selectedTrack(), i = t?.last_session?.session_type === "quiz" && ["active", "paused"].includes(t.last_session.status);
    return r`
      <section class="quiz-shell">
        <div class="toolbar">
          <div class="toolbar-fields">
            <label>
              <span>${this.t("quiz.track")}</span>
              <select .value=${this.trackId} @change=${this.setTrack} ?disabled=${this.loading}>
                ${e.map(
      (s) => r`
                    <option value=${s.track_id}>
                      ${s.name} · ${s.source_language} → ${s.target_language}
                    </option>
                  `
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
            ${i ? r`<button @click=${this.resume} ?disabled=${this.loading}>
                  ${this.t("quiz.resume")}
                </button>` : l}
            <button class="primary" @click=${this.start} ?disabled=${this.loading}>
              ${this.t("quiz.start")}
            </button>
          </div>
        </div>
        ${this.errorMessage ? r`<div class="error" role="alert">
              <strong>${this.t("quiz.error")}</strong>
              <div>${this.errorMessage}</div>
            </div>` : l}
        ${this.notice ? r`<div class="notice" role="status" aria-live="polite">${this.notice}</div>` : l}
        ${this.renderSession()}
      </section>
    `;
  }
  renderSession() {
    if (this.session === void 0) return l;
    if (this.session.question_count === 0)
      return r`<section class="quiz-card"><p>${this.t("quiz.empty")}</p></section>`;
    if (this.session.current_question === null || this.session.status === "completed")
      return r`
        <section class="quiz-card">
          <h2>${this.t("quiz.completed")}</h2>
          <p>${this.t("quiz.completedBody")}</p>
          <button class="primary" @click=${this.start} ?disabled=${this.loading}>
            ${this.t("quiz.newSession")}
          </button>
        </section>
      `;
    const e = yi(this.session.current_question);
    return e === void 0 ? r`<section class="quiz-card"><p>${this.t("quiz.invalidQuestion")}</p></section>` : this.renderQuestion(this.session.current_question, e);
  }
  renderQuestion(e, t) {
    return r`
      <article class="quiz-card">
        <div class="progress">
          <span>${this.t("quiz.progress")}</span>
          <span>${e.position + 1} / ${this.session?.question_count ?? 0}</span>
        </div>
        <div class="format-label">${this.formatLabel(t.format)}</div>
        ${t.context_hint ? r`<div class="context">
              <strong>${this.t("quiz.context")}</strong>
              <div>${t.context_hint}</div>
            </div>` : l}
        <div class="prompt">${t.prompt_text}</div>
        ${this.hintUsed ? r`<div class="hint" role="status">
              <strong>${this.t("quiz.hintUsed")}</strong>
              ${t.hint_blocks.map((i) => this.renderBlock(i))}
            </div>` : l}
        ${this.feedback === void 0 ? this.renderInput(t) : this.renderFeedback(e, this.feedback)}
        <div class="actions">
          ${this.feedback === void 0 && t.hint_blocks.length > 0 ? r`<button @click=${this.showHint} ?disabled=${this.loading || this.hintUsed}>
                ${this.t("quiz.hint")}
              </button>` : l}
          <button @click=${() => {
      this.reportCurrentQuestion();
    }} ?disabled=${this.loading}>
            ${this.t("quiz.report")}
          </button>
        </div>
      </article>
    `;
  }
  renderInput(e) {
    return $i(e) ? r`
        <div class="options" aria-label=${this.t("quiz.answers")}>
          ${e.options.map(
      (t, i) => r`
              <button
                class="option"
                @click=${() => {
        this.submitDirect({
          selected_answer_id: t.answer_id
        });
      }}
                ?disabled=${this.loading}
              >
                ${i + 1}. ${t.text}
              </button>
            `
    )}
          <button
            @click=${() => {
      this.submitDirect({ selected_answer_id: null });
    }}
            ?disabled=${this.loading}
          >
            ${this.t("quiz.idk")}
          </button>
        </div>
      ` : r`
      <form
        class="free-text-form"
        @submit=${(t) => {
      t.preventDefault(), this.freeText.trim() !== "" && this.evaluateFreeText({ submitted_text: this.freeText });
    }}
      >
        <label>
          <span>${this.t("quiz.yourAnswer")}</span>
          <input
            autocomplete="off"
            .value=${this.freeText}
            @input=${(t) => {
      const i = t.currentTarget;
      i instanceof HTMLInputElement && (this.freeText = i.value);
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
            @click=${() => {
      this.submitDirect({ action: "idk" });
    }}
            ?disabled=${this.loading}
          >
            ${this.t("quiz.idk")}
          </button>
        </div>
      </form>
    `;
  }
  renderFeedback(e, t) {
    return r`
      <div class="feedback" role="status" aria-live="polite">
        <p class="feedback-title">${this.feedbackLabel(t.result)}</p>
        ${t.selected_answer ? r`<p class="feedback-detail">
              ${this.t("quiz.yourChoice")}: ${t.selected_answer}
            </p>` : l}
        ${t.reveal_correct_answer && t.correct_answer ? r`<p class="feedback-detail">
              ${this.t("quiz.correctAnswer")}: ${t.correct_answer}
            </p>` : l}
        ${t.contrastive_feedback ? r`<p class="feedback-detail">${this.t("quiz.contrastive")}</p>` : l}
        <div class="actions">
          ${this.pendingSession !== void 0 ? r`<button
                class="primary"
                @click=${() => {
      this.advanceCommitted();
    }}
                ?disabled=${this.loading}
              >
                ${this.t("quiz.continue")}
              </button>` : r`<button
                class="primary"
                @click=${() => {
      this.submitProvisional();
    }}
                ?disabled=${this.loading}
              >
                ${t.result === "wrong" ? this.t("quiz.showCorrection") : this.t("quiz.continue")}
              </button>`}
          ${Je(t) ? r`<button
                @click=${() => {
      this.acceptReportedFreeText();
    }}
                ?disabled=${this.loading}
              >
                ${this.t("quiz.shouldAccept")}
              </button>` : l}
        </div>
      </div>
    `;
  }
  formatLabel(e) {
    return e === "mcq" ? this.t("quiz.formatMcq") : e === "cloze_mcq" ? this.t("quiz.formatCloze") : this.t("quiz.formatFreeText");
  }
  feedbackLabel(e) {
    return e === "correct" ? this.t("quiz.correct") : e === "wrong" ? this.t("quiz.wrong") : e === "idk" ? this.t("quiz.idkFeedback") : this.t("quiz.unrecognized");
  }
  renderBlock(e) {
    return ot(e);
  }
};
qe.styles = M`
    ${rt}
    ${H}

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
let f = qe;
w([
  y({ attribute: !1 })
], f.prototype, "hass");
w([
  y({ attribute: !1 })
], f.prototype, "profile");
w([
  y({ attribute: !1 })
], f.prototype, "dashboard");
w([
  c()
], f.prototype, "trackId");
w([
  c()
], f.prototype, "format");
w([
  c()
], f.prototype, "session");
w([
  c()
], f.prototype, "loading");
w([
  c()
], f.prototype, "errorMessage");
w([
  c()
], f.prototype, "notice");
w([
  c()
], f.prototype, "feedback");
w([
  c()
], f.prototype, "pendingAnswer");
w([
  c()
], f.prototype, "pendingSession");
w([
  c()
], f.prototype, "freeText");
w([
  c()
], f.prototype, "hintUsed");
globalThis.customElements !== void 0 && customElements.get("locklearn-quiz-view") === void 0 && customElements.define("locklearn-quiz-view", f);
var ki = Object.defineProperty, v = (a, e, t, i) => {
  for (var s = void 0, n = a.length - 1, o; n >= 0; n--)
    (o = a[n]) && (s = o(e, t, s) || s);
  return s && ki(e, t, s), s;
};
function q(a, e, t) {
  const i = Number.parseInt(String(a ?? ""), 10);
  return Number.isFinite(i) && i >= t ? i : e;
}
function L(a, e, t, i) {
  const s = Number.parseFloat(String(a ?? ""));
  return Number.isFinite(s) && s >= t && s <= i ? s : e;
}
function X(a, e) {
  const t = a?.[e];
  return typeof t == "object" && t !== null ? t : {};
}
function wi(a) {
  return a === "owner";
}
function xi(a) {
  return a === "owner" || a === "editor";
}
const Ae = class Ae extends A {
  constructor() {
    super(...arguments), this.route = "profiles", this.tracks = [], this.packs = [], this.notificationTargets = [], this.members = [], this.shareTargets = [], this.selectedTrackId = "", this.packDiffTrack = "", this.packDiffTarget = "", this.loading = !1, this.errorMessage = "", this.notice = "";
  }
  updated(e) {
    (e.has("profile") || e.has("route")) && this.load();
  }
  locale() {
    return W(
      this.hass?.locale?.language ?? this.hass?.language ?? globalThis.navigator?.language ?? "en"
    );
  }
  t(e) {
    return F(this.locale(), e);
  }
  isOwner() {
    return wi(this.profile?.role);
  }
  canEditTrack() {
    return xi(this.profile?.role);
  }
  async load() {
    if (this.hass !== void 0) {
      if (this.profile === void 0) {
        this.tracks = [], this.packs = [], this.notificationTargets = [], this.members = [], this.shareTargets = [];
        return;
      }
      this.loading = !0, this.errorMessage = "";
      try {
        [this.tracks, this.packs] = await Promise.all([
          ct(this.hass, this.profile.profile_id),
          ti(this.hass)
        ]), this.notificationTargets = this.canEditTrack() ? await Gt(this.hass, this.profile.profile_id) : [], this.tracks.some((e) => e.track_id === this.selectedTrackId) || (this.selectedTrackId = this.tracks[0]?.track_id ?? ""), this.isOwner() && this.route === "profiles" ? [this.members, this.shareTargets] = await Promise.all([
          Bt(this.hass, this.profile.profile_id),
          Kt(this.hass, this.profile.profile_id)
        ]) : (this.members = [], this.shareTargets = []);
      } catch (e) {
        this.errorMessage = e instanceof Error ? e.message : String(e);
      } finally {
        this.loading = !1;
      }
    }
  }
  async mutate(e, t) {
    this.loading = !0, this.errorMessage = "";
    try {
      await e(), await this.load(), this.notice = t, this.dispatchEvent(new CustomEvent("locklearn-refresh", { bubbles: !0, composed: !0 }));
    } catch (i) {
      this.errorMessage = i instanceof Error ? i.message : String(i);
    } finally {
      this.loading = !1;
    }
  }
  render() {
    return this.profile === void 0 ? r`<section class="stack">
        <h1>${this.t("manage.profiles")}</h1>
        ${this.errorMessage ? r`<div class="error" role="alert">${this.errorMessage}</div>` : l}
        ${this.notice ? r`<div class="notice" role="status">${this.notice}</div>` : l}
        ${this.renderCreateProfile()}
      </section>` : r`
      <section class="stack">
        <h1>${this.routeTitle()}</h1>
        ${this.errorMessage ? r`<div class="error" role="alert">${this.errorMessage}</div>` : l}
        ${this.notice ? r`<div class="notice" role="status">${this.notice}</div>` : l}
        ${this.route === "profiles" ? this.renderProfiles() : this.route === "tracks" ? this.renderTracks() : this.route === "packs" ? this.renderPacks() : this.renderSettings()}
      </section>
    `;
  }
  routeTitle() {
    return this.route === "profiles" ? this.t("manage.profiles") : this.route === "tracks" ? this.t("manage.tracks") : this.route === "packs" ? this.t("manage.packs") : this.t("manage.settings");
  }
  renderProfiles() {
    return r`
      <div class="grid">
        <article class="card">
          <h2>${this.profile?.name}</h2>
          <dl>
            <dt>${this.t("manage.role")}</dt><dd>${this.profile?.role}</dd>
            <dt>${this.t("manage.preset")}</dt><dd>${this.profile?.preset}</dd>
            <dt>${this.t("manage.timezone")}</dt><dd>${this.profile?.timezone}</dd>
            <dt>${this.t("manage.status")}</dt><dd>${this.profile?.status}</dd>
          </dl>
          ${this.isOwner() ? this.renderProfileForm() : r`<p class="muted">${this.t("manage.readOnly")}</p>`}
        </article>
        ${this.isOwner() ? this.renderSharing() : l}
      </div>
      ${this.renderCreateProfile()}
    `;
  }
  renderProfileForm() {
    return r`
      <form class="form-grid" @submit=${(e) => {
      e.preventDefault();
      const t = new FormData(e.currentTarget);
      this.hass === void 0 || this.profile === void 0 || this.mutate(
        () => Ve(this.hass, this.profile.profile_id, {
          name: String(t.get("name") ?? "").trim(),
          timezone: String(t.get("timezone") ?? "").trim(),
          status: String(t.get("status") ?? "active")
        }),
        this.t("manage.saved")
      );
    }}>
        <label>${this.t("manage.name")}<input name="name" .value=${this.profile?.name ?? ""} required /></label>
        <label>${this.t("manage.timezone")}<input name="timezone" .value=${this.profile?.timezone ?? "UTC"} required /></label>
        <label>${this.t("manage.status")}
          <select name="status" .value=${this.profile?.status ?? "active"}>
            <option value="active">${this.t("manage.active")}</option>
            <option value="archived">${this.t("manage.archived")}</option>
          </select>
        </label>
        <div class="actions">
          <button class="primary" type="submit">${this.t("manage.save")}</button>
          <button type="button" @click=${() => this.removeProfile()}>${this.t("manage.deleteProfile")}</button>
        </div>
      </form>
    `;
  }
  renderSharing() {
    const e = new Set(this.members.map((s) => s.ha_user_id)), t = this.shareTargets.filter((s) => !e.has(s.ha_user_id)), i = this.members.filter((s) => s.role === "owner").length;
    return r`
      <article class="card">
        <h2>${this.t("manage.sharing")}</h2>
        ${this.members.length === 0 ? r`<p>${this.t("manage.none")}</p>` : r`
          <ul>${this.members.map((s) => r`<li>
            ${s.name}
            <select
              aria-label=${this.t("manage.role")}
              .value=${s.role}
              ?disabled=${s.role === "owner" && i === 1}
              @change=${(n) => {
      const o = n.currentTarget;
      o instanceof HTMLSelectElement && this.changeMemberRole(s.ha_user_id, o.value);
    }}
            >
              <option value="viewer">viewer</option>
              <option value="editor">editor</option>
              <option value="owner">owner</option>
            </select>
            ${s.role === "owner" && i === 1 ? l : r`
              <button @click=${() => this.removeMember(s.ha_user_id)}>${this.t("manage.remove")}</button>`}
          </li>`)}</ul>`}
        ${t.length === 0 ? l : r`
          <form class="form-grid" @submit=${(s) => {
      s.preventDefault();
      const n = new FormData(s.currentTarget);
      this.addMember(
        String(n.get("user") ?? ""),
        String(n.get("role") ?? "viewer")
      );
    }}>
            <label>${this.t("manage.user")}<select name="user">
              ${t.map((s) => r`<option value=${s.ha_user_id}>${s.name}</option>`)}
            </select></label>
            <label>${this.t("manage.role")}<select name="role">
              <option value="viewer">viewer</option><option value="editor">editor</option><option value="owner">owner</option>
            </select></label>
            <div class="actions"><button type="submit">${this.t("manage.share")}</button></div>
          </form>`}
      </article>
    `;
  }
  async addMember(e, t) {
    !e || this.hass === void 0 || this.profile === void 0 || await this.mutate(() => Be(this.hass, this.profile.profile_id, e, t), this.t("manage.saved"));
  }
  async removeMember(e) {
    this.hass === void 0 || this.profile === void 0 || await this.mutate(() => Qt(this.hass, this.profile.profile_id, e), this.t("manage.saved"));
  }
  async changeMemberRole(e, t) {
    this.hass === void 0 || this.profile === void 0 || await this.mutate(
      () => Be(this.hass, this.profile.profile_id, e, t),
      this.t("manage.saved")
    );
  }
  async removeProfile() {
    this.hass === void 0 || this.profile === void 0 || globalThis.confirm?.(this.t("manage.confirmDeleteProfile")) && await this.mutate(
      () => Vt(this.hass, this.profile.profile_id),
      this.t("manage.deleted")
    );
  }
  renderCreateProfile() {
    return r`
      <article class="card">
        <h2>${this.t("manage.createProfile")}</h2>
        <form class="form-grid" @submit=${(e) => {
      e.preventDefault();
      const t = new FormData(e.currentTarget);
      this.hass !== void 0 && this.mutate(
        () => Ft(
          this.hass,
          String(t.get("name") ?? "").trim(),
          String(t.get("preset") ?? "standard"),
          String(t.get("timezone") ?? "UTC").trim()
        ),
        this.t("manage.created")
      );
    }}>
          <label>${this.t("manage.name")}<input name="name" required /></label>
          <label>${this.t("manage.preset")}<select name="preset">
            <option value="child">child</option><option value="standard">standard</option>
            <option value="intensive">intensive</option><option value="custom">custom</option>
          </select></label>
          <label>${this.t("manage.timezone")}<input name="timezone" .value=${this.profile?.timezone ?? Intl.DateTimeFormat().resolvedOptions().timeZone ?? "UTC"} required /></label>
          <div class="actions"><button class="primary" type="submit">${this.t("manage.create")}</button></div>
        </form>
      </article>
    `;
  }
  renderTracks() {
    return r`
      ${this.tracks.length === 0 ? r`<div class="card"><p>${this.t("manage.noTracks")}</p></div>` : r`
        <div class="grid">${this.tracks.map((e) => this.renderTrack(e))}</div>`}
      ${this.canEditTrack() ? this.renderCreateTrack() : r`<div class="card"><p>${this.t("manage.readOnly")}</p></div>`}
    `;
  }
  renderTrack(e) {
    const t = X(e.settings, "scheduler"), i = Array.isArray(t.target_ids) ? t.target_ids.map(String) : [], s = e.content_weights ?? {};
    return r`
      <article class="card">
        <h2>${e.name}</h2>
        <p class="meta">${e.source_language} → ${e.target_language} · ${e.status}</p>
        <p class="meta">${this.t("manage.packVersion")}: ${e.pack_version_id ?? "—"}</p>
        ${this.canEditTrack() ? r`
          <form class="form-grid" @submit=${(n) => {
      n.preventDefault();
      const o = new FormData(n.currentTarget);
      if (this.hass === void 0) return;
      const d = o.getAll("notificationTarget").map(String), h = {
        vocabulary: L(o.get("weightVocabulary"), Number(s.vocabulary ?? 1), 0, 100),
        kanji: L(o.get("weightKanji"), Number(s.kanji ?? 1), 0, 100),
        grammar: L(o.get("weightGrammar"), Number(s.grammar ?? 1), 0, 100),
        expression: L(o.get("weightExpression"), Number(s.expression ?? 1), 0, 100)
      };
      this.mutate(() => Xt(this.hass, e.track_id, {
        name: String(o.get("name") ?? e.name),
        source_language: String(o.get("source") ?? e.source_language ?? "").trim(),
        target_language: String(o.get("target") ?? e.target_language ?? "").trim(),
        status: String(o.get("status") ?? e.status),
        priority: q(o.get("priority"), e.priority, 1),
        content_weights: h,
        scheduler_settings: {
          learning_count: q(o.get("learningCount"), Number(t.learning_count ?? 0), 0),
          quiz_count: q(o.get("quizCount"), Number(t.quiz_count ?? 0), 0),
          ...d.length === 0 ? {} : { target_ids: d }
        }
      }), this.t("manage.saved"));
    }}>
            <label>${this.t("manage.name")}<input name="name" .value=${e.name} /></label>
            <label>${this.t("manage.status")}<select name="status" .value=${e.status}>
              <option value="active">${this.t("manage.active")}</option>
              <option value="paused">${this.t("manage.paused")}</option>
              <option value="archived">${this.t("manage.archived")}</option>
            </select></label>
            <label>${this.t("manage.sourceLanguage")}<input name="source" .value=${e.source_language ?? ""} required /></label>
            <label>${this.t("manage.targetLanguage")}<input name="target" .value=${e.target_language ?? ""} required /></label>
            <label>${this.t("manage.priority")}<input name="priority" type="number" min="1" .value=${String(e.priority)} /></label>
            <label>${this.t("manage.weightVocabulary")}<input name="weightVocabulary" type="number" min="0" step=".1" .value=${String(s.vocabulary ?? 1)} /></label>
            <label>${this.t("manage.weightKanji")}<input name="weightKanji" type="number" min="0" step=".1" .value=${String(s.kanji ?? 1)} /></label>
            <label>${this.t("manage.weightGrammar")}<input name="weightGrammar" type="number" min="0" step=".1" .value=${String(s.grammar ?? 1)} /></label>
            <label>${this.t("manage.weightExpression")}<input name="weightExpression" type="number" min="0" step=".1" .value=${String(s.expression ?? 1)} /></label>
            <label>${this.t("manage.learningNotifications")}<input name="learningCount" type="number" min="0" .value=${String(t.learning_count ?? 0)} /></label>
            <label>${this.t("manage.quizNotifications")}<input name="quizCount" type="number" min="0" .value=${String(t.quiz_count ?? 0)} /></label>
            <label>${this.t("manage.notificationTargets")}
              <select name="notificationTarget" multiple size=${Math.min(4, Math.max(2, this.notificationTargets.length))}>
                ${this.notificationTargets.map((n) => r`
                  <option value=${n.target_id} ?selected=${i.includes(n.target_id)}>
                    ${n.friendly_name} · ${n.platform}
                  </option>`)}
              </select>
              <span class="meta">${this.notificationTargets.length === 0 ? this.t("manage.noNotificationTargets") : this.t("manage.notificationTargetsHelp")}</span>
            </label>
            <div class="actions">
              <button type="submit">${this.t("manage.save")}</button>
              <button type="button" @click=${() => {
      this.selectedTrackId = e.track_id, this.forecast = void 0, this.forecastPlan = void 0;
    }}>${this.t("manage.plan")}</button>
              <button type="button" @click=${() => this.removeTrack(e.track_id)}>${this.t("manage.delete")}</button>
            </div>
          </form>
          ${this.selectedTrackId === e.track_id ? this.renderPlan(e) : l}
        ` : l}
      </article>
    `;
  }
  renderCreateTrack() {
    return r`
      <article class="card">
        <h2>${this.t("manage.createTrack")}</h2>
        ${this.packs.length === 0 ? r`<p>${this.t("manage.noPacks")}</p>` : r`
          <form class="form-grid" @submit=${(e) => {
      e.preventDefault();
      const t = new FormData(e.currentTarget);
      this.hass === void 0 || this.profile === void 0 || this.mutate(() => Zt(this.hass, {
        profile_id: this.profile.profile_id,
        name: String(t.get("name") ?? "").trim(),
        pack_version_id: String(t.get("pack") ?? ""),
        source_language: String(t.get("source") ?? "").trim(),
        target_language: String(t.get("target") ?? "").trim(),
        priority: q(t.get("priority"), 1, 1)
      }), this.t("manage.created"));
    }}>
            <label>${this.t("manage.name")}<input name="name" required /></label>
            <label>${this.t("manage.pack")}<select name="pack">
              ${this.packs.map((e) => r`<option value=${e.pack_version_id}>${e.name} · ${e.version}</option>`)}
            </select></label>
            <label>${this.t("manage.sourceLanguage")}<input name="source" placeholder="ja" required /></label>
            <label>${this.t("manage.targetLanguage")}<input name="target" placeholder="fr" required /></label>
            <label>${this.t("manage.priority")}<input name="priority" type="number" min="1" value="1" /></label>
            <div class="actions"><button class="primary" type="submit">${this.t("manage.create")}</button></div>
          </form>`}
      </article>
    `;
  }
  async removeTrack(e) {
    this.hass !== void 0 && await this.mutate(() => ei(this.hass, e), this.t("manage.deleted"));
  }
  planFrom(e) {
    const t = new FormData(e);
    return {
      max_new_per_day_cards: q(t.get("new"), 0, 0),
      max_reviews_per_day_cards: q(t.get("reviews"), 50, 1),
      max_notification_new_teasers: q(t.get("teasers"), 2, 0),
      target_date: String(t.get("date") ?? "").trim() || null,
      target_coverage: L(t.get("coverage"), 1, 0.01, 1),
      target_retention: L(t.get("retention"), 0.9, 0.01, 1)
    };
  }
  renderPlan(e) {
    const t = X(e.settings, "learning_plan"), i = Number(this.profile?.settings?.max_new_per_day_cards ?? 8);
    return r`
      <div class="stack">
        <h3>${this.t("manage.plan")}</h3>
        <form class="form-grid" @submit=${(s) => {
      if (s.preventDefault(), this.hass === void 0) return;
      const n = this.planFrom(s.currentTarget);
      this.loading = !0, oi(this.hass, e.track_id, n).then((o) => {
        this.forecast = o, this.forecastPlan = n;
      }).catch((o) => {
        this.errorMessage = o instanceof Error ? o.message : String(o);
      }).finally(() => {
        this.loading = !1;
      });
    }}>
          <label>${this.t("manage.newPerDay")}<input name="new" type="number" min="0" .value=${String(t.max_new_per_day_cards ?? i)} /></label>
          <label>${this.t("manage.reviewsPerDay")}<input name="reviews" type="number" min="1" .value=${String(t.max_reviews_per_day_cards ?? 50)} /></label>
          <label>${this.t("manage.notificationTeasers")}<input name="teasers" type="number" min="0" .value=${String(t.max_notification_new_teasers ?? Math.min(2, i))} /></label>
          <label>${this.t("manage.targetDate")}<input name="date" type="date" .value=${String(t.target_date ?? "")} /></label>
          <label>${this.t("manage.coverage")}<input name="coverage" type="number" min=".01" max="1" step=".01" .value=${String(t.target_coverage ?? 1)} /></label>
          <label>${this.t("manage.retention")}<input name="retention" type="number" min=".01" max="1" step=".01" .value=${String(t.target_retention ?? 0.9)} /></label>
          <div class="actions"><button class="primary" type="submit">${this.t("manage.preview")}</button></div>
        </form>
        ${this.forecast === void 0 ? l : this.renderForecast(e)}
      </div>
    `;
  }
  renderForecast(e) {
    const t = this.forecast;
    return r`
      <div class=${t.warnings.length > 0 ? "warning" : "notice"}>
        <strong>${this.t("manage.forecast")}</strong>
        <dl>
          <dt>${this.t("manage.cardsRemaining")}</dt><dd>${t.remaining_target_cards}</dd>
          <dt>${this.t("manage.requiredNew")}</dt><dd>${t.required_new_per_day}</dd>
          <dt>${this.t("manage.reviews3Weeks")}</dt><dd>${t.reviews_per_day_in_3_weeks}</dd>
          <dt>${this.t("manage.reviews3Months")}</dt><dd>${t.reviews_per_day_in_3_months}</dd>
          <dt>${this.t("manage.notifications3Weeks")}</dt><dd>${t.notification_deliverable_in_3_weeks}</dd>
          <dt>${this.t("manage.notifications3Months")}</dt><dd>${t.notification_deliverable_in_3_months}</dd>
          <dt>${this.t("manage.sessionLoad3Weeks")}</dt><dd>${t.active_session_cards_in_3_weeks}</dd>
          <dt>${this.t("manage.sessionLoad3Months")}</dt><dd>${t.active_session_cards_in_3_months}</dd>
        </dl>
        ${t.warnings.length === 0 ? l : r`<ul>${t.warnings.map((i) => r`<li>${i}</li>`)}</ul>`}
        <div class="actions"><button class="primary" @click=${() => this.applyPlan(e)}>${this.t("manage.applyPlan")}</button></div>
      </div>
    `;
  }
  async applyPlan(e) {
    this.hass === void 0 || this.forecastPlan === void 0 || await this.mutate(() => li(this.hass, e.track_id, this.forecastPlan), this.t("manage.saved"));
  }
  renderPacks() {
    return r`
      <div class="grid">${this.packs.map((e) => r`
        <article class="card">
          <h2>${e.name}</h2><p>${e.version}</p>
          <p class="meta">${e.total_items} items · ${e.total_cards} cards</p>
        </article>`)}</div>
      ${this.canEditTrack() ? this.renderPackUpdates() : l}
    `;
  }
  renderPackUpdates() {
    const e = this.tracks.flatMap((t) => {
      const i = this.packs.find((s) => s.pack_version_id === t.pack_version_id);
      return i === void 0 ? [] : this.packs.filter((s) => s.pack_id === i.pack_id && s.pack_version_id !== i.pack_version_id).map((s) => ({ track: t, pack: s }));
    });
    return r`
      <article class="card">
        <h2>${this.t("manage.packUpdates")}</h2>
        ${e.length === 0 ? r`<p>${this.t("manage.noPackUpdates")}</p>` : r`
          <ul>${e.map(({ track: t, pack: i }) => r`<li>
            ${t.name}: ${t.pack_version_id} → ${i.pack_version_id}
            <button @click=${() => this.previewUpdate(t, i)}>${this.t("manage.preview")}</button>
          </li>`)}</ul>`}
        ${this.packDiff === void 0 ? l : r`
          <div class="notice">
            <strong>${this.t("manage.packDiff")}</strong>
            <p>+ ${this.packDiff.added_learning_item_ids.length} · − ${this.packDiff.removed_learning_item_ids.length} · ~ ${this.packDiff.changed_learning_item_ids.length}</p>
            <button class="primary" @click=${() => this.applyPackUpdate()}>${this.t("manage.integrate")}</button>
          </div>`}
      </article>
    `;
  }
  async previewUpdate(e, t) {
    if (this.hass !== void 0) {
      this.loading = !0;
      try {
        this.packDiff = await ri(this.hass, e.track_id, t.pack_version_id), this.packDiffTrack = e.track_id, this.packDiffTarget = t.pack_version_id;
      } catch (i) {
        this.errorMessage = i instanceof Error ? i.message : String(i);
      } finally {
        this.loading = !1;
      }
    }
  }
  async applyPackUpdate() {
    if (this.hass === void 0 || !this.packDiffTrack || !this.packDiffTarget) return;
    const e = this.packDiffTrack, t = this.packDiffTarget;
    await this.mutate(
      () => ni(this.hass, e, t),
      this.t("manage.packIntegrated")
    ), this.errorMessage === "" && (this.packDiff = void 0, this.packDiffTrack = "", this.packDiffTarget = "");
  }
  renderSettings() {
    if (!this.isOwner()) return r`<div class="card"><p>${this.t("manage.readOnly")}</p></div>`;
    const e = this.profile?.settings ?? {}, t = X(e, "quiet_hours"), i = X(e, "scheduler"), s = Array.isArray(i.active_windows) ? i.active_windows : [], n = typeof s[0] == "object" && s[0] !== null ? s[0] : {};
    return r`
      <article class="card">
        <h2>${this.t("manage.profileSettings")}</h2>
        <p class="muted">${this.t("manage.presetInitialOnly")}: ${this.profile?.preset}</p>
        <form class="form-grid" @submit=${(o) => {
      o.preventDefault();
      const d = new FormData(o.currentTarget);
      this.hass === void 0 || this.profile === void 0 || this.mutate(() => Ve(this.hass, this.profile.profile_id, {
        settings_patch: {
          session_length_cards: q(d.get("session"), 20, 1),
          max_new_per_day_cards: q(d.get("new"), 8, 0),
          daily_push_budget: q(d.get("push"), 6, 0),
          quiet_hours: {
            start: String(d.get("quietStart") ?? "22:00"),
            end: String(d.get("quietEnd") ?? "08:00")
          },
          scheduler: {
            ...i,
            active_windows: [{
              start: String(d.get("activeStart") ?? "08:00"),
              end: String(d.get("activeEnd") ?? "20:00")
            }]
          }
        }
      }), this.t("manage.saved"));
    }}>
          <label>${this.t("manage.sessionLength")}<input name="session" type="number" min="1" .value=${String(e.session_length_cards ?? 20)} /></label>
          <label>${this.t("manage.newPerDay")}<input name="new" type="number" min="0" .value=${String(e.max_new_per_day_cards ?? 8)} /></label>
          <label>${this.t("manage.pushBudget")}<input name="push" type="number" min="0" .value=${String(e.daily_push_budget ?? 6)} /></label>
          <label>${this.t("manage.quietStart")}<input name="quietStart" type="time" .value=${String(t.start ?? "22:00")} /></label>
          <label>${this.t("manage.quietEnd")}<input name="quietEnd" type="time" .value=${String(t.end ?? "08:00")} /></label>
          <label>${this.t("manage.activeStart")}<input name="activeStart" type="time" .value=${String(n.start ?? "08:00")} /></label>
          <label>${this.t("manage.activeEnd")}<input name="activeEnd" type="time" .value=${String(n.end ?? "20:00")} /></label>
          <div class="actions"><button class="primary" type="submit">${this.t("manage.save")}</button></div>
        </form>
      </article>
    `;
  }
};
Ae.styles = M`
    ${H}
    :host, .stack, .grid, .card, .form-grid, .actions, label, input, select, button {
      box-sizing: border-box;
      min-width: 0;
      max-width: 100%;
    }
    :host { display: block; }
    .stack { display: grid; gap: 16px; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit,minmax(280px,1fr)); gap: 14px; }
    .card {
      padding: 18px; border: 1px solid var(--divider-color); border-radius: 12px;
      background: var(--card-background-color,var(--primary-background-color));
    }
    .card h2, .card h3 { margin-top: 0; }
    .form-grid { display: grid; grid-template-columns: repeat(auto-fit,minmax(190px,1fr)); gap: 12px; }
    label { display: grid; gap: 5px; color: var(--secondary-text-color); font-size: .82rem; }
    input, select {
      width: 100%; padding: 9px; border: 1px solid var(--divider-color); border-radius: 8px;
      color: var(--primary-text-color); background: var(--card-background-color,var(--primary-background-color));
      font: inherit;
    }
    button {
      min-height: 40px; padding: 8px 12px; border: 1px solid var(--divider-color);
      border-radius: 8px; color: var(--primary-text-color); background: var(--secondary-background-color);
      font: inherit; cursor: pointer;
    }
    button.primary { border-color: var(--primary-color); color: var(--text-primary-color,white); background: var(--primary-color); }
    button:disabled { cursor: not-allowed; opacity: .55; }
    .actions { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
    .muted, .meta { color: var(--secondary-text-color); }
    .meta { font-size: .82rem; overflow-wrap: anywhere; }
    .notice, .error, .warning { padding: 12px; border-radius: 9px; background: var(--secondary-background-color); line-height: 1.45; }
    .error, .warning { color: var(--error-color,var(--primary-text-color)); }
    dl { display: grid; grid-template-columns: minmax(150px,auto) 1fr; gap: 6px 12px; margin: 0; }
    dt { color: var(--secondary-text-color); }
    dd { margin: 0; overflow-wrap: anywhere; }
    ul { padding-left: 20px; }
    @media (max-width: 600px) {
      .grid, .form-grid, dl { grid-template-columns: 1fr; }
      .actions { flex-direction: column; align-items: stretch; }
      button { width: 100%; }
    }
  `;
let g = Ae;
v([
  y({ attribute: !1 })
], g.prototype, "hass");
v([
  y({ attribute: !1 })
], g.prototype, "profile");
v([
  y({ attribute: !1 })
], g.prototype, "route");
v([
  c()
], g.prototype, "tracks");
v([
  c()
], g.prototype, "packs");
v([
  c()
], g.prototype, "notificationTargets");
v([
  c()
], g.prototype, "members");
v([
  c()
], g.prototype, "shareTargets");
v([
  c()
], g.prototype, "selectedTrackId");
v([
  c()
], g.prototype, "forecast");
v([
  c()
], g.prototype, "forecastPlan");
v([
  c()
], g.prototype, "packDiff");
v([
  c()
], g.prototype, "packDiffTrack");
v([
  c()
], g.prototype, "packDiffTarget");
v([
  c()
], g.prototype, "loading");
v([
  c()
], g.prototype, "errorMessage");
v([
  c()
], g.prototype, "notice");
globalThis.customElements !== void 0 && customElements.get("locklearn-management-view") === void 0 && customElements.define("locklearn-management-view", g);
var Si = Object.defineProperty, N = (a, e, t, i) => {
  for (var s = void 0, n = a.length - 1, o; n >= 0; n--)
    (o = a[n]) && (s = o(e, t, s) || s);
  return s && Si(e, t, s), s;
};
function ee(a) {
  if (a === null) return null;
  try {
    const e = new URL(a);
    return e.protocol === "https:" || e.protocol === "http:" ? e.href : null;
  } catch {
    return null;
  }
}
function qi(a) {
  if (a < 1024) return `${a} B`;
  const e = ["KiB", "MiB", "GiB"];
  let t = a / 1024, i = 0;
  for (; t >= 1024 && i < e.length - 1; )
    t /= 1024, i += 1;
  return `${t.toFixed(t >= 10 ? 1 : 2)} ${e[i]}`;
}
const Te = class Te extends A {
  constructor() {
    super(...arguments), this.admin = !1, this.datasets = [], this.loading = !1, this.errorMessage = "", this.notice = "", this.attributionPages = {};
  }
  connectedCallback() {
    super.connectedCallback(), this.load();
  }
  updated(e) {
    e.has("hass") && this.hass !== void 0 && this.load();
  }
  locale() {
    return W(
      this.hass?.locale?.language ?? this.hass?.language ?? globalThis.navigator?.language ?? "en"
    );
  }
  t(e) {
    return F(this.locale(), e);
  }
  async load() {
    if (this.hass !== void 0) {
      this.loading = !0, this.errorMessage = "";
      try {
        this.datasets = await ii(this.hass);
      } catch (e) {
        this.errorMessage = e instanceof Error ? e.message : String(e);
      } finally {
        this.loading = !1;
      }
    }
  }
  async refresh() {
    if (!(this.hass === void 0 || !this.admin)) {
      this.loading = !0, this.errorMessage = "", this.notice = "";
      try {
        this.datasets = await si(this.hass), this.notice = this.t("datasets.refreshed");
      } catch (e) {
        this.errorMessage = e instanceof Error ? e.message : String(e);
      } finally {
        this.loading = !1;
      }
    }
  }
  async install(e) {
    if (!(this.hass === void 0 || !this.admin)) {
      this.loading = !0, this.errorMessage = "", this.notice = "";
      try {
        const t = await ai(this.hass, e.dataset_id, e.available_version);
        this.datasets = t.statuses, this.notice = this.t("datasets.installed"), this.dispatchEvent(new CustomEvent("locklearn-refresh", { bubbles: !0, composed: !0 }));
      } catch (t) {
        this.errorMessage = t instanceof Error ? t.message : String(t);
      } finally {
        this.loading = !1;
      }
    }
  }
  attributionKey(e, t) {
    return `${e}\0${t}`;
  }
  async toggleAttributions(e, t) {
    if (this.hass === void 0) return;
    const i = this.attributionKey(e, t), s = this.attributionPages[i];
    if (s !== void 0) {
      this.attributionPages = {
        ...this.attributionPages,
        [i]: { ...s, expanded: !s.expanded }
      };
      return;
    }
    this.attributionPages = {
      ...this.attributionPages,
      [i]: { items: [], cursor: null, expanded: !0, loading: !0 }
    };
    try {
      const n = await Ke(this.hass, e, t);
      this.attributionPages = {
        ...this.attributionPages,
        [i]: { ...n, expanded: !0, loading: !1 }
      };
    } catch (n) {
      this.errorMessage = n instanceof Error ? n.message : String(n), this.attributionPages = {
        ...this.attributionPages,
        [i]: { items: [], cursor: null, expanded: !0, loading: !1 }
      };
    }
  }
  async loadMoreAttributions(e, t) {
    if (this.hass === void 0) return;
    const i = this.attributionKey(e, t), s = this.attributionPages[i];
    if (!(s === void 0 || s.cursor === null || s.loading)) {
      this.attributionPages = {
        ...this.attributionPages,
        [i]: { ...s, loading: !0 }
      };
      try {
        const n = await Ke(
          this.hass,
          e,
          t,
          s.cursor
        );
        this.attributionPages = {
          ...this.attributionPages,
          [i]: {
            items: [...s.items, ...n.items],
            cursor: n.cursor,
            expanded: !0,
            loading: !1
          }
        };
      } catch (n) {
        this.errorMessage = n instanceof Error ? n.message : String(n), this.attributionPages = {
          ...this.attributionPages,
          [i]: { ...s, loading: !1 }
        };
      }
    }
  }
  render() {
    return r`
      <section class="stack">
        <div>
          <h1>${this.t("datasets.title")}</h1>
          <p class="muted">${this.t("datasets.intro")}</p>
          ${this.admin ? r`<div class="actions">
                <button ?disabled=${this.loading} @click=${() => {
      this.refresh();
    }}>
                  ${this.t("datasets.check")}
                </button>
              </div>` : r`<p class="muted">${this.t("datasets.adminOnly")}</p>`}
        </div>
        ${this.errorMessage ? r`<div class="error" role="alert">${this.errorMessage}</div>` : l}
        ${this.notice ? r`<div class="notice" role="status">${this.notice}</div>` : l}
        ${this.loading && this.datasets.length === 0 ? r`<p>${this.t("datasets.loading")}</p>` : this.datasets.length === 0 ? r`<p>${this.t("datasets.empty")}</p>` : r`<div class="grid">${this.datasets.map((e) => this.renderDataset(e))}</div>`}
      </section>
    `;
  }
  renderDataset(e) {
    const t = e.error !== null || e.stale_sources.length > 0, i = ee(e.release_url);
    return r`
      <article class="card">
        <h2>${e.name}</h2>
        <dl>
          <dt>${this.t("datasets.state")}</dt><dd>${e.state}</dd>
          <dt>${this.t("datasets.installedVersion")}</dt><dd>${e.installed_version ?? "—"}</dd>
          <dt>${this.t("datasets.availableVersion")}</dt><dd>${e.available_version ?? "—"}</dd>
          <dt>${this.t("datasets.sourceAge")}</dt>
          <dd>${e.source_age_days === null ? "—" : `${e.source_age_days} ${this.t("datasets.days")}`}</dd>
          <dt>${this.t("datasets.disk")}</dt><dd>${qi(e.cache_bytes)}</dd>
          <dt>${this.t("datasets.builtAt")}</dt><dd>${e.built_at_utc ?? "—"}</dd>
        </dl>
        ${t ? r`<div class="warning" role="status">
              ${e.error ? r`<div>${e.error}</div>` : l}
              ${e.stale_sources.length > 0 ? r`<div>${this.t("datasets.stale")}: ${e.stale_sources.join(", ")}</div>` : l}
            </div>` : l}
        ${e.changelog ? r`<h3>${this.t("datasets.changelog")}</h3><p>${e.changelog}</p>` : l}
        ${i ? r`<p><a href=${i} target="_blank" rel="noopener noreferrer">${this.t("datasets.release")}</a></p>` : l}
        ${this.admin && (e.update_available || e.installed_version === null) && e.available_version ? r`<div class="actions">
              <button class="primary" ?disabled=${this.loading} @click=${() => {
      this.install(e);
    }}>
                ${e.installed_version === null ? this.t("datasets.install") : this.t("datasets.update")}
              </button>
            </div>` : l}
        <h3>${this.t("datasets.sources")}</h3>
        ${e.sources.length === 0 ? r`<p class="muted">${this.t("datasets.noSources")}</p>` : r`<ul>${e.sources.map((s) => {
      const n = ee(s.homepage), o = this.attributionKey(e.dataset_id, s.source_id), d = this.attributionPages[o];
      return r`
                <li>
                  <strong>${s.name}</strong> — ${s.provider}
                  <div class="meta">${s.attribution_template}</div>
                  <div class="meta">
                    ${this.t("datasets.upstream")}: ${s.upstream_version}
                    ${s.upstream_date ? r` · ${s.upstream_date}` : l}
                    · ${s.provenance_records} ${this.t("datasets.records")}
                    ${s.modified_records > 0 ? r` · ${s.modified_records} ${this.t("datasets.modified")}` : l}
                  </div>
                  ${n ? r`<a href=${n} target="_blank" rel="noopener noreferrer">${this.t("datasets.sourcePage")}</a>` : l}
                  ${s.attribution_records > 0 ? r`
                        <div class="actions">
                          <button
                            type="button"
                            @click=${() => {
        this.toggleAttributions(e.dataset_id, s.source_id);
      }}
                          >
                            ${d?.expanded ? this.t("datasets.hideAttributions") : this.t("datasets.showAttributions")}
                          </button>
                        </div>
                        ${d?.expanded ? r`
                              <div class="notice">
                                <strong>${this.t("datasets.individualAttributions")}</strong>
                                ${d.loading && d.items.length === 0 ? r`<p>${this.t("datasets.loading")}</p>` : r`<ul>
                                      ${d.items.map((h) => r`
                                        <li>
                                          ${h.attribution_text}
                                          <div class="meta">
                                            ${h.source_record_id ?? "—"}
                                            ${h.author ? r` · ${h.author}` : l}
                                            ${h.language_tag ? r` · ${h.language_tag}` : l}
                                            ${h.modified_from_source ? r` · ${this.t("datasets.modified")}` : l}
                                          </div>
                                        </li>
                                      `)}
                                    </ul>`}
                                ${d.cursor !== null ? r`<button
                                      type="button"
                                      ?disabled=${d.loading}
                                      @click=${() => {
        this.loadMoreAttributions(e.dataset_id, s.source_id);
      }}
                                    >
                                      ${this.t("datasets.loadMore")}
                                    </button>` : l}
                              </div>` : l}
                      ` : l}
                </li>
              `;
    })}</ul>`}
        <h3>${this.t("datasets.licenses")}</h3>
        ${e.licenses.length === 0 ? r`<p class="muted">${this.t("datasets.noLicenses")}</p>` : r`<ul>${e.licenses.map((s) => r`
              <li>
                <strong>${s.name}</strong>
                <span class="meta">(${s.license_id} · ${s.license_scope})</span>
                <div class="meta">
                  ${s.attribution_required ? this.t("datasets.attributionRequired") : this.t("datasets.attributionOptional")}
                  · ${s.commercial_use_allowed ? this.t("datasets.commercialAllowed") : this.t("datasets.commercialBlocked")}
                  ${s.share_alike ? r` · ${this.t("datasets.shareAlike")}` : l}
                </div>
                ${ee(s.source_url) ? r`<a href=${ee(s.source_url)} target="_blank" rel="noopener noreferrer">${this.t("datasets.licensePage")}</a>` : l}
              </li>
            `)}</ul>`}
      </article>
    `;
  }
};
Te.styles = M`
    ${H}
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
let T = Te;
N([
  y({ attribute: !1 })
], T.prototype, "hass");
N([
  y({ type: Boolean })
], T.prototype, "admin");
N([
  c()
], T.prototype, "datasets");
N([
  c()
], T.prototype, "loading");
N([
  c()
], T.prototype, "errorMessage");
N([
  c()
], T.prototype, "notice");
N([
  c()
], T.prototype, "attributionPages");
globalThis.customElements !== void 0 && customElements.get("locklearn-dataset-view") === void 0 && customElements.define("locklearn-dataset-view", T);
var Ai = Object.defineProperty, x = (a, e, t, i) => {
  for (var s = void 0, n = a.length - 1, o; n >= 0; n--)
    (o = a[n]) && (s = o(e, t, s) || s);
  return s && Ai(e, t, s), s;
};
function ge(a) {
  return a === null ? "—" : `${Math.round(a * 100)}%`;
}
function Ti(a, e = 14) {
  if (e <= 0) return [];
  const t = /* @__PURE__ */ new Map();
  for (const i of a) {
    const s = t.get(i.local_date);
    if (s === void 0) {
      t.set(i.local_date, { ...i });
      continue;
    }
    s.learning_exposures += i.learning_exposures, s.verified_retrievals += i.verified_retrievals, s.self_known += i.self_known, s.verified_correct += i.verified_correct, s.verified_wrong += i.verified_wrong, s.quiz_total += i.quiz_total, s.free_text_total += i.free_text_total, s.hints_used += i.hints_used, s.new_cards += i.new_cards, s.reviewed_cards += i.reviewed_cards, s.relearning_cards += i.relearning_cards, s.leech_cards += i.leech_cards, s.active_seconds += i.active_seconds;
  }
  return [...t.values()].sort((i, s) => i.local_date.localeCompare(s.local_date)).slice(-e).reverse();
}
function zi(a) {
  return {
    exposures: a.reduce((e, t) => e + t.learning_exposures, 0),
    verifiedRetrievals: a.reduce((e, t) => e + t.verified_retrievals, 0)
  };
}
function te(a) {
  return a?.role === "owner" || a?.role === "editor";
}
const ze = class ze extends A {
  constructor() {
    super(...arguments), this.difficulties = [], this.tracks = [], this.selectedTrackId = "", this.loading = !1, this.errorMessage = "", this.notice = "", this.mnemonicEdits = {}, this.busyCardKey = null, this.loadGeneration = 0;
  }
  updated(e) {
    (e.has("hass") || e.has("profile")) && this.load();
  }
  locale() {
    return W(
      this.hass?.locale?.language ?? this.hass?.language ?? globalThis.navigator?.language ?? "en"
    );
  }
  t(e) {
    return F(this.locale(), e);
  }
  async load() {
    if (this.hass === void 0 || this.profile === void 0) {
      this.stats = void 0, this.difficulties = [], this.tracks = [];
      return;
    }
    const e = ++this.loadGeneration, t = this.hass, i = this.profile.profile_id;
    this.loading = !0, this.errorMessage = "";
    try {
      const s = (await ct(t, i)).filter(
        (u) => u.status === "active"
      ), n = this.selectedTrackId && s.some((u) => u.track_id === this.selectedTrackId) ? this.selectedTrackId : "", [o, d] = await Promise.all([
        Jt(t, i, n || null),
        Yt(t, i, n || null)
      ]);
      if (e !== this.loadGeneration) return;
      this.tracks = s, this.selectedTrackId = n, this.stats = o, this.difficulties = d;
      const h = { ...this.mnemonicEdits };
      for (const u of d)
        h[u.card_key] === void 0 && (h[u.card_key] = u.annotations[0]?.note ?? "");
      this.mnemonicEdits = h;
    } catch (s) {
      if (e !== this.loadGeneration) return;
      this.errorMessage = s instanceof Error ? s.message : String(s);
    } finally {
      e === this.loadGeneration && (this.loading = !1);
    }
  }
  async selectTrack(e) {
    this.selectedTrackId = e.currentTarget.value, await this.load();
  }
  editMnemonic(e, t) {
    const i = t.currentTarget;
    i instanceof HTMLTextAreaElement && (this.mnemonicEdits = { ...this.mnemonicEdits, [e]: i.value });
  }
  async saveMnemonic(e) {
    if (this.hass === void 0 || this.profile === void 0 || !te(this.profile)) return;
    const t = (this.mnemonicEdits[e.card_key] ?? "").trim();
    if (t) {
      this.busyCardKey = e.card_key, this.errorMessage = "", this.notice = "";
      try {
        const i = e.annotations[0];
        i === void 0 ? await pt(this.hass, this.profile.profile_id, e.card_key, t) : await mi(
          this.hass,
          this.profile.profile_id,
          i.annotation_id,
          t
        ), this.notice = this.t("stats.mnemonicSaved"), await this.load();
      } catch (i) {
        this.errorMessage = i instanceof Error ? i.message : String(i);
      } finally {
        this.busyCardKey = null;
      }
    }
  }
  async startTargetedSession(e) {
    if (!(this.hass === void 0 || this.profile === void 0 || !te(this.profile))) {
      this.busyCardKey = e.card_key, this.errorMessage = "", this.notice = "";
      try {
        const t = await vi(
          this.hass,
          this.profile.profile_id,
          e.track_id,
          e.targeted_session_settings.requested_cards
        );
        this.dispatchEvent(
          new CustomEvent("locklearn-open-session", {
            detail: { session: t },
            bubbles: !0,
            composed: !0
          })
        );
      } catch (t) {
        this.errorMessage = t instanceof Error ? t.message : String(t);
      } finally {
        this.busyCardKey = null;
      }
    }
  }
  async reactivate(e) {
    if (!(this.hass === void 0 || this.profile === void 0 || !te(this.profile) || !(globalThis.confirm?.(this.t("stats.reactivateConfirm")) ?? !0))) {
      this.busyCardKey = e.card_key, this.errorMessage = "", this.notice = "";
      try {
        await fi(
          this.hass,
          this.profile.profile_id,
          e.track_id,
          e.card_key
        ), this.notice = this.t("stats.reactivated"), await this.load();
      } catch (i) {
        this.errorMessage = i instanceof Error ? i.message : String(i);
      } finally {
        this.busyCardKey = null;
      }
    }
  }
  render() {
    return this.profile === void 0 ? l : r`
      <section class="stack">
        <div>
          <h1>${this.t("stats.title")}</h1>
          <p class="muted">${this.t("stats.intro")}</p>
          <div class="toolbar">
            <label>
              <span>${this.t("stats.track")}</span>
              <select .value=${this.selectedTrackId} @change=${this.selectTrack}>
                <option value="">${this.t("stats.allTracks")}</option>
                ${this.tracks.map(
      (e) => r`<option value=${e.track_id}>${e.name}</option>`
    )}
              </select>
            </label>
          </div>
        </div>

        ${this.errorMessage ? r`<div class="error" role="alert">${this.errorMessage}</div>` : l}
        ${this.notice ? r`<div class="notice" role="status" aria-live="polite">${this.notice}</div>` : l}
        ${this.loading && this.stats === void 0 ? r`<p>${this.t("stats.loading")}</p>` : this.stats === void 0 ? l : this.renderStats(this.stats)}
      </section>
    `;
  }
  renderStats(e) {
    const t = e.recent_verified_accuracy, i = e.calibration, s = Ti(e.daily), n = zi(s);
    return r`
      <section class="grid" aria-label=${this.t("stats.verifiedGroup")}>
        <article class="card metric verified">
          <span>${this.t("stats.dueToday")}</span>
          <strong>${e.due_today}</strong>
        </article>
        <article class="card metric verified">
          <span>${this.t("stats.verifiedAccuracy")}</span>
          <strong>${ge(t.accuracy)}</strong>
          <div class="meta">${t.correct}/${t.total} · ${this.t("stats.verifiedOnly")}</div>
        </article>
        <article class="card metric verified">
          <span>${this.t("stats.latestRetention")}</span>
          <strong>${e.latest_verified_retention === null ? "—" : e.latest_verified_retention.retained ? this.t("stats.retained") : this.t("stats.notRetained")}</strong>
        </article>
        <article class="card metric">
          <span>${this.t("stats.streak")}</span>
          <strong>${e.streak.days}</strong>
          <div class="meta">${this.t("stats.days")}</div>
        </article>
      </section>

      <article class="card">
        <h2>${this.t("stats.states")}</h2>
        <div class="grid">
          ${this.stateMetric("stats.stateNew", e.states.new)}
          ${this.stateMetric("stats.stateLearning", e.states.learning)}
          ${this.stateMetric("stats.stateReview", e.states.review)}
          ${this.stateMetric("stats.stateRelearning", e.states.relearning)}
          ${this.stateMetric("stats.stateLeech", e.states.leech)}
        </div>
      </article>

      <article class="card verified">
        <h2>${this.t("stats.evidence")}</h2>
        <p>${this.t("stats.evidenceExplain")}</p>
        <div class="grid">
          <div class="metric">
            <span>${this.t("stats.exposures")}</span>
            <strong>${n.exposures}</strong>
            <div class="meta">${this.t("stats.notAccuracy")}</div>
          </div>
          <div class="metric">
            <span>${this.t("stats.verifiedRetrievals")}</span>
            <strong>${n.verifiedRetrievals}</strong>
            <div class="meta">${this.t("stats.countsAccuracy")}</div>
          </div>
        </div>
      </article>

      <article class="card">
        <h2>${this.t("stats.calibration")}</h2>
        <p>${this.t("stats.calibrationExplain")}</p>
        <div class="grid">
          ${this.stateMetric("stats.declaredKnown", i.declared_known_cards)}
          ${this.stateMetric("stats.verifiedLater", i.later_verified_cards)}
          ${this.stateMetric("stats.verifiedCorrectLater", i.later_verified_correct)}
          ${this.stateMetric("stats.verifiedWrongLater", i.later_verified_wrong)}
          ${this.stateMetric("stats.awaitingVerification", i.awaiting_verified_followup)}
          <div class="metric">
            <span>${this.t("stats.calibrationAccuracy")}</span>
            <strong>${ge(i.later_verified_accuracy)}</strong>
          </div>
        </div>
      </article>

      <article class="card secondary">
        <h2>${this.t("stats.mastery")}</h2>
        <div class="metric">
          <strong>${ge(e.mastery.value)}</strong>
          <div class="meta">${e.mastery.card_count} ${this.t("stats.cards")}</div>
        </div>
        <p>${this.t("stats.masteryExplain")}</p>
      </article>

      <article class="card">
        <h2>${this.t("stats.difficulties")}</h2>
        ${this.difficulties.length === 0 ? r`<p class="muted">${this.t("stats.noDifficulties")}</p>` : r`<ul>
              ${this.difficulties.map(
      (o) => r`
                  <li>
                    <strong>${o.card_key}</strong>
                    — ${this.t("stats.leechScore")} ${o.leech_score}
                    <div class="meta">
                      ${o.verified_correct_count} ${this.t("stats.correct")} ·
                      ${o.verified_wrong_count} ${this.t("stats.wrong")} ·
                      ${o.annotations.length > 0 ? this.t("stats.mnemonicPresent") : this.t("stats.mnemonicSuggested")}
                    </div>
                    ${o.confusions.length === 0 ? l : r`<div class="meta">
                          ${this.t("stats.confusions")}: ${o.confusions.map(
        (d) => `${d.expected_answer_id}→${d.chosen_answer_id} ×${d.count}`
      ).join(", ")}
                        </div>`}
                    ${o.annotations[0]?.note ? r`<p>${o.annotations[0].note}</p>` : l}
                    ${te(this.profile) ? r`
                          <label>
                            <span>${this.t("stats.personalMnemonic")}</span>
                            <textarea
                              .value=${this.mnemonicEdits[o.card_key] ?? ""}
                              @input=${(d) => this.editMnemonic(o.card_key, d)}
                            ></textarea>
                          </label>
                          <div class="actions">
                            <button
                              ?disabled=${this.busyCardKey !== null}
                              @click=${() => {
        this.saveMnemonic(o);
      }}
                            >
                              ${o.annotations.length > 0 ? this.t("stats.updateMnemonic") : this.t("stats.createMnemonic")}
                            </button>
                            <button
                              ?disabled=${this.busyCardKey !== null}
                              @click=${() => {
        this.startTargetedSession(o);
      }}
                            >
                              ${this.t("stats.targetedSession")}
                            </button>
                            <button
                              ?disabled=${this.busyCardKey !== null}
                              @click=${() => {
        this.reactivate(o);
      }}
                            >
                              ${this.t("stats.reactivate")}
                            </button>
                          </div>
                        ` : r`<div class="meta">${this.t("stats.readOnlyDifficulty")}</div>`}
                  </li>
                `
    )}
            </ul>`}
      </article>

      <article class="card">
        <h2>${this.t("stats.confusions")}</h2>
        ${e.confusions.length === 0 ? r`<p class="muted">${this.t("stats.noConfusions")}</p>` : r`<ul>
              ${e.confusions.map(
      (o) => r`
                  <li>
                    <strong>${o.card_key}</strong>
                    <div class="meta">
                      ${this.t("stats.expected")} ${o.expected_answer_id} →
                      ${this.t("stats.chosen")} ${o.chosen_answer_id} ·
                      ${o.count}×
                    </div>
                  </li>
                `
    )}
            </ul>`}
      </article>

      <article class="card">
        <h2>${this.t("stats.recentActivity")}</h2>
        ${s.length === 0 ? r`<p class="muted">${this.t("stats.noActivity")}</p>` : r`<div class="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>${this.t("stats.date")}</th>
                    <th>${this.t("stats.exposures")}</th>
                    <th>${this.t("stats.verifiedRetrievals")}</th>
                    <th>${this.t("stats.correct")}</th>
                    <th>${this.t("stats.wrong")}</th>
                    <th>${this.t("stats.new")}</th>
                    <th>${this.t("stats.reviewed")}</th>
                    <th>${this.t("stats.relearning")}</th>
                  </tr>
                </thead>
                <tbody>
                  ${s.map(
      (o) => r`
                      <tr>
                        <td>${o.local_date}</td>
                        <td>${o.learning_exposures}</td>
                        <td>${o.verified_retrievals}</td>
                        <td>${o.verified_correct}</td>
                        <td>${o.verified_wrong}</td>
                        <td>${o.new_cards}</td>
                        <td>${o.reviewed_cards}</td>
                        <td>${o.relearning_cards}</td>
                      </tr>
                    `
    )}
                </tbody>
              </table>
            </div>`}
      </article>
    `;
  }
  stateMetric(e, t) {
    return r`<div class="metric"><span>${this.t(e)}</span><strong>${t}</strong></div>`;
  }
};
ze.styles = M`
    ${H}
    :host, section, article, div, select { box-sizing: border-box; min-width: 0; max-width: 100%; }
    :host { display: block; }
    .stack { display: grid; gap: 18px; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit,minmax(190px,1fr)); gap: 12px; }
    .card { padding: 16px; border: 1px solid var(--divider-color); border-radius: 12px;
      background: var(--card-background-color,var(--primary-background-color)); overflow-wrap: anywhere; }
    .metric strong { display: block; font-size: 1.55rem; margin-top: 4px; }
    .muted, .meta { color: var(--secondary-text-color); }
    .meta { font-size: .86rem; }
    .verified { border-inline-start: 4px solid var(--primary-color); }
    .secondary { opacity: .92; }
    .notice, .error { padding: 12px; border-radius: 9px; background: var(--secondary-background-color); }
    .error { color: var(--error-color,var(--primary-text-color)); }
    .toolbar { display: flex; flex-wrap: wrap; gap: 10px; align-items: end; }
    label { display: grid; gap: 5px; }
    select, textarea, button { font: inherit; }
    select { min-height: 40px; padding: 7px; border: 1px solid var(--divider-color);
      border-radius: 8px; color: var(--primary-text-color);
      background: var(--card-background-color,var(--primary-background-color)); }
    textarea { width: 100%; min-height: 70px; resize: vertical; padding: 8px;
      border: 1px solid var(--divider-color); border-radius: 8px;
      color: var(--primary-text-color); background: var(--primary-background-color); }
    button { min-height: 40px; padding: 8px 12px; border: 1px solid var(--divider-color);
      border-radius: 8px; color: var(--primary-text-color);
      background: var(--secondary-background-color); cursor: pointer; }
    button:disabled { opacity: .55; cursor: not-allowed; }
    .actions { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; }
    table { width: 100%; border-collapse: collapse; font-size: .9rem; }
    th, td { padding: 7px 8px; text-align: left; border-bottom: 1px solid var(--divider-color); }
    .table-wrap { overflow-x: auto; }
    ul { padding-left: 20px; }
    h1, h2, h3, p { overflow-wrap: anywhere; }
    @media (max-width: 600px) {
      .grid { grid-template-columns: 1fr; }
      .toolbar, label, select { width: 100%; }
    }
  `;
let _ = ze;
x([
  y({ attribute: !1 })
], _.prototype, "hass");
x([
  y({ attribute: !1 })
], _.prototype, "profile");
x([
  c()
], _.prototype, "stats");
x([
  c()
], _.prototype, "difficulties");
x([
  c()
], _.prototype, "tracks");
x([
  c()
], _.prototype, "selectedTrackId");
x([
  c()
], _.prototype, "loading");
x([
  c()
], _.prototype, "errorMessage");
x([
  c()
], _.prototype, "notice");
x([
  c()
], _.prototype, "mnemonicEdits");
x([
  c()
], _.prototype, "busyCardKey");
globalThis.customElements !== void 0 && customElements.get("locklearn-stats-view") === void 0 && customElements.define("locklearn-stats-view", _);
const Ye = [
  { route: "home", labelKey: "nav.home" },
  { route: "learn", labelKey: "nav.learn" },
  { route: "quiz", labelKey: "nav.quiz" },
  { route: "exam", labelKey: "nav.exam" },
  { route: "stats", labelKey: "nav.stats" },
  { route: "profiles", labelKey: "nav.profiles" },
  { route: "tracks", labelKey: "nav.tracks" },
  { route: "packs", labelKey: "nav.packs" },
  { route: "sources", labelKey: "nav.sources" }
], Pi = [
  { route: "settings", labelKey: "nav.settings" }
];
function be(a) {
  return a.length === 0 ? [] : new Set(a.map((t) => t.role)).has("owner") ? [...Ye, ...Pi] : Ye;
}
function ie(a, e) {
  return be(e).some((t) => t.route === a);
}
function Ei(a) {
  return {
    mine: a.filter((e) => e.role === "owner"),
    shared: a.filter((e) => e.role !== "owner")
  };
}
function Ze(a, e) {
  const t = e.personal_profile?.profile_id;
  if (t !== void 0 && a.some((s) => s.profile_id === t))
    return t;
  const i = a.find((s) => s.role === "owner");
  return i !== void 0 ? i.profile_id : a[0]?.profile_id ?? null;
}
function Mi(a) {
  if (a === void 0) return { kind: "define" };
  const e = typeof a.locklearnFrontendProtocol == "number" ? a.locklearnFrontendProtocol : null;
  return e === I ? { kind: "reuse" } : {
    kind: "reload",
    existingProtocol: e,
    frontendProtocol: I
  };
}
function Ci(a, e, t) {
  return !a && e && t;
}
const Ri = [
  "home",
  "learn",
  "quiz",
  "exam",
  "stats",
  "profiles",
  "tracks",
  "packs",
  "sources",
  "settings"
], Di = "home";
function me(a) {
  const t = a.replace(/^\/+|\/+$/g, "").split("/").filter(Boolean), i = t[0] === "locklearn" ? t[1] : t[0];
  return Ri.includes(i) ? i : Di;
}
function Ii(a) {
  return a === "home" ? "/locklearn" : `/locklearn/${a}`;
}
function fe(a) {
  const e = Ii(a);
  globalThis.location?.pathname !== e && (globalThis.history?.pushState({}, "", e), globalThis.dispatchEvent?.(new PopStateEvent("popstate")));
}
var Ni = Object.defineProperty, S = (a, e, t, i) => {
  for (var s = void 0, n = a.length - 1, o; n >= 0; n--)
    (o = a[n]) && (s = o(e, t, s) || s);
  return s && Ni(e, t, s), s;
};
const Xe = "locklearn-hard-reload-required", oe = class oe extends A {
  constructor() {
    super(...arguments), this.status = "loading", this.activeRoute = me(
      globalThis.location?.pathname ?? "/locklearn"
    ), this.profiles = [], this.selectedProfileId = null, this.dashboardLoading = !1, this.dashboardError = "", this.errorMessage = "", this.loadGeneration = 0, this.dashboardGeneration = 0, this.initialLoadStarted = !1, this.handlePopState = () => {
      const e = me(globalThis.location?.pathname ?? "/locklearn");
      this.activeRoute = ie(e, this.profiles) ? e : "home";
    };
  }
  connectedCallback() {
    super.connectedCallback(), globalThis.addEventListener?.("popstate", this.handlePopState);
  }
  disconnectedCallback() {
    globalThis.removeEventListener?.("popstate", this.handlePopState), super.disconnectedCallback();
  }
  updated(e) {
    Ci(
      this.initialLoadStarted,
      e.has("hass"),
      this.hass !== void 0
    ) && (this.initialLoadStarted = !0, this.load());
  }
  locale() {
    const e = this.hass?.locale?.language ?? this.hass?.language ?? globalThis.navigator?.language ?? "en";
    return W(e);
  }
  t(e) {
    return F(this.locale(), e);
  }
  async load() {
    if (this.hass === void 0) return;
    const e = ++this.loadGeneration;
    this.status = "loading", this.errorMessage = "";
    try {
      const t = await Wt(this.hass), i = await Fe(this.hass);
      if (e !== this.loadGeneration) return;
      this.bootstrapState = t, this.profiles = i, this.selectedProfileId = Ze(i, t);
      const s = me(globalThis.location?.pathname ?? t.panel_path);
      this.activeRoute = ie(s, i) ? s : "home", this.status = "ready", this.loadDashboard();
    } catch (t) {
      if (e !== this.loadGeneration) return;
      if (t instanceof lt) {
        this.bootstrapState = {
          frontend_protocol: t.backendProtocol,
          backend_version: t.backendVersion,
          panel_path: "/locklearn",
          authenticated_user_id: "",
          is_admin: !1,
          personal_profile: null
        }, this.status = "protocol-mismatch";
        return;
      }
      this.errorMessage = t instanceof Error ? t.message : String(t), this.status = "error";
    }
  }
  selectRoute(e) {
    ie(e, this.profiles) && (this.activeRoute = e, fe(e));
  }
  selectProfile(e) {
    const t = e.currentTarget;
    if (!(t instanceof HTMLSelectElement)) return;
    const i = t.value;
    this.profiles.some((s) => s.profile_id === i) && (this.selectedProfileId = i, this.handoffSession = void 0, this.loadDashboard());
  }
  openTargetedSession(e) {
    const t = e.detail?.session;
    t === void 0 || this.selectedProfileId === null || t.profile_id !== this.selectedProfileId || (this.handoffSession = t, this.activeRoute = "learn", fe("learn"));
  }
  clearSessionHandoff() {
    this.handoffSession = void 0;
  }
  async refreshManagement() {
    if (this.hass === void 0) return;
    const e = this.selectedProfileId;
    try {
      const t = await Fe(this.hass);
      this.profiles = t, this.selectedProfileId = e !== null && t.some((i) => i.profile_id === e) ? e : this.bootstrapState === void 0 ? t[0]?.profile_id ?? null : Ze(t, this.bootstrapState), ie(this.activeRoute, t) || (this.activeRoute = "home", fe("home")), await this.loadDashboard();
    } catch (t) {
      this.errorMessage = t instanceof Error ? t.message : String(t);
    }
  }
  async loadDashboard() {
    if (this.hass === void 0 || this.selectedProfileId === null) {
      this.dashboard = void 0, this.dashboardError = "";
      return;
    }
    const e = ++this.dashboardGeneration;
    this.dashboardLoading = !0, this.dashboardError = "";
    try {
      const t = await ci(this.hass, this.selectedProfileId);
      if (e !== this.dashboardGeneration) return;
      this.dashboard = t;
    } catch (t) {
      if (e !== this.dashboardGeneration) return;
      this.dashboard = void 0, this.dashboardError = t instanceof Error ? t.message : String(t);
    } finally {
      e === this.dashboardGeneration && (this.dashboardLoading = !1);
    }
  }
  hardReload() {
    globalThis.location?.reload();
  }
  render() {
    if (this.status === "loading")
      return this.renderState(this.t("state.loading"));
    if (this.status === "protocol-mismatch")
      return r`
        <main>
          <section class="state-card" role="alert">
            <h1>${this.t("state.protocol.title")}</h1>
            <p>${this.t("state.protocol.body")}</p>
            <button class="primary-button" @click=${this.hardReload}>
              ${this.t("state.protocol.reload")}
            </button>
            <div class="meta">
              frontend protocol ${I} · backend protocol
              ${this.bootstrapState?.frontend_protocol ?? "?"} · backend
              ${this.bootstrapState?.backend_version ?? "?"}
            </div>
          </section>
        </main>
      `;
    if (this.status === "error")
      return r`
        <main>
          <section class="state-card" role="alert">
            <h1>${this.t("state.error")}</h1>
            <p>${this.errorMessage}</p>
            <button class="primary-button" @click=${() => {
        this.load();
      }}>
              ${this.t("state.retry")}
            </button>
          </section>
        </main>
      `;
    const e = be(this.profiles), t = Ei(this.profiles);
    return r`
      <div class="shell">
        <header>
          <div class="brand">${this.t("app.title")}</div>
          ${this.profiles.length === 0 ? l : r`<label class="profile-switcher">
                <span>${this.t("profile.select")}</span>
                <select
                  .value=${this.selectedProfileId ?? ""}
                  @change=${this.selectProfile}
                >
                  ${t.mine.length === 0 ? l : r`<optgroup label=${this.t("profile.mine")}>
                        ${t.mine.map(
      (i) => r`<option value=${i.profile_id}>${i.name}</option>`
    )}
                      </optgroup>`}
                  ${t.shared.length === 0 ? l : r`<optgroup label=${this.t("profile.shared")}>
                        ${t.shared.map(
      (i) => r`<option value=${i.profile_id}>${i.name}</option>`
    )}
                      </optgroup>`}
                </select>
              </label>`}
          <nav aria-label="LockLearn">
            ${e.map(
      (i) => r`
                <button
                  class="nav-button"
                  aria-current=${this.activeRoute === i.route ? "page" : l}
                  @click=${() => this.selectRoute(i.route)}
                >
                  ${this.t(i.labelKey)}
                </button>
              `
    )}
          </nav>
        </header>
        <main>
          ${this.profiles.length === 0 ? r`<locklearn-management-view
                .hass=${this.hass}
                .profile=${void 0}
                .route=${"profiles"}
                @locklearn-refresh=${() => {
      this.refreshManagement();
    }}
              ></locklearn-management-view>` : this.activeRoute === "home" ? this.renderHome() : this.activeRoute === "learn" ? r`<locklearn-learn-view
                    .hass=${this.hass}
                    .profile=${this.profiles.find(
      (i) => i.profile_id === this.selectedProfileId
    )}
                    .dashboard=${this.dashboard}
                    .externalSession=${this.handoffSession}
                    @locklearn-session-handoff-consumed=${this.clearSessionHandoff}
                  ></locklearn-learn-view>` : this.activeRoute === "quiz" ? r`<locklearn-quiz-view
                      .hass=${this.hass}
                      .profile=${this.profiles.find(
      (i) => i.profile_id === this.selectedProfileId
    )}
                      .dashboard=${this.dashboard}
                    ></locklearn-quiz-view>` : this.activeRoute === "stats" ? r`<locklearn-stats-view
                        .hass=${this.hass}
                        .profile=${this.profiles.find(
      (i) => i.profile_id === this.selectedProfileId
    )}
                        @locklearn-open-session=${this.openTargetedSession}
                      ></locklearn-stats-view>` : this.activeRoute === "sources" ? r`<locklearn-dataset-view
                        .hass=${this.hass}
                        .admin=${this.bootstrapState?.is_admin ?? !1}
                        @locklearn-refresh=${() => {
      this.refreshManagement();
    }}
                      ></locklearn-dataset-view>` : ["profiles", "tracks", "packs", "settings"].includes(this.activeRoute) ? r`<locklearn-management-view
                        .hass=${this.hass}
                        .profile=${this.profiles.find(
      (i) => i.profile_id === this.selectedProfileId
    )}
                        .route=${this.activeRoute}
                        @locklearn-refresh=${() => {
      this.refreshManagement();
    }}
                      ></locklearn-management-view>` : r`<section class="page">
                    <h1>${this.routeLabel(this.activeRoute)}</h1>
                    <p>${this.t("route.placeholder")}</p>
                  </section>`}
        </main>
      </div>
    `;
  }
  renderHome() {
    return this.dashboardLoading ? r`<section class="page"><p>${this.t("dashboard.loading")}</p></section>` : this.dashboardError ? r`<section class="page" role="alert">
        <h1>${this.t("dashboard.error")}</h1>
        <p>${this.dashboardError}</p>
      </section>` : this.dashboard === void 0 ? r`<section class="page"><p>${this.t("dashboard.noTracks")}</p></section>` : r`
      <section>
        <div class="home-header">
          <h1>${this.dashboard.profile.name}</h1>
        </div>
        ${this.dashboard.tracks.length === 0 ? r`<section class="page"><p>${this.t("dashboard.noTracks")}</p></section>` : r`<div class="track-grid">
              ${this.dashboard.tracks.map((e) => r`
                <article class="track-card">
                  <h2>${e.name}</h2>
                  <div class="track-languages">
                    ${e.source_language} → ${e.target_language}
                  </div>
                  <div class="metrics">
                    <div class="metric">
                      <div class="metric-label">${this.t("dashboard.dueToday")}</div>
                      <div class="metric-value">${e.due_today}</div>
                    </div>
                    <div class="metric">
                      <div class="metric-label">${this.t("dashboard.accuracy")}</div>
                      <div class="metric-value">${this.formatAccuracy(e.recent_verified_accuracy.accuracy)}</div>
                      <div class="metric-detail">
                        ${e.recent_verified_accuracy.correct}/${e.recent_verified_accuracy.total}
                      </div>
                    </div>
                    <div class="metric">
                      <div class="metric-label">${this.t("dashboard.latestVerified")}</div>
                      <div class="metric-value">
                        ${e.recent_verified_retention === null ? this.t("dashboard.noVerified") : e.recent_verified_retention.retained ? this.t("dashboard.retained") : this.t("dashboard.notRetained")}
                      </div>
                      ${e.recent_verified_retention === null ? l : r`<div class="metric-detail">
                            ${this.formatDateTime(
      e.recent_verified_retention.created_at_utc,
      this.dashboard?.profile.timezone
    )}
                          </div>`}
                    </div>
                    <div class="metric">
                      <div class="metric-label">${this.t("dashboard.lastSession")}</div>
                      <div class="metric-value">
                        ${e.last_session === null ? this.t("dashboard.noSession") : `${e.last_session.answered_count}/${e.last_session.question_count} ${this.t("dashboard.answered")}`}
                      </div>
                      ${e.last_session === null ? l : r`<div class="metric-detail">
                            ${this.formatDateTime(
      e.last_session.completed_at_utc ?? e.last_session.last_activity_at_utc,
      this.dashboard?.profile.timezone
    )}
                          </div>`}
                    </div>
                    <div class="metric">
                      <div class="metric-label">${this.t("dashboard.nextNotification")}</div>
                      <div class="metric-value">
                        ${e.next_notification === null ? this.t("dashboard.noNotification") : this.formatDateTime(
      e.next_notification.effective_for_utc,
      this.dashboard?.profile.timezone
    )}
                      </div>
                    </div>
                  </div>
                </article>
              `)}
            </div>`}
      </section>
    `;
  }
  formatAccuracy(e) {
    return e === null ? "—" : new Intl.NumberFormat(this.locale(), {
      style: "percent",
      maximumFractionDigits: 0
    }).format(e);
  }
  formatDateTime(e, t) {
    const i = new Date(e);
    return Number.isNaN(i.getTime()) ? "—" : new Intl.DateTimeFormat(this.locale(), {
      dateStyle: "short",
      timeStyle: "short",
      ...t === void 0 ? {} : { timeZone: t }
    }).format(i);
  }
  renderState(e) {
    return r`<main><section class="state-card"><p>${e}</p></section></main>`;
  }
  routeLabel(e) {
    const t = be(this.profiles).find((i) => i.route === e);
    return t === void 0 ? this.t("nav.home") : this.t(t.labelKey);
  }
};
oe.locklearnFrontendProtocol = I, oe.styles = M`
    ${H}
    :host {
      display: block;
      min-height: 100%;
      box-sizing: border-box;
      color: var(--primary-text-color);
      background: var(--primary-background-color);
      font-family: var(--paper-font-body1_-_font-family, system-ui, sans-serif);
    }

    .shell {
      min-height: 100vh;
      display: grid;
      grid-template-rows: auto 1fr;
    }

    header {
      position: sticky;
      top: 0;
      z-index: 1;
      display: flex;
      align-items: center;
      gap: 20px;
      min-height: 64px;
      padding: 0 24px;
      border-bottom: 1px solid var(--divider-color);
      background: var(--card-background-color, var(--primary-background-color));
    }

    .brand {
      font-size: 1.15rem;
      font-weight: 700;
      white-space: nowrap;
    }

    .profile-switcher {
      display: grid;
      gap: 2px;
      min-width: 170px;
      color: var(--secondary-text-color);
      font-size: 0.75rem;
    }

    .profile-switcher select {
      min-width: 0;
      padding: 7px 28px 7px 9px;
      border: 1px solid var(--divider-color);
      border-radius: 8px;
      color: var(--primary-text-color);
      background: var(--card-background-color, var(--primary-background-color));
      font: inherit;
      font-size: 0.9rem;
    }

    nav {
      display: flex;
      align-items: center;
      gap: 4px;
      min-width: 0;
      overflow-x: auto;
      scrollbar-width: thin;
    }

    button {
      font: inherit;
    }

    .nav-button,
    .primary-button {
      border: 0;
      border-radius: 8px;
      cursor: pointer;
    }

    .nav-button {
      padding: 9px 11px;
      color: var(--secondary-text-color);
      background: transparent;
      white-space: nowrap;
    }

    .nav-button[aria-current="page"] {
      color: var(--primary-text-color);
      background: var(--secondary-background-color);
      font-weight: 600;
    }

    main {
      width: min(1100px, calc(100% - 32px));
      margin: 0 auto;
      padding: 28px 0 48px;
      box-sizing: border-box;
    }

    .state-card,
    .page {
      padding: 24px;
      border-radius: 12px;
      background: var(--card-background-color, var(--primary-background-color));
      box-shadow: var(--ha-card-box-shadow, none);
    }

    .state-card {
      max-width: 680px;
      margin: 48px auto 0;
    }

    .home-header {
      display: flex;
      align-items: end;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 18px;
    }

    .home-header h1 {
      margin: 0;
    }

    .track-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 16px;
    }

    .track-card {
      padding: 20px;
      border: 1px solid var(--divider-color);
      border-radius: 12px;
      background: var(--card-background-color, var(--primary-background-color));
      box-shadow: var(--ha-card-box-shadow, none);
    }

    .track-card h2 {
      margin: 0;
      font-size: 1.15rem;
    }

    .track-languages {
      margin-top: 4px;
      color: var(--secondary-text-color);
      font-size: 0.85rem;
    }

    .metrics {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
      margin-top: 18px;
    }

    .metric {
      min-width: 0;
      padding: 12px;
      border-radius: 10px;
      background: var(--secondary-background-color);
    }

    .metric-label {
      color: var(--secondary-text-color);
      font-size: 0.78rem;
    }

    .metric-value {
      margin-top: 4px;
      font-weight: 650;
      line-height: 1.25;
    }

    .metric-detail {
      margin-top: 4px;
      color: var(--secondary-text-color);
      font-size: 0.78rem;
      line-height: 1.3;
    }

    .state-card h1,
    .page h1 {
      margin-top: 0;
    }

    .state-card p,
    .page p {
      color: var(--secondary-text-color);
      line-height: 1.5;
    }

    .primary-button {
      margin-top: 8px;
      padding: 10px 14px;
      color: var(--text-primary-color, white);
      background: var(--primary-color);
    }

    .meta {
      margin-top: 18px;
      font-size: 0.85rem;
      color: var(--secondary-text-color);
    }

    @media (max-width: 720px) {
      header {
        align-items: flex-start;
        flex-direction: column;
        gap: 8px;
        padding: 14px 16px 10px;
      }

      .profile-switcher {
        width: 100%;
      }

      .profile-switcher select {
        width: 100%;
      }

      nav {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        width: 100%;
        overflow-x: visible;
      }

      .nav-button {
        width: 100%;
        min-width: 0;
        padding-inline: 8px;
        overflow: hidden;
        text-overflow: ellipsis;
      }

      main {
        width: min(100% - 24px, 1100px);
        padding-top: 18px;
      }
    }
  `;
let k = oe;
S([
  y({ attribute: !1 })
], k.prototype, "hass");
S([
  c()
], k.prototype, "status");
S([
  c()
], k.prototype, "activeRoute");
S([
  c()
], k.prototype, "bootstrapState");
S([
  c()
], k.prototype, "profiles");
S([
  c()
], k.prototype, "selectedProfileId");
S([
  c()
], k.prototype, "dashboard");
S([
  c()
], k.prototype, "dashboardLoading");
S([
  c()
], k.prototype, "dashboardError");
S([
  c()
], k.prototype, "errorMessage");
S([
  c()
], k.prototype, "handoffSession");
function Li(a) {
  if (typeof document > "u" || document.getElementById(Xe) !== null) return;
  const e = document.createElement("div");
  e.id = Xe, e.setAttribute("role", "alert"), e.style.cssText = "position:fixed;inset:0;z-index:2147483647;display:grid;place-items:center;padding:24px;background:var(--primary-background-color,#fff);color:var(--primary-text-color,#111);font-family:system-ui,sans-serif";
  const t = document.createElement("div");
  t.style.cssText = "max-width:680px;padding:24px;border:1px solid var(--divider-color,#ddd);border-radius:12px;background:var(--card-background-color,#fff)";
  const i = document.createElement("h1");
  i.textContent = "LockLearn was updated";
  const s = document.createElement("p");
  s.textContent = "An older LockLearn panel is still loaded in this browser. Perform a full browser reload before continuing.";
  const n = document.createElement("p");
  n.textContent = `loaded protocol ${a ?? "unknown"} · current protocol ${I}`;
  const o = document.createElement("button");
  o.textContent = "Reload now", o.addEventListener("click", () => globalThis.location?.reload()), t.append(i, s, n, o), e.append(t), document.body.append(e);
}
const Ui = customElements.get(
  "locklearn-panel"
), ve = Mi(Ui);
ve.kind === "define" ? customElements.define("locklearn-panel", k) : ve.kind === "reload" && Li(ve.existingProtocol);
export {
  k as LockLearnPanel
};
