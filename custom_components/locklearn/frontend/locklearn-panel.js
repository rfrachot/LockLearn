const q = globalThis, J = q.ShadowRoot && (q.ShadyCSS === void 0 || q.ShadyCSS.nativeShadow) && "adoptedStyleSheets" in Document.prototype && "replace" in CSSStyleSheet.prototype, Y = /* @__PURE__ */ Symbol(), se = /* @__PURE__ */ new WeakMap();
let ye = class {
  constructor(e, t, i) {
    if (this._$cssResult$ = !0, i !== Y) throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");
    this.cssText = e, this.t = t;
  }
  get styleSheet() {
    let e = this.o;
    const t = this.t;
    if (J && e === void 0) {
      const i = t !== void 0 && t.length === 1;
      i && (e = se.get(t)), e === void 0 && ((this.o = e = new CSSStyleSheet()).replaceSync(this.cssText), i && se.set(t, e));
    }
    return e;
  }
  toString() {
    return this.cssText;
  }
};
const Te = (r) => new ye(typeof r == "string" ? r : r + "", void 0, Y), _e = (r, ...e) => {
  const t = r.length === 1 ? r[0] : e.reduce((i, s, o) => i + ((n) => {
    if (n._$cssResult$ === !0) return n.cssText;
    if (typeof n == "number") return n;
    throw Error("Value passed to 'css' function must be a 'css' function result: " + n + ". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.");
  })(s) + r[o + 1], r[0]);
  return new ye(t, r, Y);
}, Ce = (r, e) => {
  if (J) r.adoptedStyleSheets = e.map((t) => t instanceof CSSStyleSheet ? t : t.styleSheet);
  else for (const t of e) {
    const i = document.createElement("style"), s = q.litNonce;
    s !== void 0 && i.setAttribute("nonce", s), i.textContent = t.cssText, r.appendChild(i);
  }
}, re = J ? (r) => r : (r) => r instanceof CSSStyleSheet ? ((e) => {
  let t = "";
  for (const i of e.cssRules) t += i.cssText;
  return Te(t);
})(r) : r;
const { is: Me, defineProperty: Re, getOwnPropertyDescriptor: Ue, getOwnPropertyNames: Ie, getOwnPropertySymbols: Le, getPrototypeOf: Ne } = Object, j = globalThis, oe = j.trustedTypes, Oe = oe ? oe.emptyScript : "", He = j.reactiveElementPolyfillSupport, M = (r, e) => r, z = { toAttribute(r, e) {
  switch (e) {
    case Boolean:
      r = r ? Oe : null;
      break;
    case Object:
    case Array:
      r = r == null ? r : JSON.stringify(r);
  }
  return r;
}, fromAttribute(r, e) {
  let t = r;
  switch (e) {
    case Boolean:
      t = r !== null;
      break;
    case Number:
      t = r === null ? null : Number(r);
      break;
    case Object:
    case Array:
      try {
        t = JSON.parse(r);
      } catch {
        t = null;
      }
  }
  return t;
} }, Z = (r, e) => !Me(r, e), ne = { attribute: !0, type: String, converter: z, reflect: !1, useDefault: !1, hasChanged: Z };
Symbol.metadata ??= /* @__PURE__ */ Symbol("metadata"), j.litPropertyMetadata ??= /* @__PURE__ */ new WeakMap();
let S = class extends HTMLElement {
  static addInitializer(e) {
    this._$Ei(), (this.l ??= []).push(e);
  }
  static get observedAttributes() {
    return this.finalize(), this._$Eh && [...this._$Eh.keys()];
  }
  static createProperty(e, t = ne) {
    if (t.state && (t.attribute = !1), this._$Ei(), this.prototype.hasOwnProperty(e) && ((t = Object.create(t)).wrapped = !0), this.elementProperties.set(e, t), !t.noAccessor) {
      const i = /* @__PURE__ */ Symbol(), s = this.getPropertyDescriptor(e, i, t);
      s !== void 0 && Re(this.prototype, e, s);
    }
  }
  static getPropertyDescriptor(e, t, i) {
    const { get: s, set: o } = Ue(this.prototype, e) ?? { get() {
      return this[t];
    }, set(n) {
      this[t] = n;
    } };
    return { get: s, set(n) {
      const c = s?.call(this);
      o?.call(this, n), this.requestUpdate(e, c, i);
    }, configurable: !0, enumerable: !0 };
  }
  static getPropertyOptions(e) {
    return this.elementProperties.get(e) ?? ne;
  }
  static _$Ei() {
    if (this.hasOwnProperty(M("elementProperties"))) return;
    const e = Ne(this);
    e.finalize(), e.l !== void 0 && (this.l = [...e.l]), this.elementProperties = new Map(e.elementProperties);
  }
  static finalize() {
    if (this.hasOwnProperty(M("finalized"))) return;
    if (this.finalized = !0, this._$Ei(), this.hasOwnProperty(M("properties"))) {
      const t = this.properties, i = [...Ie(t), ...Le(t)];
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
      for (const s of i) t.unshift(re(s));
    } else e !== void 0 && t.push(re(e));
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
    return Ce(e, this.constructor.elementStyles), e;
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
      const o = (i.converter?.toAttribute !== void 0 ? i.converter : z).toAttribute(t, i.type);
      this._$Em = e, o == null ? this.removeAttribute(s) : this.setAttribute(s, o), this._$Em = null;
    }
  }
  _$AK(e, t) {
    const i = this.constructor, s = i._$Eh.get(e);
    if (s !== void 0 && this._$Em !== s) {
      const o = i.getPropertyOptions(s), n = typeof o.converter == "function" ? { fromAttribute: o.converter } : o.converter?.fromAttribute !== void 0 ? o.converter : z;
      this._$Em = s;
      const c = n.fromAttribute(t, o.type);
      this[s] = c ?? this._$Ej?.get(s) ?? c, this._$Em = null;
    }
  }
  requestUpdate(e, t, i, s = !1, o) {
    if (e !== void 0) {
      const n = this.constructor;
      if (s === !1 && (o = this[e]), i ??= n.getPropertyOptions(e), !((i.hasChanged ?? Z)(o, t) || i.useDefault && i.reflect && o === this._$Ej?.get(e) && !this.hasAttribute(n._$Eu(e, i)))) return;
      this.C(e, t, i);
    }
    this.isUpdatePending === !1 && (this._$ES = this._$EP());
  }
  C(e, t, { useDefault: i, reflect: s, wrapped: o }, n) {
    i && !(this._$Ej ??= /* @__PURE__ */ new Map()).has(e) && (this._$Ej.set(e, n ?? t ?? this[e]), o !== !0 || n !== void 0) || (this._$AL.has(e) || (this.hasUpdated || i || (t = void 0), this._$AL.set(e, t)), s === !0 && this._$Em !== e && (this._$Eq ??= /* @__PURE__ */ new Set()).add(e));
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
        for (const [s, o] of this._$Ep) this[s] = o;
        this._$Ep = void 0;
      }
      const i = this.constructor.elementProperties;
      if (i.size > 0) for (const [s, o] of i) {
        const { wrapped: n } = o, c = this[s];
        n !== !0 || this._$AL.has(s) || c === void 0 || this.C(s, void 0, o, c);
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
S.elementStyles = [], S.shadowRootOptions = { mode: "open" }, S[M("elementProperties")] = /* @__PURE__ */ new Map(), S[M("finalized")] = /* @__PURE__ */ new Map(), He?.({ ReactiveElement: S }), (j.reactiveElementVersions ??= []).push("2.1.2");
const X = globalThis, ae = (r) => r, D = X.trustedTypes, le = D ? D.createPolicy("lit-html", { createHTML: (r) => r }) : void 0, ke = "$lit$", _ = `lit$${Math.random().toFixed(9).slice(2)}$`, we = "?" + _, qe = `<${we}>`, x = document, R = () => x.createComment(""), U = (r) => r === null || typeof r != "object" && typeof r != "function", ee = Array.isArray, ze = (r) => ee(r) || typeof r?.[Symbol.iterator] == "function", V = `[ 	
\f\r]`, C = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, de = /-->/g, ce = />/g, k = RegExp(`>|${V}(?:([^\\s"'>=/]+)(${V}*=${V}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`, "g"), he = /'/g, pe = /"/g, xe = /^(?:script|style|textarea|title)$/i, De = (r) => (e, ...t) => ({ _$litType$: r, strings: e, values: t }), a = De(1), P = /* @__PURE__ */ Symbol.for("lit-noChange"), l = /* @__PURE__ */ Symbol.for("lit-nothing"), ue = /* @__PURE__ */ new WeakMap(), w = x.createTreeWalker(x, 129);
function Ae(r, e) {
  if (!ee(r) || !r.hasOwnProperty("raw")) throw Error("invalid template strings array");
  return le !== void 0 ? le.createHTML(e) : e;
}
const Be = (r, e) => {
  const t = r.length - 1, i = [];
  let s, o = e === 2 ? "<svg>" : e === 3 ? "<math>" : "", n = C;
  for (let c = 0; c < t; c++) {
    const d = r[c];
    let u, m, h = -1, $ = 0;
    for (; $ < d.length && (n.lastIndex = $, m = n.exec(d), m !== null); ) $ = n.lastIndex, n === C ? m[1] === "!--" ? n = de : m[1] !== void 0 ? n = ce : m[2] !== void 0 ? (xe.test(m[2]) && (s = RegExp("</" + m[2], "g")), n = k) : m[3] !== void 0 && (n = k) : n === k ? m[0] === ">" ? (n = s ?? C, h = -1) : m[1] === void 0 ? h = -2 : (h = n.lastIndex - m[2].length, u = m[1], n = m[3] === void 0 ? k : m[3] === '"' ? pe : he) : n === pe || n === he ? n = k : n === de || n === ce ? n = C : (n = k, s = void 0);
    const y = n === k && r[c + 1].startsWith("/>") ? " " : "";
    o += n === C ? d + qe : h >= 0 ? (i.push(u), d.slice(0, h) + ke + d.slice(h) + _ + y) : d + _ + (h === -2 ? c : y);
  }
  return [Ae(r, o + (r[t] || "<?>") + (e === 2 ? "</svg>" : e === 3 ? "</math>" : "")), i];
};
class I {
  constructor({ strings: e, _$litType$: t }, i) {
    let s;
    this.parts = [];
    let o = 0, n = 0;
    const c = e.length - 1, d = this.parts, [u, m] = Be(e, t);
    if (this.el = I.createElement(u, i), w.currentNode = this.el.content, t === 2 || t === 3) {
      const h = this.el.content.firstChild;
      h.replaceWith(...h.childNodes);
    }
    for (; (s = w.nextNode()) !== null && d.length < c; ) {
      if (s.nodeType === 1) {
        if (s.hasAttributes()) for (const h of s.getAttributeNames()) if (h.endsWith(ke)) {
          const $ = m[n++], y = s.getAttribute(h).split(_), O = /([.?@])?(.*)/.exec($);
          d.push({ type: 1, index: o, name: O[2], strings: y, ctor: O[1] === "." ? We : O[1] === "?" ? Ve : O[1] === "@" ? Qe : W }), s.removeAttribute(h);
        } else h.startsWith(_) && (d.push({ type: 6, index: o }), s.removeAttribute(h));
        if (xe.test(s.tagName)) {
          const h = s.textContent.split(_), $ = h.length - 1;
          if ($ > 0) {
            s.textContent = D ? D.emptyScript : "";
            for (let y = 0; y < $; y++) s.append(h[y], R()), w.nextNode(), d.push({ type: 2, index: ++o });
            s.append(h[$], R());
          }
        }
      } else if (s.nodeType === 8) if (s.data === we) d.push({ type: 2, index: o });
      else {
        let h = -1;
        for (; (h = s.data.indexOf(_, h + 1)) !== -1; ) d.push({ type: 7, index: o }), h += _.length - 1;
      }
      o++;
    }
  }
  static createElement(e, t) {
    const i = x.createElement("template");
    return i.innerHTML = e, i;
  }
}
function T(r, e, t = r, i) {
  if (e === P) return e;
  let s = i !== void 0 ? t._$Co?.[i] : t._$Cl;
  const o = U(e) ? void 0 : e._$litDirective$;
  return s?.constructor !== o && (s?._$AO?.(!1), o === void 0 ? s = void 0 : (s = new o(r), s._$AT(r, t, i)), i !== void 0 ? (t._$Co ??= [])[i] = s : t._$Cl = s), s !== void 0 && (e = T(r, s._$AS(r, e.values), s, i)), e;
}
class je {
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
    const { el: { content: t }, parts: i } = this._$AD, s = (e?.creationScope ?? x).importNode(t, !0);
    w.currentNode = s;
    let o = w.nextNode(), n = 0, c = 0, d = i[0];
    for (; d !== void 0; ) {
      if (n === d.index) {
        let u;
        d.type === 2 ? u = new L(o, o.nextSibling, this, e) : d.type === 1 ? u = new d.ctor(o, d.name, d.strings, this, e) : d.type === 6 && (u = new Ke(o, this, e)), this._$AV.push(u), d = i[++c];
      }
      n !== d?.index && (o = w.nextNode(), n++);
    }
    return w.currentNode = x, s;
  }
  p(e) {
    let t = 0;
    for (const i of this._$AV) i !== void 0 && (i.strings !== void 0 ? (i._$AI(e, i, t), t += i.strings.length - 2) : i._$AI(e[t])), t++;
  }
}
class L {
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
    e = T(this, e, t), U(e) ? e === l || e == null || e === "" ? (this._$AH !== l && this._$AR(), this._$AH = l) : e !== this._$AH && e !== P && this._(e) : e._$litType$ !== void 0 ? this.$(e) : e.nodeType !== void 0 ? this.T(e) : ze(e) ? this.k(e) : this._(e);
  }
  O(e) {
    return this._$AA.parentNode.insertBefore(e, this._$AB);
  }
  T(e) {
    this._$AH !== e && (this._$AR(), this._$AH = this.O(e));
  }
  _(e) {
    this._$AH !== l && U(this._$AH) ? this._$AA.nextSibling.data = e : this.T(x.createTextNode(e)), this._$AH = e;
  }
  $(e) {
    const { values: t, _$litType$: i } = e, s = typeof i == "number" ? this._$AC(e) : (i.el === void 0 && (i.el = I.createElement(Ae(i.h, i.h[0]), this.options)), i);
    if (this._$AH?._$AD === s) this._$AH.p(t);
    else {
      const o = new je(s, this), n = o.u(this.options);
      o.p(t), this.T(n), this._$AH = o;
    }
  }
  _$AC(e) {
    let t = ue.get(e.strings);
    return t === void 0 && ue.set(e.strings, t = new I(e)), t;
  }
  k(e) {
    ee(this._$AH) || (this._$AH = [], this._$AR());
    const t = this._$AH;
    let i, s = 0;
    for (const o of e) s === t.length ? t.push(i = new L(this.O(R()), this.O(R()), this, this.options)) : i = t[s], i._$AI(o), s++;
    s < t.length && (this._$AR(i && i._$AB.nextSibling, s), t.length = s);
  }
  _$AR(e = this._$AA.nextSibling, t) {
    for (this._$AP?.(!1, !0, t); e !== this._$AB; ) {
      const i = ae(e).nextSibling;
      ae(e).remove(), e = i;
    }
  }
  setConnected(e) {
    this._$AM === void 0 && (this._$Cv = e, this._$AP?.(e));
  }
}
class W {
  get tagName() {
    return this.element.tagName;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  constructor(e, t, i, s, o) {
    this.type = 1, this._$AH = l, this._$AN = void 0, this.element = e, this.name = t, this._$AM = s, this.options = o, i.length > 2 || i[0] !== "" || i[1] !== "" ? (this._$AH = Array(i.length - 1).fill(new String()), this.strings = i) : this._$AH = l;
  }
  _$AI(e, t = this, i, s) {
    const o = this.strings;
    let n = !1;
    if (o === void 0) e = T(this, e, t, 0), n = !U(e) || e !== this._$AH && e !== P, n && (this._$AH = e);
    else {
      const c = e;
      let d, u;
      for (e = o[0], d = 0; d < o.length - 1; d++) u = T(this, c[i + d], t, d), u === P && (u = this._$AH[d]), n ||= !U(u) || u !== this._$AH[d], u === l ? e = l : e !== l && (e += (u ?? "") + o[d + 1]), this._$AH[d] = u;
    }
    n && !s && this.j(e);
  }
  j(e) {
    e === l ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, e ?? "");
  }
}
class We extends W {
  constructor() {
    super(...arguments), this.type = 3;
  }
  j(e) {
    this.element[this.name] = e === l ? void 0 : e;
  }
}
class Ve extends W {
  constructor() {
    super(...arguments), this.type = 4;
  }
  j(e) {
    this.element.toggleAttribute(this.name, !!e && e !== l);
  }
}
class Qe extends W {
  constructor(e, t, i, s, o) {
    super(e, t, i, s, o), this.type = 5;
  }
  _$AI(e, t = this) {
    if ((e = T(this, e, t, 0) ?? l) === P) return;
    const i = this._$AH, s = e === l && i !== l || e.capture !== i.capture || e.once !== i.once || e.passive !== i.passive, o = e !== l && (i === l || s);
    s && this.element.removeEventListener(this.name, this, i), o && this.element.addEventListener(this.name, this, e), this._$AH = e;
  }
  handleEvent(e) {
    typeof this._$AH == "function" ? this._$AH.call(this.options?.host ?? this.element, e) : this._$AH.handleEvent(e);
  }
}
class Ke {
  constructor(e, t, i) {
    this.element = e, this.type = 6, this._$AN = void 0, this._$AM = t, this.options = i;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AI(e) {
    T(this, e);
  }
}
const Fe = X.litHtmlPolyfillSupport;
Fe?.(I, L), (X.litHtmlVersions ??= []).push("3.3.3");
const Ge = (r, e, t) => {
  const i = t?.renderBefore ?? e;
  let s = i._$litPart$;
  if (s === void 0) {
    const o = t?.renderBefore ?? null;
    i._$litPart$ = s = new L(e.insertBefore(R(), o), o, void 0, t ?? {});
  }
  return s._$AI(r), s;
};
const te = globalThis;
class E extends S {
  constructor() {
    super(...arguments), this.renderOptions = { host: this }, this._$Do = void 0;
  }
  createRenderRoot() {
    const e = super.createRenderRoot();
    return this.renderOptions.renderBefore ??= e.firstChild, e;
  }
  update(e) {
    const t = this.render();
    this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(e), this._$Do = Ge(t, this.renderRoot, this.renderOptions);
  }
  connectedCallback() {
    super.connectedCallback(), this._$Do?.setConnected(!0);
  }
  disconnectedCallback() {
    super.disconnectedCallback(), this._$Do?.setConnected(!1);
  }
  render() {
    return P;
  }
}
E._$litElement$ = !0, E.finalized = !0, te.litElementHydrateSupport?.({ LitElement: E });
const Je = te.litElementPolyfillSupport;
Je?.({ LitElement: E });
(te.litElementVersions ??= []).push("4.2.2");
const Ye = { attribute: !0, type: String, converter: z, reflect: !1, hasChanged: Z }, Ze = (r = Ye, e, t) => {
  const { kind: i, metadata: s } = t;
  let o = globalThis.litPropertyMetadata.get(s);
  if (o === void 0 && globalThis.litPropertyMetadata.set(s, o = /* @__PURE__ */ new Map()), i === "setter" && ((r = Object.create(r)).wrapped = !0), o.set(t.name, r), i === "accessor") {
    const { name: n } = t;
    return { set(c) {
      const d = e.get.call(this);
      e.set.call(this, c), this.requestUpdate(n, d, r, !0, c);
    }, init(c) {
      return c !== void 0 && this.C(n, void 0, r, c), c;
    } };
  }
  if (i === "setter") {
    const { name: n } = t;
    return function(c) {
      const d = this[n];
      e.call(this, c), this.requestUpdate(n, d, r, !0, c);
    };
  }
  throw Error("Unsupported decorator location: " + i);
};
function N(r) {
  return (e, t) => typeof t == "object" ? Ze(r, e, t) : ((i, s, o) => {
    const n = s.hasOwnProperty(o);
    return s.constructor.createProperty(o, i), n ? Object.getOwnPropertyDescriptor(s, o) : void 0;
  })(r, e, t);
}
function p(r) {
  return N({ ...r, state: !0, attribute: !1 });
}
const fe = {
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
    "nav.home": "Home",
    "nav.learn": "Learn",
    "nav.quiz": "Quiz",
    "nav.exam": "Exam",
    "nav.stats": "Stats",
    "nav.profiles": "Profiles",
    "nav.tracks": "Tracks",
    "nav.packs": "Packs",
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
    "nav.home": "Accueil",
    "nav.learn": "Apprendre",
    "nav.quiz": "Quiz",
    "nav.exam": "Examen",
    "nav.stats": "Stats",
    "nav.profiles": "Profils",
    "nav.tracks": "Parcours",
    "nav.packs": "Packs",
    "nav.settings": "Réglages"
  }
};
function Se(r) {
  const e = r.toLowerCase();
  return e === "fr" || e.startsWith("fr-") ? "fr" : "en";
}
function Ee(r, e) {
  return fe[r][e] ?? fe.en[e];
}
function Xe(r) {
  return r?.payload.selection?.progress_state === "new";
}
function et(r) {
  const e = r?.payload.available_at_utc;
  if (typeof e != "string") return null;
  const t = Date.parse(e);
  return Number.isNaN(t) ? null : t;
}
function me(r) {
  return r !== void 0 && r.role !== "viewer";
}
const A = 2;
class Pe extends Error {
  constructor(e, t, i) {
    super(
      `LockLearn frontend protocol ${e} does not match backend protocol ${t}`
    ), this.frontendProtocol = e, this.backendProtocol = t, this.backendVersion = i;
  }
}
async function tt(r) {
  const e = await r.callWS({
    type: "locklearn/bootstrap"
  });
  if (e.frontend_protocol !== A)
    throw new Pe(
      A,
      e.frontend_protocol,
      e.backend_version
    );
  return e;
}
async function it(r) {
  const e = [];
  let t = null;
  do {
    const i = await r.callWS({
      type: "locklearn/profiles/list",
      limit: 100,
      ...t === null ? {} : { cursor: t }
    });
    e.push(...i.items), t = i.cursor;
  } while (t !== null);
  return e;
}
async function st(r, e) {
  return r.callWS({
    type: "locklearn/dashboard/get",
    profile_id: e
  });
}
async function rt(r, e, t, i = 20) {
  return r.callWS({
    type: "locklearn/session/start",
    profile_id: e,
    track_id: t,
    session_type: "learn",
    strategy: "default",
    settings: { requested_cards: i }
  });
}
async function ge(r, e) {
  return r.callWS({
    type: "locklearn/session/get",
    session_id: e
  });
}
async function ve(r, e, t, i) {
  return r.callWS({
    type: "locklearn/session/answer",
    session_id: e.id,
    expected_version: e.version,
    question_id: t,
    answer: i
  });
}
async function ot(r, e) {
  return r.callWS({
    type: "locklearn/session/complete",
    session_id: e.id,
    expected_version: e.version
  });
}
async function nt(r, e, t, i, s) {
  return r.callWS({
    type: "locklearn/progress/set_user_state",
    profile_id: e,
    track_id: t,
    card_key: i,
    user_state: s
  });
}
async function at(r, e, t, i, s) {
  return r.callWS({
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
async function lt(r, e, t, i) {
  return r.callWS({
    type: "locklearn/annotations/create",
    profile_id: e,
    card_key: t,
    note: i.trim()
  });
}
var dt = Object.defineProperty, g = (r, e, t, i) => {
  for (var s = void 0, o = r.length - 1, n; o >= 0; o--)
    (n = r[o]) && (s = n(e, t, s) || s);
  return s && dt(e, t, s), s;
};
function H() {
  return globalThis.performance?.now() ?? Date.now();
}
const ie = class ie extends E {
  constructor() {
    super(...arguments), this.trackId = "", this.loading = !1, this.errorMessage = "", this.notice = "", this.revealed = !1, this.hintUsed = !1, this.pendingIdk = !1, this.mnemonic = "", this.reportMessage = "", this.questionStartedAt = H(), this.questionId = null;
  }
  disconnectedCallback() {
    this.clearAvailabilityTimer(), super.disconnectedCallback();
  }
  updated(e) {
    if (e.has("profile") || e.has("dashboard")) {
      const t = this.tracks();
      t.some((i) => i.track_id === this.trackId) || (this.trackId = t[0]?.track_id ?? ""), e.has("profile") && (this.session = void 0, this.resetQuestionUi());
    }
  }
  locale() {
    const e = this.hass?.locale?.language ?? this.hass?.language ?? globalThis.navigator?.language ?? "en";
    return Se(e);
  }
  t(e) {
    return Ee(this.locale(), e);
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
    this.clearAvailabilityTimer(), this.waitingUntil = void 0, this.revealed = !1, this.hintUsed = !1, this.pendingIdk = !1, this.pendingIdkLatency = void 0, this.mnemonic = "", this.reportMessage = "", this.notice = "", this.questionStartedAt = H(), this.questionId = this.session?.current_question?.question_id ?? null;
  }
  clearAvailabilityTimer() {
    this.availabilityTimer !== void 0 && (globalThis.clearTimeout(this.availabilityTimer), this.availabilityTimer = void 0);
  }
  scheduleCurrentQuestionAvailability() {
    const e = et(this.session?.current_question);
    e === null || e <= Date.now() || (this.waitingUntil = new Date(e).toISOString(), this.availabilityTimer = globalThis.setTimeout(() => {
      this.availabilityTimer = void 0, this.waitingUntil = void 0, this.questionStartedAt = H();
    }, e - Date.now()));
  }
  applySession(e) {
    const i = (e.current_question?.question_id ?? null) !== this.questionId;
    this.session = e, i && (this.resetQuestionUi(), this.scheduleCurrentQuestionAvailability());
  }
  elapsedMs() {
    return Math.max(0, Math.round(H() - this.questionStartedAt));
  }
  async start() {
    if (!(this.hass === void 0 || this.profile === void 0 || this.trackId === "" || !me(this.profile))) {
      this.loading = !0, this.errorMessage = "", this.notice = "";
      try {
        const e = await rt(
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
        this.applySession(await ge(this.hass, e.session_id));
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
        this.applySession(await ge(this.hass, this.session.id)), this.notice = this.t("learn.reloaded");
        return;
      } catch {
      }
    this.errorMessage = e instanceof Error ? e.message : String(e);
  }
  async finalizeIfDone(e) {
    return this.hass !== void 0 && e.status === "active" && e.current_question === null && e.question_count > 0 ? ot(this.hass, e) : e;
  }
  async learningAction(e, t) {
    const i = this.session?.current_question;
    if (!(this.hass === void 0 || this.session === void 0 || i === null || i === void 0)) {
      this.loading = !0, this.errorMessage = "";
      try {
        const s = await ve(
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
        await nt(
          this.hass,
          this.profile.profile_id,
          this.session.track_id,
          t.card_key,
          e
        );
        const i = await ve(
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
        await at(
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
        await lt(
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
    if (!me(this.profile))
      return a`<section class="learn-card"><p>${this.t("learn.readOnly")}</p></section>`;
    const e = this.tracks();
    if (e.length === 0)
      return a`<section class="learn-card"><p>${this.t("learn.noTracks")}</p></section>`;
    const t = this.selectedTrack(), i = t?.last_session !== null && t?.last_session !== void 0 && ["active", "paused"].includes(t.last_session.status);
    return a`
      <section class="learn-shell">
        <div class="toolbar">
          <label>
            <span>${this.t("learn.track")}</span>
            <select .value=${this.trackId} @change=${this.setTrack} ?disabled=${this.loading}>
              ${e.map(
      (s) => a`
                  <option value=${s.track_id}>
                    ${s.name} · ${s.source_language} → ${s.target_language}
                  </option>
                `
    )}
            </select>
          </label>
          <div class="actions">
            ${i ? a`<button @click=${this.resume} ?disabled=${this.loading}>
                  ${this.t("learn.resume")}
                </button>` : l}
            <button class="primary" @click=${this.start} ?disabled=${this.loading}>
              ${this.t("learn.start")}
            </button>
          </div>
        </div>
        ${this.loading && this.session === void 0 ? a`<div class="notice" role="status">${this.t("learn.loading")}</div>` : l}
        ${this.errorMessage ? a`<div class="error" role="alert">
              <strong>${this.t("learn.error")}</strong>
              <div>${this.errorMessage}</div>
            </div>` : l}
        ${this.notice ? a`<div class="notice" role="status" aria-live="polite">${this.notice}</div>` : l}
        ${this.renderSession()}
      </section>
    `;
  }
  renderSession() {
    return this.session === void 0 ? l : this.session.question_count === 0 ? a`<section class="learn-card"><p>${this.t("learn.empty")}</p></section>` : this.session.current_question === null || this.session.status === "completed" ? a`
        <section class="learn-card">
          <h2>${this.t("learn.completed")}</h2>
          <p>${this.t("learn.completedBody")}</p>
          <button class="primary" @click=${this.start} ?disabled=${this.loading}>
            ${this.t("learn.newSession")}
          </button>
        </section>
      ` : this.waitingUntil !== void 0 ? this.renderWaiting(this.session.current_question) : Xe(this.session.current_question) ? this.renderIntroduction(this.session.current_question) : this.renderRetrieval(this.session.current_question);
  }
  renderWaiting(e) {
    const t = this.waitingUntil;
    if (t === void 0) return l;
    const i = new Date(t), s = Number.isNaN(i.getTime()) ? "" : new Intl.DateTimeFormat(this.locale(), { timeStyle: "medium" }).format(i);
    return a`
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
    return a`
      <div class="progress">
        <span>${this.t("learn.progress")}</span>
        <span>${e.position + 1} / ${this.session?.question_count ?? 0}</span>
      </div>
    `;
  }
  renderIntroduction(e) {
    const t = e.payload.presentation;
    return t === void 0 ? a`<section class="learn-card"></section>` : a`
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
    if (t === void 0) return a`<section class="learn-card"></section>`;
    const i = [...t.hint_blocks, ...t.mnemonic_blocks];
    return a`
      <article class="learn-card">
        ${this.renderProgress(e)}
        <div class="stage">${this.t("learn.prompt")}</div>
        <div class="content">
          ${t.context.flatMap(
      (s) => s.blocks.map((o) => this.renderBlock(o, !1))
    )}
          ${t.prompt.blocks.map((s) => this.renderBlock(s, !0))}
        </div>
        ${this.hintUsed ? a`
              <div class="hint-state" role="status">
                ${this.t("learn.hintUsed")}
                ${i.map((s) => this.renderBlock(s, !1))}
              </div>
            ` : l}
        ${this.revealed ? a`
              <div class="answer">
                <div class="stage">${this.t("learn.answer")}</div>
                ${t.answer.blocks.map((s) => this.renderBlock(s, !0))}
                ${this.pendingIdk ? a`<p>${this.t("learn.feedbackIdk")}</p>` : l}
              </div>
            ` : l}
        <div class="actions">
          ${this.revealed ? this.pendingIdk ? a`<button
                  class="primary"
                  @click=${() => {
      this.learningAction("idk", this.pendingIdkLatency);
    }}
                  ?disabled=${this.loading}
                >
                  ${this.t("learn.continue")}
                </button>` : a`
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
                ` : a`
                <button class="primary" @click=${this.reveal} ?disabled=${this.loading}>
                  ${this.t("learn.reveal")}
                </button>
                <button @click=${this.idk} ?disabled=${this.loading}>
                  ${this.t("learn.idk")}
                </button>
                ${i.length > 0 ? a`<button @click=${this.showHint} ?disabled=${this.loading || this.hintUsed}>
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
    return i.length === 0 ? l : a`
      <div class="hint-state" role="status">
        ${this.t("learn.hintUsed")}
        ${i.map((s) => this.renderBlock(s, !1))}
      </div>
    `;
  }
  renderSecondaryActions(e) {
    return a`
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
    const i = e.payload.text;
    if (typeof i != "string" || i === "") return l;
    const s = e.language_tag ?? void 0;
    return a`
      <div
        class="content-block ${t ? "primary-content" : ""}"
        lang=${s ?? l}
      >
        ${i}
      </div>
    `;
  }
};
ie.styles = _e`
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
let f = ie;
g([
  N({ attribute: !1 })
], f.prototype, "hass");
g([
  N({ attribute: !1 })
], f.prototype, "profile");
g([
  N({ attribute: !1 })
], f.prototype, "dashboard");
g([
  p()
], f.prototype, "trackId");
g([
  p()
], f.prototype, "session");
g([
  p()
], f.prototype, "loading");
g([
  p()
], f.prototype, "errorMessage");
g([
  p()
], f.prototype, "notice");
g([
  p()
], f.prototype, "revealed");
g([
  p()
], f.prototype, "hintUsed");
g([
  p()
], f.prototype, "pendingIdk");
g([
  p()
], f.prototype, "pendingIdkLatency");
g([
  p()
], f.prototype, "mnemonic");
g([
  p()
], f.prototype, "reportMessage");
g([
  p()
], f.prototype, "waitingUntil");
globalThis.customElements !== void 0 && customElements.get("locklearn-learn-view") === void 0 && customElements.define("locklearn-learn-view", f);
const be = [
  { route: "home", labelKey: "nav.home" },
  { route: "learn", labelKey: "nav.learn" },
  { route: "quiz", labelKey: "nav.quiz" },
  { route: "exam", labelKey: "nav.exam" },
  { route: "stats", labelKey: "nav.stats" },
  { route: "profiles", labelKey: "nav.profiles" },
  { route: "tracks", labelKey: "nav.tracks" },
  { route: "packs", labelKey: "nav.packs" }
], ct = [
  { route: "settings", labelKey: "nav.settings" }
];
function G(r) {
  return r.length === 0 ? [] : new Set(r.map((t) => t.role)).has("owner") ? [...be, ...ct] : be;
}
function Q(r, e) {
  return G(e).some((t) => t.route === r);
}
function ht(r) {
  return {
    mine: r.filter((e) => e.role === "owner"),
    shared: r.filter((e) => e.role !== "owner")
  };
}
function pt(r, e) {
  const t = e.personal_profile?.profile_id;
  if (t !== void 0 && r.some((s) => s.profile_id === t))
    return t;
  const i = r.find((s) => s.role === "owner");
  return i !== void 0 ? i.profile_id : r[0]?.profile_id ?? null;
}
function ut(r) {
  if (r === void 0) return { kind: "define" };
  const e = typeof r.locklearnFrontendProtocol == "number" ? r.locklearnFrontendProtocol : null;
  return e === A ? { kind: "reuse" } : {
    kind: "reload",
    existingProtocol: e,
    frontendProtocol: A
  };
}
function ft(r, e, t) {
  return !r && e && t;
}
const mt = [
  "home",
  "learn",
  "quiz",
  "exam",
  "stats",
  "profiles",
  "tracks",
  "packs",
  "settings"
], gt = "home";
function K(r) {
  const t = r.replace(/^\/+|\/+$/g, "").split("/").filter(Boolean), i = t[0] === "locklearn" ? t[1] : t[0];
  return mt.includes(i) ? i : gt;
}
function vt(r) {
  return r === "home" ? "/locklearn" : `/locklearn/${r}`;
}
function bt(r) {
  const e = vt(r);
  globalThis.location?.pathname !== e && (globalThis.history?.pushState({}, "", e), globalThis.dispatchEvent?.(new PopStateEvent("popstate")));
}
var $t = Object.defineProperty, b = (r, e, t, i) => {
  for (var s = void 0, o = r.length - 1, n; o >= 0; o--)
    (n = r[o]) && (s = n(e, t, s) || s);
  return s && $t(e, t, s), s;
};
const $e = "locklearn-hard-reload-required", B = class B extends E {
  constructor() {
    super(...arguments), this.status = "loading", this.activeRoute = K(
      globalThis.location?.pathname ?? "/locklearn"
    ), this.profiles = [], this.selectedProfileId = null, this.dashboardLoading = !1, this.dashboardError = "", this.errorMessage = "", this.loadGeneration = 0, this.dashboardGeneration = 0, this.initialLoadStarted = !1, this.handlePopState = () => {
      const e = K(globalThis.location?.pathname ?? "/locklearn");
      this.activeRoute = Q(e, this.profiles) ? e : "home";
    };
  }
  connectedCallback() {
    super.connectedCallback(), globalThis.addEventListener?.("popstate", this.handlePopState);
  }
  disconnectedCallback() {
    globalThis.removeEventListener?.("popstate", this.handlePopState), super.disconnectedCallback();
  }
  updated(e) {
    ft(
      this.initialLoadStarted,
      e.has("hass"),
      this.hass !== void 0
    ) && (this.initialLoadStarted = !0, this.load());
  }
  locale() {
    const e = this.hass?.locale?.language ?? this.hass?.language ?? globalThis.navigator?.language ?? "en";
    return Se(e);
  }
  t(e) {
    return Ee(this.locale(), e);
  }
  async load() {
    if (this.hass === void 0) return;
    const e = ++this.loadGeneration;
    this.status = "loading", this.errorMessage = "";
    try {
      const t = await tt(this.hass), i = await it(this.hass);
      if (e !== this.loadGeneration) return;
      this.bootstrapState = t, this.profiles = i, this.selectedProfileId = pt(i, t);
      const s = K(globalThis.location?.pathname ?? t.panel_path);
      this.activeRoute = Q(s, i) ? s : "home", this.status = "ready", this.loadDashboard();
    } catch (t) {
      if (e !== this.loadGeneration) return;
      if (t instanceof Pe) {
        this.bootstrapState = {
          frontend_protocol: t.backendProtocol,
          backend_version: t.backendVersion,
          panel_path: "/locklearn",
          authenticated_user_id: "",
          personal_profile: null
        }, this.status = "protocol-mismatch";
        return;
      }
      this.errorMessage = t instanceof Error ? t.message : String(t), this.status = "error";
    }
  }
  selectRoute(e) {
    Q(e, this.profiles) && (this.activeRoute = e, bt(e));
  }
  selectProfile(e) {
    const t = e.currentTarget;
    if (!(t instanceof HTMLSelectElement)) return;
    const i = t.value;
    this.profiles.some((s) => s.profile_id === i) && (this.selectedProfileId = i, this.loadDashboard());
  }
  async loadDashboard() {
    if (this.hass === void 0 || this.selectedProfileId === null) {
      this.dashboard = void 0, this.dashboardError = "";
      return;
    }
    const e = ++this.dashboardGeneration;
    this.dashboardLoading = !0, this.dashboardError = "";
    try {
      const t = await st(this.hass, this.selectedProfileId);
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
      return a`
        <main>
          <section class="state-card" role="alert">
            <h1>${this.t("state.protocol.title")}</h1>
            <p>${this.t("state.protocol.body")}</p>
            <button class="primary-button" @click=${this.hardReload}>
              ${this.t("state.protocol.reload")}
            </button>
            <div class="meta">
              frontend protocol ${A} · backend protocol
              ${this.bootstrapState?.frontend_protocol ?? "?"} · backend
              ${this.bootstrapState?.backend_version ?? "?"}
            </div>
          </section>
        </main>
      `;
    if (this.status === "error")
      return a`
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
    const e = G(this.profiles), t = ht(this.profiles);
    return a`
      <div class="shell">
        <header>
          <div class="brand">${this.t("app.title")}</div>
          ${this.profiles.length === 0 ? l : a`<label class="profile-switcher">
                <span>${this.t("profile.select")}</span>
                <select
                  .value=${this.selectedProfileId ?? ""}
                  @change=${this.selectProfile}
                >
                  ${t.mine.length === 0 ? l : a`<optgroup label=${this.t("profile.mine")}>
                        ${t.mine.map(
      (i) => a`<option value=${i.profile_id}>${i.name}</option>`
    )}
                      </optgroup>`}
                  ${t.shared.length === 0 ? l : a`<optgroup label=${this.t("profile.shared")}>
                        ${t.shared.map(
      (i) => a`<option value=${i.profile_id}>${i.name}</option>`
    )}
                      </optgroup>`}
                </select>
              </label>`}
          <nav aria-label="LockLearn">
            ${e.map(
      (i) => a`
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
          ${this.profiles.length === 0 ? a`<section class="state-card">
                <h1>${this.t("app.title")}</h1>
                <p>${this.t("state.noProfiles")}</p>
              </section>` : this.activeRoute === "home" ? this.renderHome() : this.activeRoute === "learn" ? a`<locklearn-learn-view
                    .hass=${this.hass}
                    .profile=${this.profiles.find(
      (i) => i.profile_id === this.selectedProfileId
    )}
                    .dashboard=${this.dashboard}
                  ></locklearn-learn-view>` : a`<section class="page">
                  <h1>${this.routeLabel(this.activeRoute)}</h1>
                  <p>${this.t("route.placeholder")}</p>
                </section>`}
        </main>
      </div>
    `;
  }
  renderHome() {
    return this.dashboardLoading ? a`<section class="page"><p>${this.t("dashboard.loading")}</p></section>` : this.dashboardError ? a`<section class="page" role="alert">
        <h1>${this.t("dashboard.error")}</h1>
        <p>${this.dashboardError}</p>
      </section>` : this.dashboard === void 0 ? a`<section class="page"><p>${this.t("dashboard.noTracks")}</p></section>` : a`
      <section>
        <div class="home-header">
          <h1>${this.dashboard.profile.name}</h1>
        </div>
        ${this.dashboard.tracks.length === 0 ? a`<section class="page"><p>${this.t("dashboard.noTracks")}</p></section>` : a`<div class="track-grid">
              ${this.dashboard.tracks.map((e) => a`
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
                      ${e.recent_verified_retention === null ? l : a`<div class="metric-detail">
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
                      ${e.last_session === null ? l : a`<div class="metric-detail">
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
    return a`<main><section class="state-card"><p>${e}</p></section></main>`;
  }
  routeLabel(e) {
    const t = G(this.profiles).find((i) => i.route === e);
    return t === void 0 ? this.t("nav.home") : this.t(t.labelKey);
  }
};
B.locklearnFrontendProtocol = A, B.styles = _e`
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
let v = B;
b([
  N({ attribute: !1 })
], v.prototype, "hass");
b([
  p()
], v.prototype, "status");
b([
  p()
], v.prototype, "activeRoute");
b([
  p()
], v.prototype, "bootstrapState");
b([
  p()
], v.prototype, "profiles");
b([
  p()
], v.prototype, "selectedProfileId");
b([
  p()
], v.prototype, "dashboard");
b([
  p()
], v.prototype, "dashboardLoading");
b([
  p()
], v.prototype, "dashboardError");
b([
  p()
], v.prototype, "errorMessage");
function yt(r) {
  if (typeof document > "u" || document.getElementById($e) !== null) return;
  const e = document.createElement("div");
  e.id = $e, e.setAttribute("role", "alert"), e.style.cssText = "position:fixed;inset:0;z-index:2147483647;display:grid;place-items:center;padding:24px;background:var(--primary-background-color,#fff);color:var(--primary-text-color,#111);font-family:system-ui,sans-serif";
  const t = document.createElement("div");
  t.style.cssText = "max-width:680px;padding:24px;border:1px solid var(--divider-color,#ddd);border-radius:12px;background:var(--card-background-color,#fff)";
  const i = document.createElement("h1");
  i.textContent = "LockLearn was updated";
  const s = document.createElement("p");
  s.textContent = "An older LockLearn panel is still loaded in this browser. Perform a full browser reload before continuing.";
  const o = document.createElement("p");
  o.textContent = `loaded protocol ${r ?? "unknown"} · current protocol ${A}`;
  const n = document.createElement("button");
  n.textContent = "Reload now", n.addEventListener("click", () => globalThis.location?.reload()), t.append(i, s, o, n), e.append(t), document.body.append(e);
}
const _t = customElements.get(
  "locklearn-panel"
), F = ut(_t);
F.kind === "define" ? customElements.define("locklearn-panel", v) : F.kind === "reload" && yt(F.existingProtocol);
export {
  v as LockLearnPanel
};
