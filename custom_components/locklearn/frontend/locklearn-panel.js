const U = globalThis, W = U.ShadowRoot && (U.ShadyCSS === void 0 || U.ShadyCSS.nativeShadow) && "adoptedStyleSheets" in Document.prototype && "replace" in CSSStyleSheet.prototype, F = /* @__PURE__ */ Symbol(), Z = /* @__PURE__ */ new WeakMap();
let pt = class {
  constructor(t, e, r) {
    if (this._$cssResult$ = !0, r !== F) throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");
    this.cssText = t, this.t = e;
  }
  get styleSheet() {
    let t = this.o;
    const e = this.t;
    if (W && t === void 0) {
      const r = e !== void 0 && e.length === 1;
      r && (t = Z.get(e)), t === void 0 && ((this.o = t = new CSSStyleSheet()).replaceSync(this.cssText), r && Z.set(e, t));
    }
    return t;
  }
  toString() {
    return this.cssText;
  }
};
const $t = (s) => new pt(typeof s == "string" ? s : s + "", void 0, F), _t = (s, ...t) => {
  const e = s.length === 1 ? s[0] : t.reduce((r, i, o) => r + ((a) => {
    if (a._$cssResult$ === !0) return a.cssText;
    if (typeof a == "number") return a;
    throw Error("Value passed to 'css' function must be a 'css' function result: " + a + ". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.");
  })(i) + s[o + 1], s[0]);
  return new pt(e, s, F);
}, yt = (s, t) => {
  if (W) s.adoptedStyleSheets = t.map((e) => e instanceof CSSStyleSheet ? e : e.styleSheet);
  else for (const e of t) {
    const r = document.createElement("style"), i = U.litNonce;
    i !== void 0 && r.setAttribute("nonce", i), r.textContent = e.cssText, s.appendChild(r);
  }
}, X = W ? (s) => s : (s) => s instanceof CSSStyleSheet ? ((t) => {
  let e = "";
  for (const r of t.cssRules) e += r.cssText;
  return $t(e);
})(s) : s;
const { is: xt, defineProperty: At, getOwnPropertyDescriptor: wt, getOwnPropertyNames: Et, getOwnPropertySymbols: St, getPrototypeOf: kt } = Object, z = globalThis, tt = z.trustedTypes, Pt = tt ? tt.emptyScript : "", Tt = z.reactiveElementPolyfillSupport, P = (s, t) => s, M = { toAttribute(s, t) {
  switch (t) {
    case Boolean:
      s = s ? Pt : null;
      break;
    case Object:
    case Array:
      s = s == null ? s : JSON.stringify(s);
  }
  return s;
}, fromAttribute(s, t) {
  let e = s;
  switch (t) {
    case Boolean:
      e = s !== null;
      break;
    case Number:
      e = s === null ? null : Number(s);
      break;
    case Object:
    case Array:
      try {
        e = JSON.parse(s);
      } catch {
        e = null;
      }
  }
  return e;
} }, G = (s, t) => !xt(s, t), et = { attribute: !0, type: String, converter: M, reflect: !1, useDefault: !1, hasChanged: G };
Symbol.metadata ??= /* @__PURE__ */ Symbol("metadata"), z.litPropertyMetadata ??= /* @__PURE__ */ new WeakMap();
let w = class extends HTMLElement {
  static addInitializer(t) {
    this._$Ei(), (this.l ??= []).push(t);
  }
  static get observedAttributes() {
    return this.finalize(), this._$Eh && [...this._$Eh.keys()];
  }
  static createProperty(t, e = et) {
    if (e.state && (e.attribute = !1), this._$Ei(), this.prototype.hasOwnProperty(t) && ((e = Object.create(e)).wrapped = !0), this.elementProperties.set(t, e), !e.noAccessor) {
      const r = /* @__PURE__ */ Symbol(), i = this.getPropertyDescriptor(t, r, e);
      i !== void 0 && At(this.prototype, t, i);
    }
  }
  static getPropertyDescriptor(t, e, r) {
    const { get: i, set: o } = wt(this.prototype, t) ?? { get() {
      return this[e];
    }, set(a) {
      this[e] = a;
    } };
    return { get: i, set(a) {
      const l = i?.call(this);
      o?.call(this, a), this.requestUpdate(t, l, r);
    }, configurable: !0, enumerable: !0 };
  }
  static getPropertyOptions(t) {
    return this.elementProperties.get(t) ?? et;
  }
  static _$Ei() {
    if (this.hasOwnProperty(P("elementProperties"))) return;
    const t = kt(this);
    t.finalize(), t.l !== void 0 && (this.l = [...t.l]), this.elementProperties = new Map(t.elementProperties);
  }
  static finalize() {
    if (this.hasOwnProperty(P("finalized"))) return;
    if (this.finalized = !0, this._$Ei(), this.hasOwnProperty(P("properties"))) {
      const e = this.properties, r = [...Et(e), ...St(e)];
      for (const i of r) this.createProperty(i, e[i]);
    }
    const t = this[Symbol.metadata];
    if (t !== null) {
      const e = litPropertyMetadata.get(t);
      if (e !== void 0) for (const [r, i] of e) this.elementProperties.set(r, i);
    }
    this._$Eh = /* @__PURE__ */ new Map();
    for (const [e, r] of this.elementProperties) {
      const i = this._$Eu(e, r);
      i !== void 0 && this._$Eh.set(i, e);
    }
    this.elementStyles = this.finalizeStyles(this.styles);
  }
  static finalizeStyles(t) {
    const e = [];
    if (Array.isArray(t)) {
      const r = new Set(t.flat(1 / 0).reverse());
      for (const i of r) e.unshift(X(i));
    } else t !== void 0 && e.push(X(t));
    return e;
  }
  static _$Eu(t, e) {
    const r = e.attribute;
    return r === !1 ? void 0 : typeof r == "string" ? r : typeof t == "string" ? t.toLowerCase() : void 0;
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
    for (const r of e.keys()) this.hasOwnProperty(r) && (t.set(r, this[r]), delete this[r]);
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
  attributeChangedCallback(t, e, r) {
    this._$AK(t, r);
  }
  _$ET(t, e) {
    const r = this.constructor.elementProperties.get(t), i = this.constructor._$Eu(t, r);
    if (i !== void 0 && r.reflect === !0) {
      const o = (r.converter?.toAttribute !== void 0 ? r.converter : M).toAttribute(e, r.type);
      this._$Em = t, o == null ? this.removeAttribute(i) : this.setAttribute(i, o), this._$Em = null;
    }
  }
  _$AK(t, e) {
    const r = this.constructor, i = r._$Eh.get(t);
    if (i !== void 0 && this._$Em !== i) {
      const o = r.getPropertyOptions(i), a = typeof o.converter == "function" ? { fromAttribute: o.converter } : o.converter?.fromAttribute !== void 0 ? o.converter : M;
      this._$Em = i;
      const l = a.fromAttribute(e, o.type);
      this[i] = l ?? this._$Ej?.get(i) ?? l, this._$Em = null;
    }
  }
  requestUpdate(t, e, r, i = !1, o) {
    if (t !== void 0) {
      const a = this.constructor;
      if (i === !1 && (o = this[t]), r ??= a.getPropertyOptions(t), !((r.hasChanged ?? G)(o, e) || r.useDefault && r.reflect && o === this._$Ej?.get(t) && !this.hasAttribute(a._$Eu(t, r)))) return;
      this.C(t, e, r);
    }
    this.isUpdatePending === !1 && (this._$ES = this._$EP());
  }
  C(t, e, { useDefault: r, reflect: i, wrapped: o }, a) {
    r && !(this._$Ej ??= /* @__PURE__ */ new Map()).has(t) && (this._$Ej.set(t, a ?? e ?? this[t]), o !== !0 || a !== void 0) || (this._$AL.has(t) || (this.hasUpdated || r || (e = void 0), this._$AL.set(t, e)), i === !0 && this._$Em !== t && (this._$Eq ??= /* @__PURE__ */ new Set()).add(t));
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
        for (const [i, o] of this._$Ep) this[i] = o;
        this._$Ep = void 0;
      }
      const r = this.constructor.elementProperties;
      if (r.size > 0) for (const [i, o] of r) {
        const { wrapped: a } = o, l = this[i];
        a !== !0 || this._$AL.has(i) || l === void 0 || this.C(i, void 0, o, l);
      }
    }
    let t = !1;
    const e = this._$AL;
    try {
      t = this.shouldUpdate(e), t ? (this.willUpdate(e), this._$EO?.forEach((r) => r.hostUpdate?.()), this.update(e)) : this._$EM();
    } catch (r) {
      throw t = !1, this._$EM(), r;
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
w.elementStyles = [], w.shadowRootOptions = { mode: "open" }, w[P("elementProperties")] = /* @__PURE__ */ new Map(), w[P("finalized")] = /* @__PURE__ */ new Map(), Tt?.({ ReactiveElement: w }), (z.reactiveElementVersions ??= []).push("2.1.2");
const J = globalThis, rt = (s) => s, H = J.trustedTypes, st = H ? H.createPolicy("lit-html", { createHTML: (s) => s }) : void 0, ut = "$lit$", $ = `lit$${Math.random().toFixed(9).slice(2)}$`, ft = "?" + $, Ct = `<${ft}>`, x = document, C = () => x.createComment(""), R = (s) => s === null || typeof s != "object" && typeof s != "function", Q = Array.isArray, Rt = (s) => Q(s) || typeof s?.[Symbol.iterator] == "function", j = `[ 	
\f\r]`, k = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, it = /-->/g, ot = />/g, _ = RegExp(`>|${j}(?:([^\\s"'>=/]+)(${j}*=${j}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`, "g"), at = /'/g, nt = /"/g, mt = /^(?:script|style|textarea|title)$/i, Lt = (s) => (t, ...e) => ({ _$litType$: s, strings: t, values: e }), h = Lt(1), E = /* @__PURE__ */ Symbol.for("lit-noChange"), c = /* @__PURE__ */ Symbol.for("lit-nothing"), lt = /* @__PURE__ */ new WeakMap(), y = x.createTreeWalker(x, 129);
function gt(s, t) {
  if (!Q(s) || !s.hasOwnProperty("raw")) throw Error("invalid template strings array");
  return st !== void 0 ? st.createHTML(t) : t;
}
const Nt = (s, t) => {
  const e = s.length - 1, r = [];
  let i, o = t === 2 ? "<svg>" : t === 3 ? "<math>" : "", a = k;
  for (let l = 0; l < e; l++) {
    const n = s[l];
    let p, u, d = -1, g = 0;
    for (; g < n.length && (a.lastIndex = g, u = a.exec(n), u !== null); ) g = a.lastIndex, a === k ? u[1] === "!--" ? a = it : u[1] !== void 0 ? a = ot : u[2] !== void 0 ? (mt.test(u[2]) && (i = RegExp("</" + u[2], "g")), a = _) : u[3] !== void 0 && (a = _) : a === _ ? u[0] === ">" ? (a = i ?? k, d = -1) : u[1] === void 0 ? d = -2 : (d = a.lastIndex - u[2].length, p = u[1], a = u[3] === void 0 ? _ : u[3] === '"' ? nt : at) : a === nt || a === at ? a = _ : a === it || a === ot ? a = k : (a = _, i = void 0);
    const v = a === _ && s[l + 1].startsWith("/>") ? " " : "";
    o += a === k ? n + Ct : d >= 0 ? (r.push(p), n.slice(0, d) + ut + n.slice(d) + $ + v) : n + $ + (d === -2 ? l : v);
  }
  return [gt(s, o + (s[e] || "<?>") + (t === 2 ? "</svg>" : t === 3 ? "</math>" : "")), r];
};
class L {
  constructor({ strings: t, _$litType$: e }, r) {
    let i;
    this.parts = [];
    let o = 0, a = 0;
    const l = t.length - 1, n = this.parts, [p, u] = Nt(t, e);
    if (this.el = L.createElement(p, r), y.currentNode = this.el.content, e === 2 || e === 3) {
      const d = this.el.content.firstChild;
      d.replaceWith(...d.childNodes);
    }
    for (; (i = y.nextNode()) !== null && n.length < l; ) {
      if (i.nodeType === 1) {
        if (i.hasAttributes()) for (const d of i.getAttributeNames()) if (d.endsWith(ut)) {
          const g = u[a++], v = i.getAttribute(d).split($), O = /([.?@])?(.*)/.exec(g);
          n.push({ type: 1, index: o, name: O[2], strings: v, ctor: O[1] === "." ? Ut : O[1] === "?" ? Mt : O[1] === "@" ? Ht : I }), i.removeAttribute(d);
        } else d.startsWith($) && (n.push({ type: 6, index: o }), i.removeAttribute(d));
        if (mt.test(i.tagName)) {
          const d = i.textContent.split($), g = d.length - 1;
          if (g > 0) {
            i.textContent = H ? H.emptyScript : "";
            for (let v = 0; v < g; v++) i.append(d[v], C()), y.nextNode(), n.push({ type: 2, index: ++o });
            i.append(d[g], C());
          }
        }
      } else if (i.nodeType === 8) if (i.data === ft) n.push({ type: 2, index: o });
      else {
        let d = -1;
        for (; (d = i.data.indexOf($, d + 1)) !== -1; ) n.push({ type: 7, index: o }), d += $.length - 1;
      }
      o++;
    }
  }
  static createElement(t, e) {
    const r = x.createElement("template");
    return r.innerHTML = t, r;
  }
}
function S(s, t, e = s, r) {
  if (t === E) return t;
  let i = r !== void 0 ? e._$Co?.[r] : e._$Cl;
  const o = R(t) ? void 0 : t._$litDirective$;
  return i?.constructor !== o && (i?._$AO?.(!1), o === void 0 ? i = void 0 : (i = new o(s), i._$AT(s, e, r)), r !== void 0 ? (e._$Co ??= [])[r] = i : e._$Cl = i), i !== void 0 && (t = S(s, i._$AS(s, t.values), i, r)), t;
}
class Ot {
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
    const { el: { content: e }, parts: r } = this._$AD, i = (t?.creationScope ?? x).importNode(e, !0);
    y.currentNode = i;
    let o = y.nextNode(), a = 0, l = 0, n = r[0];
    for (; n !== void 0; ) {
      if (a === n.index) {
        let p;
        n.type === 2 ? p = new N(o, o.nextSibling, this, t) : n.type === 1 ? p = new n.ctor(o, n.name, n.strings, this, t) : n.type === 6 && (p = new Dt(o, this, t)), this._$AV.push(p), n = r[++l];
      }
      a !== n?.index && (o = y.nextNode(), a++);
    }
    return y.currentNode = x, i;
  }
  p(t) {
    let e = 0;
    for (const r of this._$AV) r !== void 0 && (r.strings !== void 0 ? (r._$AI(t, r, e), e += r.strings.length - 2) : r._$AI(t[e])), e++;
  }
}
class N {
  get _$AU() {
    return this._$AM?._$AU ?? this._$Cv;
  }
  constructor(t, e, r, i) {
    this.type = 2, this._$AH = c, this._$AN = void 0, this._$AA = t, this._$AB = e, this._$AM = r, this.options = i, this._$Cv = i?.isConnected ?? !0;
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
    t = S(this, t, e), R(t) ? t === c || t == null || t === "" ? (this._$AH !== c && this._$AR(), this._$AH = c) : t !== this._$AH && t !== E && this._(t) : t._$litType$ !== void 0 ? this.$(t) : t.nodeType !== void 0 ? this.T(t) : Rt(t) ? this.k(t) : this._(t);
  }
  O(t) {
    return this._$AA.parentNode.insertBefore(t, this._$AB);
  }
  T(t) {
    this._$AH !== t && (this._$AR(), this._$AH = this.O(t));
  }
  _(t) {
    this._$AH !== c && R(this._$AH) ? this._$AA.nextSibling.data = t : this.T(x.createTextNode(t)), this._$AH = t;
  }
  $(t) {
    const { values: e, _$litType$: r } = t, i = typeof r == "number" ? this._$AC(t) : (r.el === void 0 && (r.el = L.createElement(gt(r.h, r.h[0]), this.options)), r);
    if (this._$AH?._$AD === i) this._$AH.p(e);
    else {
      const o = new Ot(i, this), a = o.u(this.options);
      o.p(e), this.T(a), this._$AH = o;
    }
  }
  _$AC(t) {
    let e = lt.get(t.strings);
    return e === void 0 && lt.set(t.strings, e = new L(t)), e;
  }
  k(t) {
    Q(this._$AH) || (this._$AH = [], this._$AR());
    const e = this._$AH;
    let r, i = 0;
    for (const o of t) i === e.length ? e.push(r = new N(this.O(C()), this.O(C()), this, this.options)) : r = e[i], r._$AI(o), i++;
    i < e.length && (this._$AR(r && r._$AB.nextSibling, i), e.length = i);
  }
  _$AR(t = this._$AA.nextSibling, e) {
    for (this._$AP?.(!1, !0, e); t !== this._$AB; ) {
      const r = rt(t).nextSibling;
      rt(t).remove(), t = r;
    }
  }
  setConnected(t) {
    this._$AM === void 0 && (this._$Cv = t, this._$AP?.(t));
  }
}
class I {
  get tagName() {
    return this.element.tagName;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  constructor(t, e, r, i, o) {
    this.type = 1, this._$AH = c, this._$AN = void 0, this.element = t, this.name = e, this._$AM = i, this.options = o, r.length > 2 || r[0] !== "" || r[1] !== "" ? (this._$AH = Array(r.length - 1).fill(new String()), this.strings = r) : this._$AH = c;
  }
  _$AI(t, e = this, r, i) {
    const o = this.strings;
    let a = !1;
    if (o === void 0) t = S(this, t, e, 0), a = !R(t) || t !== this._$AH && t !== E, a && (this._$AH = t);
    else {
      const l = t;
      let n, p;
      for (t = o[0], n = 0; n < o.length - 1; n++) p = S(this, l[r + n], e, n), p === E && (p = this._$AH[n]), a ||= !R(p) || p !== this._$AH[n], p === c ? t = c : t !== c && (t += (p ?? "") + o[n + 1]), this._$AH[n] = p;
    }
    a && !i && this.j(t);
  }
  j(t) {
    t === c ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, t ?? "");
  }
}
class Ut extends I {
  constructor() {
    super(...arguments), this.type = 3;
  }
  j(t) {
    this.element[this.name] = t === c ? void 0 : t;
  }
}
class Mt extends I {
  constructor() {
    super(...arguments), this.type = 4;
  }
  j(t) {
    this.element.toggleAttribute(this.name, !!t && t !== c);
  }
}
class Ht extends I {
  constructor(t, e, r, i, o) {
    super(t, e, r, i, o), this.type = 5;
  }
  _$AI(t, e = this) {
    if ((t = S(this, t, e, 0) ?? c) === E) return;
    const r = this._$AH, i = t === c && r !== c || t.capture !== r.capture || t.once !== r.once || t.passive !== r.passive, o = t !== c && (r === c || i);
    i && this.element.removeEventListener(this.name, this, r), o && this.element.addEventListener(this.name, this, t), this._$AH = t;
  }
  handleEvent(t) {
    typeof this._$AH == "function" ? this._$AH.call(this.options?.host ?? this.element, t) : this._$AH.handleEvent(t);
  }
}
class Dt {
  constructor(t, e, r) {
    this.element = t, this.type = 6, this._$AN = void 0, this._$AM = e, this.options = r;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AI(t) {
    S(this, t);
  }
}
const zt = J.litHtmlPolyfillSupport;
zt?.(L, N), (J.litHtmlVersions ??= []).push("3.3.3");
const It = (s, t, e) => {
  const r = e?.renderBefore ?? t;
  let i = r._$litPart$;
  if (i === void 0) {
    const o = e?.renderBefore ?? null;
    r._$litPart$ = i = new N(t.insertBefore(C(), o), o, void 0, e ?? {});
  }
  return i._$AI(s), i;
};
const Y = globalThis;
class T extends w {
  constructor() {
    super(...arguments), this.renderOptions = { host: this }, this._$Do = void 0;
  }
  createRenderRoot() {
    const t = super.createRenderRoot();
    return this.renderOptions.renderBefore ??= t.firstChild, t;
  }
  update(t) {
    const e = this.render();
    this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(t), this._$Do = It(e, this.renderRoot, this.renderOptions);
  }
  connectedCallback() {
    super.connectedCallback(), this._$Do?.setConnected(!0);
  }
  disconnectedCallback() {
    super.disconnectedCallback(), this._$Do?.setConnected(!1);
  }
  render() {
    return E;
  }
}
T._$litElement$ = !0, T.finalized = !0, Y.litElementHydrateSupport?.({ LitElement: T });
const jt = Y.litElementPolyfillSupport;
jt?.({ LitElement: T });
(Y.litElementVersions ??= []).push("4.2.2");
const Vt = { attribute: !0, type: String, converter: M, reflect: !1, hasChanged: G }, qt = (s = Vt, t, e) => {
  const { kind: r, metadata: i } = e;
  let o = globalThis.litPropertyMetadata.get(i);
  if (o === void 0 && globalThis.litPropertyMetadata.set(i, o = /* @__PURE__ */ new Map()), r === "setter" && ((s = Object.create(s)).wrapped = !0), o.set(e.name, s), r === "accessor") {
    const { name: a } = e;
    return { set(l) {
      const n = t.get.call(this);
      t.set.call(this, l), this.requestUpdate(a, n, s, !0, l);
    }, init(l) {
      return l !== void 0 && this.C(a, void 0, s, l), l;
    } };
  }
  if (r === "setter") {
    const { name: a } = e;
    return function(l) {
      const n = this[a];
      t.call(this, l), this.requestUpdate(a, n, s, !0, l);
    };
  }
  throw Error("Unsupported decorator location: " + r);
};
function bt(s) {
  return (t, e) => typeof e == "object" ? qt(s, t, e) : ((r, i, o) => {
    const a = i.hasOwnProperty(o);
    return i.constructor.createProperty(o, r), a ? Object.getOwnPropertyDescriptor(i, o) : void 0;
  })(s, t, e);
}
function b(s) {
  return bt({ ...s, state: !0, attribute: !1 });
}
const dt = {
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
function Bt(s) {
  const t = s.toLowerCase();
  return t === "fr" || t.startsWith("fr-") ? "fr" : "en";
}
function Kt(s, t) {
  return dt[s][t] ?? dt.en[t];
}
const ct = [
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
function K(s) {
  return s.length === 0 ? [] : new Set(s.map((e) => e.role)).has("owner") ? [...ct, ...Wt] : ct;
}
function V(s, t) {
  return K(t).some((e) => e.route === s);
}
function Ft(s) {
  return {
    mine: s.filter((t) => t.role === "owner"),
    shared: s.filter((t) => t.role !== "owner")
  };
}
function Gt(s, t) {
  const e = t.personal_profile?.profile_id;
  if (e !== void 0 && s.some((i) => i.profile_id === e))
    return e;
  const r = s.find((i) => i.role === "owner");
  return r !== void 0 ? r.profile_id : s[0]?.profile_id ?? null;
}
const A = 1;
class vt extends Error {
  constructor(t, e, r) {
    super(
      `LockLearn frontend protocol ${t} does not match backend protocol ${e}`
    ), this.frontendProtocol = t, this.backendProtocol = e, this.backendVersion = r;
  }
}
async function Jt(s) {
  const t = await s.callWS({
    type: "locklearn/bootstrap"
  });
  if (t.frontend_protocol !== A)
    throw new vt(
      A,
      t.frontend_protocol,
      t.backend_version
    );
  return t;
}
async function Qt(s) {
  const t = [];
  let e = null;
  do {
    const r = await s.callWS({
      type: "locklearn/profiles/list",
      limit: 100,
      ...e === null ? {} : { cursor: e }
    });
    t.push(...r.items), e = r.cursor;
  } while (e !== null);
  return t;
}
async function Yt(s, t) {
  return s.callWS({
    type: "locklearn/dashboard/get",
    profile_id: t
  });
}
function Zt(s) {
  if (s === void 0) return { kind: "define" };
  const t = typeof s.locklearnFrontendProtocol == "number" ? s.locklearnFrontendProtocol : null;
  return t === A ? { kind: "reuse" } : {
    kind: "reload",
    existingProtocol: t,
    frontendProtocol: A
  };
}
function Xt(s, t, e) {
  return !s && t && e;
}
const te = [
  "home",
  "learn",
  "quiz",
  "exam",
  "stats",
  "profiles",
  "tracks",
  "packs",
  "settings"
], ee = "home";
function q(s) {
  const e = s.replace(/^\/+|\/+$/g, "").split("/").filter(Boolean), r = e[0] === "locklearn" ? e[1] : e[0];
  return te.includes(r) ? r : ee;
}
function re(s) {
  return s === "home" ? "/locklearn" : `/locklearn/${s}`;
}
function se(s) {
  const t = re(s);
  globalThis.location?.pathname !== t && (globalThis.history?.pushState({}, "", t), globalThis.dispatchEvent?.(new PopStateEvent("popstate")));
}
var ie = Object.defineProperty, m = (s, t, e, r) => {
  for (var i = void 0, o = s.length - 1, a; o >= 0; o--)
    (a = s[o]) && (i = a(t, e, i) || i);
  return i && ie(t, e, i), i;
};
const ht = "locklearn-hard-reload-required", D = class D extends T {
  constructor() {
    super(...arguments), this.status = "loading", this.activeRoute = q(
      globalThis.location?.pathname ?? "/locklearn"
    ), this.profiles = [], this.selectedProfileId = null, this.dashboardLoading = !1, this.dashboardError = "", this.errorMessage = "", this.loadGeneration = 0, this.dashboardGeneration = 0, this.initialLoadStarted = !1, this.handlePopState = () => {
      const t = q(globalThis.location?.pathname ?? "/locklearn");
      this.activeRoute = V(t, this.profiles) ? t : "home";
    };
  }
  connectedCallback() {
    super.connectedCallback(), globalThis.addEventListener?.("popstate", this.handlePopState);
  }
  disconnectedCallback() {
    globalThis.removeEventListener?.("popstate", this.handlePopState), super.disconnectedCallback();
  }
  updated(t) {
    Xt(
      this.initialLoadStarted,
      t.has("hass"),
      this.hass !== void 0
    ) && (this.initialLoadStarted = !0, this.load());
  }
  locale() {
    const t = this.hass?.locale?.language ?? this.hass?.language ?? globalThis.navigator?.language ?? "en";
    return Bt(t);
  }
  t(t) {
    return Kt(this.locale(), t);
  }
  async load() {
    if (this.hass === void 0) return;
    const t = ++this.loadGeneration;
    this.status = "loading", this.errorMessage = "";
    try {
      const e = await Jt(this.hass), r = await Qt(this.hass);
      if (t !== this.loadGeneration) return;
      this.bootstrapState = e, this.profiles = r, this.selectedProfileId = Gt(r, e);
      const i = q(globalThis.location?.pathname ?? e.panel_path);
      this.activeRoute = V(i, r) ? i : "home", this.status = "ready", this.loadDashboard();
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
    V(t, this.profiles) && (this.activeRoute = t, se(t));
  }
  selectProfile(t) {
    const e = t.currentTarget;
    if (!(e instanceof HTMLSelectElement)) return;
    const r = e.value;
    this.profiles.some((i) => i.profile_id === r) && (this.selectedProfileId = r, this.loadDashboard());
  }
  async loadDashboard() {
    if (this.hass === void 0 || this.selectedProfileId === null) {
      this.dashboard = void 0, this.dashboardError = "";
      return;
    }
    const t = ++this.dashboardGeneration;
    this.dashboardLoading = !0, this.dashboardError = "";
    try {
      const e = await Yt(this.hass, this.selectedProfileId);
      if (t !== this.dashboardGeneration) return;
      this.dashboard = e;
    } catch (e) {
      if (t !== this.dashboardGeneration) return;
      this.dashboard = void 0, this.dashboardError = e instanceof Error ? e.message : String(e);
    } finally {
      t === this.dashboardGeneration && (this.dashboardLoading = !1);
    }
  }
  hardReload() {
    globalThis.location?.reload();
  }
  render() {
    if (this.status === "loading")
      return this.renderState(this.t("state.loading"));
    if (this.status === "protocol-mismatch")
      return h`
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
      return h`
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
    const t = K(this.profiles), e = Ft(this.profiles);
    return h`
      <div class="shell">
        <header>
          <div class="brand">${this.t("app.title")}</div>
          ${this.profiles.length === 0 ? c : h`<label class="profile-switcher">
                <span>${this.t("profile.select")}</span>
                <select
                  .value=${this.selectedProfileId ?? ""}
                  @change=${this.selectProfile}
                >
                  ${e.mine.length === 0 ? c : h`<optgroup label=${this.t("profile.mine")}>
                        ${e.mine.map(
      (r) => h`<option value=${r.profile_id}>${r.name}</option>`
    )}
                      </optgroup>`}
                  ${e.shared.length === 0 ? c : h`<optgroup label=${this.t("profile.shared")}>
                        ${e.shared.map(
      (r) => h`<option value=${r.profile_id}>${r.name}</option>`
    )}
                      </optgroup>`}
                </select>
              </label>`}
          <nav aria-label="LockLearn">
            ${t.map(
      (r) => h`
                <button
                  class="nav-button"
                  aria-current=${this.activeRoute === r.route ? "page" : c}
                  @click=${() => this.selectRoute(r.route)}
                >
                  ${this.t(r.labelKey)}
                </button>
              `
    )}
          </nav>
        </header>
        <main>
          ${this.profiles.length === 0 ? h`<section class="state-card">
                <h1>${this.t("app.title")}</h1>
                <p>${this.t("state.noProfiles")}</p>
              </section>` : this.activeRoute === "home" ? this.renderHome() : h`<section class="page">
                  <h1>${this.routeLabel(this.activeRoute)}</h1>
                  <p>${this.t("route.placeholder")}</p>
                </section>`}
        </main>
      </div>
    `;
  }
  renderHome() {
    return this.dashboardLoading ? h`<section class="page"><p>${this.t("dashboard.loading")}</p></section>` : this.dashboardError ? h`<section class="page" role="alert">
        <h1>${this.t("dashboard.error")}</h1>
        <p>${this.dashboardError}</p>
      </section>` : this.dashboard === void 0 ? h`<section class="page"><p>${this.t("dashboard.noTracks")}</p></section>` : h`
      <section>
        <div class="home-header">
          <h1>${this.dashboard.profile.name}</h1>
        </div>
        ${this.dashboard.tracks.length === 0 ? h`<section class="page"><p>${this.t("dashboard.noTracks")}</p></section>` : h`<div class="track-grid">
              ${this.dashboard.tracks.map((t) => h`
                <article class="track-card">
                  <h2>${t.name}</h2>
                  <div class="track-languages">
                    ${t.source_language} → ${t.target_language}
                  </div>
                  <div class="metrics">
                    <div class="metric">
                      <div class="metric-label">${this.t("dashboard.dueToday")}</div>
                      <div class="metric-value">${t.due_today}</div>
                    </div>
                    <div class="metric">
                      <div class="metric-label">${this.t("dashboard.accuracy")}</div>
                      <div class="metric-value">${this.formatAccuracy(t.recent_verified_accuracy.accuracy)}</div>
                      <div class="metric-detail">
                        ${t.recent_verified_accuracy.correct}/${t.recent_verified_accuracy.total}
                      </div>
                    </div>
                    <div class="metric">
                      <div class="metric-label">${this.t("dashboard.latestVerified")}</div>
                      <div class="metric-value">
                        ${t.recent_verified_retention === null ? this.t("dashboard.noVerified") : t.recent_verified_retention.retained ? this.t("dashboard.retained") : this.t("dashboard.notRetained")}
                      </div>
                      ${t.recent_verified_retention === null ? c : h`<div class="metric-detail">
                            ${this.formatDateTime(
      t.recent_verified_retention.created_at_utc,
      this.dashboard?.profile.timezone
    )}
                          </div>`}
                    </div>
                    <div class="metric">
                      <div class="metric-label">${this.t("dashboard.lastSession")}</div>
                      <div class="metric-value">
                        ${t.last_session === null ? this.t("dashboard.noSession") : `${t.last_session.answered_count}/${t.last_session.question_count} ${this.t("dashboard.answered")}`}
                      </div>
                      ${t.last_session === null ? c : h`<div class="metric-detail">
                            ${this.formatDateTime(
      t.last_session.completed_at_utc ?? t.last_session.last_activity_at_utc,
      this.dashboard?.profile.timezone
    )}
                          </div>`}
                    </div>
                    <div class="metric">
                      <div class="metric-label">${this.t("dashboard.nextNotification")}</div>
                      <div class="metric-value">
                        ${t.next_notification === null ? this.t("dashboard.noNotification") : this.formatDateTime(
      t.next_notification.effective_for_utc,
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
  formatAccuracy(t) {
    return t === null ? "—" : new Intl.NumberFormat(this.locale(), {
      style: "percent",
      maximumFractionDigits: 0
    }).format(t);
  }
  formatDateTime(t, e) {
    const r = new Date(t);
    return Number.isNaN(r.getTime()) ? "—" : new Intl.DateTimeFormat(this.locale(), {
      dateStyle: "short",
      timeStyle: "short",
      ...e === void 0 ? {} : { timeZone: e }
    }).format(r);
  }
  renderState(t) {
    return h`<main><section class="state-card"><p>${t}</p></section></main>`;
  }
  routeLabel(t) {
    const e = K(this.profiles).find((r) => r.route === t);
    return e === void 0 ? this.t("nav.home") : this.t(e.labelKey);
  }
};
D.locklearnFrontendProtocol = A, D.styles = _t`
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
let f = D;
m([
  bt({ attribute: !1 })
], f.prototype, "hass");
m([
  b()
], f.prototype, "status");
m([
  b()
], f.prototype, "activeRoute");
m([
  b()
], f.prototype, "bootstrapState");
m([
  b()
], f.prototype, "profiles");
m([
  b()
], f.prototype, "selectedProfileId");
m([
  b()
], f.prototype, "dashboard");
m([
  b()
], f.prototype, "dashboardLoading");
m([
  b()
], f.prototype, "dashboardError");
m([
  b()
], f.prototype, "errorMessage");
function oe(s) {
  if (typeof document > "u" || document.getElementById(ht) !== null) return;
  const t = document.createElement("div");
  t.id = ht, t.setAttribute("role", "alert"), t.style.cssText = "position:fixed;inset:0;z-index:2147483647;display:grid;place-items:center;padding:24px;background:var(--primary-background-color,#fff);color:var(--primary-text-color,#111);font-family:system-ui,sans-serif";
  const e = document.createElement("div");
  e.style.cssText = "max-width:680px;padding:24px;border:1px solid var(--divider-color,#ddd);border-radius:12px;background:var(--card-background-color,#fff)";
  const r = document.createElement("h1");
  r.textContent = "LockLearn was updated";
  const i = document.createElement("p");
  i.textContent = "An older LockLearn panel is still loaded in this browser. Perform a full browser reload before continuing.";
  const o = document.createElement("p");
  o.textContent = `loaded protocol ${s ?? "unknown"} · current protocol ${A}`;
  const a = document.createElement("button");
  a.textContent = "Reload now", a.addEventListener("click", () => globalThis.location?.reload()), e.append(r, i, o, a), t.append(e), document.body.append(t);
}
const ae = customElements.get(
  "locklearn-panel"
), B = Zt(ae);
B.kind === "define" ? customElements.define("locklearn-panel", f) : B.kind === "reload" && oe(B.existingProtocol);
export {
  f as LockLearnPanel
};
