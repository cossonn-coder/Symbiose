// SYMBIOSE — tools/splat/portraits/table_cs.js (sprint PRÉCUISSON SPLATS ⑥)
// La TABLE DES ESPÈCES des portraits, lue DANS LE C# DE LA VUE — source unique.
//
// Pourquoi lire le C# plutôt que l'exporter ou le recopier (kickoff ⑥ §1) :
//   • recopier la table dans l'outil JS = deux vérités qui divergent au premier
//     réglage F5 (interdit par le kickoff) ;
//   • l'exporter depuis Godot demanderait un mode d'export DANS la vue (code de vue
//     ajouté pour un outil) et un Godot lancé à chaque cuisson ;
//   • les tables sont des LITTÉRAUX (records à arguments nommés, dictionnaires
//     `["Cle"] = new(...)`) : un mini-lecteur de littéraux C# suffit, sans toucher à
//     la vue. Il ÉCHOUE BRUYAMMENT si la syntaxe change (exception, pas de silence).
//
// Fichiers lus (visuals/) : PortsFiches (FichePort + palettes ajoutées), Organs
// (palettes), Lianes (FicheLiane), Rameaux (RecetteRameaux), FruitsArbre,
// FleursArbre, Prairie + Graminees (ports de prairie + constantes).
//
// 📖 Pédagogie : c'est un analyseur « descente récursive » — une fonction par
// règle de grammaire (expression, arguments, tableau…), chacune consomme les
// jetons qu'elle reconnaît. Le même schéma que le parseur d'une trame série en C.
//
// Valeurs rendues : nombres JS, chaînes, booléens, null ; énumérations → le nom du
// membre (« Tige ») ; `new Color("hex")` → « #hex » ; records → objets aux noms des
// paramètres (positionnels rangés, défauts appliqués).

'use strict';

const fs = require('fs');
const path = require('path');

const RACINE = path.resolve(__dirname, '..', '..', '..');
const VUE = f => fs.readFileSync(path.join(RACINE, 'visuals', `PlantRenderer.${f}.cs`), 'utf8');

// --- Jetons ------------------------------------------------------------------
function jetons(src) {
  const re = /\s+|\/\/[^\n]*|\/\*[\s\S]*?\*\/|"(?:[^"\\]|\\.)*"|-?\d+(?:\.\d+)?f?|[A-Za-z_][\w]*|\[\]|[()[\]{},:=.;<>?]/gy;
  const out = [];
  let m;
  while (re.lastIndex < src.length) {
    const i = re.lastIndex;
    if (!(m = re.exec(src))) throw new Error('table_cs : caractère inattendu « ' + src.slice(i, i + 20) + ' »');
    const t = m[0];
    if (/^\s|^\/\//.test(t) || t.startsWith('/*')) continue;
    out.push(t);
  }
  return out;
}

// --- Grammaire des littéraux ---------------------------------------------------
// `types` : nom → { params: [{ nom, type, defaut?, reste? }] } (records et constructeurs).
function lecteur(toks, types) {
  let i = 0;
  const voir = () => toks[i], prendre = attendu => {
    const t = toks[i++];
    if (attendu !== undefined && t !== attendu) throw new Error(`table_cs : « ${attendu} » attendu, « ${t} » lu`);
    return t;
  };
  function expr(type) {
    const t = voir();
    if (t === 'new') return nouveau(type);
    if (t === '(') {                                   // tuple (a, b)
      prendre('(');
      const vals = [expr()];
      while (voir() === ',') { prendre(','); vals.push(expr()); }
      prendre(')');
      return vals;
    }
    prendre();
    if (t[0] === '"') return t.slice(1, -1);
    if (/^-?\d/.test(t)) return parseFloat(t);
    if (t === 'true' || t === 'false') return t === 'true';
    if (t === 'null' || t === 'default') return null;
    let nom = t;                                       // énumération / constante : dernier membre
    while (voir() === '.') { prendre('.'); nom = prendre(); }
    return nom;
  }
  function nouveau(typeAttendu) {
    prendre('new');
    let type = typeAttendu;
    if (/^[A-Za-z_]/.test(voir())) type = prendre();
    if (voir() === '[]') {                             // new[] { … } ou new T[] { … }
      prendre('[]'); prendre('{');
      const vals = [];
      while (voir() !== '}') { vals.push(expr()); if (voir() === ',') prendre(','); }
      prendre('}');
      return vals;
    }
    // C# ≥ 7.2 : un argument nommé À SA PLACE peut précéder des positionnels → chaque
    // argument garde son rang `k`, le nom ne sert qu'à vérifier/placer.
    prendre('(');
    const pos = [], nommes = {};
    for (let k = 0; voir() !== ')'; k++) {
      if (toks[i + 1] === ':' && /^[A-Za-z_]/.test(voir())) { const n = prendre(); prendre(':'); nommes[n] = expr(paramType(type, n)); }
      else pos[k] = expr(paramType(type, k));
      if (voir() === ',') prendre(',');
    }
    prendre(')');
    if (type === 'Color') return '#' + pos[0];
    return construire(type, pos, nommes);
  }
  function paramType(type, cle) {
    const d = types[type];
    if (!d) return undefined;
    const p = typeof cle === 'number' ? d.params[Math.min(cle, d.params.length - 1)] : d.params.find(q => q.nom === cle);
    return p && types[p.type] ? p.type : undefined;
  }
  function construire(type, pos, nommes) {
    const d = types[type];
    if (!d) throw new Error('table_cs : type inconnu ' + type);
    const o = {};
    d.params.forEach((p, k) => {
      if (p.reste) o[p.nom] = pos.slice(k);
      else if (pos[k] !== undefined) o[p.nom] = pos[k];
      else if (p.nom in nommes) o[p.nom] = nommes[p.nom];
      else if ('defaut' in p) o[p.nom] = p.defaut;
      else throw new Error(`table_cs : ${type}.${p.nom} manquant`);
    });
    for (const n of Object.keys(nommes)) if (!(n in o)) throw new Error(`table_cs : ${type}.${n} inconnu`);
    return o;
  }
  return { expr, voir, prendre, get i() { return i; }, set i(v) { i = v; } };
}

