const M = globalThis, W = M.ShadowRoot && (M.ShadyCSS === void 0 || M.ShadyCSS.nativeShadow) && "adoptedStyleSheets" in Document.prototype && "replace" in CSSStyleSheet.prototype, F = /* @__PURE__ */ Symbol(), Y = /* @__PURE__ */ new WeakMap();
let pt = class {
  constructor(t, e, s) {
    if (this._$cssResult$ = !0, s !== F) throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");
    this.cssText = t, this.t = e;
  }
  get styleSheet() {
    let t = this.o;
    const e = this.t;
    if (W && t === void 0) {
      const s = e !== void 0 && e.length === 1;
      s && (t = Y.get(e)), t === void 0 && ((this.o = t = new CSSStyleSheet()).replaceSync(this.cssText), s && Y.set(e, t));
    }
    return t;
  }
  toString() {
    return this.cssText;
  }
};
const bt = (o) => new pt(typeof o == "string" ? o : o + "", void 0, F), _t = (o, ...t) => {
  const e = o.length === 1 ? o[0] : t.reduce((s, r, i) => s + ((n) => {
    if (n._$cssResult$ === !0) return n.cssText;
    if (typeof n == "number") return n;
    throw Error("Value passed to 'css' function must be a 'css' function result: " + n + ". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.");
  })(r) + o[i + 1], o[0]);
  return new pt(e, o, F);
}, yt = (o, t) => {
  if (W) o.adoptedStyleSheets = t.map((e) => e instanceof CSSStyleSheet ? e : e.styleSheet);
  else for (const e of t) {
    const s = document.createElement("style"), r = M.litNonce;
    r !== void 0 && s.setAttribute("nonce", r), s.textContent = e.cssText, o.appendChild(s);
  }
}, X = W ? (o) => o : (o) => o instanceof CSSStyleSheet ? ((t) => {
  let e = "";
  for (const s of t.cssRules) e += s.cssText;
  return bt(e);
})(o) : o;
const { is: At, defineProperty: xt, getOwnPropertyDescriptor: Et, getOwnPropertyNames: wt, getOwnPropertySymbols: St, getPrototypeOf: kt } = Object, D = globalThis, tt = D.trustedTypes, Pt = tt ? tt.emptyScript : "", Ct = D.reactiveElementPolyfillSupport, k = (o, t) => o, H = { toAttribute(o, t) {
  switch (t) {
    case Boolean:
      o = o ? Pt : null;
      break;
    case Object:
    case Array:
      o = o == null ? o : JSON.stringify(o);
  }
  return o;
}, fromAttribute(o, t) {
  let e = o;
  switch (t) {
    case Boolean:
      e = o !== null;
      break;
    case Number:
      e = o === null ? null : Number(o);
      break;
    case Object:
    case Array:
      try {
        e = JSON.parse(o);
      } catch {
        e = null;
      }
  }
  return e;
} }, G = (o, t) => !At(o, t), et = { attribute: !0, type: String, converter: H, reflect: !1, useDefault: !1, hasChanged: G };
Symbol.metadata ??= /* @__PURE__ */ Symbol("metadata"), D.litPropertyMetadata ??= /* @__PURE__ */ new WeakMap();
let A = class extends HTMLElement {
  static addInitializer(t) {
    this._$Ei(), (this.l ??= []).push(t);
  }
  static get observedAttributes() {
    return this.finalize(), this._$Eh && [...this._$Eh.keys()];
  }
  static createProperty(t, e = et) {
    if (e.state && (e.attribute = !1), this._$Ei(), this.prototype.hasOwnProperty(t) && ((e = Object.create(e)).wrapped = !0), this.elementProperties.set(t, e), !e.noAccessor) {
      const s = /* @__PURE__ */ Symbol(), r = this.getPropertyDescriptor(t, s, e);
      r !== void 0 && xt(this.prototype, t, r);
    }
  }
  static getPropertyDescriptor(t, e, s) {
    const { get: r, set: i } = Et(this.prototype, t) ?? { get() {
      return this[e];
    }, set(n) {
      this[e] = n;
    } };
    return { get: r, set(n) {
      const l = r?.call(this);
      i?.call(this, n), this.requestUpdate(t, l, s);
    }, configurable: !0, enumerable: !0 };
  }
  static getPropertyOptions(t) {
    return this.elementProperties.get(t) ?? et;
  }
  static _$Ei() {
    if (this.hasOwnProperty(k("elementProperties"))) return;
    const t = kt(this);
    t.finalize(), t.l !== void 0 && (this.l = [...t.l]), this.elementProperties = new Map(t.elementProperties);
  }
  static finalize() {
    if (this.hasOwnProperty(k("finalized"))) return;
    if (this.finalized = !0, this._$Ei(), this.hasOwnProperty(k("properties"))) {
      const e = this.properties, s = [...wt(e), ...St(e)];
      for (const r of s) this.createProperty(r, e[r]);
    }
    const t = this[Symbol.metadata];
    if (t !== null) {
      const e = litPropertyMetadata.get(t);
      if (e !== void 0) for (const [s, r] of e) this.elementProperties.set(s, r);
    }
    this._$Eh = /* @__PURE__ */ new Map();
    for (const [e, s] of this.elementProperties) {
      const r = this._$Eu(e, s);
      r !== void 0 && this._$Eh.set(r, e);
    }
    this.elementStyles = this.finalizeStyles(this.styles);
  }
  static finalizeStyles(t) {
    const e = [];
    if (Array.isArray(t)) {
      const s = new Set(t.flat(1 / 0).reverse());
      for (const r of s) e.unshift(X(r));
    } else t !== void 0 && e.push(X(t));
    return e;
  }
  static _$Eu(t, e) {
    const s = e.attribute;
    return s === !1 ? void 0 : typeof s == "string" ? s : typeof t == "string" ? t.toLowerCase() : void 0;
  }
  constructor() {
    super(), this._$Ep = void 0, this.isUpdatePending = !1, this.hasUpdated = !1, this._$Em = null, this._$Ev();
  }
  _$Ev() {
    this._$ES = new Promise((t) => this.enableUpdating = t), this._$AL = /* @__PURE__ */ new Map(), this._$E_(), this.requestUpdate(), this.constructor.l?.forEach((t) => t(this));
  }
  addController(t) {
    (this._$EO ??= /* @__PURE__ */ new Set()).add(t), this.renderRoot !== void 0 && this.isConnected && t.hostConnected?.();
  }
  removeController(t) {
    this._$EO?.delete(t);
  }
  _$E_() {
    const t = /* @__PURE__ */ new Map(), e = this.constructor.elementProperties;
    for (const s of e.keys()) this.hasOwnProperty(s) && (t.set(s, this[s]), delete this[s]);
    t.size > 0 && (this._$Ep = t);
  }
  createRenderRoot() {
    const t = this.shadowRoot ?? this.attachShadow(this.constructor.shadowRootOptions);
    return yt(t, this.constructor.elementStyles), t;
  }
  connectedCallback() {
    this.renderRoot ??= this.createRenderRoot(), this.enableUpdating(!0), this._$EO?.forEach((t) => t.hostConnected?.());
  }
  enableUpdating(t) {
  }
  disconnectedCallback() {
    this._$EO?.forEach((t) => t.hostDisconnected?.());
  }
  attributeChangedCallback(t, e, s) {
    this._$AK(t, s);
  }
  _$ET(t, e) {
    const s = this.constructor.elementProperties.get(t), r = this.constructor._$Eu(t, s);
    if (r !== void 0 && s.reflect === !0) {
      const i = (s.converter?.toAttribute !== void 0 ? s.converter : H).toAttribute(e, s.type);
      this._$Em = t, i == null ? this.removeAttribute(r) : this.setAttribute(r, i), this._$Em = null;
    }
  }
  _$AK(t, e) {
    const s = this.constructor, r = s._$Eh.get(t);
    if (r !== void 0 && this._$Em !== r) {
      const i = s.getPropertyOptions(r), n = typeof i.converter == "function" ? { fromAttribute: i.converter } : i.converter?.fromAttribute !== void 0 ? i.converter : H;
      this._$Em = r;
      const l = n.fromAttribute(e, i.type);
      this[r] = l ?? this._$Ej?.get(r) ?? l, this._$Em = null;
    }
  }
  requestUpdate(t, e, s, r = !1, i) {
    if (t !== void 0) {
      const n = this.constructor;
      if (r === !1 && (i = this[t]), s ??= n.getPropertyOptions(t), !((s.hasChanged ?? G)(i, e) || s.useDefault && s.reflect && i === this._$Ej?.get(t) && !this.hasAttribute(n._$Eu(t, s)))) return;
      this.C(t, e, s);
    }
    this.isUpdatePending === !1 && (this._$ES = this._$EP());
  }
  C(t, e, { useDefault: s, reflect: r, wrapped: i }, n) {
    s && !(this._$Ej ??= /* @__PURE__ */ new Map()).has(t) && (this._$Ej.set(t, n ?? e ?? this[t]), i !== !0 || n !== void 0) || (this._$AL.has(t) || (this.hasUpdated || s || (e = void 0), this._$AL.set(t, e)), r === !0 && this._$Em !== t && (this._$Eq ??= /* @__PURE__ */ new Set()).add(t));
  }
  async _$EP() {
    this.isUpdatePending = !0;
    try {
      await this._$ES;
    } catch (e) {
      Promise.reject(e);
    }
    const t = this.scheduleUpdate();
    return t != null && await t, !this.isUpdatePending;
  }
  scheduleUpdate() {
    return this.performUpdate();
  }
  performUpdate() {
    if (!this.isUpdatePending) return;
    if (!this.hasUpdated) {
      if (this.renderRoot ??= this.createRenderRoot(), this._$Ep) {
        for (const [r, i] of this._$Ep) this[r] = i;
        this._$Ep = void 0;
      }
      const s = this.constructor.elementProperties;
      if (s.size > 0) for (const [r, i] of s) {
        const { wrapped: n } = i, l = this[r];
        n !== !0 || this._$AL.has(r) || l === void 0 || this.C(r, void 0, i, l);
      }
    }
    let t = !1;
    const e = this._$AL;
    try {
      t = this.shouldUpdate(e), t ? (this.willUpdate(e), this._$EO?.forEach((s) => s.hostUpdate?.()), this.update(e)) : this._$EM();
    } catch (s) {
      throw t = !1, this._$EM(), s;
    }
    t && this._$AE(e);
  }
  willUpdate(t) {
  }
  _$AE(t) {
    this._$EO?.forEach((e) => e.hostUpdated?.()), this.hasUpdated || (this.hasUpdated = !0, this.firstUpdated(t)), this.updated(t);
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
  shouldUpdate(t) {
    return !0;
  }
  update(t) {
    this._$Eq &&= this._$Eq.forEach((e) => this._$ET(e, this[e])), this._$EM();
  }
  updated(t) {
  }
  firstUpdated(t) {
  }
};
A.elementStyles = [], A.shadowRootOptions = { mode: "open" }, A[k("elementProperties")] = /* @__PURE__ */ new Map(), A[k("finalized")] = /* @__PURE__ */ new Map(), Ct?.({ ReactiveElement: A }), (D.reactiveElementVersions ??= []).push("2.1.2");
const Z = globalThis, st = (o) => o, N = Z.trustedTypes, rt = N ? N.createPolicy("lit-html", { createHTML: (o) => o }) : void 0, ut = "$lit$", $ = `lit$${Math.random().toFixed(9).slice(2)}$`, ft = "?" + $, Tt = `<${ft}>`, _ = document, C = () => _.createComment(""), T = (o) => o === null || typeof o != "object" && typeof o != "function", J = Array.isArray, Lt = (o) => J(o) || typeof o?.[Symbol.iterator] == "function", I = `[ 	
\f\r]`, S = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, ot = /-->/g, it = />/g, g = RegExp(`>|${I}(?:([^\\s"'>=/]+)(${I}*=${I}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`, "g"), nt = /'/g, at = /"/g, mt = /^(?:script|style|textarea|title)$/i, Ot = (o) => (t, ...e) => ({ _$litType$: o, strings: t, values: e }), v = Ot(1), x = /* @__PURE__ */ Symbol.for("lit-noChange"), h = /* @__PURE__ */ Symbol.for("lit-nothing"), lt = /* @__PURE__ */ new WeakMap(), b = _.createTreeWalker(_, 129);
function $t(o, t) {
  if (!J(o) || !o.hasOwnProperty("raw")) throw Error("invalid template strings array");
  return rt !== void 0 ? rt.createHTML(t) : t;
}
const Rt = (o, t) => {
  const e = o.length - 1, s = [];
  let r, i = t === 2 ? "<svg>" : t === 3 ? "<math>" : "", n = S;
  for (let l = 0; l < e; l++) {
    const a = o[l];
    let d, p, c = -1, u = 0;
    for (; u < a.length && (n.lastIndex = u, p = n.exec(a), p !== null); ) u = n.lastIndex, n === S ? p[1] === "!--" ? n = ot : p[1] !== void 0 ? n = it : p[2] !== void 0 ? (mt.test(p[2]) && (r = RegExp("</" + p[2], "g")), n = g) : p[3] !== void 0 && (n = g) : n === g ? p[0] === ">" ? (n = r ?? S, c = -1) : p[1] === void 0 ? c = -2 : (c = n.lastIndex - p[2].length, d = p[1], n = p[3] === void 0 ? g : p[3] === '"' ? at : nt) : n === at || n === nt ? n = g : n === ot || n === it ? n = S : (n = g, r = void 0);
    const m = n === g && o[l + 1].startsWith("/>") ? " " : "";
    i += n === S ? a + Tt : c >= 0 ? (s.push(d), a.slice(0, c) + ut + a.slice(c) + $ + m) : a + $ + (c === -2 ? l : m);
  }
  return [$t(o, i + (o[e] || "<?>") + (t === 2 ? "</svg>" : t === 3 ? "</math>" : "")), s];
};
class L {
  constructor({ strings: t, _$litType$: e }, s) {
    let r;
    this.parts = [];
    let i = 0, n = 0;
    const l = t.length - 1, a = this.parts, [d, p] = Rt(t, e);
    if (this.el = L.createElement(d, s), b.currentNode = this.el.content, e === 2 || e === 3) {
      const c = this.el.content.firstChild;
      c.replaceWith(...c.childNodes);
    }
    for (; (r = b.nextNode()) !== null && a.length < l; ) {
      if (r.nodeType === 1) {
        if (r.hasAttributes()) for (const c of r.getAttributeNames()) if (c.endsWith(ut)) {
          const u = p[n++], m = r.getAttribute(c).split($), U = /([.?@])?(.*)/.exec(u);
          a.push({ type: 1, index: i, name: U[2], strings: m, ctor: U[1] === "." ? Mt : U[1] === "?" ? Ht : U[1] === "@" ? Nt : j }), r.removeAttribute(c);
        } else c.startsWith($) && (a.push({ type: 6, index: i }), r.removeAttribute(c));
        if (mt.test(r.tagName)) {
          const c = r.textContent.split($), u = c.length - 1;
          if (u > 0) {
            r.textContent = N ? N.emptyScript : "";
            for (let m = 0; m < u; m++) r.append(c[m], C()), b.nextNode(), a.push({ type: 2, index: ++i });
            r.append(c[u], C());
          }
        }
      } else if (r.nodeType === 8) if (r.data === ft) a.push({ type: 2, index: i });
      else {
        let c = -1;
        for (; (c = r.data.indexOf($, c + 1)) !== -1; ) a.push({ type: 7, index: i }), c += $.length - 1;
      }
      i++;
    }
  }
  static createElement(t, e) {
    const s = _.createElement("template");
    return s.innerHTML = t, s;
  }
}
function E(o, t, e = o, s) {
  if (t === x) return t;
  let r = s !== void 0 ? e._$Co?.[s] : e._$Cl;
  const i = T(t) ? void 0 : t._$litDirective$;
  return r?.constructor !== i && (r?._$AO?.(!1), i === void 0 ? r = void 0 : (r = new i(o), r._$AT(o, e, s)), s !== void 0 ? (e._$Co ??= [])[s] = r : e._$Cl = r), r !== void 0 && (t = E(o, r._$AS(o, t.values), r, s)), t;
}
class Ut {
  constructor(t, e) {
    this._$AV = [], this._$AN = void 0, this._$AD = t, this._$AM = e;
  }
  get parentNode() {
    return this._$AM.parentNode;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  u(t) {
    const { el: { content: e }, parts: s } = this._$AD, r = (t?.creationScope ?? _).importNode(e, !0);
    b.currentNode = r;
    let i = b.nextNode(), n = 0, l = 0, a = s[0];
    for (; a !== void 0; ) {
      if (n === a.index) {
        let d;
        a.type === 2 ? d = new O(i, i.nextSibling, this, t) : a.type === 1 ? d = new a.ctor(i, a.name, a.strings, this, t) : a.type === 6 && (d = new zt(i, this, t)), this._$AV.push(d), a = s[++l];
      }
      n !== a?.index && (i = b.nextNode(), n++);
    }
    return b.currentNode = _, r;
  }
  p(t) {
    let e = 0;
    for (const s of this._$AV) s !== void 0 && (s.strings !== void 0 ? (s._$AI(t, s, e), e += s.strings.length - 2) : s._$AI(t[e])), e++;
  }
}
class O {
  get _$AU() {
    return this._$AM?._$AU ?? this._$Cv;
  }
  constructor(t, e, s, r) {
    this.type = 2, this._$AH = h, this._$AN = void 0, this._$AA = t, this._$AB = e, this._$AM = s, this.options = r, this._$Cv = r?.isConnected ?? !0;
  }
  get parentNode() {
    let t = this._$AA.parentNode;
    const e = this._$AM;
    return e !== void 0 && t?.nodeType === 11 && (t = e.parentNode), t;
  }
  get startNode() {
    return this._$AA;
  }
  get endNode() {
    return this._$AB;
  }
  _$AI(t, e = this) {
    t = E(this, t, e), T(t) ? t === h || t == null || t === "" ? (this._$AH !== h && this._$AR(), this._$AH = h) : t !== this._$AH && t !== x && this._(t) : t._$litType$ !== void 0 ? this.$(t) : t.nodeType !== void 0 ? this.T(t) : Lt(t) ? this.k(t) : this._(t);
  }
  O(t) {
    return this._$AA.parentNode.insertBefore(t, this._$AB);
  }
  T(t) {
    this._$AH !== t && (this._$AR(), this._$AH = this.O(t));
  }
  _(t) {
    this._$AH !== h && T(this._$AH) ? this._$AA.nextSibling.data = t : this.T(_.createTextNode(t)), this._$AH = t;
  }
  $(t) {
    const { values: e, _$litType$: s } = t, r = typeof s == "number" ? this._$AC(t) : (s.el === void 0 && (s.el = L.createElement($t(s.h, s.h[0]), this.options)), s);
    if (this._$AH?._$AD === r) this._$AH.p(e);
    else {
      const i = new Ut(r, this), n = i.u(this.options);
      i.p(e), this.T(n), this._$AH = i;
    }
  }
  _$AC(t) {
    let e = lt.get(t.strings);
    return e === void 0 && lt.set(t.strings, e = new L(t)), e;
  }
  k(t) {
    J(this._$AH) || (this._$AH = [], this._$AR());
    const e = this._$AH;
    let s, r = 0;
    for (const i of t) r === e.length ? e.push(s = new O(this.O(C()), this.O(C()), this, this.options)) : s = e[r], s._$AI(i), r++;
    r < e.length && (this._$AR(s && s._$AB.nextSibling, r), e.length = r);
  }
  _$AR(t = this._$AA.nextSibling, e) {
    for (this._$AP?.(!1, !0, e); t !== this._$AB; ) {
      const s = st(t).nextSibling;
      st(t).remove(), t = s;
    }
  }
  setConnected(t) {
    this._$AM === void 0 && (this._$Cv = t, this._$AP?.(t));
  }
}
class j {
  get tagName() {
    return this.element.tagName;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  constructor(t, e, s, r, i) {
    this.type = 1, this._$AH = h, this._$AN = void 0, this.element = t, this.name = e, this._$AM = r, this.options = i, s.length > 2 || s[0] !== "" || s[1] !== "" ? (this._$AH = Array(s.length - 1).fill(new String()), this.strings = s) : this._$AH = h;
  }
  _$AI(t, e = this, s, r) {
    const i = this.strings;
    let n = !1;
    if (i === void 0) t = E(this, t, e, 0), n = !T(t) || t !== this._$AH && t !== x, n && (this._$AH = t);
    else {
      const l = t;
      let a, d;
      for (t = i[0], a = 0; a < i.length - 1; a++) d = E(this, l[s + a], e, a), d === x && (d = this._$AH[a]), n ||= !T(d) || d !== this._$AH[a], d === h ? t = h : t !== h && (t += (d ?? "") + i[a + 1]), this._$AH[a] = d;
    }
    n && !r && this.j(t);
  }
  j(t) {
    t === h ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, t ?? "");
  }
}
class Mt extends j {
  constructor() {
    super(...arguments), this.type = 3;
  }
  j(t) {
    this.element[this.name] = t === h ? void 0 : t;
  }
}
class Ht extends j {
  constructor() {
    super(...arguments), this.type = 4;
  }
  j(t) {
    this.element.toggleAttribute(this.name, !!t && t !== h);
  }
}
class Nt extends j {
  constructor(t, e, s, r, i) {
    super(t, e, s, r, i), this.type = 5;
  }
  _$AI(t, e = this) {
    if ((t = E(this, t, e, 0) ?? h) === x) return;
    const s = this._$AH, r = t === h && s !== h || t.capture !== s.capture || t.once !== s.once || t.passive !== s.passive, i = t !== h && (s === h || r);
    r && this.element.removeEventListener(this.name, this, s), i && this.element.addEventListener(this.name, this, t), this._$AH = t;
  }
  handleEvent(t) {
    typeof this._$AH == "function" ? this._$AH.call(this.options?.host ?? this.element, t) : this._$AH.handleEvent(t);
  }
}
class zt {
  constructor(t, e, s) {
    this.element = t, this.type = 6, this._$AN = void 0, this._$AM = e, this.options = s;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AI(t) {
    E(this, t);
  }
}
const Dt = Z.litHtmlPolyfillSupport;
Dt?.(L, O), (Z.litHtmlVersions ??= []).push("3.3.3");
const jt = (o, t, e) => {
  const s = e?.renderBefore ?? t;
  let r = s._$litPart$;
  if (r === void 0) {
    const i = e?.renderBefore ?? null;
    s._$litPart$ = r = new O(t.insertBefore(C(), i), i, void 0, e ?? {});
  }
  return r._$AI(o), r;
};
const Q = globalThis;
class P extends A {
  constructor() {
    super(...arguments), this.renderOptions = { host: this }, this._$Do = void 0;
  }
  createRenderRoot() {
    const t = super.createRenderRoot();
    return this.renderOptions.renderBefore ??= t.firstChild, t;
  }
  update(t) {
    const e = this.render();
    this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(t), this._$Do = jt(e, this.renderRoot, this.renderOptions);
  }
  connectedCallback() {
    super.connectedCallback(), this._$Do?.setConnected(!0);
  }
  disconnectedCallback() {
    super.disconnectedCallback(), this._$Do?.setConnected(!1);
  }
  render() {
    return x;
  }
}
P._$litElement$ = !0, P.finalized = !0, Q.litElementHydrateSupport?.({ LitElement: P });
const It = Q.litElementPolyfillSupport;
It?.({ LitElement: P });
(Q.litElementVersions ??= []).push("4.2.2");
const qt = { attribute: !0, type: String, converter: H, reflect: !1, hasChanged: G }, Bt = (o = qt, t, e) => {
  const { kind: s, metadata: r } = e;
  let i = globalThis.litPropertyMetadata.get(r);
  if (i === void 0 && globalThis.litPropertyMetadata.set(r, i = /* @__PURE__ */ new Map()), s === "setter" && ((o = Object.create(o)).wrapped = !0), i.set(e.name, o), s === "accessor") {
    const { name: n } = e;
    return { set(l) {
      const a = t.get.call(this);
      t.set.call(this, l), this.requestUpdate(n, a, o, !0, l);
    }, init(l) {
      return l !== void 0 && this.C(n, void 0, o, l), l;
    } };
  }
  if (s === "setter") {
    const { name: n } = e;
    return function(l) {
      const a = this[n];
      t.call(this, l), this.requestUpdate(n, a, o, !0, l);
    };
  }
  throw Error("Unsupported decorator location: " + s);
};
function gt(o) {
  return (t, e) => typeof e == "object" ? Bt(o, t, e) : ((s, r, i) => {
    const n = r.hasOwnProperty(i);
    return r.constructor.createProperty(i, s), n ? Object.getOwnPropertyDescriptor(r, i) : void 0;
  })(o, t, e);
}
function R(o) {
  return gt({ ...o, state: !0, attribute: !1 });
}
const ct = {
  en: {
    "app.title": "LockLearn",
    "state.loading": "Loading LockLearn…",
    "state.error": "LockLearn could not be loaded.",
    "state.retry": "Retry",
    "state.protocol.title": "LockLearn was updated",
    "state.protocol.body": "The frontend and backend versions no longer match. Perform a full browser reload to load the current panel.",
    "state.protocol.reload": "Reload now",
    "state.noProfiles": "No LockLearn profile is available for this Home Assistant user.",
    "route.placeholder": "This section will be implemented in a later P5 milestone.",
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
    "route.placeholder": "Cette section sera implémentée dans une étape P5 ultérieure.",
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
function Vt(o) {
  const t = o.toLowerCase();
  return t === "fr" || t.startsWith("fr-") ? "fr" : "en";
}
function Kt(o, t) {
  return ct[o][t] ?? ct.en[t];
}
const ht = [
  { route: "home", labelKey: "nav.home" },
  { route: "learn", labelKey: "nav.learn" },
  { route: "quiz", labelKey: "nav.quiz" },
  { route: "exam", labelKey: "nav.exam" },
  { route: "stats", labelKey: "nav.stats" },
  { route: "profiles", labelKey: "nav.profiles" },
  { route: "tracks", labelKey: "nav.tracks" },
  { route: "packs", labelKey: "nav.packs" }
], Wt = [
  { route: "settings", labelKey: "nav.settings" }
];
function K(o) {
  return o.length === 0 ? [] : new Set(o.map((e) => e.role)).has("owner") ? [...ht, ...Wt] : ht;
}
function q(o, t) {
  return K(t).some((e) => e.route === o);
}
const y = 1;
class vt extends Error {
  constructor(t, e, s) {
    super(
      `LockLearn frontend protocol ${t} does not match backend protocol ${e}`
    ), this.frontendProtocol = t, this.backendProtocol = e, this.backendVersion = s;
  }
}
async function Ft(o) {
  const t = await o.callWS({
    type: "locklearn/bootstrap"
  });
  if (t.frontend_protocol !== y)
    throw new vt(
      y,
      t.frontend_protocol,
      t.backend_version
    );
  return t;
}
async function Gt(o) {
  const t = [];
  let e = null;
  do {
    const s = await o.callWS({
      type: "locklearn/profiles/list",
      limit: 100,
      ...e === null ? {} : { cursor: e }
    });
    t.push(...s.items), e = s.cursor;
  } while (e !== null);
  return t;
}
function Zt(o) {
  if (o === void 0) return { kind: "define" };
  const t = typeof o.locklearnFrontendProtocol == "number" ? o.locklearnFrontendProtocol : null;
  return t === y ? { kind: "reuse" } : {
    kind: "reload",
    existingProtocol: t,
    frontendProtocol: y
  };
}
function Jt(o, t, e) {
  return !o && t && e;
}
const Qt = [
  "home",
  "learn",
  "quiz",
  "exam",
  "stats",
  "profiles",
  "tracks",
  "packs",
  "settings"
], Yt = "home";
function B(o) {
  const e = o.replace(/^\/+|\/+$/g, "").split("/").filter(Boolean), s = e[0] === "locklearn" ? e[1] : e[0];
  return Qt.includes(s) ? s : Yt;
}
function Xt(o) {
  return o === "home" ? "/locklearn" : `/locklearn/${o}`;
}
function te(o) {
  const t = Xt(o);
  globalThis.location?.pathname !== t && (globalThis.history?.pushState({}, "", t), globalThis.dispatchEvent?.(new PopStateEvent("popstate")));
}
var ee = Object.defineProperty, w = (o, t, e, s) => {
  for (var r = void 0, i = o.length - 1, n; i >= 0; i--)
    (n = o[i]) && (r = n(t, e, r) || r);
  return r && ee(t, e, r), r;
};
const dt = "locklearn-hard-reload-required", z = class z extends P {
  constructor() {
    super(...arguments), this.status = "loading", this.route = B(globalThis.location?.pathname ?? "/locklearn"), this.profiles = [], this.errorMessage = "", this.loadGeneration = 0, this.initialLoadStarted = !1, this.handlePopState = () => {
      const t = B(globalThis.location?.pathname ?? "/locklearn");
      this.route = q(t, this.profiles) ? t : "home";
    };
  }
  connectedCallback() {
    super.connectedCallback(), globalThis.addEventListener?.("popstate", this.handlePopState);
  }
  disconnectedCallback() {
    globalThis.removeEventListener?.("popstate", this.handlePopState), super.disconnectedCallback();
  }
  updated(t) {
    Jt(
      this.initialLoadStarted,
      t.has("hass"),
      this.hass !== void 0
    ) && (this.initialLoadStarted = !0, this.load());
  }
  locale() {
    const t = this.hass?.locale?.language ?? this.hass?.language ?? globalThis.navigator?.language ?? "en";
    return Vt(t);
  }
  t(t) {
    return Kt(this.locale(), t);
  }
  async load() {
    if (this.hass === void 0) return;
    const t = ++this.loadGeneration;
    this.status = "loading", this.errorMessage = "";
    try {
      const e = await Ft(this.hass), s = await Gt(this.hass);
      if (t !== this.loadGeneration) return;
      this.bootstrapState = e, this.profiles = s;
      const r = B(globalThis.location?.pathname ?? e.panel_path);
      this.route = q(r, s) ? r : "home", this.status = "ready";
    } catch (e) {
      if (t !== this.loadGeneration) return;
      if (e instanceof vt) {
        this.bootstrapState = {
          frontend_protocol: e.backendProtocol,
          backend_version: e.backendVersion,
          panel_path: "/locklearn",
          authenticated_user_id: "",
          personal_profile: null
        }, this.status = "protocol-mismatch";
        return;
      }
      this.errorMessage = e instanceof Error ? e.message : String(e), this.status = "error";
    }
  }
  selectRoute(t) {
    q(t, this.profiles) && (this.route = t, te(t));
  }
  hardReload() {
    globalThis.location?.reload();
  }
  render() {
    if (this.status === "loading")
      return this.renderState(this.t("state.loading"));
    if (this.status === "protocol-mismatch")
      return v`
        <main>
          <section class="state-card" role="alert">
            <h1>${this.t("state.protocol.title")}</h1>
            <p>${this.t("state.protocol.body")}</p>
            <button class="primary-button" @click=${this.hardReload}>
              ${this.t("state.protocol.reload")}
            </button>
            <div class="meta">
              frontend protocol ${y} · backend protocol
              ${this.bootstrapState?.frontend_protocol ?? "?"} · backend
              ${this.bootstrapState?.backend_version ?? "?"}
            </div>
          </section>
        </main>
      `;
    if (this.status === "error")
      return v`
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
    const t = K(this.profiles);
    return v`
      <div class="shell">
        <header>
          <div class="brand">${this.t("app.title")}</div>
          <nav aria-label="LockLearn">
            ${t.map(
      (e) => v`
                <button
                  class="nav-button"
                  aria-current=${this.route === e.route ? "page" : h}
                  @click=${() => this.selectRoute(e.route)}
                >
                  ${this.t(e.labelKey)}
                </button>
              `
    )}
          </nav>
        </header>
        <main>
          ${this.profiles.length === 0 ? v`<section class="state-card">
                <h1>${this.t("app.title")}</h1>
                <p>${this.t("state.noProfiles")}</p>
              </section>` : v`<section class="page">
                <h1>${this.routeLabel(this.route)}</h1>
                <p>${this.t("route.placeholder")}</p>
              </section>`}
        </main>
      </div>
    `;
  }
  renderState(t) {
    return v`<main><section class="state-card"><p>${t}</p></section></main>`;
  }
  routeLabel(t) {
    const e = K(this.profiles).find((s) => s.route === t);
    return e === void 0 ? this.t("nav.home") : this.t(e.labelKey);
  }
};
z.locklearnFrontendProtocol = y, z.styles = _t`
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
let f = z;
w([
  gt({ attribute: !1 })
], f.prototype, "hass");
w([
  R()
], f.prototype, "status");
w([
  R()
], f.prototype, "route");
w([
  R()
], f.prototype, "bootstrapState");
w([
  R()
], f.prototype, "profiles");
w([
  R()
], f.prototype, "errorMessage");
function se(o) {
  if (typeof document > "u" || document.getElementById(dt) !== null) return;
  const t = document.createElement("div");
  t.id = dt, t.setAttribute("role", "alert"), t.style.cssText = "position:fixed;inset:0;z-index:2147483647;display:grid;place-items:center;padding:24px;background:var(--primary-background-color,#fff);color:var(--primary-text-color,#111);font-family:system-ui,sans-serif";
  const e = document.createElement("div");
  e.style.cssText = "max-width:680px;padding:24px;border:1px solid var(--divider-color,#ddd);border-radius:12px;background:var(--card-background-color,#fff)";
  const s = document.createElement("h1");
  s.textContent = "LockLearn was updated";
  const r = document.createElement("p");
  r.textContent = "An older LockLearn panel is still loaded in this browser. Perform a full browser reload before continuing.";
  const i = document.createElement("p");
  i.textContent = `loaded protocol ${o ?? "unknown"} · current protocol ${y}`;
  const n = document.createElement("button");
  n.textContent = "Reload now", n.addEventListener("click", () => globalThis.location?.reload()), e.append(s, r, i, n), t.append(e), document.body.append(t);
}
const re = customElements.get(
  "locklearn-panel"
), V = Zt(re);
V.kind === "define" ? customElements.define("locklearn-panel", f) : V.kind === "reload" && se(V.existingProtocol);
export {
  f as LockLearnPanel
};
