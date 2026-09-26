const H = globalThis, J = H.ShadowRoot && (H.ShadyCSS === void 0 || H.ShadyCSS.nativeShadow) && "adoptedStyleSheets" in Document.prototype && "replace" in CSSStyleSheet.prototype, Y = /* @__PURE__ */ Symbol(), re = /* @__PURE__ */ new WeakMap();
let ye = class {
  constructor(e, t, s) {
    if (this._$cssResult$ = !0, s !== Y) throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");
    this.cssText = e, this.t = t;
  }
  get styleSheet() {
    let e = this.o;
    const t = this.t;
    if (J && e === void 0) {
      const s = t !== void 0 && t.length === 1;
      s && (e = re.get(t)), e === void 0 && ((this.o = e = new CSSStyleSheet()).replaceSync(this.cssText), s && re.set(t, e));
    }
    return e;
  }
  toString() {
    return this.cssText;
  }
};
const Te = (i) => new ye(typeof i == "string" ? i : i + "", void 0, Y), _e = (i, ...e) => {
  const t = i.length === 1 ? i[0] : e.reduce((s, r, o) => s + ((n) => {
    if (n._$cssResult$ === !0) return n.cssText;
    if (typeof n == "number") return n;
    throw Error("Value passed to 'css' function must be a 'css' function result: " + n + ". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.");
  })(r) + i[o + 1], i[0]);
  return new ye(t, i, Y);
}, Me = (i, e) => {
  if (J) i.adoptedStyleSheets = e.map((t) => t instanceof CSSStyleSheet ? t : t.styleSheet);
  else for (const t of e) {
    const s = document.createElement("style"), r = H.litNonce;
    r !== void 0 && s.setAttribute("nonce", r), s.textContent = t.cssText, i.appendChild(s);
  }
}, ie = J ? (i) => i : (i) => i instanceof CSSStyleSheet ? ((e) => {
  let t = "";
  for (const s of e.cssRules) t += s.cssText;
  return Te(t);
})(i) : i;
const { is: Re, defineProperty: Ce, getOwnPropertyDescriptor: Ie, getOwnPropertyNames: Le, getOwnPropertySymbols: Ue, getPrototypeOf: Ne } = Object, j = globalThis, oe = j.trustedTypes, Oe = oe ? oe.emptyScript : "", He = j.reactiveElementPolyfillSupport, R = (i, e) => i, z = { toAttribute(i, e) {
  switch (e) {
    case Boolean:
      i = i ? Oe : null;
      break;
    case Object:
    case Array:
      i = i == null ? i : JSON.stringify(i);
  }
  return i;
}, fromAttribute(i, e) {
  let t = i;
  switch (e) {
    case Boolean:
      t = i !== null;
      break;
    case Number:
      t = i === null ? null : Number(i);
      break;
    case Object:
    case Array:
      try {
        t = JSON.parse(i);
      } catch {
        t = null;
      }
  }
  return t;
} }, Z = (i, e) => !Re(i, e), ne = { attribute: !0, type: String, converter: z, reflect: !1, useDefault: !1, hasChanged: Z };
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
      const s = /* @__PURE__ */ Symbol(), r = this.getPropertyDescriptor(e, s, t);
      r !== void 0 && Ce(this.prototype, e, r);
    }
  }
  static getPropertyDescriptor(e, t, s) {
    const { get: r, set: o } = Ie(this.prototype, e) ?? { get() {
      return this[t];
    }, set(n) {
      this[t] = n;
    } };
    return { get: r, set(n) {
      const c = r?.call(this);
      o?.call(this, n), this.requestUpdate(e, c, s);
    }, configurable: !0, enumerable: !0 };
  }
  static getPropertyOptions(e) {
    return this.elementProperties.get(e) ?? ne;
  }
  static _$Ei() {
    if (this.hasOwnProperty(R("elementProperties"))) return;
    const e = Ne(this);
    e.finalize(), e.l !== void 0 && (this.l = [...e.l]), this.elementProperties = new Map(e.elementProperties);
  }
  static finalize() {
    if (this.hasOwnProperty(R("finalized"))) return;
    if (this.finalized = !0, this._$Ei(), this.hasOwnProperty(R("properties"))) {
      const t = this.properties, s = [...Le(t), ...Ue(t)];
      for (const r of s) this.createProperty(r, t[r]);
    }
    const e = this[Symbol.metadata];
    if (e !== null) {
      const t = litPropertyMetadata.get(e);
      if (t !== void 0) for (const [s, r] of t) this.elementProperties.set(s, r);
    }
    this._$Eh = /* @__PURE__ */ new Map();
    for (const [t, s] of this.elementProperties) {
      const r = this._$Eu(t, s);
      r !== void 0 && this._$Eh.set(r, t);
    }
    this.elementStyles = this.finalizeStyles(this.styles);
  }
  static finalizeStyles(e) {
    const t = [];
    if (Array.isArray(e)) {
      const s = new Set(e.flat(1 / 0).reverse());
      for (const r of s) t.unshift(ie(r));
    } else e !== void 0 && t.push(ie(e));
    return t;
  }
  static _$Eu(e, t) {
    const s = t.attribute;
    return s === !1 ? void 0 : typeof s == "string" ? s : typeof e == "string" ? e.toLowerCase() : void 0;
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
    for (const s of t.keys()) this.hasOwnProperty(s) && (e.set(s, this[s]), delete this[s]);
    e.size > 0 && (this._$Ep = e);
  }
  createRenderRoot() {
    const e = this.shadowRoot ?? this.attachShadow(this.constructor.shadowRootOptions);
    return Me(e, this.constructor.elementStyles), e;
  }
  connectedCallback() {
    this.renderRoot ??= this.createRenderRoot(), this.enableUpdating(!0), this._$EO?.forEach((e) => e.hostConnected?.());
  }
  enableUpdating(e) {
  }
  disconnectedCallback() {
    this._$EO?.forEach((e) => e.hostDisconnected?.());
  }
  attributeChangedCallback(e, t, s) {
    this._$AK(e, s);
  }
  _$ET(e, t) {
    const s = this.constructor.elementProperties.get(e), r = this.constructor._$Eu(e, s);
    if (r !== void 0 && s.reflect === !0) {
      const o = (s.converter?.toAttribute !== void 0 ? s.converter : z).toAttribute(t, s.type);
      this._$Em = e, o == null ? this.removeAttribute(r) : this.setAttribute(r, o), this._$Em = null;
    }
  }
  _$AK(e, t) {
    const s = this.constructor, r = s._$Eh.get(e);
    if (r !== void 0 && this._$Em !== r) {
      const o = s.getPropertyOptions(r), n = typeof o.converter == "function" ? { fromAttribute: o.converter } : o.converter?.fromAttribute !== void 0 ? o.converter : z;
      this._$Em = r;
      const c = n.fromAttribute(t, o.type);
      this[r] = c ?? this._$Ej?.get(r) ?? c, this._$Em = null;
    }
  }
  requestUpdate(e, t, s, r = !1, o) {
    if (e !== void 0) {
      const n = this.constructor;
      if (r === !1 && (o = this[e]), s ??= n.getPropertyOptions(e), !((s.hasChanged ?? Z)(o, t) || s.useDefault && s.reflect && o === this._$Ej?.get(e) && !this.hasAttribute(n._$Eu(e, s)))) return;
      this.C(e, t, s);
    }
    this.isUpdatePending === !1 && (this._$ES = this._$EP());
  }
  C(e, t, { useDefault: s, reflect: r, wrapped: o }, n) {
    s && !(this._$Ej ??= /* @__PURE__ */ new Map()).has(e) && (this._$Ej.set(e, n ?? t ?? this[e]), o !== !0 || n !== void 0) || (this._$AL.has(e) || (this.hasUpdated || s || (t = void 0), this._$AL.set(e, t)), r === !0 && this._$Em !== e && (this._$Eq ??= /* @__PURE__ */ new Set()).add(e));
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
        for (const [r, o] of this._$Ep) this[r] = o;
        this._$Ep = void 0;
      }
      const s = this.constructor.elementProperties;
      if (s.size > 0) for (const [r, o] of s) {
        const { wrapped: n } = o, c = this[r];
        n !== !0 || this._$AL.has(r) || c === void 0 || this.C(r, void 0, o, c);
      }
    }
    let e = !1;
    const t = this._$AL;
    try {
      e = this.shouldUpdate(t), e ? (this.willUpdate(t), this._$EO?.forEach((s) => s.hostUpdate?.()), this.update(t)) : this._$EM();
    } catch (s) {
      throw e = !1, this._$EM(), s;
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
S.elementStyles = [], S.shadowRootOptions = { mode: "open" }, S[R("elementProperties")] = /* @__PURE__ */ new Map(), S[R("finalized")] = /* @__PURE__ */ new Map(), He?.({ ReactiveElement: S }), (j.reactiveElementVersions ??= []).push("2.1.2");
const X = globalThis, ae = (i) => i, q = X.trustedTypes, le = q ? q.createPolicy("lit-html", { createHTML: (i) => i }) : void 0, ke = "$lit$", _ = `lit$${Math.random().toFixed(9).slice(2)}$`, xe = "?" + _, ze = `<${xe}>`, w = document, C = () => w.createComment(""), I = (i) => i === null || typeof i != "object" && typeof i != "function", ee = Array.isArray, qe = (i) => ee(i) || typeof i?.[Symbol.iterator] == "function", W = `[ 	
\f\r]`, M = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, de = /-->/g, ce = />/g, k = RegExp(`>|${W}(?:([^\\s"'>=/]+)(${W}*=${W}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`, "g"), he = /'/g, pe = /"/g, we = /^(?:script|style|textarea|title)$/i, De = (i) => (e, ...t) => ({ _$litType$: i, strings: e, values: t }), a = De(1), P = /* @__PURE__ */ Symbol.for("lit-noChange"), d = /* @__PURE__ */ Symbol.for("lit-nothing"), ue = /* @__PURE__ */ new WeakMap(), x = w.createTreeWalker(w, 129);
function Ae(i, e) {
  if (!ee(i) || !i.hasOwnProperty("raw")) throw Error("invalid template strings array");
  return le !== void 0 ? le.createHTML(e) : e;
}
const je = (i, e) => {
  const t = i.length - 1, s = [];
  let r, o = e === 2 ? "<svg>" : e === 3 ? "<math>" : "", n = M;
  for (let c = 0; c < t; c++) {
    const l = i[c];
    let u, m, h = -1, $ = 0;
    for (; $ < l.length && (n.lastIndex = $, m = n.exec(l), m !== null); ) $ = n.lastIndex, n === M ? m[1] === "!--" ? n = de : m[1] !== void 0 ? n = ce : m[2] !== void 0 ? (we.test(m[2]) && (r = RegExp("</" + m[2], "g")), n = k) : m[3] !== void 0 && (n = k) : n === k ? m[0] === ">" ? (n = r ?? M, h = -1) : m[1] === void 0 ? h = -2 : (h = n.lastIndex - m[2].length, u = m[1], n = m[3] === void 0 ? k : m[3] === '"' ? pe : he) : n === pe || n === he ? n = k : n === de || n === ce ? n = M : (n = k, r = void 0);
    const y = n === k && i[c + 1].startsWith("/>") ? " " : "";
    o += n === M ? l + ze : h >= 0 ? (s.push(u), l.slice(0, h) + ke + l.slice(h) + _ + y) : l + _ + (h === -2 ? c : y);
  }
  return [Ae(i, o + (i[t] || "<?>") + (e === 2 ? "</svg>" : e === 3 ? "</math>" : "")), s];
};
class L {
  constructor({ strings: e, _$litType$: t }, s) {
    let r;
    this.parts = [];
    let o = 0, n = 0;
    const c = e.length - 1, l = this.parts, [u, m] = je(e, t);
    if (this.el = L.createElement(u, s), x.currentNode = this.el.content, t === 2 || t === 3) {
      const h = this.el.content.firstChild;
      h.replaceWith(...h.childNodes);
    }
    for (; (r = x.nextNode()) !== null && l.length < c; ) {
      if (r.nodeType === 1) {
        if (r.hasAttributes()) for (const h of r.getAttributeNames()) if (h.endsWith(ke)) {
          const $ = m[n++], y = r.getAttribute(h).split(_), O = /([.?@])?(.*)/.exec($);
          l.push({ type: 1, index: o, name: O[2], strings: y, ctor: O[1] === "." ? We : O[1] === "?" ? Ve : O[1] === "@" ? Ke : B }), r.removeAttribute(h);
        } else h.startsWith(_) && (l.push({ type: 6, index: o }), r.removeAttribute(h));
        if (we.test(r.tagName)) {
          const h = r.textContent.split(_), $ = h.length - 1;
          if ($ > 0) {
            r.textContent = q ? q.emptyScript : "";
            for (let y = 0; y < $; y++) r.append(h[y], C()), x.nextNode(), l.push({ type: 2, index: ++o });
            r.append(h[$], C());
          }
        }
      } else if (r.nodeType === 8) if (r.data === xe) l.push({ type: 2, index: o });
      else {
        let h = -1;
        for (; (h = r.data.indexOf(_, h + 1)) !== -1; ) l.push({ type: 7, index: o }), h += _.length - 1;
      }
      o++;
    }
  }
  static createElement(e, t) {
    const s = w.createElement("template");
    return s.innerHTML = e, s;
  }
}
function T(i, e, t = i, s) {
  if (e === P) return e;
  let r = s !== void 0 ? t._$Co?.[s] : t._$Cl;
  const o = I(e) ? void 0 : e._$litDirective$;
  return r?.constructor !== o && (r?._$AO?.(!1), o === void 0 ? r = void 0 : (r = new o(i), r._$AT(i, t, s)), s !== void 0 ? (t._$Co ??= [])[s] = r : t._$Cl = r), r !== void 0 && (e = T(i, r._$AS(i, e.values), r, s)), e;
}
class Be {
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
    const { el: { content: t }, parts: s } = this._$AD, r = (e?.creationScope ?? w).importNode(t, !0);
    x.currentNode = r;
    let o = x.nextNode(), n = 0, c = 0, l = s[0];
    for (; l !== void 0; ) {
      if (n === l.index) {
        let u;
        l.type === 2 ? u = new U(o, o.nextSibling, this, e) : l.type === 1 ? u = new l.ctor(o, l.name, l.strings, this, e) : l.type === 6 && (u = new Qe(o, this, e)), this._$AV.push(u), l = s[++c];
      }
      n !== l?.index && (o = x.nextNode(), n++);
    }
    return x.currentNode = w, r;
  }
  p(e) {
    let t = 0;
    for (const s of this._$AV) s !== void 0 && (s.strings !== void 0 ? (s._$AI(e, s, t), t += s.strings.length - 2) : s._$AI(e[t])), t++;
  }
}
class U {
  get _$AU() {
    return this._$AM?._$AU ?? this._$Cv;
  }
  constructor(e, t, s, r) {
    this.type = 2, this._$AH = d, this._$AN = void 0, this._$AA = e, this._$AB = t, this._$AM = s, this.options = r, this._$Cv = r?.isConnected ?? !0;
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
    e = T(this, e, t), I(e) ? e === d || e == null || e === "" ? (this._$AH !== d && this._$AR(), this._$AH = d) : e !== this._$AH && e !== P && this._(e) : e._$litType$ !== void 0 ? this.$(e) : e.nodeType !== void 0 ? this.T(e) : qe(e) ? this.k(e) : this._(e);
  }
  O(e) {
    return this._$AA.parentNode.insertBefore(e, this._$AB);
  }
  T(e) {
    this._$AH !== e && (this._$AR(), this._$AH = this.O(e));
  }
  _(e) {
    this._$AH !== d && I(this._$AH) ? this._$AA.nextSibling.data = e : this.T(w.createTextNode(e)), this._$AH = e;
  }
  $(e) {
    const { values: t, _$litType$: s } = e, r = typeof s == "number" ? this._$AC(e) : (s.el === void 0 && (s.el = L.createElement(Ae(s.h, s.h[0]), this.options)), s);
    if (this._$AH?._$AD === r) this._$AH.p(t);
    else {
      const o = new Be(r, this), n = o.u(this.options);
      o.p(t), this.T(n), this._$AH = o;
    }
  }
  _$AC(e) {
    let t = ue.get(e.strings);
    return t === void 0 && ue.set(e.strings, t = new L(e)), t;
  }
  k(e) {
    ee(this._$AH) || (this._$AH = [], this._$AR());
    const t = this._$AH;
    let s, r = 0;
    for (const o of e) r === t.length ? t.push(s = new U(this.O(C()), this.O(C()), this, this.options)) : s = t[r], s._$AI(o), r++;
    r < t.length && (this._$AR(s && s._$AB.nextSibling, r), t.length = r);
  }
  _$AR(e = this._$AA.nextSibling, t) {
    for (this._$AP?.(!1, !0, t); e !== this._$AB; ) {
      const s = ae(e).nextSibling;
      ae(e).remove(), e = s;
    }
  }
  setConnected(e) {
    this._$AM === void 0 && (this._$Cv = e, this._$AP?.(e));
  }
}
class B {
  get tagName() {
    return this.element.tagName;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  constructor(e, t, s, r, o) {
    this.type = 1, this._$AH = d, this._$AN = void 0, this.element = e, this.name = t, this._$AM = r, this.options = o, s.length > 2 || s[0] !== "" || s[1] !== "" ? (this._$AH = Array(s.length - 1).fill(new String()), this.strings = s) : this._$AH = d;
  }
  _$AI(e, t = this, s, r) {
    const o = this.strings;
    let n = !1;
    if (o === void 0) e = T(this, e, t, 0), n = !I(e) || e !== this._$AH && e !== P, n && (this._$AH = e);
    else {
      const c = e;
      let l, u;
      for (e = o[0], l = 0; l < o.length - 1; l++) u = T(this, c[s + l], t, l), u === P && (u = this._$AH[l]), n ||= !I(u) || u !== this._$AH[l], u === d ? e = d : e !== d && (e += (u ?? "") + o[l + 1]), this._$AH[l] = u;
    }
    n && !r && this.j(e);
  }
  j(e) {
    e === d ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, e ?? "");
  }
}
class We extends B {
  constructor() {
    super(...arguments), this.type = 3;
  }
  j(e) {
    this.element[this.name] = e === d ? void 0 : e;
  }
}
class Ve extends B {
  constructor() {
    super(...arguments), this.type = 4;
  }
  j(e) {
    this.element.toggleAttribute(this.name, !!e && e !== d);
  }
}
class Ke extends B {
  constructor(e, t, s, r, o) {
    super(e, t, s, r, o), this.type = 5;
  }
  _$AI(e, t = this) {
    if ((e = T(this, e, t, 0) ?? d) === P) return;
    const s = this._$AH, r = e === d && s !== d || e.capture !== s.capture || e.once !== s.once || e.passive !== s.passive, o = e !== d && (s === d || r);
    r && this.element.removeEventListener(this.name, this, s), o && this.element.addEventListener(this.name, this, e), this._$AH = e;
  }
  handleEvent(e) {
    typeof this._$AH == "function" ? this._$AH.call(this.options?.host ?? this.element, e) : this._$AH.handleEvent(e);
  }
}
class Qe {
  constructor(e, t, s) {
    this.element = e, this.type = 6, this._$AN = void 0, this._$AM = t, this.options = s;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AI(e) {
    T(this, e);
  }
}
const Fe = X.litHtmlPolyfillSupport;
Fe?.(L, U), (X.litHtmlVersions ??= []).push("3.3.3");
const Ge = (i, e, t) => {
  const s = t?.renderBefore ?? e;
  let r = s._$litPart$;
  if (r === void 0) {
    const o = t?.renderBefore ?? null;
    s._$litPart$ = r = new U(e.insertBefore(C(), o), o, void 0, t ?? {});
  }
  return r._$AI(i), r;
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
const Ye = { attribute: !0, type: String, converter: z, reflect: !1, hasChanged: Z }, Ze = (i = Ye, e, t) => {
  const { kind: s, metadata: r } = t;
  let o = globalThis.litPropertyMetadata.get(r);
  if (o === void 0 && globalThis.litPropertyMetadata.set(r, o = /* @__PURE__ */ new Map()), s === "setter" && ((i = Object.create(i)).wrapped = !0), o.set(t.name, i), s === "accessor") {
    const { name: n } = t;
    return { set(c) {
      const l = e.get.call(this);
      e.set.call(this, c), this.requestUpdate(n, l, i, !0, c);
    }, init(c) {
      return c !== void 0 && this.C(n, void 0, i, c), c;
    } };
  }
  if (s === "setter") {
    const { name: n } = t;
    return function(c) {
      const l = this[n];
      e.call(this, c), this.requestUpdate(n, l, i, !0, c);
    };
  }
  throw Error("Unsupported decorator location: " + s);
};
function N(i) {
  return (e, t) => typeof t == "object" ? Ze(i, e, t) : ((s, r, o) => {
    const n = r.hasOwnProperty(o);
    return r.constructor.createProperty(o, s), n ? Object.getOwnPropertyDescriptor(r, o) : void 0;
  })(i, e, t);
}
function p(i) {
  return N({ ...i, state: !0, attribute: !1 });
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
function Se(i) {
  const e = i.toLowerCase();
  return e === "fr" || e.startsWith("fr-") ? "fr" : "en";
}
function Ee(i, e) {
  return fe[i][e] ?? fe.en[e];
}
function Xe(i) {
  return i?.payload.selection?.progress_state === "new";
}
function me(i) {
  return i !== void 0 && i.role !== "viewer";
}
const A = 2;
class Pe extends Error {
  constructor(e, t, s) {
    super(
      `LockLearn frontend protocol ${e} does not match backend protocol ${t}`
    ), this.frontendProtocol = e, this.backendProtocol = t, this.backendVersion = s;
  }
}
async function et(i) {
  const e = await i.callWS({
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
async function tt(i) {
  const e = [];
  let t = null;
  do {
    const s = await i.callWS({
      type: "locklearn/profiles/list",
      limit: 100,
      ...t === null ? {} : { cursor: t }
    });
    e.push(...s.items), t = s.cursor;
  } while (t !== null);
  return e;
}
async function st(i, e) {
  return i.callWS({
    type: "locklearn/dashboard/get",
    profile_id: e
  });
}
async function rt(i, e, t, s = 20) {
  return i.callWS({
    type: "locklearn/session/start",
    profile_id: e,
    track_id: t,
    session_type: "learn",
    strategy: "default",
    settings: { requested_cards: s }
  });
}
async function ge(i, e) {
  return i.callWS({
    type: "locklearn/session/get",
    session_id: e
  });
}
async function ve(i, e, t, s) {
  return i.callWS({
    type: "locklearn/session/answer",
    session_id: e.id,
    expected_version: e.version,
    question_id: t,
    answer: s
  });
}
async function it(i, e) {
  return i.callWS({
    type: "locklearn/session/complete",
    session_id: e.id,
    expected_version: e.version
  });
}
async function ot(i, e, t, s, r) {
  return i.callWS({
    type: "locklearn/progress/set_user_state",
    profile_id: e,
    track_id: t,
    card_key: s,
    user_state: r
  });
}
async function nt(i, e, t, s, r) {
  return i.callWS({
    type: "locklearn/content/report_question",
    profile_id: e,
    track_id: t,
    card_key: s.card_key,
    learning_item_id: s.learning_item_id,
    prompt_facet_id: s.prompt_facet_id,
    answer_facet_id: s.answer_facet_id,
    reason: "user_reported_question",
    ...r === void 0 || r.trim() === "" ? {} : { message: r.trim() }
  });
}
async function at(i, e, t, s) {
  return i.callWS({
    type: "locklearn/annotations/create",
    profile_id: e,
    card_key: t,
    note: s.trim()
  });
}
var lt = Object.defineProperty, g = (i, e, t, s) => {
  for (var r = void 0, o = i.length - 1, n; o >= 0; o--)
    (n = i[o]) && (r = n(e, t, r) || r);
  return r && lt(e, t, r), r;
};
function V() {
  return globalThis.performance?.now() ?? Date.now();
}
const se = class se extends E {
  constructor() {
    super(...arguments), this.trackId = "", this.loading = !1, this.errorMessage = "", this.notice = "", this.revealed = !1, this.hintUsed = !1, this.pendingIdk = !1, this.mnemonic = "", this.reportMessage = "", this.questionStartedAt = V(), this.questionId = null;
  }
  updated(e) {
    if (e.has("profile") || e.has("dashboard")) {
      const t = this.tracks();
      t.some((s) => s.track_id === this.trackId) || (this.trackId = t[0]?.track_id ?? ""), e.has("profile") && (this.session = void 0, this.resetQuestionUi());
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
    this.revealed = !1, this.hintUsed = !1, this.pendingIdk = !1, this.pendingIdkLatency = void 0, this.mnemonic = "", this.reportMessage = "", this.notice = "", this.questionStartedAt = V(), this.questionId = this.session?.current_question?.question_id ?? null;
  }
  applySession(e) {
    const s = (e.current_question?.question_id ?? null) !== this.questionId;
    this.session = e, s && this.resetQuestionUi();
  }
  elapsedMs() {
    return Math.max(0, Math.round(V() - this.questionStartedAt));
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
    return this.hass !== void 0 && e.status === "active" && e.current_question === null && e.question_count > 0 ? it(this.hass, e) : e;
  }
  async learningAction(e, t) {
    const s = this.session?.current_question;
    if (!(this.hass === void 0 || this.session === void 0 || s === null || s === void 0)) {
      this.loading = !0, this.errorMessage = "";
      try {
        const r = await ve(
          this.hass,
          this.session,
          s.question_id,
          {
            kind: "learning",
            action: e,
            hint_used: this.hintUsed,
            presentation_to_answer_ms: t ?? this.elapsedMs()
          }
        );
        this.applySession(await this.finalizeIfDone(r));
      } catch (r) {
        await this.recover(r);
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
        await ot(
          this.hass,
          this.profile.profile_id,
          this.session.track_id,
          t.card_key,
          e
        );
        const s = await ve(
          this.hass,
          this.session,
          t.question_id,
          { kind: "user_state", action: e }
        );
        this.applySession(await this.finalizeIfDone(s));
      } catch (s) {
        await this.recover(s);
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
        await nt(
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
        await at(
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
    if (this.profile === void 0) return d;
    if (!me(this.profile))
      return a`<section class="learn-card"><p>${this.t("learn.readOnly")}</p></section>`;
    const e = this.tracks();
    if (e.length === 0)
      return a`<section class="learn-card"><p>${this.t("learn.noTracks")}</p></section>`;
    const t = this.selectedTrack(), s = t?.last_session !== null && t?.last_session !== void 0 && ["active", "paused"].includes(t.last_session.status);
    return a`
      <section class="learn-shell">
        <div class="toolbar">
          <label>
            <span>${this.t("learn.track")}</span>
            <select .value=${this.trackId} @change=${this.setTrack} ?disabled=${this.loading}>
              ${e.map(
      (r) => a`
                  <option value=${r.track_id}>
                    ${r.name} · ${r.source_language} → ${r.target_language}
                  </option>
                `
    )}
            </select>
          </label>
          <div class="actions">
            ${s ? a`<button @click=${this.resume} ?disabled=${this.loading}>
                  ${this.t("learn.resume")}
                </button>` : d}
            <button class="primary" @click=${this.start} ?disabled=${this.loading}>
              ${this.t("learn.start")}
            </button>
          </div>
        </div>
        ${this.loading && this.session === void 0 ? a`<div class="notice" role="status">${this.t("learn.loading")}</div>` : d}
        ${this.errorMessage ? a`<div class="error" role="alert">
              <strong>${this.t("learn.error")}</strong>
              <div>${this.errorMessage}</div>
            </div>` : d}
        ${this.notice ? a`<div class="notice" role="status" aria-live="polite">${this.notice}</div>` : d}
        ${this.renderSession()}
      </section>
    `;
  }
  renderSession() {
    return this.session === void 0 ? d : this.session.question_count === 0 ? a`<section class="learn-card"><p>${this.t("learn.empty")}</p></section>` : this.session.current_question === null || this.session.status === "completed" ? a`
        <section class="learn-card">
          <h2>${this.t("learn.completed")}</h2>
          <p>${this.t("learn.completedBody")}</p>
          <button class="primary" @click=${this.start} ?disabled=${this.loading}>
            ${this.t("learn.newSession")}
          </button>
        </section>
      ` : Xe(this.session.current_question) ? this.renderIntroduction(this.session.current_question) : this.renderRetrieval(this.session.current_question);
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
      (s, r) => this.renderBlock(s, r === 0)
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
    const s = [...t.hint_blocks, ...t.mnemonic_blocks];
    return a`
      <article class="learn-card">
        ${this.renderProgress(e)}
        <div class="stage">${this.t("learn.prompt")}</div>
        <div class="content">
          ${t.context.flatMap(
      (r) => r.blocks.map((o) => this.renderBlock(o, !1))
    )}
          ${t.prompt.blocks.map((r) => this.renderBlock(r, !0))}
        </div>
        ${this.hintUsed ? a`
              <div class="hint-state" role="status">
                ${this.t("learn.hintUsed")}
                ${s.map((r) => this.renderBlock(r, !1))}
              </div>
            ` : d}
        ${this.revealed ? a`
              <div class="answer">
                <div class="stage">${this.t("learn.answer")}</div>
                ${t.answer.blocks.map((r) => this.renderBlock(r, !0))}
                ${this.pendingIdk ? a`<p>${this.t("learn.feedbackIdk")}</p>` : d}
              </div>
            ` : d}
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
                ${s.length > 0 ? a`<button @click=${this.showHint} ?disabled=${this.loading || this.hintUsed}>
                      ${this.t("learn.hint")}
                    </button>` : d}
              `}
        </div>
        ${this.renderSecondaryActions(e)}
      </article>
    `;
  }
  renderHintState(e, t) {
    if (!this.hintUsed) return d;
    const s = [...e, ...t];
    return s.length === 0 ? d : a`
      <div class="hint-state" role="status">
        ${this.t("learn.hintUsed")}
        ${s.map((r) => this.renderBlock(r, !1))}
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
      const s = t.currentTarget;
      s instanceof HTMLTextAreaElement && (this.mnemonic = s.value);
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
    const s = e.payload.text;
    if (typeof s != "string" || s === "") return d;
    const r = e.language_tag ?? void 0;
    return a`
      <div
        class="content-block ${t ? "primary-content" : ""}"
        lang=${r ?? d}
      >
        ${s}
      </div>
    `;
  }
};
se.styles = _e`
    :host {
      display: block;
    }

    .learn-shell,
    .learn-card {
      box-sizing: border-box;
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
      }

      .progress {
        flex-direction: column;
        gap: 4px;
      }
    }
  `;
let f = se;
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
], dt = [
  { route: "settings", labelKey: "nav.settings" }
];
function G(i) {
  return i.length === 0 ? [] : new Set(i.map((t) => t.role)).has("owner") ? [...be, ...dt] : be;
}
function K(i, e) {
  return G(e).some((t) => t.route === i);
}
function ct(i) {
  return {
    mine: i.filter((e) => e.role === "owner"),
    shared: i.filter((e) => e.role !== "owner")
  };
}
function ht(i, e) {
  const t = e.personal_profile?.profile_id;
  if (t !== void 0 && i.some((r) => r.profile_id === t))
    return t;
  const s = i.find((r) => r.role === "owner");
  return s !== void 0 ? s.profile_id : i[0]?.profile_id ?? null;
}
function pt(i) {
  if (i === void 0) return { kind: "define" };
  const e = typeof i.locklearnFrontendProtocol == "number" ? i.locklearnFrontendProtocol : null;
  return e === A ? { kind: "reuse" } : {
    kind: "reload",
    existingProtocol: e,
    frontendProtocol: A
  };
}
function ut(i, e, t) {
  return !i && e && t;
}
const ft = [
  "home",
  "learn",
  "quiz",
  "exam",
  "stats",
  "profiles",
  "tracks",
  "packs",
  "settings"
], mt = "home";
function Q(i) {
  const t = i.replace(/^\/+|\/+$/g, "").split("/").filter(Boolean), s = t[0] === "locklearn" ? t[1] : t[0];
  return ft.includes(s) ? s : mt;
}
function gt(i) {
  return i === "home" ? "/locklearn" : `/locklearn/${i}`;
}
function vt(i) {
  const e = gt(i);
  globalThis.location?.pathname !== e && (globalThis.history?.pushState({}, "", e), globalThis.dispatchEvent?.(new PopStateEvent("popstate")));
}
var bt = Object.defineProperty, b = (i, e, t, s) => {
  for (var r = void 0, o = i.length - 1, n; o >= 0; o--)
    (n = i[o]) && (r = n(e, t, r) || r);
  return r && bt(e, t, r), r;
};
const $e = "locklearn-hard-reload-required", D = class D extends E {
  constructor() {
    super(...arguments), this.status = "loading", this.activeRoute = Q(
      globalThis.location?.pathname ?? "/locklearn"
    ), this.profiles = [], this.selectedProfileId = null, this.dashboardLoading = !1, this.dashboardError = "", this.errorMessage = "", this.loadGeneration = 0, this.dashboardGeneration = 0, this.initialLoadStarted = !1, this.handlePopState = () => {
      const e = Q(globalThis.location?.pathname ?? "/locklearn");
      this.activeRoute = K(e, this.profiles) ? e : "home";
    };
  }
  connectedCallback() {
    super.connectedCallback(), globalThis.addEventListener?.("popstate", this.handlePopState);
  }
  disconnectedCallback() {
    globalThis.removeEventListener?.("popstate", this.handlePopState), super.disconnectedCallback();
  }
  updated(e) {
    ut(
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
      const t = await et(this.hass), s = await tt(this.hass);
      if (e !== this.loadGeneration) return;
      this.bootstrapState = t, this.profiles = s, this.selectedProfileId = ht(s, t);
      const r = Q(globalThis.location?.pathname ?? t.panel_path);
      this.activeRoute = K(r, s) ? r : "home", this.status = "ready", this.loadDashboard();
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
    K(e, this.profiles) && (this.activeRoute = e, vt(e));
  }
  selectProfile(e) {
    const t = e.currentTarget;
    if (!(t instanceof HTMLSelectElement)) return;
    const s = t.value;
    this.profiles.some((r) => r.profile_id === s) && (this.selectedProfileId = s, this.loadDashboard());
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
    const e = G(this.profiles), t = ct(this.profiles);
    return a`
      <div class="shell">
        <header>
          <div class="brand">${this.t("app.title")}</div>
          ${this.profiles.length === 0 ? d : a`<label class="profile-switcher">
                <span>${this.t("profile.select")}</span>
                <select
                  .value=${this.selectedProfileId ?? ""}
                  @change=${this.selectProfile}
                >
                  ${t.mine.length === 0 ? d : a`<optgroup label=${this.t("profile.mine")}>
                        ${t.mine.map(
      (s) => a`<option value=${s.profile_id}>${s.name}</option>`
    )}
                      </optgroup>`}
                  ${t.shared.length === 0 ? d : a`<optgroup label=${this.t("profile.shared")}>
                        ${t.shared.map(
      (s) => a`<option value=${s.profile_id}>${s.name}</option>`
    )}
                      </optgroup>`}
                </select>
              </label>`}
          <nav aria-label="LockLearn">
            ${e.map(
      (s) => a`
                <button
                  class="nav-button"
                  aria-current=${this.activeRoute === s.route ? "page" : d}
                  @click=${() => this.selectRoute(s.route)}
                >
                  ${this.t(s.labelKey)}
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
      (s) => s.profile_id === this.selectedProfileId
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
                      ${e.recent_verified_retention === null ? d : a`<div class="metric-detail">
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
                      ${e.last_session === null ? d : a`<div class="metric-detail">
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
    const s = new Date(e);
    return Number.isNaN(s.getTime()) ? "—" : new Intl.DateTimeFormat(this.locale(), {
      dateStyle: "short",
      timeStyle: "short",
      ...t === void 0 ? {} : { timeZone: t }
    }).format(s);
  }
  renderState(e) {
    return a`<main><section class="state-card"><p>${e}</p></section></main>`;
  }
  routeLabel(e) {
    const t = G(this.profiles).find((s) => s.route === e);
    return t === void 0 ? this.t("nav.home") : this.t(t.labelKey);
  }
};
D.locklearnFrontendProtocol = A, D.styles = _e`
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
let v = D;
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
function $t(i) {
  if (typeof document > "u" || document.getElementById($e) !== null) return;
  const e = document.createElement("div");
  e.id = $e, e.setAttribute("role", "alert"), e.style.cssText = "position:fixed;inset:0;z-index:2147483647;display:grid;place-items:center;padding:24px;background:var(--primary-background-color,#fff);color:var(--primary-text-color,#111);font-family:system-ui,sans-serif";
  const t = document.createElement("div");
  t.style.cssText = "max-width:680px;padding:24px;border:1px solid var(--divider-color,#ddd);border-radius:12px;background:var(--card-background-color,#fff)";
  const s = document.createElement("h1");
  s.textContent = "LockLearn was updated";
  const r = document.createElement("p");
  r.textContent = "An older LockLearn panel is still loaded in this browser. Perform a full browser reload before continuing.";
  const o = document.createElement("p");
  o.textContent = `loaded protocol ${i ?? "unknown"} · current protocol ${A}`;
  const n = document.createElement("button");
  n.textContent = "Reload now", n.addEventListener("click", () => globalThis.location?.reload()), t.append(s, r, o, n), e.append(t), document.body.append(e);
}
const yt = customElements.get(
  "locklearn-panel"
), F = pt(yt);
F.kind === "define" ? customElements.define("locklearn-panel", v) : F.kind === "reload" && $t(F.existingProtocol);
export {
  v as LockLearnPanel
};
