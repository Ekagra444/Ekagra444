#!/usr/bin/env python3
from __future__ import annotations
"""Prepare the supplied portrait for deterministic ASCII rendering.

The original photo stays outside the repository. Segmentation is performed
locally at a small working resolution with OpenCV GrabCut, using a conservative
subject prior tuned to this head-to-torso portrait. The resulting RGBA image is
only a local intermediate; the public repo receives generated SVG text art.
"""

"""
This script does three main things - 
    1. Isolates Subject 
    2. Enhances Contrast 
    3. Saves a cropped transparent RGBA PNG image
"""

import argparse
from pathlib import Path
import cv2
import numpy as np


def subject_polygon(w: int, h: int) -> np.ndarray:
    points = np.array([
        [0.31, 0.02], [0.54, 0.00], [0.62, 0.08], [0.65, 0.20],
        [0.64, 0.36], [0.70, 0.52], [0.84, 0.65], [0.97, 0.84],
        [1.00, 1.00], [0.00, 1.00], [0.03, 0.83], [0.16, 0.69],
        [0.27, 0.58], [0.32, 0.46], [0.29, 0.32], [0.14, 0.19]
    ], dtype=np.float32)

    points[:, 0] *= w
    points[:, 1] *= h
    return points.astype(np.int32)


def segment(image: np.ndarray) -> np.ndarray:
    """
    Takes the image and tells GrabCut where the person is(probably...),
    Seperate the person from the background, clean the result , return grayscale foreground mask
    """
    h, w = image.shape[:2]
    scale = min(1.0, 560.0 / max(h, w))
    small = cv2.resize(image, (round(w * scale), round(h * scale)), interpolation=cv2.INTER_AREA)
    sh, sw = small.shape[:2]

    mask = np.full((sh, sw), cv2.GC_BGD, np.uint8)
    poly = subject_polygon(sw, sh)
    cv2.fillPoly(mask, [poly], cv2.GC_PR_FGD)

    # Definite foreground seeds across hair, face, and shirt. These seeds are
    # inside the generous silhouette and guide GrabCut without encoding skin tone.
    seeds = np.array([
        [0.39, 0.10], [0.56, 0.10], [0.35, 0.28], [0.61, 0.28],
        [0.38, 0.43], [0.60, 0.43], [0.31, 0.68], [0.70, 0.75],
        [0.46, 0.90], [0.59, 0.90]
    ], dtype=np.float32)
    seeds[:, 0] *= sw
    seeds[:, 1] *= sh
    for x, y in seeds.astype(np.int32):
        cv2.circle(mask, (int(x), int(y)), max(3, sw // 30), cv2.GC_FGD, -1)

    # Extra definite background strips in the plain wall areas.
    bw = max(3, sw // 28)
    mask[:, :bw] = cv2.GC_BGD
    mask[:, -bw:] = cv2.GC_BGD
    mask[: max(3, sh // 25), :] = cv2.GC_BGD
    bg_spots = np.array([
        [0.12, 0.14],   # upper-left background globule
        [0.73, 0.14],   # upper-right background globule
    ], dtype=np.float32)

    bg_spots[:, 0] *= sw
    bg_spots[:, 1] *= sh

    radius = max(5, sw // 24)

    for x, y in bg_spots.astype(np.int32):
        cv2.circle(
            mask,
            (int(x), int(y)),
            radius,
            cv2.GC_BGD,
            -1,
        )

    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)
    cv2.grabCut(small, mask, None, bgd_model, fgd_model, 4 , cv2.GC_INIT_WITH_MASK)

    alpha_small = np.where(
        (mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0
    ).astype(np.uint8)

    # Keep the center-connected foreground and smooth the edge.
    n, labels, stats, _ = cv2.connectedComponentsWithStats(alpha_small, 8)
    cx = sw / 2
    keep = np.zeros_like(alpha_small)
    for i in range(1, n):
        x, y, ww, hh, area = stats[i]
        if x <= cx <= x + ww and area > 0.04 * sw * sh and y + hh > 0.55 * sh:
            keep[labels == i] = 255

    keep = cv2.morphologyEx(keep, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8), iterations=2)
    keep = cv2.GaussianBlur(keep, (5, 5), 0)
    alpha = cv2.resize(keep, (w, h), interpolation=cv2.INTER_CUBIC)
    return np.clip(alpha, 0, 255).astype(np.uint8)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    image = cv2.imread(str(args.source), cv2.IMREAD_COLOR)
    if image is None:
        raise SystemExit(f"Could not read image: {args.source}")

    h, w = image.shape[:2]
    if max(h, w) > 1600:
        scale = 1600 / max(h, w)
        image = cv2.resize(image, (round(w * scale), round(h * scale)), interpolation=cv2.INTER_AREA)

    alpha = segment(image)

    ys, xs = np.where(alpha > 24)
    if len(xs) == 0:
        raise SystemExit("Foreground segmentation produced an empty mask")

    pad_x = int(image.shape[1] * 0.018)
    pad_y = int(image.shape[0] * 0.018)
    x1 = max(0, int(xs.min()) - pad_x)
    x2 = min(image.shape[1], int(xs.max()) + pad_x + 1)
    y1 = max(0, int(ys.min()) - pad_y)
    y2 = min(image.shape[0], int(ys.max()) + pad_y + 1)

    image = image[y1:y2, x1:x2]
    alpha = alpha[y1:y2, x1:x2]

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)
    rgba = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGRA)
    rgba[:, :, 3] = alpha

    args.output.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(args.output), rgba)
    print(f"wrote {args.output} ({rgba.shape[1]}x{rgba.shape[0]})")


if __name__ == "__main__":
    main()
