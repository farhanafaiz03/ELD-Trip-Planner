import './LogSheet.css';

// Order top-to-bottom matches the real FMCSA paper form exactly -
// don't reorder these without checking the reference image again.
// Sleeper Berth is included purely for visual authenticity - the
// engine never produces that status, since the assessment's
// assumptions rule out sleeper-berth split logic, so this row will
// always render empty. That's intentional, not a bug.
const ROWS = [
  { key: 'off_duty', label: 'Off Duty' },
  { key: 'sleeper_berth', label: 'Sleeper Berth' },
  { key: 'driving', label: 'Driving' },
  { key: 'on_duty_not_driving', label: 'On Duty (Not Driving)' },
];

// Same duty-status colors the map markers use, pulled from
// index.css - a color means the same thing everywhere in the app.
const STATUS_COLORS = {
  off_duty: 'var(--status-off-duty)',
  driving: 'var(--status-driving)',
  on_duty_not_driving: 'var(--status-on-duty)',
};

// Layout constants for the SVG grid - resize the whole drawing by
// changing these, everything else below is calculated from them.
const GRID_LEFT = 130;
const GRID_WIDTH = 760;
const GRID_TOP = 30;
const ROW_HEIGHT = 34;

const HOUR_LABELS = Array.from({ length: 25 }, (_, hour) => {
  if (hour === 0 || hour === 24) return 'Mid night';
  if (hour === 12) return 'Noon';
  return String(hour);
});

/**
 * LogSheet
 *
 * Draws one day's worth of the FMCSA driver's daily log as SVG, built
 * entirely from the `log` object the backend already computed
 * (daily_logs.py). This component makes zero decisions about the
 * trip itself - it only turns already-correct data into pixels.
 */
export default function LogSheet({ log }) {
  const dateLabel = new Date(`${log.date}T00:00:00`).toLocaleDateString(undefined, {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  });

  // Converts an ISO timestamp into "hours since this day's midnight".
  // Deliberately not using .getHours() - a segment ending exactly at
  // the next day's midnight needs to land at x=24 (the far right
  // edge), not wrap back around to x=0.
  const hourOfDay = (isoString) => {
    const dayStart = new Date(`${log.date}T00:00:00`);
    return (new Date(isoString) - dayStart) / (1000 * 60 * 60);
  };

  const xForHour = (hour) => GRID_LEFT + (hour / 24) * GRID_WIDTH;
  const yForRow = (rowIndex) => GRID_TOP + rowIndex * ROW_HEIGHT + ROW_HEIGHT / 2;

  // Builds one continuous line across all four rows for the whole
  // day. Because daily_logs.py now guarantees the segments are
  // gapless and cover a full 24 hours, the end of every segment lines
  // up exactly with the start of the next - so wherever the status
  // changes, this naturally draws a clean vertical jump between rows
  // without us having to calculate connector lines separately.
  const linePoints = log.segments
    .map((segment) => {
      const y = yForRow(ROWS.findIndex((row) => row.key === segment.status));
      const x1 = xForHour(hourOfDay(segment.start));
      const x2 = xForHour(hourOfDay(segment.end));
      return `${x1},${y} ${x2},${y}`;
    })
    .join(' ');

  const gridHeight = ROWS.length * ROW_HEIGHT;

  return (
    <div className="log-sheet">
      <div className="log-sheet-header">
        <h3>{dateLabel}</h3>
        <span className="log-sheet-subtitle">Driver's Daily Log</span>
      </div>

      <svg
        className="log-sheet-svg"
        viewBox={`0 0 ${GRID_LEFT + GRID_WIDTH + 90} ${GRID_TOP + gridHeight + 10}`}
      >
        {HOUR_LABELS.map((label, hour) => (
          <text key={hour} x={xForHour(hour)} y={GRID_TOP - 10} textAnchor="middle" className="log-sheet-hour-label">
            {label}
          </text>
        ))}

        {Array.from({ length: 25 }, (_, hour) => (
          <line
            key={hour}
            x1={xForHour(hour)}
            y1={GRID_TOP}
            x2={xForHour(hour)}
            y2={GRID_TOP + gridHeight}
            className={hour % 6 === 0 ? 'log-sheet-gridline-bold' : 'log-sheet-gridline'}
          />
        ))}

        {ROWS.map((row, index) => (
          <g key={row.key}>
            <line
              x1={GRID_LEFT}
              y1={GRID_TOP + index * ROW_HEIGHT}
              x2={GRID_LEFT + GRID_WIDTH}
              y2={GRID_TOP + index * ROW_HEIGHT}
              className="log-sheet-gridline-bold"
            />
            <text x={GRID_LEFT - 10} y={yForRow(index)} textAnchor="end" dominantBaseline="middle" className="log-sheet-row-label">
              {row.label}
            </text>
            <text x={GRID_LEFT + GRID_WIDTH + 15} y={yForRow(index)} dominantBaseline="middle" className="log-sheet-total">
              {(log.totals[row.key] || 0).toFixed(1)}
            </text>
          </g>
        ))}
        <line
          x1={GRID_LEFT}
          y1={GRID_TOP + gridHeight}
          x2={GRID_LEFT + GRID_WIDTH}
          y2={GRID_TOP + gridHeight}
          className="log-sheet-gridline-bold"
        />

        <polyline points={linePoints} className="log-sheet-line" />
      </svg>

      <div className="log-sheet-remarks">
        <span className="log-sheet-remarks-title">Remarks</span>
        <ul>
          {log.segments
            .filter((s) => s.label !== 'Off duty') // the implicit padding blocks aren't worth listing
            .map((segment, index) => (
              <li key={index}>
                <span className="log-sheet-remarks-dot" style={{ background: STATUS_COLORS[segment.status] }} />
                {formatTime(segment.start)} – {formatTime(segment.end)}: {segment.label}
              </li>
            ))}
        </ul>
      </div>
    </div>
  );
}

function formatTime(isoString) {
  return new Date(isoString).toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' });
}