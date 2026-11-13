#!/usr/bin/env python3
"""Convert a CV (.docx, .pdf, .md or .txt) into the HTML that career-ops'
verify-ats.mjs scores.

verify-ats.mjs was written to score HTML that career-ops generates itself.
Students upload PDFs and Word files instead, so this script maps the parts of
those files the scorer cares about into plain HTML, without judging anything:

  - section headings  -> <h2>  (Word: real Heading/Title styles only;
                                PDF: short lines set bold or larger than body text)
  - tables            -> <table>   (Word tables; PDF tables pdfplumber detects)
  - images            -> <img>     (pictures embedded in the file)
  - fonts             -> font-family declarations (the fonts actually used)
  - everything else   -> <p>

All scoring is done by the unmodified verify-ats.mjs.

Usage: python3 cv_to_html.py <cv-file> <out.html>
Prints one line describing what was detected.
"""
import html
import re
import statistics
import sys
import zipfile
from pathlib import Path

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'


def page(body_parts, fonts):
    fonts = sorted({f for f in fonts if f})
    style = ''
    if fonts:
        fam = ', '.join(f"'{f}'" for f in fonts)
        style = f'<style>body {{ font-family: {fam}; }}</style>'
    return ('<!DOCTYPE html>\n<html><head><meta charset="utf-8"><title>CV</title>'
            f'{style}</head><body>\n' + '\n'.join(body_parts) + '\n</body></html>\n')


def esc(s):
    return html.escape(s, quote=False)


# ---------------------------------------------------------------- DOCX
def from_docx(path):
    import xml.etree.ElementTree as ET
    z = zipfile.ZipFile(path)
    doc = ET.fromstring(z.read('word/document.xml'))
    # map styleId -> (name, font)
    style_names, style_fonts = {}, {}
    if 'word/styles.xml' in z.namelist():
        st = ET.fromstring(z.read('word/styles.xml'))
        for s in st.iter(W + 'style'):
            sid = s.get(W + 'styleId')
            n = s.find(W + 'name')
            style_names[sid] = (n.get(W + 'val') if n is not None else sid or '').lower()
            rf = s.find(f'.//{W}rFonts')
            if rf is not None:
                style_fonts[sid] = rf.get(W + 'ascii')
        dd = st.find(f'{W}docDefaults//{W}rFonts')
        if dd is not None and dd.get(W + 'ascii'):
            style_fonts['__default__'] = dd.get(W + 'ascii')
    fonts = {style_fonts.get('__default__')}
    parts, stats = [], {'headings': 0, 'tables': 0, 'images': 0}

    def para_text(p):
        return ''.join(t.text or '' for t in p.iter(W + 't')).strip()

    def para_html(p):
        for rf in p.iter(W + 'rFonts'):
            fonts.add(rf.get(W + 'ascii'))
        if list(p.iter(W + 'drawing')) or list(p.iter(W + 'pict')):
            stats['images'] += 1
            parts.append('<img src="embedded-image" alt="">')
        text = para_text(p)
        if not text:
            return
        ps = p.find(f'{W}pPr/{W}pStyle')
        sid = ps.get(W + 'val') if ps is not None else ''
        fonts.add(style_fonts.get(sid))
        name = style_names.get(sid, (sid or '').lower())
        if name.startswith('heading') or name == 'title':
            stats['headings'] += 1
            parts.append(f'<h2>{esc(text)}</h2>')
        else:
            parts.append(f'<p>{esc(text)}</p>')

    body = doc.find(W + 'body')
    for el in body:
        if el.tag == W + 'p':
            para_html(el)
        elif el.tag == W + 'tbl':
            stats['tables'] += 1
            rows = []
            for tr in el.iter(W + 'tr'):
                cells = []
                for tc in tr.iter(W + 'tc'):
                    txt = ' '.join(para_text(p) for p in tc.iter(W + 'p'))
                    cells.append(f'<td>{esc(txt)}</td>')
                rows.append('<tr>' + ''.join(cells) + '</tr>')
            parts.append('<table>' + ''.join(rows) + '</table>')
    # text boxes (floating shapes) are a classic ATS trap: surface them as tables
    if b'txbxContent' in z.read('word/document.xml'):
        stats['tables'] += 1
        parts.append('<table><tr><td>text box content</td></tr></table>')
    return page(parts, fonts), stats


