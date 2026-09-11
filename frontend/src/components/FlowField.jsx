import { useEffect, useRef } from "react";

const SPACING = 26;
const SEGMENT = 9;

// Cheap smooth scalar field. Real Perlin noise would need a dependency, and the
// sum of a few offset sinusoids reads the same at this scale.
function fieldAngle(x, y, time) {
  return (
    Math.sin(x * 0.9 + time) * Math.cos(y * 0.8 - time * 0.7) +
    Math.sin((x + y) * 0.5 + time * 0.4) * 0.5
  );
}

export default function FlowField({ className, interactive = true }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const context = canvas.getContext("2d");
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    const pointer = { x: -999, y: -999, active: false };
    let ripples = [];
    let width = 0;
    let height = 0;
    let frame = 0;
    let start = performance.now();

    // Canvas cannot read CSS custom properties, so resolve them here and
    // refresh on resize, which is also when the theme switch repaints.
    let palette = { primary: "#7c5cff", secondary: "#22d3ee" };

    function readPalette() {
      const styles = getComputedStyle(canvas);
      palette = {
        primary: styles.getPropertyValue("--art-primary").trim() || palette.primary,
        secondary: styles.getPropertyValue("--art-secondary").trim() || palette.secondary,
      };
    }

    function resize() {
      const rect = canvas.getBoundingClientRect();
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      width = rect.width;
      height = rect.height;
      canvas.width = Math.max(1, Math.round(width * dpr));
      canvas.height = Math.max(1, Math.round(height * dpr));
      context.setTransform(dpr, 0, 0, dpr, 0, 0);
      readPalette();
    }

    function draw(now) {
      const time = reduceMotion ? 0 : (now - start) / 4000;
      context.clearRect(0, 0, width, height);
      ripples = ripples.filter((ripple) => now - ripple.born < 1600);

      for (let x = SPACING / 2; x < width; x += SPACING) {
        for (let y = SPACING / 2; y < height; y += SPACING) {
          let angle = fieldAngle(x / 90, y / 90, time) * Math.PI;
          let energy = 0;

          if (pointer.active) {
            const dx = x - pointer.x;
            const dy = y - pointer.y;
            const distance = Math.hypot(dx, dy);
            if (distance < 150) {
              const pull = 1 - distance / 150;
              // Segments swing to face the cursor, strongest at the centre.
              angle = angle * (1 - pull) + Math.atan2(dy, dx) * pull;
              energy = Math.max(energy, pull);
            }
          }

          for (const ripple of ripples) {
            const age = (now - ripple.born) / 1600;
            const radius = age * 260;
            const distance = Math.hypot(x - ripple.x, y - ripple.y);
            const band = Math.abs(distance - radius);
            if (band < 46) {
              const strength = (1 - band / 46) * (1 - age);
              angle += strength * 1.9;
              energy = Math.max(energy, strength);
            }
          }

          const length = SEGMENT * (1 + energy * 1.5);
          const cos = Math.cos(angle) * length;
          const sin = Math.sin(angle) * length;

          context.strokeStyle = energy > 0.04 ? palette.secondary : palette.primary;
          context.globalAlpha = 0.16 + energy * 0.7;
          context.lineWidth = 1 + energy * 1.1;
          context.beginPath();
          context.moveTo(x - cos / 2, y - sin / 2);
          context.lineTo(x + cos / 2, y + sin / 2);
          context.stroke();
        }
      }

      context.globalAlpha = 1;

      if (!reduceMotion) {
        frame = requestAnimationFrame(draw);
      }
    }

    function handlePointerMove(event) {
      const rect = canvas.getBoundingClientRect();
      pointer.x = event.clientX - rect.left;
      pointer.y = event.clientY - rect.top;
      pointer.active = true;
    }

    function handlePointerLeave() {
      pointer.active = false;
    }

    function handlePointerDown(event) {
      const rect = canvas.getBoundingClientRect();
      ripples.push({
        x: event.clientX - rect.left,
        y: event.clientY - rect.top,
        born: performance.now(),
      });
    }

    const observer = new ResizeObserver(resize);
    observer.observe(canvas);
    resize();

    if (reduceMotion) {
      draw(start);
    } else {
      frame = requestAnimationFrame(draw);
    }

    if (interactive && !reduceMotion) {
      canvas.addEventListener("pointermove", handlePointerMove);
      canvas.addEventListener("pointerleave", handlePointerLeave);
      canvas.addEventListener("pointerdown", handlePointerDown);
    }

    return () => {
      cancelAnimationFrame(frame);
      observer.disconnect();
      canvas.removeEventListener("pointermove", handlePointerMove);
      canvas.removeEventListener("pointerleave", handlePointerLeave);
      canvas.removeEventListener("pointerdown", handlePointerDown);
    };
  }, [interactive]);

  return <canvas ref={canvasRef} className={className} aria-hidden="true" />;
}