// Signatures : `record [struct] Nom(Type a, Type b = v, …)` et `public Nom(…)` (constructeur).
function signatures(src, types) {
  const re = /(?:record(?:\s+struct)?\s+(\w+)|public\s+(\w+))\s*\(([^)]*)\)/g;
  let m;
  while ((m = re.exec(src))) {
    const nom = m[1] || m[2];
    if (types[nom]) continue;
    const params = [];
    for (const brut of m[3].split(',').map(s => s.trim()).filter(Boolean)) {
      const reste = brut.startsWith('params ');
      const [decl, defaut] = brut.replace(/^params\s+/, '').split('=').map(s => s.trim());
      const mots = decl.split(/\s+/);
      const p = { nom: mots[mots.length - 1], type: mots[0].replace('[]', ''), reste };
      if (defaut !== undefined) p.defaut = lecteur(jetons(defaut), types).expr();
      params.push(p);
    }
    types[nom] = { params };
  }
}

// Dictionnaires `Dictionary<string, T> Nom = new() { ["Cle"] = expr, … };`
function dictionnaires(src, types) {
  const out = {};
  const re = /Dictionary<string,\s*(\([^)]*\)|\w+)>\s+(\w+)\s*=\s*new\(\)\s*\{/g;
  let m;
  while ((m = re.exec(src))) {
    let type = m[1];
    if (type.startsWith('(')) {                         // tuple nommé (int Grappe, float QueueCm)
      const noms = type.slice(1, -1).split(',').map(s => s.trim().split(/\s+/)[1]);
      type = 'tuple:' + m[2];
      types[type] = { params: noms.map(nom => ({ nom, type: '' })) };
    }
    const toks = jetons(src.slice(re.lastIndex, src.indexOf('};', re.lastIndex)));
    const L = lecteur(toks, types), d = {};
    while (L.i < toks.length) {
      L.prendre('['); const cle = L.expr(); L.prendre(']'); L.prendre('=');
      let v = L.expr(type);
      if (Array.isArray(v) && type.startsWith('tuple:')) v = Object.fromEntries(types[type].params.map((p, k) => [p.nom, v[k]]));
      d[cle] = v;
      if (L.voir() === ',') L.prendre(',');
    }
    out[m[2]] = d;
  }
  return out;
}

// Affectations `Nom["Cle"] = expr;` (palettes complétées par le constructeur static).
function affectations(src, types, cible) {
  const re = new RegExp(cible + '\\["(\\w+)"\\]\\s*=\\s*([^;]+);', 'g');
  const out = {};
  let m;
  while ((m = re.exec(src))) out[m[1]] = lecteur(jetons(m[2]), types).expr();
  return out;
}

// Constantes `const float|int Nom = valeur;`.
function constantes(src) {
  const out = {};
  for (const m of src.matchAll(/const\s+(?:float|int)\s+(\w+)\s*=\s*(-?\d+(?:\.\d+)?)f?\s*[;,]/g)) out[m[1]] = parseFloat(m[2]);
  return out;
}

// La table complète, lue une fois.
function lireTable() {
  const sources = ['PortsFiches', 'Organs', 'Lianes', 'Rameaux', 'FruitsArbre', 'FleursArbre', 'Prairie', 'Graminees', 'Arbres', 'Sapin']
    .map(f => [f, VUE(f)]);
  const types = { Color: { params: [{ nom: 'hex', type: 'string' }] } };
  for (const [, s] of sources) signatures(s, types);
  const d = {};
  for (const [, s] of sources) Object.assign(d, dictionnaires(s, types));
  const src = Object.fromEntries(sources);
  const palettes = { ...d.Palettes, ...affectations(src.PortsFiches, types, 'Palettes') };
  const def = /DefaultPalette\s*=\s*([^;]+);/.exec(src.Organs);
  return {
    ports: d.FichesPort, lianes: d.FichesLiane, rameaux: d.RecettesRameaux,
    fruitsArbres: d.FruitsArbres, grappes: d.GrappesFruits, fleursArbres: d.FleursArbres,
    prairie: d.PortsPrairie, constPrairie: { ...constantes(src.Prairie), ...constantes(src.Graminees) },
    palettes, paletteDefaut: lecteur(jetons(def[1]), types).expr(),
    // BOIS & ARBRES ⑤ : écorce d'essence (RecetteArbre.Ecorce) et règle du cône (PlantRenderer.Sapin.cs).
    ecorces: Object.fromEntries(Object.entries(d.RecettesArbres || {}).map(([e, r]) => [e, r.Ecorce])),
    cone: { ...constantes(src.Sapin),
      especes: [.../PortsConiques\s*=\s*new\(\)\s*\{([^}]*)\}/.exec(src.Sapin)[1].matchAll(/"(\w+)"/g)].map(m => m[1]) },
    automneDefaut: [...src.Organs.match(/AutumnLeaves\s*=\s*\{([^}]*)\}/)[1].matchAll(/"(\w+)"/g)].map(m => '#' + m[1])
  };
}

module.exports = { lireTable, jetons };

if (require.main === module) {
  const t = lireTable();
  console.log(JSON.stringify(process.argv[2] ? t[process.argv[2]] : Object.fromEntries(
    Object.entries(t).map(([k, v]) => [k, v && typeof v === 'object' ? Object.keys(v).length : v])), null, 1));
}
