// usage: node arc_diagram_d3_golden_gen.mjs /path/to/d3-scale-4.0.2/src/index.js > arc_diagram_d3_golden.json
// arc_diagram: the node positions on the line are d3-scale scalePoint().domain(ids).range([r0, r1]).padding(0.5). No d3 layout module computes the arcs
// themselves (each is a semicircle over its two nodes), so the golden holds only this scale: for n = 0 to 40 nodes and four ranges, every node's position.
const {scalePoint} = await import(process.argv[2]);
const ranges = [[0, 800], [0, 1000], [12.5, 487.3], [0, 600.5]];
const out = {ranges, padding: 0.5, cases: []};
for (const r of ranges) {
  for (let n = 0; n <= 40; n++) {
    const ids = Array.from({length: n}, (_, i) => 'n' + i);
    const s = scalePoint().domain(ids).range(r).padding(0.5);
    out.cases.push({n, range: r, values: ids.map(d => s(d))});
  }
}
console.log(JSON.stringify(out));
