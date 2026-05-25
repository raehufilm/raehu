/**
 * portfolio-grid.js — Irregular grid layout engine for raehu.com
 *
 * Lays out child elements in a gapless CSS Grid with irregular column widths
 * per row. Row heights are computed automatically so that every cell stays
 * landscape (wider than tall), using object-fit:cover for cropping.
 *
 * Usage:
 *
 *   <div class="portfolio-grid" data-layout="7-5, 3-5-4, 5-4-3, 4-8">
 *     <img src="a.webp" alt="...">
 *     <img src="b.webp" alt="...">
 *     <!-- one child per cell, 10 total for the pattern above -->
 *   </div>
 *   <script src="/js/portfolio-grid.js"></script>
 *
 * Attributes:
 *
 *   data-layout   Comma-separated rows. Each row is dash-separated column
 *                 spans on a 12-column grid (configurable via data-cols).
 *                 "7-5, 3-5-4" = row 1 has items spanning 7 and 5 cols;
 *                 row 2 has items spanning 3, 5, and 4 cols.
 *
 *   data-min-ar   (optional) Minimum aspect ratio for the narrowest cell in
 *                 any row. Default: 1.35. Lower = taller rows, more cropping.
 *                 Higher = shorter rows, less cropping. The landscape
 *                 constraint is: min-ar > 1.
 *
 *   data-cols     (optional) Total columns in the base grid. Default: 12.
 *
 * Algorithm:
 *
 *   For each row with spans [s1, s2, ...] summing to S:
 *     narrowest_cell_width = (min(spans) / S) * container_width
 *     row_height = narrowest_cell_width / min_aspect_ratio
 *
 *   This guarantees every cell is at least min_aspect_ratio wide-to-tall.
 *   Wider cells in the same row will have even higher aspect ratios.
 *   Images fill cells via object-fit:cover, cropping symmetrically.
 */

(function () {
  'use strict';

  var DEFAULT_MIN_AR = 1.35;
  var DEFAULT_COLS = 12;

  function parseLayout(str) {
    return str.split(',').map(function (row) {
      return row.trim().split('-').map(Number);
    });
  }

  function layoutGrid(container) {
    var layoutStr = container.getAttribute('data-layout');
    if (!layoutStr) return;

    var minAR = parseFloat(container.getAttribute('data-min-ar')) || DEFAULT_MIN_AR;
    var totalCols = parseInt(container.getAttribute('data-cols'), 10) || DEFAULT_COLS;
    var rows = parseLayout(layoutStr);

    // Count expected items
    var totalItems = rows.reduce(function (sum, row) { return sum + row.length; }, 0);
    var children = Array.prototype.slice.call(container.children);

    if (children.length < totalItems) {
      console.warn(
        'portfolio-grid: layout expects ' + totalItems +
        ' items but container has ' + children.length
      );
    }

    // Measure container width for height calculations
    var containerWidth = container.offsetWidth;

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
      document.querySelectorAll('.portfolio-grid[data-layout]')
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
    initAll: initAll
  };

})();
