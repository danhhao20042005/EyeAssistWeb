import { existsSync } from 'node:fs';
import { fileURLToPath, pathToFileURL } from 'node:url';
import path from 'node:path';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

export async function resolve(specifier, context, next) {
  let target = null;
  if (specifier.startsWith('@/')) target = path.join(root, specifier.slice(2));
  else if (specifier.startsWith('.') && context.parentURL) target = path.resolve(path.dirname(fileURLToPath(context.parentURL)), specifier);
  if (target && !path.extname(target) && existsSync(`${target}.ts`)) {
    return next(pathToFileURL(`${target}.ts`).href, context);
  }
  return next(specifier, context);
}
