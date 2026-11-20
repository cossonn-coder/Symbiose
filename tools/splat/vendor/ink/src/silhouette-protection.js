/* Per-subject fog and contrast settings using the scene's normal target selectors. */
const SilhouetteProtection = (() => {
  const targets = typeof TargetSelectors === 'undefined' ? require('./target-selectors.js') : TargetSelectors;
  const number = (n, lo, hi, label) => {
    if (!Number.isFinite(n) || n < lo || n > hi) throw new RangeError(label + ' is out of range');
    return n;
  };
  const record = (value, keys) => {
    if (!value || Object.getPrototypeOf(value) !== Object.prototype || Object.keys(value).some(k => !keys.includes(k)))
      throw new TypeError('Invalid silhouette protection settings');
    return value;
  };
  function prepare(authored, override) {
    const source = override === true ? authored : override ?? authored;
    if (source == null || source === false) return null;
    const { targets: rules } = record(source, ['targets']);
    if (!Array.isArray(rules) || rules.length > 64) throw new TypeError('Silhouette protection needs up to 64 targets');
    const ids = new Set();
    const prepared = Array.from(rules, (row,i) => {
      const { id = 'target-' + (i+1), select, fogScale = 1, contrast = 1, pivot = .5 } =
        record(row, ['id','select','fogScale','contrast','pivot']);
      if (!targets.name(id) || ids.has(id)) throw new TypeError('Silhouette protection target IDs must be unique names');
      ids.add(id);
      const selection = targets.prepare(select);
      if ('medium' in selection || 'mediumKind' in selection)
        throw new TypeError('Silhouette protection selectors must identify a scene subject');
      return Object.freeze({ id, slot: i+1, select: selection, fogScale: number(fogScale,0,2,'Subject fog scale'),
        contrast: number(contrast,0,4,'Subject contrast'), pivot: number(pivot,0,1,'Subject contrast pivot') });
    });
    if (!prepared.length) return null;
    function match(target) {
      const rule = prepared.find(row => targets.matches(row.select,target));
      return rule ?? null;
    }
    function bind(world) {
      const index = targets.index(world), cache = new WeakMap();
      return i => {
        if (i < 0 || i >= world.count) return null;
        const target = index.row(i);
        if (!cache.has(target)) cache.set(target,match(target));
        return cache.get(target);
      };
    }
    return Object.freeze({ targets: Object.freeze(prepared), affectsFog: prepared.some(r=>r.fogScale!==1), match, bind });
  }
  return Object.freeze({ prepare });
})();
if (typeof module !== 'undefined') module.exports = SilhouetteProtection;
