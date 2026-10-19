const fs=require('fs'),babel=require('@babel/core'),React=require('react'),{renderToStaticMarkup}=require('react-dom/server');
const vars={'--cds-chart-axis':'#8a8f98','--cds-chart-categorical-1':'#2a78d6','--cds-text-primary':'#1b2333','--cds-text-secondary':'#5a6170','--cds-chart-status-warning':'#e8a33d','--cds-chart-grid':'#e4e3df','--cds-chart-reference-tint':'#f1f0ec'};
for (const [inp,out,vb] of process.argv.slice(2).map(a=>a.split(':'))){
  let src=fs.readFileSync(inp,'utf8').replace('export default','module.exports =');
  src=src.replace(/<text data-claude-text-id='title'[^>]*>[^<]*<\/text>/,'');
  const code=babel.transformSync(src,{presets:['@babel/preset-react']}).code;
  const m={exports:{}}; new Function('module','React',code)(m,React);
  let svg=renderToStaticMarkup(React.createElement(m.exports));
  for(const[k,v] of Object.entries(vars)) svg=svg.split(`var(${k})`).join(v);
  svg=svg.replace(/data-claude-[a-z-]+="[^"]*"/g,'').replace('<svg ','<svg xmlns="http://www.w3.org/2000/svg" font-family="Inter" ').replace(/viewBox="[^"]*"/,`viewBox="${vb}"`);
  fs.writeFileSync(out,svg);
}
