/* Silent native-media proof. Resize mutates geometry only, never media state.
 * Source/event/clock decisions are compiled by composition.py, not duplicated here.
 * All boundary seeks, loads and decoded-frame callbacks remain inspectable.
 */
'use strict';
const number = value => {
  const parts = String(value).split('/').map(Number);
  const result = parts.length === 1 ? parts[0] : parts[0] / parts[1];
  if (!Number.isFinite(result)) throw new Error('Invalid compiled rational');
  return result;
};
const stage = document.querySelector('#stage');
const runtime = window.compositionRuntime = {
  ready: false, running: false, finished: false, error: null, frame: 0,
  events: [], nodes: new Map(), sources: new Map(), plan: null, origin: 0,
  orientation: null, layoutIndex: 0,
};
function record(type, id, details = {}) {
  runtime.events.push({type, id, frame: runtime.frame, wall: performance.now(), ...details});
}
function fail(error) {
  runtime.error = String(error); runtime.running = false;
  for (const node of runtime.nodes.values()) node.media.pause?.();
  stage.dataset.status = 'error';
  record('error', null, {message: String(error)});
}
function waitFor(media, event, action) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => finish(new Error(`Media timeout: ${event}`)), 10000);
    const good = () => finish();
    const bad = () => finish(new Error('Media decode failed'));
    function finish(error) {
      clearTimeout(timer); media.removeEventListener(event, good);
      media.removeEventListener('error', bad); error ? reject(error) : resolve();
    }
    media.addEventListener(event, good, {once: true});
    media.addEventListener('error', bad, {once: true});
    try { action(); } catch (error) { finish(error); }
  });
}
function frameProbe(node) {
  if (typeof node.media.requestVideoFrameCallback !== 'function') return;
  node.media.requestVideoFrameCallback((now, metadata) => {
    node.decoded = {wall: now, mediaTime: metadata.mediaTime, presentedFrames: metadata.presentedFrames};
    node.callbacks += 1;
    if (node.media.isConnected) frameProbe(node);
  });
}
function applyLayout() {
  if (!runtime.plan || runtime.nodes.size !== runtime.plan.tracks.length) return;
  const {width, height} = stage.getBoundingClientRect();
  if (width <= 0 || height <= 0) return;
  const orientation = width >= height ? 'landscape' : 'portrait';
  const layout = runtime.plan.layout_keyframes[runtime.layoutIndex].layouts[orientation];
  runtime.orientation = orientation;
  layout.cells.forEach((cell, z) => {
    const node = runtime.nodes.get(cell.loop);
    const [x,y,w,h] = cell.rect.map(number);
    Object.assign(node.box.style, {left:`${x*100}%`, top:`${y*100}%`,
      width:`${w*100}%`, height:`${h*100}%`, zIndex:String(z)});
    node.media.style.objectFit = cell.fit;
    node.media.style.objectPosition = cell.focal.map(v => `${number(v)*100}%`).join(' ');
  });
  record('layout', null, {orientation, width, height});
}
new ResizeObserver(applyLayout).observe(stage);

