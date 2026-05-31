import os, re
from html.parser import HTMLParser

src = r'\\dlowenas\HPWorkstation\Desktop\Master HTMl\K-Production-Ready\03-moral-decline\DEPLOY-READY'
files = sorted([f for f in os.listdir(src) if f.endswith('.html') and (f.startswith('MDA-') or f == 'index.html')])

class TitleExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_title = False
        self.title = ''
        self.in_h1 = False
        self.h1 = ''
    def handle_starttag(self, tag, attrs):
        if tag == 'title': self.in_title = True
        if tag == 'h1' and not self.h1: self.in_h1 = True
    def handle_endtag(self, tag):
        if tag == 'title': self.in_title = False
        if tag == 'h1': self.in_h1 = False
    def handle_data(self, data):
        if self.in_title: self.title += data
        if self.in_h1: self.h1 += data

for f in files:
    path = os.path.join(src, f)
    with open(path, 'r', encoding='utf-8', errors='replace') as fh:
        content = fh.read()

    te = TitleExtractor()
    try:
        te.feed(content)
    except:
        pass
    title = (te.h1 or te.title or 'NO TITLE').strip()[:80]

    # Find all href links in nav-like contexts
    all_hrefs = re.findall(r'href=["\']([^"\']+\.html)["\']', content)
    
    # Find prev/next by looking at link text
    nav_prev = []
    nav_next = []
    # Pattern: <a href="X">...prev/next text...</a>
    link_pattern = re.findall(r'<a[^>]*href=["\']([^"\']+\.html)["\'][^>]*>(.*?)</a>', content, re.DOTALL | re.IGNORECASE)
    for href, text in link_pattern:
        clean = re.sub(r'<[^>]+>', '', text).strip().lower()
        if any(w in clean for w in ['prev', 'previous', 'back']):
            nav_prev.append(href)
        if any(w in clean for w in ['next', 'continue', 'forward']):
            nav_next.append(href)
    
    # Also check for arrow entities
    for href, text in link_pattern:
        if '8592' in text or 'larr' in text or '\u2190' in text:
            nav_prev.append(href)
        if '8594' in text or 'rarr' in text or '\u2192' in text:
            nav_next.append(href)

    prev = list(set(nav_prev))
    nxt = list(set(nav_next))

    print(f'{f}')
    print(f'  TITLE: {title}')
    if prev: print(f'  PREV: {", ".join(prev[:2])}')
    if nxt: print(f'  NEXT: {", ".join(nxt[:2])}')
    if not prev and not nxt: print(f'  NAV: none detected')
    print()