"""Build the Cheap Stats cartoon logo from a source photo.

Turns a player photo into a clean cartoon cut-out: background removed (grabCut),
flat colour (k-means) + edges, jersey blurred to obscure club marks, output as a
**grayscale master** the app tints live with the team accent.

Usage:
    python tools/make_logo.py [path/to/photo.jpg]

All the knobs are in CONFIG below — tweak and re-run. Coordinates are fractions of
the image (0..1), so they survive a differently-sized photo. Outputs go to OUT_DIR:
  logo_mark_gray.png   the master to ship (grayscale + alpha)
  logo_tint_*.png      accent previews (teal/red/blue/gold) on the app ink

Requires: opencv-python, numpy.
"""
from __future__ import annotations
import os
import sys
import cv2
import numpy as np

# ── CONFIG ──────────────────────────────────────────────────────────────────
CONFIG = dict(
    src=r"C:\Users\mitch\Desktop\image_logo.jpg",
    out_dir=os.environ.get("TEMP", "."),

    # grabCut seeds (fractions of width/height). Probable-foreground band, a solid
    # foreground core ellipse, two arm strokes, the ball, and definite-background edges.
    fg_band=(0.06, 0.31, 0.72),                 # (top_y, left_x, right_x)
    fg_core=((0.47, 0.52), (0.14, 0.36)),       # (center xy, axes) ellipse over torso+legs
    fg_head=((0.58, 0.11), 0.06),               # (center xy, radius)
    fg_arm_left=[(0.40, 0.22), (0.345, 0.42), (0.40, 0.56)],   # image-left arm polyline
    fg_arm_right=[(0.59, 0.22), (0.66, 0.40), (0.48, 0.56)],   # image-right arm polyline
    fg_ball=((0.40, 0.60), 0.05),
    bg_left=0.31, bg_right=0.72, bg_top=0.04,
    bg_upper_left=(0.18, 0.50),                  # rect (max_y, max_x) above-left of head

    # cartoonify
    bilateral_passes=2, kmeans_k=10,

    # jersey blur (obscures club marks). Ellipse over the guernsey, skin-protected
    # so arms stay sharp. Raise blur_sigma for a stronger smear.
    blur_center=(0.47, 0.40), blur_axes=(0.18, 0.21),
    blur_feather=0.04, blur_sigma=0.055, skin_protect=True,

    # duotone tint ink background for previews
    ink=(10, 14, 20),
    tints=dict(teal="#15e6c4", red="#ff4d57", blue="#4aa8ff", gold="#ffb020"),

    # square app icon (baked teal on a rounded ink tile) -> logo_icon.png
    icon_size=512, icon_pad=0.12, icon_radius=0.20, icon_accent="#15e6c4",
)


def _rounded_mask(size, rad):
    m = np.zeros((size, size), np.uint8)
    cv2.rectangle(m, (rad, 0), (size - rad, size), 255, -1)
    cv2.rectangle(m, (0, rad), (size, size - rad), 255, -1)
    for cx, cy in [(rad, rad), (size - rad, rad), (rad, size - rad), (size - rad, size - rad)]:
        cv2.circle(m, (cx, cy), rad, 255, -1)
    return m


def make_icon(master, cfg):
    """Square app icon: the tinted figure centred on a rounded ink tile (BGRA)."""
    size, pad, ink = cfg["icon_size"], cfg["icon_pad"], cfg["ink"]
    L = master[:, :, 0].astype(np.float32) / 255
    a = master[:, :, 3].astype(np.float32) / 255
    r, g, b = (int(cfg["icon_accent"][i:i + 2], 16) for i in (1, 3, 5))
    fig = np.stack([L * b, L * g, L * r], -1).astype(np.uint8)
    fh = int(size * (1 - 2 * pad)); scale = fh / master.shape[0]
    fw = max(1, int(master.shape[1] * scale))
    fig = cv2.resize(fig, (fw, fh)); fa = cv2.resize(a, (fw, fh))[..., None]
    canvas = np.zeros((size, size, 4), np.float32)
    canvas[..., :3] = np.array(ink[::-1], np.float32)
    canvas[..., 3] = _rounded_mask(size, int(size * cfg["icon_radius"])).astype(np.float32)
    ox, oy = (size - fw) // 2, (size - fh) // 2
    roi = canvas[oy:oy + fh, ox:ox + fw, :3]
    canvas[oy:oy + fh, ox:ox + fw, :3] = fig * fa + roi * (1 - fa)
    return canvas.astype(np.uint8)


