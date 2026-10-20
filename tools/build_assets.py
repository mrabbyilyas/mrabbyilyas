#!/usr/bin/env python3
"""Build the SVGs in assets/ that the profile README shows.

GitHub renders README images in a sandboxed <img>, so every SVG here is
self-contained: fonts come from Google Fonts, subset to the exact characters
each file uses and inlined as base64, and the avatar is inlined from
mrabbyilyas.com. Edit the data below, then run:

    python3 tools/build_assets.py
"""

from __future__ import annotations

import base64
import math
import re
import textwrap
import urllib.parse
import urllib.request
from functools import cache
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

OUT = Path(__file__).resolve().parent.parent / "assets"
SITE = "https://mrabbyilyas.com"
AVATAR = f"{SITE}/rabby-avatar-poster.webp"
EMAIL = "muhammadrabby7@gmail.com"
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)

# ---------------------------------------------------------------- data

PROJECTS = [
    {
        "slug": "second-act-pro",
        "title": "Second Act Pro",
        "category": "AI matching engine",
        "who": "Client · Craig, United States · 2025 — now",
        "flag": "us",
        "tagline": "A second act, with purpose.",
        "metrics": [("9", "vectors per CV"), ("4", "stage match funnel"), ("25", "API routes")],
        "stack": ["Next.js", "FastAPI", "Supabase", "Pinecone", "Gemini", "ColBERT"],
        "colors": {"bg": "#071a33", "fg": "#f6efe1", "accent": "#fcb040", "soft": "#123a66"},
        "fonts": {"title": "bodoni", "tagline": "bodoni-i", "body": "sans", "mono": "mono"},
        "sizes": {"title": 46, "tagline": 22},
        "motif": "match",
    },
    {
        "slug": "daphne",
        "title": "Daphne",
        "category": "Cognitive companion",
        "who": "Client · Ralf, Germany · 2026 — now",
        "flag": "de",
        "tagline": "Bring clarity to long-form conversations.",
        "metrics": [("30/30", "eval pass, up from 13"), ("4.8s", "median, down from 32.3s"), ("438", "commits")],
        "stack": ["Next.js", "OpenAI Realtime", "Pinecone", "Trigger.dev", "Three.js", "Recall.ai"],
        "colors": {"bg": "#131b24", "fg": "#f3f8fa", "accent": "#5271ff", "soft": "#e08a4f"},
        "fonts": {"title": "spectral", "tagline": "spectral-i", "body": "sans", "mono": "jetbrains"},
        "sizes": {"title": 50, "tagline": 20},
        "motif": "graph",
    },
    {
        "slug": "juraganin",
        "title": "Juraganin",
        "category": "AI store builder",
        "who": "My startup · Founder, Indonesia · 2026 — now",
        "flag": "id",
        "tagline": "Tanpa developer. Tanpa komisi. Cukup chat.",
        "metrics": [("660", "commits in 11 weeks"), ("20", "agent tools"), ("80", "test files")],
        "stack": ["Next.js", "AI SDK", "OpenRouter", "Supabase", "AWS Fargate", "Pulumi"],
        "colors": {"bg": "#fbf1dd", "fg": "#2a1c13", "accent": "#b0512a", "soft": "#cf9a3c"},
        "fonts": {"title": "bricolage", "tagline": "bricolage-sb", "body": "hanken", "mono": "plex"},
        "sizes": {"title": 48, "tagline": 18},
        "motif": "awning",
    },
    {
        "slug": "atlaspad",
        "title": "AtlasPad",
        "category": "Voice-first clinical docs",
        "who": "Client · Ralf, Germany · 2026",
        "flag": "de",
        "tagline": "Talk, and the chart writes itself.",
        "metrics": [("10", "voice tools"), ("510", "patient vectors"), ("70", "ICD-10 dimensions")],
        "stack": ["Next.js", "OpenAI Realtime", "WebRTC", "Three.js", "Supabase", "UMAP"],
        "colors": {"bg": "#efecf7", "fg": "#2a2440", "accent": "#6c3df4", "soft": "#dcd2f8"},
        "fonts": {"title": "manrope", "tagline": "manrope-sb", "body": "manrope-md", "mono": "mono"},
        "sizes": {"title": 46, "tagline": 20},
        "motif": "wave",
    },
]

