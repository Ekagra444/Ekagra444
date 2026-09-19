#!/usr/bin/env python3
"""Generate a lightweight, animated ASCII portrait SVG from a local PNG."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Iterable

import cv2
import numpy as np

DENSITY = " .,:;irsXA253hMHGS#9B&@"


def sample_ascii(
    path: Path,
    *,
    mode: str,
    cols: int = 64,
    rows: int = 58,
    alpha_cutoff: int = 22,
) -> list[str]:
    image = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if image is None:
        raise SystemExit(f"Could not read prepared portrait: {path}")
    if image.shape[2] != 4:
        raise SystemExit("Prepared portrait must be RGBA")

    bgr = image[:, :, :3]
    alpha = image[:, :, 3]
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

    # Characters are taller than they are wide. Render at a slightly shorter
    # vertical resolution to preserve face/body proportions in monospace fonts.
    resized_gray = cv2.resize(
        gray,
        (cols, rows),
        interpolation=cv2.INTER_AREA,
    )

    resized_alpha = cv2.resize(
        alpha,
        (cols, rows),
        interpolation=cv2.INTER_AREA,
    )

    lines: list[str] = []

    for y in range(rows):
        chars = []

        for x in range(cols):
            a = int(resized_alpha[y, x])

            if a < alpha_cutoff:
                chars.append(" ")
                continue

            gray_value = int(resized_gray[y, x])

            if mode == "dark":
                # Dark background + light characters:
                # bright pixels need denser glyphs.
                value = gray_value
            else:
                # Light background + dark characters:
                # dark pixels need denser glyphs.
                value = 255 - gray_value

            idx = min(
                len(DENSITY) - 1,
                max(
                    0,
                    int(
                        value
                        / 255
                        * (len(DENSITY) - 1)
                    ),
                ),
            )

            chars.append(DENSITY[idx])

        lines.append("".join(chars).rstrip())

    while lines and not lines[-1].strip():
        lines.pop()

    return lines


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def build_svg(
    lines: Iterable[str],
    *,
    mode: str,
    output: Path,
) -> dict:
    lines = list(lines)

    width, height = 980, 520

    fg = "#E6EDF3" if mode == "dark" else "#15202B"
    muted = "#8B949E" if mode == "dark" else "#57606A"
    border = "#30363D" if mode == "dark" else "#D0D7DE"
    panel = "#0D1117" if mode == "dark" else "#F6F8FA"
    accent = "#58A6FF" if mode == "dark" else "#0969DA"

    start_x, start_y = 40, 56
    font_size = 7.65
    line_height = 7.9

    text_rows = []

    for i, line in enumerate(lines):
        y = start_y + i * line_height

        text_rows.append(
            f'<text x="{start_x}" y="{y:.1f}" '
            f'class="ascii">{esc(line)}</text>'
        )

    meta = {
        "width": width,
        "height": height,
        "columns": max(
            (len(x) for x in lines),
            default=0,
        ),
        "rows": len(lines),
        "mode": mode,
        "generator": (
            "ekagra-github-portfolio/"
            "scripts/generate_portrait.py"
        ),
    }

    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg
  xmlns="http://www.w3.org/2000/svg"
  width="{width}"
  height="{height}"
  viewBox="0 0 {width} {height}"
  role="img"
  aria-labelledby="title desc"
>
  <title id="title">
    Ekagra Agrawal — animated ASCII portrait
  </title>

  <desc id="desc">
    A monochrome terminal-style ASCII portrait with
    a rolling scan reveal.
  </desc>

  <defs>

    <style>
      .frame {{
        fill: {panel};
        stroke: {border};
        stroke-width: 1;
      }}

      .ascii {{
        fill: {fg};
        font-family:
          ui-monospace,
          SFMono-Regular,
          Menlo,
          Monaco,
          Consolas,
          "Liberation Mono",
          monospace;
        font-size: {font_size}px;
        font-weight: 500;
        letter-spacing: 0.05px;
        white-space: pre;
      }}

      .muted {{
        fill: {muted};
        font-family:
          ui-monospace,
          SFMono-Regular,
          Menlo,
          Monaco,
          Consolas,
          monospace;
        font-size: 12px;
      }}

      .accent {{
        fill: {accent};
        font-family:
          ui-monospace,
          SFMono-Regular,
          Menlo,
          Monaco,
          Consolas,
          monospace;
        font-size: 12px;
        font-weight: 700;
      }}
    </style>


    <!-- =========================================================
         SCANNER GRADIENT
         ========================================================= -->

    <linearGradient
      id="scan"
      x1="0"
      y1="0"
      x2="1"
      y2="0"
    >
      <stop
        offset="0"
        stop-color="{accent}"
        stop-opacity="0"
      />

      <stop
        offset="0.40"
        stop-color="{accent}"
        stop-opacity="0.12"
      />

      <stop
        offset="0.50"
        stop-color="{accent}"
        stop-opacity="0.75"
      />

      <stop
        offset="0.60"
        stop-color="{accent}"
        stop-opacity="0.12"
      />

      <stop
        offset="1"
        stop-color="{accent}"
        stop-opacity="0"
      />
    </linearGradient>


    <!-- =========================================================
         PORTRAIT REVEAL / ERASE MASK

         Timeline:

         0%   -> width 0
         42%  -> width 510   (fully revealed)
         50%  -> width 510   (pause)
         92%  -> width 0     (fully erased)
         100% -> width 0
         ========================================================= -->

    <mask id="roll-mask">

      <!-- Entire portrait starts hidden -->
      <rect
        x="24"
        y="24"
        width="510"
        height="455"
        fill="black"
      />

      <!-- White region = visible portrait -->
      <rect
        x="24"
        y="24"
        width="0"
        height="455"
        fill="white"
      >
        <animate
          attributeName="width"
          values="0;510;510;0;0"
          keyTimes="0;0.42;0.50;0.92;1"
          dur="15s"
          repeatCount="indefinite"
        />
      </rect>

    </mask>


    <!-- Clips the actual portrait -->
    <clipPath id="portrait-clip">
      <rect
        x="24"
        y="24"
        width="510"
        height="455"
        rx="10"
      />
    </clipPath>


    <!-- Scanner can cover the ENTIRE card -->
    <clipPath id="scanner-clip">
      <rect
        x="1"
        y="1"
        width="978"
        height="518"
        rx="14"
      />
    </clipPath>

  </defs>


  <!-- =========================================================
       OUTER CARD
       ========================================================= -->

  <rect
    class="frame"
    x="1"
    y="1"
    width="978"
    height="518"
    rx="14"
  />


  <!-- =========================================================
       TERMINAL HEADER
       ========================================================= -->

  <text
    x="24"
    y="22"
    class="muted"
  >
    ekagra@github:~$ ./profile --portrait
  </text>

  <text
    x="836"
    y="22"
    class="muted"
  >
    PROFILE
  </text>

  <circle
    cx="920"
    cy="18"
    r="4"
    fill="{accent}"
  />


  <!-- =========================================================
       PORTRAIT
       ========================================================= -->

  <g clip-path="url(#portrait-clip)">

    <rect
      x="24"
      y="24"
      width="510"
      height="455"
      fill="{panel}"
    />

    <!--
      The ASCII art itself is controlled by roll-mask.

      LEFT -> RIGHT:
          mask grows
          portrait gets painted/revealed

      RIGHT -> LEFT:
          mask shrinks
          portrait gets unpainted/erased
    -->
    <g mask="url(#roll-mask)">
      {''.join(text_rows)}
    </g>

  </g>


  <!-- =========================================================
       GLOBAL SCANNER

       IMPORTANT:

       This scanner is NOT clipped to the portrait.

       It travels across the entire 980px card, including
       the profile information on the right.
       ========================================================= -->

  <g clip-path="url(#scanner-clip)">

    <rect
      x="-360"
      y="1"
      width="360"
      height="518"
      fill="url(#scan)"
      opacity="0"
    >

      <!--
        Same timeline as the mask:

        0%  -> left
        42% -> right
        50% -> pause at right
        92% -> left
        100% -> reset
      -->
      <animate
        attributeName="x"
        values="-360;980;980;-360;-360"
        keyTimes="0;0.42;0.50;0.92;1"
        dur="15s"
        repeatCount="indefinite"
      />

      <!-- Scanner fades in/out at the edges -->
      <animate
        attributeName="opacity"
        values="0;0.35;0.35;0;0"
        keyTimes="0;0.08;0.84;0.92;1"
        dur="15s"
        repeatCount="indefinite"
      />

    </rect>

  </g>


  <!-- =========================================================
       RIGHT SIDE PROFILE
       ========================================================= -->

  <line
    x1="566"
    y1="50"
    x2="944"
    y2="50"
    stroke="{border}"
  />

  <text
    x="566"
    y="83"
    class="accent"
  >
    EKAGRA AGRAWAL
  </text>

  <text
    x="566"
    y="108"
    class="muted"
  >
    SOFTWARE ENGINEER
  </text>

  <text
    x="566"
    y="142"
    class="muted"
  >
    current
  </text>

  <text
    x="566"
    y="163"
    class="ascii"
    style="font-size:12px;"
  >
    GSPANN Technologies
  </text>

  <text
    x="566"
    y="182"
    class="ascii"
    style="font-size:12px;"
  >
    Software Engineer Trainee
  </text>

  <text
    x="566"
    y="201"
    class="ascii"
    style="font-size:12px;"
  >
    SRE focus
  </text>


  <line
    x1="566"
    y1="228"
    x2="944"
    y2="228"
    stroke="{border}"
  />

  <text
    x="566"
    y="258"
    class="muted"
  >
    signal
  </text>

  <text
    x="566"
    y="281"
    class="ascii"
    style="font-size:12px;"
  >
    900+ problems
  </text>

  <text
    x="566"
    y="300"
    class="ascii"
    style="font-size:12px;"
  >
    Codeforces Specialist · 1440
  </text>

  <text
    x="566"
    y="319"
    class="ascii"
    style="font-size:12px;"
  >
    CodeChef · global rank 193
  </text>


  <line
    x1="566"
    y1="346"
    x2="944"
    y2="346"
    stroke="{border}"
  />

  <text
    x="566"
    y="376"
    class="muted"
  >
    stack
  </text>

  <text
    x="566"
    y="397"
    class="ascii"
    style="font-size:11px;"
  >
    TypeScript · Node.js · PostgreSQL
  </text>

  <text
    x="566"
    y="416"
    class="ascii"
    style="font-size:11px;"
  >
    Redis · React · Next.js · Python
  </text>

  <text
    x="566"
    y="452"
    class="muted"
  >
    IIT Jammu · B.Tech 2026 · CGPA 8.37
  </text>

  <text
    x="566"
    y="474"
    class="muted"
  >
    github.com/Ekagra444
  </text>

</svg>
'''

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(svg, encoding="utf-8")

    return meta


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()

    manifest = {"assets": []}

    for mode in ("dark", "light"):
        # Generate a different ASCII brightness mapping for each theme.
        lines = sample_ascii(
            args.source,
            mode=mode,
        )

        out = args.output_dir / f"hero-{mode}.svg"

        meta = build_svg(
            lines,
            mode=mode,
            output=out,
        )

        manifest["assets"].append({
            "file": out.name,
            **meta,
        })

    (
        args.output_dir / "manifest.json"
    ).write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()