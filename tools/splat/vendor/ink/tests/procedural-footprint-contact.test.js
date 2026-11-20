const test = require('node:test');
const assert = require('node:assert/strict');
const {fitFootprintContact: fit} = require('..').load().KIT.procedural;

const footprint = {center: [4, 2, -3], tangent: [0, 4, 2], size: [1, .8, .5], samples: 3};
const flat = () => 0;
function close(actual, expected) {
  assert(Math.abs(actual - expected) < 1e-9);
}

test('seat follows the highest supported sample while the frame stays upright', () => {
  const result = fit({...footprint, height: (x, z) => 1 + .07 * (z + 3), interval: [.9, 1.1]});
  assert.deepEqual(Array.from(result.tangent), [0, 0, 1]);
  assert.deepEqual(Array.from(result.normal), [0, 1, 0]);
  close(result.point[0], 4);
  close(result.point[1], 1.035);
  close(result.point[2], -3);
  close(result.range[0], .965);
  assert.equal(result.points.length, 9);
  assert(result.points.some(([x, z]) => x === 3.75 && z === -3.5));
});

test('fit rejects gaps, narrow obstructions and excessive grades or elevations', () => {
  assert.equal(fit({...footprint, height: (x, z) => x === 4 && z === -3 ? null : 0}), null);
  assert.equal(fit({...footprint, height: flat, blocked: ([x, y, z]) => x === 3.75 && z === -3.5 && y > .7}), null);
  assert.equal(fit({...footprint, height: (x) => x - 4}), null);
  assert.equal(fit({...footprint, height: flat, interval: [.1, 3]}), null);
  assert.throws(() => fit({...footprint, height: flat, interval: ['0', 3]}), /dimensions/);
});

test('compact contact produces the same frame and checks the same support and obstruction samples', () => {
  const options={...footprint,height:(x,z)=>1+.07*(z+3),blocked:()=>false};
  const {points,...frame}=fit(options), compact=fit({...options,includePoints:false});
  assert.equal(points.length,9);
  assert.deepEqual(compact,frame);
  const blocked = ([x,y,z])=>x===3.75&&z===-3.5&&y>1.7;
  assert.equal(fit({...options,blocked,includePoints:false}),null);
});
