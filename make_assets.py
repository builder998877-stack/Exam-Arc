"""Runs inside the free cloud build: makes the app icon + splash screen and sets status bar colours."""
import glob, os, re, shutil
from PIL import Image, ImageDraw, ImageFilter

RES = "android/app/src/main/res"

def bubble(d):
    body = Image.new("RGBA", (d, d)); bp = body.load()
    lav = (190, 172, 245); mint = (150, 225, 200)
    for y in range(d):
        for x in range(d):
            t = min(1, max(0, (x + y) / (2 * d)))
            r = [lav[i] + (mint[i] - lav[i]) * t for i in range(3)]
            cx, cy = (x - d / 2) / (d / 2), (y - d / 2) / (d / 2)
            rr = (cx * cx + cy * cy) ** 0.5
            k = 0.55 * min(1, rr) ** 2.2
            c = [int(r[i] * (1 - 0.25 * k) + (100, 90, 190)[i] * 0.25 * k + (255 - r[i]) * 0.35 * (1 - min(1, rr))) for i in range(3)]
            bp[x, y] = (min(255, c[0]), min(255, c[1]), min(255, c[2]), 255)
    m = Image.new("L", (d, d), 0); ImageDraw.Draw(m).ellipse((0, 0, d - 1, d - 1), fill=255)
    body.putalpha(m)
    ImageDraw.Draw(body).ellipse((0, 0, d - 1, d - 1), outline=(255, 255, 255, 235), width=max(2, d // 60))
    hl = Image.new("RGBA", (d, d), (255, 255, 255, 0)); h = ImageDraw.Draw(hl)
    h.ellipse((d * .17, d * .10, d * .62, d * .38), fill=(255, 255, 255, 215))
    h.ellipse((d * .66, d * .70, d * .80, d * .80), fill=(255, 255, 255, 150))
    return Image.alpha_composite(body, hl.filter(ImageFilter.GaussianBlur(d * .006)))

def cream(w, h):
    g = Image.new("RGB", (2, 2)); g.putpixel((0, 0), (252, 248, 241)); g.putpixel((1, 1), (239, 227, 226))
    g.putpixel((1, 0), (246, 238, 232)); g.putpixel((0, 1), (246, 238, 232))
    return g.resize((w, h), Image.BICUBIC)

def with_bubble(w, h, frac, shadow=True):
    img = cream(w, h).convert("RGBA")
    d = int(min(w, h) * frac); x0, y0 = (w - d) // 2, (h - d) // 2
    if shadow:
        sh = Image.new("RGBA", (w, h), (110, 90, 150, 0))
        ImageDraw.Draw(sh).ellipse((x0 + d * .04, y0 + d * .10, x0 + d, y0 + d * 1.06), fill=(110, 90, 150, 90))
        img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(d * .05)))
    img.alpha_composite(BUB.resize((d, d), Image.LANCZOS), (x0, y0))
    return img.convert("RGB")

BUB = bubble(640)

# --- launcher icons (plain PNG icons: simple and reliable on every phone)
master = with_bubble(512, 512, 0.66)
shutil.rmtree(f"{RES}/mipmap-anydpi-v26", ignore_errors=True)
for dpi, s in {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}.items():
    folder = f"{RES}/mipmap-{dpi}"
    os.makedirs(folder, exist_ok=True)
    ic = master.resize((s, s), Image.LANCZOS)
    ic.save(f"{folder}/ic_launcher.png")
    rd = ic.convert("RGBA"); m = Image.new("L", (s, s), 0); ImageDraw.Draw(m).ellipse((0, 0, s - 1, s - 1), fill=255)
    rd.putalpha(m); rd.save(f"{folder}/ic_launcher_round.png")
print("icons done")

# --- splash screens (replace every splash.png the template made, keeping each size)
for p in glob.glob(f"{RES}/**/splash.png", recursive=True):
    try:
        w, h = Image.open(p).size
        with_bubble(w, h, 0.30).save(p)
    except Exception as e:
        print("splash skipped", p, e)
print("splash done")

# --- status bar / navigation bar colours to match the cream look
try:
    cp = f"{RES}/values/colors.xml"
    if os.path.exists(cp):
        s = open(cp).read()
        s = re.sub(r"(<color name=\"colorPrimaryDark\">)[^<]*", r"\g<1>#F5ECE1", s)
        s = re.sub(r"(<color name=\"colorPrimary\">)[^<]*", r"\g<1>#F5ECE1", s)
        open(cp, "w").write(s)
    sp = f"{RES}/values/styles.xml"
    if os.path.exists(sp):
        s = open(sp).read()
        extra = ('<item name="android:windowLightStatusBar">true</item>'
                 '<item name="android:statusBarColor">#F5ECE1</item>'
                 '<item name="android:navigationBarColor">#FCF8F1</item>')
        s = re.sub(r'(<style name="AppTheme\.NoActionBar"[^>]*>)', r"\1" + extra, s, count=1)
        open(sp, "w").write(s)
    print("colours done")
except Exception as e:
    print("colours skipped", e)
