/**
 * portfolio-grid.js — Irregular grid layout engine for raehu.com
 *
 * Lays out child elements in a gapless CSS Grid with irregular column widths
 * per row. Row heights are computed automatically so that every cell stays
 * landscape (wider than tall), using object-fit:cover for cropping.
 *
 * Usage (auto-layout — count children, generate pattern):
 *
 *   <div class="portfolio-grid">
 *     <img src="a.webp" alt="...">
 *     <img src="b.webp" alt="...">
 *     <!-- any number of children -->
 *   </div>
 *
 * Usage (manual override):
 *
 *   <div class="portfolio-grid" data-layout="7-5, 3-5-4, 5-7, 4-8">
 *     <!-- item count MUST match the pattern -->
 *   </div>
 *
 * Attributes:
 *
 *   data-layout   (optional) Comma-separated rows, each dash-separated column
 *                 spans on a 12-column grid. If omitted, a layout is generated
 *                 automatically from the number of children.
 *
 *   data-min-ar   (optional) Minimum aspect ratio for the narrowest cell.
 *                 Default: 1.35. Lower = taller rows, more cropping.
 *                 Higher = shorter rows, less cropping.
 *
 *   data-cols     (optional) Base column count. Default: 12.
 *
 *   data-seed     (optional) Integer seed for the layout generator, producing
 *                 a deterministic but varied pattern. Different seeds give
 *                 different arrangements for the same item count. Default: 0.
 *
 * Algorithm:
 *
 *   1. Count children N. If data-layout is set, use it (must match N).
 *      Otherwise, generate a layout for N items.
 *
 *   2. Generator partitions N into rows of 2 or 3 items, then assigns
 *      column spans from a pool of irregular presets. Adjacent rows never
 *      share the same span pattern. Column breaks are staggered so no
 *      vertical line runs through consecutive rows.
 *
 *   3. For each row with spans [s1, s2, ...] summing to S:
 *        narrowest_cell_width = (min(spans) / S) * container_width
 *        row_height = narrowest_cell_width / min_aspect_ratio
 *
 *      This guarantees every cell is at least min_aspect_ratio wide-to-tall.
 *      Images fill cells via object-fit:cover, cropping symmetrically.
 */