STACK_AI = [
    "OpenAI Realtime", "Gemini", "AI SDK", "OpenRouter", "Pinecone", "RAG",
    "Tool calling", "Voice agents", "Deepgram", "Recall.ai", "ColBERT", "Embeddings",
]
STACK_PRODUCT = [
    "Next.js", "TypeScript", "React", "Three.js", "Python", "FastAPI", "Supabase",
    "PostgreSQL", "Trigger.dev", "WebRTC", "Vercel", "AWS Fargate", "Pulumi",
]

JOURNEY = [
    ("Education", "Computer Science", "Bina Nusantara University"),
    ("May 2024", "Data Intern", "Comms8"),
    ("Mar 2025", "AI/ML Engineer", "Comms8"),
    ("Aug 2025", "Full-Stack Developer", "Growthmarketing.tw"),
    ("Oct 2025", "Second Act Pro", "Freelance · United States"),
    ("Jan 2026", "Daphne", "Freelance · Germany"),
    ("Jul 2026", "Juraganin", "Founder · Indonesia"),
    ("Aug 2026", "AtlasPad", "Freelance · Germany"),
]
JOURNEY_HIGHLIGHT = "Juraganin"

BUTTONS = [
    ("site", "mrabbyilyas.com", True),
    ("linkedin", "LinkedIn", False),
    ("email", "Email", False),
    ("juraganin", "Juraganin", False),
]

# Site palette (mrabbyilyas.com globals.css), plus a dark counterpart.
THEMES = {
    "light": {
        "bg": "#f1ebe0", "ink": "#121110", "smoke": "#6d675e", "line": "#ddd3c2",
        "ghost": "#e5dbc9", "glow": "#e6ddcd", "shadow": "#d6ccb9", "pill": "#cfc4b1",
        "chip": "#f8f4ec", "page_ink": "#121110", "page_smoke": "#6d675e",
    },
    "dark": {
        "bg": "#151412", "ink": "#f1ebe0", "smoke": "#a39b8f", "line": "#2c2925",
        "ghost": "#201e1b", "glow": "#3a352e", "shadow": "#0b0a09", "pill": "#3d3934",
        "chip": "#1e1c19", "page_ink": "#f0f6fc", "page_smoke": "#9198a1",
    },
}
LIME = "#c8f53c"
ON_LIME = "#121110"

# ---------------------------------------------------------------- fonts

FONTS = {
    "sans": "Geist:wght@400",
    "sans-sb": "Geist:wght@600",
    "sans-xb": "Geist:wght@800",
    "mono": "Geist+Mono:wght@500",
    "serif-i": "Instrument+Serif:ital@1",
    "bodoni": "Bodoni+Moda:opsz,wght@6..96,700",
    "bodoni-i": "Bodoni+Moda:ital,opsz,wght@1,6..96,500",
    "spectral": "Spectral:wght@500",
    "spectral-i": "Spectral:ital,wght@1,400",
    "jetbrains": "JetBrains+Mono:wght@500",
    "bricolage": "Bricolage+Grotesque:opsz,wght@12..96,800",
    "bricolage-sb": "Bricolage+Grotesque:opsz,wght@12..96,600",
    "hanken": "Hanken+Grotesk:wght@500",
    "plex": "IBM+Plex+Mono:wght@500",
    "manrope": "Manrope:wght@800",
    "manrope-sb": "Manrope:wght@600",
    "manrope-md": "Manrope:wght@500",
}


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


@cache
def font_face(key: str, chars: str) -> str:
    text = urllib.parse.quote(chars, safe="")
    css = fetch(f"https://fonts.googleapis.com/css2?family={FONTS[key]}&text={text}&display=block").decode()
    faces = []
    for src in re.findall(r"url\((https://[^)]+)\)", css):
        data = base64.b64encode(fetch(src)).decode()
        faces.append(f"@font-face{{font-family:'{key}';src:url(data:font/woff2;base64,{data}) format('woff2')}}")
    return "".join(faces)


@cache
def avatar() -> str:
    return "data:image/webp;base64," + base64.b64encode(fetch(AVATAR)).decode()


def mono_width(text: str, size: float, spacing: float = 0) -> float:
    """Every mono face used here has a 0.6em advance, so widths are exact."""
    return len(text) * (size * 0.6 + spacing)


# ---------------------------------------------------------------- svg

