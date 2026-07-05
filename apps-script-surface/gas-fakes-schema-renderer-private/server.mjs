/**
 * server.mjs — A2UI schema renderer dev server via gas-fakes.
 *
 * Usage:
 *   npm install
 *   npm start              # serves at http://localhost:3099/?p=<base64>
 *   PORT=4000 npm start    # custom port
 *
 * Powered by gas-fakes: https://github.com/brucemcpherson/gas-fakes
 */
import { fileURLToPath } from 'url';
import path from 'path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PORT      = parseInt(process.env.PORT || '3099', 10);

// Point gas-fakes at the stub — it loads all .gs files in each worker thread
const stubPath = path.join(__dirname, 'gas_entry_stub.js');
globalThis.__gasFakesMainScriptPath = stubPath;
process.argv[1] = stubPath;

await import('@mcpher/gas-fakes/main.js');

HtmlService.__startWebApp(PORT);
