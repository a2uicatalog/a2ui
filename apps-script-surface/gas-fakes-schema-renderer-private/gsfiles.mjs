/**
 * gsfiles.mjs — auto-discovers GAS renderer files in load order.
 *
 * Order: atom.gs → atoms_*.gs (alpha) → other *.gs (alpha) → Code.js → Code.private.js
 * New atom files are picked up automatically — no manual list to maintain.
 */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const all = fs.readdirSync(__dirname);

const atomsGS   = all.filter(f => f.startsWith('atoms_') && f.endsWith('.gs')).sort();
const otherGS   = all.filter(f => f.endsWith('.gs') && f !== 'atom.gs' && !f.startsWith('atoms_')).sort();

export const gasFiles = [
  'atom.gs',
  ...atomsGS,
  ...otherGS,
  'Code.js',
  'Code.private.js',
];