BASE_CSS = """
.rise{animation:rise 1.1s cubic-bezier(.16,1,.3,1) both}
@keyframes rise{from{opacity:0;transform:translateY(22px)}}
.fade{animation:fade 1s ease both}
@keyframes fade{from{opacity:0}}
.float{animation:float 5s ease-in-out infinite}
@keyframes float{50%{transform:translateY(-10px)}}
.breathe{transform-box:fill-box;transform-origin:center;animation:breathe 5s ease-in-out infinite}
@keyframes breathe{50%{transform:scaleX(.84);opacity:.6}}
.ping{transform-box:fill-box;transform-origin:center;animation:ping 2.2s cubic-bezier(0,0,.2,1) infinite}
@keyframes ping{from{transform:scale(1);opacity:.7}to{transform:scale(3);opacity:0}}
.pop{transform-box:fill-box;transform-origin:center;animation:pop .7s cubic-bezier(.34,1.56,.64,1) both}
@keyframes pop{from{transform:scale(0)}}
.blink{animation:blink 2.7s ease-in-out infinite}
@keyframes blink{50%{opacity:.2}}
.bar{transform-box:fill-box;transform-origin:center;animation:bar 1.2s ease-in-out infinite}
@keyframes bar{50%{transform:scaleY(.22)}}
.swing{transform-box:fill-box;transform-origin:50% 0;animation:swing 3.2s ease-in-out infinite}
@keyframes swing{0%,100%{transform:rotate(-7deg)}50%{transform:rotate(7deg)}}
.draw{animation:draw 2s cubic-bezier(.65,0,.35,1) both}
@keyframes draw{from{stroke-dashoffset:1000}}
.slide{animation:slide linear infinite}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}
"""


class Svg:
    def __init__(self, width: float, height: float, label: str):
        self.width, self.height, self.label = width, height, label
        self.parts: list[str] = []
        self.css: list[str] = []
        self.glyphs: dict[str, set[str]] = {}

    def add(self, *parts: str) -> None:
        self.parts.extend(parts)

    def rich(self, x, y, runs, fill, anchor="start", spacing=0, attrs="") -> str:
        """runs: [(text, font, size)] set inline on one baseline."""
        spans = []
        for text, font, size in runs:
            self.glyphs.setdefault(font, set()).update(text)
            spans.append(f'<tspan class="f-{font}" font-size="{size}">{escape(text)}</tspan>')
        extra = f' letter-spacing="{spacing}"' if spacing else ""
        return (
            f'<text x="{x:g}" y="{y:g}" fill="{fill}" text-anchor="{anchor}"{extra}'
            f' xml:space="preserve" {attrs}>{"".join(spans)}</text>'
        )

    def text(self, x, y, text, font, size, fill, anchor="start", spacing=0, attrs="") -> str:
        return self.rich(x, y, [(text, font, size)], fill, anchor, spacing, attrs)

    def render(self) -> str:
        faces = "".join(font_face(key, "".join(sorted(chars))) for key, chars in sorted(self.glyphs.items()))
        families = "".join(f".f-{key}{{font-family:'{key}'}}" for key in sorted(self.glyphs))
        css = faces + families + BASE_CSS + "".join(self.css)
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.width:g} {self.height:g}"'
            f' width="{self.width:g}" height="{self.height:g}" role="img" aria-label={quoteattr(self.label)}>'
            f"<title>{escape(self.label)}</title><style>{css}</style>{''.join(self.parts)}</svg>\n"
        )


def delay(seconds: float) -> str:
    return f'style="animation-delay:{seconds:g}s"'


def arrow(cx: float, cy: float, color: str, size: float = 6, width: float = 2.2) -> str:
    """A north-east arrow drawn as a path, so it never depends on a glyph."""
    s = size
    return (
        f'<path d="M{cx - s:g} {cy + s:g}L{cx + s:g} {cy - s:g}M{cx - s * 0.45:g} {cy - s:g}H{cx + s:g}V{cy + s * 0.45:g}"'
        f' fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"/>'
    )


def pill(svg: Svg, x, y, label, font, size, fg, bg=None, stroke=None, pad=14, height=None, spacing=0) -> float:
    """Draw a mono pill and return its width."""
    height = height or size * 2.6
    width = mono_width(label, size, spacing) + pad * 2
    fill = bg or "none"
    line = f' stroke="{stroke}"' if stroke else ""
    svg.add(
        f'<rect x="{x:g}" y="{y:g}" width="{width:g}" height="{height:g}" rx="{height / 2:g}" fill="{fill}"{line}/>',
        svg.text(x + pad, y + height / 2 + size * 0.36, label, font, size, fg, spacing=spacing),
    )
    return width


