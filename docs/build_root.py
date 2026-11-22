#!/usr/bin/env python3
"""Post-processing of the multi-version build in build/html.

* Finds the newest release (e.g., v0.25.0).
* For every HTML page of that release, writes a redirect stub at the same path
  in the site root, so that old, unversioned URLs (e.g., /changelog.html) keep working
  and always point to the latest release -- also for future releases, as the stubs
  are regenerated on every build.
* Copies objects.inv to the root, so that intersphinx mappings to the unversioned URL keep working.
* Adds .nojekyll.
"""
import re
import shutil
from pathlib import Path

here = Path(__file__).parent
root = here / 'build' / 'html'
template = (here / '_templates' / 'redirect.html').read_text()


def version_key(tag: str):
    return tuple(int(x) for x in tag[1:].split('.'))


tags = sorted((d.name for d in root.iterdir() if d.is_dir() and re.fullmatch(r'v\d+\.\d+\.\d+', d.name)),
              key=version_key)
if not tags:
    raise SystemExit('No release docs found in build/html')
latest = tags[-1]

count = 0
for page in (root / latest).rglob('*.html'):
    rel = page.relative_to(root / latest)
    target = f'./{latest}/{rel.as_posix()}'
    stub = root / rel
    stub.parent.mkdir(parents=True, exist_ok=True)
    # a stub in a subdirectory needs a path relative to that directory
    depth = len(rel.parts) - 1
    target = '../' * depth + f'{latest}/{rel.as_posix()}' if depth else target
    stub.write_text(template.replace('{{ target }}', target).replace('{{ latest }}', latest))
    count += 1

if (root / latest / 'objects.inv').exists():
    shutil.copy(root / latest / 'objects.inv', root / 'objects.inv')
(root / '.nojekyll').touch()
print(f'Latest release: {latest}; {count} redirect stubs written; versions: {", ".join(tags)}')
