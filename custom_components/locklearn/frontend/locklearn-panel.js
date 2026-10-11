const ge = globalThis, Re = ge.ShadowRoot && (ge.ShadyCSS === void 0 || ge.ShadyCSS.nativeShadow) && "adoptedStyleSheets" in Document.prototype && "replace" in CSSStyleSheet.prototype, Ee = /* @__PURE__ */ Symbol(), Ke = /* @__PURE__ */ new WeakMap();
let _t = class {
  constructor(e, t, i) {
    if (this._$cssResult$ = !0, i !== Ee) throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");
    this.cssText = e, this.t = t;
  }
  get styleSheet() {
    let e = this.o;
    const t = this.t;
    if (Re && e === void 0) {
      const i = t !== void 0 && t.length === 1;
      i && (e = Ke.get(t)), e === void 0 && ((this.o = e = new CSSStyleSheet()).replaceSync(this.cssText), i && Ke.set(t, e));
    }
    return e;
  }
  toString() {
    return this.cssText;
  }
};
const Ot = (s) => new _t(typeof s == "string" ? s : s + "", void 0, Ee), N = (s, ...e) => {
  const t = s.length === 1 ? s[0] : e.reduce((i, a, o) => i + ((n) => {
    if (n._$cssResult$ === !0) return n.cssText;
    if (typeof n == "number") return n;
    throw Error("Value passed to 'css' function must be a 'css' function result: " + n + ". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.");
  })(a) + s[o + 1], s[0]);
  return new _t(t, s, Ee);
}, Wt = (s, e) => {
  if (Re) s.adoptedStyleSheets = e.map((t) => t instanceof CSSStyleSheet ? t : t.styleSheet);
  else for (const t of e) {
    const i = document.createElement("style"), a = ge.litNonce;
    a !== void 0 && i.setAttribute("nonce", a), i.textContent = t.cssText, s.appendChild(i);
  }
}, Ge = Re ? (s) => s : (s) => s instanceof CSSStyleSheet ? ((e) => {
  let t = "";
  for (const i of e.cssRules) t += i.cssText;
  return Ot(t);
})(s) : s;
const { is: Vt, defineProperty: Bt, getOwnPropertyDescriptor: Kt, getOwnPropertyNames: Gt, getOwnPropertySymbols: Qt, getPrototypeOf: Yt } = Object, ye = globalThis, Qe = ye.trustedTypes, Zt = Qe ? Qe.emptyScript : "", Jt = ye.reactiveElementPolyfillSupport, ie = (s, e) => s, fe = { toAttribute(s, e) {
  switch (e) {
    case Boolean:
      s = s ? Zt : null;
      break;
    case Object:
    case Array:
      s = s == null ? s : JSON.stringify(s);
  }
  return s;
}, fromAttribute(s, e) {
  let t = s;
  switch (e) {
    case Boolean:
      t = s !== null;
      break;
    case Number:
      t = s === null ? null : Number(s);
      break;
    case Object:
    case Array:
      try {
        t = JSON.parse(s);
      } catch {
        t = null;
      }
  }
  return t;
} }, Le = (s, e) => !Vt(s, e), Ye = { attribute: !0, type: String, converter: fe, reflect: !1, useDefault: !1, hasChanged: Le };
Symbol.metadata ??= /* @__PURE__ */ Symbol("metadata"), ye.litPropertyMetadata ??= /* @__PURE__ */ new WeakMap();
let G = class extends HTMLElement {
  static addInitializer(e) {
    this._$Ei(), (this.l ??= []).push(e);
  }
  static get observedAttributes() {
    return this.finalize(), this._$Eh && [...this._$Eh.keys()];
  }
  static createProperty(e, t = Ye) {
    if (t.state && (t.attribute = !1), this._$Ei(), this.prototype.hasOwnProperty(e) && ((t = Object.create(t)).wrapped = !0), this.elementProperties.set(e, t), !t.noAccessor) {
      const i = /* @__PURE__ */ Symbol(), a = this.getPropertyDescriptor(e, i, t);
      a !== void 0 && Bt(this.prototype, e, a);
    }
  }
  static getPropertyDescriptor(e, t, i) {
    const { get: a, set: o } = Kt(this.prototype, e) ?? { get() {
      return this[t];
    }, set(n) {
      this[t] = n;
    } };
    return { get: a, set(n) {
      const u = a?.call(this);
      o?.call(this, n), this.requestUpdate(e, u, i);
    }, configurable: !0, enumerable: !0 };
  }
  static getPropertyOptions(e) {
    return this.elementProperties.get(e) ?? Ye;
  }
  static _$Ei() {
    if (this.hasOwnProperty(ie("elementProperties"))) return;
    const e = Yt(this);
    e.finalize(), e.l !== void 0 && (this.l = [...e.l]), this.elementProperties = new Map(e.elementProperties);
  }
  static finalize() {
    if (this.hasOwnProperty(ie("finalized"))) return;
    if (this.finalized = !0, this._$Ei(), this.hasOwnProperty(ie("properties"))) {
      const t = this.properties, i = [...Gt(t), ...Qt(t)];
      for (const a of i) this.createProperty(a, t[a]);
    }
    const e = this[Symbol.metadata];
    if (e !== null) {
      const t = litPropertyMetadata.get(e);
      if (t !== void 0) for (const [i, a] of t) this.elementProperties.set(i, a);
    }
    this._$Eh = /* @__PURE__ */ new Map();
    for (const [t, i] of this.elementProperties) {
      const a = this._$Eu(t, i);
      a !== void 0 && this._$Eh.set(a, t);
    }
    this.elementStyles = this.finalizeStyles(this.styles);
  }
  static finalizeStyles(e) {
    const t = [];
    if (Array.isArray(e)) {
      const i = new Set(e.flat(1 / 0).reverse());
      for (const a of i) t.unshift(Ge(a));
    } else e !== void 0 && t.push(Ge(e));
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
    return Wt(e, this.constructor.elementStyles), e;
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
    const i = this.constructor.elementProperties.get(e), a = this.constructor._$Eu(e, i);
    if (a !== void 0 && i.reflect === !0) {
      const o = (i.converter?.toAttribute !== void 0 ? i.converter : fe).toAttribute(t, i.type);
      this._$Em = e, o == null ? this.removeAttribute(a) : this.setAttribute(a, o), this._$Em = null;
    }
  }
  _$AK(e, t) {
    const i = this.constructor, a = i._$Eh.get(e);
    if (a !== void 0 && this._$Em !== a) {
      const o = i.getPropertyOptions(a), n = typeof o.converter == "function" ? { fromAttribute: o.converter } : o.converter?.fromAttribute !== void 0 ? o.converter : fe;
      this._$Em = a;
      const u = n.fromAttribute(t, o.type);
      this[a] = u ?? this._$Ej?.get(a) ?? u, this._$Em = null;
    }
  }
  requestUpdate(e, t, i, a = !1, o) {
    if (e !== void 0) {
      const n = this.constructor;
      if (a === !1 && (o = this[e]), i ??= n.getPropertyOptions(e), !((i.hasChanged ?? Le)(o, t) || i.useDefault && i.reflect && o === this._$Ej?.get(e) && !this.hasAttribute(n._$Eu(e, i)))) return;
      this.C(e, t, i);
    }
    this.isUpdatePending === !1 && (this._$ES = this._$EP());
  }
  C(e, t, { useDefault: i, reflect: a, wrapped: o }, n) {
    i && !(this._$Ej ??= /* @__PURE__ */ new Map()).has(e) && (this._$Ej.set(e, n ?? t ?? this[e]), o !== !0 || n !== void 0) || (this._$AL.has(e) || (this.hasUpdated || i || (t = void 0), this._$AL.set(e, t)), a === !0 && this._$Em !== e && (this._$Eq ??= /* @__PURE__ */ new Set()).add(e));
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
        for (const [a, o] of this._$Ep) this[a] = o;
        this._$Ep = void 0;
      }
      const i = this.constructor.elementProperties;
      if (i.size > 0) for (const [a, o] of i) {
        const { wrapped: n } = o, u = this[a];
        n !== !0 || this._$AL.has(a) || u === void 0 || this.C(a, void 0, o, u);
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
G.elementStyles = [], G.shadowRootOptions = { mode: "open" }, G[ie("elementProperties")] = /* @__PURE__ */ new Map(), G[ie("finalized")] = /* @__PURE__ */ new Map(), Jt?.({ ReactiveElement: G }), (ye.reactiveElementVersions ??= []).push("2.1.2");
const Ne = globalThis, Ze = (s) => s, ve = Ne.trustedTypes, Je = ve ? ve.createPolicy("lit-html", { createHTML: (s) => s }) : void 0, xt = "$lit$", D = `lit$${Math.random().toFixed(9).slice(2)}$`, St = "?" + D, Xt = `<${St}>`, F = document, ae = () => F.createComment(""), re = (s) => s === null || typeof s != "object" && typeof s != "function", Me = Array.isArray, ei = (s) => Me(s) || typeof s?.[Symbol.iterator] == "function", we = `[ 	
\f\r]`, J = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, Xe = /-->/g, et = />/g, H = RegExp(`>|${we}(?:([^\\s"'>=/]+)(${we}*=${we}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`, "g"), tt = /'/g, it = /"/g, qt = /^(?:script|style|textarea|title)$/i, ti = (s) => (e, ...t) => ({ _$litType$: s, strings: e, values: t }), r = ti(1), Q = /* @__PURE__ */ Symbol.for("lit-noChange"), l = /* @__PURE__ */ Symbol.for("lit-nothing"), st = /* @__PURE__ */ new WeakMap(), U = F.createTreeWalker(F, 129);
function Tt(s, e) {
  if (!Me(s) || !s.hasOwnProperty("raw")) throw Error("invalid template strings array");
  return Je !== void 0 ? Je.createHTML(e) : e;
}
const ii = (s, e) => {
  const t = s.length - 1, i = [];
  let a, o = e === 2 ? "<svg>" : e === 3 ? "<math>" : "", n = J;
  for (let u = 0; u < t; u++) {
    const d = s[u];
    let h, $, m = -1, x = 0;
    for (; x < d.length && (n.lastIndex = x, $ = n.exec(d), $ !== null); ) x = n.lastIndex, n === J ? $[1] === "!--" ? n = Xe : $[1] !== void 0 ? n = et : $[2] !== void 0 ? (qt.test($[2]) && (a = RegExp("</" + $[2], "g")), n = H) : $[3] !== void 0 && (n = H) : n === H ? $[0] === ">" ? (n = a ?? J, m = -1) : $[1] === void 0 ? m = -2 : (m = n.lastIndex - $[2].length, h = $[1], n = $[3] === void 0 ? H : $[3] === '"' ? it : tt) : n === it || n === tt ? n = H : n === Xe || n === et ? n = J : (n = H, a = void 0);
    const M = n === H && s[u + 1].startsWith("/>") ? " " : "";
    o += n === J ? d + Xt : m >= 0 ? (i.push(h), d.slice(0, m) + xt + d.slice(m) + D + M) : d + D + (m === -2 ? u : M);
  }
  return [Tt(s, o + (s[t] || "<?>") + (e === 2 ? "</svg>" : e === 3 ? "</math>" : "")), i];
};
class ne {
  constructor({ strings: e, _$litType$: t }, i) {
    let a;
    this.parts = [];
    let o = 0, n = 0;
    const u = e.length - 1, d = this.parts, [h, $] = ii(e, t);
    if (this.el = ne.createElement(h, i), U.currentNode = this.el.content, t === 2 || t === 3) {
      const m = this.el.content.firstChild;
      m.replaceWith(...m.childNodes);
    }
    for (; (a = U.nextNode()) !== null && d.length < u; ) {
      if (a.nodeType === 1) {
        if (a.hasAttributes()) for (const m of a.getAttributeNames()) if (m.endsWith(xt)) {
          const x = $[n++], M = a.getAttribute(m).split(D), ce = /([.?@])?(.*)/.exec(x);
          d.push({ type: 1, index: o, name: ce[2], strings: M, ctor: ce[1] === "." ? ai : ce[1] === "?" ? ri : ce[1] === "@" ? ni : $e }), a.removeAttribute(m);
        } else m.startsWith(D) && (d.push({ type: 6, index: o }), a.removeAttribute(m));
        if (qt.test(a.tagName)) {
          const m = a.textContent.split(D), x = m.length - 1;
          if (x > 0) {
            a.textContent = ve ? ve.emptyScript : "";
            for (let M = 0; M < x; M++) a.append(m[M], ae()), U.nextNode(), d.push({ type: 2, index: ++o });
            a.append(m[x], ae());
          }
        }
      } else if (a.nodeType === 8) if (a.data === St) d.push({ type: 2, index: o });
      else {
        let m = -1;
        for (; (m = a.data.indexOf(D, m + 1)) !== -1; ) d.push({ type: 7, index: o }), m += D.length - 1;
      }
      o++;
    }
  }
  static createElement(e, t) {
    const i = F.createElement("template");
    return i.innerHTML = e, i;
  }
}
function Y(s, e, t = s, i) {
  if (e === Q) return e;
  let a = i !== void 0 ? t._$Co?.[i] : t._$Cl;
  const o = re(e) ? void 0 : e._$litDirective$;
  return a?.constructor !== o && (a?._$AO?.(!1), o === void 0 ? a = void 0 : (a = new o(s), a._$AT(s, t, i)), i !== void 0 ? (t._$Co ??= [])[i] = a : t._$Cl = a), a !== void 0 && (e = Y(s, a._$AS(s, e.values), a, i)), e;
}
class si {
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
    const { el: { content: t }, parts: i } = this._$AD, a = (e?.creationScope ?? F).importNode(t, !0);
    U.currentNode = a;
    let o = U.nextNode(), n = 0, u = 0, d = i[0];
    for (; d !== void 0; ) {
      if (n === d.index) {
        let h;
        d.type === 2 ? h = new oe(o, o.nextSibling, this, e) : d.type === 1 ? h = new d.ctor(o, d.name, d.strings, this, e) : d.type === 6 && (h = new oi(o, this, e)), this._$AV.push(h), d = i[++u];
      }
      n !== d?.index && (o = U.nextNode(), n++);
    }
    return U.currentNode = F, a;
  }
  p(e) {
    let t = 0;
    for (const i of this._$AV) i !== void 0 && (i.strings !== void 0 ? (i._$AI(e, i, t), t += i.strings.length - 2) : i._$AI(e[t])), t++;
  }
}
class oe {
  get _$AU() {
    return this._$AM?._$AU ?? this._$Cv;
  }
  constructor(e, t, i, a) {
    this.type = 2, this._$AH = l, this._$AN = void 0, this._$AA = e, this._$AB = t, this._$AM = i, this.options = a, this._$Cv = a?.isConnected ?? !0;
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
    e = Y(this, e, t), re(e) ? e === l || e == null || e === "" ? (this._$AH !== l && this._$AR(), this._$AH = l) : e !== this._$AH && e !== Q && this._(e) : e._$litType$ !== void 0 ? this.$(e) : e.nodeType !== void 0 ? this.T(e) : ei(e) ? this.k(e) : this._(e);
  }
  O(e) {
    return this._$AA.parentNode.insertBefore(e, this._$AB);
  }
  T(e) {
    this._$AH !== e && (this._$AR(), this._$AH = this.O(e));
  }
  _(e) {
    this._$AH !== l && re(this._$AH) ? this._$AA.nextSibling.data = e : this.T(F.createTextNode(e)), this._$AH = e;
  }
  $(e) {
    const { values: t, _$litType$: i } = e, a = typeof i == "number" ? this._$AC(e) : (i.el === void 0 && (i.el = ne.createElement(Tt(i.h, i.h[0]), this.options)), i);
    if (this._$AH?._$AD === a) this._$AH.p(t);
    else {
      const o = new si(a, this), n = o.u(this.options);
      o.p(t), this.T(n), this._$AH = o;
    }
  }
  _$AC(e) {
    let t = st.get(e.strings);
    return t === void 0 && st.set(e.strings, t = new ne(e)), t;
  }
  k(e) {
    Me(this._$AH) || (this._$AH = [], this._$AR());
    const t = this._$AH;
    let i, a = 0;
    for (const o of e) a === t.length ? t.push(i = new oe(this.O(ae()), this.O(ae()), this, this.options)) : i = t[a], i._$AI(o), a++;
    a < t.length && (this._$AR(i && i._$AB.nextSibling, a), t.length = a);
  }
  _$AR(e = this._$AA.nextSibling, t) {
    for (this._$AP?.(!1, !0, t); e !== this._$AB; ) {
      const i = Ze(e).nextSibling;
      Ze(e).remove(), e = i;
    }
  }
  setConnected(e) {
    this._$AM === void 0 && (this._$Cv = e, this._$AP?.(e));
  }
}
class $e {
  get tagName() {
    return this.element.tagName;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  constructor(e, t, i, a, o) {
    this.type = 1, this._$AH = l, this._$AN = void 0, this.element = e, this.name = t, this._$AM = a, this.options = o, i.length > 2 || i[0] !== "" || i[1] !== "" ? (this._$AH = Array(i.length - 1).fill(new String()), this.strings = i) : this._$AH = l;
  }
  _$AI(e, t = this, i, a) {
    const o = this.strings;
    let n = !1;
    if (o === void 0) e = Y(this, e, t, 0), n = !re(e) || e !== this._$AH && e !== Q, n && (this._$AH = e);
    else {
      const u = e;
      let d, h;
      for (e = o[0], d = 0; d < o.length - 1; d++) h = Y(this, u[i + d], t, d), h === Q && (h = this._$AH[d]), n ||= !re(h) || h !== this._$AH[d], h === l ? e = l : e !== l && (e += (h ?? "") + o[d + 1]), this._$AH[d] = h;
    }
    n && !a && this.j(e);
  }
  j(e) {
    e === l ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, e ?? "");
  }
}
class ai extends $e {
  constructor() {
    super(...arguments), this.type = 3;
  }
  j(e) {
    this.element[this.name] = e === l ? void 0 : e;
  }
}
class ri extends $e {
  constructor() {
    super(...arguments), this.type = 4;
  }
  j(e) {
    this.element.toggleAttribute(this.name, !!e && e !== l);
  }
}
class ni extends $e {
  constructor(e, t, i, a, o) {
    super(e, t, i, a, o), this.type = 5;
  }
  _$AI(e, t = this) {
    if ((e = Y(this, e, t, 0) ?? l) === Q) return;
    const i = this._$AH, a = e === l && i !== l || e.capture !== i.capture || e.once !== i.once || e.passive !== i.passive, o = e !== l && (i === l || a);
    a && this.element.removeEventListener(this.name, this, i), o && this.element.addEventListener(this.name, this, e), this._$AH = e;
  }
  handleEvent(e) {
    typeof this._$AH == "function" ? this._$AH.call(this.options?.host ?? this.element, e) : this._$AH.handleEvent(e);
  }
}
class oi {
  constructor(e, t, i) {
    this.element = e, this.type = 6, this._$AN = void 0, this._$AM = t, this.options = i;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AI(e) {
    Y(this, e);
  }
}
const li = Ne.litHtmlPolyfillSupport;
li?.(ne, oe), (Ne.litHtmlVersions ??= []).push("3.3.3");
const ci = (s, e, t) => {
  const i = t?.renderBefore ?? e;
  let a = i._$litPart$;
  if (a === void 0) {
    const o = t?.renderBefore ?? null;
    i._$litPart$ = a = new oe(e.insertBefore(ae(), o), o, void 0, t ?? {});
  }
  return a._$AI(s), a;
};
const De = globalThis;
let z = class extends G {
  constructor() {
    super(...arguments), this.renderOptions = { host: this }, this._$Do = void 0;
  }
  createRenderRoot() {
    const e = super.createRenderRoot();
    return this.renderOptions.renderBefore ??= e.firstChild, e;
  }
  update(e) {
    const t = this.render();
    this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(e), this._$Do = ci(t, this.renderRoot, this.renderOptions);
  }
  connectedCallback() {
    super.connectedCallback(), this._$Do?.setConnected(!0);
  }
  disconnectedCallback() {
    super.disconnectedCallback(), this._$Do?.setConnected(!1);
  }
  render() {
    return Q;
  }
};
z._$litElement$ = !0, z.finalized = !0, De.litElementHydrateSupport?.({ LitElement: z });
const di = De.litElementPolyfillSupport;
di?.({ LitElement: z });
(De.litElementVersions ??= []).push("4.2.2");
const ui = (s) => (e, t) => {
  t !== void 0 ? t.addInitializer(() => {
    customElements.define(s, e);
  }) : customElements.define(s, e);
};
const hi = { attribute: !0, type: String, converter: fe, reflect: !1, hasChanged: Le }, pi = (s = hi, e, t) => {
  const { kind: i, metadata: a } = t;
  let o = globalThis.litPropertyMetadata.get(a);
  if (o === void 0 && globalThis.litPropertyMetadata.set(a, o = /* @__PURE__ */ new Map()), i === "setter" && ((s = Object.create(s)).wrapped = !0), o.set(t.name, s), i === "accessor") {
    const { name: n } = t;
    return { set(u) {
      const d = e.get.call(this);
      e.set.call(this, u), this.requestUpdate(n, d, s, !0, u);
    }, init(u) {
      return u !== void 0 && this.C(n, void 0, s, u), u;
    } };
  }
  if (i === "setter") {
    const { name: n } = t;
    return function(u) {
      const d = this[n];
      e.call(this, u), this.requestUpdate(n, d, s, !0, u);
    };
  }
  throw Error("Unsupported decorator location: " + i);
};
function f(s) {
  return (e, t) => typeof t == "object" ? pi(s, e, t) : ((i, a, o) => {
    const n = a.hasOwnProperty(o);
    return a.constructor.createProperty(o, i), n ? Object.getOwnPropertyDescriptor(a, o) : void 0;
  })(s, e, t);
}
function c(s) {
  return f({ ...s, state: !0, attribute: !1 });
}
const Ie = N`
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
`, j = N`
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

  .track-form > .scope-actions {
    order: 1;
  }

  .track-form > .scope-state {
    order: 2;
  }
`;
function mi(s, e) {
  const t = s.ruby_segments;
  if (!Array.isArray(t) || t.length === 0) return null;
  const i = [];
  for (const a of t) {
    if (typeof a != "object" || a === null) return null;
    const o = a;
    if (typeof o.text != "string" || o.text === "") return null;
    const n = o.reading === void 0 || o.reading === null ? null : typeof o.reading == "string" && o.reading !== "" ? o.reading : void 0;
    if (n === void 0) return null;
    i.push({ text: o.text, reading: n });
  }
  return i.map((a) => a.text).join("") !== e ? null : i;
}
function gi(s) {
  return r`${s.map(
    (e) => e.reading === null ? e.text : r`<ruby>${e.text}<rp>(</rp><rt>${e.reading}</rt><rp>)</rp></ruby>`
  )}`;
}
function At(s, e = 0) {
  if (e > 16 || typeof s != "object" || s === null) return l;
  const t = s;
  if ((t.type === "text" || t.type === "inline_code") && typeof t.text == "string")
    return t.type === "inline_code" ? r`<code>${t.text}</code>` : t.text;
  if (t.type === "line_break") return r`<br />`;
  if (t.type === "ruby" && typeof t.text == "string" && t.text !== "" && typeof t.reading == "string" && t.reading !== "")
    return r`<ruby>${t.text}<rp>(</rp><rt>${t.reading}</rt><rp>)</rp></ruby>`;
  if ((t.type === "paragraph" || t.type === "emphasis" || t.type === "strong") && Array.isArray(t.children)) {
    const i = t.children.map((a) => At(a, e + 1));
    return t.type === "paragraph" ? r`<p>${i}</p>` : t.type === "emphasis" ? r`<em>${i}</em>` : r`<strong>${i}</strong>`;
  }
  return l;
}
function fi(s) {
  const e = s.payload.text;
  if (typeof e == "string" && e !== "") {
    const t = mi(s.payload, e);
    return t === null ? e : gi(t);
  }
  return s.kind === "rich_text" && s.payload.type === "document" && Array.isArray(s.payload.children) ? r`${s.payload.children.map((t) => At(t, 1))}` : l;
}
function He(s, e = !1) {
  const t = fi(s);
  return t === l ? l : r`
    <div
      class="content-block ${e ? "primary-content" : ""}"
      lang=${s.language_tag ?? l}
    >
      ${t}
    </div>
  `;
}
const at = ["en", "fr"], rt = {
  en: {
    "app.title": "LockLearn",
    "state.loading": "Loading LockLearn…",
    "state.error": "LockLearn could not be loaded.",
    "state.retry": "Retry",
    "state.home": "Home",
    "state.copyDiagnostic": "Copy diagnostic",
    "state.diagnosticCopied": "Diagnostic copied.",
    "state.offline": "Connection lost. LockLearn will refresh when connectivity returns.",
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
    "learn.resumeHelp": "A session is already in progress. Resume returns to the exact cards and position you left; starting a new session is only offered when there is no unfinished session.",
    "learn.startHelp": "Start builds a new learning session from cards that are eligible now. LockLearn may ask you to wait between recalls so the answer is not still in short-term memory.",
    "learn.readyTitle": "A new learning session is available",
    "learn.readyAlternative": "{mode} is ready on {track}",
    "learn.readyFromEmpty": "This older session has no question left to show, but {count} cards are currently eligible for a new session.",
    "learn.conditionsTitle": "What is LockLearn waiting for?",
    "learn.viewCards": "View cards",
    "learn.startedCards": "Cards already started",
    "learn.unstartedCards": "Cards not started yet",
    "learn.newQuotaRemaining": "New cards still allowed today",
    "learn.noExactTime": "LockLearn has no exact next time to display yet. Some cards may be temporarily blocked by spacing, daily limits or Track selection rules.",
    "learn.loading": "Loading learning session…",
    "learn.waiting": "First retrieval scheduled",
    "learn.waitingBody": "The answer stays hidden until this learning step is due.",
    "learn.waitingUntil": "Available at",
    "learn.noTracks": "No active Track is available for learning.",
    "learn.readOnly": "This Profile is read-only for your Home Assistant user.",
    "learn.empty": "No card is currently available for this Track.",
    "learn.pauseTitle": "Learning pause",
    "learn.readiness": "Learning availability",
    "learn.cardsReady": "cards ready to learn",
    "learn.noCardsReady": "No card is due within the normal learning plan right now.",
    "learn.overrideNewHelp": "Your daily new-card target has been reached, but you can deliberately continue with more new cards. Failed and relearning cards still keep their required cooldown.",
    "learn.emptyExplain": "Nothing is due right now. LockLearn spaces recalls so you do not simply repeat from short-term memory.",
    "learn.nextAvailable": "Next scheduled step",
    "learn.quotaReset": "New-card quota resets",
    "learn.inAbout": "in about",
    "learn.continueNow": "Continue now",
    "learn.continueEarlyHelp": "You can continue early with safe learning steps. Failed cards still keep their required cooldown.",
    "learn.waitingExplain": "Waiting improves the value of the next recall. You may continue early here because this is a post-introduction learning step, not a failed-card retest.",
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
    "learn.knownPending": "Marked as already known. LockLearn will verify it later.",
    "learn.knownUndone": "The already-known mark was undone.",
    "learn.bulkGuardTitle": "You may already know a lot of this track",
    "learn.bulkGuardBody": "You have marked several cards as already known in this session. Quick calibration can place you faster without treating self-assessment as verified memory.",
    "learn.bulkGuardCalibrate": "Start quick calibration",
    "learn.bulkGuardContinue": "Continue this session",
    "learn.undo": "Undo",
    "learn.quickCalibration": "Quick calibration",
    "learn.calibrationTitle": "Quick calibration",
    "learn.calibrationHelp": "Answer 20–40 questions to estimate what you already know. LockLearn never reveals the answer before your choice.",
    "learn.calibrationSize": "Number of questions",
    "learn.calibrationStart": "Start calibration",
    "learn.remindMe": "Notify me when it is ready",
    "learn.configureNotifications": "Configure notifications",
    "learn.cancelReminder": "Cancel reminder",
    "learn.reminderArmed": "Reminder armed. LockLearn will re-check readiness before notifying you.",
    "learn.reminderCancelled": "Reminder cancelled.",
    "learn.answerUnconfirmed": "Answer not confirmed yet.",
    "learn.verify": "Check status",
    "learn.retryAnswer": "Retry answer",
    "learn.answerApplied": "The answer was applied.",
    "learn.answerNotConfirmed": "The answer is still not confirmed. You can retry safely.",
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
    "learn.completedBody": "This learning session is finished. Some cards may still have spaced learning steps before a quiz becomes due.",
    "learn.newSession": "Start another session",
    "learn.error": "The learning session could not be updated.",
    "learn.reloaded": "The session was refreshed. The latest recorded state was reloaded.",
    "learn.targetedSession": "Targeted difficulty session started.",
    "quiz.title": "Quiz",
    "quiz.readyAlternative": "{mode} is ready on {track}",
    "quiz.track": "Track",
    "quiz.format": "Format",
    "quiz.formatMixed": "Mixed",
    "quiz.formatMcq": "Multiple choice",
    "quiz.formatFreeText": "Free text",
    "quiz.formatCloze": "Cloze multiple choice",
    "quiz.start": "Start quiz",
    "quiz.resume": "Resume quiz",
    "quiz.resumeHelp": "An unfinished quiz already exists. Resume continues that exact quiz; a new quiz is only started when there is no unfinished one.",
    "quiz.resumeCalibration": "Resume calibration",
    "quiz.resumeCalibrationHelp": "Continue the unfinished calibration with the same questions and progress.",
    "quiz.startHelp": "A quiz is not an immediate re-test. LockLearn only quizzes cards whose scheduled recall time has arrived, so the result reflects memory rather than a just-seen answer.",
    "quiz.readyFromEmpty": "This older quiz has no question to show, but {count} cards are now ready for a new quiz.",
    "quiz.startedCards": "Cards already started",
    "quiz.readyCards": "Ready for quiz now",
    "quiz.noExactTime": "LockLearn has no future quiz time to display yet. The cards may still be moving through their short learning steps or be temporarily ineligible.",
    "quiz.noTracks": "No active Track is available for quiz.",
    "quiz.readOnly": "This Profile is read-only for your Home Assistant user.",
    "quiz.empty": "No introduced card is currently due for this quiz.",
    "quiz.notReadyTitle": "No quiz due right now",
    "quiz.howItWorks": "Quiz readiness",
    "quiz.cardsReady": "cards ready for quiz",
    "quiz.learnFirst": "A quiz tests cards you have already learned. Start with Learn to introduce some cards first.",
    "quiz.emptyExplain": "You have cards in learning or review, but none has reached its scheduled quiz time yet.",
    "quiz.viewCards": "View cards",
    "quiz.nextAvailable": "Next scheduled review",
    "quiz.inAbout": "in about",
    "quiz.whyDueOnly": "Quiz answers are verified retrievals, so LockLearn waits for cards to become due instead of testing them immediately from short-term memory.",
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
    "quiz.reloaded": "The quiz was refreshed. The latest recorded state was reloaded.",
    "quiz.remindMe": "Notify me when a quiz is ready",
    "quiz.configureNotifications": "Configure notifications",
    "quiz.cancelReminder": "Cancel reminder",
    "quiz.reminderArmed": "Reminder armed. LockLearn will re-check readiness before notifying you.",
    "quiz.reminderCancelled": "Reminder cancelled.",
    "quiz.answerUnconfirmed": "Answer not confirmed yet.",
    "quiz.verify": "Check status",
    "quiz.retryAnswer": "Retry answer",
    "quiz.answerApplied": "The answer was applied.",
    "quiz.answerNotConfirmed": "The answer is still not confirmed. You can retry safely.",
    "quiz.calibrationStarted": "Quick calibration started. Answers stay hidden until you respond.",
    "quiz.calibrationCompleted": "Calibration complete",
    "quiz.calibrationCompletedBody": "Verified answers entered the review system; cards you did not know remain available to learn.",
    "quiz.calibrationKnown": "Known from verified retrieval",
    "quiz.calibrationNeedsLearning": "Still to learn",
    "quiz.learnRemaining": "Learn the remaining cards",
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
    "manage.sharingHelp": "Sharing gives another Home Assistant user access to this LockLearn Profile. Viewer can read it, editor can learn and edit Tracks, and owner can also manage the Profile, sharing and notification targets.",
    "manage.confirmRemoveMember": "Remove this Home Assistant user from the Profile?",
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
    "manage.plan": "Learning pace & goal",
    "manage.planHelp": "Optional. Use this section to choose how quickly this Track should introduce new cards and to estimate the future review workload. It does not schedule one specific session.",
    "manage.planPreviewHelp": "Preview calculates an estimate only; it does not save anything. Apply the plan only if the workload looks reasonable.",
    "manage.basicPlan": "Main pace settings",
    "manage.advancedPlan": "Advanced planning assumptions",
    "manage.newPerDayHelp": "Maximum number of never-seen cards LockLearn may introduce in one day.",
    "manage.reviewsPerDayHelp": "Safety ceiling for scheduled reviews in one day. Existing learning steps can still affect the real daily experience.",
    "manage.targetDateHelp": "Optional date by which you would like to reach the selected coverage. Leave empty if you only want a daily pace.",
    "manage.coverageHelp": "Share of the Track you want to have introduced by the target date. 1.00 means 100%.",
    "manage.notificationTeasersHelp": "Maximum new-card teaser notifications per day. Most new cards are still introduced in the panel.",
    "manage.retentionHelp": "Stored as your target retention goal. The current V1 workload estimator does not yet change its forecast from this value.",
    "manage.previewFailed": "The forecast could not be calculated for this Track.",
    "manage.forecastCurrent": "Current Track snapshot",
    "manage.selectedCards": "Cards in this Track",
    "manage.introducedCards": "Cards already started",
    "manage.targetCards": "Cards included in this goal",
    "manage.dueNow": "Reviews due now",
    "manage.plannedNew": "Planned new cards / day",
    "manage.forecastZeroWarning": "This Track currently reports zero selected cards, so a useful workload forecast cannot be produced. This is unexpected if Learn can already serve cards.",
    "manage.forecastMethod": "How this estimate works",
    "manage.forecastMethodHelp": "The forecast is an estimate, not a promise. It uses the Track's current card count, your daily new/review limits and the V1 review intervals. Future mistakes, relearning and difficult cards can increase the real workload.",
    "manage.warningTargetDate": "The target date would require more new cards per day than the configured daily limit.",
    "manage.warningReviews3Weeks": "Estimated review load in three weeks exceeds the daily review ceiling.",
    "manage.warningReviews3Months": "Estimated review load in three months exceeds the daily review ceiling.",
    "manage.warningDueBacklog": "The current due backlog already exceeds the daily review ceiling.",
    "manage.advancedTrackSettings": "Advanced Track settings",
    "manage.advancedTrackSettingsHelp": "These settings tune prioritization, content weighting and automatic notifications. The defaults are suitable for normal use.",
    "manage.dangerZone": "Danger zone",
    "manage.deleteTrack": "Delete this Track…",
    "manage.deleteTrackHelp": "Deleting a Track removes its Track-specific settings and learning progress. It does not delete the installed Pack or Dataset.",
    "manage.confirmDeleteTrack": "Are you sure you want to permanently delete Track",
    "manage.trackDeleted": "Track deleted.",
    "manage.delete": "Delete",
    "manage.archiveProfile": "Archive Profile",
    "manage.confirmArchiveProfile": "Archive this Profile and disable its scheduler/notifications?",
    "manage.archivedNotice": "Profile archived.",
    "manage.deletePermanently": "Delete permanently",
    "manage.confirmDeletePermanently": "Permanent deletion removes private LockLearn data. Type exactly:",
    "manage.deleted": "Deleted permanently.",
    "manage.createTrack": "Create Track",
    "manage.noPacks": "No installed PackVersion is available.",
    "manage.noPackDirections": "This pack does not expose any usable language direction.",
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
    "manage.noNotificationTargets": "No notification target is configured for this Profile.",
    "manage.notificationTargetSettings": "Companion notification targets",
    "manage.notificationTargetSettingsHelp": "Targets use stable Home Assistant device identity. Technical capabilities stay conservative until they have been qualified.",
    "manage.advancedTargetSettings": "Advanced target settings",
    "manage.availableNotificationDevice": "Available Companion device",
    "manage.noAvailableNotificationDevices": "No unconfigured Companion device is available.",
    "manage.addNotificationTarget": "Add target",
    "manage.notificationTargetCreated": "Notification target added.",
    "manage.notificationTargetUpdated": "Notification target updated.",
    "manage.testNotification": "Test notification",
    "manage.notificationTestSent": "Test notification sent.",
    "manage.routeUnavailable": "route currently unavailable",
    "manage.platform": "Platform",
    "manage.lockscreenVisibility": "Lock-screen visibility",
    "manage.minimumGapSeconds": "Minimum gap (seconds)",
    "manage.maximumPerHour": "Maximum notifications / hour",
    "manage.targetPushBudget": "Target daily push budget",
    "manage.targetEnabled": "Target enabled",
    "manage.sharedDevice": "Shared device",
    "manage.capabilitiesConservative": "Notification capabilities remain conservative until qualified",
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
    "stats.statesHelp": "SRS means spaced repetition: LockLearn waits progressively longer between recalls when a card is remembered. Learning is the short-step phase; Review is the longer-term phase; Relearning follows a failed verified recall.",
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
    "form.dirty": "Unsaved changes",
    "form.pristine": "No unsaved changes",
    "form.save": "Save changes",
    "form.cancel": "Discard changes",
    "form.saving": "Saving…",
    "form.saved": "Changes saved ✓",
    "form.navigationTitle": "Unsaved changes",
    "form.navigationBody": "Some track changes have not been saved.",
    "form.saveAndLeave": "Save and leave",
    "form.leaveWithoutSaving": "Leave without saving",
    "form.stay": "Stay",
    "common.close": "Close",
    "common.loading": "Loading…",
    "cards.concernedTitle": "Cards concerned",
    "cards.noneConcerned": "No card currently matches this waiting reason.",
    "cards.learnInstead": "Return to learning",
    "cards.reactivate": "Reactivate",
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
    "state.home": "Accueil",
    "state.copyDiagnostic": "Copier le diagnostic",
    "state.diagnosticCopied": "Diagnostic copié.",
    "state.offline": "Connexion perdue. LockLearn se rafraîchira au retour de la connexion.",
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
    "learn.resumeHelp": "Une session est déjà en cours. « Reprendre » revient exactement aux cartes et à la position où vous vous êtes arrêté ; une nouvelle session n’est proposée que lorsqu’aucune session n’est inachevée.",
    "learn.startHelp": "« Commencer » crée une nouvelle session avec les cartes disponibles maintenant. LockLearn peut imposer un délai entre deux rappels pour éviter de mesurer uniquement la mémoire à court terme.",
    "learn.readyTitle": "Une nouvelle session d’apprentissage est disponible",
    "learn.readyAlternative": "{mode} est disponible sur {track}",
    "learn.readyFromEmpty": "Cette ancienne session n’a plus de question à afficher, mais {count} cartes sont maintenant disponibles pour une nouvelle session.",
    "learn.conditionsTitle": "Qu’attend LockLearn ?",
    "learn.viewCards": "Voir les cartes",
    "learn.startedCards": "Cartes déjà commencées",
    "learn.unstartedCards": "Cartes pas encore commencées",
    "learn.newQuotaRemaining": "Nouvelles cartes encore autorisées aujourd’hui",
    "learn.noExactTime": "LockLearn n’a pas encore d’heure exacte à afficher. Certaines cartes peuvent être temporairement bloquées par l’espacement, les limites quotidiennes ou les règles du parcours.",
    "learn.loading": "Chargement de la session d’apprentissage…",
    "learn.waiting": "Première récupération planifiée",
    "learn.waitingBody": "La réponse reste masquée jusqu’à l’échéance de cette étape d’apprentissage.",
    "learn.waitingUntil": "Disponible à",
    "learn.noTracks": "Aucun parcours actif n’est disponible pour l’apprentissage.",
    "learn.readOnly": "Ce profil est en lecture seule pour votre utilisateur Home Assistant.",
    "learn.empty": "Aucune carte n’est disponible actuellement pour ce parcours.",
    "learn.pauseTitle": "Pause d’apprentissage",
    "learn.readiness": "Disponibilité de l’apprentissage",
    "learn.cardsReady": "cartes prêtes à apprendre",
    "learn.noCardsReady": "Aucune carte n’est disponible dans le plan d’apprentissage normal pour le moment.",
    "learn.overrideNewHelp": "Votre objectif quotidien de nouvelles cartes est atteint, mais vous pouvez choisir de continuer avec davantage de nouvelles cartes. Les cartes ratées et en réapprentissage conservent toujours leur délai obligatoire.",
    "learn.emptyExplain": "Rien n’est à revoir maintenant. LockLearn espace les rappels pour éviter de simplement répéter depuis la mémoire à court terme.",
    "learn.nextAvailable": "Prochaine étape prévue",
    "learn.quotaReset": "Réinitialisation du quota de nouvelles cartes",
    "learn.inAbout": "dans environ",
    "learn.continueNow": "Continuer maintenant",
    "learn.continueEarlyHelp": "Vous pouvez continuer en avance sur les étapes d’apprentissage sûres. Une carte ratée conserve toujours son temps de pause obligatoire.",
    "learn.waitingExplain": "Attendre rend le prochain rappel plus utile. Vous pouvez continuer en avance ici car il s’agit d’une étape après introduction, pas d’un nouveau test immédiat après un échec.",
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
    "learn.knownPending": "Marquée comme déjà connue. LockLearn la vérifiera plus tard.",
    "learn.knownUndone": "Le marquage « déjà connue » a été annulé.",
    "learn.bulkGuardTitle": "Vous connaissez peut-être déjà une bonne partie de ce parcours",
    "learn.bulkGuardBody": "Vous avez marqué plusieurs cartes comme déjà connues dans cette session. La calibration rapide peut vous positionner plus vite sans traiter une auto-évaluation comme une preuve vérifiée.",
    "learn.bulkGuardCalibrate": "Démarrer une calibration rapide",
    "learn.bulkGuardContinue": "Continuer cette session",
    "learn.undo": "Annuler",
    "learn.quickCalibration": "Calibration rapide",
    "learn.calibrationTitle": "Calibration rapide",
    "learn.calibrationHelp": "Répondez à 20–40 questions pour estimer ce que vous connaissez déjà. LockLearn n’affiche jamais la réponse avant votre choix.",
    "learn.calibrationSize": "Nombre de questions",
    "learn.calibrationStart": "Démarrer la calibration",
    "learn.remindMe": "Me prévenir quand ce sera prêt",
    "learn.configureNotifications": "Configurer les notifications",
    "learn.cancelReminder": "Annuler le rappel",
    "learn.reminderArmed": "Rappel activé. LockLearn revérifiera la disponibilité avant de vous prévenir.",
    "learn.reminderCancelled": "Rappel annulé.",
    "learn.answerUnconfirmed": "Réponse pas encore confirmée.",
    "learn.verify": "Vérifier",
    "learn.retryAnswer": "Réessayer la réponse",
    "learn.answerApplied": "La réponse a bien été appliquée.",
    "learn.answerNotConfirmed": "La réponse n’est toujours pas confirmée. Vous pouvez réessayer sans risque.",
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
    "learn.completedBody": "Cette session est terminée. Certaines cartes peuvent encore avoir des étapes d’apprentissage espacées avant qu’un quiz ne soit dû.",
    "learn.newSession": "Commencer une autre session",
    "learn.error": "Impossible de mettre à jour la session d’apprentissage.",
    "learn.reloaded": "La session a été actualisée. Le dernier état enregistré a été rechargé.",
    "learn.targetedSession": "Session ciblée sur les difficultés démarrée.",
    "quiz.title": "Quiz",
    "quiz.readyAlternative": "{mode} est disponible sur {track}",
    "quiz.track": "Parcours",
    "quiz.format": "Format",
    "quiz.formatMixed": "Mixte",
    "quiz.formatMcq": "QCM",
    "quiz.formatFreeText": "Réponse libre",
    "quiz.formatCloze": "Texte à trous — QCM",
    "quiz.start": "Commencer le quiz",
    "quiz.resume": "Reprendre le quiz",
    "quiz.resumeHelp": "Un quiz inachevé existe déjà. « Reprendre » continue exactement ce quiz ; un nouveau quiz n’est démarré que lorsqu’aucun quiz n’est en cours.",
    "quiz.resumeCalibration": "Reprendre la calibration",
    "quiz.resumeCalibrationHelp": "Continuer la calibration inachevée avec les mêmes questions et la même progression.",
    "quiz.startHelp": "Un quiz n’est pas un re-test immédiat. LockLearn ne propose que les cartes dont l’heure de rappel est arrivée, afin de mesurer ce que vous retenez plutôt qu’une réponse encore fraîche en mémoire.",
    "quiz.readyFromEmpty": "Cet ancien quiz n’a plus de question à afficher, mais {count} cartes sont maintenant prêtes pour un nouveau quiz.",
    "quiz.startedCards": "Cartes déjà commencées",
    "quiz.readyCards": "Prêtes pour un quiz maintenant",
    "quiz.noExactTime": "LockLearn n’a pas encore d’heure future de quiz à afficher. Les cartes peuvent encore être dans leurs courtes étapes d’apprentissage ou être temporairement indisponibles.",
    "quiz.noTracks": "Aucun parcours actif n’est disponible pour le quiz.",
    "quiz.readOnly": "Ce profil est en lecture seule pour votre utilisateur Home Assistant.",
    "quiz.empty": "Aucune carte déjà introduite n’est actuellement due pour ce quiz.",
    "quiz.notReadyTitle": "Aucun quiz à faire pour le moment",
    "quiz.howItWorks": "Disponibilité du quiz",
    "quiz.cardsReady": "cartes prêtes pour un quiz",
    "quiz.learnFirst": "Le quiz teste des cartes déjà apprises. Commencez par Apprendre pour introduire quelques cartes.",
    "quiz.emptyExplain": "Vous avez des cartes en apprentissage ou en révision, mais aucune n’a encore atteint son heure prévue de quiz.",
    "quiz.viewCards": "Voir les cartes",
    "quiz.nextAvailable": "Prochaine révision prévue",
    "quiz.inAbout": "dans environ",
    "quiz.whyDueOnly": "Les réponses de quiz sont des rappels vérifiés. LockLearn attend donc l’échéance des cartes au lieu de les retester immédiatement depuis la mémoire à court terme.",
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
    "quiz.reloaded": "Le quiz a été actualisé. Le dernier état enregistré a été rechargé.",
    "quiz.remindMe": "Me prévenir quand un quiz sera prêt",
    "quiz.configureNotifications": "Configurer les notifications",
    "quiz.cancelReminder": "Annuler le rappel",
    "quiz.reminderArmed": "Rappel activé. LockLearn revérifiera la disponibilité avant de vous prévenir.",
    "quiz.reminderCancelled": "Rappel annulé.",
    "quiz.answerUnconfirmed": "Réponse pas encore confirmée.",
    "quiz.verify": "Vérifier",
    "quiz.retryAnswer": "Réessayer la réponse",
    "quiz.answerApplied": "La réponse a bien été appliquée.",
    "quiz.answerNotConfirmed": "La réponse n’est toujours pas confirmée. Vous pouvez réessayer sans risque.",
    "quiz.calibrationStarted": "Calibration rapide démarrée. Les réponses restent cachées jusqu’à votre choix.",
    "quiz.calibrationCompleted": "Calibration terminée",
    "quiz.calibrationCompletedBody": "Les réponses vérifiées sont entrées dans les révisions ; les cartes non connues restent à apprendre.",
    "quiz.calibrationKnown": "Connues après récupération vérifiée",
    "quiz.calibrationNeedsLearning": "Restent à apprendre",
    "quiz.learnRemaining": "Apprendre les cartes restantes",
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
    "manage.sharingHelp": "Le partage donne à un autre utilisateur Home Assistant accès à ce profil LockLearn. Lecteur peut le consulter, éditeur peut apprendre et modifier les parcours, propriétaire peut aussi gérer le profil, le partage et les cibles de notification.",
    "manage.confirmRemoveMember": "Retirer cet utilisateur Home Assistant du profil ?",
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
    "manage.plan": "Objectif & rythme d’apprentissage",
    "manage.planHelp": "Facultatif. Cette section sert à choisir à quelle vitesse ce parcours introduit de nouvelles cartes et à estimer la charge de révisions à venir. Elle ne programme pas une session précise.",
    "manage.planPreviewHelp": "Prévisualiser calcule seulement une estimation : rien n’est enregistré. Appliquez le plan uniquement si la charge vous convient.",
    "manage.basicPlan": "Rythme principal",
    "manage.advancedPlan": "Hypothèses avancées",
    "manage.newPerDayHelp": "Nombre maximum de cartes jamais vues que LockLearn peut introduire dans une journée.",
    "manage.reviewsPerDayHelp": "Plafond de sécurité pour les révisions planifiées dans une journée. Les étapes d’apprentissage déjà en cours peuvent encore influencer la charge réelle.",
    "manage.targetDateHelp": "Date facultative à laquelle vous aimeriez atteindre la couverture choisie. Laissez vide si vous souhaitez seulement fixer un rythme quotidien.",
    "manage.coverageHelp": "Part du parcours que vous voulez avoir commencée à la date cible. 1,00 correspond à 100 %.",
    "manage.notificationTeasersHelp": "Nombre maximal de notifications quotidiennes servant à introduire de nouvelles cartes. La majorité des nouvelles cartes restent introduites dans le panneau.",
    "manage.retentionHelp": "Objectif de mémorisation enregistré pour ce parcours. L’estimateur de charge V1 ne modifie pas encore ses calculs en fonction de cette valeur.",
    "manage.previewFailed": "Impossible de calculer la prévision pour ce parcours.",
    "manage.forecastCurrent": "État actuel du parcours",
    "manage.selectedCards": "Cartes dans ce parcours",
    "manage.introducedCards": "Cartes déjà commencées",
    "manage.targetCards": "Cartes incluses dans l’objectif",
    "manage.dueNow": "Révisions dues maintenant",
    "manage.plannedNew": "Nouvelles cartes prévues / jour",
    "manage.forecastZeroWarning": "Ce parcours indique actuellement zéro carte sélectionnée : une prévision de charge utile est donc impossible. C’est anormal si l’onglet Apprendre peut déjà proposer des cartes.",
    "manage.forecastMethod": "Comment cette estimation est calculée",
    "manage.forecastMethodHelp": "La prévision est une estimation, pas une promesse. Elle utilise le nombre actuel de cartes du parcours, vos plafonds quotidiens et les intervalles de révision V1. Les erreurs futures, le réapprentissage et les cartes difficiles peuvent augmenter la charge réelle.",
    "manage.warningTargetDate": "La date cible demanderait plus de nouvelles cartes par jour que le plafond configuré.",
    "manage.warningReviews3Weeks": "La charge estimée de révisions dans trois semaines dépasse le plafond quotidien.",
    "manage.warningReviews3Months": "La charge estimée de révisions dans trois mois dépasse le plafond quotidien.",
    "manage.warningDueBacklog": "Les révisions déjà dues dépassent le plafond quotidien.",
    "manage.advancedTrackSettings": "Paramètres avancés du parcours",
    "manage.advancedTrackSettingsHelp": "Ces réglages ajustent la priorité, la pondération du contenu et les notifications automatiques. Les valeurs par défaut conviennent à un usage normal.",
    "manage.dangerZone": "Zone sensible",
    "manage.deleteTrack": "Supprimer ce parcours…",
    "manage.deleteTrackHelp": "Supprimer un parcours efface ses réglages et sa progression propres. Le pack et le dataset installés ne sont pas supprimés.",
    "manage.confirmDeleteTrack": "Êtes-vous sûr de vouloir supprimer définitivement le parcours",
    "manage.trackDeleted": "Parcours supprimé.",
    "manage.delete": "Supprimer",
    "manage.archiveProfile": "Archiver le profil",
    "manage.confirmArchiveProfile": "Archiver ce profil et désactiver son scheduler et ses notifications ?",
    "manage.archivedNotice": "Profil archivé.",
    "manage.deletePermanently": "Supprimer définitivement",
    "manage.confirmDeletePermanently": "La suppression définitive efface les données privées LockLearn. Saisissez exactement :",
    "manage.deleted": "Supprimé définitivement.",
    "manage.createTrack": "Créer un parcours",
    "manage.noPacks": "Aucune PackVersion installée n’est disponible.",
    "manage.noPackDirections": "Ce pack ne propose aucune direction de langue exploitable.",
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
    "manage.noNotificationTargets": "Aucune cible de notification n’est configurée pour ce profil.",
    "manage.notificationTargetSettings": "Cibles de notification Companion",
    "manage.notificationTargetSettingsHelp": "Les cibles utilisent l’identité stable des appareils Home Assistant. Les capacités techniques restent prudentes tant qu’elles n’ont pas été qualifiées.",
    "manage.advancedTargetSettings": "Paramètres avancés de la cible",
    "manage.availableNotificationDevice": "Appareil Companion disponible",
    "manage.noAvailableNotificationDevices": "Aucun appareil Companion non configuré n’est disponible.",
    "manage.addNotificationTarget": "Ajouter la cible",
    "manage.notificationTargetCreated": "Cible de notification ajoutée.",
    "manage.notificationTargetUpdated": "Cible de notification mise à jour.",
    "manage.testNotification": "Tester la notification",
    "manage.notificationTestSent": "Notification de test envoyée.",
    "manage.routeUnavailable": "route actuellement indisponible",
    "manage.platform": "Plateforme",
    "manage.lockscreenVisibility": "Visibilité écran verrouillé",
    "manage.minimumGapSeconds": "Écart minimum (secondes)",
    "manage.maximumPerHour": "Notifications maximum / heure",
    "manage.targetPushBudget": "Budget push quotidien de la cible",
    "manage.targetEnabled": "Cible active",
    "manage.sharedDevice": "Appareil partagé",
    "manage.capabilitiesConservative": "Les capacités de notification restent prudentes tant qu’elles ne sont pas qualifiées",
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
    "stats.statesHelp": "SRS signifie « répétition espacée » : lorsque vous vous souvenez d’une carte, LockLearn espace progressivement les rappels. « Apprentissage » correspond aux étapes courtes ; « Révision » au suivi à plus long terme ; « Réapprentissage » intervient après un rappel vérifié raté.",
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
    "form.dirty": "Modifications non enregistrées",
    "form.pristine": "Aucune modification non enregistrée",
    "form.save": "Enregistrer les modifications",
    "form.cancel": "Annuler les modifications",
    "form.saving": "Enregistrement…",
    "form.saved": "Modifications enregistrées ✓",
    "form.navigationTitle": "Des modifications ne sont pas enregistrées",
    "form.navigationBody": "Certaines modifications du parcours ne sont pas encore enregistrées.",
    "form.saveAndLeave": "Enregistrer et quitter",
    "form.leaveWithoutSaving": "Quitter sans enregistrer",
    "form.stay": "Rester",
    "common.close": "Fermer",
    "common.loading": "Chargement…",
    "cards.concernedTitle": "Cartes concernées",
    "cards.noneConcerned": "Aucune carte ne correspond actuellement à cette attente.",
    "cards.learnInstead": "Remettre à apprendre",
    "cards.reactivate": "Réactiver",
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
function Z(s) {
  const e = s.trim().toLowerCase().replaceAll("_", "-");
  if (at.includes(e))
    return e;
  const t = e.split("-", 1)[0];
  return at.includes(t) ? t : "en";
}
function O(s, e) {
  return rt[s][e] ?? rt.en[e];
}
const I = 3;
class zt extends Error {
  constructor(e, t, i) {
    super(
      `LockLearn frontend protocol ${e} does not match backend protocol ${t}`
    ), this.frontendProtocol = e, this.backendProtocol = t, this.backendVersion = i;
  }
}
async function vi(s) {
  const e = await s.callWS({
    type: "locklearn/bootstrap"
  });
  if (e.frontend_protocol !== I)
    throw new zt(
      I,
      e.frontend_protocol,
      e.backend_version
    );
  return e;
}
async function nt(s) {
  const e = [];
  let t = null;
  do {
    const i = await s.callWS({
      type: "locklearn/profiles/list",
      limit: 100,
      ...t === null ? {} : { cursor: t }
    });
    e.push(...i.items), t = i.cursor;
  } while (t !== null);
  return e;
}
async function le(s, e, t = {}) {
  const i = [];
  let a = null;
  do {
    const o = await s.callWS({
      type: e,
      limit: 100,
      ...t,
      ...a === null ? {} : { cursor: a }
    });
    i.push(...o.items), a = o.cursor;
  } while (a !== null);
  return i;
}
async function bi(s, e, t, i) {
  return s.callWS({
    type: "locklearn/profiles/create",
    name: e,
    preset: t,
    timezone: i
  });
}
async function ot(s, e, t) {
  return s.callWS({
    type: "locklearn/profiles/update",
    profile_id: e,
    ...t
  });
}
async function lt(s, e, t, i) {
  await s.callWS({
    type: "locklearn/profiles/delete",
    profile_id: e,
    action: t,
    ...i === void 0 ? {} : { confirmation: i }
  });
}
async function yi(s, e) {
  return s.callWS({
    type: "locklearn/profiles/members",
    profile_id: e
  });
}
async function $i(s, e) {
  return s.callWS({
    type: "locklearn/profiles/share_targets",
    profile_id: e
  });
}
async function ct(s, e, t, i) {
  await s.callWS({
    type: "locklearn/profiles/share",
    profile_id: e,
    target_user_id: t,
    role: i
  });
}
async function ki(s, e, t) {
  await s.callWS({
    type: "locklearn/profiles/share",
    profile_id: e,
    target_user_id: t,
    remove: !0
  });
}
async function Ct(s, e) {
  return le(s, "locklearn/tracks/list", {
    profile_id: e
  });
}
async function Ue(s, e) {
  return le(s, "locklearn/targets/list", {
    profile_id: e
  });
}
async function wi(s, e) {
  return le(s, "locklearn/targets/discover", {
    profile_id: e
  });
}
async function _i(s, e, t) {
  return s.callWS({
    type: "locklearn/targets/create",
    profile_id: e,
    device_registry_id: t
  });
}
async function xi(s, e, t, i) {
  return s.callWS({
    type: "locklearn/targets/update",
    profile_id: e,
    target_id: t,
    ...i
  });
}
async function Si(s, e, t) {
  return s.callWS({
    type: "locklearn/targets/test",
    profile_id: e,
    target_id: t
  });
}
async function qi(s, e, t) {
  return s.callWS({
    type: "locklearn/stats/get",
    profile_id: e,
    recent_verified_limit: 30,
    calibration_days: 7,
    confusion_limit: 20,
    ...t ? { track_id: t } : {}
  });
}
async function Ti(s, e, t) {
  return (await s.callWS({
    type: "locklearn/difficulties/list",
    profile_id: e,
    ...t ? { track_id: t } : {}
  })).items;
}
async function Ai(s, e) {
  return s.callWS({
    type: "locklearn/tracks/create",
    ...e
  });
}
async function zi(s, e, t) {
  return s.callWS({
    type: "locklearn/tracks/update",
    track_id: e,
    ...t
  });
}
async function Ci(s, e) {
  await s.callWS({
    type: "locklearn/tracks/delete",
    track_id: e
  });
}
async function Pi(s) {
  return le(s, "locklearn/packs/list");
}
async function Ri(s) {
  return le(s, "locklearn/datasets/list");
}
async function dt(s, e, t, i) {
  return s.callWS({
    type: "locklearn/datasets/attributions",
    dataset_id: e,
    source_id: t,
    limit: 50,
    ...i ? { cursor: i } : {}
  });
}
async function Ei(s) {
  return (await s.callWS({
    type: "locklearn/datasets/refresh"
  })).items;
}
async function Li(s, e, t) {
  return s.callWS({
    type: "locklearn/datasets/install",
    dataset_id: e,
    ...t ? { version: t } : {}
  });
}
async function Ni(s, e, t) {
  return s.callWS({
    type: "locklearn/tracks/preview_pack_update",
    track_id: e,
    pack_version_id: t
  });
}
async function Mi(s, e, t) {
  return s.callWS({
    type: "locklearn/tracks/integrate_pack_update",
    track_id: e,
    pack_version_id: t
  });
}
function Pt(s, e, t) {
  return {
    type: s,
    track_id: e,
    ...t
  };
}
async function Di(s, e, t) {
  return s.callWS(
    Pt("locklearn/tracks/plan_preview", e, t)
  );
}
async function ut(s, e, t) {
  return s.callWS(
    Pt("locklearn/tracks/plan_set", e, t)
  );
}
async function Ii(s, e) {
  return s.callWS({
    type: "locklearn/dashboard/get",
    profile_id: e
  });
}
async function ke(s, e, t, i, a = {}) {
  return s.callWS({
    type: "locklearn/session/availability",
    profile_id: e,
    track_id: t,
    session_type: i,
    settings: a
  });
}
async function ze(s, e, t, i, a = "mixed") {
  return s.callWS({
    type: "locklearn/session/start_v04",
    profile_id: e,
    track_id: t,
    session_type: "quiz",
    strategy: "default",
    settings: {
      quiz_format: a,
      option_count: 4
    }
  });
}
async function Hi(s, e, t, i = 20) {
  return s.callWS({
    type: "locklearn/session/start_v04",
    profile_id: e,
    track_id: t,
    session_type: "calibration",
    strategy: "calibration",
    settings: {
      requested_cards: i,
      quiz_format: "mixed",
      option_count: 4
    }
  });
}
async function de(s, e, t, i) {
  return s.callWS({
    type: "locklearn/quiz/answer_v04",
    session_id: e.id,
    expected_version: e.version,
    question_id: t,
    answer: i
  });
}
async function Ui(s, e, t, i) {
  return s.callWS({
    type: "locklearn/quiz/evaluate",
    session_id: e,
    question_id: t,
    answer: i
  });
}
async function Fi(s, e, t, i, a) {
  if (typeof a.submitted_text != "string" || a.grading_policy_kind === void 0 || a.grading_policy_version === void 0 || a.normalization_version === void 0)
    throw new Error("free-text report metadata is incomplete");
  return s.callWS({
    type: "locklearn/content/report",
    profile_id: e,
    track_id: t,
    card_key: i.card_key,
    learning_item_id: i.learning_item_id,
    prompt_facet_id: i.prompt_facet_id,
    answer_facet_id: i.answer_facet_id,
    submitted_text: a.submitted_text,
    normalized_submission: a.normalized_submission ?? null,
    grading_policy_kind: a.grading_policy_kind,
    grading_policy_version: a.grading_policy_version,
    normalization_version: a.normalization_version
  });
}
async function Ce(s, e, t, i, a = !1) {
  return s.callWS({
    type: "locklearn/session/start_v04",
    profile_id: e,
    track_id: t,
    session_type: "learn",
    strategy: "default",
    settings: {
      ...a ? { allow_early_learning: !0 } : {}
    }
  });
}
async function ji(s, e, t, i) {
  return s.callWS({
    type: "locklearn/calibration/followup/status",
    profile_id: e,
    track_id: t
  });
}
async function Rt(s, e, t, i) {
  return s.callWS({
    type: "locklearn/calibration/followup/start",
    profile_id: e,
    track_id: t,
    calibration_session_id: i
  });
}
async function E(s, e) {
  return s.callWS({
    type: "locklearn/session/get",
    session_id: e
  });
}
async function _e(s, e, t, i) {
  return s.callWS({
    type: "locklearn/session/answer_v04",
    session_id: e.id,
    expected_version: e.version,
    question_id: t,
    answer: i
  });
}
async function Et(s, e) {
  return s.callWS({
    type: "locklearn/session/complete",
    session_id: e.id,
    expected_version: e.version
  });
}
async function Lt(s, e, t, i, a) {
  return s.callWS({
    type: "locklearn/progress/set_user_state",
    profile_id: e,
    track_id: t,
    card_key: i,
    user_state: a
  });
}
async function Oi(s, e, t, i, a) {
  return s.callWS({
    type: "locklearn/cards/concerned/list",
    profile_id: e,
    track_id: t,
    filter: i,
    mode: a
  });
}
async function Nt(s, e, t, i) {
  return s.callWS({
    type: "locklearn/cards/learn_instead",
    profile_id: e,
    track_id: t,
    card_key: i
  });
}
async function Mt(s, e, t, i) {
  return s.callWS({
    type: "locklearn/reminders/ready/status",
    profile_id: e,
    track_id: t,
    mode: i
  });
}
async function Dt(s, e, t, i) {
  return s.callWS({
    type: "locklearn/reminders/ready/arm",
    profile_id: e,
    track_id: t,
    mode: i
  });
}
async function It(s, e, t, i) {
  return s.callWS({
    type: "locklearn/reminders/ready/cancel",
    profile_id: e,
    track_id: t,
    mode: i
  });
}
async function Ht(s, e, t, i, a) {
  return s.callWS({
    type: "locklearn/content/report_question",
    profile_id: e,
    track_id: t,
    card_key: i.card_key,
    learning_item_id: i.learning_item_id,
    prompt_facet_id: i.prompt_facet_id,
    answer_facet_id: i.answer_facet_id,
    reason: "user_reported_question",
    ...a === void 0 || a.trim() === "" ? {} : { message: a.trim() }
  });
}
async function Ut(s, e, t, i) {
  return s.callWS({
    type: "locklearn/annotations/create",
    profile_id: e,
    card_key: t,
    note: i.trim()
  });
}
async function Wi(s, e, t, i) {
  return s.callWS({
    type: "locklearn/annotations/update",
    profile_id: e,
    annotation_id: t,
    note: i.trim()
  });
}
async function Vi(s, e, t, i) {
  return s.callWS({
    type: "locklearn/leeches/reactivate",
    profile_id: e,
    track_id: t,
    card_key: i
  });
}
async function Bi(s, e, t, i = 20) {
  return s.callWS({
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
async function Ki(s, e, t, i) {
  return s.callWS({
    type: "locklearn/exam/start",
    profile_id: e,
    track_id: t,
    requested_cards: i.requestedCards,
    ...i.contentTypes === void 0 ? {} : { content_types: i.contentTypes },
    ...i.direction === void 0 ? {} : { direction: i.direction },
    ...i.packId === void 0 ? {} : { pack_id: i.packId },
    ...i.packVersionId === void 0 ? {} : { pack_version_id: i.packVersionId },
    ...i.levels === void 0 ? {} : { levels: i.levels },
    ...i.tags === void 0 ? {} : { tags: i.tags },
    ...i.shuffle === void 0 ? {} : { shuffle: i.shuffle },
    ...i.optionCount === void 0 ? {} : { option_count: i.optionCount }
  });
}
async function Gi(s, e, t, i) {
  return s.callWS({
    type: "locklearn/exam/answer",
    session_id: e.id,
    expected_version: e.version,
    question_id: t,
    selected_answer_id: i
  });
}
async function Qi(s, e) {
  return s.callWS({
    type: "locklearn/exam/finish",
    session_id: e.id,
    expected_version: e.version
  });
}
async function ht(s, e) {
  return s.callWS({
    type: "locklearn/exam/result",
    session_id: e
  });
}
async function Yi(s, e) {
  return s.callWS({
    type: "locklearn/exam/history",
    profile_id: e,
    limit: 20
  });
}
async function Zi(s, e, t) {
  return s.callWS({
    type: "locklearn/session/pause",
    session_id: e.id,
    expected_version: e.version,
    paused: t
  });
}
var Ji = Object.defineProperty, Xi = Object.getOwnPropertyDescriptor, C = (s, e, t, i) => {
  for (var a = i > 1 ? void 0 : i ? Xi(e, t) : e, o = s.length - 1, n; o >= 0; o--)
    (n = s[o]) && (a = (i ? n(e, t, a) : n(a)) || a);
  return i && a && Ji(e, t, a), a;
};
let A = class extends z {
  constructor() {
    super(...arguments), this.profileId = "", this.trackId = "", this.filter = "current_waiting_context", this.mode = "learn", this.language = "en", this.timeZone = "UTC", this.cards = [], this.loading = !0, this.errorMessage = "";
  }
  connectedCallback() {
    super.connectedCallback(), this.refresh();
  }
  updated(s) {
    (s.has("profileId") || s.has("trackId") || s.has("filter") || s.has("mode")) && this.refresh();
  }
  tr(s) {
    return O(this.language, s);
  }
  filterCopy() {
    const s = this.language === "fr", i = {
      known_pending: { en: ["Already-known cards to verify", "These cards were marked as already known and will be verified later."], fr: ["Cartes déjà connues à vérifier", "Ces cartes ont été marquées comme déjà connues et seront vérifiées plus tard."] },
      suspended: { en: ["Suspended cards", "These cards are excluded until you reactivate them."], fr: ["Cartes suspendues", "Ces cartes restent exclues tant que vous ne les réactivez pas."] },
      buried: { en: ["Cards temporarily set aside", "These cards are temporarily hidden from normal sessions."], fr: ["Cartes mises de côté temporairement", "Ces cartes sont temporairement retirées des sessions normales."] },
      prerequisite_support: { en: ["Prerequisites to learn first", "These prerequisite cards currently block other material."], fr: ["Prérequis à apprendre d’abord", "Ces cartes prérequises bloquent actuellement d’autres contenus."] },
      current_waiting_context: { en: ["Cards currently waiting", "These cards explain why the current mode is not ready yet."], fr: ["Cartes actuellement en attente", "Ces cartes expliquent pourquoi ce mode n’est pas encore disponible."] }
    }[this.filter][s ? "fr" : "en"];
    return { title: i[0], body: i[1] };
  }
  stateLabel(s) {
    const e = this.language === "fr";
    return ({
      known_already: ["Marked as already known", "Marquée comme déjà connue"],
      suspended: ["Suspended", "Suspendue"],
      buried: ["Temporarily set aside", "Mise de côté temporairement"],
      active: ["Active", "Active"],
      new: ["Not learned yet", "Pas encore apprise"],
      learning: ["Learning", "En apprentissage"],
      review: ["Review", "En révision"],
      relearning: ["Relearning", "En réapprentissage"]
    }[s] ?? ["Waiting", "En attente"])[e ? 1 : 0];
  }
  horizonLabel(s) {
    const e = new Date(s);
    return Number.isNaN(e.getTime()) ? "" : new Intl.DateTimeFormat(this.language, {
      dateStyle: "medium",
      timeStyle: "short",
      timeZone: this.timeZone
    }).format(e);
  }
  async refresh() {
    if (!(this.hass === void 0 || this.profileId === "" || this.trackId === "")) {
      this.loading = !0, this.errorMessage = "";
      try {
        const s = await Oi(
          this.hass,
          this.profileId,
          this.trackId,
          this.filter,
          this.mode
        );
        this.cards = s.cards;
      } catch (s) {
        this.errorMessage = s instanceof Error ? s.message : String(s);
      } finally {
        this.loading = !1;
      }
    }
  }
  close() {
    this.dispatchEvent(new CustomEvent("locklearn-concerned-cards-close", {
      bubbles: !0,
      composed: !0
    }));
  }
  async apply(s) {
    if (this.hass !== void 0) {
      this.loading = !0, this.errorMessage = "";
      try {
        s.action === "learn_instead" ? await Nt(this.hass, this.profileId, this.trackId, s.card_key) : s.action === "reactivate" && await Lt(this.hass, this.profileId, this.trackId, s.card_key, "active"), await this.refresh(), this.dispatchEvent(new CustomEvent("locklearn-concerned-cards-changed", {
          bubbles: !0,
          composed: !0
        }));
      } catch (e) {
        this.errorMessage = e instanceof Error ? e.message : String(e), this.loading = !1;
      }
    }
  }
  renderCard(s) {
    return r`
      <li>
        <div>
          ${s.prompt.blocks.map((e, t) => He(e, t === 0))}
        </div>
        <div class="meta">
          ${this.stateLabel(s.user_state)}
          ${s.horizon_utc === null ? l : r` · ${this.horizonLabel(s.horizon_utc)}`}
        </div>
        ${s.action === null ? l : r`
              <div class="actions">
                <button class="primary" @click=${() => {
      this.apply(s);
    }} ?disabled=${this.loading}>
                  ${s.action === "learn_instead" ? this.tr("cards.learnInstead") : this.tr("cards.reactivate")}
                </button>
                ${s.action === "learn_instead" ? r`<span class="meta">${this.language === "fr" ? "Annule le marquage « déjà connue » et remet cette carte dans l’apprentissage normal." : "Cancels the already-known mark and returns this card to normal learning."}</span>` : s.action === "reactivate" ? r`<span class="meta">${this.language === "fr" ? "Remet cette carte dans les sessions normales." : "Returns this card to normal sessions."}</span>` : l}
              </div>
            `}
      </li>
    `;
  }
  render() {
    return r`
      <div class="backdrop" @click=${this.close}></div>
      <section class="sheet" role="dialog" aria-modal="true" aria-labelledby="concerned-title">
        <header>
          <h2 id="concerned-title">${this.filterCopy().title}</h2>
          <button @click=${this.close} aria-label=${this.tr("common.close")}>×</button>
        </header>
        <p class="meta">${this.filterCopy().body}</p>
        ${this.loading && this.cards.length === 0 ? r`<p role="status">${this.tr("common.loading")}</p>` : l}
        ${this.errorMessage === "" ? l : r`<p class="error" role="alert">${this.errorMessage}</p>`}
        ${!this.loading && this.cards.length === 0 ? r`<p>${this.tr("cards.noneConcerned")}</p>` : r`<ul>${this.cards.map((s) => this.renderCard(s))}</ul>`}
      </section>
    `;
  }
};
A.styles = [
  Ie,
  j,
  N`
      :host {
        position: fixed;
        inset: 0;
        z-index: 1000;
        display: block;
      }

      .backdrop {
        position: absolute;
        inset: 0;
        background: color-mix(in srgb, var(--primary-text-color) 28%, transparent);
      }

      .sheet {
        position: absolute;
        left: 50%;
        transform: translateX(-50%);
        width: min(960px, calc(100% - 24px));
        bottom: 0;
        max-height: min(78vh, 720px);
        overflow: auto;
        background: var(--card-background-color);
        color: var(--primary-text-color);
        border-radius: 18px 18px 0 0;
        padding: 20px max(18px, env(safe-area-inset-right))
          max(20px, env(safe-area-inset-bottom))
          max(18px, env(safe-area-inset-left));
        box-shadow: var(--ha-card-box-shadow, 0 -8px 28px rgb(0 0 0 / 18%));
      }

      header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 16px;
        margin-bottom: 16px;
      }

      h2 {
        margin: 0;
        font-size: 1.2rem;
      }

      button {
        min-height: 44px;
        min-width: 44px;
        border-radius: 10px;
        border: 1px solid var(--divider-color);
        background: var(--card-background-color);
        color: var(--primary-text-color);
        padding: 0.55rem 0.8rem;
        cursor: pointer;
      }

      button.primary {
        background: var(--primary-color);
        color: var(--text-primary-color, white);
        border-color: var(--primary-color);
      }

      ul {
        list-style: none;
        margin: 0;
        padding: 0;
        display: grid;
        gap: 12px;
      }

      li {
        border: 1px solid var(--divider-color);
        border-radius: 14px;
        padding: 14px;
        display: grid;
        gap: 10px;
      }

      .meta {
        color: var(--secondary-text-color);
        font-size: 0.9rem;
      }

      .actions {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
      }

      .error {
        color: var(--error-color);
      }
    `
];
C([
  f({ attribute: !1 })
], A.prototype, "hass", 2);
C([
  f()
], A.prototype, "profileId", 2);
C([
  f()
], A.prototype, "trackId", 2);
C([
  f()
], A.prototype, "filter", 2);
C([
  f()
], A.prototype, "mode", 2);
C([
  f()
], A.prototype, "language", 2);
C([
  f()
], A.prototype, "timeZone", 2);
C([
  c()
], A.prototype, "cards", 2);
C([
  c()
], A.prototype, "loading", 2);
C([
  c()
], A.prototype, "errorMessage", 2);
A = C([
  ui("locklearn-concerned-cards")
], A);
function es(s) {
  return s.sort(
    (e, t) => e.track.priority - t.track.priority || t.availableNow - e.availableNow || e.track.track_id.localeCompare(t.track.track_id)
  );
}
async function pt(s, e, t, i) {
  const a = await Promise.all(
    t.map(async (o) => {
      const n = await ke(
        s,
        e,
        o.track_id,
        i
      );
      return { track: o, availableNow: n.available_now };
    })
  );
  return es(a.filter((o) => o.availableNow > 0));
}
async function Ft(s, e, t, i) {
  if (e === void 0 || t === "") return;
  const a = e.tracks.find((x) => x.track_id === t);
  if (a === void 0) return;
  const o = i === "learn" ? "quiz" : "learn", n = e.profile.profile_id, u = await ke(
    s,
    n,
    t,
    o
  );
  if (u.available_now > 0)
    return {
      trackId: a.track_id,
      trackName: a.name,
      mode: o,
      availableNow: u.available_now
    };
  const d = e.tracks.filter((x) => x.track_id !== t), h = await pt(s, n, d, i);
  if (h.length > 0) {
    const x = h[0];
    return {
      trackId: x.track.track_id,
      trackName: x.track.name,
      mode: i,
      availableNow: x.availableNow
    };
  }
  const $ = await pt(s, n, d, o);
  if ($.length === 0) return;
  const m = $[0];
  return {
    trackId: m.track.track_id,
    trackName: m.track.name,
    mode: o,
    availableNow: m.availableNow
  };
}
const ts = [
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
], is = "home";
function xe(s) {
  const t = s.replace(/^\/+|\/+$/g, "").split("/").filter(Boolean), i = t[0] === "locklearn" ? t[1] : t[0];
  return ts.includes(i) ? i : is;
}
function jt(s) {
  return s === "home" ? "/locklearn" : `/locklearn/${s}`;
}
function se(s) {
  const e = jt(s);
  globalThis.location?.pathname !== e && (globalThis.history?.pushState({}, "", e), globalThis.dispatchEvent?.(new PopStateEvent("popstate")));
}
function mt(s) {
  return s != null && ["learn", "learning", "bounded"].includes(s.session_type) && ["active", "paused"].includes(s.status);
}
function ss(s) {
  return s?.payload.selection?.progress_state === "new";
}
function as(s) {
  const e = s?.payload.available_at_utc;
  if (typeof e != "string") return null;
  const t = Date.parse(e);
  return Number.isNaN(t) ? null : t;
}
function gt(s) {
  return s !== void 0 && s.role !== "viewer";
}
function X(s) {
  if (s === void 0) return null;
  let e;
  for (const t of s.blockers) {
    if (t.code !== "scheduled_step" || t.until_utc === null) continue;
    const i = Date.parse(t.until_utc);
    Number.isNaN(i) || (e === void 0 || i < e.timestamp) && (e = { raw: t.until_utc, timestamp: i });
  }
  return e?.raw ?? null;
}
function ft(s) {
  return s === void 0 ? 0 : s.blockers.filter((e) => e.code === "scheduled_step").reduce((e, t) => e + t.count, 0);
}
const rs = 3, ns = 5;
function os(s) {
  if (typeof s != "object" || s === null) return !1;
  const e = s;
  return e.kind === "learning" && e.action === "known_already";
}
function ls(s) {
  let e = 0, t = 0;
  for (const [i, a] of s.entries()) {
    if (os(a.answer)) {
      if (e += 1, t += 1, t >= rs || e >= ns)
        return i;
      continue;
    }
    t = 0;
  }
  return null;
}
function cs(s) {
  return s.length === 0 ? !1 : ls(s) === s.length - 1;
}
var ds = Object.defineProperty, g = (s, e, t, i) => {
  for (var a = void 0, o = s.length - 1, n; o >= 0; o--)
    (n = s[o]) && (a = n(e, t, a) || a);
  return a && ds(e, t, a), a;
};
function ee() {
  return globalThis.performance?.now() ?? Date.now();
}
const Fe = class Fe extends z {
  constructor() {
    super(...arguments), this.trackId = "", this.loading = !1, this.errorMessage = "", this.notice = "", this.revealed = !1, this.hintUsed = !1, this.pendingIdk = !1, this.mnemonic = "", this.reportMessage = "", this.forceEarlyCurrent = !1, this.submissionSlow = !1, this.knownNoticeVisible = !1, this.calibrationSetup = !1, this.calibrationSize = 20, this.hasNotificationTarget = !1, this.knownBulkGuardVisible = !1, this.questionStartedAt = ee(), this.questionId = null, this.refreshOnReturn = () => {
      document.visibilityState === "visible" && this.refreshAvailability();
    };
  }
  connectedCallback() {
    super.connectedCallback(), globalThis.addEventListener("focus", this.refreshOnReturn), globalThis.addEventListener("online", this.refreshOnReturn), globalThis.addEventListener("pageshow", this.refreshOnReturn), document.addEventListener("visibilitychange", this.refreshOnReturn);
  }
  disconnectedCallback() {
    this.clearAvailabilityTimer(), this.nextDueTimer !== void 0 && globalThis.clearTimeout(this.nextDueTimer), this.submissionTimer !== void 0 && globalThis.clearTimeout(this.submissionTimer), this.knownUndoTimer !== void 0 && globalThis.clearTimeout(this.knownUndoTimer), globalThis.removeEventListener("focus", this.refreshOnReturn), globalThis.removeEventListener("online", this.refreshOnReturn), globalThis.removeEventListener("pageshow", this.refreshOnReturn), document.removeEventListener("visibilitychange", this.refreshOnReturn), super.disconnectedCallback();
  }
  updated(e) {
    if (e.has("profile") || e.has("dashboard")) {
      const t = this.tracks();
      t.some((i) => i.track_id === this.trackId) || (this.trackId = t[0]?.track_id ?? ""), e.has("profile") && (this.session = void 0, this.resetQuestionUi()), this.refreshAvailability();
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
    return Z(e);
  }
  t(e) {
    return O(this.locale(), e);
  }
  tracks() {
    return this.dashboard?.tracks ?? [];
  }
  selectedTrack() {
    return this.tracks().find((e) => e.track_id === this.trackId);
  }
  setTrack(e) {
    const t = e.currentTarget;
    t instanceof HTMLSelectElement && (this.trackId = t.value, this.session = void 0, this.errorMessage = "", this.notice = "", this.resetQuestionUi(), this.refreshAvailability());
  }
  resetQuestionUi() {
    this.clearAvailabilityTimer(), this.waitingUntil = void 0, this.revealed = !1, this.hintUsed = !1, this.pendingIdk = !1, this.pendingIdkLatency = void 0, this.mnemonic = "", this.reportMessage = "", this.notice = "", this.forceEarlyCurrent = !1, this.questionStartedAt = ee(), this.questionId = this.session?.current_question?.question_id ?? null;
  }
  clearAvailabilityTimer() {
    this.availabilityTimer !== void 0 && (globalThis.clearTimeout(this.availabilityTimer), this.availabilityTimer = void 0);
  }
  scheduleCurrentQuestionAvailability() {
    const e = as(this.session?.current_question);
    e === null || e <= Date.now() || (this.waitingUntil = new Date(e).toISOString(), this.availabilityTimer = globalThis.setTimeout(() => {
      this.availabilityTimer = void 0, this.waitingUntil = void 0, this.questionStartedAt = ee();
    }, e - Date.now()));
  }
  applySession(e) {
    const i = (e.current_question?.question_id ?? null) !== this.questionId;
    this.session = e, i && (this.resetQuestionUi(), this.scheduleCurrentQuestionAvailability());
  }
  async refreshAvailability() {
    if (this.hass === void 0 || this.profile === void 0 || this.trackId === "") {
      this.availability = void 0;
      return;
    }
    try {
      this.availability = await ke(
        this.hass,
        this.profile.profile_id,
        this.trackId,
        "learn"
      ), this.readyAlternative = this.availability.available_now === 0 ? await Ft(this.hass, this.dashboard, this.trackId, "learn") : void 0, this.reminder = await Mt(
        this.hass,
        this.profile.profile_id,
        this.trackId,
        "learn"
      ), this.hasNotificationTarget = (await Ue(this.hass, this.profile.profile_id)).some((i) => i.enabled), this.calibrationFollowup = await ji(
        this.hass,
        this.profile.profile_id,
        this.trackId
      ), this.nextDueTimer !== void 0 && globalThis.clearTimeout(this.nextDueTimer);
      const t = [
        X(this.availability),
        this.availability.next_available_at_utc
      ].filter((i) => i !== null).map((i) => Date.parse(i)).filter((i) => !Number.isNaN(i) && i > Date.now()).sort((i, a) => i - a)[0];
      if (t !== void 0) {
        const i = t - Date.now();
        i > 0 && i < 2147e6 && (this.nextDueTimer = globalThis.setTimeout(() => {
          this.nextDueTimer = void 0, this.refreshAvailability();
        }, i + 250));
      }
    } catch {
      this.availability = void 0, this.readyAlternative = void 0, this.calibrationFollowup = void 0;
    }
  }
  async openReadyAlternative() {
    if (this.hass === void 0 || this.profile === void 0 || this.readyAlternative === void 0) return;
    const e = this.readyAlternative;
    this.loading = !0, this.errorMessage = "";
    try {
      if (e.mode === "learn") {
        this.trackId = e.trackId, this.session = void 0, this.resetQuestionUi(), this.applySession(await Ce(
          this.hass,
          this.profile.profile_id,
          e.trackId
        )), await this.refreshAvailability();
        return;
      }
      const t = await ze(
        this.hass,
        this.profile.profile_id,
        e.trackId
      );
      this.dispatchEvent(new CustomEvent("locklearn-open-session", {
        detail: { session: t },
        bubbles: !0,
        composed: !0
      }));
    } catch (t) {
      this.errorMessage = t instanceof Error ? t.message : String(t);
    } finally {
      this.loading = !1;
    }
  }
  dueLabel(e) {
    if (e === null) return "";
    const t = new Date(e);
    if (Number.isNaN(t.getTime())) return "";
    const i = Math.max(1, Math.ceil((t.getTime() - Date.now()) / 6e4));
    return `${new Intl.DateTimeFormat(this.locale(), { timeStyle: "short" }).format(t)} · ${this.t("learn.inAbout")} ${i} min`;
  }
  nextLearningRecallLabel() {
    return this.locale() === "fr" ? "Prochain rappel d’une carte déjà commencée" : "Next recall of a card already started";
  }
  continueCurrentEarly() {
    this.clearAvailabilityTimer(), this.waitingUntil = void 0, this.forceEarlyCurrent = !0, this.questionStartedAt = ee();
  }
  elapsedMs() {
    return Math.max(0, Math.round(ee() - this.questionStartedAt));
  }
  beginSubmissionWatch() {
    this.submissionSlow = !1, this.submissionTimer !== void 0 && globalThis.clearTimeout(this.submissionTimer), this.submissionTimer = globalThis.setTimeout(() => {
      this.submissionTimer = void 0, this.submissionSlow = !0;
    }, 8e3);
  }
  endSubmissionWatch() {
    this.submissionTimer !== void 0 && globalThis.clearTimeout(this.submissionTimer), this.submissionTimer = void 0, this.submissionSlow = !1;
  }
  async verifySubmission() {
    if (!(this.hass === void 0 || this.session === void 0))
      try {
        const e = this.retryRequest?.session ?? this.session, t = await E(this.hass, e.id), i = t.version !== e.version || t.current_question?.question_id !== e.current_question?.question_id;
        this.applySession(t), i ? (this.loading = !1, this.retryRequest = void 0, this.endSubmissionWatch(), this.notice = this.t("learn.answerApplied")) : (this.loading = !1, this.submissionSlow = !0, this.notice = this.t("learn.answerNotConfirmed"));
      } catch (e) {
        this.errorMessage = e instanceof Error ? e.message : String(e);
      }
  }
  async retrySubmission() {
    if (this.hass === void 0 || this.retryRequest === void 0) return;
    const e = this.retryRequest;
    this.loading = !0, this.errorMessage = "";
    try {
      const t = await E(this.hass, e.session.id);
      if (!(t.version === e.session.version && t.current_question?.question_id === e.questionId)) {
        this.applySession(t), this.retryRequest = void 0, this.endSubmissionWatch(), this.notice = this.t("learn.answerApplied");
        return;
      }
      this.applySession(await _e(
        this.hass,
        e.session,
        e.questionId,
        e.answer
      )), this.retryRequest = void 0, this.endSubmissionWatch(), await this.refreshAvailability();
    } catch (t) {
      await this.recover(t);
    } finally {
      this.loading = !1;
    }
  }
  async armReminder() {
    if (!(this.hass === void 0 || this.profile === void 0 || this.trackId === "")) {
      this.loading = !0, this.errorMessage = "";
      try {
        this.reminder = await Dt(this.hass, this.profile.profile_id, this.trackId, "learn"), this.notice = this.t("learn.reminderArmed");
      } catch (e) {
        this.errorMessage = e instanceof Error ? e.message : String(e);
      } finally {
        this.loading = !1;
      }
    }
  }
  async cancelReminder() {
    if (!(this.hass === void 0 || this.profile === void 0 || this.trackId === "")) {
      this.loading = !0;
      try {
        this.reminder = await It(this.hass, this.profile.profile_id, this.trackId, "learn"), this.notice = this.t("learn.reminderCancelled");
      } finally {
        this.loading = !1;
      }
    }
  }
  openCalibrationSetup() {
    this.calibrationSetup = !0;
  }
  closeCalibrationSetup() {
    this.calibrationSetup = !1;
  }
  setCalibrationSize(e) {
    const t = e.currentTarget;
    if (!(t instanceof HTMLSelectElement)) return;
    const i = Number.parseInt(t.value, 10);
    [20, 30, 40].includes(i) && (this.calibrationSize = i);
  }
  async startCalibration() {
    if (!(this.hass === void 0 || this.profile === void 0 || this.trackId === "")) {
      this.loading = !0, this.errorMessage = "";
      try {
        const e = await Hi(
          this.hass,
          this.profile.profile_id,
          this.trackId,
          this.calibrationSize
        );
        this.calibrationSetup = !1, this.dispatchEvent(new CustomEvent("locklearn-open-session", {
          detail: { session: e },
          bubbles: !0,
          composed: !0
        }));
      } catch (e) {
        this.errorMessage = e instanceof Error ? e.message : String(e);
      } finally {
        this.loading = !1;
      }
    }
  }
  bulkGuardStorageKey(e) {
    return `locklearn:known-bulk-guard:${e}`;
  }
  maybeShowKnownBulkGuard() {
    if (this.session === void 0 || !cs(this.session.answers)) return;
    const e = this.bulkGuardStorageKey(this.session.id);
    globalThis.localStorage?.getItem(e) !== "shown" && (globalThis.localStorage?.setItem(e, "shown"), this.knownBulkGuardVisible = !0);
  }
  dismissKnownBulkGuard() {
    this.knownBulkGuardVisible = !1;
  }
  startCalibrationFromBulkGuard() {
    this.knownBulkGuardVisible = !1, this.calibrationSetup = !0;
  }
  async markKnownAlready(e) {
    if (this.lastKnownCardKey = e.card_key, !await this.learningAction("known_already")) {
      this.lastKnownCardKey = void 0;
      return;
    }
    this.maybeShowKnownBulkGuard(), this.lastKnownCardKey === e.card_key && (this.notice = "", this.knownNoticeVisible = !0, this.knownUndoTimer !== void 0 && globalThis.clearTimeout(this.knownUndoTimer), this.knownUndoTimer = globalThis.setTimeout(() => {
      this.knownUndoTimer = void 0, this.knownNoticeVisible = !1, this.lastKnownCardKey = void 0;
    }, 8e3));
  }
  async undoKnownAlready() {
    if (!(this.hass === void 0 || this.profile === void 0 || this.session === void 0 || this.session.track_id === null || this.lastKnownCardKey === void 0)) {
      this.loading = !0;
      try {
        await Nt(this.hass, this.profile.profile_id, this.session.track_id, this.lastKnownCardKey), this.lastKnownCardKey = void 0, this.knownNoticeVisible = !1, this.knownUndoTimer !== void 0 && globalThis.clearTimeout(this.knownUndoTimer), this.knownUndoTimer = void 0, this.notice = this.t("learn.knownUndone"), await this.refreshAvailability();
      } catch (e) {
        this.errorMessage = e instanceof Error ? e.message : String(e);
      } finally {
        this.loading = !1;
      }
    }
  }
  async start(e = !1) {
    if (!(this.hass === void 0 || this.profile === void 0 || this.trackId === "" || !gt(this.profile))) {
      this.loading = !0, this.errorMessage = "", this.notice = "";
      try {
        const t = await Ce(
          this.hass,
          this.profile.profile_id,
          this.trackId,
          void 0,
          e
        );
        this.applySession(t), await this.refreshAvailability();
      } catch (t) {
        this.errorMessage = t instanceof Error ? t.message : String(t);
      } finally {
        this.loading = !1;
      }
    }
  }
  async resume() {
    const e = this.selectedTrack()?.last_session;
    if (!(this.hass === void 0 || !mt(e))) {
      this.loading = !0, this.errorMessage = "";
      try {
        this.applySession(await E(this.hass, e.session_id)), await this.refreshAvailability();
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
        this.applySession(await E(this.hass, this.session.id)), this.notice = this.t("learn.reloaded");
        return;
      } catch {
      }
    this.errorMessage = e instanceof Error ? e.message : String(e);
  }
  async finalizeIfDone(e) {
    return this.hass !== void 0 && e.status === "active" && e.current_question === null && e.question_count > 0 ? Et(this.hass, e) : e;
  }
  async learningAction(e, t) {
    const i = this.session?.current_question;
    if (this.hass === void 0 || this.session === void 0 || i === null || i === void 0) return !1;
    const a = this.session, o = {
      kind: "learning",
      action: e,
      hint_used: this.hintUsed,
      presentation_to_answer_ms: t ?? this.elapsedMs(),
      ...this.forceEarlyCurrent ? { force_early: !0 } : {}
    };
    this.retryRequest = {
      session: a,
      questionId: i.question_id,
      answer: o
    }, this.loading = !0, this.errorMessage = "", this.beginSubmissionWatch();
    try {
      const n = await _e(
        this.hass,
        a,
        i.question_id,
        o
      );
      return this.retryRequest = void 0, this.applySession(await this.finalizeIfDone(n)), await this.refreshAvailability(), !0;
    } catch (n) {
      return await this.recover(n), !1;
    } finally {
      this.loading = !1, this.endSubmissionWatch();
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
        await Lt(
          this.hass,
          this.profile.profile_id,
          this.session.track_id,
          t.card_key,
          e
        );
        const i = await _e(
          this.hass,
          this.session,
          t.question_id,
          { kind: "user_state", action: e }
        );
        this.applySession(await this.finalizeIfDone(i)), await this.refreshAvailability();
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
        await Ht(
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
        await Ut(
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
  renderReminderAction() {
    return X(this.availability) === null ? l : this.hasNotificationTarget ? this.reminder?.active ? r`<button @click=${() => {
      this.cancelReminder();
    }} ?disabled=${this.loading}>
          ${this.t("learn.cancelReminder")}
        </button>` : r`<button @click=${() => {
      this.armReminder();
    }} ?disabled=${this.loading}>
          ${this.locale() === "fr" ? "Me prévenir pour ce rappel" : "Notify me for this recall"}
        </button>` : r`<button @click=${() => se("settings")}>
        ${this.t("learn.configureNotifications")}
      </button>`;
  }
  renderAvailabilitySummary() {
    const e = this.availability;
    if (e === void 0) return l;
    const t = X(e), i = ft(e), a = this.locale() === "fr";
    return r`
      <div class="notice" role="status">
        <strong>${this.t("learn.readiness")}</strong>
        ${e.available_now > 0 ? r`<div>
              ${a ? `Une nouvelle session de ${e.available_now} cartes est disponible.` : `A new session of ${e.available_now} cards is available.`}
            </div>` : r`<div>${this.t("learn.noCardsReady")}</div>`}
        <dl>
          <dt>${a ? "Cartes restant à découvrir dans ce parcours" : "Cards left to discover in this Track"}</dt>
          <dd>${e.new_cards}</dd>
          <dt>${this.t("learn.startedCards")}</dt>
          <dd>${e.introduced_cards}</dd>
          <dt>${a ? "Cartes commencées en attente de leur prochaine étape" : "Started cards waiting for their next step"}</dt>
          <dd>${i}</dd>
          <dt>${this.t("learn.newQuotaRemaining")}</dt>
          <dd>${e.remaining_new_quota}</dd>
        </dl>
        ${t === null ? e.next_available_reason === "new_quota" && e.next_available_at_utc !== null ? r`<div>
                <strong>${this.t("learn.quotaReset")}:</strong>
                ${this.dueLabel(e.next_available_at_utc)}
              </div>` : e.available_now === 0 ? r`<div class="muted">${this.t("learn.noExactTime")}</div>` : l : r`<div>
              <strong>${this.nextLearningRecallLabel()}:</strong>
              ${this.dueLabel(t)}
            </div>`}
        ${e.forceable_early > 0 ? r`
          <p class="muted">
            ${e.forceable_new > 0 ? this.t("learn.overrideNewHelp") : this.t("learn.continueEarlyHelp")}
          </p>
          <button class="primary" @click=${() => {
      this.start(!0);
    }} ?disabled=${this.loading}>
            ${this.t("learn.continueNow")}
          </button>
        ` : l}
      </div>
    `;
  }
  render() {
    if (this.profile === void 0) return l;
    if (!gt(this.profile))
      return r`<section class="learn-card"><p>${this.t("learn.readOnly")}</p></section>`;
    const e = this.tracks();
    if (e.length === 0)
      return r`<section class="learn-card"><p>${this.t("learn.noTracks")}</p></section>`;
    const t = this.selectedTrack(), i = mt(t?.last_session);
    return r`
      <section class="learn-shell">
        <div class="toolbar">
          <label>
            <span>${this.t("learn.track")}</span>
            <select .value=${this.trackId} @change=${this.setTrack} ?disabled=${this.loading}>
              ${e.map(
      (a) => r`
                  <option value=${a.track_id}>
                    ${a.name} · ${a.source_language} → ${a.target_language}
                  </option>
                `
    )}
            </select>
          </label>
          <div class="actions">
            ${this.session === void 0 && i ? r`<button class="primary" @click=${this.resume} ?disabled=${this.loading}>
                  ${this.t("learn.resume")}
                </button>` : this.session === void 0 ? r`<button class="primary" @click=${() => {
      this.start();
    }} ?disabled=${this.loading}>
                  ${this.t("learn.start")}
                </button>` : l}
          </div>
          ${this.session === void 0 ? r`<p class="muted">
            ${i ? this.t("learn.resumeHelp") : this.t("learn.startHelp")}
          </p>` : l}
        </div>
        ${this.session === void 0 ? this.renderAvailabilitySummary() : l}
        ${this.session === void 0 ? this.renderNoDeadEndActions() : l}
        ${this.calibrationSetup ? r`
              <section class="learn-card" role="dialog" aria-labelledby="calibration-title">
                <h2 id="calibration-title">${this.t("learn.calibrationTitle")}</h2>
                <p>${this.t("learn.calibrationHelp")}</p>
                <label>
                  <span>${this.t("learn.calibrationSize")}</span>
                  <select .value=${String(this.calibrationSize)} @change=${this.setCalibrationSize}>
                    <option value="20">20</option>
                    <option value="30">30</option>
                    <option value="40">40</option>
                  </select>
                </label>
                <div class="actions">
                  <button class="primary" @click=${() => {
      this.startCalibration();
    }} ?disabled=${this.loading}>
                    ${this.t("learn.calibrationStart")}
                  </button>
                  <button @click=${this.closeCalibrationSetup} ?disabled=${this.loading}>
                    ${this.t("common.close")}
                  </button>
                </div>
              </section>
            ` : l}
        ${this.loading && this.session === void 0 ? r`<div class="notice" role="status">${this.t("learn.loading")}</div>` : l}
        ${this.errorMessage ? r`<div class="error" role="alert">
              <strong>${this.t("learn.error")}</strong>
              <div>${this.errorMessage}</div>
            </div>` : l}
        ${this.submissionSlow ? r`<div class="notice" role="status" aria-live="polite">
              <strong>${this.t("learn.answerUnconfirmed")}</strong>
              <button @click=${() => {
      this.verifySubmission();
    }}>${this.t("learn.verify")}</button>
              ${this.retryRequest === void 0 ? l : r`<button @click=${() => {
      this.retrySubmission();
    }}>${this.t("learn.retryAnswer")}</button>`}
            </div>` : l}
        ${this.notice ? r`<div class="notice" role="status" aria-live="polite">${this.notice}</div>` : l}
        ${this.renderSession()}
        ${this.knownBulkGuardVisible ? r`<div class="bulk-guard" role="presentation">
              <section class="bulk-guard-card" role="dialog" aria-modal="true" aria-labelledby="known-bulk-title">
                <h2 id="known-bulk-title">${this.t("learn.bulkGuardTitle")}</h2>
                <p>${this.t("learn.bulkGuardBody")}</p>
                <div class="actions">
                  <button class="primary" @click=${this.startCalibrationFromBulkGuard}>
                    ${this.t("learn.bulkGuardCalibrate")}
                  </button>
                  <button @click=${this.dismissKnownBulkGuard}>
                    ${this.t("learn.bulkGuardContinue")}
                  </button>
                </div>
              </section>
            </div>` : l}
        ${this.knownNoticeVisible && this.lastKnownCardKey !== void 0 ? r`<div class="known-snackbar" role="status" aria-live="polite">
              <span>${this.t("learn.knownPending")}</span>
              <button @click=${() => {
      this.undoKnownAlready();
    }} ?disabled=${this.loading}>
                ${this.t("learn.undo")}
              </button>
            </div>` : l}
        ${this.concernedFilter === void 0 ? l : r`<locklearn-concerned-cards
              .hass=${this.hass}
              .profileId=${this.profile.profile_id}
              .trackId=${this.trackId}
              .filter=${this.concernedFilter}
              .mode=${"learn"}
              .language=${this.locale()}
              .timeZone=${this.profile.timezone}
              @locklearn-concerned-cards-close=${this.closeConcerned}
              @locklearn-concerned-cards-changed=${() => {
      this.refreshAvailability();
    }}
            ></locklearn-concerned-cards>`}
      </section>
    `;
  }
  async startCalibrationFollowup() {
    if (!(this.hass === void 0 || this.profile === void 0 || this.calibrationFollowup?.source_session_id === null || this.calibrationFollowup?.source_session_id === void 0)) {
      this.loading = !0, this.errorMessage = "";
      try {
        const e = await Rt(
          this.hass,
          this.profile.profile_id,
          this.trackId,
          this.calibrationFollowup.source_session_id
        );
        this.applySession(e), await this.refreshAvailability();
      } catch (e) {
        this.errorMessage = e instanceof Error ? e.message : String(e);
      } finally {
        this.loading = !1;
      }
    }
  }
  blockerTitle(e) {
    const t = this.locale() === "fr";
    return ({
      scheduled_step: ["Started card waiting for recall", "Carte déjà commencée en attente de rappel"],
      known_already_verification: ["Already-known cards to verify", "Cartes déjà connues à vérifier"],
      new_quota: ["New-card limit reached", "Limite de nouvelles cartes atteinte"],
      sibling_gap: ["Similar cards are spaced", "Cartes similaires espacées"],
      confusable_gap: ["Similar cards are spaced", "Cartes similaires espacées"],
      buried: ["Cards temporarily set aside", "Cartes mises de côté temporairement"],
      prerequisite: ["Prerequisites first", "Prérequis à apprendre d’abord"],
      suspended: ["Suspended cards", "Cartes suspendues"]
    }[e] ?? ["Unavailable for now", "Indisponible pour le moment"])[t ? 1 : 0];
  }
  blockerBody(e, t) {
    const i = this.locale() === "fr";
    return e === "scheduled_step" ? i ? `${t} carte(s) attendent leur prochaine étape d’apprentissage.` : `${t} card(s) are waiting for their next learning step.` : e === "known_already_verification" ? i ? `${t} carte(s) marquées comme déjà connues seront vérifiées plus tard.` : `${t} already-known card(s) will be verified later.` : e === "new_quota" ? i ? `${t} carte(s) attendent le prochain quota de nouvelles cartes.` : `${t} card(s) are waiting for the next new-card quota.` : e === "sibling_gap" || e === "confusable_gap" ? i ? `${t} carte(s) similaires sont espacées pour limiter les confusions.` : `${t} similar card(s) are spaced to reduce confusion.` : e === "prerequisite" ? i ? `${t} carte(s) attendent un prérequis.` : `${t} card(s) are waiting for a prerequisite.` : e === "suspended" ? i ? `${t} carte(s) sont suspendues.` : `${t} card(s) are suspended.` : e === "buried" ? i ? `${t} carte(s) sont temporairement mises de côté.` : `${t} card(s) are temporarily set aside.` : i ? `${t} carte(s) ne sont pas disponibles pour le moment.` : `${t} card(s) are not available yet.`;
  }
  blockerFilter(e) {
    return e === "known_already_verification" ? "known_pending" : e === "suspended" ? "suspended" : e === "buried" ? "buried" : e === "prerequisite" ? "prerequisite_support" : "current_waiting_context";
  }
  openConcerned(e) {
    this.concernedFilter = e;
  }
  closeConcerned() {
    this.concernedFilter = void 0;
  }
  renderNoDeadEndActions() {
    const e = this.availability;
    return e === void 0 ? l : r`
      <div class="actions">
        ${(this.calibrationFollowup?.pending_count ?? 0) > 0 ? r`<button class="primary" @click=${() => {
      this.startCalibrationFollowup();
    }} ?disabled=${this.loading}>
              ${this.locale() === "fr" ? "Apprendre les cartes identifiées par la calibration" : "Learn the cards identified by calibration"}
            </button>` : e.new_cards > 0 ? r`<button @click=${this.openCalibrationSetup} ?disabled=${this.loading}>
                ${this.t("learn.quickCalibration")}
              </button>` : l}
        ${this.readyAlternative === void 0 ? l : r`<button @click=${() => {
      this.openReadyAlternative();
    }} ?disabled=${this.loading}>
              ${this.t("learn.readyAlternative").replace("{track}", this.readyAlternative.trackName).replace("{mode}", this.readyAlternative.mode === "learn" ? this.t("learn.title") : this.t("quiz.title"))}
            </button>`}
        ${this.renderReminderAction()}
      </div>
      ${e.blockers.length > 0 ? r`<details>
            <summary>${this.t("learn.conditionsTitle")}</summary>
            <dl>
              ${e.blockers.map(
      (t) => r`
                  <dt>${this.blockerTitle(t.code)}</dt>
                  <dd>
                    ${this.blockerBody(t.code, t.count)}
                    ${t.until_utc === null ? l : r` · ${this.dueLabel(t.until_utc)}`}
                    <button
                      @click=${() => this.openConcerned(this.blockerFilter(t.code))}
                      ?disabled=${this.loading}
                    >
                      ${this.t("learn.viewCards")}
                    </button>
                  </dd>
                `
    )}
            </dl>
          </details>` : l}
    `;
  }
  renderSession() {
    if (this.session === void 0) return l;
    if (this.session.question_count === 0) {
      const e = X(this.availability), t = this.availability?.next_available_at_utc ?? null, i = this.availability?.next_available_reason ?? null, a = (this.availability?.forceable_early ?? 0) > 0, o = this.availability?.available_now ?? 0;
      return o > 0 ? r`
          <section class="learn-card">
            <h2>${this.t("learn.readyTitle")}</h2>
            <p>${this.locale() === "fr" ? `Une nouvelle session de ${o} cartes est disponible.` : `A new session of ${o} cards is available.`}</p>
            ${e === null ? l : r`
              <p><strong>${this.nextLearningRecallLabel()}:</strong> ${this.dueLabel(e)}</p>
              <div class="actions">${this.renderReminderAction()}</div>
            `}
            <button class="primary" @click=${() => {
        this.start();
      }} ?disabled=${this.loading}>
              ${this.t("learn.start")}
            </button>
          </section>
        ` : r`
        <section class="learn-card">
          <h2>${this.t("learn.pauseTitle")}</h2>
          <p>${this.t("learn.emptyExplain")}</p>
          <dl>
            <dt>${this.t("learn.startedCards")}</dt><dd>${this.availability?.introduced_cards ?? 0}</dd>
            <dt>${this.locale() === "fr" ? "Cartes restant à découvrir dans ce parcours" : "Cards left to discover in this Track"}</dt>
            <dd>${this.availability?.new_cards ?? 0}</dd>
            <dt>${this.locale() === "fr" ? "Cartes commencées en attente de leur prochaine étape" : "Started cards waiting for their next step"}</dt>
            <dd>${ft(this.availability)}</dd>
            <dt>${this.t("learn.newQuotaRemaining")}</dt><dd>${this.availability?.remaining_new_quota ?? 0}</dd>
          </dl>
          ${e !== null ? r`<p><strong>${this.nextLearningRecallLabel()}:</strong> ${this.dueLabel(e)}</p>` : t === null ? r`<p class="muted">${this.t("learn.noExactTime")}</p>` : r`
                  <p>
                    <strong>${this.t(
        i === "new_quota" ? "learn.quotaReset" : "learn.nextAvailable"
      )}:</strong>
                    ${this.dueLabel(t)}
                  </p>
                `}
          ${this.renderReminderAction()}
          ${a ? r`
            <p class="muted">
              ${(this.availability?.forceable_new ?? 0) > 0 ? this.t("learn.overrideNewHelp") : this.t("learn.continueEarlyHelp")}
            </p>
            <button class="primary" @click=${() => {
        this.start(!0);
      }} ?disabled=${this.loading}>
              ${this.t("learn.continueNow")}
            </button>
          ` : l}
        </section>
      `;
    }
    if (this.session.current_question === null || this.session.status === "completed") {
      const e = X(this.availability), t = this.availability?.next_available_at_utc ?? null, i = this.availability?.next_available_reason ?? null, a = (this.availability?.forceable_early ?? 0) > 0;
      return r`
        <section class="learn-card">
          <h2>${this.t("learn.completed")}</h2>
          <p>${this.t("learn.completedBody")}</p>
          ${e !== null ? r`<p><strong>${this.nextLearningRecallLabel()}:</strong> ${this.dueLabel(e)}</p>` : t === null ? l : r`
              <p>
                <strong>${this.t(
        i === "new_quota" ? "learn.quotaReset" : "learn.nextAvailable"
      )}:</strong>
                ${this.dueLabel(t)}
              </p>
            `}
          <div class="actions">${this.renderReminderAction()}</div>
          ${a ? r`
            <p class="muted">${this.t("learn.continueEarlyHelp")}</p>
            <button class="primary" @click=${() => {
        this.start(!0);
      }} ?disabled=${this.loading}>
              ${this.t("learn.continueNow")}
            </button>
          ` : l}
          <button @click=${() => {
        this.start();
      }} ?disabled=${this.loading}>
            ${this.t("learn.newSession")}
          </button>
        </section>
      `;
    }
    return this.waitingUntil !== void 0 ? this.renderWaiting(this.session.current_question) : ss(this.session.current_question) ? this.renderIntroduction(this.session.current_question) : this.renderRetrieval(this.session.current_question);
  }
  renderWaiting(e) {
    const t = this.waitingUntil;
    if (t === void 0) return l;
    const i = new Date(t), a = Number.isNaN(i.getTime()) ? "" : new Intl.DateTimeFormat(this.locale(), { timeStyle: "medium" }).format(i);
    return r`
      <article class="learn-card" aria-live="polite">
        ${this.renderProgress(e)}
        <div class="stage">${this.t("learn.waiting")}</div>
        <p>${this.t("learn.waitingBody")}</p>
        <p>
          ${this.t("learn.waitingUntil")}
          <time datetime=${t}>${a}</time>
        </p>
        <p class="muted">${this.t("learn.waitingExplain")}</p>
        <button class="primary" @click=${this.continueCurrentEarly} ?disabled=${this.loading}>
          ${this.t("learn.continueNow")}
        </button>
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
      (i, a) => this.renderBlock(i, a === 0)
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
            ${e.position + 1 < (this.session?.question_count ?? 0) ? this.locale() === "fr" ? "Passer à la carte suivante" : "Go to the next card" : this.locale() === "fr" ? "Continuer la session" : "Continue the session"}
          </button>
        </div>
        ${this.renderSecondaryActions(e, !0)}
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
      (a) => a.blocks.map((o) => this.renderBlock(o, !1))
    )}
          ${t.prompt.blocks.map((a) => this.renderBlock(a, !0))}
        </div>
        ${this.hintUsed ? r`
              <div class="hint-state" role="status">
                ${this.t("learn.hintUsed")}
                ${i.map((a) => this.renderBlock(a, !1))}
              </div>
            ` : l}
        ${this.revealed ? r`
              <div class="answer">
                <div class="stage">${this.t("learn.answer")}</div>
                ${t.answer.blocks.map((a) => this.renderBlock(a, !0))}
                ${this.pendingIdk ? r`<p>${this.t("learn.feedbackIdk")}</p>` : l}
              </div>
            ` : l}
        ${this.revealed ? l : r`<p class="muted">${this.locale() === "fr" ? "Répondez mentalement, puis révélez la réponse pour vous évaluer." : "Answer mentally, then reveal the answer to evaluate yourself."}</p>`}
        <div class="actions">
          ${this.revealed ? this.pendingIdk ? r`<button
                  class="primary"
                  @click=${() => {
      this.learningAction("idk", this.pendingIdkLatency);
    }}
                  ?disabled=${this.loading}
                >
                  ${this.locale() === "fr" ? "Continuer la session" : "Continue the session"}
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
        ${i.map((a) => this.renderBlock(a, !1))}
      </div>
    `;
  }
  renderSecondaryActions(e, t = !1) {
    return r`
      <div class="secondary-actions">
        ${t ? r`<button
              @click=${() => {
      this.markKnownAlready(e);
    }}
              ?disabled=${this.loading}
            >
              ${this.t("learn.knownAlready")}
            </button>` : l}
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
            @input=${(i) => {
      const a = i.currentTarget;
      a instanceof HTMLTextAreaElement && (this.mnemonic = a.value);
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
    return He(e, t);
  }
};
Fe.styles = N`
    ${Ie}
    ${j}

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

    dl {
      display: grid;
      grid-template-columns: minmax(170px, auto) 1fr;
      gap: 6px 12px;
      margin: 12px 0 0;
    }

    dt {
      color: var(--secondary-text-color);
    }

    dd {
      margin: 0;
      font-weight: 650;
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

    .bulk-guard {
      position: fixed;
      z-index: 1200;
      inset: 0;
      display: grid;
      place-items: center;
      padding: 20px;
      background: rgb(0 0 0 / 45%);
    }

    .bulk-guard-card {
      width: min(520px, 100%);
      display: grid;
      gap: 14px;
      padding: 20px;
      border-radius: 14px;
      background: var(--card-background-color, var(--primary-background-color));
      box-shadow: var(--ha-card-box-shadow, 0 12px 36px rgb(0 0 0 / 30%));
    }

    .known-snackbar {
      position: sticky;
      z-index: 1100;
      bottom: max(16px, env(safe-area-inset-bottom));
      width: min(560px, 100%);
      margin: 0 auto max(16px, env(safe-area-inset-bottom));
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 12px 14px;
      border-radius: 12px;
      background: var(--card-background-color, var(--primary-background-color));
      color: var(--primary-text-color);
      box-shadow: var(--ha-card-box-shadow, 0 8px 28px rgb(0 0 0 / 24%));
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

      .known-snackbar {
        width: 100%;
        align-items: stretch;
        flex-direction: column;
      }

      .progress {
        flex-direction: column;
        gap: 4px;
      }
    }
  `;
let p = Fe;
g([
  f({ attribute: !1 })
], p.prototype, "hass");
g([
  f({ attribute: !1 })
], p.prototype, "profile");
g([
  f({ attribute: !1 })
], p.prototype, "dashboard");
g([
  f({ attribute: !1 })
], p.prototype, "externalSession");
g([
  c()
], p.prototype, "trackId");
g([
  c()
], p.prototype, "session");
g([
  c()
], p.prototype, "loading");
g([
  c()
], p.prototype, "errorMessage");
g([
  c()
], p.prototype, "notice");
g([
  c()
], p.prototype, "revealed");
g([
  c()
], p.prototype, "hintUsed");
g([
  c()
], p.prototype, "pendingIdk");
g([
  c()
], p.prototype, "pendingIdkLatency");
g([
  c()
], p.prototype, "mnemonic");
g([
  c()
], p.prototype, "reportMessage");
g([
  c()
], p.prototype, "waitingUntil");
g([
  c()
], p.prototype, "availability");
g([
  c()
], p.prototype, "forceEarlyCurrent");
g([
  c()
], p.prototype, "reminder");
g([
  c()
], p.prototype, "submissionSlow");
g([
  c()
], p.prototype, "retryRequest");
g([
  c()
], p.prototype, "lastKnownCardKey");
g([
  c()
], p.prototype, "knownNoticeVisible");
g([
  c()
], p.prototype, "concernedFilter");
g([
  c()
], p.prototype, "readyAlternative");
g([
  c()
], p.prototype, "calibrationSetup");
g([
  c()
], p.prototype, "calibrationSize");
g([
  c()
], p.prototype, "hasNotificationTarget");
g([
  c()
], p.prototype, "knownBulkGuardVisible");
g([
  c()
], p.prototype, "calibrationFollowup");
globalThis.customElements !== void 0 && customElements.get("locklearn-learn-view") === void 0 && customElements.define("locklearn-learn-view", p);
function vt(s) {
  return s != null && ["quiz", "calibration"].includes(s.session_type) && ["active", "paused"].includes(s.status);
}
function bt(s) {
  return s !== void 0 && s.role !== "viewer";
}
function us(s) {
  return s?.payload.quiz;
}
function hs(s) {
  return s?.format === "mcq" || s?.format === "cloze_mcq";
}
function yt(s) {
  return s?.format === "free_text" && s.result === "wrong" && s.reportable && typeof s.submitted_text == "string" && s.grading_policy_kind !== void 0 && s.grading_policy_version !== void 0 && s.normalization_version !== void 0;
}
var ps = Object.defineProperty, k = (s, e, t, i) => {
  for (var a = void 0, o = s.length - 1, n; o >= 0; o--)
    (n = s[o]) && (a = n(e, t, a) || a);
  return a && ps(e, t, a), a;
};
function Se() {
  return globalThis.performance?.now() ?? Date.now();
}
const je = class je extends z {
  constructor() {
    super(...arguments), this.trackId = "", this.format = "mixed", this.loading = !1, this.errorMessage = "", this.notice = "", this.freeText = "", this.hintUsed = !1, this.submissionSlow = !1, this.hasNotificationTarget = !1, this.questionStartedAt = Se(), this.questionId = null, this.refreshOnReturn = () => {
      document.visibilityState === "visible" && this.refreshAvailability();
    };
  }
  connectedCallback() {
    super.connectedCallback(), globalThis.addEventListener("focus", this.refreshOnReturn), globalThis.addEventListener("online", this.refreshOnReturn), globalThis.addEventListener("pageshow", this.refreshOnReturn), document.addEventListener("visibilitychange", this.refreshOnReturn);
  }
  disconnectedCallback() {
    this.nextDueTimer !== void 0 && globalThis.clearTimeout(this.nextDueTimer), this.submissionTimer !== void 0 && globalThis.clearTimeout(this.submissionTimer), globalThis.removeEventListener("focus", this.refreshOnReturn), globalThis.removeEventListener("online", this.refreshOnReturn), globalThis.removeEventListener("pageshow", this.refreshOnReturn), document.removeEventListener("visibilitychange", this.refreshOnReturn), super.disconnectedCallback();
  }
  updated(e) {
    if (e.has("profile") || e.has("dashboard")) {
      const t = this.tracks();
      t.some((i) => i.track_id === this.trackId) || (this.trackId = t[0]?.track_id ?? ""), e.has("profile") && (this.session = void 0, this.resetQuestionUi()), this.refreshAvailability();
    }
    e.has("externalSession") && this.externalSession !== void 0 && this.profile !== void 0 && this.externalSession.profile_id === this.profile.profile_id && ["quiz", "calibration"].includes(this.externalSession.type) && (this.trackId = this.externalSession.track_id ?? this.trackId, this.applySession(this.externalSession), this.notice = this.externalSession.type === "calibration" ? this.t("quiz.calibrationStarted") : this.t("quiz.reloaded"), this.dispatchEvent(new CustomEvent("locklearn-session-handoff-consumed", {
      bubbles: !0,
      composed: !0
    })));
  }
  locale() {
    const e = this.hass?.locale?.language ?? this.hass?.language ?? globalThis.navigator?.language ?? "en";
    return Z(e);
  }
  t(e) {
    return O(this.locale(), e);
  }
  tracks() {
    return this.dashboard?.tracks ?? [];
  }
  selectedTrack() {
    return this.tracks().find((e) => e.track_id === this.trackId);
  }
  setTrack(e) {
    const t = e.currentTarget;
    t instanceof HTMLSelectElement && (this.trackId = t.value, this.session = void 0, this.errorMessage = "", this.resetQuestionUi(), this.refreshAvailability());
  }
  setFormat(e) {
    const t = e.currentTarget;
    t instanceof HTMLSelectElement && (this.format = t.value, this.session = void 0, this.errorMessage = "", this.resetQuestionUi());
  }
  resetQuestionUi() {
    this.feedback = void 0, this.pendingAnswer = void 0, this.pendingSession = void 0, this.freeText = "", this.hintUsed = !1, this.notice = "", this.questionStartedAt = Se(), this.questionId = this.session?.current_question?.question_id ?? null;
  }
  applySession(e) {
    const i = (e.current_question?.question_id ?? null) !== this.questionId;
    this.session = e, i && this.resetQuestionUi();
  }
  async refreshAvailability() {
    if (this.hass === void 0 || this.profile === void 0 || this.trackId === "") {
      this.availability = void 0;
      return;
    }
    try {
      this.availability = await ke(
        this.hass,
        this.profile.profile_id,
        this.trackId,
        "quiz"
      ), this.readyAlternative = this.availability.available_now === 0 ? await Ft(this.hass, this.dashboard, this.trackId, "quiz") : void 0, this.reminder = await Mt(
        this.hass,
        this.profile.profile_id,
        this.trackId,
        "quiz"
      ), this.hasNotificationTarget = (await Ue(this.hass, this.profile.profile_id)).some((t) => t.enabled), this.nextDueTimer !== void 0 && globalThis.clearTimeout(this.nextDueTimer);
      const e = this.availability.next_available_at_utc;
      if (e !== null) {
        const t = Date.parse(e) - Date.now();
        t > 0 && t < 2147e6 && (this.nextDueTimer = globalThis.setTimeout(() => {
          this.nextDueTimer = void 0, this.refreshAvailability();
        }, t + 250));
      }
    } catch {
      this.availability = void 0, this.readyAlternative = void 0;
    }
  }
  async openReadyAlternative() {
    if (this.hass === void 0 || this.profile === void 0 || this.readyAlternative === void 0) return;
    const e = this.readyAlternative;
    this.loading = !0, this.errorMessage = "";
    try {
      if (e.mode === "quiz") {
        this.trackId = e.trackId, this.session = void 0, this.resetQuestionUi(), this.applySession(await ze(
          this.hass,
          this.profile.profile_id,
          e.trackId,
          void 0,
          this.format
        )), await this.refreshAvailability();
        return;
      }
      const t = await Ce(
        this.hass,
        this.profile.profile_id,
        e.trackId
      );
      this.dispatchEvent(new CustomEvent("locklearn-open-session", {
        detail: { session: t },
        bubbles: !0,
        composed: !0
      }));
    } catch (t) {
      this.errorMessage = t instanceof Error ? t.message : String(t);
    } finally {
      this.loading = !1;
    }
  }
  dueLabel(e) {
    if (e === null) return "";
    const t = new Date(e);
    if (Number.isNaN(t.getTime())) return "";
    const i = Math.max(1, Math.ceil((t.getTime() - Date.now()) / 6e4));
    return `${new Intl.DateTimeFormat(this.locale(), { timeStyle: "short" }).format(t)} · ${this.t("quiz.inAbout")} ${i} min`;
  }
  nextQuizAvailableLabel() {
    return this.locale() === "fr" ? "Prochaine carte disponible pour un quiz" : "Next card available for a quiz";
  }
  elapsedMs() {
    return Math.max(0, Math.round(Se() - this.questionStartedAt));
  }
  beginSubmissionWatch() {
    this.submissionSlow = !1, this.submissionTimer !== void 0 && globalThis.clearTimeout(this.submissionTimer), this.submissionTimer = globalThis.setTimeout(() => {
      this.submissionTimer = void 0, this.submissionSlow = !0;
    }, 8e3);
  }
  endSubmissionWatch() {
    this.submissionTimer !== void 0 && globalThis.clearTimeout(this.submissionTimer), this.submissionTimer = void 0, this.submissionSlow = !1;
  }
  async verifySubmission() {
    if (!(this.hass === void 0 || this.session === void 0))
      try {
        const e = this.retryRequest?.session ?? this.session, t = await E(this.hass, e.id), i = t.version !== e.version || t.current_question?.question_id !== e.current_question?.question_id;
        this.applySession(t), i ? (this.loading = !1, this.retryRequest = void 0, this.endSubmissionWatch(), this.notice = this.t("quiz.answerApplied")) : (this.loading = !1, this.submissionSlow = !0, this.notice = this.t("quiz.answerNotConfirmed"));
      } catch (e) {
        this.errorMessage = e instanceof Error ? e.message : String(e);
      }
  }
  async retrySubmission() {
    if (this.hass === void 0 || this.retryRequest === void 0) return;
    const e = this.retryRequest;
    this.loading = !0, this.errorMessage = "";
    try {
      const t = await E(this.hass, e.session.id);
      if (!(t.version === e.session.version && t.current_question?.question_id === e.questionId)) {
        this.applySession(t), this.retryRequest = void 0, this.endSubmissionWatch(), this.notice = this.t("quiz.answerApplied");
        return;
      }
      const a = await de(
        this.hass,
        e.session,
        e.questionId,
        e.answer
      );
      this.feedback = a.feedback, this.pendingSession = a.session, this.retryRequest = void 0, this.retryRequest = void 0, this.endSubmissionWatch();
    } catch (t) {
      await this.recover(t);
    } finally {
      this.loading = !1;
    }
  }
  async armReminder() {
    if (!(this.hass === void 0 || this.profile === void 0 || this.trackId === "")) {
      this.loading = !0, this.errorMessage = "";
      try {
        this.reminder = await Dt(this.hass, this.profile.profile_id, this.trackId, "quiz"), this.notice = this.t("quiz.reminderArmed");
      } catch (e) {
        this.errorMessage = e instanceof Error ? e.message : String(e);
      } finally {
        this.loading = !1;
      }
    }
  }
  async cancelReminder() {
    if (!(this.hass === void 0 || this.profile === void 0 || this.trackId === "")) {
      this.loading = !0;
      try {
        this.reminder = await It(this.hass, this.profile.profile_id, this.trackId, "quiz"), this.notice = this.t("quiz.reminderCancelled");
      } finally {
        this.loading = !1;
      }
    }
  }
  async start() {
    if (!(this.hass === void 0 || this.profile === void 0 || this.trackId === "" || !bt(this.profile))) {
      this.loading = !0, this.errorMessage = "";
      try {
        this.applySession(
          await ze(
            this.hass,
            this.profile.profile_id,
            this.trackId,
            void 0,
            this.format
          )
        ), await this.refreshAvailability();
      } catch (e) {
        this.errorMessage = e instanceof Error ? e.message : String(e);
      } finally {
        this.loading = !1;
      }
    }
  }
  async resume() {
    const e = this.selectedTrack()?.last_session;
    if (!(this.hass === void 0 || !vt(e))) {
      this.loading = !0, this.errorMessage = "";
      try {
        this.applySession(await E(this.hass, e.session_id)), await this.refreshAvailability();
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
        this.applySession(await E(this.hass, this.session.id)), this.notice = this.t("quiz.reloaded");
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
      this.feedback = await Ui(
        this.hass,
        this.session.id,
        t.question_id,
        i
      ), this.pendingAnswer = i;
    } catch (a) {
      await this.recover(a);
    } finally {
      this.loading = !1;
    }
  }
  async submitDirect(e) {
    const t = this.session?.current_question;
    if (this.hass === void 0 || this.session === void 0 || t === null || t === void 0) return;
    const i = this.enrichAnswer(e), a = this.session;
    this.retryRequest = {
      session: a,
      questionId: t.question_id,
      answer: i
    }, this.loading = !0, this.errorMessage = "", this.beginSubmissionWatch();
    try {
      const o = await de(
        this.hass,
        a,
        t.question_id,
        i
      );
      this.feedback = o.feedback, this.pendingAnswer = void 0, this.pendingSession = o.session, this.retryRequest = void 0;
    } catch (o) {
      await this.recover(o);
    } finally {
      this.loading = !1, this.endSubmissionWatch();
    }
  }
  async submitProvisional() {
    const e = this.session?.current_question;
    if (this.hass === void 0 || this.session === void 0 || e === null || e === void 0 || this.pendingAnswer === void 0) return;
    const t = this.session, i = this.pendingAnswer;
    this.retryRequest = {
      session: t,
      questionId: e.question_id,
      answer: i
    }, this.loading = !0, this.errorMessage = "", this.beginSubmissionWatch();
    try {
      const a = await de(
        this.hass,
        t,
        e.question_id,
        i
      );
      if (this.feedback?.result === "correct") {
        await this.advanceSession(a.session);
        return;
      }
      this.feedback = a.feedback, this.pendingSession = a.session;
    } catch (a) {
      await this.recover(a);
    } finally {
      this.loading = !1, this.endSubmissionWatch();
    }
  }
  async advanceSession(e) {
    let t = e;
    this.hass !== void 0 && t.status === "active" && t.current_question === null && t.question_count > 0 && (t = await Et(this.hass, t)), this.applySession(t), await this.refreshAvailability();
  }
  async startLearningAfterCalibration() {
    if (!(this.hass === void 0 || this.profile === void 0 || this.session?.track_id === null || this.session?.track_id === void 0)) {
      this.loading = !0, this.errorMessage = "";
      try {
        const e = await Rt(
          this.hass,
          this.profile.profile_id,
          this.session.track_id,
          this.session.id
        );
        this.dispatchEvent(new CustomEvent("locklearn-open-session", {
          detail: { session: e },
          bubbles: !0,
          composed: !0
        }));
      } catch (e) {
        this.errorMessage = e instanceof Error ? e.message : String(e);
      } finally {
        this.loading = !1;
      }
    }
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
    if (!(this.hass === void 0 || this.profile === void 0 || this.session === void 0 || this.session.track_id === null || e === null || e === void 0 || this.feedback === void 0 || this.pendingAnswer === void 0 || !yt(this.feedback))) {
      this.loading = !0, this.errorMessage = "";
      try {
        if ((await Fi(
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
        }, a = await de(
          this.hass,
          this.session,
          e.question_id,
          i
        );
        await this.advanceSession(a.session), this.notice = this.t("quiz.reportAccepted");
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
        await Ht(
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
  blockerFilter(e) {
    return e === "known_already_verification" ? "known_pending" : e === "suspended" ? "suspended" : e === "buried" ? "buried" : e === "prerequisite" ? "prerequisite_support" : "current_waiting_context";
  }
  openConcerned(e = "current_waiting_context") {
    this.concernedFilter = e;
  }
  closeConcerned() {
    this.concernedFilter = void 0;
  }
  renderReminderButton() {
    return this.availability?.available_now !== 0 || this.availability.next_available_at_utc === null ? l : this.hasNotificationTarget ? this.reminder?.active ? r`<button @click=${() => {
      this.cancelReminder();
    }} ?disabled=${this.loading}>${this.t("quiz.cancelReminder")}</button>` : r`<button @click=${() => {
      this.armReminder();
    }} ?disabled=${this.loading}>${this.t("quiz.remindMe")}</button>` : r`<button @click=${() => se("settings")}>${this.t("quiz.configureNotifications")}</button>`;
  }
  render() {
    if (this.profile === void 0) return l;
    if (!bt(this.profile))
      return r`<section class="quiz-card"><p>${this.t("quiz.readOnly")}</p></section>`;
    const e = this.tracks();
    if (e.length === 0)
      return r`<section class="quiz-card"><p>${this.t("quiz.noTracks")}</p></section>`;
    const t = this.selectedTrack(), i = vt(t?.last_session), a = i && t?.last_session?.session_type === "calibration";
    return r`
      <section class="quiz-shell">
        <div class="toolbar">
          <div class="toolbar-fields">
            <label>
              <span>${this.t("quiz.track")}</span>
              <select .value=${this.trackId} @change=${this.setTrack} ?disabled=${this.loading}>
                ${e.map(
      (o) => r`
                    <option value=${o.track_id}>
                      ${o.name} · ${o.source_language} → ${o.target_language}
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
            ${this.session === void 0 && i ? r`<button class="primary" @click=${this.resume} ?disabled=${this.loading}>
                  ${this.t(a ? "quiz.resumeCalibration" : "quiz.resume")}
                </button>` : this.session === void 0 ? r`<button class="primary" @click=${() => {
      this.start();
    }} ?disabled=${this.loading}>
                  ${this.t("quiz.start")}
                </button>` : l}
          </div>
          ${this.session === void 0 ? r`<p class="muted">
            ${i ? this.t(a ? "quiz.resumeCalibrationHelp" : "quiz.resumeHelp") : this.t("quiz.startHelp")}
          </p>` : l}
        </div>
        ${this.session === void 0 && this.availability !== void 0 ? r`
          <div class="notice availability-card" role="status">
            <strong>${this.t("quiz.howItWorks")}</strong>
            ${this.availability.available_now > 0 ? r`<div>${this.availability.available_now} ${this.t("quiz.cardsReady")}</div>` : this.availability.introduced_cards === 0 ? r`<div>${this.t("quiz.learnFirst")}</div>` : r`
                    <div>${this.t("quiz.emptyExplain")}</div>
                    <dl>
                      <dt>${this.t("quiz.startedCards")}</dt><dd>${this.availability.introduced_cards}</dd>
                      <dt>${this.t("quiz.readyCards")}</dt><dd>${this.availability.available_now}</dd>
                    </dl>
                    ${this.availability.next_available_at_utc === null ? r`<div class="muted">${this.t("quiz.noExactTime")}</div>` : r`
                          <div>
                            <strong>${this.nextQuizAvailableLabel()}:</strong>
                            ${this.dueLabel(this.availability.next_available_at_utc)}
                          </div>
                        `}
                  `}
            <div class="muted">${this.t("quiz.whyDueOnly")}</div>
            <div class="availability-actions">
            ${this.availability.blockers.length > 0 ? r`<button
                  @click=${() => this.openConcerned(
      this.blockerFilter(this.availability?.blockers[0]?.code ?? "")
    )}
                  ?disabled=${this.loading}
                >${this.t("quiz.viewCards")}</button>` : l}
            ${this.readyAlternative === void 0 ? l : r`<button @click=${() => {
      this.openReadyAlternative();
    }} ?disabled=${this.loading}>
                  ${this.t("quiz.readyAlternative").replace("{track}", this.readyAlternative.trackName).replace("{mode}", this.readyAlternative.mode === "learn" ? this.t("learn.title") : this.t("quiz.title"))}
                </button>`}
            ${this.renderReminderButton()}
            </div>
          </div>
        ` : l}
        ${this.submissionSlow ? r`<div class="notice" role="status" aria-live="polite">
              <strong>${this.t("quiz.answerUnconfirmed")}</strong>
              <button @click=${() => {
      this.verifySubmission();
    }}>${this.t("quiz.verify")}</button>
              ${this.retryRequest === void 0 ? l : r`<button @click=${() => {
      this.retrySubmission();
    }}>${this.t("quiz.retryAnswer")}</button>`}
            </div>` : l}
        ${this.errorMessage ? r`<div class="error" role="alert">
              <strong>${this.t("quiz.error")}</strong>
              <div>${this.errorMessage}</div>
            </div>` : l}
        ${this.notice ? r`<div class="notice" role="status" aria-live="polite">${this.notice}</div>` : l}
        ${this.renderSession()}
        ${this.concernedFilter === void 0 ? l : r`<locklearn-concerned-cards
              .hass=${this.hass}
              .profileId=${this.profile.profile_id}
              .trackId=${this.trackId}
              .filter=${this.concernedFilter}
              .mode=${"quiz"}
              .language=${this.locale()}
              .timeZone=${this.profile.timezone}
              @locklearn-concerned-cards-close=${this.closeConcerned}
              @locklearn-concerned-cards-changed=${() => {
      this.refreshAvailability();
    }}
            ></locklearn-concerned-cards>`}
      </section>
    `;
  }
  renderSession() {
    if (this.session === void 0) return l;
    if (this.session.question_count === 0) {
      const t = this.availability?.introduced_cards ?? 0, i = this.availability?.next_available_at_utc ?? null, a = this.availability?.available_now ?? 0;
      return a > 0 ? r`
          <section class="quiz-card">
            <h2>${this.t("quiz.howItWorks")}</h2>
            <p>${this.t("quiz.readyFromEmpty").replace("{count}", String(a))}</p>
            <button class="primary" @click=${() => {
        this.start();
      }} ?disabled=${this.loading}>
              ${this.t("quiz.start")}
            </button>
          </section>
        ` : r`
        <section class="quiz-card">
          <h2>${this.t("quiz.notReadyTitle")}</h2>
          <p>
            ${t === 0 ? this.t("quiz.learnFirst") : this.t("quiz.emptyExplain")}
          </p>
          <dl>
            <dt>${this.t("quiz.startedCards")}</dt><dd>${t}</dd>
            <dt>${this.t("quiz.readyCards")}</dt><dd>${a}</dd>
          </dl>
          ${i === null ? r`<p class="muted">${this.t("quiz.noExactTime")}</p>` : r`
                <p><strong>${this.nextQuizAvailableLabel()}:</strong> ${this.dueLabel(i)}</p>
              `}
          <p class="muted">${this.t("quiz.whyDueOnly")}</p>
          ${(this.availability?.blockers.length ?? 0) > 0 ? r`<button
                @click=${() => this.openConcerned(
        this.blockerFilter(this.availability?.blockers[0]?.code ?? "")
      )}
                ?disabled=${this.loading}
              >${this.t("quiz.viewCards")}</button>` : l}
          ${this.readyAlternative === void 0 ? l : r`<button @click=${() => {
        this.openReadyAlternative();
      }} ?disabled=${this.loading}>
                ${this.t("quiz.readyAlternative").replace("{track}", this.readyAlternative.trackName).replace("{mode}", this.readyAlternative.mode === "learn" ? this.t("learn.title") : this.t("quiz.title"))}
              </button>`}
          ${this.renderReminderButton()}
        </section>
      `;
    }
    if (this.session.current_question === null || this.session.status === "completed") {
      const t = this.session.type === "calibration", i = this.session.calibration_summary;
      return r`
        <section class="quiz-card">
          <h2>${t ? this.t("quiz.calibrationCompleted") : this.t("quiz.completed")}</h2>
          <p>${t ? this.t("quiz.calibrationCompletedBody") : this.t("quiz.completedBody")}</p>
          ${t && i !== void 0 ? r`<dl>
                <dt>${this.t("quiz.calibrationKnown")}</dt><dd>${i.known}</dd>
                <dt>${this.t("quiz.calibrationNeedsLearning")}</dt><dd>${i.needs_learning}</dd>
              </dl>` : l}
          <div class="actions">
            ${t && (i?.needs_learning ?? 0) > 0 ? r`<button class="primary" @click=${() => {
        this.startLearningAfterCalibration();
      }} ?disabled=${this.loading}>
                  ${this.t("quiz.learnRemaining")}
                </button>` : l}
            ${t && (this.availability?.available_now ?? 0) > 0 ? r`<button @click=${() => {
        this.start();
      }} ?disabled=${this.loading}>
                  ${this.t("quiz.start")}
                </button>` : t ? l : r`<button class="primary" @click=${() => {
        this.start();
      }} ?disabled=${this.loading}>
                    ${this.t("quiz.newSession")}
                  </button>`}
          </div>
        </section>
      `;
    }
    const e = us(this.session.current_question);
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
    return hs(e) ? r`
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
            autocapitalize="none"
            autocorrect="off"
            spellcheck="false"
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
          ${yt(t) ? r`<button
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
    return He(e);
  }
};
je.styles = N`
    ${Ie}
    ${j}

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
      min-height: 110px;
      display: grid;
      place-items: center;
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
      min-height: 190px;
      align-content: start;
      display: grid;
      gap: 10px;
    }

    .option {
      width: 100%;
      text-align: left;
      overflow-wrap: anywhere;
    }

    .feedback {
      min-height: 190px;
      align-content: start;
    }

    .availability-card {
      display: grid;
      gap: 16px;
    }

    .availability-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      padding-top: 4px;
    }

    .feedback-title {
      margin: 0 0 6px;
      font-weight: 700;
    }

    .feedback-detail {
      margin: 6px 0 0;
    }

    .free-text-form {
      min-height: 190px;
      align-content: start;
      display: grid;
      gap: 10px;
    }

    dl {
      display: grid;
      grid-template-columns: minmax(170px, auto) 1fr;
      gap: 6px 12px;
      margin: 12px 0 0;
    }

    dt {
      color: var(--secondary-text-color);
    }

    dd {
      margin: 0;
      font-weight: 650;
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

      .prompt { min-height: 80px; }
      .options, .free-text-form, .feedback { min-height: 150px; }

      .progress {
        flex-direction: column;
        gap: 4px;
      }
    }
  `;
let b = je;
k([
  f({ attribute: !1 })
], b.prototype, "hass");
k([
  f({ attribute: !1 })
], b.prototype, "profile");
k([
  f({ attribute: !1 })
], b.prototype, "dashboard");
k([
  f({ attribute: !1 })
], b.prototype, "externalSession");
k([
  c()
], b.prototype, "trackId");
k([
  c()
], b.prototype, "format");
k([
  c()
], b.prototype, "session");
k([
  c()
], b.prototype, "loading");
k([
  c()
], b.prototype, "errorMessage");
k([
  c()
], b.prototype, "notice");
k([
  c()
], b.prototype, "feedback");
k([
  c()
], b.prototype, "pendingAnswer");
k([
  c()
], b.prototype, "pendingSession");
k([
  c()
], b.prototype, "freeText");
k([
  c()
], b.prototype, "hintUsed");
k([
  c()
], b.prototype, "availability");
k([
  c()
], b.prototype, "reminder");
k([
  c()
], b.prototype, "submissionSlow");
k([
  c()
], b.prototype, "retryRequest");
k([
  c()
], b.prototype, "concernedFilter");
k([
  c()
], b.prototype, "readyAlternative");
k([
  c()
], b.prototype, "hasNotificationTarget");
globalThis.customElements !== void 0 && customElements.get("locklearn-quiz-view") === void 0 && customElements.define("locklearn-quiz-view", b);
var ms = Object.defineProperty, S = (s, e, t, i) => {
  for (var a = void 0, o = s.length - 1, n; o >= 0; o--)
    (n = s[o]) && (a = n(e, t, a) || a);
  return a && ms(e, t, a), a;
};
const Oe = class Oe extends z {
  constructor() {
    super(...arguments), this.trackId = "", this.count = 20, this.contentTypes = [], this.direction = "any", this.packId = "", this.level = "", this.tags = "", this.shuffle = !0, this.optionCount = 4, this.history = [], this.busy = !1, this.error = "";
  }
  updated(e) {
    e.has("profile") && (this.session = void 0, this.result = void 0, this.trackId = this.dashboard?.tracks[0]?.track_id ?? "", this.history = [], this.hass && this.profile && this.loadHistory(this.profile.profile_id)), e.has("dashboard") && !this.trackId && (this.trackId = this.dashboard?.tracks[0]?.track_id ?? "");
  }
  async loadHistory(e) {
    try {
      const t = await Yi(this.hass, e);
      this.profile?.profile_id === e && (this.history = t.items);
    } catch {
    }
  }
  get fr() {
    return (this.hass?.locale?.language ?? this.hass?.language ?? "en").toLowerCase().startsWith("fr");
  }
  async perform(e) {
    if (!this.busy) {
      this.busy = !0, this.error = "";
      try {
        await e();
      } catch (t) {
        this.error = t instanceof Error ? t.message : String(t);
      } finally {
        this.busy = !1;
      }
    }
  }
  begin() {
    this.perform(async () => {
      !this.hass || !this.profile || !this.trackId || (this.session = await Ki(this.hass, this.profile.profile_id, this.trackId, {
        requestedCards: this.count,
        contentTypes: this.contentTypes.length ? this.contentTypes : void 0,
        direction: this.direction,
        packId: this.packId.trim() || void 0,
        levels: this.level.trim() ? [this.level.trim()] : void 0,
        tags: this.tags.split(",").map((e) => e.trim()).filter(Boolean),
        shuffle: this.shuffle,
        optionCount: this.optionCount
      }), this.result = void 0, await this.loadHistory(this.profile.profile_id));
    });
  }
  pause() {
    this.perform(async () => {
      !this.hass || !this.session || this.session.status !== "active" || (this.session = await Zi(this.hass, this.session, !0));
    });
  }
  resume() {
    this.perform(async () => {
      const e = this.dashboard?.tracks.find((t) => t.track_id === this.trackId)?.last_session;
      !this.hass || e?.session_type !== "exam" || (this.session = await E(this.hass, e.session_id), this.session.status === "completed" && (this.result = await ht(this.hass, this.session.id)));
    });
  }
  resumePaused() {
    this.perform(async () => {
      !this.hass || !this.session || this.session.status !== "paused" || (this.session = await this.hass.callWS({
        type: "locklearn/session/pause",
        session_id: this.session.id,
        expected_version: this.session.version,
        paused: !1
      }));
    });
  }
  openHistory(e) {
    this.perform(async () => {
      if (!this.hass) return;
      const t = await E(this.hass, e.attempt_id);
      this.session = t, this.result = e.status === "completed" ? await ht(this.hass, e.attempt_id) : void 0, t.track_id && (this.trackId = t.track_id);
    });
  }
  answer(e) {
    this.perform(async () => {
      !this.hass || !this.session?.current_question || (this.session = await Gi(
        this.hass,
        this.session,
        this.session.current_question.question_id,
        e
      ));
    });
  }
  finish() {
    this.perform(async () => {
      if (!this.hass || !this.session) return;
      const e = await Qi(this.hass, this.session);
      this.session = e.session, this.result = e.result, await this.loadHistory(this.profile?.profile_id ?? "");
    });
  }
  render() {
    if (!this.profile) return r`<section>${this.fr ? "Aucun profil disponible." : "No profile available."}</section>`;
    const e = this.dashboard?.tracks ?? [], t = e.find((n) => n.track_id === this.trackId)?.last_session, i = t?.session_type === "exam" && (t.status === "active" || t.status === "paused" || t.status === "completed"), a = this.session?.current_question, o = a?.payload.quiz;
    return r`<section>
      <h1>${this.fr ? "Examen" : "Exam"}</h1>
      <p class="muted">${this.fr ? "Les réponses sont définitives. Le corrigé et le score apparaissent uniquement à la fin. Aucun changement direct des boxes SRS." : "Answers are final. Corrections and score appear only at the end. No direct SRS box promotion."}</p>
      ${this.session ? this.result ? r`
        <h2>${this.result.correct} / ${this.result.total} — ${this.result.percentage}%</h2>
        <h3>${this.fr ? "Revoir mes erreurs" : "Review mistakes"}</h3>
        ${this.result.questions.filter((n) => n.result !== "correct").map((n) => r`
          <div class="weak">
            <p><strong>${n.prompt}</strong></p>
            <p>${this.fr ? "Votre réponse" : "Your answer"}: ${n.given ?? (this.fr ? "Je ne sais pas" : "I don't know")}</p>
            <p>${this.fr ? "Bonne réponse" : "Correct answer"}: ${n.correct}</p>
            ${n.context ? r`<p class="muted">${n.context}</p>` : l}
          </div>
        `)}
        <button @click=${() => {
      this.session = void 0, this.result = void 0;
    }}>${this.fr ? "Retour" : "Back"}</button>
      ` : this.session.status === "paused" ? r`
        <p>${this.fr ? "Examen en pause." : "Exam paused."}</p>
        <button @click=${this.resumePaused} ?disabled=${this.busy}>${this.fr ? "Reprendre" : "Resume"}</button>
    ` : a && o ? r`
        <p>${this.fr, "Question"} ${a.position + 1} / ${this.session.question_count}</p>
        <div class="prompt">${o.prompt_text}</div>
        <div class="choices">
          ${o.options.map((n) => r`<button ?disabled=${this.busy || this.profile?.role === "viewer"}
            @click=${() => this.answer(n.answer_id)}>${n.text}</button>`)}
          <button ?disabled=${this.busy || this.profile?.role === "viewer"}
            @click=${() => this.answer(null)}>${this.fr ? "Je ne sais pas" : "I don't know"}</button>
        </div>
        <p class="muted">${this.fr ? "Pas de correction avant la fin." : "No correction until the end."}</p>
        <button @click=${this.pause} ?disabled=${this.busy}>${this.fr ? "Mettre en pause" : "Pause exam"}</button>
      ` : r`
        <p>${this.fr ? "Toutes les réponses sont enregistrées." : "All answers have been recorded."}</p>
        <button @click=${this.finish} ?disabled=${this.busy || this.session?.status !== "active"}>
          ${this.fr ? "Terminer et voir le score" : "Finish and see score"}
        </button>
      ` : r`
        <label>${this.fr ? "Parcours" : "Track"}
          <select .value=${this.trackId} @change=${(n) => {
      this.trackId = n.target.value;
    }}>
            ${e.map((n) => r`<option value=${n.track_id}>${n.name}</option>`)}
          </select>
        </label>
        <label>${this.fr ? "Nombre de questions" : "Number of questions"}
          <select .value=${String(this.count)} @change=${(n) => {
      this.count = Number(n.target.value);
    }}>
            ${[10, 20, 30, 40].map((n) => r`<option value=${n}>${n}</option>`)}
          </select>
        </label>
        <fieldset>
          <legend>${this.fr ? "Types de contenu" : "Content types"}</legend>
          ${["vocabulary", "kanji", "grammar", "expression", "sentence"].map((n) => r`
            <label><input type="checkbox" .checked=${this.contentTypes.includes(n)}
              @change=${(u) => {
      const d = u.target.checked;
      this.contentTypes = d ? [...this.contentTypes, n] : this.contentTypes.filter((h) => h !== n);
    }} /> ${n}</label>
          `)}
        </fieldset>
        <label>${this.fr, "Direction"}
          <select .value=${this.direction} @change=${(n) => {
      this.direction = n.target.value;
    }}>
            <option value="any">${this.fr ? "Les deux" : "Any"}</option>
            <option value="forward">${this.fr ? "Source → cible" : "Source → target"}</option>
            <option value="reverse">${this.fr ? "Cible → source" : "Target → source"}</option>
          </select>
        </label>
        <label>${this.fr ? "Pack (identifiant, optionnel)" : "Pack (optional id)"}
          <input .value=${this.packId} @input=${(n) => {
      this.packId = n.target.value;
    }} />
        </label>
        <label>${this.fr ? "Niveau (tag level, optionnel)" : "Level (optional level tag)"}
          <input .value=${this.level} @input=${(n) => {
      this.level = n.target.value;
    }} />
        </label>
        <label>${this.fr ? "Tags (séparés par des virgules)" : "Tags (comma-separated)"}
          <input .value=${this.tags} @input=${(n) => {
      this.tags = n.target.value;
    }} />
        </label>
        <label><input type="checkbox" .checked=${this.shuffle}
          @change=${(n) => {
      this.shuffle = n.target.checked;
    }} />
          ${this.fr ? "Mélanger les questions" : "Shuffle questions"}</label>
        <label>${this.fr ? "Nombre d'options par QCM" : "Options per MCQ"}
          <select .value=${String(this.optionCount)} @change=${(n) => {
      this.optionCount = Number(n.target.value);
    }}>
            ${[2, 3, 4, 5, 6].map((n) => r`<option value=${n}>${n}</option>`)}
          </select>
        </label>
        ${this.profile.role === "viewer" ? l : r`
          <button @click=${this.begin} ?disabled=${this.busy || !this.trackId}>${this.fr ? "Commencer l'examen" : "Start exam"}</button>
        `}
        ${i ? r`<button @click=${this.resume} ?disabled=${this.busy}>${this.fr ? "Reprendre / consulter" : "Resume / review"}</button>` : l}
        ${this.history.length ? r`
          <h2>${this.fr ? "Examens précédents" : "Previous exams"}</h2>
          ${this.history.map((n) => r`<button class="history" @click=${() => this.openHistory(n)}>
            ${new Date(n.started_at_utc).toLocaleString()} —
            ${n.status === "completed" ? `${n.correct_count}/${n.question_count}` : n.status}
          </button>`)}
        ` : l}
      `}
      ${this.error ? r`<p class="error" role="alert">${this.error}</p>` : l}
    </section>`;
  }
};
Oe.styles = N`
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
let w = Oe;
S([
  f({ attribute: !1 })
], w.prototype, "hass");
S([
  f({ attribute: !1 })
], w.prototype, "profile");
S([
  f({ attribute: !1 })
], w.prototype, "dashboard");
S([
  c()
], w.prototype, "trackId");
S([
  c()
], w.prototype, "count");
S([
  c()
], w.prototype, "contentTypes");
S([
  c()
], w.prototype, "direction");
S([
  c()
], w.prototype, "packId");
S([
  c()
], w.prototype, "level");
S([
  c()
], w.prototype, "tags");
S([
  c()
], w.prototype, "shuffle");
S([
  c()
], w.prototype, "optionCount");
S([
  c()
], w.prototype, "session");
S([
  c()
], w.prototype, "result");
S([
  c()
], w.prototype, "history");
S([
  c()
], w.prototype, "busy");
S([
  c()
], w.prototype, "error");
customElements.define("locklearn-exam-view", w);
const gs = (s) => (...e) => ({ _$litDirective$: s, values: e });
let fs = class {
  constructor(e) {
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AT(e, t, i) {
    this._$Ct = e, this._$AM = t, this._$Ci = i;
  }
  _$AS(e, t) {
    return this.update(e, t);
  }
  update(e, t) {
    return this.render(...t);
  }
};
const vs = {}, bs = (s, e = vs) => s._$AH = e;
const ue = gs(class extends fs {
  constructor() {
    super(...arguments), this.key = l;
  }
  render(s, e) {
    return this.key = s, e;
  }
  update(s, [e, t]) {
    return e !== this.key && (bs(s), this.key = e), t;
  }
});
var ys = Object.defineProperty, y = (s, e, t, i) => {
  for (var a = void 0, o = s.length - 1, n; o >= 0; o--)
    (n = s[o]) && (a = n(e, t, a) || a);
  return a && ys(e, t, a), a;
};
function R(s, e, t) {
  const i = Number.parseInt(String(s ?? ""), 10);
  return Number.isFinite(i) && i >= t ? i : e;
}
function qe(s, e) {
  const t = String(s ?? "").trim();
  if (t === "") return null;
  const i = Number.parseInt(t, 10);
  return Number.isFinite(i) && i >= e ? i : null;
}
function V(s, e, t, i) {
  const a = Number.parseFloat(String(s ?? ""));
  return Number.isFinite(a) && a >= t && a <= i ? a : e;
}
function te(s) {
  if (s instanceof Error && s.message) return s.message;
  if (typeof s == "string") return s;
  if (typeof s == "object" && s !== null) {
    const e = s;
    if (typeof e.message == "string" && e.message) return e.message;
    if (typeof e.code == "string" && e.code) return e.code;
    try {
      return JSON.stringify(e);
    } catch {
      return "Unknown error";
    }
  }
  return String(s);
}
function B(s, e) {
  if (s === "ja-Latn")
    return e === "fr" ? "Japonais (rōmaji)" : "Japanese (romaji)";
  try {
    const t = s.split("-", 1)[0] ?? s;
    return new Intl.DisplayNames([e], { type: "language" }).of(t) ?? s;
  } catch {
    return s;
  }
}
function K(s, e) {
  const t = s?.[e];
  return typeof t == "object" && t !== null ? t : {};
}
function $s(s) {
  return s === "owner";
}
function ks(s) {
  return s === "owner" || s === "editor";
}
const We = class We extends z {
  constructor() {
    super(...arguments), this.route = "profiles", this.tracks = [], this.packs = [], this.notificationTargets = [], this.notificationCandidates = [], this.members = [], this.shareTargets = [], this.createTrackPackId = "", this.createTrackSource = "", this.forecasts = {}, this.forecastPlans = {}, this.packDiffTrack = "", this.packDiffTarget = "", this.loading = !1, this.errorMessage = "", this.notice = "", this.dirtyScopes = /* @__PURE__ */ new Set(), this.formResetVersions = {}, this.saveFeedback = {};
  }
  updated(e) {
    (e.has("profile") || e.has("route")) && this.load();
  }
  locale() {
    return Z(
      this.hass?.locale?.language ?? this.hass?.language ?? globalThis.navigator?.language ?? "en"
    );
  }
  t(e) {
    return O(this.locale(), e);
  }
  isOwner() {
    return $s(this.profile?.role);
  }
  canEditTrack() {
    return ks(this.profile?.role);
  }
  async load() {
    if (this.hass !== void 0) {
      if (this.profile === void 0) {
        this.tracks = [], this.packs = [], this.notificationTargets = [], this.notificationCandidates = [], this.members = [], this.shareTargets = [];
        return;
      }
      this.loading = !0, this.errorMessage = "";
      try {
        [this.tracks, this.packs] = await Promise.all([
          Ct(this.hass, this.profile.profile_id),
          Pi(this.hass)
        ]), this.notificationTargets = this.canEditTrack() ? await Ue(this.hass, this.profile.profile_id) : [], this.notificationCandidates = this.isOwner() && this.route === "settings" ? await wi(this.hass, this.profile.profile_id) : [], this.packs.some((e) => e.pack_version_id === this.createTrackPackId) || (this.createTrackPackId = this.packs[0]?.pack_version_id ?? "", this.createTrackSource = ""), this.isOwner() && this.route === "profiles" ? [this.members, this.shareTargets] = await Promise.all([
          yi(this.hass, this.profile.profile_id),
          $i(this.hass, this.profile.profile_id)
        ]) : (this.members = [], this.shareTargets = []);
      } catch (e) {
        this.errorMessage = te(e);
      } finally {
        this.loading = !1;
      }
    }
  }
  scopeKey(e, t) {
    return `${e}:${t}`;
  }
  profileSettingsScope() {
    return `settings:${this.profile?.profile_id ?? "none"}`;
  }
  targetScope(e) {
    return `target:${e}`;
  }
  isScopeDirty(e) {
    return this.dirtyScopes.has(e);
  }
  clearSaveFeedback(e) {
    if (this.saveFeedback[e] === void 0) return;
    const t = { ...this.saveFeedback };
    delete t[e], this.saveFeedback = t;
  }
  markScopeDirty(e) {
    if (this.clearSaveFeedback(e), this.dirtyScopes.has(e)) return;
    const t = new Set(this.dirtyScopes);
    t.add(e), this.dirtyScopes = t, this.emitDirtyState();
  }
  clearScopeDirty(e) {
    if (!this.dirtyScopes.has(e)) return;
    const t = new Set(this.dirtyScopes);
    t.delete(e), this.dirtyScopes = t, this.emitDirtyState();
  }
  scopeFeedbackText(e) {
    const t = this.locale() === "fr";
    return this.submittingScope === e ? t ? "Enregistrement…" : "Saving…" : this.saveFeedback[e] === "error" ? t ? "Échec de l’enregistrement" : "Save failed" : this.isScopeDirty(e) ? t ? "Modifications non enregistrées" : "Unsaved changes" : this.saveFeedback[e] === "saved" ? t ? "Enregistré ✓" : "Saved ✓" : this.t("form.pristine");
  }
  emitDirtyState() {
    this.dispatchEvent(
      new CustomEvent("locklearn-dirty-state-changed", {
        detail: { dirty: this.dirtyScopes.size > 0 },
        bubbles: !0,
        composed: !0
      })
    );
  }
  resetScope(e) {
    this.formResetVersions = {
      ...this.formResetVersions,
      [e]: (this.formResetVersions[e] ?? 0) + 1
    };
  }
  cancelScope(e) {
    this.resetScope(e), this.clearScopeDirty(e), this.clearSaveFeedback(e), this.requestUpdate();
  }
  validateScope(e) {
    if (e.checkValidity()) return !0;
    const t = e.querySelector(":invalid"), i = t?.closest("details");
    return i instanceof HTMLDetailsElement && (i.open = !0), t?.focus(), e.reportValidity(), !1;
  }
  async mutateScope(e, t, i) {
    this.clearSaveFeedback(e), this.submittingScope = e, this.loading = !0, this.errorMessage = "";
    try {
      await t(), this.clearScopeDirty(e), this.saveFeedback = { ...this.saveFeedback, [e]: "saved" }, await this.load(), this.notice = i, this.dispatchEvent(new CustomEvent("locklearn-refresh", { bubbles: !0, composed: !0 }));
    } catch (a) {
      this.saveFeedback = { ...this.saveFeedback, [e]: "error" }, this.errorMessage = te(a);
    } finally {
      this.loading = !1, this.submittingScope = void 0;
    }
  }
  async saveTrackDetails(e, t) {
    if (this.hass === void 0 || !this.validateScope(t)) return !1;
    const i = new FormData(t), a = K(e.settings, "scheduler"), o = e.content_weights ?? {}, n = i.getAll("notificationTarget").map(String), u = {
      vocabulary: V(i.get("weightVocabulary"), Number(o.vocabulary ?? 1), 0, 100),
      kanji: V(i.get("weightKanji"), Number(o.kanji ?? 1), 0, 100),
      grammar: V(i.get("weightGrammar"), Number(o.grammar ?? 1), 0, 100),
      expression: V(i.get("weightExpression"), Number(o.expression ?? 1), 0, 100)
    }, d = this.scopeKey(e.track_id, "details");
    return await this.mutateScope(
      d,
      () => zi(this.hass, e.track_id, {
        name: String(i.get("name") ?? e.name),
        source_language: String(i.get("source") ?? e.source_language ?? "").trim(),
        target_language: String(i.get("target") ?? e.target_language ?? "").trim(),
        status: String(i.get("status") ?? e.status),
        priority: R(i.get("priority"), e.priority, 1),
        content_weights: u,
        scheduler_settings: {
          learning_count: R(i.get("learningCount"), Number(a.learning_count ?? 0), 0),
          quiz_count: R(i.get("quizCount"), Number(a.quiz_count ?? 0), 0),
          ...n.length === 0 ? {} : { target_ids: n }
        }
      }),
      this.t("manage.saved")
    ), !this.isScopeDirty(d);
  }
  async savePlanScope(e, t) {
    if (this.hass === void 0 || !this.validateScope(t)) return !1;
    const i = this.scopeKey(e.track_id, "plan"), a = this.planFrom(t);
    return await this.mutateScope(
      i,
      () => ut(this.hass, e.track_id, a),
      this.t("manage.saved")
    ), !this.isScopeDirty(i);
  }
  async saveProfileSettings(e) {
    if (this.hass === void 0 || this.profile === void 0 || !this.validateScope(e)) return !1;
    const t = this.profileSettingsScope(), i = new FormData(e), a = this.profile.settings ?? {}, o = K(a, "scheduler");
    return await this.mutateScope(
      t,
      () => ot(this.hass, this.profile.profile_id, {
        settings_patch: {
          session_length_cards: R(i.get("session"), 20, 1),
          max_new_per_day_cards: R(i.get("new"), 8, 0),
          daily_push_budget: R(i.get("push"), 6, 0),
          quiet_hours: {
            start: String(i.get("quietStart") ?? "22:00"),
            end: String(i.get("quietEnd") ?? "08:00")
          },
          scheduler: {
            ...o,
            active_windows: [{
              start: String(i.get("activeStart") ?? "08:00"),
              end: String(i.get("activeEnd") ?? "20:00")
            }]
          }
        }
      }),
      this.t("manage.saved")
    ), !this.isScopeDirty(t);
  }
  async saveNotificationTarget(e, t) {
    if (this.hass === void 0 || this.profile === void 0 || !this.validateScope(t)) return !1;
    const i = this.targetScope(e.target_id), a = new FormData(t);
    return await this.mutateScope(
      i,
      () => xi(
        this.hass,
        this.profile.profile_id,
        e.target_id,
        {
          friendly_name: String(a.get("friendlyName") ?? "").trim(),
          shared_device: a.get("sharedDevice") === "on",
          lockscreen_visibility: String(
            a.get("lockscreenVisibility") ?? "private"
          ),
          enabled: a.get("enabled") === "on",
          minimum_gap_seconds: qe(a.get("minimumGap"), 0),
          maximum_notifications_per_hour: qe(a.get("maxPerHour"), 1),
          daily_push_budget: qe(a.get("targetBudget"), 0)
        }
      ),
      this.t("manage.notificationTargetUpdated")
    ), !this.isScopeDirty(i);
  }
  async saveDirtyScopes() {
    const e = [...this.dirtyScopes];
    for (const t of e) {
      const i = this.renderRoot.querySelector(
        `form[data-save-scope="${t}"]`
      );
      if (i === null) return !1;
      if (t.startsWith("settings:")) {
        if (!await this.saveProfileSettings(i)) return !1;
        continue;
      }
      if (t.startsWith("target:")) {
        const h = t.slice(7), $ = this.notificationTargets.find((m) => m.target_id === h);
        if ($ === void 0 || !await this.saveNotificationTarget($, i)) return !1;
        continue;
      }
      const a = t.lastIndexOf(":");
      if (a < 1) continue;
      const o = t.slice(0, a), n = t.slice(a + 1), u = this.tracks.find((h) => h.track_id === o);
      if (u === void 0 || !(n === "details" ? await this.saveTrackDetails(u, i) : n === "plan" ? await this.savePlanScope(u, i) : !1)) return !1;
    }
    return this.dirtyScopes.size === 0;
  }
  discardDirtyScopes() {
    for (const e of [...this.dirtyScopes])
      this.resetScope(e);
    this.dirtyScopes = /* @__PURE__ */ new Set(), this.forecasts = {}, this.forecastPlans = {}, this.saveFeedback = {}, this.emitDirtyState(), this.requestUpdate();
  }
  async mutate(e, t) {
    this.loading = !0, this.errorMessage = "";
    try {
      await e(), await this.load(), this.notice = t, this.dispatchEvent(new CustomEvent("locklearn-refresh", { bubbles: !0, composed: !0 }));
    } catch (i) {
      this.errorMessage = te(i);
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
        () => ot(this.hass, this.profile.profile_id, {
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
          <button type="button" @click=${() => this.archiveProfile()}>${this.t("manage.archiveProfile")}</button>
          <button type="button" @click=${() => this.deleteProfilePermanently()}>${this.t("manage.deletePermanently")}</button>
        </div>
      </form>
    `;
  }
  renderSharing() {
    const e = new Set(this.members.map((a) => a.ha_user_id)), t = this.shareTargets.filter((a) => !e.has(a.ha_user_id)), i = this.members.filter((a) => a.role === "owner").length;
    return r`
      <article class="card">
        <h2>${this.t("manage.sharing")}</h2>
        <p class="muted">${this.t("manage.sharingHelp")}</p>
        ${this.members.length === 0 ? r`<p>${this.t("manage.none")}</p>` : r`
          <ul>${this.members.map((a) => r`<li>
            ${a.name}
            <select
              aria-label=${this.t("manage.role")}
              .value=${a.role}
              ?disabled=${a.role === "owner" && i === 1}
              @change=${(o) => {
      const n = o.currentTarget;
      n instanceof HTMLSelectElement && this.changeMemberRole(a.ha_user_id, n.value);
    }}
            >
              <option value="viewer">viewer</option>
              <option value="editor">editor</option>
              <option value="owner">owner</option>
            </select>
            ${a.role === "owner" && i === 1 ? l : r`
              <button @click=${() => this.removeMember(a.ha_user_id)}>${this.t("manage.remove")}</button>`}
          </li>`)}</ul>`}
        ${t.length === 0 ? l : r`
          <form class="form-grid" @submit=${(a) => {
      a.preventDefault();
      const o = new FormData(a.currentTarget);
      this.addMember(
        String(o.get("user") ?? ""),
        String(o.get("role") ?? "viewer")
      );
    }}>
            <label>${this.t("manage.user")}<select name="user">
              ${t.map((a) => r`<option value=${a.ha_user_id}>${a.name}</option>`)}
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
    !e || this.hass === void 0 || this.profile === void 0 || await this.mutate(() => ct(this.hass, this.profile.profile_id, e, t), this.t("manage.saved"));
  }
  async removeMember(e) {
    this.hass === void 0 || this.profile === void 0 || globalThis.confirm?.(this.t("manage.confirmRemoveMember")) && await this.mutate(() => ki(this.hass, this.profile.profile_id, e), this.t("manage.saved"));
  }
  async changeMemberRole(e, t) {
    this.hass === void 0 || this.profile === void 0 || await this.mutate(
      () => ct(this.hass, this.profile.profile_id, e, t),
      this.t("manage.saved")
    );
  }
  async archiveProfile() {
    this.hass === void 0 || this.profile === void 0 || globalThis.confirm?.(this.t("manage.confirmArchiveProfile")) && await this.mutate(
      () => lt(this.hass, this.profile.profile_id, "archive"),
      this.t("manage.archivedNotice")
    );
  }
  async deleteProfilePermanently() {
    if (this.hass === void 0 || this.profile === void 0) return;
    const e = `DELETE ${this.profile.profile_id}`, t = globalThis.prompt?.(
      `${this.t("manage.confirmDeletePermanently")} ${e}`
    );
    t === e && await this.mutate(
      () => lt(
        this.hass,
        this.profile.profile_id,
        "delete_permanently",
        t
      ),
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
        () => bi(
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
  packDirections(e) {
    return this.packs.find((t) => t.pack_version_id === e)?.directions ?? [];
  }
  sourceLanguages(e) {
    return [...new Set(
      this.packDirections(e).map((t) => t.source_language)
    )].sort((t, i) => t.localeCompare(i));
  }
  targetLanguages(e, t) {
    return [...new Set(
      this.packDirections(e).filter((i) => i.source_language === t).map((i) => i.target_language)
    )].sort((i, a) => i.localeCompare(a));
  }
  renderTrack(e) {
    const t = K(e.settings, "scheduler"), i = Array.isArray(t.target_ids) ? t.target_ids.map(String) : [], a = e.content_weights ?? {}, o = this.scopeKey(e.track_id, "details"), n = B(e.source_language ?? "", this.locale()), u = B(e.target_language ?? "", this.locale());
    return r`
      <article class="card">
        <div class="track-summary">
          <h2>${e.name}</h2>
          <p class="meta">${n} → ${u} · ${e.status === "active" ? this.t("manage.active") : e.status === "paused" ? this.t("manage.paused") : this.t("manage.archived")}</p>
          <p class="meta">${this.t("manage.packVersion")}: ${e.pack_version_id ?? "—"}</p>
        </div>
        ${this.canEditTrack() ? r`
          ${ue(`${o}:${this.formResetVersions[o] ?? 0}`, r`<form
            class="track-form"
            data-save-scope=${o}
            @input=${() => this.markScopeDirty(o)}
            @change=${() => this.markScopeDirty(o)}
            @submit=${(d) => {
      d.preventDefault(), this.saveTrackDetails(e, d.currentTarget);
    }}>
            <div class="form-grid">
              <label>${this.t("manage.name")}<input name="name" .value=${e.name} /></label>
              <label>${this.t("manage.status")}
                <select name="status" .value=${e.status}>
                  <option value="active">${this.t("manage.active")}</option>
                  <option value="paused">${this.t("manage.paused")}</option>
                  <option value="archived">${this.t("manage.archived")}</option>
                </select>
              </label>
              <label>${this.t("manage.sourceLanguage")}
                <select name="source" .value=${e.source_language ?? ""} required>
                  ${this.sourceLanguages(e.pack_version_id ?? "").map((d) => r`
                    <option value=${d}>${B(d, this.locale())}</option>
                  `)}
                </select>
              </label>
              <label>${this.t("manage.targetLanguage")}
                <select name="target" .value=${e.target_language ?? ""} required>
                  ${this.targetLanguages(
      e.pack_version_id ?? "",
      e.source_language ?? ""
    ).map((d) => r`
                    <option value=${d}>${B(d, this.locale())}</option>
                  `)}
                </select>
              </label>
            </div>

            <details class="section-panel">
              <summary>${this.t("manage.advancedTrackSettings")}</summary>
              <div class="section-body">
                <p class="muted">${this.t("manage.advancedTrackSettingsHelp")}</p>
                <div class="form-grid">
                  <label>${this.t("manage.priority")}<input name="priority" type="number" min="1" .value=${String(e.priority)} /></label>
                  <label>${this.t("manage.weightVocabulary")}<input name="weightVocabulary" type="number" min="0" step=".1" .value=${String(a.vocabulary ?? 1)} /></label>
                  <label>${this.t("manage.weightKanji")}<input name="weightKanji" type="number" min="0" step=".1" .value=${String(a.kanji ?? 1)} /></label>
                  <label>${this.t("manage.weightGrammar")}<input name="weightGrammar" type="number" min="0" step=".1" .value=${String(a.grammar ?? 1)} /></label>
                  <label>${this.t("manage.weightExpression")}<input name="weightExpression" type="number" min="0" step=".1" .value=${String(a.expression ?? 1)} /></label>
                  <label>${this.t("manage.learningNotifications")}<input name="learningCount" type="number" min="0" .value=${String(t.learning_count ?? 0)} /></label>
                  <label>${this.t("manage.quizNotifications")}<input name="quizCount" type="number" min="0" .value=${String(t.quiz_count ?? 0)} /></label>
                  <label>${this.t("manage.notificationTargets")}
                    <select name="notificationTarget" multiple size=${Math.min(4, Math.max(2, this.notificationTargets.length))}>
                      ${this.notificationTargets.map((d) => r`
                        <option value=${d.target_id} ?selected=${i.includes(d.target_id)}>
                          ${d.friendly_name} · ${d.platform}
                        </option>`)}
                    </select>
                    <span class="meta">${this.notificationTargets.length === 0 ? this.t("manage.noNotificationTargets") : this.t("manage.notificationTargetsHelp")}</span>
                  </label>
                </div>
              </div>
            </details>

            <p class="scope-state ${this.saveFeedback[o] === "error" ? "is-error" : ""}" role="status">
              ${this.scopeFeedbackText(o)}
            </p>
            <div class="scope-actions ${this.isScopeDirty(o) ? "is-dirty" : ""}">
              <button
                class="primary"
                type="submit"
                ?disabled=${!this.isScopeDirty(o) || this.submittingScope === o}
              >
                ${this.submittingScope === o ? this.t("form.saving") : this.t("form.save")}
              </button>
              <button
                type="button"
                ?disabled=${!this.isScopeDirty(o) || this.submittingScope === o}
                @click=${() => this.cancelScope(o)}
              >
                ${this.t("form.cancel")}
              </button>
            </div>
          </form>`)}

          <details class="section-panel">
            <summary>${this.t("manage.plan")}</summary>
            <div class="section-body">${this.renderPlan(e)}</div>
          </details>

          <div class="danger-zone">
            <strong>${this.t("manage.dangerZone")}</strong>
            <p class="muted">${this.t("manage.deleteTrackHelp")}</p>
            <button type="button" @click=${() => this.removeTrack(e.track_id, e.name)}>
              ${this.t("manage.deleteTrack")}
            </button>
          </div>
        ` : l}
      </article>
    `;
  }
  renderCreateTrack() {
    const e = this.createTrackPackId || this.packs[0]?.pack_version_id || "", t = this.sourceLanguages(e), i = t.includes(this.createTrackSource) ? this.createTrackSource : t[0] ?? "", a = this.targetLanguages(e, i);
    return r`
      <article class="card">
        <h2>${this.t("manage.createTrack")}</h2>
        ${this.packs.length === 0 ? r`<p>${this.t("manage.noPacks")}</p>` : r`
          <form class="form-grid" @submit=${(o) => {
      o.preventDefault();
      const n = new FormData(o.currentTarget);
      this.hass === void 0 || this.profile === void 0 || this.mutate(() => Ai(this.hass, {
        profile_id: this.profile.profile_id,
        name: String(n.get("name") ?? "").trim(),
        pack_version_id: String(n.get("pack") ?? ""),
        source_language: String(n.get("source") ?? "").trim(),
        target_language: String(n.get("target") ?? "").trim(),
        priority: R(n.get("priority"), 1, 1)
      }), this.t("manage.created"));
    }}>
            <label>${this.t("manage.name")}<input name="name" required /></label>
            <label>${this.t("manage.pack")}
              <select
                name="pack"
                .value=${e}
                @change=${(o) => {
      const n = o.currentTarget;
      n instanceof HTMLSelectElement && (this.createTrackPackId = n.value, this.createTrackSource = "");
    }}
              >
                ${this.packs.map((o) => r`
                  <option value=${o.pack_version_id}>${o.name} · ${o.version}</option>
                `)}
              </select>
            </label>
            ${t.length === 0 ? r`
              <p class="warning">${this.t("manage.noPackDirections")}</p>
            ` : r`
              <label>${this.t("manage.sourceLanguage")}
                <select
                  name="source"
                  .value=${i}
                  required
                  @change=${(o) => {
      const n = o.currentTarget;
      n instanceof HTMLSelectElement && (this.createTrackSource = n.value);
    }}
                >
                  ${t.map((o) => r`
                    <option value=${o}>${B(o, this.locale())}</option>
                  `)}
                </select>
              </label>
              <label>${this.t("manage.targetLanguage")}
                <select name="target" required>
                  ${a.map((o) => r`
                    <option value=${o}>${B(o, this.locale())}</option>
                  `)}
                </select>
              </label>
            `}
            <label>${this.t("manage.priority")}<input name="priority" type="number" min="1" value="1" /></label>
            <div class="actions">
              <button class="primary" type="submit" ?disabled=${t.length === 0 || a.length === 0}>
                ${this.t("manage.create")}
              </button>
            </div>
          </form>`}
      </article>
    `;
  }
  async removeTrack(e, t) {
    this.hass !== void 0 && globalThis.confirm?.(`${this.t("manage.confirmDeleteTrack")} "${t}"?`) && await this.mutate(() => Ci(this.hass, e), this.t("manage.trackDeleted"));
  }
  planFrom(e) {
    const t = new FormData(e);
    return {
      max_new_per_day_cards: R(t.get("new"), 0, 0),
      max_reviews_per_day_cards: R(t.get("reviews"), 50, 1),
      max_notification_new_teasers: R(t.get("teasers"), 2, 0),
      target_date: String(t.get("date") ?? "").trim() || null,
      target_coverage: V(t.get("coverage"), 1, 0.01, 1),
      target_retention: V(t.get("retention"), 0.9, 0.01, 1)
    };
  }
  renderPlan(e) {
    const t = K(e.settings, "learning_plan"), i = this.scopeKey(e.track_id, "plan"), a = Number(this.profile?.settings?.max_new_per_day_cards ?? 8), o = this.forecasts[e.track_id];
    return r`
      <div class="stack">
        <p class="muted">${this.t("manage.planHelp")}</p>
        ${ue(`${i}:${this.formResetVersions[i] ?? 0}`, r`<form
          class="stack"
          data-save-scope=${i}
          @input=${() => this.markScopeDirty(i)}
          @change=${() => this.markScopeDirty(i)}
          @submit=${(n) => {
      if (n.preventDefault(), this.hass === void 0) return;
      const u = n.currentTarget;
      if (!this.validateScope(u)) return;
      const d = this.planFrom(u);
      this.loading = !0, this.errorMessage = "", Di(this.hass, e.track_id, d).then((h) => {
        this.forecasts = { ...this.forecasts, [e.track_id]: h }, this.forecastPlans = { ...this.forecastPlans, [e.track_id]: d };
      }).catch((h) => {
        this.forecasts = { ...this.forecasts, [e.track_id]: void 0 }, this.errorMessage = `${this.t("manage.previewFailed")} ${te(h)}`;
      }).finally(() => {
        this.loading = !1;
      });
    }}>
          <strong>${this.t("manage.basicPlan")}</strong>
          <div class="form-grid">
            <label>
              ${this.t("manage.newPerDay")}
              <input name="new" type="number" min="0" .value=${String(t.max_new_per_day_cards ?? a)} />
              <span class="meta">${this.t("manage.newPerDayHelp")}</span>
            </label>
            <label>
              ${this.t("manage.reviewsPerDay")}
              <input name="reviews" type="number" min="1" .value=${String(t.max_reviews_per_day_cards ?? 50)} />
              <span class="meta">${this.t("manage.reviewsPerDayHelp")}</span>
            </label>
            <label>
              ${this.t("manage.targetDate")}
              <input name="date" type="date" .value=${String(t.target_date ?? "")} />
              <span class="meta">${this.t("manage.targetDateHelp")}</span>
            </label>
          </div>
          <details class="section-panel">
            <summary>${this.t("manage.advancedPlan")}</summary>
            <div class="section-body form-grid">
              <label>
                ${this.t("manage.notificationTeasers")}
                <input name="teasers" type="number" min="0" .value=${String(t.max_notification_new_teasers ?? Math.min(2, a))} />
                <span class="meta">${this.t("manage.notificationTeasersHelp")}</span>
              </label>
              <label>
                ${this.t("manage.coverage")}
                <input name="coverage" type="number" min=".01" max="1" step=".01" .value=${String(t.target_coverage ?? 1)} />
                <span class="meta">${this.t("manage.coverageHelp")}</span>
              </label>
              <label>
                ${this.t("manage.retention")}
                <input name="retention" type="number" min=".01" max="1" step=".01" .value=${String(t.target_retention ?? 0.9)} />
                <span class="meta">${this.t("manage.retentionHelp")}</span>
              </label>
            </div>
          </details>
          <p class="muted">${this.t("manage.planPreviewHelp")}</p>
          <div class="actions"><button type="submit">${this.t("manage.preview")}</button></div>
          <p class="scope-state ${this.saveFeedback[i] === "error" ? "is-error" : ""}" role="status">
            ${this.scopeFeedbackText(i)}
          </p>
          <div class="scope-actions ${this.isScopeDirty(i) ? "is-dirty" : ""}">
            <button
              class="primary"
              type="button"
              @click=${(n) => {
      const u = n.currentTarget.closest("form");
      u instanceof HTMLFormElement && this.savePlanScope(e, u);
    }}
              ?disabled=${!this.isScopeDirty(i) || this.submittingScope === i}
            >
              ${this.submittingScope === i ? this.t("form.saving") : this.t("form.save")}
            </button>
            <button
              type="button"
              ?disabled=${!this.isScopeDirty(i) || this.submittingScope === i}
              @click=${() => {
      this.forecasts = { ...this.forecasts, [e.track_id]: void 0 }, this.forecastPlans = { ...this.forecastPlans, [e.track_id]: void 0 }, this.cancelScope(i);
    }}
            >
              ${this.t("form.cancel")}
            </button>
          </div>
        </form>`)}
        ${o === void 0 ? l : this.renderForecast(e, o)}
      </div>
    `;
  }
  forecastWarning(e) {
    return e === "target_date_requires_more_new_cards_than_daily_quota" ? this.t("manage.warningTargetDate") : e === "review_load_exceeds_quota_in_3_weeks" ? this.t("manage.warningReviews3Weeks") : e === "review_load_exceeds_quota_in_3_months" ? this.t("manage.warningReviews3Months") : e === "current_due_backlog_exceeds_review_quota" ? this.t("manage.warningDueBacklog") : e;
  }
  renderForecast(e, t) {
    const i = t.selected_cards === 0;
    return r`
      <div class=${t.warnings.length > 0 || i ? "warning" : "notice"}>
        <strong>${this.t("manage.forecast")}</strong>
        ${i ? r`<p>${this.t("manage.forecastZeroWarning")}</p>` : l}
        <h3>${this.t("manage.forecastCurrent")}</h3>
        <dl>
          <dt>${this.t("manage.selectedCards")}</dt><dd>${t.selected_cards}</dd>
          <dt>${this.t("manage.introducedCards")}</dt><dd>${t.introduced_cards}</dd>
          <dt>${this.t("manage.targetCards")}</dt><dd>${t.target_cards}</dd>
          <dt>${this.t("manage.cardsRemaining")}</dt><dd>${t.remaining_target_cards}</dd>
          <dt>${this.t("manage.dueNow")}</dt><dd>${t.due_now}</dd>
          <dt>${this.t("manage.requiredNew")}</dt><dd>${t.required_new_per_day}</dd>
          <dt>${this.t("manage.plannedNew")}</dt><dd>${t.planned_new_per_day}</dd>
        </dl>
        <h3>${this.t("manage.forecast")}</h3>
        <dl>
          <dt>${this.t("manage.reviews3Weeks")}</dt><dd>${t.reviews_per_day_in_3_weeks}</dd>
          <dt>${this.t("manage.reviews3Months")}</dt><dd>${t.reviews_per_day_in_3_months}</dd>
          <dt>${this.t("manage.notifications3Weeks")}</dt><dd>${t.notification_deliverable_in_3_weeks}</dd>
          <dt>${this.t("manage.notifications3Months")}</dt><dd>${t.notification_deliverable_in_3_months}</dd>
          <dt>${this.t("manage.sessionLoad3Weeks")}</dt><dd>${t.active_session_cards_in_3_weeks}</dd>
          <dt>${this.t("manage.sessionLoad3Months")}</dt><dd>${t.active_session_cards_in_3_months}</dd>
        </dl>
        <details class="section-panel">
          <summary>${this.t("manage.forecastMethod")}</summary>
          <div class="section-body"><p class="muted">${this.t("manage.forecastMethodHelp")}</p></div>
        </details>
        ${t.warnings.length === 0 ? l : r`<ul>${t.warnings.map((a) => r`<li>${this.forecastWarning(a)}</li>`)}</ul>`}
        <div class="actions">
          <button class="primary" @click=${() => this.applyPlan(e)} ?disabled=${i}>
            ${this.t("manage.applyPlan")}
          </button>
        </div>
      </div>
    `;
  }
  async applyPlan(e) {
    const t = this.forecastPlans[e.track_id];
    if (this.hass === void 0 || t === void 0) return;
    const i = this.scopeKey(e.track_id, "plan");
    await this.mutateScope(
      i,
      () => ut(this.hass, e.track_id, t),
      this.t("manage.saved")
    );
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
      const i = this.packs.find((a) => a.pack_version_id === t.pack_version_id);
      return i === void 0 ? [] : this.packs.filter((a) => a.pack_id === i.pack_id && a.pack_version_id !== i.pack_version_id).map((a) => ({ track: t, pack: a }));
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
        this.packDiff = await Ni(this.hass, e.track_id, t.pack_version_id), this.packDiffTrack = e.track_id, this.packDiffTarget = t.pack_version_id;
      } catch (i) {
        this.errorMessage = te(i);
      } finally {
        this.loading = !1;
      }
    }
  }
  async applyPackUpdate() {
    if (this.hass === void 0 || !this.packDiffTrack || !this.packDiffTarget) return;
    const e = this.packDiffTrack, t = this.packDiffTarget;
    await this.mutate(
      () => Mi(this.hass, e, t),
      this.t("manage.packIntegrated")
    ), this.errorMessage === "" && (this.packDiff = void 0, this.packDiffTrack = "", this.packDiffTarget = "");
  }
  renderNotificationTargets() {
    const e = this.notificationCandidates.filter(
      (t) => t.configured_target_id === null
    );
    return r`
      <article class="card">
        <h2>${this.t("manage.notificationTargetSettings")}</h2>
        <p class="muted">${this.t("manage.notificationTargetSettingsHelp")}</p>

        <div class="section-panel">
          <div class="section-body">
            ${e.length === 0 ? r`
              <p class="muted">${this.t("manage.noAvailableNotificationDevices")}</p>
            ` : r`
              <form class="form-grid" @submit=${(t) => {
      t.preventDefault();
      const i = new FormData(t.currentTarget), a = String(i.get("device") ?? "");
      !a || this.hass === void 0 || this.profile === void 0 || this.mutate(
        () => _i(this.hass, this.profile.profile_id, a),
        this.t("manage.notificationTargetCreated")
      );
    }}>
                <label>${this.t("manage.availableNotificationDevice")}
                  <select name="device" required>
                    ${e.map((t) => r`
                      <option value=${t.device_registry_id}>
                        ${t.friendly_name} · ${t.platform}
                        ${t.route_available ? "" : ` · ${this.t("manage.routeUnavailable")}`}
                      </option>
                    `)}
                  </select>
                </label>
                <div class="actions">
                  <button class="primary" type="submit">${this.t("manage.addNotificationTarget")}</button>
                </div>
              </form>
            `}
          </div>
        </div>

        ${this.notificationTargets.length === 0 ? r`
          <p>${this.t("manage.noNotificationTargets")}</p>
        ` : r`
          <div class="target-grid">
            ${this.notificationTargets.map((t) => {
      const i = this.targetScope(t.target_id);
      return ue(`${i}:${this.formResetVersions[i] ?? 0}`, r`
              <form
                class="target-card"
                data-save-scope=${i}
                @input=${() => this.markScopeDirty(i)}
                @change=${() => this.markScopeDirty(i)}
                @submit=${(a) => {
        a.preventDefault(), this.saveNotificationTarget(t, a.currentTarget);
      }}>
                <div class="target-header">
                  <h3>${t.friendly_name}</h3>
                  <span class="meta">${t.platform} · ${t.enabled ? this.t("manage.active") : this.t("manage.paused")}</span>
                </div>

                <div class="form-grid">
                  <label>${this.t("manage.name")}
                    <input name="friendlyName" .value=${t.friendly_name} required />
                  </label>
                  <label class="check-row">
                    <input name="enabled" type="checkbox" .checked=${t.enabled} />
                    ${this.t("manage.targetEnabled")}
                  </label>
                  <label class="check-row">
                    <input name="sharedDevice" type="checkbox" .checked=${t.shared_device} />
                    ${this.t("manage.sharedDevice")}
                  </label>
                </div>

                <details class="section-panel">
                  <summary>${this.t("manage.advancedTargetSettings")}</summary>
                  <div class="section-body">
                    <div class="form-grid">
                      <label>${this.t("manage.lockscreenVisibility")}
                        <select name="lockscreenVisibility" .value=${t.lockscreen_visibility}>
                          <option value="public">public</option>
                          <option value="private">private</option>
                          <option value="secret">secret</option>
                        </select>
                      </label>
                      <label>${this.t("manage.minimumGapSeconds")}
                        <input name="minimumGap" type="number" min="0" .value=${t.minimum_gap_seconds === null ? "" : String(t.minimum_gap_seconds)} />
                      </label>
                      <label>${this.t("manage.maximumPerHour")}
                        <input name="maxPerHour" type="number" min="1" .value=${t.maximum_notifications_per_hour === null ? "" : String(t.maximum_notifications_per_hour)} />
                      </label>
                      <label>${this.t("manage.targetPushBudget")}
                        <input name="targetBudget" type="number" min="0" .value=${t.daily_push_budget === null ? "" : String(t.daily_push_budget)} />
                      </label>
                    </div>
                    <p class="meta">
                      ${this.t("manage.capabilitiesConservative")} · ${t.device_registry_id}
                    </p>
                  </div>
                </details>

                <p class="scope-state ${this.saveFeedback[i] === "error" ? "is-error" : ""}" role="status">
                  ${this.scopeFeedbackText(i)}
                </p>
                <div class="scope-actions ${this.isScopeDirty(i) ? "is-dirty" : ""}">
                  <button
                    class="primary"
                    type="submit"
                    ?disabled=${!this.isScopeDirty(i) || this.submittingScope === i}
                  >
                    ${this.submittingScope === i ? this.t("form.saving") : this.t("form.save")}
                  </button>
                  <button
                    type="button"
                    ?disabled=${!this.isScopeDirty(i) || this.submittingScope === i}
                    @click=${() => this.cancelScope(i)}
                  >
                    ${this.t("form.cancel")}
                  </button>
                </div>
                <div class="actions">
                  <button
                    type="button"
                    @click=${() => {
        this.hass === void 0 || this.profile === void 0 || this.mutate(
          () => Si(
            this.hass,
            this.profile.profile_id,
            t.target_id
          ),
          this.t("manage.notificationTestSent")
        );
      }}
                  >
                    ${this.t("manage.testNotification")}
                  </button>
                </div>
              </form>`);
    })}
          </div>
        `}
      </article>
    `;
  }
  renderSettings() {
    if (!this.isOwner()) return r`<div class="card"><p>${this.t("manage.readOnly")}</p></div>`;
    const e = this.profile?.settings ?? {}, t = K(e, "quiet_hours"), i = K(e, "scheduler"), a = Array.isArray(i.active_windows) ? i.active_windows : [], o = typeof a[0] == "object" && a[0] !== null ? a[0] : {}, n = this.profileSettingsScope();
    return r`
      <article class="card">
        <h2>${this.t("manage.profileSettings")}</h2>
        <p class="muted">${this.t("manage.presetInitialOnly")}: ${this.profile?.preset}</p>
        ${ue(`${n}:${this.formResetVersions[n] ?? 0}`, r`<form
          class="form-grid"
          data-save-scope=${n}
          @input=${() => this.markScopeDirty(n)}
          @change=${() => this.markScopeDirty(n)}
          @submit=${(u) => {
      u.preventDefault(), this.saveProfileSettings(u.currentTarget);
    }}>
          <label>${this.t("manage.sessionLength")}<input name="session" type="number" min="1" .value=${String(e.session_length_cards ?? 20)} /></label>
          <label>${this.t("manage.newPerDay")}<input name="new" type="number" min="0" .value=${String(e.max_new_per_day_cards ?? 8)} /></label>
          <label>${this.t("manage.pushBudget")}<input name="push" type="number" min="0" .value=${String(e.daily_push_budget ?? 6)} /></label>
          <label>${this.t("manage.quietStart")}<input name="quietStart" type="time" .value=${String(t.start ?? "22:00")} /></label>
          <label>${this.t("manage.quietEnd")}<input name="quietEnd" type="time" .value=${String(t.end ?? "08:00")} /></label>
          <label>${this.t("manage.activeStart")}<input name="activeStart" type="time" .value=${String(o.start ?? "08:00")} /></label>
          <label>${this.t("manage.activeEnd")}<input name="activeEnd" type="time" .value=${String(o.end ?? "20:00")} /></label>
          <p class="scope-state ${this.saveFeedback[n] === "error" ? "is-error" : ""}" role="status">
            ${this.scopeFeedbackText(n)}
          </p>
          <div class="scope-actions ${this.isScopeDirty(n) ? "is-dirty" : ""}">
            <button
              class="primary"
              type="submit"
              ?disabled=${!this.isScopeDirty(n) || this.submittingScope === n}
            >
              ${this.submittingScope === n ? this.t("form.saving") : this.t("form.save")}
            </button>
            <button
              type="button"
              ?disabled=${!this.isScopeDirty(n) || this.submittingScope === n}
              @click=${() => this.cancelScope(n)}
            >
              ${this.t("form.cancel")}
            </button>
          </div>
        </form>`)}
      </article>
      ${this.renderNotificationTargets()}
    `;
  }
};
We.styles = N`
    ${j}
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
    .scope-state {
      margin-top: 10px;
      color: var(--secondary-text-color);
      font-size: .86rem;
    }
    .scope-state.is-error { color: var(--error-color,var(--primary-text-color)); }
    .scope-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 12px;
    }
    .scope-error-summary {
      margin-top: 10px;
      color: var(--error-color,var(--primary-text-color));
    }
    .track-form { display: grid; gap: 14px; }
    .section-panel {
      margin-top: 14px;
      border: 1px solid var(--divider-color);
      border-radius: 10px;
      overflow: clip;
      background: var(--secondary-background-color);
    }
    .section-panel > summary {
      display: flex;
      align-items: center;
      gap: 9px;
      padding: 12px 14px;
      cursor: pointer;
      list-style: none;
      font-weight: 650;
      color: var(--primary-text-color);
      background: var(--card-background-color,var(--primary-background-color));
    }
    .section-panel > summary::-webkit-details-marker { display: none; }
    .section-panel > summary::before {
      content: "›";
      display: inline-block;
      font-size: 1.2rem;
      line-height: 1;
      transition: transform 120ms ease;
    }
    .section-panel[open] > summary::before { transform: rotate(90deg); }
    .section-body { padding: 14px; }
    .section-body > :first-child { margin-top: 0; }
    .section-body > :last-child { margin-bottom: 0; }
    .target-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit,minmax(300px,1fr));
      gap: 14px;
      margin-top: 14px;
    }
    .target-card {
      display: grid;
      align-content: start;
      gap: 12px;
      padding: 16px;
      border: 1px solid var(--divider-color);
      border-radius: 10px;
      background: var(--card-background-color,var(--primary-background-color));
    }
    .target-header { display: grid; gap: 3px; }
    .target-header h3 { margin: 0; }
    .target-card .section-panel { margin-top: 0; }
    .check-row {
      display: flex;
      align-items: center;
      gap: 8px;
      color: var(--primary-text-color);
      font-size: .9rem;
    }
    .check-row input { width: auto; }
    .track-summary {
      display: grid;
      gap: 4px;
      margin-bottom: 14px;
    }
    .danger-zone {
      margin-top: 18px;
      padding: 14px;
      border: 1px solid var(--error-color,var(--divider-color));
      border-radius: 9px;
      background: var(--secondary-background-color);
    }
    .danger-zone button {
      border-color: var(--error-color,var(--divider-color));
    }
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
      .scope-actions.is-dirty {
        position: sticky;
        bottom: 0;
        z-index: 10;
        margin-inline: -18px;
        margin-bottom: -18px;
        padding: 10px max(18px, env(safe-area-inset-right))
          max(10px, env(safe-area-inset-bottom))
          max(18px, env(safe-area-inset-left));
        background: var(--card-background-color,var(--primary-background-color));
        border-top: 1px solid var(--divider-color);
        box-shadow: 0 -4px 14px rgb(0 0 0 / 10%);
      }
    }
  `;
let v = We;
y([
  f({ attribute: !1 })
], v.prototype, "hass");
y([
  f({ attribute: !1 })
], v.prototype, "profile");
y([
  f({ attribute: !1 })
], v.prototype, "route");
y([
  c()
], v.prototype, "tracks");
y([
  c()
], v.prototype, "packs");
y([
  c()
], v.prototype, "notificationTargets");
y([
  c()
], v.prototype, "notificationCandidates");
y([
  c()
], v.prototype, "members");
y([
  c()
], v.prototype, "shareTargets");
y([
  c()
], v.prototype, "createTrackPackId");
y([
  c()
], v.prototype, "createTrackSource");
y([
  c()
], v.prototype, "forecasts");
y([
  c()
], v.prototype, "forecastPlans");
y([
  c()
], v.prototype, "packDiff");
y([
  c()
], v.prototype, "packDiffTrack");
y([
  c()
], v.prototype, "packDiffTarget");
y([
  c()
], v.prototype, "loading");
y([
  c()
], v.prototype, "errorMessage");
y([
  c()
], v.prototype, "notice");
y([
  c()
], v.prototype, "dirtyScopes");
y([
  c()
], v.prototype, "formResetVersions");
y([
  c()
], v.prototype, "submittingScope");
y([
  c()
], v.prototype, "saveFeedback");
globalThis.customElements !== void 0 && customElements.get("locklearn-management-view") === void 0 && customElements.define("locklearn-management-view", v);
var ws = Object.defineProperty, W = (s, e, t, i) => {
  for (var a = void 0, o = s.length - 1, n; o >= 0; o--)
    (n = s[o]) && (a = n(e, t, a) || a);
  return a && ws(e, t, a), a;
};
function he(s) {
  if (s === null) return null;
  try {
    const e = new URL(s);
    return e.protocol === "https:" || e.protocol === "http:" ? e.href : null;
  } catch {
    return null;
  }
}
function _s(s) {
  if (s < 1024) return `${s} B`;
  const e = ["KiB", "MiB", "GiB"];
  let t = s / 1024, i = 0;
  for (; t >= 1024 && i < e.length - 1; )
    t /= 1024, i += 1;
  return `${t.toFixed(t >= 10 ? 1 : 2)} ${e[i]}`;
}
const Ve = class Ve extends z {
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
    return Z(
      this.hass?.locale?.language ?? this.hass?.language ?? globalThis.navigator?.language ?? "en"
    );
  }
  t(e) {
    return O(this.locale(), e);
  }
  async load() {
    if (this.hass !== void 0) {
      this.loading = !0, this.errorMessage = "";
      try {
        this.datasets = await Ri(this.hass);
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
        this.datasets = await Ei(this.hass), this.notice = this.t("datasets.refreshed");
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
        const t = await Li(this.hass, e.dataset_id, e.available_version);
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
    const i = this.attributionKey(e, t), a = this.attributionPages[i];
    if (a !== void 0) {
      this.attributionPages = {
        ...this.attributionPages,
        [i]: { ...a, expanded: !a.expanded }
      };
      return;
    }
    this.attributionPages = {
      ...this.attributionPages,
      [i]: { items: [], cursor: null, expanded: !0, loading: !0 }
    };
    try {
      const o = await dt(this.hass, e, t);
      this.attributionPages = {
        ...this.attributionPages,
        [i]: { ...o, expanded: !0, loading: !1 }
      };
    } catch (o) {
      this.errorMessage = o instanceof Error ? o.message : String(o), this.attributionPages = {
        ...this.attributionPages,
        [i]: { items: [], cursor: null, expanded: !0, loading: !1 }
      };
    }
  }
  async loadMoreAttributions(e, t) {
    if (this.hass === void 0) return;
    const i = this.attributionKey(e, t), a = this.attributionPages[i];
    if (!(a === void 0 || a.cursor === null || a.loading)) {
      this.attributionPages = {
        ...this.attributionPages,
        [i]: { ...a, loading: !0 }
      };
      try {
        const o = await dt(
          this.hass,
          e,
          t,
          a.cursor
        );
        this.attributionPages = {
          ...this.attributionPages,
          [i]: {
            items: [...a.items, ...o.items],
            cursor: o.cursor,
            expanded: !0,
            loading: !1
          }
        };
      } catch (o) {
        this.errorMessage = o instanceof Error ? o.message : String(o), this.attributionPages = {
          ...this.attributionPages,
          [i]: { ...a, loading: !1 }
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
    const t = e.error !== null || e.stale_sources.length > 0, i = he(e.release_url);
    return r`
      <article class="card">
        <h2>${e.name}</h2>
        <dl>
          <dt>${this.t("datasets.state")}</dt><dd>${e.state}</dd>
          <dt>${this.t("datasets.installedVersion")}</dt><dd>${e.installed_version ?? "—"}</dd>
          <dt>${this.t("datasets.availableVersion")}</dt><dd>${e.available_version ?? "—"}</dd>
          <dt>${this.t("datasets.sourceAge")}</dt>
          <dd>${e.source_age_days === null ? "—" : `${e.source_age_days} ${this.t("datasets.days")}`}</dd>
          <dt>${this.t("datasets.disk")}</dt><dd>${_s(e.cache_bytes)}</dd>
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
        ${e.sources.length === 0 ? r`<p class="muted">${this.t("datasets.noSources")}</p>` : r`<ul>${e.sources.map((a) => {
      const o = he(a.homepage), n = this.attributionKey(e.dataset_id, a.source_id), u = this.attributionPages[n];
      return r`
                <li>
                  <strong>${a.name}</strong> — ${a.provider}
                  <div class="meta">${a.attribution_template}</div>
                  <div class="meta">
                    ${this.t("datasets.upstream")}: ${a.upstream_version}
                    ${a.upstream_date ? r` · ${a.upstream_date}` : l}
                    · ${a.provenance_records} ${this.t("datasets.records")}
                    ${a.modified_records > 0 ? r` · ${a.modified_records} ${this.t("datasets.modified")}` : l}
                  </div>
                  ${o ? r`<a href=${o} target="_blank" rel="noopener noreferrer">${this.t("datasets.sourcePage")}</a>` : l}
                  ${a.attribution_records > 0 ? r`
                        <div class="actions">
                          <button
                            type="button"
                            @click=${() => {
        this.toggleAttributions(e.dataset_id, a.source_id);
      }}
                          >
                            ${u?.expanded ? this.t("datasets.hideAttributions") : this.t("datasets.showAttributions")}
                          </button>
                        </div>
                        ${u?.expanded ? r`
                              <div class="notice">
                                <strong>${this.t("datasets.individualAttributions")}</strong>
                                ${u.loading && u.items.length === 0 ? r`<p>${this.t("datasets.loading")}</p>` : r`<ul>
                                      ${u.items.map((d) => r`
                                        <li>
                                          ${d.attribution_text}
                                          <div class="meta">
                                            ${d.source_record_id ?? "—"}
                                            ${d.author ? r` · ${d.author}` : l}
                                            ${d.language_tag ? r` · ${d.language_tag}` : l}
                                            ${d.modified_from_source ? r` · ${this.t("datasets.modified")}` : l}
                                          </div>
                                        </li>
                                      `)}
                                    </ul>`}
                                ${u.cursor !== null ? r`<button
                                      type="button"
                                      ?disabled=${u.loading}
                                      @click=${() => {
        this.loadMoreAttributions(e.dataset_id, a.source_id);
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
        ${e.licenses.length === 0 ? r`<p class="muted">${this.t("datasets.noLicenses")}</p>` : r`<ul>${e.licenses.map((a) => r`
              <li>
                <strong>${a.name}</strong>
                <span class="meta">(${a.license_id} · ${a.license_scope})</span>
                <div class="meta">
                  ${a.attribution_required ? this.t("datasets.attributionRequired") : this.t("datasets.attributionOptional")}
                  · ${a.commercial_use_allowed ? this.t("datasets.commercialAllowed") : this.t("datasets.commercialBlocked")}
                  ${a.share_alike ? r` · ${this.t("datasets.shareAlike")}` : l}
                </div>
                ${he(a.source_url) ? r`<a href=${he(a.source_url)} target="_blank" rel="noopener noreferrer">${this.t("datasets.licensePage")}</a>` : l}
              </li>
            `)}</ul>`}
      </article>
    `;
  }
};
Ve.styles = N`
    ${j}
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
let L = Ve;
W([
  f({ attribute: !1 })
], L.prototype, "hass");
W([
  f({ type: Boolean })
], L.prototype, "admin");
W([
  c()
], L.prototype, "datasets");
W([
  c()
], L.prototype, "loading");
W([
  c()
], L.prototype, "errorMessage");
W([
  c()
], L.prototype, "notice");
W([
  c()
], L.prototype, "attributionPages");
globalThis.customElements !== void 0 && customElements.get("locklearn-dataset-view") === void 0 && customElements.define("locklearn-dataset-view", L);
var xs = Object.defineProperty, P = (s, e, t, i) => {
  for (var a = void 0, o = s.length - 1, n; o >= 0; o--)
    (n = s[o]) && (a = n(e, t, a) || a);
  return a && xs(e, t, a), a;
};
function Te(s) {
  return s === null ? "—" : `${Math.round(s * 100)}%`;
}
function Ss(s, e = 14) {
  if (e <= 0) return [];
  const t = /* @__PURE__ */ new Map();
  for (const i of s) {
    const a = t.get(i.local_date);
    if (a === void 0) {
      t.set(i.local_date, { ...i });
      continue;
    }
    a.learning_exposures += i.learning_exposures, a.verified_retrievals += i.verified_retrievals, a.self_known += i.self_known, a.verified_correct += i.verified_correct, a.verified_wrong += i.verified_wrong, a.quiz_total += i.quiz_total, a.free_text_total += i.free_text_total, a.hints_used += i.hints_used, a.new_cards += i.new_cards, a.reviewed_cards += i.reviewed_cards, a.relearning_cards += i.relearning_cards, a.leech_cards += i.leech_cards, a.active_seconds += i.active_seconds;
  }
  return [...t.values()].sort((i, a) => i.local_date.localeCompare(a.local_date)).slice(-e).reverse();
}
function qs(s) {
  return {
    exposures: s.reduce((e, t) => e + t.learning_exposures, 0),
    verifiedRetrievals: s.reduce((e, t) => e + t.verified_retrievals, 0)
  };
}
function pe(s) {
  return s?.role === "owner" || s?.role === "editor";
}
const Be = class Be extends z {
  constructor() {
    super(...arguments), this.difficulties = [], this.tracks = [], this.selectedTrackId = "", this.loading = !1, this.errorMessage = "", this.notice = "", this.mnemonicEdits = {}, this.busyCardKey = null, this.loadGeneration = 0;
  }
  updated(e) {
    (e.has("hass") || e.has("profile")) && this.load();
  }
  locale() {
    return Z(
      this.hass?.locale?.language ?? this.hass?.language ?? globalThis.navigator?.language ?? "en"
    );
  }
  t(e) {
    return O(this.locale(), e);
  }
  async load() {
    if (this.hass === void 0 || this.profile === void 0) {
      this.stats = void 0, this.difficulties = [], this.tracks = [];
      return;
    }
    const e = ++this.loadGeneration, t = this.hass, i = this.profile.profile_id;
    this.loading = !0, this.errorMessage = "";
    try {
      const a = (await Ct(t, i)).filter(
        (h) => h.status === "active"
      ), o = this.selectedTrackId && a.some((h) => h.track_id === this.selectedTrackId) ? this.selectedTrackId : "", [n, u] = await Promise.all([
        qi(t, i, o || null),
        Ti(t, i, o || null)
      ]);
      if (e !== this.loadGeneration) return;
      this.tracks = a, this.selectedTrackId = o, this.stats = n, this.difficulties = u;
      const d = { ...this.mnemonicEdits };
      for (const h of u)
        d[h.card_key] === void 0 && (d[h.card_key] = h.annotations[0]?.note ?? "");
      this.mnemonicEdits = d;
    } catch (a) {
      if (e !== this.loadGeneration) return;
      this.errorMessage = a instanceof Error ? a.message : String(a);
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
    if (this.hass === void 0 || this.profile === void 0 || !pe(this.profile)) return;
    const t = (this.mnemonicEdits[e.card_key] ?? "").trim();
    if (t) {
      this.busyCardKey = e.card_key, this.errorMessage = "", this.notice = "";
      try {
        const i = e.annotations[0];
        i === void 0 ? await Ut(this.hass, this.profile.profile_id, e.card_key, t) : await Wi(
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
    if (!(this.hass === void 0 || this.profile === void 0 || !pe(this.profile))) {
      this.busyCardKey = e.card_key, this.errorMessage = "", this.notice = "";
      try {
        const t = await Bi(
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
    if (!(this.hass === void 0 || this.profile === void 0 || !pe(this.profile) || !(globalThis.confirm?.(this.t("stats.reactivateConfirm")) ?? !0))) {
      this.busyCardKey = e.card_key, this.errorMessage = "", this.notice = "";
      try {
        await Vi(
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
    const t = e.recent_verified_accuracy, i = e.calibration, a = Ss(e.daily), o = qs(a);
    return r`
      <section class="grid" aria-label=${this.t("stats.verifiedGroup")}>
        <article class="card metric verified">
          <span>${this.t("stats.dueToday")}</span>
          <strong>${e.due_today}</strong>
        </article>
        <article class="card metric verified">
          <span>${this.t("stats.verifiedAccuracy")}</span>
          <strong>${Te(t.accuracy)}</strong>
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
        <p class="muted">${this.t("stats.statesHelp")}</p>
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
            <strong>${o.exposures}</strong>
            <div class="meta">${this.t("stats.notAccuracy")}</div>
          </div>
          <div class="metric">
            <span>${this.t("stats.verifiedRetrievals")}</span>
            <strong>${o.verifiedRetrievals}</strong>
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
            <strong>${Te(i.later_verified_accuracy)}</strong>
          </div>
        </div>
      </article>

      <article class="card secondary">
        <h2>${this.t("stats.mastery")}</h2>
        <div class="metric">
          <strong>${Te(e.mastery.value)}</strong>
          <div class="meta">${e.mastery.card_count} ${this.t("stats.cards")}</div>
        </div>
        <p>${this.t("stats.masteryExplain")}</p>
      </article>

      <article class="card">
        <h2>${this.t("stats.difficulties")}</h2>
        ${this.difficulties.length === 0 ? r`<p class="muted">${this.t("stats.noDifficulties")}</p>` : r`<ul>
              ${this.difficulties.map(
      (n) => r`
                  <li>
                    <strong>${n.card_key}</strong>
                    — ${this.t("stats.leechScore")} ${n.leech_score}
                    <div class="meta">
                      ${n.verified_correct_count} ${this.t("stats.correct")} ·
                      ${n.verified_wrong_count} ${this.t("stats.wrong")} ·
                      ${n.annotations.length > 0 ? this.t("stats.mnemonicPresent") : this.t("stats.mnemonicSuggested")}
                    </div>
                    ${n.confusions.length === 0 ? l : r`<div class="meta">
                          ${this.t("stats.confusions")}: ${n.confusions.map(
        (u) => `${u.expected_answer_id}→${u.chosen_answer_id} ×${u.count}`
      ).join(", ")}
                        </div>`}
                    ${n.annotations[0]?.note ? r`<p>${n.annotations[0].note}</p>` : l}
                    ${pe(this.profile) ? r`
                          <label>
                            <span>${this.t("stats.personalMnemonic")}</span>
                            <textarea
                              .value=${this.mnemonicEdits[n.card_key] ?? ""}
                              @input=${(u) => this.editMnemonic(n.card_key, u)}
                            ></textarea>
                          </label>
                          <div class="actions">
                            <button
                              ?disabled=${this.busyCardKey !== null}
                              @click=${() => {
        this.saveMnemonic(n);
      }}
                            >
                              ${n.annotations.length > 0 ? this.t("stats.updateMnemonic") : this.t("stats.createMnemonic")}
                            </button>
                            <button
                              ?disabled=${this.busyCardKey !== null}
                              @click=${() => {
        this.startTargetedSession(n);
      }}
                            >
                              ${this.t("stats.targetedSession")}
                            </button>
                            <button
                              ?disabled=${this.busyCardKey !== null}
                              @click=${() => {
        this.reactivate(n);
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
      (n) => r`
                  <li>
                    <strong>${n.card_key}</strong>
                    <div class="meta">
                      ${this.t("stats.expected")} ${n.expected_answer_id} →
                      ${this.t("stats.chosen")} ${n.chosen_answer_id} ·
                      ${n.count}×
                    </div>
                  </li>
                `
    )}
            </ul>`}
      </article>

      <article class="card">
        <h2>${this.t("stats.recentActivity")}</h2>
        ${a.length === 0 ? r`<p class="muted">${this.t("stats.noActivity")}</p>` : r`<div class="table-wrap">
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
                  ${a.map(
      (n) => r`
                      <tr>
                        <td>${n.local_date}</td>
                        <td>${n.learning_exposures}</td>
                        <td>${n.verified_retrievals}</td>
                        <td>${n.verified_correct}</td>
                        <td>${n.verified_wrong}</td>
                        <td>${n.new_cards}</td>
                        <td>${n.reviewed_cards}</td>
                        <td>${n.relearning_cards}</td>
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
Be.styles = N`
    ${j}
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
let T = Be;
P([
  f({ attribute: !1 })
], T.prototype, "hass");
P([
  f({ attribute: !1 })
], T.prototype, "profile");
P([
  c()
], T.prototype, "stats");
P([
  c()
], T.prototype, "difficulties");
P([
  c()
], T.prototype, "tracks");
P([
  c()
], T.prototype, "selectedTrackId");
P([
  c()
], T.prototype, "loading");
P([
  c()
], T.prototype, "errorMessage");
P([
  c()
], T.prototype, "notice");
P([
  c()
], T.prototype, "mnemonicEdits");
P([
  c()
], T.prototype, "busyCardKey");
globalThis.customElements !== void 0 && customElements.get("locklearn-stats-view") === void 0 && customElements.define("locklearn-stats-view", T);
const $t = [
  { route: "home", labelKey: "nav.home" },
  { route: "learn", labelKey: "nav.learn" },
  { route: "quiz", labelKey: "nav.quiz" },
  { route: "exam", labelKey: "nav.exam" },
  { route: "stats", labelKey: "nav.stats" },
  { route: "profiles", labelKey: "nav.profiles" },
  { route: "tracks", labelKey: "nav.tracks" },
  { route: "packs", labelKey: "nav.packs" },
  { route: "sources", labelKey: "nav.sources" }
], Ts = [
  { route: "settings", labelKey: "nav.settings" }
];
function Pe(s) {
  return s.length === 0 ? [] : new Set(s.map((t) => t.role)).has("owner") ? [...$t, ...Ts] : $t;
}
function me(s, e) {
  return Pe(e).some((t) => t.route === s);
}
function As(s) {
  return {
    mine: s.filter((e) => e.role === "owner"),
    shared: s.filter((e) => e.role !== "owner")
  };
}
function kt(s, e) {
  const t = e.personal_profile?.profile_id;
  if (t !== void 0 && s.some((a) => a.profile_id === t))
    return t;
  const i = s.find((a) => a.role === "owner");
  return i !== void 0 ? i.profile_id : s[0]?.profile_id ?? null;
}
function zs(s) {
  if (s === void 0) return { kind: "define" };
  const e = typeof s.locklearnFrontendProtocol == "number" ? s.locklearnFrontendProtocol : null;
  return e === I ? { kind: "reuse" } : {
    kind: "reload",
    existingProtocol: e,
    frontendProtocol: I
  };
}
function Cs(s, e, t) {
  return !s && e && t;
}
var Ps = Object.defineProperty, q = (s, e, t, i) => {
  for (var a = void 0, o = s.length - 1, n; o >= 0; o--)
    (n = s[o]) && (a = n(e, t, a) || a);
  return a && Ps(e, t, a), a;
};
const wt = "locklearn-hard-reload-required";
async function Rs(s, e) {
  let t;
  try {
    return await Promise.race([
      s,
      new Promise((i, a) => {
        t = globalThis.setTimeout(
          () => a(new Error("LockLearn initial load timed out")),
          e
        );
      })
    ]);
  } finally {
    t !== void 0 && globalThis.clearTimeout(t);
  }
}
const be = class be extends z {
  constructor() {
    super(...arguments), this.status = "loading", this.activeRoute = xe(
      globalThis.location?.pathname ?? "/locklearn"
    ), this.profiles = [], this.selectedProfileId = null, this.dashboardLoading = !1, this.dashboardError = "", this.errorMessage = "", this.managementDirty = !1, this.navigationSaving = !1, this.loadFailures = 0, this.diagnosticNotice = "", this.online = globalThis.navigator?.onLine ?? !0, this.loadGeneration = 0, this.dashboardGeneration = 0, this.initialLoadStarted = !1, this.handlePopState = () => {
      const e = xe(globalThis.location?.pathname ?? "/locklearn"), t = me(e, this.profiles) ? e : "home";
      if (this.managementDirty && t !== this.activeRoute) {
        this.pendingNavigation = { kind: "route", route: t }, globalThis.history?.replaceState({}, "", jt(this.activeRoute)), this.requestUpdate();
        return;
      }
      this.activeRoute = t;
    }, this.handleBeforeUnload = (e) => {
      this.managementDirty && (e.preventDefault(), e.returnValue = "");
    }, this.handleConnectivity = () => {
      this.online = globalThis.navigator?.onLine ?? !0;
    };
  }
  connectedCallback() {
    super.connectedCallback(), globalThis.addEventListener?.("popstate", this.handlePopState), globalThis.addEventListener?.("beforeunload", this.handleBeforeUnload), globalThis.addEventListener?.("online", this.handleConnectivity), globalThis.addEventListener?.("offline", this.handleConnectivity);
  }
  disconnectedCallback() {
    globalThis.removeEventListener?.("popstate", this.handlePopState), globalThis.removeEventListener?.("beforeunload", this.handleBeforeUnload), globalThis.removeEventListener?.("online", this.handleConnectivity), globalThis.removeEventListener?.("offline", this.handleConnectivity), super.disconnectedCallback();
  }
  updated(e) {
    Cs(
      this.initialLoadStarted,
      e.has("hass"),
      this.hass !== void 0
    ) && (this.initialLoadStarted = !0, this.load());
  }
  locale() {
    const e = this.hass?.locale?.language ?? this.hass?.language ?? globalThis.navigator?.language ?? "en";
    return Z(e);
  }
  t(e) {
    return O(this.locale(), e);
  }
  async load() {
    if (this.hass === void 0) return;
    const e = ++this.loadGeneration;
    this.status = "loading", this.errorMessage = "";
    try {
      const { bootstrapState: t, profiles: i } = await Rs((async () => {
        const o = await vi(this.hass), n = await nt(this.hass);
        return { bootstrapState: o, profiles: n };
      })(), 1e4);
      if (e !== this.loadGeneration) return;
      this.bootstrapState = t, this.profiles = i, this.selectedProfileId = kt(i, t);
      const a = xe(globalThis.location?.pathname ?? t.panel_path);
      this.activeRoute = me(a, i) ? a : "home", this.status = "ready", this.loadFailures = 0, this.diagnosticNotice = "", this.loadDashboard();
    } catch (t) {
      if (e !== this.loadGeneration) return;
      if (t instanceof zt) {
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
      this.errorMessage = t instanceof Error ? t.message : String(t), this.loadFailures += 1, this.status = "error";
    }
  }
  selectRoute(e) {
    if (!(!me(e, this.profiles) || e === this.activeRoute)) {
      if (this.managementDirty) {
        this.pendingNavigation = { kind: "route", route: e };
        return;
      }
      this.applyNavigation({ kind: "route", route: e });
    }
  }
  selectProfile(e) {
    const t = e.currentTarget;
    if (!(t instanceof HTMLSelectElement)) return;
    const i = t.value;
    if (!(!this.profiles.some((a) => a.profile_id === i) || i === this.selectedProfileId)) {
      if (this.managementDirty) {
        this.pendingNavigation = { kind: "profile", profileId: i }, this.requestUpdate();
        return;
      }
      this.applyNavigation({ kind: "profile", profileId: i });
    }
  }
  applyNavigation(e) {
    if (e.kind === "route") {
      this.activeRoute = e.route, se(e.route);
      return;
    }
    this.selectedProfileId = e.profileId, this.handoffSession = void 0, this.loadDashboard();
  }
  handleManagementDirty(e) {
    this.managementDirty = !!e.detail?.dirty;
  }
  managementView() {
    return this.renderRoot.querySelector(
      "locklearn-management-view"
    );
  }
  async saveAndNavigate() {
    const e = this.pendingNavigation, t = this.managementView();
    if (!(e === void 0 || t === null)) {
      this.navigationSaving = !0;
      try {
        if (!await t.saveDirtyScopes()) return;
        this.managementDirty = !1, this.pendingNavigation = void 0, this.applyNavigation(e);
      } finally {
        this.navigationSaving = !1;
      }
    }
  }
  discardAndNavigate() {
    const e = this.pendingNavigation;
    e !== void 0 && (this.managementView()?.discardDirtyScopes(), this.managementDirty = !1, this.pendingNavigation = void 0, this.applyNavigation(e));
  }
  stayOnDirtyForm() {
    this.pendingNavigation = void 0, this.requestUpdate();
  }
  openTargetedSession(e) {
    const t = e.detail?.session;
    if (t === void 0 || this.selectedProfileId === null || t.profile_id !== this.selectedProfileId)
      return;
    this.handoffSession = t;
    const i = ["quiz", "calibration"].includes(t.type) ? "quiz" : "learn";
    this.activeRoute = i, se(i);
  }
  clearSessionHandoff() {
    this.handoffSession = void 0;
  }
  async refreshManagement() {
    if (this.hass !== void 0)
      try {
        const e = await nt(this.hass), t = this.selectedProfileId;
        this.profiles = e, this.selectedProfileId = t !== null && e.some((i) => i.profile_id === t) ? t : this.bootstrapState === void 0 ? e[0]?.profile_id ?? null : kt(e, this.bootstrapState), me(this.activeRoute, e) || (this.activeRoute = "home", se("home")), await this.loadDashboard();
      } catch (e) {
        this.errorMessage = e instanceof Error ? e.message : String(e);
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
      const t = await Ii(this.hass, this.selectedProfileId);
      if (e !== this.dashboardGeneration) return;
      this.dashboard = t;
    } catch (t) {
      if (e !== this.dashboardGeneration) return;
      this.dashboard = void 0, this.dashboardError = t instanceof Error ? t.message : String(t);
    } finally {
      e === this.dashboardGeneration && (this.dashboardLoading = !1);
    }
  }
  async copyDiagnostic() {
    const e = [
      `LockLearn frontend protocol: ${I}`,
      `route: ${this.activeRoute}`,
      `online: ${this.online}`,
      `failures: ${this.loadFailures}`,
      `error: ${this.errorMessage}`
    ].join(`
`);
    try {
      await globalThis.navigator?.clipboard?.writeText(e), this.diagnosticNotice = this.t("state.diagnosticCopied");
    } catch {
      this.diagnosticNotice = e;
    }
  }
  goHome() {
    globalThis.location?.assign("/");
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
            <div class="guard-actions">
              <button class="primary-button" @click=${() => {
        this.load();
      }}>
                ${this.t("state.retry")}
              </button>
              <button @click=${this.goHome}>${this.t("state.home")}</button>
              ${this.loadFailures >= 3 ? r`<button @click=${() => {
        this.copyDiagnostic();
      }}>
                    ${this.t("state.copyDiagnostic")}
                  </button>` : l}
            </div>
            ${this.diagnosticNotice ? r`<p class="meta" role="status">${this.diagnosticNotice}</p>` : l}
          </section>
        </main>
      `;
    const e = Pe(this.profiles), t = As(this.profiles);
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
        ${this.online ? l : r`<div class="connection-banner" role="status">${this.t("state.offline")}</div>`}
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
                    @locklearn-open-session=${this.openTargetedSession}
                  ></locklearn-learn-view>` : this.activeRoute === "quiz" ? r`<locklearn-quiz-view
                      .hass=${this.hass}
                      .profile=${this.profiles.find(
      (i) => i.profile_id === this.selectedProfileId
    )}
                      .dashboard=${this.dashboard}
                      .externalSession=${this.handoffSession}
                      @locklearn-session-handoff-consumed=${this.clearSessionHandoff}
                      @locklearn-open-session=${this.openTargetedSession}
                    ></locklearn-quiz-view>` : this.activeRoute === "exam" ? r`<locklearn-exam-view
                        .hass=${this.hass}
                        .profile=${this.profiles.find(
      (i) => i.profile_id === this.selectedProfileId
    )}
                        .dashboard=${this.dashboard}
                      ></locklearn-exam-view>` : this.activeRoute === "stats" ? r`<locklearn-stats-view
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
                        @locklearn-dirty-state-changed=${this.handleManagementDirty}
                      ></locklearn-management-view>` : r`<section class="page">
                    <h1>${this.routeLabel(this.activeRoute)}</h1>
                    <p>${this.t("route.placeholder")}</p>
                  </section>`}
        </main>
        ${this.pendingNavigation === void 0 ? l : r`<div class="guard-backdrop">
              <section
                class="guard-dialog"
                role="dialog"
                aria-modal="true"
                aria-labelledby="unsaved-title"
              >
                <h2 id="unsaved-title">${this.t("form.navigationTitle")}</h2>
                <p>${this.t("form.navigationBody")}</p>
                <div class="guard-actions">
                  <button
                    class="primary-button"
                    @click=${() => {
      this.saveAndNavigate();
    }}
                    ?disabled=${this.navigationSaving}
                  >
                    ${this.navigationSaving ? this.t("form.saving") : this.t("form.saveAndLeave")}
                  </button>
                  <button
                    @click=${this.discardAndNavigate}
                    ?disabled=${this.navigationSaving}
                  >
                    ${this.t("form.leaveWithoutSaving")}
                  </button>
                  <button
                    @click=${this.stayOnDirtyForm}
                    ?disabled=${this.navigationSaving}
                  >
                    ${this.t("form.stay")}
                  </button>
                </div>
              </section>
            </div>`}
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
    const t = Pe(this.profiles).find((i) => i.route === e);
    return t === void 0 ? this.t("nav.home") : this.t(t.labelKey);
  }
};
be.locklearnFrontendProtocol = I, be.styles = N`
    ${j}
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

    .guard-backdrop {
      position: fixed;
      inset: 0;
      z-index: 1000;
      display: grid;
      place-items: center;
      padding: 20px;
      background: color-mix(in srgb, var(--primary-text-color) 30%, transparent);
    }

    .guard-dialog {
      width: min(520px, 100%);
      padding: 20px;
      border-radius: 14px;
      background: var(--card-background-color, var(--primary-background-color));
      color: var(--primary-text-color);
      box-shadow: var(--ha-card-box-shadow, 0 12px 36px rgb(0 0 0 / 24%));
    }

    .guard-dialog h2 { margin-top: 0; }

    .connection-banner {
      position: sticky;
      top: 64px;
      z-index: 2;
      padding: 8px 16px;
      text-align: center;
      background: var(--warning-color, var(--secondary-background-color));
      color: var(--primary-text-color);
    }
    .guard-actions { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 18px; }
    .guard-actions button { min-height: 44px; padding: 9px 12px; }

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
let _ = be;
q([
  f({ attribute: !1 })
], _.prototype, "hass");
q([
  c()
], _.prototype, "status");
q([
  c()
], _.prototype, "activeRoute");
q([
  c()
], _.prototype, "bootstrapState");
q([
  c()
], _.prototype, "profiles");
q([
  c()
], _.prototype, "selectedProfileId");
q([
  c()
], _.prototype, "dashboard");
q([
  c()
], _.prototype, "dashboardLoading");
q([
  c()
], _.prototype, "dashboardError");
q([
  c()
], _.prototype, "errorMessage");
q([
  c()
], _.prototype, "handoffSession");
q([
  c()
], _.prototype, "managementDirty");
q([
  c()
], _.prototype, "pendingNavigation");
q([
  c()
], _.prototype, "navigationSaving");
q([
  c()
], _.prototype, "loadFailures");
q([
  c()
], _.prototype, "diagnosticNotice");
q([
  c()
], _.prototype, "online");
function Es(s) {
  if (typeof document > "u" || document.getElementById(wt) !== null) return;
  const e = document.createElement("div");
  e.id = wt, e.setAttribute("role", "alert"), e.style.cssText = "position:fixed;inset:0;z-index:2147483647;display:grid;place-items:center;padding:24px;background:var(--primary-background-color,#fff);color:var(--primary-text-color,#111);font-family:system-ui,sans-serif";
  const t = document.createElement("div");
  t.style.cssText = "max-width:680px;padding:24px;border:1px solid var(--divider-color,#ddd);border-radius:12px;background:var(--card-background-color,#fff)";
  const i = document.createElement("h1");
  i.textContent = "LockLearn was updated";
  const a = document.createElement("p");
  a.textContent = "An older LockLearn panel is still loaded in this browser. Perform a full browser reload before continuing.";
  const o = document.createElement("p");
  o.textContent = `loaded protocol ${s ?? "unknown"} · current protocol ${I}`;
  const n = document.createElement("button");
  n.textContent = "Reload now", n.addEventListener("click", () => globalThis.location?.reload()), t.append(i, a, o, n), e.append(t), document.body.append(e);
}
const Ls = customElements.get(
  "locklearn-panel"
), Ae = zs(Ls);
Ae.kind === "define" ? customElements.define("locklearn-panel", _) : Ae.kind === "reload" && Es(Ae.existingProtocol);
export {
  _ as LockLearnPanel
};