def flag(code: str, x: float, y: float, w: float = 21, h: float = 14) -> str:
    clip = f"flag-{code}-{x:g}-{y:g}".replace(".", "_")
    if code == "us":
        stripes = "".join(
            f'<rect x="{x:g}" y="{y + i * h / 7:g}" width="{w:g}" height="{h / 7:g}" fill="{"#b22234" if i % 2 == 0 else "#ffffff"}"/>'
            for i in range(7)
        )
        body = stripes + f'<rect x="{x:g}" y="{y:g}" width="{w * 0.42:g}" height="{h * 4 / 7:g}" fill="#3c3b6e"/>'
    elif code == "de":
        body = "".join(
            f'<rect x="{x:g}" y="{y + i * h / 3:g}" width="{w:g}" height="{h / 3 + 0.2:g}" fill="{c}"/>'
            for i, c in enumerate(["#000000", "#dd0000", "#ffce00"])
        )
    else:  # id
        body = (
            f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h / 2:g}" fill="#ce1126"/>'
            f'<rect x="{x:g}" y="{y + h / 2:g}" width="{w:g}" height="{h / 2:g}" fill="#ffffff"/>'
        )
    return (
        f'<clipPath id="{clip}"><rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="2.5"/></clipPath>'
        f'<g clip-path="url(#{clip})">{body}</g>'
        f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="2.5" fill="none" stroke="#000" stroke-opacity=".18"/>'
    )


# ---------------------------------------------------------------- hero

