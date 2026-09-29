const ne = globalThis, ke = ne.ShadowRoot && (ne.ShadyCSS === void 0 || ne.ShadyCSS.nativeShadow) && "adoptedStyleSheets" in Document.prototype && "replace" in CSSStyleSheet.prototype, we = /* @__PURE__ */ Symbol(), Ce = /* @__PURE__ */ new WeakMap();
let st = class {
  constructor(e, t, i) {
    if (this._$cssResult$ = !0, i !== we) throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");
    this.cssText = e, this.t = t;
  }
  get styleSheet() {
    let e = this.o;
    const t = this.t;
    if (ke && e === void 0) {
      const i = t !== void 0 && t.length === 1;
      i && (e = Ce.get(t)), e === void 0 && ((this.o = e = new CSSStyleSheet()).replaceSync(this.cssText), i && Ce.set(t, e));
    }
    return e;
  }
  toString() {
    return this.cssText;
  }
};
const yt = (s) => new st(typeof s == "string" ? s : s + "", void 0, we), M = (s, ...e) => {
  const t = s.length === 1 ? s[0] : e.reduce((i, a, n) => i + ((o) => {
    if (o._$cssResult$ === !0) return o.cssText;
    if (typeof o == "number") return o;
    throw Error("Value passed to 'css' function must be a 'css' function result: " + o + ". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.");
  })(a) + s[n + 1], s[0]);
  return new st(t, s, we);
}, $t = (s, e) => {
  if (ke) s.adoptedStyleSheets = e.map((t) => t instanceof CSSStyleSheet ? t : t.styleSheet);
  else for (const t of e) {
    const i = document.createElement("style"), a = ne.litNonce;
    a !== void 0 && i.setAttribute("nonce", a), i.textContent = t.cssText, s.appendChild(i);
  }
}, De = ke ? (s) => s : (s) => s instanceof CSSStyleSheet ? ((e) => {
  let t = "";
  for (const i of e.cssRules) t += i.cssText;
  return yt(t);
})(s) : s;
const { is: _t, defineProperty: kt, getOwnPropertyDescriptor: wt, getOwnPropertyNames: xt, getOwnPropertySymbols: St, getPrototypeOf: Tt } = Object, ue = globalThis, Ne = ue.trustedTypes, qt = Ne ? Ne.emptyScript : "", At = ue.reactiveElementPolyfillSupport, K = (s, e) => s, oe = { toAttribute(s, e) {
  switch (e) {
    case Boolean:
      s = s ? qt : null;
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
} }, xe = (s, e) => !_t(s, e), Re = { attribute: !0, type: String, converter: oe, reflect: !1, useDefault: !1, hasChanged: xe };
Symbol.metadata ??= /* @__PURE__ */ Symbol("metadata"), ue.litPropertyMetadata ??= /* @__PURE__ */ new WeakMap();
let H = class extends HTMLElement {
  static addInitializer(e) {
    this._$Ei(), (this.l ??= []).push(e);
  }
  static get observedAttributes() {
    return this.finalize(), this._$Eh && [...this._$Eh.keys()];
  }
  static createProperty(e, t = Re) {
    if (t.state && (t.attribute = !1), this._$Ei(), this.prototype.hasOwnProperty(e) && ((t = Object.create(t)).wrapped = !0), this.elementProperties.set(e, t), !t.noAccessor) {
      const i = /* @__PURE__ */ Symbol(), a = this.getPropertyDescriptor(e, i, t);
      a !== void 0 && kt(this.prototype, e, a);
    }
  }
  static getPropertyDescriptor(e, t, i) {
    const { get: a, set: n } = wt(this.prototype, e) ?? { get() {
      return this[t];
    }, set(o) {
      this[t] = o;
    } };
    return { get: a, set(o) {
      const c = a?.call(this);
      n?.call(this, o), this.requestUpdate(e, c, i);
    }, configurable: !0, enumerable: !0 };
  }
  static getPropertyOptions(e) {
    return this.elementProperties.get(e) ?? Re;
  }
  static _$Ei() {
    if (this.hasOwnProperty(K("elementProperties"))) return;
    const e = Tt(this);
    e.finalize(), e.l !== void 0 && (this.l = [...e.l]), this.elementProperties = new Map(e.elementProperties);
  }
  static finalize() {
    if (this.hasOwnProperty(K("finalized"))) return;
    if (this.finalized = !0, this._$Ei(), this.hasOwnProperty(K("properties"))) {
      const t = this.properties, i = [...xt(t), ...St(t)];
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
      for (const a of i) t.unshift(De(a));
    } else e !== void 0 && t.push(De(e));
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
    return $t(e, this.constructor.elementStyles), e;
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
      const n = (i.converter?.toAttribute !== void 0 ? i.converter : oe).toAttribute(t, i.type);
      this._$Em = e, n == null ? this.removeAttribute(a) : this.setAttribute(a, n), this._$Em = null;
    }
  }
  _$AK(e, t) {
    const i = this.constructor, a = i._$Eh.get(e);
    if (a !== void 0 && this._$Em !== a) {
      const n = i.getPropertyOptions(a), o = typeof n.converter == "function" ? { fromAttribute: n.converter } : n.converter?.fromAttribute !== void 0 ? n.converter : oe;
      this._$Em = a;
      const c = o.fromAttribute(t, n.type);
      this[a] = c ?? this._$Ej?.get(a) ?? c, this._$Em = null;
    }
  }
  requestUpdate(e, t, i, a = !1, n) {
    if (e !== void 0) {
      const o = this.constructor;
      if (a === !1 && (n = this[e]), i ??= o.getPropertyOptions(e), !((i.hasChanged ?? xe)(n, t) || i.useDefault && i.reflect && n === this._$Ej?.get(e) && !this.hasAttribute(o._$Eu(e, i)))) return;
      this.C(e, t, i);
    }
    this.isUpdatePending === !1 && (this._$ES = this._$EP());
  }
  C(e, t, { useDefault: i, reflect: a, wrapped: n }, o) {
    i && !(this._$Ej ??= /* @__PURE__ */ new Map()).has(e) && (this._$Ej.set(e, o ?? t ?? this[e]), n !== !0 || o !== void 0) || (this._$AL.has(e) || (this.hasUpdated || i || (t = void 0), this._$AL.set(e, t)), a === !0 && this._$Em !== e && (this._$Eq ??= /* @__PURE__ */ new Set()).add(e));
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
        for (const [a, n] of this._$Ep) this[a] = n;
        this._$Ep = void 0;
      }
      const i = this.constructor.elementProperties;
      if (i.size > 0) for (const [a, n] of i) {
        const { wrapped: o } = n, c = this[a];
        o !== !0 || this._$AL.has(a) || c === void 0 || this.C(a, void 0, n, c);
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
H.elementStyles = [], H.shadowRootOptions = { mode: "open" }, H[K("elementProperties")] = /* @__PURE__ */ new Map(), H[K("finalized")] = /* @__PURE__ */ new Map(), At?.({ ReactiveElement: H }), (ue.reactiveElementVersions ??= []).push("2.1.2");
const Se = globalThis, Le = (s) => s, le = Se.trustedTypes, Ie = le ? le.createPolicy("lit-html", { createHTML: (s) => s }) : void 0, rt = "$lit$", E = `lit$${Math.random().toFixed(9).slice(2)}$`, nt = "?" + E, zt = `<${nt}>`, N = document, G = () => N.createComment(""), J = (s) => s === null || typeof s != "object" && typeof s != "function", Te = Array.isArray, Pt = (s) => Te(s) || typeof s?.[Symbol.iterator] == "function", pe = `[ 	
\f\r]`, B = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, Ue = /-->/g, He = />/g, C = RegExp(`>|${pe}(?:([^\\s"'>=/]+)(${pe}*=${pe}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`, "g"), Oe = /'/g, je = /"/g, ot = /^(?:script|style|textarea|title)$/i, Et = (s) => (e, ...t) => ({ _$litType$: s, strings: e, values: t }), r = Et(1), O = /* @__PURE__ */ Symbol.for("lit-noChange"), l = /* @__PURE__ */ Symbol.for("lit-nothing"), We = /* @__PURE__ */ new WeakMap(), D = N.createTreeWalker(N, 129);
function lt(s, e) {
  if (!Te(s) || !s.hasOwnProperty("raw")) throw Error("invalid template strings array");
  return Ie !== void 0 ? Ie.createHTML(e) : e;
}
const Mt = (s, e) => {
  const t = s.length - 1, i = [];
  let a, n = e === 2 ? "<svg>" : e === 3 ? "<math>" : "", o = B;
  for (let c = 0; c < t; c++) {
    const u = s[c];
    let h, v, p = -1, z = 0;
    for (; z < u.length && (o.lastIndex = z, v = o.exec(u), v !== null); ) z = o.lastIndex, o === B ? v[1] === "!--" ? o = Ue : v[1] !== void 0 ? o = He : v[2] !== void 0 ? (ot.test(v[2]) && (a = RegExp("</" + v[2], "g")), o = C) : v[3] !== void 0 && (o = C) : o === C ? v[0] === ">" ? (o = a ?? B, p = -1) : v[1] === void 0 ? p = -2 : (p = o.lastIndex - v[2].length, h = v[1], o = v[3] === void 0 ? C : v[3] === '"' ? je : Oe) : o === je || o === Oe ? o = C : o === Ue || o === He ? o = B : (o = C, a = void 0);
    const P = o === C && s[c + 1].startsWith("/>") ? " " : "";
    n += o === B ? u + zt : p >= 0 ? (i.push(h), u.slice(0, p) + rt + u.slice(p) + E + P) : u + E + (p === -2 ? c : P);
  }
  return [lt(s, n + (s[t] || "<?>") + (e === 2 ? "</svg>" : e === 3 ? "</math>" : "")), i];
};
class Y {
  constructor({ strings: e, _$litType$: t }, i) {
    let a;
    this.parts = [];
    let n = 0, o = 0;
    const c = e.length - 1, u = this.parts, [h, v] = Mt(e, t);
    if (this.el = Y.createElement(h, i), D.currentNode = this.el.content, t === 2 || t === 3) {
      const p = this.el.content.firstChild;
      p.replaceWith(...p.childNodes);
    }
    for (; (a = D.nextNode()) !== null && u.length < c; ) {
      if (a.nodeType === 1) {
        if (a.hasAttributes()) for (const p of a.getAttributeNames()) if (p.endsWith(rt)) {
          const z = v[o++], P = a.getAttribute(p).split(E), ee = /([.?@])?(.*)/.exec(z);
          u.push({ type: 1, index: n, name: ee[2], strings: P, ctor: ee[1] === "." ? Dt : ee[1] === "?" ? Nt : ee[1] === "@" ? Rt : he }), a.removeAttribute(p);
        } else p.startsWith(E) && (u.push({ type: 6, index: n }), a.removeAttribute(p));
        if (ot.test(a.tagName)) {
          const p = a.textContent.split(E), z = p.length - 1;
          if (z > 0) {
            a.textContent = le ? le.emptyScript : "";
            for (let P = 0; P < z; P++) a.append(p[P], G()), D.nextNode(), u.push({ type: 2, index: ++n });
            a.append(p[z], G());
          }
        }
      } else if (a.nodeType === 8) if (a.data === nt) u.push({ type: 2, index: n });
      else {
        let p = -1;
        for (; (p = a.data.indexOf(E, p + 1)) !== -1; ) u.push({ type: 7, index: n }), p += E.length - 1;
      }
      n++;
    }
  }
  static createElement(e, t) {
    const i = N.createElement("template");
    return i.innerHTML = e, i;
  }
}
function j(s, e, t = s, i) {
  if (e === O) return e;
  let a = i !== void 0 ? t._$Co?.[i] : t._$Cl;
  const n = J(e) ? void 0 : e._$litDirective$;
  return a?.constructor !== n && (a?._$AO?.(!1), n === void 0 ? a = void 0 : (a = new n(s), a._$AT(s, t, i)), i !== void 0 ? (t._$Co ??= [])[i] = a : t._$Cl = a), a !== void 0 && (e = j(s, a._$AS(s, e.values), a, i)), e;
}
class Ct {
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
    const { el: { content: t }, parts: i } = this._$AD, a = (e?.creationScope ?? N).importNode(t, !0);
    D.currentNode = a;
    let n = D.nextNode(), o = 0, c = 0, u = i[0];
    for (; u !== void 0; ) {
      if (o === u.index) {
        let h;
        u.type === 2 ? h = new Z(n, n.nextSibling, this, e) : u.type === 1 ? h = new u.ctor(n, u.name, u.strings, this, e) : u.type === 6 && (h = new Lt(n, this, e)), this._$AV.push(h), u = i[++c];
      }
      o !== u?.index && (n = D.nextNode(), o++);
    }
    return D.currentNode = N, a;
  }
  p(e) {
    let t = 0;
    for (const i of this._$AV) i !== void 0 && (i.strings !== void 0 ? (i._$AI(e, i, t), t += i.strings.length - 2) : i._$AI(e[t])), t++;
  }
}
class Z {
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
    e = j(this, e, t), J(e) ? e === l || e == null || e === "" ? (this._$AH !== l && this._$AR(), this._$AH = l) : e !== this._$AH && e !== O && this._(e) : e._$litType$ !== void 0 ? this.$(e) : e.nodeType !== void 0 ? this.T(e) : Pt(e) ? this.k(e) : this._(e);
  }
  O(e) {
    return this._$AA.parentNode.insertBefore(e, this._$AB);
  }
  T(e) {
    this._$AH !== e && (this._$AR(), this._$AH = this.O(e));
  }
  _(e) {
    this._$AH !== l && J(this._$AH) ? this._$AA.nextSibling.data = e : this.T(N.createTextNode(e)), this._$AH = e;
  }
  $(e) {
    const { values: t, _$litType$: i } = e, a = typeof i == "number" ? this._$AC(e) : (i.el === void 0 && (i.el = Y.createElement(lt(i.h, i.h[0]), this.options)), i);
    if (this._$AH?._$AD === a) this._$AH.p(t);
    else {
      const n = new Ct(a, this), o = n.u(this.options);
      n.p(t), this.T(o), this._$AH = n;
    }
  }
  _$AC(e) {
    let t = We.get(e.strings);
    return t === void 0 && We.set(e.strings, t = new Y(e)), t;
  }
  k(e) {
    Te(this._$AH) || (this._$AH = [], this._$AR());
    const t = this._$AH;
    let i, a = 0;
    for (const n of e) a === t.length ? t.push(i = new Z(this.O(G()), this.O(G()), this, this.options)) : i = t[a], i._$AI(n), a++;
    a < t.length && (this._$AR(i && i._$AB.nextSibling, a), t.length = a);
  }
  _$AR(e = this._$AA.nextSibling, t) {
    for (this._$AP?.(!1, !0, t); e !== this._$AB; ) {
      const i = Le(e).nextSibling;
      Le(e).remove(), e = i;
    }
  }
  setConnected(e) {
    this._$AM === void 0 && (this._$Cv = e, this._$AP?.(e));
  }
}
class he {
  get tagName() {
    return this.element.tagName;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  constructor(e, t, i, a, n) {
    this.type = 1, this._$AH = l, this._$AN = void 0, this.element = e, this.name = t, this._$AM = a, this.options = n, i.length > 2 || i[0] !== "" || i[1] !== "" ? (this._$AH = Array(i.length - 1).fill(new String()), this.strings = i) : this._$AH = l;
  }
  _$AI(e, t = this, i, a) {
    const n = this.strings;
    let o = !1;
    if (n === void 0) e = j(this, e, t, 0), o = !J(e) || e !== this._$AH && e !== O, o && (this._$AH = e);
    else {
      const c = e;
      let u, h;
      for (e = n[0], u = 0; u < n.length - 1; u++) h = j(this, c[i + u], t, u), h === O && (h = this._$AH[u]), o ||= !J(h) || h !== this._$AH[u], h === l ? e = l : e !== l && (e += (h ?? "") + n[u + 1]), this._$AH[u] = h;
    }
    o && !a && this.j(e);
  }
  j(e) {
    e === l ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, e ?? "");
  }
}
class Dt extends he {
  constructor() {
    super(...arguments), this.type = 3;
  }
  j(e) {
    this.element[this.name] = e === l ? void 0 : e;
  }
}
class Nt extends he {
  constructor() {
    super(...arguments), this.type = 4;
  }
  j(e) {
    this.element.toggleAttribute(this.name, !!e && e !== l);
  }
}
class Rt extends he {
  constructor(e, t, i, a, n) {
    super(e, t, i, a, n), this.type = 5;
  }
  _$AI(e, t = this) {
    if ((e = j(this, e, t, 0) ?? l) === O) return;
    const i = this._$AH, a = e === l && i !== l || e.capture !== i.capture || e.once !== i.once || e.passive !== i.passive, n = e !== l && (i === l || a);
    a && this.element.removeEventListener(this.name, this, i), n && this.element.addEventListener(this.name, this, e), this._$AH = e;
  }
  handleEvent(e) {
    typeof this._$AH == "function" ? this._$AH.call(this.options?.host ?? this.element, e) : this._$AH.handleEvent(e);
  }
}
class Lt {
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
const It = Se.litHtmlPolyfillSupport;
It?.(Y, Z), (Se.litHtmlVersions ??= []).push("3.3.3");
const Ut = (s, e, t) => {
  const i = t?.renderBefore ?? e;
  let a = i._$litPart$;
  if (a === void 0) {
    const n = t?.renderBefore ?? null;
    i._$litPart$ = a = new Z(e.insertBefore(G(), n), n, void 0, t ?? {});
  }
  return a._$AI(s), a;
};
const qe = globalThis;
class q extends H {
  constructor() {
    super(...arguments), this.renderOptions = { host: this }, this._$Do = void 0;
  }
  createRenderRoot() {
    const e = super.createRenderRoot();
    return this.renderOptions.renderBefore ??= e.firstChild, e;
  }
  update(e) {
    const t = this.render();
    this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(e), this._$Do = Ut(t, this.renderRoot, this.renderOptions);
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
q._$litElement$ = !0, q.finalized = !0, qe.litElementHydrateSupport?.({ LitElement: q });
const Ht = qe.litElementPolyfillSupport;
Ht?.({ LitElement: q });
(qe.litElementVersions ??= []).push("4.2.2");
const Ot = { attribute: !0, type: String, converter: oe, reflect: !1, hasChanged: xe }, jt = (s = Ot, e, t) => {
  const { kind: i, metadata: a } = t;
  let n = globalThis.litPropertyMetadata.get(a);
  if (n === void 0 && globalThis.litPropertyMetadata.set(a, n = /* @__PURE__ */ new Map()), i === "setter" && ((s = Object.create(s)).wrapped = !0), n.set(t.name, s), i === "accessor") {
    const { name: o } = t;
    return { set(c) {
      const u = e.get.call(this);
      e.set.call(this, c), this.requestUpdate(o, u, s, !0, c);
    }, init(c) {
      return c !== void 0 && this.C(o, void 0, s, c), c;
    } };
  }
  if (i === "setter") {
    const { name: o } = t;
    return function(c) {
      const u = this[o];
      e.call(this, c), this.requestUpdate(o, u, s, !0, c);
    };
  }
  throw Error("Unsupported decorator location: " + i);
};
function $(s) {
  return (e, t) => typeof t == "object" ? jt(s, e, t) : ((i, a, n) => {
    const o = a.hasOwnProperty(n);
    return a.constructor.createProperty(n, i), o ? Object.getOwnPropertyDescriptor(a, n) : void 0;
  })(s, e, t);
}
function d(s) {
  return $({ ...s, state: !0, attribute: !1 });
}
const ct = M`
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
`, W = M`
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
function Wt(s, e) {
  const t = s.ruby_segments;
  if (!Array.isArray(t) || t.length === 0) return null;
  const i = [];
  for (const a of t) {
    if (typeof a != "object" || a === null) return null;
    const n = a;
    if (typeof n.text != "string" || n.text === "") return null;
    const o = n.reading === void 0 || n.reading === null ? null : typeof n.reading == "string" && n.reading !== "" ? n.reading : void 0;
    if (o === void 0) return null;
    i.push({ text: n.text, reading: o });
  }
  return i.map((a) => a.text).join("") !== e ? null : i;
}
function Ft(s) {
  return r`${s.map(
    (e) => e.reading === null ? e.text : r`<ruby>${e.text}<rp>(</rp><rt>${e.reading}</rt><rp>)</rp></ruby>`
  )}`;
}
function dt(s, e = 0) {
  if (e > 16 || typeof s != "object" || s === null) return l;
  const t = s;
  if ((t.type === "text" || t.type === "inline_code") && typeof t.text == "string")
    return t.type === "inline_code" ? r`<code>${t.text}</code>` : t.text;
  if (t.type === "line_break") return r`<br />`;
  if (t.type === "ruby" && typeof t.text == "string" && t.text !== "" && typeof t.reading == "string" && t.reading !== "")
    return r`<ruby>${t.text}<rp>(</rp><rt>${t.reading}</rt><rp>)</rp></ruby>`;
  if ((t.type === "paragraph" || t.type === "emphasis" || t.type === "strong") && Array.isArray(t.children)) {
    const i = t.children.map((a) => dt(a, e + 1));
    return t.type === "paragraph" ? r`<p>${i}</p>` : t.type === "emphasis" ? r`<em>${i}</em>` : r`<strong>${i}</strong>`;
  }
  return l;
}
function Vt(s) {
  const e = s.payload.text;
  if (typeof e == "string" && e !== "") {
    const t = Wt(s.payload, e);
    return t === null ? e : Ft(t);
  }
  return s.kind === "rich_text" && s.payload.type === "document" && Array.isArray(s.payload.children) ? r`${s.payload.children.map((t) => dt(t, 1))}` : l;
}
function ut(s, e = !1) {
  const t = Vt(s);
  return t === l ? l : r`
    <div
      class="content-block ${e ? "primary-content" : ""}"
      lang=${s.language_tag ?? l}
    >
      ${t}
    </div>
  `;
}
const Fe = ["en", "fr"], Ve = {
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
    "learn.pauseTitle": "Learning pause",
    "learn.readiness": "Learning availability",
    "learn.cardsReady": "cards available now",
    "learn.noCardsReady": "No card is due within the normal learning plan right now.",
    "learn.overrideNewHelp": "Your daily new-card target has been reached, but you can deliberately continue with more new cards. Failed and relearning cards still keep their required cooldown.",
    "learn.emptyExplain": "Nothing is due right now. LockLearn spaces recalls so you do not simply repeat from short-term memory.",
    "learn.nextAvailable": "Next scheduled step",
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
    "quiz.notReadyTitle": "No quiz due right now",
    "quiz.howItWorks": "Quiz readiness",
    "quiz.cardsReady": "cards ready now",
    "quiz.learnFirst": "A quiz tests cards you have already learned. Start with Learn to introduce some cards first.",
    "quiz.emptyExplain": "You have learned cards, but none has reached its scheduled quiz/review time yet.",
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
    "manage.plan": "Learning plan",
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
    "learn.pauseTitle": "Pause d’apprentissage",
    "learn.readiness": "Disponibilité de l’apprentissage",
    "learn.cardsReady": "cartes disponibles maintenant",
    "learn.noCardsReady": "Aucune carte n’est disponible dans le plan d’apprentissage normal pour le moment.",
    "learn.overrideNewHelp": "Votre objectif quotidien de nouvelles cartes est atteint, mais vous pouvez choisir de continuer avec davantage de nouvelles cartes. Les cartes ratées et en réapprentissage conservent toujours leur délai obligatoire.",
    "learn.emptyExplain": "Rien n’est à revoir maintenant. LockLearn espace les rappels pour éviter de simplement répéter depuis la mémoire à court terme.",
    "learn.nextAvailable": "Prochaine étape prévue",
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
    "quiz.notReadyTitle": "Aucun quiz à faire pour le moment",
    "quiz.howItWorks": "Disponibilité du quiz",
    "quiz.cardsReady": "cartes disponibles maintenant",
    "quiz.learnFirst": "Le quiz teste des cartes déjà apprises. Commencez par Apprendre pour introduire quelques cartes.",
    "quiz.emptyExplain": "Vous avez déjà appris des cartes, mais aucune n’a encore atteint son heure prévue de quiz ou de révision.",
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
    "manage.plan": "Plan de charge",
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
function F(s) {
  const e = s.trim().toLowerCase().replaceAll("_", "-");
  if (Fe.includes(e))
    return e;
  const t = e.split("-", 1)[0];
  return Fe.includes(t) ? t : "en";
}
function V(s, e) {
  return Ve[s][e] ?? Ve.en[e];
}
function Bt(s) {
  return s?.payload.selection?.progress_state === "new";
}
function Qt(s) {
  const e = s?.payload.available_at_utc;
  if (typeof e != "string") return null;
  const t = Date.parse(e);
  return Number.isNaN(t) ? null : t;
}
function Be(s) {
  return s !== void 0 && s.role !== "viewer";
}
const R = 3;
class ht extends Error {
  constructor(e, t, i) {
    super(
      `LockLearn frontend protocol ${e} does not match backend protocol ${t}`
    ), this.frontendProtocol = e, this.backendProtocol = t, this.backendVersion = i;
  }
}
async function Kt(s) {
  const e = await s.callWS({
    type: "locklearn/bootstrap"
  });
  if (e.frontend_protocol !== R)
    throw new ht(
      R,
      e.frontend_protocol,
      e.backend_version
    );
  return e;
}
async function Qe(s) {
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
async function X(s, e, t = {}) {
  const i = [];
  let a = null;
  do {
    const n = await s.callWS({
      type: e,
      limit: 100,
      ...t,
      ...a === null ? {} : { cursor: a }
    });
    i.push(...n.items), a = n.cursor;
  } while (a !== null);
  return i;
}
async function Gt(s, e, t, i) {
  return s.callWS({
    type: "locklearn/profiles/create",
    name: e,
    preset: t,
    timezone: i
  });
}
async function Ke(s, e, t) {
  return s.callWS({
    type: "locklearn/profiles/update",
    profile_id: e,
    ...t
  });
}
async function Ge(s, e, t, i) {
  await s.callWS({
    type: "locklearn/profiles/delete",
    profile_id: e,
    action: t,
    ...i === void 0 ? {} : { confirmation: i }
  });
}
async function Jt(s, e) {
  return s.callWS({
    type: "locklearn/profiles/members",
    profile_id: e
  });
}
async function Yt(s, e) {
  return s.callWS({
    type: "locklearn/profiles/share_targets",
    profile_id: e
  });
}
async function Je(s, e, t, i) {
  await s.callWS({
    type: "locklearn/profiles/share",
    profile_id: e,
    target_user_id: t,
    role: i
  });
}
async function Zt(s, e, t) {
  await s.callWS({
    type: "locklearn/profiles/share",
    profile_id: e,
    target_user_id: t,
    remove: !0
  });
}
async function pt(s, e) {
  return X(s, "locklearn/tracks/list", {
    profile_id: e
  });
}
async function Xt(s, e) {
  return X(s, "locklearn/targets/list", {
    profile_id: e
  });
}
async function ei(s, e) {
  return X(s, "locklearn/targets/discover", {
    profile_id: e
  });
}
async function ti(s, e, t) {
  return s.callWS({
    type: "locklearn/targets/create",
    profile_id: e,
    device_registry_id: t
  });
}
async function ii(s, e, t, i) {
  return s.callWS({
    type: "locklearn/targets/update",
    profile_id: e,
    target_id: t,
    ...i
  });
}
async function ai(s, e, t) {
  return s.callWS({
    type: "locklearn/targets/test",
    profile_id: e,
    target_id: t
  });
}
async function si(s, e, t) {
  return s.callWS({
    type: "locklearn/stats/get",
    profile_id: e,
    recent_verified_limit: 30,
    calibration_days: 7,
    confusion_limit: 20,
    ...t ? { track_id: t } : {}
  });
}
async function ri(s, e, t) {
  return (await s.callWS({
    type: "locklearn/difficulties/list",
    profile_id: e,
    ...t ? { track_id: t } : {}
  })).items;
}
async function ni(s, e) {
  return s.callWS({
    type: "locklearn/tracks/create",
    ...e
  });
}
async function oi(s, e, t) {
  return s.callWS({
    type: "locklearn/tracks/update",
    track_id: e,
    ...t
  });
}
async function li(s, e) {
  await s.callWS({
    type: "locklearn/tracks/delete",
    track_id: e
  });
}
async function ci(s) {
  return X(s, "locklearn/packs/list");
}
async function di(s) {
  return X(s, "locklearn/datasets/list");
}
async function Ye(s, e, t, i) {
  return s.callWS({
    type: "locklearn/datasets/attributions",
    dataset_id: e,
    source_id: t,
    limit: 50,
    ...i ? { cursor: i } : {}
  });
}
async function ui(s) {
  return (await s.callWS({
    type: "locklearn/datasets/refresh"
  })).items;
}
async function hi(s, e, t) {
  return s.callWS({
    type: "locklearn/datasets/install",
    dataset_id: e,
    ...t ? { version: t } : {}
  });
}
async function pi(s, e, t) {
  return s.callWS({
    type: "locklearn/tracks/preview_pack_update",
    track_id: e,
    pack_version_id: t
  });
}
async function gi(s, e, t) {
  return s.callWS({
    type: "locklearn/tracks/integrate_pack_update",
    track_id: e,
    pack_version_id: t
  });
}
function gt(s, e, t) {
  return {
    type: s,
    track_id: e,
    ...t
  };
}
async function mi(s, e, t) {
  return s.callWS(
    gt("locklearn/tracks/plan_preview", e, t)
  );
}
async function fi(s, e, t) {
  return s.callWS(
    gt("locklearn/tracks/plan_set", e, t)
  );
}
async function vi(s, e) {
  return s.callWS({
    type: "locklearn/dashboard/get",
    profile_id: e
  });
}
async function mt(s, e, t, i, a = {}) {
  return s.callWS({
    type: "locklearn/session/availability",
    profile_id: e,
    track_id: t,
    session_type: i,
    settings: a
  });
}
async function bi(s, e, t, i, a = "mixed") {
  return s.callWS({
    type: "locklearn/session/start",
    profile_id: e,
    track_id: t,
    session_type: "quiz",
    strategy: "default",
    settings: {
      ...i === void 0 ? {} : { requested_cards: i },
      quiz_format: a,
      option_count: 4
    }
  });
}
async function ge(s, e, t, i) {
  return s.callWS({
    type: "locklearn/quiz/answer",
    session_id: e.id,
    expected_version: e.version,
    question_id: t,
    answer: i
  });
}
async function yi(s, e, t, i) {
  return s.callWS({
    type: "locklearn/quiz/evaluate",
    session_id: e,
    question_id: t,
    answer: i
  });
}
async function $i(s, e, t, i, a) {
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
async function _i(s, e, t, i, a = !1) {
  return s.callWS({
    type: "locklearn/session/start",
    profile_id: e,
    track_id: t,
    session_type: "learn",
    strategy: "default",
    settings: {
      ...i === void 0 ? {} : { requested_cards: i },
      ...a ? { allow_early_learning: !0 } : {}
    }
  });
}
async function ce(s, e) {
  return s.callWS({
    type: "locklearn/session/get",
    session_id: e
  });
}
async function Ze(s, e, t, i) {
  return s.callWS({
    type: "locklearn/session/answer",
    session_id: e.id,
    expected_version: e.version,
    question_id: t,
    answer: i
  });
}
async function ft(s, e) {
  return s.callWS({
    type: "locklearn/session/complete",
    session_id: e.id,
    expected_version: e.version
  });
}
async function ki(s, e, t, i, a) {
  return s.callWS({
    type: "locklearn/progress/set_user_state",
    profile_id: e,
    track_id: t,
    card_key: i,
    user_state: a
  });
}
async function vt(s, e, t, i, a) {
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
async function bt(s, e, t, i) {
  return s.callWS({
    type: "locklearn/annotations/create",
    profile_id: e,
    card_key: t,
    note: i.trim()
  });
}
async function wi(s, e, t, i) {
  return s.callWS({
    type: "locklearn/annotations/update",
    profile_id: e,
    annotation_id: t,
    note: i.trim()
  });
}
async function xi(s, e, t, i) {
  return s.callWS({
    type: "locklearn/leeches/reactivate",
    profile_id: e,
    track_id: t,
    card_key: i
  });
}
async function Si(s, e, t, i = 20) {
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
var Ti = Object.defineProperty, y = (s, e, t, i) => {
  for (var a = void 0, n = s.length - 1, o; n >= 0; n--)
    (o = s[n]) && (a = o(e, t, a) || a);
  return a && Ti(e, t, a), a;
};
function Q() {
  return globalThis.performance?.now() ?? Date.now();
}
const Ae = class Ae extends q {
  constructor() {
    super(...arguments), this.trackId = "", this.loading = !1, this.errorMessage = "", this.notice = "", this.revealed = !1, this.hintUsed = !1, this.pendingIdk = !1, this.mnemonic = "", this.reportMessage = "", this.forceEarlyCurrent = !1, this.questionStartedAt = Q(), this.questionId = null;
  }
  disconnectedCallback() {
    this.clearAvailabilityTimer(), this.nextDueTimer !== void 0 && globalThis.clearTimeout(this.nextDueTimer), super.disconnectedCallback();
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
    return F(e);
  }
  t(e) {
    return V(this.locale(), e);
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
    this.clearAvailabilityTimer(), this.waitingUntil = void 0, this.revealed = !1, this.hintUsed = !1, this.pendingIdk = !1, this.pendingIdkLatency = void 0, this.mnemonic = "", this.reportMessage = "", this.notice = "", this.forceEarlyCurrent = !1, this.questionStartedAt = Q(), this.questionId = this.session?.current_question?.question_id ?? null;
  }
  clearAvailabilityTimer() {
    this.availabilityTimer !== void 0 && (globalThis.clearTimeout(this.availabilityTimer), this.availabilityTimer = void 0);
  }
  scheduleCurrentQuestionAvailability() {
    const e = Qt(this.session?.current_question);
    e === null || e <= Date.now() || (this.waitingUntil = new Date(e).toISOString(), this.availabilityTimer = globalThis.setTimeout(() => {
      this.availabilityTimer = void 0, this.waitingUntil = void 0, this.questionStartedAt = Q();
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
      this.availability = await mt(
        this.hass,
        this.profile.profile_id,
        this.trackId,
        "learn"
      ), this.nextDueTimer !== void 0 && globalThis.clearTimeout(this.nextDueTimer);
      const e = this.availability.next_due_at_utc;
      if (e !== null) {
        const t = Date.parse(e) - Date.now();
        t > 0 && t < 2147e6 && (this.nextDueTimer = globalThis.setTimeout(() => {
          this.nextDueTimer = void 0, this.refreshAvailability();
        }, t + 250));
      }
    } catch {
      this.availability = void 0;
    }
  }
  dueLabel(e) {
    if (e === null) return "";
    const t = new Date(e);
    if (Number.isNaN(t.getTime())) return "";
    const i = Math.max(1, Math.ceil((t.getTime() - Date.now()) / 6e4));
    return `${new Intl.DateTimeFormat(this.locale(), { timeStyle: "short" }).format(t)} · ${this.t("learn.inAbout")} ${i} min`;
  }
  continueCurrentEarly() {
    this.clearAvailabilityTimer(), this.waitingUntil = void 0, this.forceEarlyCurrent = !0, this.questionStartedAt = Q();
  }
  elapsedMs() {
    return Math.max(0, Math.round(Q() - this.questionStartedAt));
  }
  async start(e = !1) {
    if (!(this.hass === void 0 || this.profile === void 0 || this.trackId === "" || !Be(this.profile))) {
      this.loading = !0, this.errorMessage = "", this.notice = "";
      try {
        const t = await _i(
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
    if (!(this.hass === void 0 || e === null || e === void 0)) {
      this.loading = !0, this.errorMessage = "";
      try {
        this.applySession(await ce(this.hass, e.session_id));
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
        this.applySession(await ce(this.hass, this.session.id)), this.notice = this.t("learn.reloaded");
        return;
      } catch {
      }
    this.errorMessage = e instanceof Error ? e.message : String(e);
  }
  async finalizeIfDone(e) {
    return this.hass !== void 0 && e.status === "active" && e.current_question === null && e.question_count > 0 ? ft(this.hass, e) : e;
  }
  async learningAction(e, t) {
    const i = this.session?.current_question;
    if (!(this.hass === void 0 || this.session === void 0 || i === null || i === void 0)) {
      this.loading = !0, this.errorMessage = "";
      try {
        const a = await Ze(
          this.hass,
          this.session,
          i.question_id,
          {
            kind: "learning",
            action: e,
            hint_used: this.hintUsed,
            presentation_to_answer_ms: t ?? this.elapsedMs(),
            ...this.forceEarlyCurrent ? { force_early: !0 } : {}
          }
        );
        this.applySession(await this.finalizeIfDone(a));
      } catch (a) {
        await this.recover(a);
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
        await ki(
          this.hass,
          this.profile.profile_id,
          this.session.track_id,
          t.card_key,
          e
        );
        const i = await Ze(
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
        await vt(
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
        await bt(
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
    if (!Be(this.profile))
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
      (a) => r`
                  <option value=${a.track_id}>
                    ${a.name} · ${a.source_language} → ${a.target_language}
                  </option>
                `
    )}
            </select>
          </label>
          <div class="actions">
            ${i ? r`<button @click=${this.resume} ?disabled=${this.loading}>
                  ${this.t("learn.resume")}
                </button>` : l}
            <button class="primary" @click=${() => {
      this.start();
    }} ?disabled=${this.loading}>
              ${this.t("learn.start")}
            </button>
          </div>
        </div>
        ${this.session === void 0 && this.availability !== void 0 ? r`
          <div class="notice" role="status">
            <strong>${this.t("learn.readiness")}</strong>
            ${this.availability.available_now > 0 ? r`<div>${this.availability.available_now} ${this.t("learn.cardsReady")}</div>` : r`
                  <div>${this.t("learn.noCardsReady")}</div>
                  ${this.availability.next_due_at_utc === null ? l : r`
                    <div>
                      <strong>${this.t("learn.nextAvailable")}:</strong>
                      ${this.dueLabel(this.availability.next_due_at_utc)}
                    </div>
                  `}
                  ${this.availability.forceable_early > 0 ? r`
                    <p class="muted">
                      ${this.availability.forceable_new > 0 ? this.t("learn.overrideNewHelp") : this.t("learn.continueEarlyHelp")}
                    </p>
                    <button class="primary" @click=${() => {
      this.start(!0);
    }} ?disabled=${this.loading}>
                      ${this.t("learn.continueNow")}
                    </button>
                  ` : l}
                `}
          </div>
        ` : l}
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
    if (this.session === void 0) return l;
    if (this.session.question_count === 0) {
      const e = this.availability?.next_due_at_utc ?? null, t = (this.availability?.forceable_early ?? 0) > 0;
      return r`
        <section class="learn-card">
          <h2>${this.t("learn.pauseTitle")}</h2>
          <p>${this.t("learn.emptyExplain")}</p>
          ${e === null ? l : r`
            <p><strong>${this.t("learn.nextAvailable")}:</strong> ${this.dueLabel(e)}</p>
          `}
          ${t ? r`
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
    return this.session.current_question === null || this.session.status === "completed" ? r`
        <section class="learn-card">
          <h2>${this.t("learn.completed")}</h2>
          <p>${this.t("learn.completedBody")}</p>
          <button class="primary" @click=${() => {
      this.start();
    }} ?disabled=${this.loading}>
            ${this.t("learn.newSession")}
          </button>
        </section>
      ` : this.waitingUntil !== void 0 ? this.renderWaiting(this.session.current_question) : Bt(this.session.current_question) ? this.renderIntroduction(this.session.current_question) : this.renderRetrieval(this.session.current_question);
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
      (a) => a.blocks.map((n) => this.renderBlock(n, !1))
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
        ${i.map((a) => this.renderBlock(a, !1))}
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
    return ut(e, t);
  }
};
Ae.styles = M`
    ${ct}
    ${W}

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
let m = Ae;
y([
  $({ attribute: !1 })
], m.prototype, "hass");
y([
  $({ attribute: !1 })
], m.prototype, "profile");
y([
  $({ attribute: !1 })
], m.prototype, "dashboard");
y([
  $({ attribute: !1 })
], m.prototype, "externalSession");
y([
  d()
], m.prototype, "trackId");
y([
  d()
], m.prototype, "session");
y([
  d()
], m.prototype, "loading");
y([
  d()
], m.prototype, "errorMessage");
y([
  d()
], m.prototype, "notice");
y([
  d()
], m.prototype, "revealed");
y([
  d()
], m.prototype, "hintUsed");
y([
  d()
], m.prototype, "pendingIdk");
y([
  d()
], m.prototype, "pendingIdkLatency");
y([
  d()
], m.prototype, "mnemonic");
y([
  d()
], m.prototype, "reportMessage");
y([
  d()
], m.prototype, "waitingUntil");
y([
  d()
], m.prototype, "availability");
y([
  d()
], m.prototype, "forceEarlyCurrent");
globalThis.customElements !== void 0 && customElements.get("locklearn-learn-view") === void 0 && customElements.define("locklearn-learn-view", m);
function Xe(s) {
  return s !== void 0 && s.role !== "viewer";
}
function qi(s) {
  return s?.payload.quiz;
}
function Ai(s) {
  return s?.format === "mcq" || s?.format === "cloze_mcq";
}
function et(s) {
  return s?.format === "free_text" && s.result === "wrong" && s.reportable && typeof s.submitted_text == "string" && s.grading_policy_kind !== void 0 && s.grading_policy_version !== void 0 && s.normalization_version !== void 0;
}
var zi = Object.defineProperty, _ = (s, e, t, i) => {
  for (var a = void 0, n = s.length - 1, o; n >= 0; n--)
    (o = s[n]) && (a = o(e, t, a) || a);
  return a && zi(e, t, a), a;
};
function me() {
  return globalThis.performance?.now() ?? Date.now();
}
const ze = class ze extends q {
  constructor() {
    super(...arguments), this.trackId = "", this.format = "mixed", this.loading = !1, this.errorMessage = "", this.notice = "", this.freeText = "", this.hintUsed = !1, this.questionStartedAt = me(), this.questionId = null;
  }
  updated(e) {
    if (e.has("profile") || e.has("dashboard")) {
      const t = this.tracks();
      t.some((i) => i.track_id === this.trackId) || (this.trackId = t[0]?.track_id ?? ""), e.has("profile") && (this.session = void 0, this.resetQuestionUi()), this.refreshAvailability();
    }
  }
  locale() {
    const e = this.hass?.locale?.language ?? this.hass?.language ?? globalThis.navigator?.language ?? "en";
    return F(e);
  }
  t(e) {
    return V(this.locale(), e);
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
    this.feedback = void 0, this.pendingAnswer = void 0, this.pendingSession = void 0, this.freeText = "", this.hintUsed = !1, this.notice = "", this.questionStartedAt = me(), this.questionId = this.session?.current_question?.question_id ?? null;
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
      this.availability = await mt(
        this.hass,
        this.profile.profile_id,
        this.trackId,
        "quiz"
      );
    } catch {
      this.availability = void 0;
    }
  }
  dueLabel(e) {
    if (e === null) return "";
    const t = new Date(e);
    if (Number.isNaN(t.getTime())) return "";
    const i = Math.max(1, Math.ceil((t.getTime() - Date.now()) / 6e4));
    return `${new Intl.DateTimeFormat(this.locale(), { timeStyle: "short" }).format(t)} · ${this.t("quiz.inAbout")} ${i} min`;
  }
  elapsedMs() {
    return Math.max(0, Math.round(me() - this.questionStartedAt));
  }
  async start() {
    if (!(this.hass === void 0 || this.profile === void 0 || this.trackId === "" || !Xe(this.profile))) {
      this.loading = !0, this.errorMessage = "";
      try {
        this.applySession(
          await bi(
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
    if (!(this.hass === void 0 || e === null || e === void 0 || e.session_type !== "quiz")) {
      this.loading = !0, this.errorMessage = "";
      try {
        this.applySession(await ce(this.hass, e.session_id));
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
        this.applySession(await ce(this.hass, this.session.id)), this.notice = this.t("quiz.reloaded");
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
      this.feedback = await yi(
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
    const i = this.enrichAnswer(e);
    this.loading = !0, this.errorMessage = "";
    try {
      const a = await ge(
        this.hass,
        this.session,
        t.question_id,
        i
      );
      this.feedback = a.feedback, this.pendingAnswer = void 0, this.pendingSession = a.session;
    } catch (a) {
      await this.recover(a);
    } finally {
      this.loading = !1;
    }
  }
  async submitProvisional() {
    const e = this.session?.current_question;
    if (!(this.hass === void 0 || this.session === void 0 || e === null || e === void 0 || this.pendingAnswer === void 0)) {
      this.loading = !0, this.errorMessage = "";
      try {
        const t = await ge(
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
    this.hass !== void 0 && t.status === "active" && t.current_question === null && t.question_count > 0 && (t = await ft(this.hass, t)), this.applySession(t);
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
    if (!(this.hass === void 0 || this.profile === void 0 || this.session === void 0 || this.session.track_id === null || e === null || e === void 0 || this.feedback === void 0 || this.pendingAnswer === void 0 || !et(this.feedback))) {
      this.loading = !0, this.errorMessage = "";
      try {
        if ((await $i(
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
        }, a = await ge(
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
        await vt(
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
    if (!Xe(this.profile))
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
      (a) => r`
                    <option value=${a.track_id}>
                      ${a.name} · ${a.source_language} → ${a.target_language}
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
            <button class="primary" @click=${() => {
      this.start();
    }} ?disabled=${this.loading}>
              ${this.t("quiz.start")}
            </button>
          </div>
        </div>
        ${this.session === void 0 && this.availability !== void 0 ? r`
          <div class="notice" role="status">
            <strong>${this.t("quiz.howItWorks")}</strong>
            ${this.availability.available_now > 0 ? r`<div>${this.availability.available_now} ${this.t("quiz.cardsReady")}</div>` : this.availability.introduced_cards === 0 ? r`<div>${this.t("quiz.learnFirst")}</div>` : r`
                    <div>${this.t("quiz.emptyExplain")}</div>
                    ${this.availability.next_due_at_utc === null ? l : r`
                      <div>
                        <strong>${this.t("quiz.nextAvailable")}:</strong>
                        ${this.dueLabel(this.availability.next_due_at_utc)}
                      </div>
                    `}
                  `}
            <div class="muted">${this.t("quiz.whyDueOnly")}</div>
          </div>
        ` : l}
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
    if (this.session.question_count === 0) {
      const t = this.availability?.introduced_cards ?? 0, i = this.availability?.next_due_at_utc ?? null;
      return r`
        <section class="quiz-card">
          <h2>${this.t("quiz.notReadyTitle")}</h2>
          <p>
            ${t === 0 ? this.t("quiz.learnFirst") : this.t("quiz.emptyExplain")}
          </p>
          ${i === null ? l : r`
            <p><strong>${this.t("quiz.nextAvailable")}:</strong> ${this.dueLabel(i)}</p>
          `}
          <p class="muted">${this.t("quiz.whyDueOnly")}</p>
        </section>
      `;
    }
    if (this.session.current_question === null || this.session.status === "completed")
      return r`
        <section class="quiz-card">
          <h2>${this.t("quiz.completed")}</h2>
          <p>${this.t("quiz.completedBody")}</p>
          <button class="primary" @click=${() => {
        this.start();
      }} ?disabled=${this.loading}>
            ${this.t("quiz.newSession")}
          </button>
        </section>
      `;
    const e = qi(this.session.current_question);
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
    return Ai(e) ? r`
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
          ${et(t) ? r`<button
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
    return ut(e);
  }
};
ze.styles = M`
    ${ct}
    ${W}

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
let b = ze;
_([
  $({ attribute: !1 })
], b.prototype, "hass");
_([
  $({ attribute: !1 })
], b.prototype, "profile");
_([
  $({ attribute: !1 })
], b.prototype, "dashboard");
_([
  d()
], b.prototype, "trackId");
_([
  d()
], b.prototype, "format");
_([
  d()
], b.prototype, "session");
_([
  d()
], b.prototype, "loading");
_([
  d()
], b.prototype, "errorMessage");
_([
  d()
], b.prototype, "notice");
_([
  d()
], b.prototype, "feedback");
_([
  d()
], b.prototype, "pendingAnswer");
_([
  d()
], b.prototype, "pendingSession");
_([
  d()
], b.prototype, "freeText");
_([
  d()
], b.prototype, "hintUsed");
_([
  d()
], b.prototype, "availability");
globalThis.customElements !== void 0 && customElements.get("locklearn-quiz-view") === void 0 && customElements.define("locklearn-quiz-view", b);
var Pi = Object.defineProperty, f = (s, e, t, i) => {
  for (var a = void 0, n = s.length - 1, o; n >= 0; n--)
    (o = s[n]) && (a = o(e, t, a) || a);
  return a && Pi(e, t, a), a;
};
function T(s, e, t) {
  const i = Number.parseInt(String(s ?? ""), 10);
  return Number.isFinite(i) && i >= t ? i : e;
}
function fe(s, e) {
  const t = String(s ?? "").trim();
  if (t === "") return null;
  const i = Number.parseInt(t, 10);
  return Number.isFinite(i) && i >= e ? i : null;
}
function I(s, e, t, i) {
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
function U(s, e) {
  if (s === "ja-Latn")
    return e === "fr" ? "Japonais (rōmaji)" : "Japanese (romaji)";
  try {
    const t = s.split("-", 1)[0] ?? s;
    return new Intl.DisplayNames([e], { type: "language" }).of(t) ?? s;
  } catch {
    return s;
  }
}
function ie(s, e) {
  const t = s?.[e];
  return typeof t == "object" && t !== null ? t : {};
}
function Ei(s) {
  return s === "owner";
}
function Mi(s) {
  return s === "owner" || s === "editor";
}
const Pe = class Pe extends q {
  constructor() {
    super(...arguments), this.route = "profiles", this.tracks = [], this.packs = [], this.notificationTargets = [], this.notificationCandidates = [], this.members = [], this.shareTargets = [], this.createTrackPackId = "", this.createTrackSource = "", this.forecasts = {}, this.forecastPlans = {}, this.packDiffTrack = "", this.packDiffTarget = "", this.loading = !1, this.errorMessage = "", this.notice = "";
  }
  updated(e) {
    (e.has("profile") || e.has("route")) && this.load();
  }
  locale() {
    return F(
      this.hass?.locale?.language ?? this.hass?.language ?? globalThis.navigator?.language ?? "en"
    );
  }
  t(e) {
    return V(this.locale(), e);
  }
  isOwner() {
    return Ei(this.profile?.role);
  }
  canEditTrack() {
    return Mi(this.profile?.role);
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
          pt(this.hass, this.profile.profile_id),
          ci(this.hass)
        ]), this.notificationTargets = this.canEditTrack() ? await Xt(this.hass, this.profile.profile_id) : [], this.notificationCandidates = this.isOwner() && this.route === "settings" ? await ei(this.hass, this.profile.profile_id) : [], this.packs.some((e) => e.pack_version_id === this.createTrackPackId) || (this.createTrackPackId = this.packs[0]?.pack_version_id ?? "", this.createTrackSource = ""), this.isOwner() && this.route === "profiles" ? [this.members, this.shareTargets] = await Promise.all([
          Jt(this.hass, this.profile.profile_id),
          Yt(this.hass, this.profile.profile_id)
        ]) : (this.members = [], this.shareTargets = []);
      } catch (e) {
        this.errorMessage = te(e);
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
        () => Ke(this.hass, this.profile.profile_id, {
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
              @change=${(n) => {
      const o = n.currentTarget;
      o instanceof HTMLSelectElement && this.changeMemberRole(a.ha_user_id, o.value);
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
      const n = new FormData(a.currentTarget);
      this.addMember(
        String(n.get("user") ?? ""),
        String(n.get("role") ?? "viewer")
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
    !e || this.hass === void 0 || this.profile === void 0 || await this.mutate(() => Je(this.hass, this.profile.profile_id, e, t), this.t("manage.saved"));
  }
  async removeMember(e) {
    this.hass === void 0 || this.profile === void 0 || globalThis.confirm?.(this.t("manage.confirmRemoveMember")) && await this.mutate(() => Zt(this.hass, this.profile.profile_id, e), this.t("manage.saved"));
  }
  async changeMemberRole(e, t) {
    this.hass === void 0 || this.profile === void 0 || await this.mutate(
      () => Je(this.hass, this.profile.profile_id, e, t),
      this.t("manage.saved")
    );
  }
  async archiveProfile() {
    this.hass === void 0 || this.profile === void 0 || globalThis.confirm?.(this.t("manage.confirmArchiveProfile")) && await this.mutate(
      () => Ge(this.hass, this.profile.profile_id, "archive"),
      this.t("manage.archivedNotice")
    );
  }
  async deleteProfilePermanently() {
    if (this.hass === void 0 || this.profile === void 0) return;
    const e = `DELETE ${this.profile.profile_id}`, t = globalThis.prompt?.(
      `${this.t("manage.confirmDeletePermanently")} ${e}`
    );
    t === e && await this.mutate(
      () => Ge(
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
        () => Gt(
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
    const t = ie(e.settings, "scheduler"), i = Array.isArray(t.target_ids) ? t.target_ids.map(String) : [], a = e.content_weights ?? {}, n = U(e.source_language ?? "", this.locale()), o = U(e.target_language ?? "", this.locale());
    return r`
      <article class="card">
        <div class="track-summary">
          <h2>${e.name}</h2>
          <p class="meta">${n} → ${o} · ${e.status === "active" ? this.t("manage.active") : e.status === "paused" ? this.t("manage.paused") : this.t("manage.archived")}</p>
          <p class="meta">${this.t("manage.packVersion")}: ${e.pack_version_id ?? "—"}</p>
        </div>
        ${this.canEditTrack() ? r`
          <form class="track-form" @submit=${(c) => {
      c.preventDefault();
      const u = new FormData(c.currentTarget);
      if (this.hass === void 0) return;
      const h = u.getAll("notificationTarget").map(String), v = {
        vocabulary: I(u.get("weightVocabulary"), Number(a.vocabulary ?? 1), 0, 100),
        kanji: I(u.get("weightKanji"), Number(a.kanji ?? 1), 0, 100),
        grammar: I(u.get("weightGrammar"), Number(a.grammar ?? 1), 0, 100),
        expression: I(u.get("weightExpression"), Number(a.expression ?? 1), 0, 100)
      };
      this.mutate(() => oi(this.hass, e.track_id, {
        name: String(u.get("name") ?? e.name),
        source_language: String(u.get("source") ?? e.source_language ?? "").trim(),
        target_language: String(u.get("target") ?? e.target_language ?? "").trim(),
        status: String(u.get("status") ?? e.status),
        priority: T(u.get("priority"), e.priority, 1),
        content_weights: v,
        scheduler_settings: {
          learning_count: T(u.get("learningCount"), Number(t.learning_count ?? 0), 0),
          quiz_count: T(u.get("quizCount"), Number(t.quiz_count ?? 0), 0),
          ...h.length === 0 ? {} : { target_ids: h }
        }
      }), this.t("manage.saved"));
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
                  ${this.sourceLanguages(e.pack_version_id ?? "").map((c) => r`
                    <option value=${c}>${U(c, this.locale())}</option>
                  `)}
                </select>
              </label>
              <label>${this.t("manage.targetLanguage")}
                <select name="target" .value=${e.target_language ?? ""} required>
                  ${this.targetLanguages(
      e.pack_version_id ?? "",
      e.source_language ?? ""
    ).map((c) => r`
                    <option value=${c}>${U(c, this.locale())}</option>
                  `)}
                </select>
              </label>
            </div>

            <div class="actions">
              <button class="primary" type="submit">${this.t("manage.save")}</button>
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
                      ${this.notificationTargets.map((c) => r`
                        <option value=${c.target_id} ?selected=${i.includes(c.target_id)}>
                          ${c.friendly_name} · ${c.platform}
                        </option>`)}
                    </select>
                    <span class="meta">${this.notificationTargets.length === 0 ? this.t("manage.noNotificationTargets") : this.t("manage.notificationTargetsHelp")}</span>
                  </label>
                </div>
              </div>
            </details>
          </form>

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
          <form class="form-grid" @submit=${(n) => {
      n.preventDefault();
      const o = new FormData(n.currentTarget);
      this.hass === void 0 || this.profile === void 0 || this.mutate(() => ni(this.hass, {
        profile_id: this.profile.profile_id,
        name: String(o.get("name") ?? "").trim(),
        pack_version_id: String(o.get("pack") ?? ""),
        source_language: String(o.get("source") ?? "").trim(),
        target_language: String(o.get("target") ?? "").trim(),
        priority: T(o.get("priority"), 1, 1)
      }), this.t("manage.created"));
    }}>
            <label>${this.t("manage.name")}<input name="name" required /></label>
            <label>${this.t("manage.pack")}
              <select
                name="pack"
                .value=${e}
                @change=${(n) => {
      const o = n.currentTarget;
      o instanceof HTMLSelectElement && (this.createTrackPackId = o.value, this.createTrackSource = "");
    }}
              >
                ${this.packs.map((n) => r`
                  <option value=${n.pack_version_id}>${n.name} · ${n.version}</option>
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
                  @change=${(n) => {
      const o = n.currentTarget;
      o instanceof HTMLSelectElement && (this.createTrackSource = o.value);
    }}
                >
                  ${t.map((n) => r`
                    <option value=${n}>${U(n, this.locale())}</option>
                  `)}
                </select>
              </label>
              <label>${this.t("manage.targetLanguage")}
                <select name="target" required>
                  ${a.map((n) => r`
                    <option value=${n}>${U(n, this.locale())}</option>
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
    this.hass !== void 0 && globalThis.confirm?.(`${this.t("manage.confirmDeleteTrack")} "${t}"?`) && await this.mutate(() => li(this.hass, e), this.t("manage.trackDeleted"));
  }
  planFrom(e) {
    const t = new FormData(e);
    return {
      max_new_per_day_cards: T(t.get("new"), 0, 0),
      max_reviews_per_day_cards: T(t.get("reviews"), 50, 1),
      max_notification_new_teasers: T(t.get("teasers"), 2, 0),
      target_date: String(t.get("date") ?? "").trim() || null,
      target_coverage: I(t.get("coverage"), 1, 0.01, 1),
      target_retention: I(t.get("retention"), 0.9, 0.01, 1)
    };
  }
  renderPlan(e) {
    const t = ie(e.settings, "learning_plan"), i = Number(this.profile?.settings?.max_new_per_day_cards ?? 8), a = this.forecasts[e.track_id];
    return r`
      <div class="stack">
        <form class="form-grid" @submit=${(n) => {
      if (n.preventDefault(), this.hass === void 0) return;
      const o = this.planFrom(n.currentTarget);
      this.loading = !0, mi(this.hass, e.track_id, o).then((c) => {
        this.forecasts = { ...this.forecasts, [e.track_id]: c }, this.forecastPlans = { ...this.forecastPlans, [e.track_id]: o };
      }).catch((c) => {
        this.errorMessage = te(c);
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
        ${a === void 0 ? l : this.renderForecast(e, a)}
      </div>
    `;
  }
  renderForecast(e, t) {
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
    const t = this.forecastPlans[e.track_id];
    this.hass === void 0 || t === void 0 || await this.mutate(() => fi(this.hass, e.track_id, t), this.t("manage.saved"));
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
        this.packDiff = await pi(this.hass, e.track_id, t.pack_version_id), this.packDiffTrack = e.track_id, this.packDiffTarget = t.pack_version_id;
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
      () => gi(this.hass, e, t),
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
        () => ti(this.hass, this.profile.profile_id, a),
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
            ${this.notificationTargets.map((t) => r`
              <form class="target-card" @submit=${(i) => {
      i.preventDefault();
      const a = new FormData(i.currentTarget);
      this.hass === void 0 || this.profile === void 0 || this.mutate(
        () => ii(
          this.hass,
          this.profile.profile_id,
          t.target_id,
          {
            friendly_name: String(a.get("friendlyName") ?? "").trim(),
            shared_device: a.get("sharedDevice") === "on",
            lockscreen_visibility: String(
              a.get("lockscreenVisibility") ?? "private"
            ),
            enabled: a.get("enabled") === "on",
            minimum_gap_seconds: fe(a.get("minimumGap"), 0),
            maximum_notifications_per_hour: fe(a.get("maxPerHour"), 1),
            daily_push_budget: fe(a.get("targetBudget"), 0)
          }
        ),
        this.t("manage.notificationTargetUpdated")
      );
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

                <div class="actions">
                  <button class="primary" type="submit">${this.t("manage.save")}</button>
                  <button
                    type="button"
                    @click=${() => {
      this.hass === void 0 || this.profile === void 0 || this.mutate(
        () => ai(
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
              </form>
            `)}
          </div>
        `}
      </article>
    `;
  }
  renderSettings() {
    if (!this.isOwner()) return r`<div class="card"><p>${this.t("manage.readOnly")}</p></div>`;
    const e = this.profile?.settings ?? {}, t = ie(e, "quiet_hours"), i = ie(e, "scheduler"), a = Array.isArray(i.active_windows) ? i.active_windows : [], n = typeof a[0] == "object" && a[0] !== null ? a[0] : {};
    return r`
      <article class="card">
        <h2>${this.t("manage.profileSettings")}</h2>
        <p class="muted">${this.t("manage.presetInitialOnly")}: ${this.profile?.preset}</p>
        <form class="form-grid" @submit=${(o) => {
      o.preventDefault();
      const c = new FormData(o.currentTarget);
      this.hass === void 0 || this.profile === void 0 || this.mutate(() => Ke(this.hass, this.profile.profile_id, {
        settings_patch: {
          session_length_cards: T(c.get("session"), 20, 1),
          max_new_per_day_cards: T(c.get("new"), 8, 0),
          daily_push_budget: T(c.get("push"), 6, 0),
          quiet_hours: {
            start: String(c.get("quietStart") ?? "22:00"),
            end: String(c.get("quietEnd") ?? "08:00")
          },
          scheduler: {
            ...i,
            active_windows: [{
              start: String(c.get("activeStart") ?? "08:00"),
              end: String(c.get("activeEnd") ?? "20:00")
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
      ${this.renderNotificationTargets()}
    `;
  }
};
Pe.styles = M`
    ${W}
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
    }
  `;
let g = Pe;
f([
  $({ attribute: !1 })
], g.prototype, "hass");
f([
  $({ attribute: !1 })
], g.prototype, "profile");
f([
  $({ attribute: !1 })
], g.prototype, "route");
f([
  d()
], g.prototype, "tracks");
f([
  d()
], g.prototype, "packs");
f([
  d()
], g.prototype, "notificationTargets");
f([
  d()
], g.prototype, "notificationCandidates");
f([
  d()
], g.prototype, "members");
f([
  d()
], g.prototype, "shareTargets");
f([
  d()
], g.prototype, "createTrackPackId");
f([
  d()
], g.prototype, "createTrackSource");
f([
  d()
], g.prototype, "forecasts");
f([
  d()
], g.prototype, "forecastPlans");
f([
  d()
], g.prototype, "packDiff");
f([
  d()
], g.prototype, "packDiffTrack");
f([
  d()
], g.prototype, "packDiffTarget");
f([
  d()
], g.prototype, "loading");
f([
  d()
], g.prototype, "errorMessage");
f([
  d()
], g.prototype, "notice");
globalThis.customElements !== void 0 && customElements.get("locklearn-management-view") === void 0 && customElements.define("locklearn-management-view", g);
var Ci = Object.defineProperty, L = (s, e, t, i) => {
  for (var a = void 0, n = s.length - 1, o; n >= 0; n--)
    (o = s[n]) && (a = o(e, t, a) || a);
  return a && Ci(e, t, a), a;
};
function ae(s) {
  if (s === null) return null;
  try {
    const e = new URL(s);
    return e.protocol === "https:" || e.protocol === "http:" ? e.href : null;
  } catch {
    return null;
  }
}
function Di(s) {
  if (s < 1024) return `${s} B`;
  const e = ["KiB", "MiB", "GiB"];
  let t = s / 1024, i = 0;
  for (; t >= 1024 && i < e.length - 1; )
    t /= 1024, i += 1;
  return `${t.toFixed(t >= 10 ? 1 : 2)} ${e[i]}`;
}
const Ee = class Ee extends q {
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
    return F(
      this.hass?.locale?.language ?? this.hass?.language ?? globalThis.navigator?.language ?? "en"
    );
  }
  t(e) {
    return V(this.locale(), e);
  }
  async load() {
    if (this.hass !== void 0) {
      this.loading = !0, this.errorMessage = "";
      try {
        this.datasets = await di(this.hass);
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
        this.datasets = await ui(this.hass), this.notice = this.t("datasets.refreshed");
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
        const t = await hi(this.hass, e.dataset_id, e.available_version);
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
      const n = await Ye(this.hass, e, t);
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
    const i = this.attributionKey(e, t), a = this.attributionPages[i];
    if (!(a === void 0 || a.cursor === null || a.loading)) {
      this.attributionPages = {
        ...this.attributionPages,
        [i]: { ...a, loading: !0 }
      };
      try {
        const n = await Ye(
          this.hass,
          e,
          t,
          a.cursor
        );
        this.attributionPages = {
          ...this.attributionPages,
          [i]: {
            items: [...a.items, ...n.items],
            cursor: n.cursor,
            expanded: !0,
            loading: !1
          }
        };
      } catch (n) {
        this.errorMessage = n instanceof Error ? n.message : String(n), this.attributionPages = {
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
    const t = e.error !== null || e.stale_sources.length > 0, i = ae(e.release_url);
    return r`
      <article class="card">
        <h2>${e.name}</h2>
        <dl>
          <dt>${this.t("datasets.state")}</dt><dd>${e.state}</dd>
          <dt>${this.t("datasets.installedVersion")}</dt><dd>${e.installed_version ?? "—"}</dd>
          <dt>${this.t("datasets.availableVersion")}</dt><dd>${e.available_version ?? "—"}</dd>
          <dt>${this.t("datasets.sourceAge")}</dt>
          <dd>${e.source_age_days === null ? "—" : `${e.source_age_days} ${this.t("datasets.days")}`}</dd>
          <dt>${this.t("datasets.disk")}</dt><dd>${Di(e.cache_bytes)}</dd>
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
      const n = ae(a.homepage), o = this.attributionKey(e.dataset_id, a.source_id), c = this.attributionPages[o];
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
                  ${n ? r`<a href=${n} target="_blank" rel="noopener noreferrer">${this.t("datasets.sourcePage")}</a>` : l}
                  ${a.attribution_records > 0 ? r`
                        <div class="actions">
                          <button
                            type="button"
                            @click=${() => {
        this.toggleAttributions(e.dataset_id, a.source_id);
      }}
                          >
                            ${c?.expanded ? this.t("datasets.hideAttributions") : this.t("datasets.showAttributions")}
                          </button>
                        </div>
                        ${c?.expanded ? r`
                              <div class="notice">
                                <strong>${this.t("datasets.individualAttributions")}</strong>
                                ${c.loading && c.items.length === 0 ? r`<p>${this.t("datasets.loading")}</p>` : r`<ul>
                                      ${c.items.map((u) => r`
                                        <li>
                                          ${u.attribution_text}
                                          <div class="meta">
                                            ${u.source_record_id ?? "—"}
                                            ${u.author ? r` · ${u.author}` : l}
                                            ${u.language_tag ? r` · ${u.language_tag}` : l}
                                            ${u.modified_from_source ? r` · ${this.t("datasets.modified")}` : l}
                                          </div>
                                        </li>
                                      `)}
                                    </ul>`}
                                ${c.cursor !== null ? r`<button
                                      type="button"
                                      ?disabled=${c.loading}
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
                ${ae(a.source_url) ? r`<a href=${ae(a.source_url)} target="_blank" rel="noopener noreferrer">${this.t("datasets.licensePage")}</a>` : l}
              </li>
            `)}</ul>`}
      </article>
    `;
  }
};
Ee.styles = M`
    ${W}
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
let A = Ee;
L([
  $({ attribute: !1 })
], A.prototype, "hass");
L([
  $({ type: Boolean })
], A.prototype, "admin");
L([
  d()
], A.prototype, "datasets");
L([
  d()
], A.prototype, "loading");
L([
  d()
], A.prototype, "errorMessage");
L([
  d()
], A.prototype, "notice");
L([
  d()
], A.prototype, "attributionPages");
globalThis.customElements !== void 0 && customElements.get("locklearn-dataset-view") === void 0 && customElements.define("locklearn-dataset-view", A);
var Ni = Object.defineProperty, x = (s, e, t, i) => {
  for (var a = void 0, n = s.length - 1, o; n >= 0; n--)
    (o = s[n]) && (a = o(e, t, a) || a);
  return a && Ni(e, t, a), a;
};
function ve(s) {
  return s === null ? "—" : `${Math.round(s * 100)}%`;
}
function Ri(s, e = 14) {
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
function Li(s) {
  return {
    exposures: s.reduce((e, t) => e + t.learning_exposures, 0),
    verifiedRetrievals: s.reduce((e, t) => e + t.verified_retrievals, 0)
  };
}
function se(s) {
  return s?.role === "owner" || s?.role === "editor";
}
const Me = class Me extends q {
  constructor() {
    super(...arguments), this.difficulties = [], this.tracks = [], this.selectedTrackId = "", this.loading = !1, this.errorMessage = "", this.notice = "", this.mnemonicEdits = {}, this.busyCardKey = null, this.loadGeneration = 0;
  }
  updated(e) {
    (e.has("hass") || e.has("profile")) && this.load();
  }
  locale() {
    return F(
      this.hass?.locale?.language ?? this.hass?.language ?? globalThis.navigator?.language ?? "en"
    );
  }
  t(e) {
    return V(this.locale(), e);
  }
  async load() {
    if (this.hass === void 0 || this.profile === void 0) {
      this.stats = void 0, this.difficulties = [], this.tracks = [];
      return;
    }
    const e = ++this.loadGeneration, t = this.hass, i = this.profile.profile_id;
    this.loading = !0, this.errorMessage = "";
    try {
      const a = (await pt(t, i)).filter(
        (h) => h.status === "active"
      ), n = this.selectedTrackId && a.some((h) => h.track_id === this.selectedTrackId) ? this.selectedTrackId : "", [o, c] = await Promise.all([
        si(t, i, n || null),
        ri(t, i, n || null)
      ]);
      if (e !== this.loadGeneration) return;
      this.tracks = a, this.selectedTrackId = n, this.stats = o, this.difficulties = c;
      const u = { ...this.mnemonicEdits };
      for (const h of c)
        u[h.card_key] === void 0 && (u[h.card_key] = h.annotations[0]?.note ?? "");
      this.mnemonicEdits = u;
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
    if (this.hass === void 0 || this.profile === void 0 || !se(this.profile)) return;
    const t = (this.mnemonicEdits[e.card_key] ?? "").trim();
    if (t) {
      this.busyCardKey = e.card_key, this.errorMessage = "", this.notice = "";
      try {
        const i = e.annotations[0];
        i === void 0 ? await bt(this.hass, this.profile.profile_id, e.card_key, t) : await wi(
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
    if (!(this.hass === void 0 || this.profile === void 0 || !se(this.profile))) {
      this.busyCardKey = e.card_key, this.errorMessage = "", this.notice = "";
      try {
        const t = await Si(
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
    if (!(this.hass === void 0 || this.profile === void 0 || !se(this.profile) || !(globalThis.confirm?.(this.t("stats.reactivateConfirm")) ?? !0))) {
      this.busyCardKey = e.card_key, this.errorMessage = "", this.notice = "";
      try {
        await xi(
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
    const t = e.recent_verified_accuracy, i = e.calibration, a = Ri(e.daily), n = Li(a);
    return r`
      <section class="grid" aria-label=${this.t("stats.verifiedGroup")}>
        <article class="card metric verified">
          <span>${this.t("stats.dueToday")}</span>
          <strong>${e.due_today}</strong>
        </article>
        <article class="card metric verified">
          <span>${this.t("stats.verifiedAccuracy")}</span>
          <strong>${ve(t.accuracy)}</strong>
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
            <strong>${ve(i.later_verified_accuracy)}</strong>
          </div>
        </div>
      </article>

      <article class="card secondary">
        <h2>${this.t("stats.mastery")}</h2>
        <div class="metric">
          <strong>${ve(e.mastery.value)}</strong>
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
        (c) => `${c.expected_answer_id}→${c.chosen_answer_id} ×${c.count}`
      ).join(", ")}
                        </div>`}
                    ${o.annotations[0]?.note ? r`<p>${o.annotations[0].note}</p>` : l}
                    ${se(this.profile) ? r`
                          <label>
                            <span>${this.t("stats.personalMnemonic")}</span>
                            <textarea
                              .value=${this.mnemonicEdits[o.card_key] ?? ""}
                              @input=${(c) => this.editMnemonic(o.card_key, c)}
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
Me.styles = M`
    ${W}
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
let k = Me;
x([
  $({ attribute: !1 })
], k.prototype, "hass");
x([
  $({ attribute: !1 })
], k.prototype, "profile");
x([
  d()
], k.prototype, "stats");
x([
  d()
], k.prototype, "difficulties");
x([
  d()
], k.prototype, "tracks");
x([
  d()
], k.prototype, "selectedTrackId");
x([
  d()
], k.prototype, "loading");
x([
  d()
], k.prototype, "errorMessage");
x([
  d()
], k.prototype, "notice");
x([
  d()
], k.prototype, "mnemonicEdits");
x([
  d()
], k.prototype, "busyCardKey");
globalThis.customElements !== void 0 && customElements.get("locklearn-stats-view") === void 0 && customElements.define("locklearn-stats-view", k);
const tt = [
  { route: "home", labelKey: "nav.home" },
  { route: "learn", labelKey: "nav.learn" },
  { route: "quiz", labelKey: "nav.quiz" },
  { route: "exam", labelKey: "nav.exam" },
  { route: "stats", labelKey: "nav.stats" },
  { route: "profiles", labelKey: "nav.profiles" },
  { route: "tracks", labelKey: "nav.tracks" },
  { route: "packs", labelKey: "nav.packs" },
  { route: "sources", labelKey: "nav.sources" }
], Ii = [
  { route: "settings", labelKey: "nav.settings" }
];
function _e(s) {
  return s.length === 0 ? [] : new Set(s.map((t) => t.role)).has("owner") ? [...tt, ...Ii] : tt;
}
function re(s, e) {
  return _e(e).some((t) => t.route === s);
}
function Ui(s) {
  return {
    mine: s.filter((e) => e.role === "owner"),
    shared: s.filter((e) => e.role !== "owner")
  };
}
function it(s, e) {
  const t = e.personal_profile?.profile_id;
  if (t !== void 0 && s.some((a) => a.profile_id === t))
    return t;
  const i = s.find((a) => a.role === "owner");
  return i !== void 0 ? i.profile_id : s[0]?.profile_id ?? null;
}
function Hi(s) {
  if (s === void 0) return { kind: "define" };
  const e = typeof s.locklearnFrontendProtocol == "number" ? s.locklearnFrontendProtocol : null;
  return e === R ? { kind: "reuse" } : {
    kind: "reload",
    existingProtocol: e,
    frontendProtocol: R
  };
}
function Oi(s, e, t) {
  return !s && e && t;
}
const ji = [
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
], Wi = "home";
function be(s) {
  const t = s.replace(/^\/+|\/+$/g, "").split("/").filter(Boolean), i = t[0] === "locklearn" ? t[1] : t[0];
  return ji.includes(i) ? i : Wi;
}
function Fi(s) {
  return s === "home" ? "/locklearn" : `/locklearn/${s}`;
}
function ye(s) {
  const e = Fi(s);
  globalThis.location?.pathname !== e && (globalThis.history?.pushState({}, "", e), globalThis.dispatchEvent?.(new PopStateEvent("popstate")));
}
var Vi = Object.defineProperty, S = (s, e, t, i) => {
  for (var a = void 0, n = s.length - 1, o; n >= 0; n--)
    (o = s[n]) && (a = o(e, t, a) || a);
  return a && Vi(e, t, a), a;
};
const at = "locklearn-hard-reload-required", de = class de extends q {
  constructor() {
    super(...arguments), this.status = "loading", this.activeRoute = be(
      globalThis.location?.pathname ?? "/locklearn"
    ), this.profiles = [], this.selectedProfileId = null, this.dashboardLoading = !1, this.dashboardError = "", this.errorMessage = "", this.loadGeneration = 0, this.dashboardGeneration = 0, this.initialLoadStarted = !1, this.handlePopState = () => {
      const e = be(globalThis.location?.pathname ?? "/locklearn");
      this.activeRoute = re(e, this.profiles) ? e : "home";
    };
  }
  connectedCallback() {
    super.connectedCallback(), globalThis.addEventListener?.("popstate", this.handlePopState);
  }
  disconnectedCallback() {
    globalThis.removeEventListener?.("popstate", this.handlePopState), super.disconnectedCallback();
  }
  updated(e) {
    Oi(
      this.initialLoadStarted,
      e.has("hass"),
      this.hass !== void 0
    ) && (this.initialLoadStarted = !0, this.load());
  }
  locale() {
    const e = this.hass?.locale?.language ?? this.hass?.language ?? globalThis.navigator?.language ?? "en";
    return F(e);
  }
  t(e) {
    return V(this.locale(), e);
  }
  async load() {
    if (this.hass === void 0) return;
    const e = ++this.loadGeneration;
    this.status = "loading", this.errorMessage = "";
    try {
      const t = await Kt(this.hass), i = await Qe(this.hass);
      if (e !== this.loadGeneration) return;
      this.bootstrapState = t, this.profiles = i, this.selectedProfileId = it(i, t);
      const a = be(globalThis.location?.pathname ?? t.panel_path);
      this.activeRoute = re(a, i) ? a : "home", this.status = "ready", this.loadDashboard();
    } catch (t) {
      if (e !== this.loadGeneration) return;
      if (t instanceof ht) {
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
    re(e, this.profiles) && (this.activeRoute = e, ye(e));
  }
  selectProfile(e) {
    const t = e.currentTarget;
    if (!(t instanceof HTMLSelectElement)) return;
    const i = t.value;
    this.profiles.some((a) => a.profile_id === i) && (this.selectedProfileId = i, this.handoffSession = void 0, this.loadDashboard());
  }
  openTargetedSession(e) {
    const t = e.detail?.session;
    t === void 0 || this.selectedProfileId === null || t.profile_id !== this.selectedProfileId || (this.handoffSession = t, this.activeRoute = "learn", ye("learn"));
  }
  clearSessionHandoff() {
    this.handoffSession = void 0;
  }
  async refreshManagement() {
    if (this.hass === void 0) return;
    const e = this.selectedProfileId;
    try {
      const t = await Qe(this.hass);
      this.profiles = t, this.selectedProfileId = e !== null && t.some((i) => i.profile_id === e) ? e : this.bootstrapState === void 0 ? t[0]?.profile_id ?? null : it(t, this.bootstrapState), re(this.activeRoute, t) || (this.activeRoute = "home", ye("home")), await this.loadDashboard();
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
      const t = await vi(this.hass, this.selectedProfileId);
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
              frontend protocol ${R} · backend protocol
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
    const e = _e(this.profiles), t = Ui(this.profiles);
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
    const t = _e(this.profiles).find((i) => i.route === e);
    return t === void 0 ? this.t("nav.home") : this.t(t.labelKey);
  }
};
de.locklearnFrontendProtocol = R, de.styles = M`
    ${W}
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
let w = de;
S([
  $({ attribute: !1 })
], w.prototype, "hass");
S([
  d()
], w.prototype, "status");
S([
  d()
], w.prototype, "activeRoute");
S([
  d()
], w.prototype, "bootstrapState");
S([
  d()
], w.prototype, "profiles");
S([
  d()
], w.prototype, "selectedProfileId");
S([
  d()
], w.prototype, "dashboard");
S([
  d()
], w.prototype, "dashboardLoading");
S([
  d()
], w.prototype, "dashboardError");
S([
  d()
], w.prototype, "errorMessage");
S([
  d()
], w.prototype, "handoffSession");
function Bi(s) {
  if (typeof document > "u" || document.getElementById(at) !== null) return;
  const e = document.createElement("div");
  e.id = at, e.setAttribute("role", "alert"), e.style.cssText = "position:fixed;inset:0;z-index:2147483647;display:grid;place-items:center;padding:24px;background:var(--primary-background-color,#fff);color:var(--primary-text-color,#111);font-family:system-ui,sans-serif";
  const t = document.createElement("div");
  t.style.cssText = "max-width:680px;padding:24px;border:1px solid var(--divider-color,#ddd);border-radius:12px;background:var(--card-background-color,#fff)";
  const i = document.createElement("h1");
  i.textContent = "LockLearn was updated";
  const a = document.createElement("p");
  a.textContent = "An older LockLearn panel is still loaded in this browser. Perform a full browser reload before continuing.";
  const n = document.createElement("p");
  n.textContent = `loaded protocol ${s ?? "unknown"} · current protocol ${R}`;
  const o = document.createElement("button");
  o.textContent = "Reload now", o.addEventListener("click", () => globalThis.location?.reload()), t.append(i, a, n, o), e.append(t), document.body.append(e);
}
const Qi = customElements.get(
  "locklearn-panel"
), $e = Hi(Qi);
$e.kind === "define" ? customElements.define("locklearn-panel", w) : $e.kind === "reload" && Bi($e.existingProtocol);
export {
  w as LockLearnPanel
};
