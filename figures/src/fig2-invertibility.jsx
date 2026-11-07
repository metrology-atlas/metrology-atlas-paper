export default () => {
  const EW = 120, SW = 96, H = 52, e0 = 24, s1 = 160, s2 = 272, s3 = 384, s4 = 496, e5 = 608, rowT = 96, rowV = 168, rowC = 286;
  const edge = 'var(--cds-chart-axis)', warn = 'var(--cds-chart-status-warning)', accent = 'var(--cds-chart-categorical-1)',
    ink = 'var(--cds-text-primary)', quiet = 'var(--cds-text-secondary)', fix = '#2e8b57';
  const step = (x, cy, lossy) => <rect x={x} y={cy - H / 2} width={SW} height={H} rx='8' fill={lossy ? warn : 'none'}
    fillOpacity={lossy ? 0.14 : 1} stroke={lossy ? warn : edge} strokeWidth={lossy ? 1.75 : 1.25}/>;
  const end = (x, cy, truth) => <rect x={x} y={cy - H / 2} width={EW} height={H} rx='8' fill={truth ? accent : 'none'}
    fillOpacity={truth ? 0.12 : 1} stroke={truth ? accent : edge} strokeWidth={truth ? 2 : 1.25}/>;
  const two = (cx, cy, a, b, bold) => <g><text x={cx} y={cy - 3} textAnchor='middle' fontWeight={bold ? 600 : 400} fill={ink}>{a}</text>
    <text x={cx} y={cy + 13} textAnchor='middle' fontWeight={bold ? 600 : 400} fill={ink}>{b}</text></g>;
  const arrows = cy => <g>{[[e0 + EW, s1], [s1 + SW, s2], [s2 + SW, s3], [s3 + SW, s4], [s4 + SW, e5]].map(([a, b]) =>
    <path key={a} d={`M${a + 1} ${cy}H${b - 1}`} markerEnd='url(#inv-arrow)'/>)}</g>;
  const fixbox = (x, w, a, b, c) => <g><rect x={x} y={rowC - H / 2} width={w} height={H} rx='8' fill={fix} fillOpacity='0.12'
    stroke={fix} strokeWidth='1.75'/><text x={x + w / 2} y={rowC - 9} textAnchor='middle' fontWeight='600' fill={ink}>{a}</text>
    <text x={x + w / 2} y={rowC + 6} textAnchor='middle' fontSize='10.5' fill={quiet}>{b}</text>
    <text x={x + w / 2} y={rowC + 19} textAnchor='middle' fontSize='10.5' fill={quiet}>{c}</text></g>;
  return <svg viewBox='0 0 760 380' role='img' aria-label='How a record was made, and what the atlas does to correct it' fontSize='12'>
    <defs>
      <marker id='inv-arrow' viewBox='0 0 10 10' refX='9' refY='5' markerWidth='6' markerHeight='6' orient='auto-start-reverse'><path d='M0 0L10 5L0 10z' fill={edge}/></marker>
      <marker id='inv-fix' viewBox='0 0 10 10' refX='9' refY='5' markerWidth='6' markerHeight='6' orient='auto-start-reverse'><path d='M0 0L10 5L0 10z' fill={fix}/></marker>
    </defs>
    <text data-claude-text-id='title' x='24' y='28' fontSize='15' fontWeight='600' fill={ink}>How a record was made, and what the atlas does</text>
    <text x='24' y='56' fontSize='11.5' fill={quiet}>How the record was made: the measurement model, forward from the truth to the recorded pair</text>
    <g fill='none' stroke={edge} strokeWidth='1.25'>{arrows(rowT)}{arrows(rowV)}</g>
    <g>{end(e0, rowT, true)}<text x={e0 + EW / 2} y={rowT - 3} textAnchor='middle' fontWeight='600' fill={ink}>True time</text>
      <text x={e0 + EW / 2} y={rowT + 13} textAnchor='middle' fontSize='11' fill={quiet}>when it happened</text></g>
    <g>{end(e0, rowV, true)}<text x={e0 + EW / 2} y={rowV - 3} textAnchor='middle' fontWeight='600' fill={ink}>True value</text>
      <text x={e0 + EW / 2} y={rowV + 13} textAnchor='middle' fontSize='11' fill={quiet}>what it was</text></g>
    <g>{step(s1, rowT, false)}{two(s1 + SW / 2, rowT, 'Delay after', 'its window')}</g>
    <g>{step(s2, rowT, false)}{two(s2 + SW / 2, rowT, 'Clock', 'drift')}</g>
    <g>{step(s3, rowT, false)}{two(s3 + SW / 2, rowT, 'Resynchron-', 'isations')}</g>
    <g>{step(s4, rowT, true)}{two(s4 + SW / 2, rowT, 'Stamp', 'grid')}</g>
    <g>{step(s1, rowV, true)}{two(s1 + SW / 2, rowV, 'Sensor', 'error')}</g>
    <g>{step(s2, rowV, false)}{two(s2 + SW / 2, rowV, 'Scale', 'factor')}</g>
    <g>{step(s3, rowV, true)}{two(s3 + SW / 2, rowV, 'Converter', 'codes')}</g>
    <g>{step(s4, rowV, true)}{two(s4 + SW / 2, rowV, 'Rounding,', 'heaping')}</g>
    <g>{end(e5, rowT, false)}{two(e5 + EW / 2, rowT, 'Recorded', 'time stamp', true)}</g>
    <g>{end(e5, rowV, false)}{two(e5 + EW / 2, rowV, 'Recorded', 'value', true)}</g>
    <line x1='24' x2='728' y1='214' y2='214' stroke={edge} strokeWidth='0.75' strokeDasharray='3 3'/>
    <text x='24' y='240' fontSize='11.5' fill={quiet}>What the atlas does: the correction, from the recorded pair back towards the truth</text>
    <g>{end(e5, rowC, false)}{two(e5 + EW / 2, rowC, 'Recorded', 'pair', true)}</g>
    {fixbox(384, 208, 'Undo the measured steps', 'delay, drift,', 'resynchronisations, scale')}
    {fixbox(160, 208, 'Carry the rest', 'as an interval or a spread:', 'grid, codes, rounding')}
    <g>{end(e0, rowC, true)}{two(e0 + EW / 2, rowC, 'Corrected', 'pair', true)}</g>
    <g fill='none' stroke={fix} strokeWidth='1.5'>
      <path d={`M${e5 - 1} ${rowC}H${593}`} markerEnd='url(#inv-fix)'/>
      <path d={`M${383} ${rowC}H${369}`} markerEnd='url(#inv-fix)'/>
      <path d={`M${159} ${rowC}H${e0 + EW + 1}`} markerEnd='url(#inv-fix)'/>
    </g>
    <text x='24' y='334' fontSize='11.5' fill={ink}>The corrected pair is a joint distribution over the true time and true value, with its own, smaller, error model</text>
    <g>
      <rect x='24' y='352' width='18' height='14' rx='3' fill='none' stroke={edge} strokeWidth='1.25'/>
      <text x='50' y='363' fontSize='11.5' fill={quiet}>can be undone once measured</text>
      <rect x='252' y='352' width='18' height='14' rx='3' fill={warn} fillOpacity='0.14' stroke={warn} strokeWidth='1.75'/>
      <text x='278' y='363' fontSize='11.5' fill={quiet}>many-to-one or random: leaves an interval or a spread</text>
      <rect x='600' y='352' width='18' height='14' rx='3' fill={fix} fillOpacity='0.12' stroke={fix} strokeWidth='1.75'/>
      <text x='626' y='363' fontSize='11.5' fill={quiet}>the atlas's correction</text>
    </g>
  </svg>;
};
