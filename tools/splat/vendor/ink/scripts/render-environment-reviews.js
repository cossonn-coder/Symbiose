const { execFileSync } = require('node:child_process');
const path = require('node:path');

const root = path.join(__dirname,'..');
const output = path.resolve(process.argv[2] ?? path.join(root,'studio/out/environment-reviews'));
const shots = ['review-beacon','review-cliff-path','review-sheltered-market'];
const kit = require('../index.js').load();

for (const shot of shots) {
  const file = 'examples/' + shot + '.js';
  const { review } = require(path.join(root,file))(kit);
  execFileSync(process.execPath,[
    'cli/ink-studio.js','clip',file,'--to',String(review.duration),
    '--w','192','--h','128','--px','1','--fps','10','--raw','--passes','environment',
    '--out',path.join(output,shot+'.png'),'--recipe',path.join(output,shot+'.json')
  ],{ cwd:root,stdio:'inherit' });
}