def build(cfg):
    img = cv2.imread(cfg["src"])
    if img is None:
        raise SystemExit(f"Could not read {cfg['src']}")
    H, W = img.shape[:2]
    def X(f): return int(f * W)
    def Y(f): return int(f * H)
    GC_BGD, GC_FGD, GC_PR_BGD, GC_PR_FGD = 0, 1, 2, 3

    # 1) seeded grabCut background removal
    m = np.full((H, W), GC_PR_BGD, np.uint8)
    ty, lx, rx = cfg["fg_band"]; m[Y(ty):H, X(lx):X(rx)] = GC_PR_FGD
    (cx, cy), (ax, ay) = cfg["fg_core"]; cv2.ellipse(m, (X(cx), Y(cy)), (X(ax), Y(ay)), 0, 0, 360, GC_FGD, -1)
    (hx, hy), hr = cfg["fg_head"]; cv2.circle(m, (X(hx), Y(hy)), X(hr), GC_FGD, -1)
    T = max(10, X(0.018))
    for arm in (cfg["fg_arm_left"], cfg["fg_arm_right"]):
        cv2.polylines(m, [np.array([(X(a), Y(b)) for a, b in arm])], False, GC_FGD, T)
    (bx, by), br = cfg["fg_ball"]; cv2.circle(m, (X(bx), Y(by)), X(br), GC_FGD, -1)
    m[:, :X(cfg["bg_left"])] = GC_BGD; m[:, X(cfg["bg_right"]):] = GC_BGD; m[:Y(cfg["bg_top"]), :] = GC_BGD
    uy, ux = cfg["bg_upper_left"]; m[:Y(uy), :X(ux)] = GC_BGD
    cv2.grabCut(img, m, None, np.zeros((1, 65)), np.zeros((1, 65)), 9, cv2.GC_INIT_WITH_MASK)
    fg = np.where((m == GC_FGD) | (m == GC_PR_FGD), 255, 0).astype(np.uint8)
    fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))

    # trim grass fringe (green-dominant / green hue; teal kit kept)
    Bi, Gi, Ri = [c.astype(np.int16) for c in cv2.split(img)]
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV); hh, ss = hsv[:, :, 0], hsv[:, :, 1]
    fg[((Gi > Bi + 10) & (Gi > Ri + 5)) | ((hh >= 25) & (hh <= 72) & (ss > 35))] = 0
    fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    nlab, lab, stats, _ = cv2.connectedComponentsWithStats(fg, 8)
    if nlab > 1:
        fg = np.where(lab == 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA]), 255, 0).astype(np.uint8)
    ff = fg.copy(); cv2.floodFill(ff, np.zeros((H + 2, W + 2), np.uint8), (0, 0), 255)
    fg = fg | cv2.bitwise_not(ff)
    fg = cv2.erode(fg, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)), 1)
    alpha = cv2.GaussianBlur(fg, (3, 3), 0)

    # 2) cartoonify
    color = img
    for _ in range(cfg["bilateral_passes"]):
        color = cv2.bilateralFilter(color, 9, 90, 90)
    Z = color.reshape(-1, 3).astype(np.float32)
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 12, 1.0)
    _, labels, centers = cv2.kmeans(Z, cfg["kmeans_k"], None, crit, 3, cv2.KMEANS_PP_CENTERS)
    quant = centers[labels.flatten()].astype(np.uint8).reshape(img.shape)
    g = cv2.medianBlur(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), 7)
    edges = cv2.adaptiveThreshold(g, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 9)
    cartoon = cv2.bitwise_and(quant, quant, mask=edges)

    # 3) skin-protected jersey blur (hide club marks; keep arms sharp)
    box = np.zeros((H, W), np.float32)
    (bcx, bcy), (bax, bay) = cfg["blur_center"], cfg["blur_axes"]
    cv2.ellipse(box, (X(bcx), Y(bcy)), (X(bax), Y(bay)), 0, 0, 360, 1.0, -1)
    box = cv2.GaussianBlur(box, (0, 0), X(cfg["blur_feather"]))
    if cfg["skin_protect"]:
        skin = ((Ri > 90) & (Ri >= Gi) & (Gi >= Bi) & ((Ri - Bi) > 14)).astype(np.float32) * 255
        skin = cv2.GaussianBlur(cv2.dilate(skin, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))), (0, 0), 4) / 255.0
        box = np.clip(box * (1.0 - skin), 0, 1)
    bm = box[..., None]
    cartoon = (cartoon * (1 - bm) + cv2.GaussianBlur(cartoon, (0, 0), X(cfg["blur_sigma"])) * bm).astype(np.uint8)

    # 4) grayscale master (luminance + alpha), cropped to figure
    lum = cv2.normalize(cv2.cvtColor(cartoon, cv2.COLOR_BGR2GRAY), None, 18, 255, cv2.NORM_MINMAX)
    master = cv2.merge([lum, lum, lum, alpha])
    ys, xs = np.where(alpha > 10); pad = 24
    master = master[max(0, ys.min() - pad):min(H, ys.max() + pad), max(0, xs.min() - pad):min(W, xs.max() + pad)]
    out = cfg["out_dir"]; os.makedirs(out, exist_ok=True)
    cv2.imwrite(os.path.join(out, "logo_mark_gray.png"), master)
    icon_png = os.path.join(out, "logo_icon.png")
    cv2.imwrite(icon_png, make_icon(master, cfg))
    # Windows .ico (multi-size) for the built .exe — best-effort (needs Pillow).
    try:
        from PIL import Image
        Image.open(icon_png).convert("RGBA").save(
            os.path.join(out, "logo_icon.ico"),
            sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
        )
    except Exception as e:  # pragma: no cover
        print(f"(.ico skipped: {e})")

    # 5) accent-tint previews (accent x luminance on ink) — same maths the app uses
    def tint(M, hexc, ink):
        L = M[:, :, 0].astype(np.float32) / 255; a = M[:, :, 3].astype(np.float32) / 255
        rgb = tuple(int(hexc[i:i + 2], 16) for i in (1, 3, 5))
        fig = np.stack([L * rgb[2], L * rgb[1], L * rgb[0]], -1)
        return (fig * a[..., None] + np.array(ink[::-1], np.float32) * (1 - a[..., None])).astype(np.uint8)
    for name, hexc in cfg["tints"].items():
        cv2.imwrite(os.path.join(out, f"logo_tint_{name}.png"), tint(master, hexc, cfg["ink"]))
    print(f"master {master.shape[1]}x{master.shape[0]} + {len(cfg['tints'])} tints -> {out}")


if __name__ == "__main__":
    cfg = dict(CONFIG)
    if len(sys.argv) > 1:
        cfg["src"] = sys.argv[1]
    build(cfg)