def hero(theme: str) -> Svg:
    c = THEMES[theme]
    w, h = 1000, 560
    svg = Svg(w, h, "Muhammad Rabby Ilyas. I build AI products that actually ship. Full-stack and AI engineer from Indonesia.")
    svg.add(
        f'<defs><clipPath id="card"><rect width="{w}" height="{h}" rx="28"/></clipPath>'
        f'<radialGradient id="glow" cx="77%" cy="55%" r="42%">'
        f'<stop offset="0" stop-color="{c["glow"]}"/><stop offset="1" stop-color="{c["glow"]}" stop-opacity="0"/>'
        f"</radialGradient></defs>",
        '<g clip-path="url(#card)">',
        f'<rect width="{w}" height="{h}" fill="{c["bg"]}"/><rect width="{w}" height="{h}" fill="url(#glow)"/>',
        f'<g class="rise" style="animation-duration:1.8s">{svg.text(500, 604, "RABBY", "sans-xb", 300, c["ghost"], "middle", -12)}</g>',
        # Avatar stands in front of the name, like the site hero.
        f'<ellipse class="breathe" cx="782" cy="508" rx="92" ry="11" fill="{c["shadow"]}"/>',
        f'<g class="float"><g class="fade" {delay(0.2)}><image href="{avatar()}" x="548" y="70" width="460" height="460"/></g></g>',
    )

    # Speech bubble by the waving hand.
    svg.add(
        f'<g class="pop" style="animation-delay:1.3s;transform-origin:15% 100%">'
        f'<rect x="874" y="156" width="116" height="40" rx="20" fill="{c["ink"]}"/>'
        f'<path d="M888 194 L900 194 L884 210 Z" fill="{c["ink"]}"/>'
        f'{svg.text(932, 182, "Hi, I’m Rabby", "serif-i", 19, c["bg"], "middle")}'
        f"</g>"
    )

    # Top meta row.
    svg.add(
        f'<circle class="ping" cx="62" cy="52" r="5" fill="{LIME}"/><circle cx="62" cy="52" r="5" fill="{LIME}"/>',
        svg.text(78, 57, "RABBY ILYAS", "mono", 13, c["ink"], spacing=2),
        svg.text(500, 57, "INDONESIA · UTC+7", "mono", 13, c["smoke"], "middle", 2),
        svg.text(938, 57, "MRABBYILYAS.COM", "mono", 13, c["ink"], "end", 2),
    )

    # Copy.
    svg.add(
        f'<g class="rise" {delay(0.1)}>{svg.text(56, 140, "FULL-STACK & AI ENGINEER", "mono", 13, c["smoke"], spacing=2.4)}</g>',
        f'<g class="rise" {delay(0.2)}>{svg.text(54, 204, "I build AI products", "sans-sb", 56, c["ink"], spacing=-2.2)}</g>',
        f'<g class="rise" {delay(0.32)}>{svg.text(56, 270, "that actually ship.", "serif-i", 68, c["ink"])}</g>',
        f'<g class="rise" {delay(0.45)}>'
        + svg.text(56, 322, "AI products for founders in the US & Germany,", "sans", 19, c["smoke"])
        + svg.text(56, 349, "plus my own startup, Juraganin.", "sans", 19, c["smoke"])
        + "</g>",
    )

    svg.add(f'<g class="rise" {delay(0.6)}>')
    x = 56
    for label, primary in [("Full-stack & AI engineer", True), ("Based in Indonesia", False), ("Founder @ Juraganin", False)]:
        x += pill(
            svg, x, 384, label, "mono", 13,
            ON_LIME if primary else c["ink"],
            bg=LIME if primary else c["bg"],
            stroke=None if primary else c["pill"],
            height=36,
        ) + 10
    svg.add("</g>", "</g>")
    svg.add(f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="27.5" fill="none" stroke="{c["line"]}"/>')
    return svg


# ---------------------------------------------------------------- cards

def motif(svg: Svg, kind: str, colors: dict) -> None:
    fg, accent, soft = colors["fg"], colors["accent"], colors["soft"]
    if kind == "match":
        cx, cy, r = 432, 92, 30
        dots = []
        for i in range(9):
            angle = math.tau * i / 9 - math.pi / 2
            x, y = cx + r * math.cos(angle), cy + r * math.sin(angle)
            dots.append(
                f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" stroke="{accent}" stroke-opacity=".35"/>'
                f'<circle class="blink" {delay(i * 0.3)} cx="{x:.1f}" cy="{y:.1f}" r="3.6" fill="{fg}"/>'
            )
        svg.add(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{fg}" stroke-opacity=".12"/>',
            *dots,
            f'<circle class="ping" cx="{cx}" cy="{cy}" r="6" fill="{accent}"/><circle cx="{cx}" cy="{cy}" r="6" fill="{accent}"/>',
        )
    elif kind == "graph":
        nodes = [(404, 84), (436, 64), (468, 88), (420, 118), (456, 124), (440, 94)]
        edges = [(0, 1), (1, 2), (0, 5), (1, 5), (2, 5), (3, 5), (4, 5), (3, 4), (2, 4), (0, 3)]
        svg.add(*[
            f'<line x1="{nodes[a][0]}" y1="{nodes[a][1]}" x2="{nodes[b][0]}" y2="{nodes[b][1]}" stroke="{fg}" stroke-opacity=".22"/>'
            for a, b in edges
        ])
        for i, (x, y) in enumerate(nodes):
            color = accent if i % 2 == 0 else soft
            radius = 6 if i == 5 else 4.2
            svg.add(f'<circle class="blink" {delay(i * 0.45)} cx="{x}" cy="{y}" r="{radius}" fill="{color}"/>')
    elif kind == "awning":
        stripe, top = 25, 22
        parts = []
        for i in range(20):
            color = accent if i % 2 == 0 else "#fffaf0"
            x = i * stripe
            parts.append(
                f'<rect x="{x}" y="0" width="{stripe}" height="{top}" fill="{color}"/>'
                f'<path d="M{x} {top} a{stripe / 2:g} {stripe / 2.2:g} 0 0 0 {stripe} 0Z" fill="{color}"/>'
            )
        # Cream stripes nearly match the card, so outline the scallops.
        parts.append(
            "".join(
                f'<path d="M{i * stripe} {top} a{stripe / 2:g} {stripe / 2.2:g} 0 0 0 {stripe} 0" fill="none"'
                f' stroke="{accent}" stroke-opacity=".45"/>'
                for i in range(1, 20, 2)
            )
        )
        svg.add(*parts)
        svg.add(
            '<g class="swing" style="transform-origin:50% 0">',
            f'<path d="M430 34 L425 62 M460 34 L465 62" stroke="{fg}" stroke-opacity=".55" stroke-width="1.5"/>',
            f'<rect x="414" y="60" width="62" height="26" rx="5" fill="#2f6b45"/>',
            svg.text(445, 78, "BUKA", "plex", 12, "#fbf1dd", "middle", 1.5),
            "</g>",
        )
    elif kind == "wave":
        heights = [10, 22, 36, 18, 44, 30, 48, 24, 38, 16, 26, 12]
        for i, height in enumerate(heights):
            x = 396 + i * 6.4
            svg.add(
                f'<rect class="bar" {delay(i * 0.09)} x="{x:.1f}" y="{92 - height / 2:g}" width="3.4" height="{height}"'
                f' rx="1.7" fill="{accent if i % 3 else fg}"/>'
            )


def card(project: dict) -> Svg:
    colors, fonts, sizes = project["colors"], project["fonts"], project["sizes"]
    bg, fg, accent = colors["bg"], colors["fg"], colors["accent"]
    w, h = 500, 330
    svg = Svg(w, h, f'{project["title"]}: {project["tagline"]} {project["category"]}. Read the case study.')
    svg.add(
        f'<defs><clipPath id="card"><rect width="{w}" height="{h}" rx="22"/></clipPath></defs>',
        '<g clip-path="url(#card)">',
        f'<rect width="{w}" height="{h}" fill="{bg}"/>',
    )
    motif(svg, project["motif"], colors)

    mono = fonts["mono"]
    svg.add(
        svg.text(32, 54, f'CASE STUDY · {project["category"].upper()}', mono, 12, fg, spacing=1.6, attrs='fill-opacity=".7"'),
        f'<g class="rise" {delay(0.1)}>{svg.text(30, 114, project["title"], fonts["title"], sizes["title"], fg)}</g>',
        f'<g class="rise" {delay(0.2)}>{svg.text(32, 148, project["tagline"], fonts["tagline"], sizes["tagline"], accent)}</g>',
        flag(project["flag"], 32, 167),
        svg.text(61, 179, project["who"], fonts["body"], 14, fg, attrs='fill-opacity=".72"'),
        f'<line x1="32" y1="202" x2="468" y2="202" stroke="{fg}" stroke-opacity=".14"/>',
    )

    for i, (value, label) in enumerate(project["metrics"]):
        x = 32 + i * 152
        svg.add(f'<g class="rise" {delay(0.3 + i * 0.1)}>', svg.text(x, 244, value, fonts["title"], 34, fg))
        for line, chunk in enumerate(textwrap.wrap(label, 21)):
            svg.add(svg.text(x, 266 + line * 14, chunk, mono, 11, fg, attrs='fill-opacity=".6"'))
        svg.add("</g>")

    x, limit = 32, 424
    stack = project["stack"]
    for i, name in enumerate(stack):
        rest = len(stack) - i - 1
        width = mono_width(name, 11) + 20
        reserve = mono_width(f"+{rest}", 11) + 26 if rest else 0
        if x + width + reserve > limit:
            pill(svg, x, 296, f"+{len(stack) - i}", mono, 11, fg, stroke=f"{fg}40", pad=10, height=22)
            break
        x += pill(svg, x, 296, name, mono, 11, fg, stroke=f"{fg}40", pad=10, height=22) + 6

    svg.add(f'<circle cx="452" cy="307" r="19" fill="{accent}"/>', arrow(452, 307, bg, 5.5, 2.2))
    svg.add("</g>")
    return svg


# ---------------------------------------------------------------- sections

def section_header(theme: str) -> Svg:
    c = THEMES[theme]
    svg = Svg(1000, 118, "Now shipping: four products, three countries.")
    svg.add(
        svg.text(4, 34, "(NOW SHIPPING)", "mono", 13, c["page_smoke"], spacing=2.4),
        svg.rich(0, 92, [("Four products. ", "sans-sb", 44), ("Three countries.", "serif-i", 52)], c["page_ink"], spacing=-0.6),
        svg.text(996, 92, "EACH CARD OPENS ITS CASE STUDY", "mono", 12, c["page_smoke"], "end", 1.6),
    )
    return svg


def stack(theme: str) -> Svg:
    c = THEMES[theme]
    w, h = 1000, 250
    svg = Svg(w, h, "Toolbox: " + ", ".join(STACK_AI + STACK_PRODUCT))
    svg.add(
        f'<defs><clipPath id="card"><rect width="{w}" height="{h}" rx="28"/></clipPath>'
        '<linearGradient id="edge"><stop offset="0" stop-color="#000"/><stop offset=".08" stop-color="#fff"/>'
        '<stop offset=".92" stop-color="#fff"/><stop offset="1" stop-color="#000"/></linearGradient>'
        f'<mask id="fade"><rect width="{w}" height="{h}" fill="url(#edge)"/></mask></defs>',
        '<g clip-path="url(#card)">',
        f'<rect width="{w}" height="{h}" fill="{c["bg"]}"/>',
        svg.text(56, 52, "(TOOLBOX)", "mono", 13, c["smoke"], spacing=2.4),
        svg.rich(54, 102, [("The stack behind ", "sans-sb", 36), ("the work.", "serif-i", 44)], c["ink"], spacing=-0.8),
        f'<circle cx="744" cy="47" r="4.5" fill="{LIME}" stroke="{c["ink"]}" stroke-opacity=".25"/>',
        svg.text(756, 52, "AI", "mono", 12, c["smoke"], spacing=1.6),
        f'<circle cx="806" cy="47" r="4.5" fill="{c["ink"]}"/>',
        svg.text(818, 52, "PRODUCT & INFRA", "mono", 12, c["smoke"], spacing=1.6),
        '<g mask="url(#fade)">',
    )
    for row, (items, dot, y, reverse) in enumerate([(STACK_AI, LIME, 136, False), (STACK_PRODUCT, c["ink"], 186, True)]):
        chips, x = [], 0.0
        for name in items:
            width = mono_width(name, 15) + 46
            chips.append(
                f'<rect x="{x:g}" y="{y}" width="{width:g}" height="38" rx="19" fill="{c["chip"]}" stroke="{c["pill"]}"/>'
                f'<circle cx="{x + 18:g}" cy="{y + 19}" r="4.5" fill="{dot}" stroke="{c["ink"]}" stroke-opacity=".25"/>'
                + svg.text(x + 30, y + 24.5, name, "mono", 15, c["ink"])
            )
            x += width + 10
        span = x
        name = f"marquee{row}"
        svg.css.append(f"@keyframes {name}{{from{{transform:translateX(0)}}to{{transform:translateX(-{span:g}px)}}}}")
        direction = "reverse" if reverse else "normal"
        svg.add(
            f'<g class="slide" style="animation-name:{name};animation-duration:{span / 32:.1f}s;animation-direction:{direction}">',
            f'<g transform="translate(24 0)">{"".join(chips)}</g>',
            f'<g transform="translate({24 + span:g} 0)">{"".join(chips)}</g>',
            "</g>",
        )
    svg.add("</g>", "</g>")
    svg.add(f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="27.5" fill="none" stroke="{c["line"]}"/>')
    return svg


def journey(theme: str) -> Svg:
    c = THEMES[theme]
    w, h = 1000, 340
    svg = Svg(w, h, "Journey: " + "; ".join(f"{when}, {title}, {place}" for when, title, place in JOURNEY))
    svg.add(
        f'<defs><clipPath id="card"><rect width="{w}" height="{h}" rx="28"/></clipPath></defs>',
        '<g clip-path="url(#card)">',
        f'<rect width="{w}" height="{h}" fill="{c["bg"]}"/>',
        svg.text(56, 52, "(JOURNEY)", "mono", 13, c["smoke"], spacing=2.4),
        svg.rich(54, 102, [("From data intern ", "sans-sb", 36), ("to founder.", "serif-i", 44)], c["ink"], spacing=-0.8),
    )

    first, last, line_y = 72, 860, 232
    svg.add(
        f'<line class="draw" x1="{first}" y1="{line_y}" x2="900" y2="{line_y}" stroke="{c["ink"]}" stroke-opacity=".3"'
        f' stroke-width="2" stroke-dasharray="1000"/>',
    )
    step = (last - first) / (len(JOURNEY) - 1)
    for i, (when, title, place) in enumerate(JOURNEY):
        x = first + i * step
        above = i % 2 == 0
        anchor, tx = ("start", x - 12) if i == 0 else ("middle", x)
        base = line_y - 82 if above else line_y + 36
        wait = 0.4 + i * 0.16
        svg.add(
            f'<g class="fade" {delay(wait)}>',
            f'<line x1="{x:g}" y1="{line_y + (-26 if above else 12):g}" x2="{x:g}" y2="{line_y + (-12 if above else 26):g}"'
            f' stroke="{c["ink"]}" stroke-opacity=".25"/>',
            svg.text(tx, base, when.upper(), "mono", 11.5, c["smoke"], anchor, 1.4),
            svg.text(tx, base + 23, title, "sans-sb", 17, c["ink"], anchor),
            svg.text(tx, base + 43, place, "sans", 14, c["smoke"], anchor),
            "</g>",
        )
        if title == JOURNEY_HIGHLIGHT:
            svg.add(f'<circle class="ping" cx="{x:g}" cy="{line_y}" r="7" fill="{LIME}"/>')
        fill = LIME if title == JOURNEY_HIGHLIGHT else c["bg"]
        svg.add(
            f'<circle class="pop" {delay(wait)} cx="{x:g}" cy="{line_y}" r="7" fill="{fill}" stroke="{c["ink"]}" stroke-width="2"/>'
        )

    svg.add(f'<g class="fade" {delay(1.9)}>')
    pill(svg, 902, line_y - 14, "NOW", "mono", 12, ON_LIME, bg=LIME, pad=11, height=28, spacing=1.4)
    svg.add("</g>", "</g>")
    svg.add(f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="27.5" fill="none" stroke="{c["line"]}"/>')
    return svg


def footer(theme: str) -> Svg:
    # Inverted against the page: ink card in light mode, paper card in dark mode.
    c = THEMES["dark" if theme == "light" else "light"]
    w, h = 1000, 260
    accent = LIME if theme == "light" else c["ink"]
    svg = Svg(w, h, f"Got something that needs to actually ship? Email {EMAIL}.")
    svg.add(
        f'<defs><clipPath id="card"><rect width="{w}" height="{h}" rx="28"/></clipPath></defs>',
        '<g clip-path="url(#card)">',
        f'<rect width="{w}" height="{h}" fill="{c["bg"]}"/>',
        f'<g class="rise">{svg.text(500, 330, "RABBY", "sans-xb", 300, c["ghost"], "middle", -12)}</g>',
        svg.text(56, 58, "(CONTACT)", "mono", 13, c["smoke"], spacing=2.4),
        f'<g class="rise" {delay(0.1)}>{svg.text(54, 124, "Got something that needs", "sans-sb", 44, c["ink"], spacing=-1.6)}</g>',
        f'<g class="rise" {delay(0.22)}>{svg.text(56, 184, "to actually ship?", "serif-i", 60, accent)}</g>',
        svg.text(944, 104, EMAIL, "mono", 15, c["ink"], "end"),
        svg.text(944, 130, "mrabbyilyas.com", "mono", 15, c["smoke"], "end"),
        svg.text(944, 156, "linkedin.com/in/mrabbyilyas", "mono", 15, c["smoke"], "end"),
        f'<circle class="ping" cx="916" cy="206" r="24" fill="{LIME}" style="animation-duration:3s"/>',
        f'<circle cx="916" cy="206" r="24" fill="{LIME}"/>',
        arrow(916, 206, ON_LIME, 7, 2.6),
        "</g>",
    )
    return svg


def button(label: str, primary: bool) -> Svg:
    text = label.upper()
    size, spacing, h = 13, 1.4, 44
    w = mono_width(text, size, spacing) + 22 + 40
    bg, fg, line = (LIME, ON_LIME, LIME) if primary else ("#121110", "#f1ebe0", "#3d3934")
    svg = Svg(w, h, label)
    svg.add(
        f'<rect x=".5" y=".5" width="{w - 1:g}" height="{h - 1}" rx="{(h - 1) / 2:g}" fill="{bg}" stroke="{line}"/>',
        svg.text(22, 27, text, "mono", size, fg, spacing=spacing),
        arrow(w - 26, h / 2, fg, 4.2, 1.8),
    )
    return svg


# ---------------------------------------------------------------- main

def main() -> None:
    OUT.mkdir(exist_ok=True)
    files: dict[str, Svg] = {}
    for theme in THEMES:
        files[f"hero-{theme}.svg"] = hero(theme)
        files[f"work-{theme}.svg"] = section_header(theme)
        files[f"stack-{theme}.svg"] = stack(theme)
        files[f"journey-{theme}.svg"] = journey(theme)
        files[f"contact-{theme}.svg"] = footer(theme)
    for project in PROJECTS:
        files[f'card-{project["slug"]}.svg'] = card(project)
    for slug, label, primary in BUTTONS:
        files[f"button-{slug}.svg"] = button(label, primary)

    for name, svg in files.items():
        (OUT / name).write_text(svg.render(), encoding="utf-8")
        print(f"{name:32} {(OUT / name).stat().st_size / 1024:6.1f} KB")


if __name__ == "__main__":
    main()
