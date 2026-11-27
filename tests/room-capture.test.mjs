import test from "node:test";
import assert from "node:assert/strict";
import { fileName, trials } from "../alfred/static/room-calibration.mjs";

test("le parcours exige le balayage, permet une reprise et télécharge dix prises nommées", async () => {
  const elements = new Map();
  const downloads = [];
  const audioEvents = new Map();
  let poll;
  let state;
  let wavCount = 0;
  const originalFetch = globalThis.fetch;

  function element(id) {
    if (!elements.has(id)) {
      elements.set(id, {
        value: "", reportValidity: () => true,
        addEventListener(event, handler) { this[event] = handler; },
      });
    }
    return elements.get(id);
  }

  Object.assign(globalThis, {
    document: {
      getElementById: id => element(id.replace("room-", "")),
      createElement: () => ({ click() { downloads.push(this); } }),
    },
    sessionStorage: { getItem: () => null, setItem() {}, removeItem() {} },
    window: { addEventListener() {} },
    Audio: class {
      paused = true;
      addEventListener(event, handler) {
        audioEvents.set(event, () => {
          this.paused = true;
          handler();
        });
      }
      pause() { this.paused = true; }
      async play() { this.paused = false; }
    },
    setInterval: callback => { poll = callback; },
    setTimeout: () => {},
    fetch: async (path, { method }) => {
      if (method === "POST") return Response.json({ token: "test", state: "waiting", remaining: 12 });
      if (method === "DELETE") return Response.json({ state: "interrompu", remaining: 12 });
      if (path.endsWith("/wav")) return new Response(Uint8Array.of(++wavCount));
      return Response.json({ state, remaining: state === "ready" ? 0 : 10 });
    },
  });

  await import("../alfred/static/room-capture.js");
  const tick = async next => {
    state = next;
    poll();
    await new Promise(resolve => setImmediate(resolve));
  };

  await element("start").click();
  await tick("ready");
  assert.equal(element("accept").hidden, true);
  assert.match(element("status").textContent, /Balayage incomplet/);

  for (let index = 0; index < trials.length; index++) {
    await element("start").click();
    await tick("recording");
    assert.equal(element("play").hidden, Boolean(trials[index].phrase));
    if (!trials[index].phrase) {
      await element("play").click();
      audioEvents.get("ended")();
    } else {
      assert.equal(element("phrase").textContent, `« ${trials[index].phrase} »`);
    }
    await tick("ready");
    assert.equal(element("accept").hidden, false);
    if (index === 2) {
      await element("cancel").click();
      assert.match(element("progress").textContent, /Étape 3 sur 10/);
      await element("start").click();
      await tick("ready");
    }
    element("accept").click();
  }
  assert.equal(wavCount, 11);
  assert.equal(element("title").textContent, "Parcours terminé");
  element("download").click();
  assert.match(downloads[0].download, /^alfred-salon-\d{4}-\d{2}-\d{2}\.zip$/);
  const bytes = await (await originalFetch(downloads[0].href)).arrayBuffer();
  const text = new TextDecoder().decode(bytes);
  for (const index of trials.keys()) assert.ok(text.includes(fileName(index)));
  assert.ok(text.includes("parcours.json"));
  URL.revokeObjectURL(downloads[0].href);
});
