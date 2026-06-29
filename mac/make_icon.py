"""Generate icon.png (1024x1024) for Read for Sleep — night/crescent theme."""
import math
from PIL import Image, ImageDraw, ImageFilter

S = 1024
SS = 4  # supersample
W = S * SS

img = Image.new("RGBA", (W, W), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

# Rounded-square background, vertical gradient #1A1222 -> #000003
top = (26, 18, 34)
bot = (0, 0, 3)
bg = Image.new("RGB", (W, W))
bd = ImageDraw.Draw(bg)
for y in range(W):
    t = y / W
    r = int(top[0] + (bot[0] - top[0]) * t)
    g = int(top[1] + (bot[1] - top[1]) * t)
    b = int(top[2] + (bot[2] - top[2]) * t)
    bd.line([(0, y), (W, y)], fill=(r, g, b))

# Rounded mask (macOS squircle-ish)
mask = Image.new("L", (W, W), 0)
md = ImageDraw.Draw(mask)
radius = int(W * 0.225)
md.rounded_rectangle([0, 0, W, W], radius=radius, fill=255)
img.paste(bg, (0, 0), mask)
d = ImageDraw.Draw(img)

# Stars
star_pts = [(0.22, 0.28, 7), (0.78, 0.22, 9), (0.7, 0.46, 5),
            (0.3, 0.7, 6), (0.82, 0.7, 7), (0.18, 0.52, 5), (0.6, 0.78, 5)]
for sx, sy, sr in star_pts:
    cx, cy, rr = sx * W, sy * W, sr * SS
    d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=(230, 225, 240, 220))

# Crescent moon: peach disc minus offset shadow disc
moon = Image.new("RGBA", (W, W), (0, 0, 0, 0))
mdraw = ImageDraw.Draw(moon)
mcx, mcy, mr = W * 0.54, W * 0.46, W * 0.26
mdraw.ellipse([mcx - mr, mcy - mr, mcx + mr, mcy + mr], fill=(245, 138, 46, 255))  # peach
# carve crescent
cut = Image.new("RGBA", (W, W), (0, 0, 0, 0))
cdraw = ImageDraw.Draw(cut)
ox, oy = mcx + mr * 0.55, mcy - mr * 0.32
cdraw.ellipse([ox - mr, oy - mr, ox + mr, oy + mr], fill=(0, 0, 0, 255))
moon = Image.alpha_composite(moon, _ := Image.new("RGBA", (W, W), (0, 0, 0, 0)))
# subtract: where cut alpha>0, clear moon
mp = moon.load()
cp = cut.load()
for yy in range(int(mcy - mr) - 2, int(mcy + mr) + 2):
    for xx in range(int(mcx - mr) - 2, int(mcx + mr) + 2):
        if 0 <= xx < W and 0 <= yy < W and cp[xx, yy][3] > 0:
            mp[xx, yy] = (0, 0, 0, 0)

# soft glow
glow = moon.filter(ImageFilter.GaussianBlur(18 * SS))
img = Image.alpha_composite(img, glow)
img = Image.alpha_composite(img, moon)

# downsample
img = img.resize((S, S), Image.LANCZOS)
img.save("mac/icon.png")
print("wrote mac/icon.png")