async function activate(node, span, frame, initial = false) {
  const source = runtime.sources.get(span.source);
  const kindChange = node.kind !== span.kind;
  if (kindChange) {
    node.media?.pause?.();
    node.media?.remove();
    node.media = document.createElement(span.kind === 'video' ? 'video' : 'img');
    node.media.dataset.loopId = node.id;
    node.media.setAttribute('aria-label', node.id);
    node.box.append(node.media); node.kind = span.kind;
    if (span.kind === 'video') {
      node.media.muted = true; node.media.defaultMuted = true;
      node.media.playsInline = true; node.media.preload = 'auto';
      node.media.addEventListener('loadstart', () => record('loadstart', node.id));
      node.media.addEventListener('seeking', () => record('seeking', node.id));
      node.media.addEventListener('error', () => fail(new Error(`Media failure: ${node.id}`)));
      frameProbe(node);
    }
  }
  const sourceChanged = node.source !== span.source || kindChange;
  node.span = span; node.source = span.source;
  if (sourceChanged) {
    record('source', node.id, {source: span.source});
    if (span.kind === 'video') await waitFor(node.media, 'loadeddata', () => { node.media.src = source.url; });
    else await waitFor(node.media, 'load', () => { node.media.src = source.url; });
  }
  if (span.kind === 'video') {
    const elapsed = (frame - span.frame) / runtime.plan.fps;
    const target = number(span.source_offset) + (span.held ? 0 : elapsed * number(span.rate));
    node.media.playbackRate = number(span.rate);
    node.media.pause();
    if (Math.abs(node.media.currentTime - target) > 0.00001) {
      record('seek-command', node.id, {target, reason: initial ? 'initial' : 'timeline-boundary'});
      await waitFor(node.media, 'seeked', () => { node.media.currentTime = target; });
    }
    if (!initial && runtime.running && !span.held) await node.media.play();
  }
  applyLayout();
}
function tick() {
  if (!runtime.running) return;
  const frame = Math.floor((performance.now() - runtime.origin) * runtime.plan.fps / 1000);
  runtime.frame = Math.min(frame, runtime.plan.frames - 1);
  if (frame >= runtime.plan.frames) {
    runtime.running = false; runtime.finished = true;
    for (const node of runtime.nodes.values()) node.media.pause?.();
    record('finished', null); stage.dataset.status = 'finished'; return;
  }
  try {
    const layouts = runtime.plan.layout_keyframes;
    while (runtime.layoutIndex + 1 < layouts.length && layouts[runtime.layoutIndex + 1].frame <= frame) {
      runtime.layoutIndex += 1; applyLayout();
    }
    for (const node of runtime.nodes.values()) {
      if (node.busy) continue;
      let next = node.index;
      while (next + 1 < node.spans.length && node.spans[next + 1].frame <= frame) next += 1;
      if (next !== node.index) {
        node.index = next; node.busy = true;
        activate(node, node.spans[next], frame).catch(fail).finally(() => { node.busy = false; });
      }
    }
  } catch (error) { fail(error); }
  requestAnimationFrame(tick);
}
runtime.start = async () => {
  if (!runtime.ready || runtime.running || runtime.finished || runtime.error) throw new Error('Runtime is not ready');
  runtime.origin = performance.now(); runtime.running = true;
  try {
    await Promise.all([...runtime.nodes.values()].filter(n => n.kind === 'video' && !n.span.held).map(n => n.media.play()));
    stage.dataset.status = 'playing'; requestAnimationFrame(tick);
  } catch (error) { fail(error); throw error; }
};
runtime.snapshot = () => ({
  frame: runtime.frame, wall: performance.now(), orientation: runtime.orientation,
  running: runtime.running, finished: runtime.finished, error: runtime.error,
  loops: [...runtime.nodes.values()].map(n => ({
    id:n.id, source:n.source, kind:n.kind, currentTime:n.media.currentTime ?? null,
    rate:n.media.playbackRate ?? 0, paused:n.media.paused ?? true, readyState:n.media.readyState ?? null,
    busy:n.busy, callbacks:n.callbacks, decoded:n.decoded,
    rect:n.box.getBoundingClientRect().toJSON(),
    quality:n.media.getVideoPlaybackQuality?.().toJSON?.() ?? (n.kind === 'video' ? {
      totalVideoFrames:n.media.getVideoPlaybackQuality().totalVideoFrames,
      droppedVideoFrames:n.media.getVideoPlaybackQuality().droppedVideoFrames} : null),
  })),
  eventCount: runtime.events.length,
});
// Tests may supply file-backed IO without enabling network access. Playback,
// layout, integrity comparisons and event handling use the identical code path.
const io = window.compositionIO || {
  async plan() {
    const response = await fetch('plan.json');
    if (!response.ok) throw new Error('Cannot load compiled plan');
    return response.json();
  },
  async bytes(source) {
    const response = await fetch(source.path);
    if (!response.ok) throw new Error(`Missing media: ${source.id}`);
    return response.arrayBuffer();
  },
  async digest(bytes) {
    if (!crypto.subtle) throw new Error('Secure context required for media hashing');
    return [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))].map(v => v.toString(16).padStart(2,'0')).join('');
  },
};
async function initialize() {
  runtime.plan = await io.plan();
  if (runtime.plan.plan_version !== 1 || runtime.plan.engine_version !== '1.0.0' || runtime.plan.audio !== 'none')
    throw new Error('Unsupported compiled plan');
  if (!runtime.plan.tracks.length || runtime.plan.tracks.length > 32) throw new Error('Loop guard');
  let total = 0;
  for (const source of runtime.plan.sources) {
    if (!/^media\/[a-f0-9]{64}\.[a-z0-9]+$/.test(source.path)) throw new Error('Unsafe media URL');
    total += source.bytes;
    if (total > 256*1024*1024) throw new Error('Media memory guard');
    const bytes = await io.bytes(source);
    const digest = await io.digest(bytes);
    if (digest !== source.sha256 || bytes.byteLength !== source.bytes) throw new Error(`Media integrity: ${source.id}`);
    const type = source.kind === 'video' ? 'video/mp4' : (source.path.endsWith('.png') ? 'image/png' : 'image/jpeg');
    runtime.sources.set(source.id, {url:URL.createObjectURL(new Blob([bytes], {type}))});
  }
  for (const track of runtime.plan.tracks) {
    if (runtime.nodes.has(track.id)) throw new Error('Duplicate loop');
    const box = document.createElement('div'); box.className = 'loop'; box.dataset.loopId = track.id; stage.append(box);
    runtime.nodes.set(track.id, {id:track.id, box, media:null, kind:null, source:null,
      spans:track.spans, index:0, span:null, callbacks:0, decoded:null, busy:false});
  }
  await Promise.all([...runtime.nodes.values()].map(n => activate(n, n.spans[0], 0, true)));
  runtime.ready = true; stage.dataset.status = 'ready'; applyLayout();
}
initialize().catch(fail);

// A local preview can be started directly without a developer console.
stage.tabIndex = 0;
stage.addEventListener('click', () => { if (runtime.ready && !runtime.running && !runtime.finished && !runtime.error) runtime.start().catch(fail); });
stage.addEventListener('keydown', event => { if (event.code === 'Space') { event.preventDefault(); stage.click(); } });