(function () {
  'use strict';

  var DEFAULT_MIN_AR = 1.35;
  var DEFAULT_COLS = 12;

  // --- Span presets (irregular, all sum to 12) ---

  var SPANS_2 = [
    [7, 5],
    [5, 7],
    [8, 4],
    [4, 8]
  ];

  var MOBILE_SPANS_2 = [
    [3, 3],
    [4, 2],
    [2, 4]
  ];

  var SPANS_3 = [
    [3, 5, 4],
    [4, 5, 3],
    [5, 4, 3],
    [3, 4, 5],
    [4, 3, 5],
    [5, 3, 4]
  ];

  // --- Seeded pseudo-random (deterministic per seed) ---

  function makeRng(seed) {
    // Simple mulberry32 PRNG
    var s = seed | 0;
    return function () {
      s = (s + 0x6D2B79F5) | 0;
      var t = Math.imul(s ^ (s >>> 15), 1 | s);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  function pick(arr, rng) {
    return arr[Math.floor(rng() * arr.length)];
  }

  // --- Layout generator ---

  function generateLayout(n, totalCols, seed) {
    if (n <= 0) return [];
    if (n === 1) return [[totalCols]];

    var rng = makeRng(seed);

    // Step 1: Partition N into row sizes (2 or 3)
    var rowSizes = partitionIntoRows(n, rng);

    // Step 2: Assign span patterns to each row, avoiding adjacent repeats
    var rows = [];
    var lastSpans = null;

    for (var i = 0; i < rowSizes.length; i++) {
      var size = rowSizes[i];
      var pool = size === 2 ? SPANS_2 : SPANS_3;
      var spans;
      var attempts = 0;

      // Pick a pattern that differs from the previous row
      do {
        spans = pick(pool, rng);
        attempts++;
      } while (spansMatch(spans, lastSpans) && attempts < 20);

      rows.push(spans);
      lastSpans = spans;
    }

    return rows;
  }

  function generateMobileLayout(n, seed) {
    if (n <= 0) return [];
    if (n === 1) return [[6]];

    var rng = makeRng(seed);
    var rows = [];
    var remaining = n;
    var lastSpans = null;

    while (remaining > 0) {
      if (remaining === 1) {
        rows.push([6]);
        remaining -= 1;
        lastSpans = [6];
        continue;
      }

      var spans;
      var attempts = 0;
      do {
        spans = pick(MOBILE_SPANS_2, rng);
        attempts++;
      } while (spansMatch(spans, lastSpans) && attempts < 20);

      rows.push(spans);
      remaining -= 2;
      lastSpans = spans;
    }

    return rows;
  }

  function partitionIntoRows(n, rng) {
    // Distribute N items into rows of 2 or 3.
    // Strategy: work backwards from N, choosing 2 or 3 per row,
    // making sure we never leave 1 remaining (which can't form a row).
    var sizes = [];
    var remaining = n;

    while (remaining > 0) {
      if (remaining === 1) {
        // Only possible if we get here — shouldn't with good partition.
        // Merge with previous row (make it a 2→3 or 3→4... but 4 is bad).
        // Safest: make the last row absorb it. We'll handle 1-item rows
        // by giving them full width.
        sizes.push(1);
        remaining = 0;
      } else if (remaining === 2) {
        sizes.push(2);
        remaining = 0;
      } else if (remaining === 3) {
        sizes.push(3);
        remaining = 0;
      } else if (remaining === 4) {
        // 4 = 2+2 (not 3+1)
        sizes.push(2);
        remaining = 2;
      } else {
        // remaining >= 5: pick 2 or 3 randomly
        var rowSize = rng() < 0.5 ? 2 : 3;
        sizes.push(rowSize);
        remaining -= rowSize;
      }
    }

    return sizes;
  }

  function spansMatch(a, b) {
    if (!a || !b || a.length !== b.length) return false;
    for (var i = 0; i < a.length; i++) {
      if (a[i] !== b[i]) return false;
    }
    return true;
  }

  // --- Layout parser (for manual data-layout) ---

  function parseLayout(str) {
    return str.split(',').map(function (row) {
      return row.trim().split('-').map(Number);
    });
  }

  // --- Main layout function ---

  function layoutGrid(container) {
    var containerWidth = container.offsetWidth;
    var isMobile = containerWidth > 0 && containerWidth < 560;
    var minAR = parseFloat(container.getAttribute('data-min-ar')) || DEFAULT_MIN_AR;
    var totalCols = parseInt(container.getAttribute('data-cols'), 10) || DEFAULT_COLS;
    var children = Array.prototype.slice.call(container.children);
    var n = children.length;

    if (n === 0) return;

    // Determine layout: manual override or auto-generate
    var rows;
    var layoutStr = isMobile ? null : container.getAttribute('data-layout');

    if (isMobile) {
      totalCols = 6;
      minAR = parseFloat(container.getAttribute('data-mobile-min-ar')) || 0.92;
    }

    if (layoutStr) {
      rows = parseLayout(layoutStr);
      var patternSlots = rows.reduce(function (sum, row) { return sum + row.length; }, 0);
      if (patternSlots !== n) {
        console.warn(
          'portfolio-grid: data-layout defines ' + patternSlots +
          ' slots but container has ' + n + ' items. Falling back to auto-layout.'
        );
        rows = null;
      }
    }

    if (!rows) {
      var seed = parseInt(container.getAttribute('data-seed'), 10) || 0;
      rows = isMobile ? generateMobileLayout(n, seed) : generateLayout(n, totalCols, seed);
    }

    // Set up CSS Grid
    container.style.display = 'grid';
    container.style.gridTemplateColumns = 'repeat(' + totalCols + ', 1fr)';
    container.style.gap = '0';

    var rowHeights = [];
    var itemIndex = 0;

    rows.forEach(function (row, rowIdx) {
      var rowSum = row.reduce(function (a, b) { return a + b; }, 0);
      var minSpan = Math.min.apply(null, row);

      // Narrowest cell width in pixels
      var minCellWidth = (minSpan / rowSum) * containerWidth;

      // Row height: keep narrowest cell at min aspect ratio
      var rowHeight = Math.round(minCellWidth / minAR);
      rowHeights.push(rowHeight + 'px');

      // Place each item in this row
      var colStart = 1;
      row.forEach(function (span) {
        if (itemIndex < children.length) {
          var child = children[itemIndex];
          child.style.gridColumn = colStart + ' / ' + (colStart + span);
          child.style.gridRow = String(rowIdx + 1);
          colStart += span;
          itemIndex++;
        }
      });
    });

    container.style.gridTemplateRows = rowHeights.join(' ');
  }

  // --- Initialization and resize handling ---

  var grids = [];

  function initAll() {
    grids = Array.prototype.slice.call(
      document.querySelectorAll('.portfolio-grid')
    );
    grids.forEach(layoutGrid);
  }

  function onResize() {
    grids.forEach(layoutGrid);
  }

  // Debounced resize
  var resizeTimer;
  window.addEventListener('resize', function () {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(onResize, 100);
  });

  // Run on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAll);
  } else {
    initAll();
  }

  // Public API for manual use
  window.portfolioGrid = {
    layout: layoutGrid,
    generate: generateLayout,
    initAll: initAll
  };

})();
