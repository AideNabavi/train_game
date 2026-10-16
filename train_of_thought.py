#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TRAIN OF THOUGHT  -  Pygame edition (الهام‌گرفته از Lumosity)

ویژگی‌های این نسخه
    1) تنظیم سرعت قطارها (۵ حالت از Very slow تا Extreme)
    2) عکس دلخواه برای هر رنگ قطار      -> assets/image/train_1.png ...
    3) عکس دلخواه برای هر رنگ خانه      -> assets/image/house_1.png ...
    4) ۱۰ مرحله با چیدمان مسیر و خانه‌های متفاوت (کنار صفحه، پخش‌شده، حلقه و ...)
    5) هر مرحله بک‌گراند مخصوص خودش را دارد -> assets/image/bg_1.png ...
       (اگر عکس نباشد، بک‌گراند ساختگی داخلی استفاده می‌شود)
    6) صدا: ورود قطار، رفتن به خانه‌ی درست، خانه‌ی اشتباه، موزیک و صدای قطار پس‌زمینه
       -> assets/sounds/enter.wav, correct.wav, wrong.wav, music.ogg, ambient.ogg

جریان بازی:
    1) انتخاب تعداد قطار/خانه (3..20)
    2) انتخاب مرحله (1..10)، زمان (1..5 دقیقه) و سرعت قطار
    3) بازی: روی سوییچ‌ها کلیک کن تا هر قطار به خانه‌ی هم‌رنگ خودش برسد.

کلیدها
    کلیک ماوس روی سوییچ .... تغییر مسیر
    P / Space / Esc ......... توقف
    L ....................... نمایش/مخفی کردن شماره‌ی رنگ‌ها
    M ....................... صدا روشن/خاموش
    F11 ..................... تمام‌صفحه

نصب:  pip install pygame
اجرا:  python train_of_thought.py

فهرست بخش‌های کد (برای جست‌وجوی سریع)
    [1] تنظیمات کلی (CONFIG)
    [2] توابع کمکی
    [3] صداها
    [4] بارگذاری تصاویر (قطار / خانه / بک‌گراند)
    [5] تعریف ۱۰ مرحله (LEVELS) و چیدمان خانه‌ها (PLACERS)
    [6] کلاس‌های Edge / Node / Level / Train
    [7] کلاس Game  (رویدادها، به‌روزرسانی، رسم)
