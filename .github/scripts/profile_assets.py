"""Refresh public profile SVGs using GitHub APIs; no third-party credentials."""
import json
import os
from collections import Counter
from html import escape
from pathlib import Path
from urllib.request import Request, urlopen

USER = 'oceankumar'
OUT = Path('dist')
TOKEN = os.environ['GITHUB_TOKEN']


def api(path, data=None):
    body = json.dumps(data).encode() if data else None
    request = Request('https://api.github.com/' + path, data=body, headers={
        'Authorization': 'Bearer ' + TOKEN,
        'Accept': 'application/vnd.github+json',
        'Content-Type': 'application/json',
        'User-Agent': 'OceanKumar-profile-assets',
        'X-GitHub-Api-Version': '2022-11-28',
    })
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def svg(theme, height, title, content, width=840):
    dark = theme == 'dark'
    colors = {'BG': '#0d1117' if dark else '#f6f8fa',
              'FG': '#f0f6fc' if dark else '#1f2328',
              'MUTED': '#919bab' if dark else '#59636e',
              'BORDER': '#30363d' if dark else '#d1d9e0',
              'ACCENT': '#b89aff' if dark else '#7546d8',
              'CYAN': '#67e8f9' if dark else '#096f83'}
    result = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title">
<title id="title">{escape(title)}</title>
<rect x="1" y="1" width="{width-2}" height="{height-2}" rx="12" fill="BG" stroke="BORDER"/>
<g font-family="system-ui,-apple-system,Segoe UI,sans-serif">{content}</g></svg>'''
    for key, value in colors.items():
        result = result.replace('"' + key + '"', '"' + value + '"')
    return result


def main():
    repos = []
    page = 1
    while True:
        batch = api(f'users/{USER}/repos?per_page=100&page={page}')
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    public = [r for r in repos if not r['private']]
    owned = [r for r in public if not r['fork']]
    languages = Counter()
    for repo in owned:
        languages.update(api(f"repos/{USER}/{repo['name']}/languages"))
    total = sum(languages.values())
    lang = '<text x="26" y="31" font-size="12" fill="ACCENT" letter-spacing="2">PUBLIC CODE / LANGUAGE MIX</text>'
    palette = ['#9575de', '#55b6c8', '#438cba', '#c084b6', '#ab985e', '#6f9d77']
    top = languages.most_common(5)
    other = total - sum(value for _, value in top)
    if other:
        top.append(('Other', other))
    if total:
        x = 26.0
        for (name, value), color in zip(top, palette):
            width = 368 * value / total
            lang += f'<rect x="{x:.2f}" y="49" width="{width:.2f}" height="9" fill="{color}"/>'
            x += width
        for i, ((name, value), color) in enumerate(zip(top, palette)):
            x = 26 + (i % 2) * 190
            y = 83 + (i // 2) * 26
            lang += f'<circle cx="{x+4}" cy="{y-4}" r="4" fill="{color}"/><text x="{x+16}" y="{y}" font-size="14" fill="FG">{escape(name)} <tspan fill="MUTED">{value/total:.1%}</tspan></text>'
    else:
        lang += '<text x="26" y="83" font-size="12" fill="MUTED">No public language data available.</text>'
    OUT.mkdir(exist_ok=True)
    for theme in ['dark', 'light']:
        (OUT / f'languages-{theme}.svg').write_text(
            svg(theme, 154, 'Language share by bytes in public non-fork repositories', lang, 420))
    print('Generated light and dark language SVGs from public GitHub data.')


if __name__ == '__main__':
    main()
