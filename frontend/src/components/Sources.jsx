export default function Sources({ observations }) {
  // Each web_search result already contains its own "1. ... 2. ... 3."
  // lines. Splitting those out and re-numbering as ONE flat, continuous
  // list (instead of stacking whole blocks) is what actually fixes the
  // "1, 2, 3... 1, 2, 3..." repeat. Failed/empty searches contribute
  // nothing here — they don't belong in "Sources Consulted".
  const seen = new Set();
  const items = [];

  observations
    .filter((o) => o.tool === "web_search" && !/^No results found/i.test(o.result))
    .forEach((o) => {
      o.result.split(/\n+/).forEach((line) => {
        const cleaned = line.replace(/^\d+\.\s*/, "").trim();
        // Skip truncation markers (executor.py's own "…" cut-off indicator)
        // and any leftover fragment that's just punctuation/ellipsis with no
        // real title — these aren't sources, they're display artifacts.
        const isJustPunctuation = /^[…"“”.\s]*$/.test(cleaned);
        if (cleaned && !isJustPunctuation && !seen.has(cleaned)) {
          seen.add(cleaned);
          items.push(cleaned);
        }
      });
    });

  if (!items.length) return null;

  return (
    <section className="panel">
      <h2>Sources Consulted</h2>
      <ol>
        {items.map((text, i) => (
          <li key={i}>{text}</li>
        ))}
      </ol>
    </section>
  );
}