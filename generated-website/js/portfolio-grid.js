/**
 * portfolio-grid.js — Irregular grid layout engine for raehu.com
 *
 * Lays out child elements in either:
 *   - an irregular CSS Grid that crops media into editorial cells, or
 *   - a justified natural-ratio mode that preserves each media frame.
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
 *   data-layout   (optional) For cropped grid mode, comma-separated rows, each
 *                 dash-separated column spans on a 12-column grid. If omitted,
 *                 a layout is generated automatically from child count.
 *
 *   data-min-ar   (optional) Minimum aspect ratio for the narrowest cell.
 *                 Default: 1.35. Lower = taller rows, more cropping.
 *                 Higher = shorter rows, less cropping.
 *
 *   data-grid-mode (optional) "justify" preserves media ratios by calculating
 *                 item widths/heights from each row's media aspect ratios.
 *                 Omit for the original irregular cropped grid.
 *
 *   data-justify-max-items (optional) Maximum items per justified desktop row.
 *                 Default: 3.
 *
 *   data-justify-mobile-max-items (optional) Maximum items per justified mobile
 *                 row. Default: 2.
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
 *
 *   In data-grid-mode="justify", the irregular grid's row-planning idea is
 *   reused: desktop/tablet candidates are scored for deterministic 2/3 row
 *   rhythm, transition count, row-height variation, and repeat avoidance.
 *   A layout with the same item count in every row is treated as invalid when
 *   there is enough media to vary the rhythm. Mobile is mostly 2-item rows,
 *   with 1-item rows inserted only to avoid uniform stacks or handle odd
 *   counts.
 *   Once rows are chosen, each row is rendered as a real row wrapper and item
 *   dimensions are calculated from media aspect ratios. This preserves frames
 *   without the greedy single-column stacking failure mode.
 */

