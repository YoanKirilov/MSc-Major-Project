/** Progressive enhancement only: report content never depends on an observer. */
export function reportViewport({ window, list }) {
  let observer;
  const marked = new WeakSet();
  const animate = row => {
    if (marked.has(row)) return;
    marked.add(row);
    // CSS/system reduced motion still wins. Focused controls never fade in.
    if (!row.contains(list.ownerDocument.activeElement)) row.classList.add('history-reveal');
    observer?.unobserve(row);
  };
  try {
    if (typeof window.IntersectionObserver === 'function') observer = new window.IntersectionObserver(entries => {
      for (const entry of entries) if (entry.isIntersecting) animate(entry.target);
    }, { threshold: 0, rootMargin: '0px 0px 64px 0px' });
  } catch { /* Normal visible content is the complete fallback. */ }
  list.addEventListener('focusin', event => {
    const row = event.target.closest('.history-report');
    if (!row) return;
    marked.add(row);
    row.classList.remove('history-reveal');
    observer?.unobserve(row);
  });
  window.addEventListener('pagehide', () => observer?.disconnect());
  return {
    update() {
      observer?.disconnect();
      for (const row of list.children) {
        if (marked.has(row)) continue;
        try { observer?.observe(row); } catch { observer?.disconnect(); observer = null; }
      }
    },
  };
}