"""
import array
import json
import math
import os
import random
import sys

import pygame

try:
    pygame.mixer.pre_init(44100, -16, 1, 512)
except Exception:
    pass
pygame.init()


# =====================================================================
# [1] تنظیمات کلی (CONFIG)  -  هر چیزی که می‌خواهی تغییر بدهی اینجاست
# =====================================================================
W, H = 1100, 720          # اندازه‌ی پنجره
FPS = 60
GAP = 34                  # حداقل فاصله‌ی دو قطار روی یک ریل
HUD_H = 64                # ارتفاع نوار بالای صفحه

# ---- سرعت قطار ------------------------------------------------------
# (اسم نمایش، ضریب سرعت)  ->  می‌توانی گزینه اضافه/کم کنی (حداکثر ۵ تا برای جا شدن در منو)
SPEED_OPTIONS = [("Very slow", 0.55), ("Slow", 0.80), ("Normal", 1.0),
                 ("Fast", 1.35), ("Extreme", 1.80)]
DEFAULT_SPEED_INDEX = 2   # پیش‌فرض: Normal
BASE_SPEED = 100          # سرعت پایه‌ی قطار (پیکسل بر ثانیه)
SPEED_RAMP = 0.45         # شتاب تدریجی سرعت در طول بازی
SPEED_RAMP_MAX_T = 200    # بعد از این تعداد ثانیه سرعت دیگر زیاد نمی‌شود

# ---- پوشه‌ی تصاویر --------------------------------------------------
# همه‌ی عکس‌ها داخل یک پوشه: assets/image/
#   train_1.png .. train_20.png   (عکس قطار، رو به راست)
#   house_1.png .. house_20.png   (عکس خانه)
#   bg_1.png .. bg_10.png         (بک‌گراند مرحله‌ی 1 تا 10)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSET_DIR = os.path.join(BASE_DIR, "assets")
IMAGE_DIR = os.path.join(ASSET_DIR, "image")
TRAIN_DIR = IMAGE_DIR
HOUSE_DIR = IMAGE_DIR
BG_DIR = IMAGE_DIR
USE_CUSTOM_IMAGES = True       # False = همیشه گرافیک داخلی
TRAIN_IMG_BOX = (46, 28)       # عکس قطار داخل این کادر جا می‌شود (عکس باید رو به راست باشد)
BG_DIM = 110                   # تیره کردن عکس بک‌گراند (0..255) تا ریل‌ها خوب دیده شوند
IMG_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".bmp")

# ---- پوشه‌ی صداها ---------------------------------------------------
# assets/sounds/enter.wav     ورود قطار
# assets/sounds/correct.wav   رفتن به خانه‌ی درست
# assets/sounds/wrong.wav     رفتن به خانه‌ی اشتباه
# assets/sounds/music.ogg     موزیک پس‌زمینه (لوپ)
# assets/sounds/ambient.ogg   صدای قطار پس‌زمینه (لوپ)
SOUND_DIR = os.path.join(ASSET_DIR, "sounds")
SND_EXTS = (".wav", ".ogg", ".mp3")
SFX_VOL = 0.8             # بلندی افکت‌ها
MUSIC_VOL = 0.35          # بلندی موزیک
AMBIENT_VOL = 0.25        # بلندی صدای قطار پس‌زمینه

SCORE_FILE = os.path.join(BASE_DIR, "train_of_thought_scores.json")

# ---- رنگ‌های قطار/خانه (شماره‌ی رنگ = ایندکس + 1) ---------------------
COLORS = [
    (235, 64, 52), (41, 121, 255), (39, 174, 96), (250, 210, 1),
    (142, 68, 173), (255, 140, 0), (0, 206, 209), (255, 105, 180),
    (139, 90, 43), (173, 255, 47), (0, 128, 128), (255, 160, 122),
    (128, 128, 0), (75, 0, 130), (220, 20, 60), (135, 206, 250),
    (210, 180, 140), (186, 85, 211), (192, 192, 192), (0, 255, 127),
]

try:
    screen = pygame.display.set_mode((W, H), pygame.SCALED | pygame.RESIZABLE)
except Exception:
    screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Train of Thought")


# =====================================================================
# [2] توابع کمکی
# =====================================================================
def shade(c, amt):
    """روشن/تیره کردن یک رنگ."""
    return tuple(max(0, min(255, v + amt)) for v in c)


def lerp(a, b, t):
    return a + (b - a) * t


def angle_lerp(a, b, t):
    """چرخش نرم زاویه (کوتاه‌ترین مسیر)."""
    d = (b - a + math.pi) % (2 * math.pi) - math.pi
    return a + d * t


_fonts = {}


def get_font(size, bold=True):
    k = (size, bold)
    if k not in _fonts:
        _fonts[k] = pygame.font.SysFont(
            "segoeui,helveticaneue,arial,dejavusans", size, bold=bold)
    return _fonts[k]


def draw_text(surf, s, size, color, pos, anchor="center", shadow=True, bold=True):
    f = get_font(size, bold)
    img = f.render(str(s), True, color)
    r = img.get_rect()
    setattr(r, anchor, pos)
    if shadow:
        sh = f.render(str(s), True, (0, 0, 0))
        surf.blit(sh, r.move(2, 2))
    surf.blit(img, r)
    return r


def poly(surf, color, pts, w):
    """رسم خط شکسته‌ی ضخیم با گوشه‌های گرد."""
    pygame.draw.lines(surf, color, False, pts, w)
    for p in pts[1:-1]:
        pygame.draw.circle(surf, color, (int(p[0]), int(p[1])), w // 2)


def load_scores():
    try:
        with open(SCORE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_scores(d):
    try:
        with open(SCORE_FILE, "w", encoding="utf-8") as f:
            json.dump(d, f)
    except Exception:
        pass


# =====================================================================
# [3] صداها (صدای پیش‌فرض با ریاضی ساخته می‌شود؛ فایل دلخواه جایش را می‌گیرد)
# =====================================================================
def find_sound(stem):
    """دنبال stem.wav / stem.ogg / stem.mp3 در پوشه‌ی صداها می‌گردد."""
    for ext in SND_EXTS:
        p = os.path.join(SOUND_DIR, stem + ext)
        if os.path.isfile(p):
            return p
    return None


class Sounds:
    def __init__(self):
        self.on = True
        self.ok = False
        self.s = {}
        self.music_path = None
        self.ambient = None
        self.amb_ch = None
        self._applied = None
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(44100, -16, 1, 512)
            self.rate, _fmt, self.ch = pygame.mixer.get_init()
            self.s["click"] = self.tone([(700, .04)], .25)
            self.s["correct"] = self.tone([(660, .08), (880, .14)], .30)
            self.s["wrong"] = self.tone([(170, .28)], .30, "square")
            self.s["beep"] = self.tone([(660, .12)], .30)
            self.s["go"] = self.tone([(990, .30)], .30)
            self.s["over"] = self.tone([(523, .12), (659, .12), (784, .12), (1047, .35)], .30)
            self.ok = True
        except Exception:
            self.ok = False
            return

        # --- صداهای دلخواه (اگر فایل باشد، جای صدای ساختگی را می‌گیرد)
        for name in ("enter", "correct", "wrong"):
            p = find_sound(name)
            if p:
                try:
                    snd = pygame.mixer.Sound(p)
                    snd.set_volume(SFX_VOL)
                    self.s[name] = snd
                except Exception:
                    pass
        self.music_path = find_sound("music")
        p = find_sound("ambient")
        if p:
            try:
                self.ambient = pygame.mixer.Sound(p)
                self.ambient.set_volume(AMBIENT_VOL)
            except Exception:
                self.ambient = None

    def tone(self, notes, vol=.3, wave="sine"):
        buf = array.array("h")
        for f, d in notes:
            n = int(self.rate * d)
            for i in range(n):
                t = i / self.rate
                env = (1 - i / n) ** 1.3
                if wave == "square":
                    v = (1.0 if math.sin(2 * math.pi * f * t) >= 0 else -1.0) * .6
                else:
                    v = math.sin(2 * math.pi * f * t)
                val = int(32767 * vol * env * v)
                for _ in range(self.ch):
                    buf.append(val)
        return pygame.mixer.Sound(buffer=buf.tobytes())

    def play(self, name):
        if self.on and self.ok and name in self.s:
            self.s[name].play()

    def start_bg(self):
        """شروع موزیک و صدای قطار پس‌زمینه (هر بار که بازی جدید شروع می‌شود)."""
        if not self.ok:
            return
        self._applied = None
        try:
            if self.music_path:
                pygame.mixer.music.load(self.music_path)
                pygame.mixer.music.set_volume(MUSIC_VOL)
                pygame.mixer.music.play(-1)
            if self.ambient:
                self.ambient.stop()
                self.amb_ch = self.ambient.play(loops=-1)
        except Exception:
            pass

    def set_bg(self, want):
        """پخش/توقف صدای پس‌زمینه (توقف بازی، خاموشی صدا، پایان بازی)."""
        state = bool(want and self.on)
        if state == self._applied or not self.ok:
            return
        self._applied = state
        try:
            if state:
                pygame.mixer.music.unpause()
                if self.amb_ch:
                    self.amb_ch.unpause()
            else:
                pygame.mixer.music.pause()
                if self.amb_ch:
                    self.amb_ch.pause()
        except Exception:
            pass


# =====================================================================
# [4] بارگذاری تصاویر  (قطار / خانه / بک‌گراند)
# =====================================================================
def ensure_asset_dirs():
    """پوشه‌های تصاویر و صداها را می‌سازد تا بدانی فایل‌ها را کجا بگذاری."""
    try:
        for d in (IMAGE_DIR, SOUND_DIR):
            os.makedirs(d, exist_ok=True)
        readme = os.path.join(ASSET_DIR, "README.txt")
        if not os.path.exists(readme):
            with open(readme, "w", encoding="utf-8") as f:
                f.write(
                    "عکس‌ها (png/jpg/webp) در assets/image/ :\n"
                    "  1.png ... 2.png   (عکس قطار، رو به راست)\n"
                    "  h1.png ... h2.png   (عکس خانه)\n"
                    "  bg_1.png ... bg_2.png         (بک‌گراند مرحله‌ی 1 تا 10)\n"
                    "شماره = شماره‌ی رنگ (همان عددی که با کلید L دیده می‌شود).\n\n"
                    "صداها (wav/ogg/mp3) در assets/sounds/ :\n"
                    "  enter    ورود قطار\n"
                    "  correct  رفتن به خانه‌ی درست\n"
                    "  wrong    رفتن به خانه‌ی اشتباه\n"
                    "  music    موزیک پس‌زمینه\n"
                    "  ambient  صدای قطار پس‌زمینه\n"
                    "فایلی که نباشد، پیش‌فرض بازی استفاده می‌شود.\n")
    except Exception:
        pass


def find_image(folder, stem):
    """دنبال stem.png / stem.jpg ... می‌گردد و مسیر را برمی‌گرداند (یا None)."""
    for ext in IMG_EXTS:
        p = os.path.join(folder, stem + ext)
        if os.path.isfile(p):
            return p
    return None


def fit_surface(img, bw, bh):
    """عکس را با حفظ نسبت داخل کادر bw*bh جا می‌دهد."""
    k = min(bw / img.get_width(), bh / img.get_height())
    size = (max(1, int(img.get_width() * k)), max(1, int(img.get_height() * k)))
    return pygame.transform.smoothscale(img, size)


_raw_cache = {}


def load_custom(kind, ci):
    """عکس خام قطار/خانه برای رنگ ci (یا None اگر فایلی نبود)."""
    if not USE_CUSTOM_IMAGES:
        return None
    key = (kind, ci)
    if key not in _raw_cache:
        img = None
        folder, stem = (TRAIN_DIR, "train_%d") if kind == "train" else (HOUSE_DIR, "house_%d")
        p = find_image(folder, stem % (ci + 1))
        if p:
            try:
                img = pygame.image.load(p).convert_alpha()
            except Exception:
                img = None
        _raw_cache[key] = img
    return _raw_cache[key]


# ---- قطار -----------------------------------------------------------
_train_cache = {}


def train_surface(ci, scale=1.0):
    """اسپرایت قطار رنگ ci (عکس دلخواه یا گرافیک داخلی)."""
    key = (ci, round(scale, 2))
    if key in _train_cache:
        return _train_cache[key]
    custom = load_custom("train", ci)
    if custom is not None:
        base = fit_surface(custom, *TRAIN_IMG_BOX)
    else:
        col = COLORS[ci]
        w, h = 40, 22
        base = pygame.Surface((w + 6, h + 6), pygame.SRCALPHA)
        body = pygame.Rect(3, 3, w, h)
        pygame.draw.rect(base, (245, 245, 245), body, border_radius=7)
        pygame.draw.rect(base, col, body.inflate(-4, -4), border_radius=5)
        cab = pygame.Rect(5, 5, int(w * .32), h - 4)
        pygame.draw.rect(base, shade(col, -60), cab, border_radius=4)
        pygame.draw.circle(base, (40, 40, 46), (3 + int(w * .68), 3 + h // 2), 4)
        pygame.draw.circle(base, (255, 235, 120), (3 + w - 3, 3 + h // 2), 3)
        for xx in (int(w * .18), int(w * .7)):
            pygame.draw.rect(base, (30, 30, 34), (3 + xx, 1, 7, 3), border_radius=1)
            pygame.draw.rect(base, (30, 30, 34), (3 + xx, 3 + h - 1, 7, 3), border_radius=1)
    if abs(scale - 1.0) > .01:
        base = pygame.transform.smoothscale(
            base, (max(2, int(base.get_width() * scale)), max(2, int(base.get_height() * scale))))
    _train_cache[key] = base
    return base


# ---- خانه -----------------------------------------------------------
_house_cache = {}


def house_surface(ci, size):
    """اسپرایت خانه‌ی رنگ ci با اندازه‌ی size (عکس دلخواه یا گرافیک داخلی)."""
    key = (ci, size)
    if key in _house_cache:
        return _house_cache[key]
    custom = load_custom("house", ci)
    if custom is not None:
        s = fit_surface(custom, size, int(size * 1.15))
        _house_cache[key] = s
        return s
    col = COLORS[ci]
    w, h = size, int(size * 1.15)
    s = pygame.Surface((w + 4, h + 4), pygame.SRCALPHA)
    body = pygame.Rect(2 + int(w * .08), 2 + int(h * .42), int(w * .84), int(h * .58))
    pygame.draw.rect(s, col, body, border_radius=4)
    pygame.draw.rect(s, (245, 245, 245), body, 2, border_radius=4)
    roof = [(2, 2 + int(h * .46)), (2 + w // 2, 2), (2 + w, 2 + int(h * .46))]
    pygame.draw.polygon(s, shade(col, -80), roof)
    pygame.draw.polygon(s, (245, 245, 245), roof, 2)
    door = pygame.Rect(0, 0, max(5, int(w * .2)), int(h * .26))
    door.midbottom = (2 + w // 2, 2 + h - 2)
    pygame.draw.rect(s, shade(col, -100), door, border_radius=2)
    win = pygame.Rect(2 + int(w * .66), 2 + int(h * .54), max(4, int(w * .16)), max(4, int(w * .16)))
    pygame.draw.rect(s, (255, 240, 170), win, border_radius=2)
    _house_cache[key] = s
    return s


# ---- بک‌گراند (۱۰ تم) --------------------------------------------------
# kind = نوع تزئینات: dots / blobs / stars / dunes / waves / grid
THEMES = [
    dict(name="Meadow",  top=(34, 58, 52),   bot=(24, 42, 42),  kind="dots",
         deco=[(40, 68, 58), (28, 50, 46), (44, 74, 62)]),
    dict(name="Desert",  top=(120, 98, 60),  bot=(92, 72, 44),  kind="dunes",
         deco=[(140, 116, 74), (104, 82, 50)]),
    dict(name="Snow",    top=(150, 170, 190), bot=(110, 132, 156), kind="dots",
         deco=[(200, 214, 228), (170, 188, 206)]),
    dict(name="Night",   top=(10, 14, 36),   bot=(20, 26, 58),  kind="stars",
         deco=[(240, 240, 200), (150, 160, 210)]),
    dict(name="Autumn",  top=(86, 56, 30),   bot=(60, 38, 24),  kind="dots",
         deco=[(170, 86, 30), (200, 130, 40), (120, 60, 28)]),
    dict(name="Beach",   top=(30, 110, 130), bot=(20, 80, 106), kind="waves",
         deco=[(70, 160, 176), (40, 120, 146)]),
    dict(name="Volcano", top=(48, 20, 20),   bot=(28, 12, 14),  kind="dots",
         deco=[(200, 70, 30), (120, 40, 24)]),
    dict(name="Candy",   top=(120, 80, 130), bot=(90, 60, 110), kind="dots",
         deco=[(170, 120, 180), (200, 150, 200)]),
    dict(name="Forest",  top=(18, 52, 34),   bot=(12, 36, 26),  kind="blobs",
         deco=[(26, 74, 46), (20, 60, 38), (34, 90, 54)]),
    dict(name="City",    top=(50, 54, 62),   bot=(36, 40, 48),  kind="grid",
         deco=[(66, 72, 82), (44, 48, 58)]),
]


def procedural_bg(idx):
    """بک‌گراند ساختگی تم شماره‌ی idx (وقتی عکسی وجود ندارد)."""
    th = THEMES[idx]
    s = pygame.Surface((W, H))
    for y in range(H):
        t = y / H
        c = tuple(int(lerp(th["top"][i], th["bot"][i], t)) for i in range(3))
        pygame.draw.line(s, c, (0, y), (W, y))
    rng = random.Random(100 + idx)
    kind, deco = th["kind"], th["deco"]
    if kind == "dots":
        for _ in range(420):
            pygame.draw.circle(s, rng.choice(deco), (rng.randrange(W), rng.randrange(HUD_H, H)),
                               rng.randint(2, 6))
    elif kind == "blobs":
        for _ in range(150):
            pygame.draw.circle(s, rng.choice(deco), (rng.randrange(W), rng.randrange(HUD_H, H)),
                               rng.randint(10, 28))
    elif kind == "stars":
        for _ in range(260):
            pygame.draw.circle(s, rng.choice(deco), (rng.randrange(W), rng.randrange(HUD_H, H)),
                               rng.choice((1, 1, 1, 2)))
    elif kind == "dunes":
        for _ in range(110):
            pygame.draw.ellipse(s, rng.choice(deco),
                                (rng.randrange(-40, W), rng.randrange(HUD_H, H),
                                 rng.randint(70, 200), rng.randint(8, 22)))
    elif kind == "waves":
        for _ in range(170):
            pygame.draw.arc(s, rng.choice(deco),
                            (rng.randrange(W), rng.randrange(HUD_H, H), 44, 22), 0, math.pi, 2)
    elif kind == "grid":
        for x in range(0, W, 60):
            pygame.draw.line(s, deco[1], (x, HUD_H), (x, H), 1)
        for y in range(HUD_H, H, 60):
            pygame.draw.line(s, deco[1], (0, y), (W, y), 1)
        for _ in range(90):
            pygame.draw.rect(s, rng.choice(deco),
                             (rng.randrange(0, W, 60) + 6, rng.randrange(HUD_H, H, 60) + 6,
                              rng.randint(12, 44), rng.randint(12, 44)))
    return s


_bg_cache = {}


def get_background(idx):
    """بک‌گراند مرحله‌ی idx: اول عکس bg_N، اگر نبود تم ساختگی."""
    if idx in _bg_cache:
        return _bg_cache[idx]
    s = None
    if USE_CUSTOM_IMAGES:
        p = find_image(BG_DIR, "bg_%d" % (idx + 1))
        if p:
            try:
                img = pygame.image.load(p).convert()
                s = pygame.transform.smoothscale(img, (W, H))
                dim = pygame.Surface((W, H), pygame.SRCALPHA)
                dim.fill((0, 0, 0, BG_DIM))
                s.blit(dim, (0, 0))
            except Exception:
                s = None
    if s is None:
        s = procedural_bg(idx)
    _bg_cache[idx] = s
    return s


# =====================================================================
# [5] ۱۰ مرحله و چیدمان خانه‌ها
# =====================================================================
# هر PLACER لیستی از موقعیت خانه‌ها (x, y) برمی‌گرداند.
# ترتیب لیست مهم است: درخت مسیرها از روی «نیمه کردن لیست» ساخته می‌شود،
# پس خانه‌های کنار هم در لیست، در یک شاخه قرار می‌گیرند.

def along_path(path, n):
    """n نقطه با فاصله‌ی مساوی روی یک خط شکسته."""
    segs, total = [], 0.0
    for a, b in zip(path, path[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        segs.append((a, b, L))
        total += L
    out = []
    for i in range(n):
        s = (i + .5) * total / n
        for a, b, L in segs:
            if s <= L or (a, b, L) == segs[-1]:
                t = min(1, s / L) if L else 0
                out.append((lerp(a[0], b[0], t), lerp(a[1], b[1], t)))
                break
            s -= L
    return out


def poisson(n, rng, x0, x1, y0, y1):
    """n نقطه‌ی تصادفی با حداقل فاصله‌ی مناسب (پخش‌شده و بدون تداخل)."""
    r = 0.68 * math.sqrt((x1 - x0) * (y1 - y0) / n)
    while True:
        pts, tries = [], 0
        while len(pts) < n and tries < 3000:
            p = (rng.uniform(x0, x1), rng.uniform(y0, y1))
            if all(math.hypot(p[0] - q[0], p[1] - q[1]) >= r for q in pts):
                pts.append(p)
            tries += 1
        if len(pts) == n:
            return pts
        r *= 0.92


def place_bottom(n, rng):          # ردیف پایین صفحه
    sp = (W - 90) / n
    return [(45 + sp * (i + .5), 610) for i in range(n)]


def place_sides(n, rng):           # دو ستون چپ و راست
    nl = n // 2
    nr = n - nl
    left = [(62, 170 + 470 * (i + .5) / nl) for i in range(nl)]
    right = [(W - 62, 170 + 470 * (i + .5) / nr) for i in range(nr)]
    return left + right[::-1]


def place_scatter(n, rng):         # پخش‌شده در کل صفحه
    return poisson(n, rng, 80, W - 80, 290, 650)


def place_frame(n, rng):           # دور تا دور صفحه (U شکل)
    return along_path([(55, 170), (55, 645), (W - 55, 645), (W - 55, 170)], n)


def place_zigzag(n, rng):          # دو ردیف زیگزاگی پایین
    sp = (W - 90) / n
    return [(45 + sp * (i + .5), 590 if i % 2 == 0 else 650) for i in range(n)]


def place_arc(n, rng):             # کمان (لبخند) دور نقطه‌ی شروع
    out = []
    for i in range(n):
        a = math.radians(15 + 150 * (i + .5) / n)
        out.append((550 + 490 * math.cos(a), 160 + 470 * math.sin(a)))
    return out


def place_L(n, rng):               # شکل L: پایین + سمت راست
    return along_path([(330, 645), (W - 55, 645), (W - 55, 170)], n)


def place_clusters(n, rng):        # گروه‌های کوچک در گوشه‌ها
    centers = [(150, 320), (950, 320), (280, 590), (820, 590)]
    k = min(4, n)
    out = []
    for ci in range(k):
        m = n // k + (1 if ci < n % k else 0)
        cols = math.ceil(math.sqrt(m))
        rows = math.ceil(m / cols)
        for j in range(m):
            r_, c_ = divmod(j, cols)
            out.append((centers[ci][0] + (c_ - (cols - 1) / 2) * 62,
                        centers[ci][1] + (r_ - (rows - 1) / 2) * 62))
    return out


def place_ring(n, rng):            # حلقه‌ی بیضی دور مرکز
    out = []
    for i in range(n):
        a = math.radians(-90 + 28 + 304 * (i + .5) / n)
        out.append((550 + 480 * math.cos(a), 450 + 190 * math.sin(a)))
    return out


def place_chaos(n, rng):           # پخش‌شده‌ی شلوغ
    return poisson(n, rng, 70, W - 70, 250, 660)


PLACERS = dict(bottom=place_bottom, sides=place_sides, scatter=place_scatter,
               frame=place_frame, zigzag=place_zigzag, arc=place_arc,
               L=place_L, clusters=place_clusters, ring=place_ring, chaos=place_chaos)

# ---- تعریف ۱۰ مرحله ---------------------------------------------------
#  place  : نوع چیدمان خانه‌ها
#  split  : "order" = تقسیم درخت به ترتیب لیست | "kd" = تقسیم بر اساس موقعیت
#  tangle : احتمال تقسیم تصادفی (هرچه بیشتر، مسیرها بیشتر در هم می‌روند) 0..1
#  route  : شکل ریل‌ها: "v" عمودی-افقی | "h" افقی-عمودی | "diag" مورب | "mixed" ترکیبی
#  start_x: محل ورود قطارها (x)
LEVELS = [
    dict(name="Classic Yard",     place="bottom",   split="order", tangle=0.00, route="v"),
    dict(name="Two Sides",        place="sides",    split="order", tangle=0.00, route="h"),
    dict(name="Scattered Town",   place="scatter",  split="kd",    tangle=0.00, route="mixed"),
    dict(name="Border Loop",      place="frame",    split="order", tangle=0.15, route="mixed"),
    dict(name="Zigzag Row",       place="zigzag",   split="order", tangle=0.30, route="diag"),
    dict(name="Rainbow Arc",      place="arc",      split="order", tangle=0.10, route="diag"),
    dict(name="Corner Express",   place="L",        split="order", tangle=0.20, route="mixed", start_x=230),
    dict(name="Villages",         place="clusters", split="order", tangle=0.20, route="h"),
    dict(name="Round Trip",       place="ring",     split="order", tangle=0.25, route="mixed"),
    dict(name="Spaghetti Chaos",  place="chaos",    split="kd",    tangle=1.00, route="mixed"),
]


# =====================================================================
# [6] کلاس‌های شبکه‌ی ریل: Edge / Node / Level / Train
# =====================================================================
class Edge:
    """یک ریل (خط شکسته) از یک گره به گره‌ی بعدی."""

    def __init__(self, pts, src=None, dst=None):
        clean = [pts[0]]
        for p in pts[1:]:
            if abs(p[0] - clean[-1][0]) > .01 or abs(p[1] - clean[-1][1]) > .01:
                clean.append(p)
        self.pts = clean
        self.cum = [0.0]
        for a, b in zip(clean, clean[1:]):
            self.cum.append(self.cum[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
        self.length = self.cum[-1]
        self.src, self.dst = src, dst
        self.trains = []

    def pos(self, d):
        """موقعیت و زاویه‌ی نقطه‌ای که d پیکسل از ابتدای ریل فاصله دارد."""
        d = max(0.0, min(self.length, d))
        for i in range(1, len(self.cum)):
            if d <= self.cum[i]:
                seg = self.cum[i] - self.cum[i - 1]
                t = (d - self.cum[i - 1]) / seg if seg else 0
                x1, y1 = self.pts[i - 1]
                x2, y2 = self.pts[i]
                return x1 + (x2 - x1) * t, y1 + (y2 - y1) * t, math.atan2(y2 - y1, x2 - x1)
        x1, y1 = self.pts[-2]
        x2, y2 = self.pts[-1]
        return x2, y2, math.atan2(y2 - y1, x2 - x1)


class Node:
    """گره: switch (سوییچ دوراهی) | house (خانه) | merge (قیف ورودی)."""

    def __init__(self, kind, x, y):
        self.kind, self.x, self.y = kind, x, y
        self.outs = []      # ریل‌های خروجی
        self.kids = []      # فرزندها (فقط سوییچ)
        self.leaves = []    # خانه‌های زیر این سوییچ
        self.state = 0      # کدام خروجی فعال است
        self.color = None   # رنگ خانه
        self.flash = 0.0
        self.flash_col = (255, 255, 255)
        self.shake = 0.0


class Level:
    """ساخت یک مرحله: خانه‌ها، سوییچ‌ها، ریل‌ها و تصویر پس‌زمینه‌ی ریل."""

    def __init__(self, n, idx, rng):
        self.n, self.idx = n, idx
        self.cfg = cfg = LEVELS[idx]
        self.edges, self.switches, self.houses, self.entries = [], [], [], []

        # --- ۱) خانه‌ها و رنگ‌هایشان
        pts = PLACERS[cfg["place"]](n, rng)
        colors = list(range(n))
        rng.shuffle(colors)
        for (x, y), c in zip(pts, colors):
            h = Node("house", x, y)
            h.color = c
            self.houses.append(h)
        mind = min(math.hypot(a.x - b.x, a.y - b.y)
                   for i, a in enumerate(self.houses) for b in self.houses[i + 1:])
        self.house_size = int(max(20, min(46, mind - 6)))

        # --- ۲) درخت سوییچ‌ها (همیشه حل‌شدنی: هر رنگ به هر خانه می‌رسد)
        self.funnel = Node("merge", cfg.get("start_x", W / 2), 190)
        self.root = self.build_tree(self.houses, rng)
        self.place_switches()
        self.relax()

        # --- ۳) ریل‌ها
        mode = cfg["route"]
        for sw in self.switches:
            sw.state = rng.randrange(2)
            for kid in sw.kids:
                e = Edge(self.route(sw, kid, mode, rng), sw, kid)
                sw.outs.append(e)
                self.edges.append(e)
        trunk = Edge(self.route(self.funnel, self.root, "v", rng), self.funnel, self.root)
        self.funnel.outs = [trunk]
        self.edges.append(trunk)

        # --- ۴) تونل‌های ورودی
        ne = 2 if n <= 6 else 3 if n <= 13 else 4
        sx = self.funnel.x
        for i in range(ne):
            ex = max(70, min(W - 70, sx + (i - (ne - 1) / 2) * 170))
            e = Edge([(ex, 78), (ex, 112), (sx, self.funnel.y)], None, self.funnel)
            self.entries.append(e)
            self.edges.append(e)

        self.track = self.make_track(get_background(idx))

    # ---- ساخت درخت دودویی از لیست خانه‌ها
    def build_tree(self, hs, rng):
        if len(hs) == 1:
            return hs[0]
        hs2 = hs[:]
        if rng.random() < self.cfg["tangle"]:
            rng.shuffle(hs2)                       # تقسیم تصادفی -> ریل‌های در هم
        elif self.cfg["split"] == "kd":
            sx = max(h.x for h in hs) - min(h.x for h in hs)
            sy = max(h.y for h in hs) - min(h.y for h in hs)
            hs2.sort(key=(lambda h: h.x) if sx >= sy else (lambda h: h.y))
        mid = len(hs2) // 2
        nd = Node("switch", 0, 0)
        nd.leaves = hs
        nd.kids = [self.build_tree(hs2[:mid], rng), self.build_tree(hs2[mid:], rng)]
        self.switches.append(nd)
        return nd

    # ---- موقعیت اولیه‌ی سوییچ‌ها: بین ورودی و مرکز خانه‌های زیرش
    def place_switches(self):
        for nd in self.switches:
            size = len(nd.leaves)
            cx = sum(h.x for h in nd.leaves) / size
            cy = sum(h.y for h in nd.leaves) / size
            f = .25 + .6 * (1 - size / self.n)
            nd.x = lerp(self.funnel.x, cx, f)
            nd.y = lerp(self.funnel.y, cy, f)

    # ---- دور کردن سوییچ‌ها از هم و از خانه‌ها (برای کلیک راحت)
    def relax(self):
        sws = self.switches
        for _ in range(40):
            for i, a in enumerate(sws):
                for b in sws[i + 1:]:
                    d = math.hypot(a.x - b.x, a.y - b.y)
                    if d < 58:
                        ux, uy = ((a.x - b.x) / d, (a.y - b.y) / d) if d else (1, 0)
                        push = (58 - d) / 2
                        a.x += ux * push
                        a.y += uy * push
                        b.x -= ux * push
                        b.y -= uy * push
                for o in self.houses + [self.funnel]:
                    d = math.hypot(a.x - o.x, a.y - o.y)
                    if d < 62:
                        ux, uy = ((a.x - o.x) / d, (a.y - o.y) / d) if d else (0, -1)
                        a.x += ux * (62 - d)
                        a.y += uy * (62 - d)
            for a in sws:
                a.x = max(50, min(W - 50, a.x))
                a.y = max(250, min(620, a.y))

    # ---- شکل ریل بین دو گره
    def route(self, a, b, mode, rng):
        if mode == "mixed":
            mode = rng.choice(("v", "h", "diag", "v", "h"))
        p, q = (a.x, a.y), (b.x, b.y)
        if mode == "v":
            my = lerp(a.y, b.y, rng.uniform(.3, .7))
            return [p, (a.x, my), (b.x, my), q]
        if mode == "h":
            mx = lerp(a.x, b.x, rng.uniform(.3, .7))
            return [p, (mx, a.y), (mx, b.y), q]
        return [p, q]

    # ---- تصویر ثابت ریل‌ها روی بک‌گراند
    def make_track(self, bg):
        s = bg.copy()
        for e in self.edges:
            poly(s, (58, 50, 46), e.pts, 22)          # بستر
        for e in self.edges:                           # تراورس‌ها
            carry = 0.0
            for (x1, y1), (x2, y2) in zip(e.pts, e.pts[1:]):
                L = math.hypot(x2 - x1, y2 - y1)
                if L == 0:
                    continue
                dx, dy = (x2 - x1) / L, (y2 - y1) / L
                px, py = -dy, dx
                d = carry
                while d < L:
                    cx, cy = x1 + dx * d, y1 + dy * d
                    pygame.draw.line(s, (100, 76, 54), (cx + px * 10, cy + py * 10),
                                     (cx - px * 10, cy - py * 10), 3)
                    d += 13
                carry = d - L
        for e in self.edges:
            poly(s, (36, 38, 44), e.pts, 9)            # ریل تیره
        return s


class Train:
    def __init__(self, tid, c, edge):
        self.id, self.c, self.edge, self.dist = tid, c, edge, 0.0
        self.x, self.y, self.angle = edge.pos(0)


# =====================================================================
# [7] کلاس Game
# =====================================================================
class Game:
    # ------------------------------------------------------------ ساخت
    def __init__(self):
        self.clock = pygame.time.Clock()
        self.frame = pygame.Surface((W, H))
        self.snd = Sounds()
        self.scores = load_scores()
        self.state = "count"          # count | setup | countdown | play | pause | over
        self.n, self.pre_n = 3, 3     # تعداد قطار/خانه
        self.minutes = 2
        self.lvl = 0                  # مرحله (0..9)
        self.speed_idx = DEFAULT_SPEED_INDEX
        self.labels = False
        self.menu_t = 0.0
        self.hover = None
        self.shake = 0.0
        self.paused_from = "play"
        self.run_key = ""
        self.build_menu_rects()

    def build_menu_rects(self):
        """مستطیل دکمه‌های منوها."""
        # صفحه‌ی انتخاب تعداد
        self.count_btns = []
        bw, bh, gx, gy = 120, 64, 18, 16
        x0 = (W - (6 * bw + 5 * gx)) // 2
        for i, n in enumerate(range(3, 21)):
            r = pygame.Rect(x0 + (i % 6) * (bw + gx), 232 + (i // 6) * (bh + gy), bw, bh)
            self.count_btns.append((n, r))
        # صفحه‌ی تنظیمات: مرحله / زمان / سرعت
        self.level_btns = [pygame.Rect(47 + i * 102, 124, 88, 52) for i in range(len(LEVELS))]
        tw, tg = 150, 22
        tx = (W - (5 * tw + 4 * tg)) // 2
        self.time_btns = [(m, pygame.Rect(tx + (m - 1) * (tw + tg), 252, tw, 56)) for m in range(1, 6)]
        self.speed_btns = [pygame.Rect(tx + i * (tw + tg), 352, tw, 56) for i in range(len(SPEED_OPTIONS))]
        self.start_btn = pygame.Rect(W // 2 - 130, 616, 260, 60)
        self.back_btn = pygame.Rect(40, 622, 150, 48)
        # دکمه‌های توقف / پایان
        self.btn_a = pygame.Rect(W // 2 - 220, 460, 200, 56)
        self.btn_b = pygame.Rect(W // 2 + 20, 460, 200, 56)

    # ------------------------------------------------------------ شروع بازی
    def start_game(self):
        self.level = Level(self.n, self.lvl, random.Random())
        self.trains, self.fading, self.particles, self.floats = [], [], [], []
        self.score = self.combo = self.best_combo = 0
        self.delivered = self.mistakes = 0
        self.elapsed = 0.0
        self.total = self.minutes * 60
        self.spawn_t = .5
        self.next_id = 0
        self.cd = 3.4
        self.last_cd = 4
        self.go_t = 0.0
        self.new_best = False
        self.labels = self.n >= 12
        self.run_key = self.make_key()
        self.state = "countdown"
        self.snd.start_bg()            # شروع موزیک و صدای قطار پس‌زمینه

    def make_key(self):
        """کلید ذخیره‌ی بهترین امتیاز (مرحله + تعداد + زمان + سرعت)."""
        return "L%d-%dx%d-S%d" % (self.lvl + 1, self.n, self.minutes, self.speed_idx + 1)

    def speed_mult(self):
        return SPEED_OPTIONS[self.speed_idx][1]

    def speed(self):
        """سرعت فعلی قطارها (پایه + شتاب تدریجی) × ضریب انتخابی بازیکن."""
        return (BASE_SPEED + min(self.elapsed, SPEED_RAMP_MAX_T) * SPEED_RAMP) * self.speed_mult()

    def sync_audio(self):
        """موزیک و صدای قطار فقط وقتی بازی در جریان است پخش شود."""
        self.snd.set_bg(self.state in ("play", "countdown"))

    # ------------------------------------------------------------ رویدادها
    def toggle(self, nd):
        nd.state ^= 1
        self.snd.play("click")

    def handle(self, ev):
        if ev.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if ev.type == pygame.KEYDOWN:
            self.handle_key(ev.key)
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            self.handle_click(ev.pos)

    def handle_key(self, k):
        if k == pygame.K_m:
            self.snd.on = not self.snd.on
        elif k == pygame.K_F11:
            pygame.display.toggle_fullscreen()
        elif k == pygame.K_l:
            self.labels = not self.labels
        elif k == pygame.K_ESCAPE:
            if self.state == "setup":
                self.state = "count"
            elif self.state in ("play", "countdown"):
                self.paused_from = self.state
                self.state = "pause"
            elif self.state == "pause":
                self.state = self.paused_from
            elif self.state == "over":
                self.state = "count"
        elif k in (pygame.K_p, pygame.K_SPACE):
            if self.state in ("play", "countdown"):
                self.paused_from = self.state
                self.state = "pause"
            elif self.state == "pause":
                self.state = self.paused_from
        elif k == pygame.K_RETURN:
            if self.state in ("over", "setup"):
                self.start_game()

    def handle_click(self, p):
        if self.state == "count":
            for n, r in self.count_btns:
                if r.collidepoint(p):
                    self.n = n
                    self.state = "setup"
                    self.snd.play("click")
        elif self.state == "setup":
            for i, r in enumerate(self.level_btns):
                if r.collidepoint(p):
                    self.lvl = i
                    self.snd.play("click")
            for m, r in self.time_btns:
                if r.collidepoint(p):
                    self.minutes = m
                    self.snd.play("click")
            for i, r in enumerate(self.speed_btns):
                if r.collidepoint(p):
                    self.speed_idx = i
                    self.snd.play("click")
            if self.back_btn.collidepoint(p):
                self.state = "count"
            elif self.start_btn.collidepoint(p):
                self.snd.play("click")
                self.start_game()
        elif self.state in ("play", "countdown"):
            if self.hover is not None:
                self.toggle(self.hover)
        elif self.state == "pause":
            if self.btn_a.collidepoint(p):
                self.state = self.paused_from
            elif self.btn_b.collidepoint(p):
                self.state = "count"
        elif self.state == "over":
            if self.btn_a.collidepoint(p):
                self.start_game()
            elif self.btn_b.collidepoint(p):
                self.state = "setup"

    # ------------------------------------------------------------ منطق بازی
    def burst(self, x, y, color, n=22):
        """انفجار ذرات رنگی هنگام تحویل درست."""
        for _ in range(n):
            a = random.random() * math.tau
            sp = random.uniform(60, 280)
            self.particles.append([x, y, math.cos(a) * sp, math.sin(a) * sp - 70,
                                   random.uniform(.4, .9), color])

    def try_spawn(self):
        lv = self.level
        e = random.choice(lv.entries)
        if any(t.edge is e and t.dist < GAP + 8 for t in self.trains):
            return False
        t = Train(self.next_id, random.randrange(self.n), e)
        self.next_id += 1
        self.trains.append(t)
        self.snd.play("enter")          # صدای ورود قطار
        return True

    def deliver(self, t, house):
        """قطار به خانه رسید: امتیاز مثبت اگر رنگ‌ها یکی باشد، وگرنه منفی."""
        self.trains.remove(t)
        t.edge.trains.remove(t)
        if t.c == house.color:
            pts = 100 + 20 * min(self.combo, 10)
            self.score += pts
            self.combo += 1
            self.best_combo = max(self.best_combo, self.combo)
            self.delivered += 1
            house.flash, house.flash_col = .5, (90, 255, 150)
            self.floats.append([house.x, house.y - 50, f"+{pts}", (120, 255, 160), 1.0])
            self.burst(house.x, house.y, COLORS[t.c])
            self.snd.play("correct")    # خانه‌ی درست
        else:
            self.score = max(0, self.score - 75)
            self.combo = 0
            self.mistakes += 1
            house.flash, house.flash_col = .6, (255, 70, 70)
            house.shake = .4
            self.shake = .3
            self.floats.append([house.x, house.y - 50, "-75", (255, 110, 110), 1.0])
            self.snd.play("wrong")      # خانه‌ی اشتباه
        self.fading.append([t.x, t.y, t.angle, t.c, .25])

    def update_trains(self, dt):
        lv = self.level
        sp = self.speed()
        for e in lv.edges:
            e.trains = []
        for t in self.trains:
            t.edge.trains.append(t)
        # حرکت روی ریل با رعایت فاصله‌ی GAP
        for e in lv.edges:
            if not e.trains:
                continue
            e.trains.sort(key=lambda t: -t.dist)
            ahead = None
            for t in e.trains:
                lim = e.length if ahead is None else min(e.length, ahead.dist - GAP)
                t.dist = max(t.dist, min(t.dist + sp * dt, lim))
                ahead = t
        # عبور از سر ریل به ریل بعدی (یا تحویل به خانه)
        movers = [t for t in self.trains
                  if t.dist >= t.edge.length - .01 and t.edge.trains and t.edge.trains[0] is t]
        movers.sort(key=lambda t: t.id)
        for t in movers:
            node = t.edge.dst
            if node.kind == "house":
                self.deliver(t, node)
                continue
            ne = node.outs[node.state] if node.kind == "switch" else node.outs[0]
            if not any(x.dist < GAP for x in ne.trains):
                t.edge.trains.remove(t)
                t.edge = ne
                t.dist = 0.0
                ne.trains.append(t)
        for t in self.trains:
            x, y, a = t.edge.pos(t.dist)
            t.x, t.y = x, y
            t.angle = angle_lerp(t.angle, a, min(1, dt * 14))

    def update(self, dt, mouse):
        self.menu_t += dt
        if self.state == "count":
            for n, r in self.count_btns:
                if r.collidepoint(mouse):
                    self.pre_n = n
            return
        if self.state in ("setup", "pause"):
            return
        lv = self.level
        # سوییچ نزدیک ماوس (برای کلیک)
        self.hover = None
        best = 30
        for nd in lv.switches:
            d = math.hypot(nd.x - mouse[0], nd.y - mouse[1])
            if d < best:
                best, self.hover = d, nd
        # افکت‌ها
        for nd in lv.houses:
            nd.flash = max(0, nd.flash - dt)
            nd.shake = max(0, nd.shake - dt)
        self.shake = max(0, self.shake - dt)
        for p in self.particles:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[3] += 320 * dt
            p[4] -= dt
        self.particles = [p for p in self.particles if p[4] > 0]
        for f in self.floats:
            f[1] -= 40 * dt
            f[4] -= dt
        self.floats = [f for f in self.floats if f[4] > 0]
        for f in self.fading:
            f[4] -= dt
        self.fading = [f for f in self.fading if f[4] > 0]
        self.go_t = max(0, self.go_t - dt)

        if self.state == "countdown":
            self.cd -= dt
            cur = math.ceil(self.cd - .4)
            if cur != self.last_cd and cur > 0:
                self.snd.play("beep")
            self.last_cd = cur
            if self.cd <= .4:
                self.state = "play"
                self.go_t = .7
                self.snd.play("go")
            return
        if self.state == "play":
            self.elapsed += dt
            self.spawn_t -= dt
            if self.spawn_t <= 0:
                if self.try_spawn():
                    # فاصله‌ی ورود قطارها: با سرعت بیشتر، قطار بیشتر وارد می‌شود
                    base = max(.8, 2.4 - self.elapsed * .012) / (self.speed_mult() ** .5)
                    self.spawn_t = base * random.uniform(.7, 1.3)
                else:
                    self.spawn_t = .05
            self.update_trains(dt)
            if self.elapsed >= self.total:
                self.elapsed = self.total
                self.state = "over"
                self.snd.play("over")
                k = self.run_key
                if self.score > self.scores.get(k, 0):
                    self.scores[k] = self.score
                    self.new_best = self.score > 0
                    save_scores(self.scores)

    # ------------------------------------------------------------ رسم: عمومی
    def button(self, rect, label, hover, selected=False, size=30, sub=None):
        col = (255, 200, 60) if selected else ((72, 100, 140) if hover else (44, 60, 84))
        pygame.draw.rect(self.frame, (10, 14, 20), rect.move(0, 4), border_radius=14)
        pygame.draw.rect(self.frame, col, rect, border_radius=14)
        pygame.draw.rect(self.frame, (190, 205, 225), rect, 2, border_radius=14)
        draw_text(self.frame, label, size, (255, 255, 255) if not selected else (30, 30, 30),
                  (rect.centerx, rect.centery - (10 if sub else 0)))
        if sub:
            draw_text(self.frame, sub, 18, (210, 220, 235), (rect.centerx, rect.centery + 24), shadow=False)

    def draw_preview(self, n, top, small=False):
        """پیش‌نمایش ردیف قطارها و خانه‌ها (با عکس‌های دلخواه)."""
        f = self.frame
        panel = pygame.Rect(80, top, W - 160, 200 if not small else 150)
        pygame.draw.rect(f, (18, 26, 36), panel, border_radius=18)
        pygame.draw.rect(f, (70, 90, 120), panel, 2, border_radius=18)
        avail = panel.w - 190
        sp = min(64, avail / n)
        x0 = panel.x + 150 + (avail - sp * n) / 2 + sp / 2
        y1 = panel.y + (52 if not small else 42)
        y2 = panel.y + (140 if not small else 108)
        draw_text(f, "TRAINS", 18, (200, 210, 225), (panel.x + 28, y1), "midleft")
        draw_text(f, "HOUSES", 18, (200, 210, 225), (panel.x + 28, y2), "midleft")
        pygame.draw.line(f, (80, 80, 90), (panel.x + 140, y1 + 22), (panel.right - 30, y1 + 22), 4)
        for i in range(n):
            ts = train_surface(i, min(.9, (sp - 4) / 40))
            f.blit(ts, ts.get_rect(center=(x0 + i * sp, y1)))
            hs = house_surface(i, int(max(18, min(46, sp - 6))))
            f.blit(hs, hs.get_rect(center=(x0 + i * sp, y2)))

    def draw_menu_bg(self):
        """بک‌گراند منوی اول + قطارهای متحرک."""
        f = self.frame
        f.blit(get_background(self.lvl), (0, 0))
        y = 150
        pygame.draw.line(f, (36, 38, 44), (0, y + 12), (W, y + 12), 8)
        for x in range(-10, W + 20, 16):
            pygame.draw.line(f, (100, 76, 54), (x, y + 2), (x, y + 22), 3)
        for i in range(10):
            x = ((self.menu_t * 90 + i * 130) % (W + 200)) - 100
            ts = train_surface(i % 20, 1.0)
            f.blit(ts, ts.get_rect(center=(x, y)))

    # ------------------------------------------------------------ رسم: منوها
    def draw_count(self, mouse):
        f = self.frame
        self.draw_menu_bg()
        draw_text(f, "TRAIN OF THOUGHT", 60, (255, 214, 90), (W // 2, 70))
        draw_text(f, "How many trains & houses?", 30, (230, 240, 250), (W // 2, 195))
        for n, r in self.count_btns:
            self.button(r, str(n), r.collidepoint(mouse), selected=(n == self.pre_n), size=32)
        self.draw_preview(self.pre_n, 480)
        draw_text(f, "Click a number to continue", 18, (170, 185, 205), (W // 2, H - 14), shadow=False)

    def draw_setup(self, mouse):
        """صفحه‌ی تنظیمات: مرحله، زمان و سرعت."""
        f = self.frame
        f.blit(get_background(self.lvl), (0, 0))
        dim = pygame.Surface((W, H), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 120))
        f.blit(dim, (0, 0))
        draw_text(f, "TRAIN OF THOUGHT", 44, (255, 214, 90), (W // 2, 38))
        draw_text(f, f"{self.n} trains & {self.n} houses", 22, (160, 220, 255), (W // 2, 80))
        # مرحله
        draw_text(f, "LEVEL", 20, (230, 240, 250), (W // 2, 108))
        for i, r in enumerate(self.level_btns):
            self.button(r, str(i + 1), r.collidepoint(mouse), selected=(i == self.lvl), size=28)
        draw_text(f, LEVELS[self.lvl]["name"] + "  -  " + THEMES[self.lvl]["name"], 24,
                  (255, 255, 255), (W // 2, 198))
        # زمان
        draw_text(f, "GAME TIME (minutes)", 20, (230, 240, 250), (W // 2, 236))
        for m, r in self.time_btns:
            self.button(r, f"{m} min", r.collidepoint(mouse), selected=(m == self.minutes), size=24)
        # سرعت
        draw_text(f, "TRAIN SPEED", 20, (230, 240, 250), (W // 2, 336))
        for i, r in enumerate(self.speed_btns):
            self.button(r, SPEED_OPTIONS[i][0], r.collidepoint(mouse),
                        selected=(i == self.speed_idx), size=24)
        self.draw_preview(self.n, 424, small=True)
        self.button(self.back_btn, "<  Back", self.back_btn.collidepoint(mouse), size=24)
        self.button(self.start_btn, "START", self.start_btn.collidepoint(mouse), size=32)
        b = self.scores.get(self.make_key())
        draw_text(f, f"Best: {b}" if b else "No score yet", 22, (255, 220, 120),
                  (W - 40, 646), "midright", shadow=False)

    # ------------------------------------------------------------ رسم: بازی
    def draw_train(self, x, y, ang, c, scale=1.0):
        s = train_surface(c)
        rot = pygame.transform.rotozoom(s, -math.degrees(ang), scale)
        self.frame.blit(rot, rot.get_rect(center=(x, y)))

    def draw_game(self):
        f = self.frame
        lv = self.level
        f.blit(lv.track, (0, 0))

        # ریل‌ها (هایلایت مسیر فعال هر سوییچ)
        for e in lv.edges:
            if e.src is not None and e.src.kind == "switch" and e.src.outs[e.src.state] is not e:
                poly(f, (82, 86, 94), e.pts, 4)
        for e in lv.edges:
            if e.src is not None and e.src.kind == "switch":
                if e.src.outs[e.src.state] is e:
                    poly(f, (232, 208, 140), e.pts, 4)
            else:
                poly(f, (205, 210, 218), e.pts, 4)

        # قطارها
        for t in self.trains:
            self.draw_train(t.x, t.y, t.angle, t.c)
            if self.labels:
                draw_text(f, t.c + 1, 13, (255, 255, 255), (t.x, t.y))

        # خانه‌ها (روی قطار کشیده می‌شوند تا قطار وارد خانه شود)
        size = lv.house_size
        for h in lv.houses:
            hs = house_surface(h.color, size)
            ox = math.sin(self.menu_t * 60) * 4 * (h.shake / .4) if h.shake > 0 else 0
            r = hs.get_rect(center=(h.x + ox, h.y))
            if h.flash > 0:
                g = pygame.Surface((120, 120), pygame.SRCALPHA)
                pygame.draw.circle(g, (*h.flash_col, int(170 * min(1, h.flash / .5))), (60, 60), 52)
                f.blit(g, g.get_rect(center=r.center))
            f.blit(hs, r)
            if self.labels:
                draw_text(f, h.color + 1, max(12, size // 2), (255, 255, 255),
                          (r.centerx, r.centery + size // 6))
        for fd in self.fading:
            self.draw_train(fd[0], fd[1], fd[2], fd[3], max(.05, fd[4] / .25))

        # سوییچ‌ها (دسته‌ی کوچک جهت مسیر فعال را نشان می‌دهد)
        for nd in lv.switches:
            hov = nd is self.hover
            rad = 13 + (3 if hov else 0)
            pygame.draw.circle(f, (20, 22, 28), (int(nd.x), int(nd.y)), rad + 3)
            pygame.draw.circle(f, (255, 240, 150) if hov else (255, 205, 70),
                               (int(nd.x), int(nd.y)), rad, 3)
            e = nd.outs[nd.state]
            dx, dy = e.pts[1][0] - nd.x, e.pts[1][1] - nd.y
            L = math.hypot(dx, dy) or 1
            pygame.draw.line(f, (255, 205, 70), (nd.x, nd.y),
                             (nd.x + dx / L * 11, nd.y + dy / L * 11), 4)
            pygame.draw.circle(f, (255, 205, 70), (int(nd.x), int(nd.y)), 4)
        pygame.draw.circle(f, (60, 62, 70), (int(lv.funnel.x), int(lv.funnel.y)), 8)

        # تونل‌های ورودی
        for e in lv.entries:
            x = e.pts[0][0]
            pygame.draw.rect(f, (26, 26, 32), (x - 28, 54, 56, 40), border_radius=14)
            pygame.draw.rect(f, (130, 118, 105), (x - 28, 54, 56, 40), 3, border_radius=14)
            pygame.draw.rect(f, (8, 8, 10), (x - 18, 60, 36, 34), border_top_left_radius=16,
                             border_top_right_radius=16)

        # ذرات و امتیازهای شناور
        for p in self.particles:
            pygame.draw.circle(f, p[5], (int(p[0]), int(p[1])), max(1, int(4 * p[4] / .9) + 1))
        for fl in self.floats:
            draw_text(f, fl[2], 30, fl[3], (fl[0], fl[1]))

        # نوار بالا (HUD)
        pygame.draw.rect(f, (14, 19, 27), (0, 0, W, HUD_H))
        left = max(0, self.total - self.elapsed)
        frac = left / self.total
        pygame.draw.rect(f, (40, 50, 66), (0, HUD_H - 5, W, 5))
        pygame.draw.rect(f, (255, 90, 80) if left < 10 else (90, 200, 255), (0, HUD_H - 5, int(W * frac), 5))
        draw_text(f, f"SCORE  {self.score}", 30, (255, 255, 255), (24, 30), "midleft")
        mm, ss = int(left) // 60, int(left) % 60
        tc = (255, 110, 100) if left < 10 and int(self.menu_t * 4) % 2 == 0 else (255, 255, 255)
        draw_text(f, f"{mm}:{ss:02d}", 38, tc, (W // 2, 30))
        draw_text(f, f"COMBO x{self.combo}", 24, (255, 214, 90), (W - 24, 22), "midright")
        draw_text(f, f"Delivered {self.delivered}  |  Mistakes {self.mistakes}", 16,
                  (180, 195, 215), (W - 24, 46), "midright", shadow=False)
        draw_text(f, f"Level {self.lvl + 1}  |  Speed: {SPEED_OPTIONS[self.speed_idx][0]}"
                     "     L: numbers   M: sound   P: pause", 14, (190, 205, 225),
                  (W // 2, H - 10), shadow=False)

    def overlay(self, title, color):
        f = self.frame
        dim = pygame.Surface((W, H), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 175))
        f.blit(dim, (0, 0))
        panel = pygame.Rect(W // 2 - 280, 150, 560, 400)
        pygame.draw.rect(f, (20, 28, 40), panel, border_radius=22)
        pygame.draw.rect(f, (110, 135, 175), panel, 3, border_radius=22)
        draw_text(f, title, 54, color, (W // 2, 205))

    def draw(self, mouse):
        f = self.frame
        if self.state == "count":
            self.draw_count(mouse)
        elif self.state == "setup":
            self.draw_setup(mouse)
        else:
            self.draw_game()
            if self.state == "countdown":
                n = math.ceil(self.cd - .4)
                if n > 0:
                    sc = 1 + (self.cd - .4) % 1 * .6
                    draw_text(f, str(n), int(150 * sc), (255, 255, 255), (W // 2, H // 2))
            if self.go_t > 0:
                draw_text(f, "GO!", 140, (120, 255, 150), (W // 2, H // 2))
            if self.state == "pause":
                self.overlay("PAUSED", (255, 255, 255))
                self.button(self.btn_a, "Resume", self.btn_a.collidepoint(mouse), size=26)
                self.button(self.btn_b, "Quit to menu", self.btn_b.collidepoint(mouse), size=26)
            elif self.state == "over":
                self.overlay("TIME'S UP!", (255, 214, 90))
                draw_text(f, f"Score: {self.score}", 44, (255, 255, 255), (W // 2, 285))
                if self.new_best:
                    draw_text(f, "NEW BEST!", 26, (120, 255, 150), (W // 2, 328))
                else:
                    draw_text(f, f"Best: {self.scores.get(self.run_key, 0)}", 24,
                              (255, 220, 120), (W // 2, 328))
                tot = self.delivered + self.mistakes
                acc = int(100 * self.delivered / tot) if tot else 0
                draw_text(f, f"Delivered {self.delivered}   Mistakes {self.mistakes}   Accuracy {acc}%",
                          22, (210, 225, 245), (W // 2, 378), shadow=False)
                draw_text(f, f"Best combo x{self.best_combo}   |   Level {self.lvl + 1}, "
                             f"{self.n} trains, {self.minutes} min, {SPEED_OPTIONS[self.speed_idx][0]}",
                          18, (170, 190, 215), (W // 2, 415), shadow=False)
                self.button(self.btn_a, "Play again", self.btn_a.collidepoint(mouse), size=26)
                self.button(self.btn_b, "Settings", self.btn_b.collidepoint(mouse), size=26)

    # ------------------------------------------------------------ حلقه‌ی اصلی
    def run(self):
        while True:
            dt = min(self.clock.tick(FPS) / 1000, .05)
            mouse = pygame.mouse.get_pos()
            for ev in pygame.event.get():
                self.handle(ev)
            self.update(dt, mouse)
            self.sync_audio()
            self.draw(mouse)
            ox = oy = 0
            if self.state in ("play", "countdown") and self.shake > 0:
                ox = random.randint(-6, 6)
                oy = random.randint(-6, 6)
            screen.fill((0, 0, 0))
            screen.blit(self.frame, (ox, oy))
            pygame.display.flip()


if __name__ == "__main__":
    ensure_asset_dirs()
    Game().run()