# ---------------------------------------------------------------- PDF
def clean_font(name):
    # PDF fonts carry PostScript names: 'ABCDEF+TimesNewRomanPSMT', 'ArialMT,Bold'.
    # Turn them back into family names ('Times New Roman', 'Arial') so the
    # scorer judges the font, not its PostScript spelling.
    name = re.sub(r'^[A-Z]{6}\+', '', name or '')
    name = re.split(r'[-,]', name)[0]
    name = re.sub(r'(PSMT|PS|MT)$', '', name)
    return re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', name).strip()


def from_pdf(path):
    import pdfplumber
    parts, fonts = [], set()
    stats = {'headings': 0, 'tables': 0, 'images': 0}
    with pdfplumber.open(path) as pdf:
        sizes = [round(c['size'], 1) for pg in pdf.pages for c in pg.chars if c['text'].strip()]
        body = statistics.median(sizes) if sizes else 10
        for pg in pdf.pages:
            for c in pg.chars:
                fonts.add(clean_font(c.get('fontname')))
            if pg.images:
                stats['images'] += len(pg.images)
                parts.extend('<img src="embedded-image" alt="">' for _ in pg.images)
            for t in pg.find_tables():
                if len(t.rows) >= 2 and len(t.rows[0].cells) >= 2:
                    stats['tables'] += 1
                    parts.append('<table><tr><td>table</td></tr></table>')
            lines = {}
            for c in pg.chars:
                key = round(c['top'] / 3)
                lines.setdefault(key, []).append(c)
            for key in sorted(lines):
                chars = sorted(lines[key], key=lambda c: c['x0'])
                text = ''
                prev = None
                for c in chars:
                    if prev is not None and c['x0'] - prev['x1'] > c['size'] * 0.25:
                        text += ' '
                    text += c['text']
                    prev = c
                text = re.sub(r'\s+', ' ', text).strip()
                if not text:
                    continue
                vis = [c for c in chars if c['text'].strip()]
                bold = all('bold' in (c.get('fontname') or '').lower() for c in vis)
                big = statistics.mean(c['size'] for c in vis) >= body + 1.5
                words = len(text.split())
                letters = re.sub(r'[^A-Za-z]', '', text)
                caps = bool(letters) and letters.isupper()
                if words <= 5 and (big or (bold and caps)) and not re.search(r'\d{4}', text):
                    stats['headings'] += 1
                    parts.append(f'<h2>{esc(text)}</h2>')
                else:
                    parts.append(f'<p>{esc(text)}</p>')
    return page(parts, fonts), stats


# ---------------------------------------------------------------- text / markdown
def from_text(path):
    parts, stats = [], {'headings': 0, 'tables': 0, 'images': 0}
    for line in Path(path).read_text(encoding='utf-8', errors='replace').splitlines():
        s = line.strip()
        if not s:
            continue
        m = re.match(r'^#{1,6}\s+(.*)', s)
        letters = re.sub(r'[^A-Za-z]', '', s)
        if m or (len(s.split()) <= 5 and letters and letters.isupper()):
            stats['headings'] += 1
            parts.append(f'<h2>{esc(m.group(1) if m else s)}</h2>')
        elif s.startswith('|'):
            stats['tables'] += 1
            parts.append(f'<table><tr><td>{esc(s)}</td></tr></table>')
        else:
            parts.append(f'<p>{esc(s.lstrip("-*• ").strip())}</p>')
    return page(parts, set()), stats


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    src, out = sys.argv[1], sys.argv[2]
    ext = Path(src).suffix.lower()
    if ext == '.docx':
        doc, stats = from_docx(src)
    elif ext == '.pdf':
        doc, stats = from_pdf(src)
    elif ext in ('.md', '.txt'):
        doc, stats = from_text(src)
    else:
        sys.exit(f'Unsupported file type {ext}: upload the CV as .docx, .pdf, .md or .txt')
    Path(out).write_text(doc, encoding='utf-8')
    print(f"converted {Path(src).name} ({ext[1:]}): {stats['headings']} headings, "
          f"{stats['tables']} tables, {stats['images']} images")


if __name__ == '__main__':
    main()
