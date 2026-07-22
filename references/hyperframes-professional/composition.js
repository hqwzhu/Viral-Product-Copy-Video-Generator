(function () {
  "use strict";

  // The materializer embeds data in the page so required assets never depend on
  // a render-time network fetch. composition-data.json remains alongside it as
  // the inspectable source of truth.
  const dataNode = document.querySelector("#composition-data");
  let embeddedData = {};
  try {
    embeddedData = dataNode ? JSON.parse(dataNode.textContent || "{}") : {};
  } catch (error) {
    embeddedData = {};
  }
  const data = window.__HF_DATA__ || embeddedData || { shots: [], captions: [], motionTypes: [] };
  // Named motion categories are retained in the composition for quality
  // inspection: zoomPan, productHighlight, and sceneTransition.
  const motionTypes = ["zoomPan", "productHighlight", "sceneTransition"];
  // HyperFrames loads the entry document in both a regular page and a
  // lightweight validation document. Keep a safe fallback for the latter;
  // normal renders always use the explicit composition root.
  const root = document.querySelector("#root") || document.body || document.documentElement;
  const timeline = gsap.timeline({ paused: true, defaults: { ease: "power2.out" } });
  const shots = Array.isArray(data.shots) ? data.shots : [];
  const escapeHtml = (value) => String(value ?? "").replace(/[&<>'"]/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "'": "&#39;",
    '"': "&quot;",
  }[character]));

  const addShot = (shot, index) => {
    const frame = document.createElement("section");
    frame.id = `shot-${shot.id || index}`;
    frame.className = `clip shot ${shot.kind || "product"}`;
    frame.dataset.start = String(shot.start || 0);
    frame.dataset.duration = String(shot.duration || 1);
    frame.dataset.trackIndex = String(index + 1);
    const mediaSource = String(shot.src || "");
    const safeMediaSource = escapeHtml(mediaSource);
    const isVideo = shot.mediaType === "video" || /\.(mp4|webm|mov)$/i.test(mediaSource);
    const mediaMarkup = isVideo
      ? `<video src="${safeMediaSource}" muted playsinline preload="auto"></video>`
      : `<img src="${safeMediaSource}" alt="Product demonstration" />`;
    const eyebrow = escapeHtml(shot.eyebrow || "ENHE PRODUCT DEMO");
    const title = escapeHtml(shot.title || "A clearer workflow");
    const subtitle = escapeHtml(shot.subtitle || "Show the real product, with motion that explains why it matters.");
    frame.innerHTML = `
      <div class="shot-visual">
        <div class="product-frame">${mediaMarkup}</div>
        <div class="product-highlight" aria-hidden="true"></div>
        <div class="pointer" aria-hidden="true"></div>
      </div>
      <div class="shot-copy"><p class="eyebrow">${eyebrow}</p><h1>${title}</h1><p>${subtitle}</p></div>
      <div class="brand">ENHE <span>AI</span></div>
      <div class="transition-wash" aria-hidden="true"></div>`;
    root.appendChild(frame);
    const start = Number(shot.start || 0);
    const duration = Math.max(0.8, Number(shot.duration || 1));
    const image = frame.querySelector("img, video");
    const highlight = frame.querySelector(".product-highlight");
    const pointer = frame.querySelector(".pointer");
    const wash = frame.querySelector(".transition-wash");
    gsap.set(frame, { opacity: 0 });
    gsap.set(highlight, { opacity: 0, scale: 0.72 });
    gsap.set(pointer, { opacity: 0, x: -80, y: 50 });
    gsap.set(wash, { opacity: 0 });
    timeline.to(frame, { opacity: 1, duration: 0.45 }, start);
    timeline.fromTo(image, { scale: 1.06, x: 0, y: 0 }, { scale: 1.15, x: Number(shot.panX || 0), y: Number(shot.panY || 0), duration: Math.max(.5, duration - .35) }, start + .15);
    timeline.to(highlight, { opacity: 1, scale: 1, duration: .34 }, start + Math.min(.8, duration / 3));
    timeline.to(pointer, { opacity: 1, x: Number(shot.pointerX || 120), y: Number(shot.pointerY || -20), duration: .48 }, start + Math.min(1.1, duration / 2));
    timeline.to(wash, { opacity: 1, duration: .24 }, start + duration - .45);
    timeline.to(frame, { opacity: 0, duration: .36 }, start + duration - .36);
  };

  shots.forEach(addShot);
  const captions = Array.isArray(data.captions) ? data.captions : [];
  captions.forEach((caption, index) => {
    const node = document.createElement("div");
    node.id = `caption-${index}`;
    node.className = "clip caption";
    node.dataset.start = String(caption.start || 0);
    node.dataset.duration = String(caption.duration || 1);
    node.dataset.trackIndex = String(40 + index);
    node.innerHTML = `<p>${escapeHtml(caption.text || "")}</p>`;
    root.appendChild(node);
    timeline.fromTo(node, { opacity: 0, y: 18 }, { opacity: 1, y: 0, duration: .2 }, Number(caption.start || 0));
    timeline.to(node, { opacity: 0, y: -10, duration: .2 }, Number(caption.start || 0) + Math.max(.3, Number(caption.duration || 1) - .2));
  });
  if (data.voiceover) {
    const audio = document.createElement("audio");
    audio.id = "voiceover";
    audio.src = data.voiceover;
    audio.preload = "auto";
    audio.dataset.start = "0";
    audio.dataset.duration = String(data.duration || 20);
    audio.dataset.trackIndex = "80";
    audio.dataset.volume = "1";
    root.appendChild(audio);
  }
  const brand = document.createElement("section");
  brand.id = "brand-outro";
  brand.className = "clip intro-outro";
  brand.dataset.start = String(Math.max(0, Number(data.duration || 20) - 2));
  brand.dataset.duration = "2";
  brand.dataset.trackIndex = "60";
  brand.innerHTML = '<div><p class="eyebrow">ENHE AI</p><h1>Make every product moment clear.</h1><p>Real capture. Intentional motion. Local-first production.</p></div>';
  root.appendChild(brand);
  timeline.fromTo(brand, { opacity: 0, scale: .96 }, { opacity: 1, scale: 1, duration: .45 }, Number(brand.dataset.start));

  window.__timelines = window.__timelines || {};
  window.__timelines.root = timeline;
})();
