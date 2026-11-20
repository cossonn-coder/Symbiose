/* Named places, local simulation clocks and directed travel links. */
(function (K) {
  const W = K.world, V = K.V, { freeze, clone } = K.procedural.data;
  const finite = Number.isFinite;
  const xyz = value => Array.isArray(value) && value.length === 3 && Array.from(value).every(finite);
  const positive = value => finite(value) && value > 0;
  const name = value => typeof value === 'string' && value.trim().length > 0;
  const point = value => {
    if (!xyz(value)) throw new TypeError('Expected finite XYZ coordinates');
    return value.slice();
  };
  function synchronous(value, label) {
    if (typeof value?.then === 'function') {
      Promise.resolve(value).catch(() => {});
      throw new TypeError(label + ' must be synchronous');
    }
    return value;
  }

  function anchor({ origin, normal = [0, 0, 1], up = [0, 1, 0] } = {}) {
    const n = V.norm(point(normal), [0, 0, 0]), right = V.norm(V.cross(point(up), n), [0, 0, 0]);
    if (V.len(n) < 0.99 || V.len(right) < 0.99)
      throw new RangeError('Portal anchor axes must be nonzero and independent');
    return freeze({ origin: point(origin), normal: n, right, up: V.cross(n, right) });
  }

  function doorway({ from, to, halfWidth, halfHeight, shape = 'rect' } = {}) {
    if (!positive(halfWidth) || !positive(halfHeight) || !['rect', 'ellipse'].includes(shape))
      throw new RangeError('A doorway needs positive half extents and a rectangular or elliptical aperture');
    const a = anchor(from), b = anchor(to);
    const project = (p, basis) => [V.dot(p, basis.right), V.dot(p, basis.up), V.dot(p, basis.normal)];
    const direction = value => {
      const [x, y, z] = project(point(value), a);
      return V.mad(V.mad(V.mul(b.right, -x), b.up, y), b.normal, -z);
    };
    const transformPoint = value => V.add(b.origin, direction(V.sub(point(value), a.origin)));
    function mapCamera(camera) {
      if (camera == null) return null;
      return freeze({ ...clone(camera), eye: transformPoint(camera.eye), right: direction(camera.right),
        up: direction(camera.up), back: direction(camera.back),
        ...(camera.target === undefined ? {} : { target: transformPoint(camera.target) }) });
    }
    function hit(previous, next, { radius = 0 } = {}) {
      if (!finite(radius) || radius < 0) throw new RangeError('Crossing radius must be nonnegative');
      const p = V.sub(point(previous), a.origin), q = V.sub(point(next), a.origin);
      const z0 = V.dot(p, a.normal), z1 = V.dot(q, a.normal);
      if (z0 < 0 || z1 >= 0 || radius >= Math.min(halfWidth, halfHeight)) return null;
      const fraction = z0 / (z0 - z1), at = V.mad(p, V.sub(q, p), fraction);
      const x = V.dot(at, a.right), y = V.dot(at, a.up);
      const fits = shape === 'ellipse' ?
        Math.hypot(x / halfWidth, y / halfHeight) + radius / Math.min(halfWidth, halfHeight) <= 1 :
        Math.abs(x) + radius <= halfWidth && Math.abs(y) + radius <= halfHeight;
      if (!fits) return null;
      return freeze({ fraction, point: V.add(a.origin, at) });
    }
    return Object.freeze({ from: a, to: b, halfWidth, halfHeight, shape,
      point: transformPoint, direction, camera: mapCamera, hit });
  }

  function unique(rows, kind) {
    if (!Array.isArray(rows) || rows.length > 4096) throw new TypeError('Expected a bounded list of ' + kind);
    const result = new Map();
    for (const row of rows) {
      if (!name(row?.id) || result.has(row.id)) throw new TypeError(kind + ' need unique IDs');
      result.set(row.id, row);
    }
    return result;
  }

  function create({ places, links = [], saved = {} } = {}) {
    const catalog = unique(places, 'Places'), graph = unique(links, 'Links');
    const exits = new Map(), away = new Map(), observers = new Set();
    let memory = savedStates(saved), clocks = new Map();
    let active = null, pending = null, restoring = null, stepping = false, handoff = false;
    let walking = false, fading = null, disposed = false;
    function savedStates(value) {
      if (!W.data.record(value)) throw new TypeError('Saved place state needs a JSON record keyed by place ID');
      return new Map(Object.entries(freeze(clone(value))));
    }
    for (const [id, row] of catalog) {
      const tickPolicy = row.tickPolicy ?? 'pause';
      if (!W.data.safeKey(id) || typeof row.prepare !== 'function' || !['pause', 'continue'].includes(tickPolicy))
        throw new TypeError('Each place needs a stable ID, a prepare callback and a pause or continue tick policy');
      const anchors = freeze(Object.fromEntries(Object.entries(row.anchors ?? {}).map(([key, value]) => [key, anchor(value)])));
      catalog.set(id, { id, anchors, prepare: row.prepare, tickPolicy });
    }
    function endpoint(value) {
      const place = catalog.get(value?.place), key = value?.anchor;
      const at = typeof key === 'string' && W.data.own(place?.anchors, key) && place.anchors[key];
      if (!at) throw new TypeError('Travel endpoints need a declared place and anchor');
      return Object.freeze({ place: place.id, anchor: value.anchor, at });
    }
    for (const [id, row] of graph) {
      const from = endpoint(row.from), to = endpoint(row.to), mode = row.mode ?? 'walk';
      const radius = row.radius ?? 1, height = row.height ?? 0.7, duration = row.duration ?? 0.8;
      if (!['walk', 'fade', 'drop'].includes(mode) || !positive(radius) || !positive(height) || !positive(duration) ||
          row.open !== undefined && typeof row.open !== 'function')
        throw new TypeError('Invalid travel mode, gate or trigger controls');
      if (row.transfer !== undefined && typeof row.transfer !== 'function')
        throw new TypeError('Link transfer must be a callback');
      const opening = mode === 'walk' ? doorway({ ...row.aperture, from: from.at, to: to.at }) : null;
      const sweep = mode === 'drop' ? doorway({ halfWidth: radius, halfHeight: radius, shape: 'ellipse',
        ...row.aperture, from: from.at, to: to.at }) : opening;
      const requires = row.requires === undefined ? undefined : freeze(clone(row.requires));
      W.query.condition(requires, {});
      const link = Object.freeze({ id, from, to, mode, opening, sweep, radius, height, duration,
        open: row.open, requires, transfer: row.transfer });
      graph.set(id, link);
      if (!exits.has(from.place)) exits.set(from.place, []);
      exits.get(from.place).push(link);
    }
    for (const outgoing of exits.values()) Object.freeze(outgoing);
    const noLinks = Object.freeze([]);

    const timeOf = id => clocks.get(id) ?? 0;
    function stateOf(id, asset) {
      const current = asset.checkpoint?.();
      return current === undefined ? memory.get(id) : current;
    }
    function guard() {
      if (disposed) throw new Error('The place session has been disposed');
      if (restoring || stepping || handoff) throw new Error('Place state is already being updated');
    }
    function permits(link, actor) {
      if (link.requires !== undefined && !W.query.condition(link.requires, {
        actor, get state() { return stateOf(active.id, active.asset); }, time: timeOf(active.id)
      })) return false;
      return !link.open || Boolean(link.open({ active, actor, link }));
    }
    function linked(id) {
      const link = graph.get(id);
      if (!link || link.from.place !== active?.id) throw new RangeError('This link does not start in the active place');
      return link;
    }
    const release = asset => {
      if (typeof asset?.dispose !== 'function' || asset === active?.asset) return;
      for (const resident of away.values()) if (resident === asset) return;
      asset.dispose();
    };
    function cancel() {
      const job = pending;
      pending = null;
      if (!job) return;
      job.controller.abort();
      release(job.asset);
    }
    function validateAsset(asset) {
      if (!asset || typeof asset !== 'object')
        throw new TypeError('Place preparation must return a payload');
      for (const method of ['step', 'checkpoint', 'prepareArrival', 'canArrive', 'dispose']) {
        if (asset[method] !== undefined && typeof asset[method] !== 'function')
          throw new TypeError('Place payload ' + method + ' must be a callback');
      }
      return asset;
    }
    function request(place, at, link, reason) {
      cancel();
      const from = active, controller = new AbortController(), job = { from, controller, place, link, asset: null };
      pending = job;
      job.done = Promise.resolve().then(async () => {
        if (controller.signal.aborted) return null;
        const previous = from?.id === place.id ? from.asset : away.get(place.id);
        job.borrowed = previous;
        const context = { id: place.id, anchor: at, state: memory.get(place.id), previous: previous ?? null,
          time: timeOf(place.id), signal: controller.signal, reason, link };
        if (previous && place.tickPolicy === 'continue') {
          if (previous.prepareArrival) {
            context.state = stateOf(place.id, previous);
            await previous.prepareArrival(context);
          }
          return previous;
        }
        return place.prepare(context);
      }).then(asset => {
        if (pending !== job) {
          if (asset !== job.borrowed) release(asset);
          return null;
        }
        try { job.asset = validateAsset(asset); }
        catch (error) { release(asset); throw error; }
        return asset;
      }).catch(error => {
        if (pending !== job) return null;
        pending = null;
        throw error;
      });
      return job;
    }
    function encounter(link, { actor, previous, radius } = {}) {
      if (!actor) return { status: 'outside' };
      if (!permits(link, actor)) return { status: 'locked' };
      if (link.sweep) {
        const crossing = previous == null ? null : link.sweep.hit(previous, actor.position, { radius });
        return crossing ? { crossing } : { status: 'outside' };
      }
      const delta = V.sub(point(actor.position), link.from.at.origin);
      return Math.hypot(delta[0], delta[2]) <= link.radius && Math.abs(delta[1]) <= link.height
        ? { crossing: null } : { status: 'outside' };
    }
    function shiftCamera(camera, delta) {
      return freeze({ ...camera, eye: V.add(point(camera.eye), delta),
        ...(camera.target == null ? {} : { target: V.add(point(camera.target), delta) }) });
    }
    function evaluateArrival(job, actor, camera, crossing) {
      const link = job.link;
      const opening = link.opening, drop = link.mode === 'drop', at = link.to.at;
      let arrival = freeze({ ...actor,
        position: opening ? opening.point(actor.position) : at.origin.slice(),
        ...(actor.velocity ? { velocity: opening ? opening.direction(actor.velocity) : drop ? point(actor.velocity) : [0, 0, 0] } : {}),
        ...(actor.forward && opening ? { forward: opening.direction(actor.forward) } : {}),
        ...(actor.up && opening ? { up: opening.direction(actor.up) } : {})
      });
      let mappedCamera = opening?.camera(camera) ?? null;
      if (drop && camera) mappedCamera = shiftCamera(camera, V.sub(arrival.position, actor.position));
      if (link.transfer) {
        const next = synchronous(link.transfer(Object.freeze({
          actor, arrival, link, crossing, source: job.from, destination: job.asset
        })), 'Link transfer');
        if (!W.data.record(next) || !xyz(next.position)) throw new TypeError('Link transfer must return an actor with a finite position');
        if (mappedCamera) mappedCamera = shiftCamera(mappedCamera, V.sub(next.position, arrival.position));
        arrival = freeze(clone(next));
      }
      const clear = !job.asset.canArrive || synchronous(job.asset.canArrive(arrival, link), 'Arrival clearance');
      return { status: clear ? 'ready' : 'blocked', link, actor: arrival, camera: mappedCamera, crossing };
    }
    function checkArrival(id, options) {
      guard();
      const link = linked(id), job = pending?.link === link ? pending : null;
      handoff = true;
      try {
        const contact = options === undefined ? null : encounter(link, options);
        const status = contact?.status ?? (job?.asset ? 'prepared' : job ? 'loading' : 'unprepared');
        if (!contact || status !== 'prepared') return Object.freeze({ status, link });
        return Object.freeze(evaluateArrival(job, freeze(clone(options.actor)),
          options.camera == null ? null : clone(options.camera), contact.crossing));
      } finally {
        handoff = false;
      }
    }
    function activate(job, actor, camera, crossing) {
      if (pending !== job || job.from !== active || !job.asset) return null;
      handoff = true;
      try {
        const link = job.link;
        let arrival = { link, actor: null, camera: null, crossing: null };
        if (link) {
          if (!permits(link, actor)) return null;
          const { status, ...candidate } = evaluateArrival(job, actor, camera, crossing);
          if (status !== 'ready') return null;
          arrival = candidate;
        }
        const source = active, state = source?.asset.checkpoint?.();
        if (state !== undefined) memory.set(source.id, freeze(clone(state)));
        away.delete(job.place.id);
        if (source && source.id !== job.place.id && catalog.get(source.id).tickPolicy === 'continue')
          away.set(source.id, source.asset);
        active = Object.freeze({ id: job.place.id, asset: job.asset });
        pending = null;
        if (!link) {
          release(source?.asset);
          return Object.freeze({ ...arrival, place: active });
        }
        const sourceDisposition = source.asset === active.asset ? 'reused' : away.has(source.id) ? 'retained' : 'released';
        const event = Object.freeze({ ...arrival, place: active, source, sourceDisposition });
        const errors = [];
        for (const observer of [...observers]) {
          try { synchronous(observer(event), 'Crossing listeners'); }
          catch (error) { errors.push(error); }
        }
        try { release(source.asset); }
        catch (error) { errors.push(error); }
        return errors.length ? Object.freeze({ ...event, errors: Object.freeze(errors) }) : event;
      } finally {
        handoff = false;
      }
    }
    function onCross(listener) {
      guard();
      if (typeof listener !== 'function') throw new TypeError('A crossing listener must be a callback');
      observers.add(listener);
      return () => observers.delete(listener);
    }
    function cancelPreparation(id = pending?.link?.id) {
      guard();
      if (!pending?.link || pending.link.id !== id || walking || fading) return false;
      cancel();
      return true;
    }

    async function enter(id, at) {
      guard();
      if (walking || fading) throw new Error('Travel is already in progress');
      const place = catalog.get(id);
      const target = typeof at === 'string' && W.data.own(place?.anchors, at) ? place.anchors[at] : null;
      if (!place || at !== undefined && !target) throw new RangeError('Unknown place or arrival anchor');
      const job = request(place, target, null, 'enter');
      if (!await job.done) return null;
      return activate(job, null, null, null)?.place ?? null;
    }
    function prepare(id) {
      guard();
      const link = linked(id);
      if (pending?.link === link) return pending.done;
      if (walking || fading) throw new Error('Travel is already in progress');
      return request(catalog.get(link.to.place), link.to.at, link, 'preview').done;
    }
    function approach(position, { distance = 8, actor } = {}) {
      guard();
      point(position);
      if (!positive(distance)) throw new RangeError('Preview distance must be positive');
      if (walking || fading) return null;
      let best = null, nearest = distance;
      for (const link of exits.get(active?.id) ?? []) {
        if (!link.opening || !permits(link, actor)) continue;
        const delta = V.sub(position, link.from.at.origin), d = V.len(delta);
        if (V.dot(delta, link.from.at.normal) >= 0 && (d < nearest || d === nearest && best && link.id < best.id)) {
          nearest = d;
          best = link;
        }
      }
      if (!best) {
        if (pending?.link?.opening) cancel();
        return null;
      }
      return Object.freeze({ link: best, ready: prepare(best.id) });
    }
    function view(id = pending?.link?.id, actor) {
      const job = pending, link = job?.link;
      if (!job?.asset || link?.id !== id || !link.opening || !permits(link, actor)) return null;
      return Object.freeze({ opening: link.opening, source: active.asset.world, destination: job.asset.world,
        link, asset: job.asset });
    }
    async function cross(id, { previous, actor, camera, radius } = {}) {
      guard();
      if (walking || fading) return null;
      const link = linked(id);
      if (!link.sweep) return null;
      const { crossing } = encounter(link, { actor, previous, radius });
      if (!crossing) return null;
      const traveler = freeze(clone(actor)), view = camera == null ? null : clone(camera);
      const loaded = prepare(id), job = pending;
      walking = true;
      try {
        if (!await loaded) return null;
        return activate(job, traveler, view, crossing);
      } finally {
        walking = false;
      }
    }
    function fade(id, { actor } = {}) {
      guard();
      if (walking || fading) throw new Error('Travel is already in progress');
      const link = linked(id);
      if (link.mode !== 'fade' || encounter(link, { actor }).status) return null;
      const loaded = prepare(id), job = pending, half = link.duration / 2;
      const traveler = freeze(clone(actor));
      let elapsed = 0, opacity = 0, phase = 'out', ready = false, error, arrival;
      loaded.then(value => {
        ready = true;
        if (!value) error = new Error('Destination preparation was cancelled');
      }, reason => { ready = true; error = reason; });
      const playback = Object.freeze({
        advance(dt) {
          guard();
          if (!finite(dt) || dt < 0) throw new RangeError('Fade steps need finite nonnegative time');
          if (phase === 'out') {
            const left = half - elapsed;
            elapsed = Math.min(half, elapsed + dt);
            opacity = elapsed / half;
            dt = Math.max(0, dt - left);
            if (elapsed === half) phase = 'hold';
          }
          if (phase === 'hold' && ready) {
            try {
              if (!error) arrival = activate(job, traveler, null, null);
            } catch (reason) {
              error = reason;
            }
            if (!arrival) error ??= new Error('Arrival is unavailable');
            if (pending === job) {
              try { cancel(); }
              catch (reason) { error ??= reason; }
            }
            elapsed = 0;
            phase = 'in';
          }
          if (phase === 'in') {
            elapsed = Math.min(half, elapsed + dt);
            opacity = 1 - elapsed / half;
            if (elapsed === half) {
              phase = error ? 'failed' : 'done';
              fading = null;
            }
          }
          return Object.freeze({ phase, opacity, arrival: arrival ?? null, error: error ?? null, place: active });
        }
      });
      fading = playback;
      return playback;
    }
    function place(id) {
      const definition = catalog.get(id);
      if (!definition) return null;
      return Object.freeze({ id, anchors: definition.anchors, tickPolicy: definition.tickPolicy, time: timeOf(id),
        status: active?.id === id ? 'active' : away.has(id) ? 'away' : 'inactive' });
    }
    function step(dt) {
      guard();
      if (!finite(dt) || dt < 0) throw new RangeError('Place steps need finite nonnegative time');
      if (!dt || !active) return;
      const residents = new Map(away).set(active.id, active.asset);
      const ids = [...residents.keys()].sort();
      if (ids.some(id => !finite(timeOf(id) + dt))) throw new RangeError('Place elapsed time is out of range');
      stepping = true;
      try {
        for (const id of ids) {
          const time = timeOf(id) + dt;
          synchronous(residents.get(id).step?.({ id, dt, time, active: id === active.id }), 'Place step callbacks');
          clocks.set(id, time);
        }
      } finally {
        stepping = false;
      }
    }
    function checkpoint() {
      guard();
      const states = new Map(memory), residents = new Map(away);
      if (active) residents.set(active.id, active.asset);
      for (const [id, asset] of residents) {
        const state = asset.checkpoint?.();
        if (state !== undefined) states.set(id, state);
      }
      return freeze({ place: active?.id ?? null, saved: clone(Object.fromEntries(states)),
        ...(clocks.size ? { clocks: Object.fromEntries(clocks) } : {}),
        ...(away.size ? { away: [...away.keys()].sort() } : {}) });
    }
    async function restore(data) {
      guard();
      if (active || pending) throw new Error('Restore needs an empty place session');
      if (!W.data.record(data) || data.place !== null && !catalog.has(data.place))
        throw new TypeError('Checkpoint needs a declared active place or null');
      const states = savedStates(data.saved);
      const times = data.clocks === undefined ? {} : data.clocks;
      if (!W.data.record(times) || !Object.entries(times).every(([id, time]) => catalog.has(id) && finite(time) && time >= 0))
        throw new TypeError('Invalid checkpoint place clocks');
      const nextClocks = new Map(Object.entries(times));
      const retained = data.away === undefined ? [] : data.away;
      if (!Array.isArray(retained) || retained.length > catalog.size || new Set(retained).size !== retained.length ||
          Array.from(retained).some(id => id === data.place || catalog.get(id)?.tickPolicy !== 'continue') ||
          retained.length && data.place === null)
        throw new TypeError('Invalid checkpoint away places');
      const current = data.place, background = retained.slice();
      const ids = current === null ? [] : [current, ...background];
      const controller = new AbortController(), assets = new Map();
      restoring = controller;
      try {
        for (const id of ids) {
          const asset = await catalog.get(id).prepare({ id, anchor: null, state: states.get(id), previous: null,
            time: nextClocks.get(id) ?? 0, signal: controller.signal, reason: 'restore', link: null });
          assets.set(id, asset);
          if (controller.signal.aborted) return null;
          validateAsset(asset);
        }
        memory = states;
        clocks = nextClocks;
        for (const id of background) away.set(id, assets.get(id));
        active = current === null ? null : Object.freeze({ id: current, asset: assets.get(current) });
        assets.clear();
        return active;
      } catch (error) {
        if (controller.signal.aborted) return null;
        throw error;
      } finally {
        restoring = null;
        for (const asset of new Set(assets.values())) release(asset);
      }
    }
    return Object.freeze({ current: () => active, place, linksFrom: id => exits.get(id) ?? noLinks,
      enter, approach, prepare, checkArrival, cancelPreparation, view, cross, fade, onCross, step, checkpoint, restore,
      dispose() {
        if (disposed) return;
        if (stepping || handoff) throw new Error('Place state is already being updated');
        disposed = true;
        observers.clear();
        restoring?.abort();
        const residents = new Set(away.values());
        if (active) residents.add(active.asset);
        try {
          cancel();
        } finally {
          active = null;
          away.clear();
          for (const asset of residents) release(asset);
        }
      } });
  }

  W.portals = Object.freeze({ anchor, doorway, create });
})(KIT);
