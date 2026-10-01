#!/usr/bin/env python3
"""Check generated presentation contracts without external packages."""
import argparse
import gzip
import json
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.h1 = 0
        self.redirect = False
        self.canonical = []
        self.task_links = []
        self.robots = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta' and attrs.get('http-equiv', '').lower() == 'refresh':
            self.redirect = True
        if tag == 'a' and 'task-card__action' in attrs.get('class', '').split():
            self.task_links.append(attrs.get('href'))
        if tag == 'h1':
            self.h1 += 1
        if tag == 'link' and attrs.get('rel') == 'canonical':
            self.canonical.append(attrs.get('href'))
        if tag == 'meta' and attrs.get('name') == 'robots':
            self.robots.append(attrs.get('content'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--public', type=Path, default=ROOT / 'public')
    public = parser.parse_args().public
    catalog = json.loads((ROOT / 'data/docs_versions.json').read_text())
    defaults = {key: config['default'] for key, config in catalog['products'].items()}
    versions = {key: {r['version'] for r in config['releases']} | {'dev'}
                for key, config in catalog['products'].items()}
    checked = 0
    for path in public.rglob('index.html'):
        text = path.read_text()
        page = Page(text)
        if page.redirect:
            continue
        assert page.h1 == 1, f'{path}: expected one H1, got {page.h1}'
        assert len(page.canonical) == 1, f'{path}: missing/duplicate canonical'
        relative = path.relative_to(public).parts
        archived = (len(relative) > 2 and relative[0] in defaults
                    and relative[1] in versions[relative[0]]
                    and relative[1] != defaults[relative[0]])
        expected = 'noindex, follow' if archived else 'index, follow'
        assert page.robots == [expected], f'{path}: unexpected robots {page.robots}'
        checked += 1
    assert checked > 0, 'Build the website first'
    navigation = json.loads((ROOT / 'data/docs_navigation.json').read_text())
    sources = json.loads((ROOT / '.cache/docs-data/docs_sources.json').read_text())
    expected_tasks = {next(x['url'] for x in sources if x['product'] == product
                           and x['version'] == default
                           and x['source_path'] == navigation['products'][product]['start'])
                      for product, default in defaults.items() if product != 'praxis'}
    expected_tasks.add('/guides/first-proxy/')
    for route in ('index.html', 'start/index.html'):
        page = Page((public / route).read_text())
        assert set(page.task_links) == expected_tasks, f'{route}: missing task starting guide'
    for route in ('start', 'docs', 'search', 'community', 'examples', 'visual-guides',
                  'guides/install', 'guides/first-proxy', 'guides/operate', 'guides/extend'):
        assert (public / route / 'index.html').is_file(), f'Missing /{route}/'
    custom = list((public / 'js').glob('praxis*.js')) + list((public / 'js').glob('flow-walkthrough*.js'))
    assert custom, 'Missing website interaction bundle'
    size = sum(len(gzip.compress(p.read_bytes())) for p in custom)
    assert size <= 20 * 1024, f'Custom JavaScript budget exceeded: {size} bytes gzip'
    print(f'Presentation checks passed: {checked} pages; custom JavaScript {size} bytes gzip')


if __name__ == '__main__':
    main()
