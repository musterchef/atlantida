/* Ogni punto è [secondi attivi, latitudine, longitudine]. */
(function (root) {
  function frameAt(segments, elapsed) {
    const completed = [];
    let position = null;
    for (const points of segments) {
      if (!points.length || elapsed < points[0][0]) break;
      let lo = 0, hi = points.length;
      while (lo < hi) {
        const mid = (lo + hi) >>> 1;
        if (points[mid][0] <= elapsed) lo = mid + 1;
        else hi = mid;
      }
      const i = lo - 1, a = points[i], b = points[i + 1];
      position = a.slice(1);
      if (b) {
        const fraction = (elapsed - a[0]) / (b[0] - a[0]);
        position = [a[1] + fraction * (b[1] - a[1]), a[2] + fraction * (b[2] - a[2])];
      }
      const line = points.slice(0, lo).map(p => p.slice(1));
      if (b) line.push(position);
      completed.push(line);
    }
    return {position, completed};
  }
  root.DesnivelPosition = {frameAt};
  if (typeof module !== 'undefined') module.exports = {frameAt};
})(globalThis);
