// score_renderer.js
// Renders the score with VexFlow and writes CSS-space note positions into
// window.srs_state.renderedPositions. It is the SOLE writer of that field.
// Depends on: Vex (VexFlow global), music_theory, window.srs_state.

const score_renderer = (() => {

  const MIN_BAR_WIDTH = 250;  // px — minimum readable bar width
  const ROW_HEIGHT    = 130;  // px per row (stave + margins)
  const STAVE_TOP     = 30;   // px from top of row to stave top
  const LEFT_MARGIN   = 10;

  const render = (bars, settings) => {
    const container = document.getElementById('score-container');
    container.innerHTML = '';

    if (!bars || !bars.length) {
      window.srs_state.renderedPositions = [];
      return;
    }

    const scaleFactor = settings.score_scale || 1.0;

    const scaledMinBarWidth = MIN_BAR_WIDTH * scaleFactor;
    const scaledRowHeight   = ROW_HEIGHT * scaleFactor;
    const scaledStaveTop    = STAVE_TOP * scaleFactor;
    const scaledLeftMargin  = LEFT_MARGIN * scaleFactor;

    const containerWidth = container.clientWidth || 800;
    const barsPerRow     = Math.max(1, Math.floor(containerWidth / scaledMinBarWidth));
    const barWidth       = Math.floor((containerWidth - scaledLeftMargin) / barsPerRow);
    const numRows        = Math.ceil(bars.length / barsPerRow);
    const totalHeight    = numRows * scaledRowHeight + (20 * scaleFactor);

    const VF       = Vex.Flow;
    const renderer = new VF.Renderer(container, VF.Renderer.Backends.SVG);
    renderer.resize(containerWidth, totalHeight);
    const context  = renderer.getContext();
    context.scale(scaleFactor, scaleFactor);

    // After scale, set width/height attributes explicitly if resize didn't work as expected
    // with CSS vs user units, though renderer.resize should handle it.
    // SVG width/height are in pixels, but context.scale affects the units within.

    const keyStr  = music_theory.getVexFlowKeyString(settings.key_sig_type, settings.key_sig_count);
    const timeSig = settings.time_signature;
    const clef    = settings.clef;
    const [beatsPerBarStr, beatUnitStr] = timeSig.split('/');
    const beatsPerBar = parseInt(beatsPerBarStr, 10);
    const beatUnit    = parseInt(beatUnitStr, 10);

    const rawPositions = [];  // {noteIndex, xAbsSvg, rowIndex, yTop, yBottom}
    let noteCounter = 0;

    // Unscaled internal width for VexFlow to work in before context.scale
    const internalBarWidth = barWidth / scaleFactor;

    for (let rowIdx = 0; rowIdx < numRows; rowIdx++) {
      const rowBars = bars.slice(rowIdx * barsPerRow, (rowIdx + 1) * barsPerRow);
      const rowY    = (rowIdx * scaledRowHeight + scaledStaveTop) / scaleFactor;

      rowBars.forEach((bar, colIdx) => {
        const isFirstBar   = rowIdx === 0 && colIdx === 0;
        const isFirstInRow = colIdx === 0;
        const xStart       = (scaledLeftMargin + colIdx * barWidth) / scaleFactor;

        const stave = new VF.Stave(xStart, rowY, internalBarWidth);
        if (isFirstInRow) stave.addClef(clef);
        if (isFirstBar) {
          stave.addKeySignature(keyStr);
          stave.addTimeSignature(timeSig);
        }
        stave.setContext(context).draw();

        // Available note width — measured AFTER clef/key/time-sig are added.
        // If the stave is too narrow to fit these plus notes, floor it to 120px
        // so notes remain readable (though they will overrun the bar line).
        const noteWidth = Math.max(120, stave.getNoteEndX() - stave.getNoteStartX() - 10);

        // Build VexFlow notes
        const vfNotes = bar.notes.map(n => new VF.StaveNote({
          keys:     [n.pitch],
          duration: n.duration,
          clef,
        }));

        const voice = new VF.Voice({ num_beats: beatsPerBar, beat_value: beatUnit })
          .setMode(VF.Voice.Mode.SOFT);
        voice.addTickables(vfNotes);

        VF.Accidental.applyAccidentals([voice], keyStr);
        new VF.Formatter().joinVoices([voice]).format([voice], noteWidth);

        // Auto-beaming for quavers and semiquavers
        const beams = VF.Beam.generateBeams(vfNotes);

        voice.draw(context, stave);
        beams.forEach(b => b.setContext(context).draw());

        vfNotes.forEach(vfNote => {
          rawPositions.push({
            noteIndex: noteCounter++,
            rowIndex:  rowIdx,
            xAbsSvg:   vfNote.getAbsoluteX(),
            yTop:      rowIdx * scaledRowHeight + scaledStaveTop - (10 * scaleFactor), // adjust for playhead
            yBottom:   rowIdx * scaledRowHeight + scaledStaveTop + (80 * scaleFactor), // adjust for playhead
          });
        });
      });
    }

    // Convert SVG user-space x → CSS px relative to #score-wrapper
    const svgEl      = container.querySelector('svg');
    const svgRect    = svgEl.getBoundingClientRect();
    const wrapper    = document.getElementById('score-wrapper');
    const wrapperRect = wrapper.getBoundingClientRect();
    const viewBoxW   = svgEl.viewBox.baseVal.width || parseFloat(svgEl.getAttribute('width')) || containerWidth;
    const scale      = svgRect.width / viewBoxW;
    const svgOffsetX = svgRect.left - wrapperRect.left;

    const positions = rawPositions.map(rp => ({
      noteIndex: rp.noteIndex,
      rowIndex:  rp.rowIndex,
      xStart:    rp.xAbsSvg * scale + svgOffsetX,
      xCenter:   rp.xAbsSvg * scale + svgOffsetX,
      xEnd:      rp.xAbsSvg * scale + svgOffsetX,  // filled by continuity rule below
      yTop:      rp.yTop,
      yBottom:   rp.yBottom,
    }));

    // xEnd continuity rule: each note's xEnd = next note's xStart
    for (let i = 0; i < positions.length - 1; i++) {
      positions[i].xEnd = positions[i + 1].xStart;
    }
    // Final note fallback
    if (positions.length) {
      const last = positions[positions.length - 1];
      last.xEnd = last.xStart + 20;
    }

    // Write to shared state (sole writer of renderedPositions)
    window.srs_state.renderedPositions = positions;

    // Park playhead at note 0
    if (positions.length) {
      const ph = document.getElementById('playhead');
      const p0 = positions[0];
      ph.style.left    = p0.xStart + 'px';
      ph.style.top     = p0.yTop   + 'px';
      ph.style.height  = (p0.yBottom - p0.yTop) + 'px';
      ph.style.display = 'block';
    }
  };

  const getNoteCount = () => window.srs_state.renderedPositions.length;

  return { render, getNoteCount };
})();
