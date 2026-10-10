// Serve the exact standalone production build, including its public assets.
const fs = require('node:fs');
const path = require('node:path');
const frontend = path.resolve(__dirname, '../frontend');
const standalone = path.join(frontend, '.next/standalone');
const entry = path.join(standalone, 'server.js');
if (!fs.existsSync(entry)) throw new Error('Run npm run build in frontend before starting production.');
fs.cpSync(path.join(frontend, '.next/static'), path.join(standalone, '.next/static'), {recursive:true});
fs.cpSync(path.join(frontend, 'public'), path.join(standalone, 'public'), {recursive:true});
process.env.PORT ||= '3010';
process.env.HOSTNAME = process.env.WEB_HOST || '127.0.0.1';
process.env.NODE_ENV = 'production';
require(entry);