(function () {
  'use strict';

  var DEFAULT_MIN_AR = 1.35;
  var DEFAULT_COLS = 12;
  var DEFAULT_MEDIA_AR = 16 / 9;
  var JUSTIFIED_ROW_CLASS = 'portfolio-grid-row';

  // --- Span presets (irregular, all sum to 12) ---

  var SPANS_2 = [
    [7, 5],
    [5, 7],
    [8, 4],
    [4, 8]
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

  function generateMobileLayout(children, totalCols, seed) {
    var n = children.length;
    if (n <= 0) return [];
    if (n === 1) return [[totalCols]];

    var rows = [];
    var rowSizes = partitionMobileIntoRows(n, seed);
    var itemIndex = 0;

    rowSizes.forEach(function (rowSize) {
      if (rowSize === 1) {
        rows.push([totalCols]);
        itemIndex += 1;
        return;
      }

      rows.push(spansForAspectRatios(
        children.slice(itemIndex, itemIndex + rowSize).map(childAspectRatio),
        totalCols
      ));
      itemIndex += rowSize;
    });

    return rows;
  }

  function partitionMobileIntoRows(n, seed) {
    var rng = makeRng(seed);
    var sizes = [];
    var remaining = n;
    var lastSize = 0;

    while (remaining > 0) {
      var candidates = [1, 2].filter(function (size) {
        return size <= remaining;
      });

      if (lastSize === 1 && candidates.length > 1) {
        candidates = candidates.filter(function (size) {
          return size !== 1;
        });
      }

      var size = pickWeightedRowSize(candidates, lastSize, remaining, rng);
      sizes.push(size);
      remaining -= size;
      lastSize = size;
    }

    return sizes;
  }

  function pickWeightedRowSize(candidates, lastSize, remaining, rng) {
    var totalWeight = 0;
    var weighted = candidates.map(function (size) {
      var weight = size === 1 ? 0.34 : 0.66;

      if (size === lastSize && candidates.length > 1) {
        weight *= 0.62;
      }

      if (remaining - size === 1 && candidates.indexOf(1) !== -1) {
        weight *= 0.75;
      }

      totalWeight += weight;
      return {
        size: size,
        weight: weight
      };
    });

    var target = rng() * totalWeight;
    var cursor = 0;

    for (var i = 0; i < weighted.length; i++) {
      cursor += weighted[i].weight;
      if (target <= cursor) {
        return weighted[i].size;
      }
    }

    return weighted[weighted.length - 1].size;
  }

  function spansForAspectRatios(ratios, totalCols) {
    if (ratios.length === 1) return [totalCols];

    var sum = ratios.reduce(function (total, ratio) {
      return total + Math.max(0.2, ratio);
    }, 0);
    var spans = ratios.map(function (ratio) {
      return Math.round((Math.max(0.2, ratio) / sum) * totalCols);
    });

    spans = spans.map(function (span) {
      return Math.max(1, Math.min(totalCols - 1, span));
    });

    var delta = totalCols - spans.reduce(function (total, span) {
      return total + span;
    }, 0);

    while (delta !== 0) {
      var adjustableIndex = -1;
      var bestRemainder = delta > 0 ? -Infinity : Infinity;

      for (var i = 0; i < ratios.length; i++) {
        var idealSpan = (Math.max(0.2, ratios[i]) / sum) * totalCols;
        var remainder = idealSpan - spans[i];
        var canGrow = delta > 0 && spans[i] < totalCols - 1;
        var canShrink = delta < 0 && spans[i] > 1;

        if (canGrow && remainder > bestRemainder) {
          bestRemainder = remainder;
          adjustableIndex = i;
        }

        if (canShrink && remainder < bestRemainder) {
          bestRemainder = remainder;
          adjustableIndex = i;
        }
      }

      if (adjustableIndex === -1) break;

      spans[adjustableIndex] += delta > 0 ? 1 : -1;
      delta += delta > 0 ? -1 : 1;
    }

    return spans;
  }

  function childAspectRatio(child) {
    var media = child.matches && child.matches('img, video')
      ? child
      : child.querySelector && child.querySelector('img, video');

    var childRatio = aspectRatioFromElement(child);
    if (childRatio) return childRatio;

    if (!media) return DEFAULT_MEDIA_AR;

    var mediaRatio = aspectRatioFromElement(media);
    if (mediaRatio) return mediaRatio;

    if (media.tagName === 'IMG' && media.naturalWidth && media.naturalHeight) {
      return media.naturalWidth / media.naturalHeight;
    }

    if (media.tagName === 'VIDEO' && media.videoWidth && media.videoHeight) {
      return media.videoWidth / media.videoHeight;
    }

    return DEFAULT_MEDIA_AR;
  }

  function aspectRatioFromElement(element) {
    if (!element || !element.getAttribute) return null;

    var ratio = parseFloat(element.getAttribute('data-aspect-ratio'));
    if (ratio && isFinite(ratio) && ratio > 0) return ratio;

    var width = parseFloat(element.getAttribute('width'));
    var height = parseFloat(element.getAttribute('height'));
    if (width && height && isFinite(width) && isFinite(height) && width > 0 && height > 0) {
      return width / height;
    }

    return null;
  }

  function gridSeed(container, layoutStr, children) {
    var explicitSeed = parseInt(container.getAttribute('data-seed'), 10);
    if (!isNaN(explicitSeed)) return explicitSeed;

    var seedText = layoutStr || '';
    seedText += '|' + children.map(childSourceKey).join('|');
    return hashString(seedText) || children.length;
  }

  function childSourceKey(child) {
    var media = child.matches && child.matches('img, video')
      ? child
      : child.querySelector && child.querySelector('img, video');

    if (media) {
      return media.getAttribute('src') ||
        media.getAttribute('data-src') ||
        media.getAttribute('poster') ||
        '';
    }

    return child.getAttribute('href') || child.textContent || '';
  }

  function hashString(str) {
    var hash = 0;

    for (var i = 0; i < str.length; i++) {
      hash = Math.imul(31, hash) + str.charCodeAt(i) | 0;
    }

    return hash;
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

  function resetGridChild(child) {
    child.style.gridColumn = '';
    child.style.gridRow = '';
    child.style.width = '';
    child.style.height = '';
    child.style.flex = '';
    child.style.maxWidth = '';
  }

  function isJustifiedRow(element) {
    return element &&
      element.classList &&
      element.classList.contains(JUSTIFIED_ROW_CLASS);
  }

  function gridItems(container) {
    var items = [];

    Array.prototype.slice.call(container.children).forEach(function (child) {
      if (isJustifiedRow(child)) {
        Array.prototype.slice.call(child.children).forEach(function (rowChild) {
          items.push(rowChild);
        });
        return;
      }

      items.push(child);
    });

    return items;
  }

  function restoreDirectChildren(container, children) {
    var hasRows = Array.prototype.slice.call(container.children).some(isJustifiedRow);
    if (!hasRows) return;

    var fragment = document.createDocumentFragment();
    children.forEach(function (child) {
      fragment.appendChild(child);
    });

    while (container.firstChild) {
      container.removeChild(container.firstChild);
    }

    container.appendChild(fragment);
  }

  function buildJustifiedRows(children, seed, container, isMobile) {
    var maxItems = isMobile
      ? parseInt(container.getAttribute('data-justify-mobile-max-items'), 10) || 2
      : parseInt(container.getAttribute('data-justify-max-items'), 10) || 3;
    var rowSizes = plannedJustifiedRowSizes(
      children.length,
      seed,
      maxItems,
      isMobile,
      container.getAttribute('data-layout') || '',
      children.map(childAspectRatio)
    );
    var index = 0;

    return rowSizes.map(function (rowSize) {
      var row = children.slice(index, index + rowSize);
      index += rowSize;
      return row;
    }).filter(function (row) {
      return row.length > 0;
    });
  }

  function plannedJustifiedRowSizes(count, seed, maxItems, isMobile, layoutStr, aspectRatios) {
    if (count <= 0) return [];
    if (count === 1) return [1];

    var rowMax = Math.max(1, Math.min(maxItems || 3, 3));
    if (rowMax <= 1) return repeatRowSize(count, 1);

    if (isMobile || rowMax === 2) {
      return mostlyPairRows(count, seed);
    }

    var layoutRows = rowSizesFromLayout(layoutStr, count, rowMax);
    var scoredPlan = bestScoredRowPlan(
      count,
      seed,
      rowMax,
      layoutRows,
      aspectRatios || []
    );

    if (scoredPlan) return scoredPlan;

    return partitionIntoRows(count, makeRng(seed));
  }

  function rowSizesFromLayout(layoutStr, count, maxItems) {
    if (!layoutStr) return null;

    var rows = parseLayout(layoutStr);
    var sizes = rows.map(function (row) {
      return row.length;
    });
    var total = sizes.reduce(function (sum, size) {
      return sum + size;
    }, 0);
    var valid = total === count && sizes.every(function (size) {
      return size > 0 && size <= maxItems;
    });

    return valid ? sizes : null;
  }

  function bestScoredRowPlan(count, seed, maxItems, layoutRows, aspectRatios) {
    var candidates = candidateRowSizePlans(count, maxItems);
    candidates = nonUniformCandidatesOrOriginal(candidates);

    if (candidates.length && candidates.every(isUniformRowPlan)) {
      candidates = nonUniformCandidatesOrOriginal(
        candidateRowSizePlans(count, maxItems, true)
      );
    }

    if (!candidates.length) return null;

    var best = null;
    var bestScore = -Infinity;

    candidates.forEach(function (plan) {
      var score = scoreJustifiedRowPlan(plan, seed, layoutRows, aspectRatios);
      if (score > bestScore) {
        bestScore = score;
        best = plan;
      }
    });

    return best;
  }

  function candidateRowSizePlans(count, maxItems, allowSingleRows) {
    if (count > 24) return [];

    var candidates = [];
    var sizes = [];
    var minSize = allowSingleRows ? 1 : 2;
    for (var size = minSize; size <= Math.max(minSize, maxItems); size++) {
      sizes.push(size);
    }

    function collect(remaining, rows) {
      if (remaining === 0) {
        candidates.push(rows.slice());
        return;
      }

      sizes.forEach(function (size) {
        if (size <= remaining) {
          rows.push(size);
          collect(remaining - size, rows);
          rows.pop();
        }
      });
    }

    collect(count, []);
    return candidates;
  }

  function nonUniformCandidatesOrOriginal(candidates) {
    var varied = candidates.filter(function (plan) {
      return !isUniformRowPlan(plan);
    });

    return varied.length ? varied : candidates;
  }

  function isUniformRowPlan(plan) {
    return plan.length > 1 && plan.every(function (size) {
      return size === plan[0];
    });
  }

  function scoreJustifiedRowPlan(plan, seed, layoutRows, aspectRatios) {
    var score = seededPlanJitter(plan, seed);
    var rowCounts = {};
    var repeatCount = 0;
    var transitionCount = 0;
    var runLength = 1;
    var maxRunLength = 1;

    plan.forEach(function (size, index) {
      rowCounts[size] = (rowCounts[size] || 0) + 1;

      if (index === 0) return;

      if (size === plan[index - 1]) {
        repeatCount++;
        runLength++;
        maxRunLength = Math.max(maxRunLength, runLength);
      } else {
        transitionCount++;
        runLength = 1;
      }
    });

    var singletonCount = rowCounts[1] || 0;
    var uniqueSizes = Object.keys(rowCounts);
    score += transitionCount * 9;
    score -= repeatCount * 18;
    score -= Math.max(0, maxRunLength - 2) * 18;
    score -= singletonCount * 10;

    if (uniqueSizes.length === 1 && plan.length > 1) {
      score -= 120;
    }

    var idealRows = plan.reduce(function (sum, size) {
      return sum + size;
    }, 0) / 2.55;
    score -= Math.abs(plan.length - idealRows) * 2;

    uniqueSizes.forEach(function (sizeKey) {
      if (rowCounts[sizeKey] !== 1 || plan.length <= 2) return;

      var uniqueIndex = plan.indexOf(parseInt(sizeKey, 10));
      if (uniqueIndex === 0 || uniqueIndex === plan.length - 1) {
        score -= 5;
      } else {
        score += 3;
      }
    });

    if (layoutRows && layoutRows.length) {
      var sharedLength = Math.min(layoutRows.length, plan.length);
      for (var i = 0; i < sharedLength; i++) {
        if (layoutRows[i] === plan[i]) score += 0.65;
      }
      score -= Math.abs(layoutRows.length - plan.length) * 0.35;
    }

    var rowHeights = rowHeightProxies(plan, aspectRatios);
    for (var j = 1; j < rowHeights.length; j++) {
      score += Math.min(0.16, Math.abs(rowHeights[j] - rowHeights[j - 1])) * 32;
    }

    rowHeights.forEach(function (height) {
      if (height > 0.42) {
        score -= (height - 0.42) * 80;
      }
    });

    return score;
  }

  function rowHeightProxies(plan, aspectRatios) {
    var index = 0;

    return plan.map(function (rowSize) {
      var aspectSum = 0;
      for (var i = 0; i < rowSize; i++) {
        aspectSum += aspectRatios[index + i] || DEFAULT_MEDIA_AR;
      }
      index += rowSize;
      return 1 / Math.max(0.1, aspectSum);
    });
  }

  function seededPlanJitter(plan, seed) {
    var unsigned = hashString(plan.join('-') + '|' + seed) >>> 0;
    return (unsigned / 4294967296) * 0.001;
  }

  function mostlyPairRows(count, seed) {
    if (count <= 0) return [];
    if (count === 1) return [1];

    var pairCount = Math.floor(count / 2);
    var rows = repeatRowSize(pairCount, 2);

    if (count % 2 === 0) {
      if (rows.length <= 1) return rows;

      var splitRng = makeRng(seed);
      var splitIndex = Math.floor(splitRng() * Math.max(1, rows.length - 1));
      rows.splice(splitIndex, 2, 1, 2, 1);
      return rows;
    }

    if (rows.length <= 1) {
      rows.push(1);
      return rows;
    }

    var rng = makeRng(seed);
    var insertPosition = 1 + Math.floor(rng() * Math.max(1, rows.length - 1));
    rows.splice(insertPosition, 0, 1);
    return rows;
  }

  function repeatRowSize(count, size) {
    var rows = [];
    for (var i = 0; i < count; i++) {
      rows.push(size);
    }
    return rows;
  }

  function layoutJustifiedGrid(container, children, containerWidth) {
    var isMobile = containerWidth > 0 && containerWidth < 560;
    var seed = gridSeed(container, '', children);
    var rows = buildJustifiedRows(children, seed, container, isMobile);
    var fragment = document.createDocumentFragment();

    container.style.display = 'block';
    container.style.flexWrap = '';
    container.style.alignItems = '';
    container.style.gap = '0';
    container.style.gridTemplateColumns = '';
    container.style.gridTemplateRows = '';

    rows.forEach(function (row) {
      var aspectSum = row.reduce(function (sum, child) {
        return sum + childAspectRatio(child);
      }, 0);
      var rowHeight = containerWidth / Math.max(0.1, aspectSum);
      var rowEl = document.createElement('div');

      rowEl.className = JUSTIFIED_ROW_CLASS;
      rowEl.style.display = 'flex';
      rowEl.style.width = '100%';
      rowEl.style.height = rowHeight + 'px';
      rowEl.style.alignItems = 'flex-start';
      rowEl.style.gap = '0';

      row.forEach(function (child) {
        var widthPercent = (childAspectRatio(child) / Math.max(0.1, aspectSum)) * 100;
        child.style.width = widthPercent + '%';
        child.style.height = rowHeight + 'px';
        child.style.flex = '0 0 ' + widthPercent + '%';
        child.style.maxWidth = widthPercent + '%';
        child.style.gridColumn = '';
        child.style.gridRow = '';
        rowEl.appendChild(child);
      });

      fragment.appendChild(rowEl);
    });

    while (container.firstChild) {
      container.removeChild(container.firstChild);
    }

    container.appendChild(fragment);
    notifyGridLayout(container);
  }

  function notifyGridLayout(container) {
    var event;
    if (typeof CustomEvent === 'function') {
      event = new CustomEvent('portfolio-grid:layout', { bubbles: true });
    } else {
      event = document.createEvent('CustomEvent');
      event.initCustomEvent('portfolio-grid:layout', true, false, null);
    }
    container.dispatchEvent(event);
  }

  // --- Main layout function ---

  function layoutGrid(container) {
    var containerWidth = container.offsetWidth;
    var isMobile = containerWidth > 0 && containerWidth < 560;
    var minAR = parseFloat(container.getAttribute('data-min-ar')) || DEFAULT_MIN_AR;
    var totalCols = parseInt(container.getAttribute('data-cols'), 10) || DEFAULT_COLS;
    var children = gridItems(container);
    var n = children.length;

    if (n === 0) return;

    if (container.getAttribute('data-grid-mode') === 'justify') {
      layoutJustifiedGrid(container, children, containerWidth);
      return;
    }

    restoreDirectChildren(container, children);
    children.forEach(resetGridChild);

    // Determine layout: manual override or auto-generate
    var rows;
    var layoutStr = isMobile ? null : container.getAttribute('data-layout');

    if (isMobile) {
      totalCols = 12;
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
      var seed = gridSeed(container, layoutStr, children);
      rows = isMobile ? generateMobileLayout(children, totalCols, seed) : generateLayout(n, totalCols, seed);
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

      var rowHeight;

      if (isMobile) {
        var rowChildren = children.slice(itemIndex, itemIndex + row.length);
        var rowAspectSum = rowChildren.reduce(function (sum, child) {
          return sum + childAspectRatio(child);
        }, 0);
        rowHeight = Math.round(containerWidth / Math.max(1, rowAspectSum || DEFAULT_MEDIA_AR));
      } else {
        // Narrowest cell width in pixels
        var minCellWidth = (minSpan / rowSum) * containerWidth;

        // Row height: keep narrowest cell at min aspect ratio
        rowHeight = Math.round(minCellWidth / minAR);
      }

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
    notifyGridLayout(container);
  }

  // --- Initialization and resize handling ---

  var grids = [];
  var watchedMedia = new WeakSet();

  function initAll() {
    grids = Array.prototype.slice.call(
      document.querySelectorAll('.portfolio-grid')
    );
    grids.forEach(function (grid) {
      watchGridMedia(grid);
      layoutGrid(grid);
    });
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

  function watchGridMedia(grid) {
    Array.prototype.slice.call(grid.querySelectorAll('img, video')).forEach(function (media) {
      if (watchedMedia.has(media)) return;
      watchedMedia.add(media);

      if (media.tagName === 'IMG') {
        if (media.complete && media.naturalWidth) {
          window.setTimeout(function () {
            layoutGrid(grid);
          }, 0);
          return;
        }

        media.addEventListener('load', function () {
          layoutGrid(grid);
        }, { once: true });
      }

      if (media.tagName === 'VIDEO') {
        if (media.readyState >= 1 && media.videoWidth) {
          window.setTimeout(function () {
            layoutGrid(grid);
          }, 0);
          return;
        }

        media.addEventListener('loadedmetadata', function () {
          layoutGrid(grid);
        }, { once: true });
      }
    });
  }

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
    initAll: initAll,
    planJustifiedRows: plannedJustifiedRowSizes
  };

})();
