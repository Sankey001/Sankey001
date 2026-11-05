"""Generate a self-contained typing-animation SVG for the profile header.

Usage (from the repo root):  python3 tools/typing_svg.py assets/typing.svg

Each line is typed one character at a time, held, deleted, then the next line
starts; the whole cycle loops forever. It uses SMIL <animate> with discrete
steps, so it runs inside an <img> tag on GitHub with no JavaScript and no
external service.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from xml.sax.saxutils import escape

LINES = [
    "Python dev building AI tools & security utilities",
    "OSINT · LLMs · Automation",
    "Running models locally, shipping code publicly",
    "Currently learning AI engineering from scratch",
]

WIDTH = 640
HEIGHT = 50
FONT_SIZE = 20
CHAR_W = FONT_SIZE * 0.6  # monospace advance; textLength pins it exactly
COLOR = "#2F81F7"  # GitHub blue, readable on light and dark themes
FONT = "'Fira Code', 'JetBrains Mono', Consolas, 'DejaVu Sans Mono', monospace"


@dataclass(frozen=True)
class Frame:
    t_ms: int
    line: int
    chars: int


def build_timeline(lines, **timing):
    """Frames at which the visible character count of a line changes."""
    return _timeline(lines, **timing)[0]


def _timeline(lines, type_ms=70, hold_ms=1800, delete_ms=30, gap_ms=300):
    """(frames, cycle length in ms)."""
    frames, t = [], 0
    for i, line in enumerate(lines):
        n = len(line)
        for c in range(n + 1):  # 0..n typed
            frames.append(Frame(t, i, c))
            t += type_ms
        t += hold_ms - type_ms
        for c in range(n - 1, -1, -1):  # n-1..0 deleted
            frames.append(Frame(t, i, c))
            t += delete_ms
        t += gap_ms
    return frames, t


def _x0(line: str) -> float:
    return (WIDTH - len(line) * CHAR_W) / 2


def _fmt(v: float) -> str:
    return f"{v:.4f}".rstrip("0").rstrip(".")


def render(lines, **timing) -> str:
    if not lines:
        raise ValueError("need at least one line")
    frames, total = _timeline(lines, **timing)
    dur = f"{total}ms"
    y = HEIGHT / 2 + FONT_SIZE * 0.35
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="{escape(" | ".join(lines))}">',
        "<defs>",
    ]

    for i, line in enumerate(lines):
        own = [f for f in frames if f.line == i]
        kt, vals = [], []
        if own[0].t_ms != 0:
            kt.append(0.0)
            vals.append(0.0)
        for f in own:
            kt.append(f.t_ms / total)
            vals.append(f.chars * CHAR_W)
        parts.append(
            f'<clipPath id="c{i}"><rect x="{_fmt(_x0(line))}" y="0" width="0" height="{HEIGHT}">'
            f'<animate attributeName="width" dur="{dur}" repeatCount="indefinite" calcMode="discrete" '
            f'keyTimes="{";".join(_fmt(k) for k in kt)}" values="{";".join(_fmt(v) for v in vals)}"/>'
            "</rect></clipPath>"
        )
    parts.append("</defs>")

    for i, line in enumerate(lines):
        parts.append(
            f'<text x="{_fmt(_x0(line))}" y="{_fmt(y)}" clip-path="url(#c{i})" fill="{COLOR}" '
            f'font-family="{FONT}" font-size="{FONT_SIZE}" textLength="{_fmt(len(line) * CHAR_W)}" '
            f'lengthAdjust="spacingAndGlyphs" xml:space="preserve">{escape(line)}</text>'
        )

    # Cursor follows the last typed character and blinks.
    kt = [_fmt(f.t_ms / total) for f in frames]
    xs = [_fmt(_x0(lines[f.line]) + f.chars * CHAR_W + 1) for f in frames]
    parts.append(
        f'<rect x="{xs[0]}" y="{_fmt(HEIGHT / 2 - FONT_SIZE * 0.6)}" width="2" '
        f'height="{_fmt(FONT_SIZE * 1.1)}" fill="{COLOR}">'
        f'<animate attributeName="x" dur="{dur}" repeatCount="indefinite" calcMode="discrete" '
        f'keyTimes="{";".join(kt)}" values="{";".join(xs)}"/>'
        '<animate attributeName="opacity" dur="1s" repeatCount="indefinite" calcMode="discrete" '
        'keyTimes="0;0.5" values="1;0"/>'
        "</rect>"
    )
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def main(argv):
    out = argv[1] if len(argv) > 1 else "assets/typing.svg"
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(render(LINES))
    print(f"wrote {out}")


if __name__ == "__main__":
    main(sys.argv)
