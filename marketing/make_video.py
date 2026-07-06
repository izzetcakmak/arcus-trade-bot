"""ArcusBot tanitim videosu uretici.

Ekran goruntuleri + ok/vurgu kaplamalari (PIL) + seslendirme (edge-tts)
+ Ken Burns zoom (ffmpeg zoompan) -> 1080p MP4.
Calistirma: python marketing/make_video.py
"""
import asyncio
import json
import os
import subprocess

import edge_tts
from PIL import Image, ImageDraw, ImageFont

DIR = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.join(DIR, "shots")
AUDIO = os.path.join(DIR, "audio")
WORK = os.path.join(DIR, "work")
os.makedirs(WORK, exist_ok=True)

VOICE = "en-US-AndrewNeural"
GREEN, BLUE, RED = (48, 209, 88), (41, 151, 255), (255, 69, 58)

# ---- sahneler: (goruntu, anlatim, [oklar], [vurgu daireleri]) ----
SCENES = [
    ("01_hero.png",
     "What if a bot traded perpetuals for you — crypto AND stocks — "
     "twenty four seven, with your rules instead of your emotions?",
     [], []),
    ("02_features.png",
     "Meet ArcusBot — an automated trading platform built on Arcus, "
     "the new exchange from dYdX Labs on Robinhood Chain. "
     "Everything is set up in about a minute.",
     [], []),
    ("05_dashboard.png",
     "Sign in with Google, and a dedicated trading wallet is created and "
     "registered for you automatically. Its keys are shown to you exactly "
     "once — then stored encrypted.",
     [((1050, 120), (760, 175))],
     [((580, 165), (900, 205))]),
    ("05_dashboard.png",
     "One click funds the account with ten thousand dollars of testnet "
     "collateral. No faucets, no bridges, no gas hunting.",
     [((900, 330), (680, 265))],
     [((575, 215), (760, 275))]),
    ("06_risk.png",
     "Then pick your risk: Low, Balanced, or High — or fine tune leverage, "
     "stop loss and take profit yourself. Changes hot-apply to the running "
     "bot in about thirty seconds.",
     [((1217, 620), (1217, 545))],
     [((575, 455), (1345, 540))]),
    ("06_risk.png",
     "Trade any of forty one markets: Bitcoin and Ethereum, stocks like "
     "Apple and Nvidia, commodities and indices — each category one tap away.",
     [((1080, 700), (950, 762))],
     [((575, 745), (985, 793)), ((765, 800), (812, 843)),
      ((1263, 800), (1310, 843)), ((1005, 882), (1058, 925))]),
    ("08_bot.png",
     "Hit start. A multi-signal strategy scans fifteen minute candles, "
     "opens positions with automatic stop loss and take profit, and reports "
     "every move straight to your Telegram.",
     [((900, 320), (668, 392)), ((950, 890), (700, 815))],
     [((580, 555), (1340, 660))]),
    ("01_hero.png",
     "It is free, it runs on testnet money, and it is open source. "
     "Try it now at A trade bot dot X Y Z — link in the description.",
     [], [], "atradebot.xyz"),
]


def _font(size, bold=True):
    for name in (("segoeuib.ttf" if bold else "segoeui.ttf"), "arialbd.ttf",
                 "arial.ttf"):
        try:
            return ImageFont.truetype(f"C:/Windows/Fonts/{name}", size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_arrow(d: ImageDraw.ImageDraw, start, end, color=RED, w=9):
    d.line([start, end], fill=color, width=w)
    # ok basi
    import math
    ang = math.atan2(end[1] - start[1], end[0] - start[0])
    L = 30
    for da in (math.radians(150), math.radians(-150)):
        d.line([end, (end[0] + L * math.cos(ang + da),
                      end[1] + L * math.sin(ang + da))], fill=color, width=w)


def badge(img: Image.Image):
    """Sag alt kose sunucu rozeti: logo + marka."""
    d = ImageDraw.Draw(img, "RGBA")
    x0, y0, x1, y1 = 1560, 975, 1885, 1050
    d.rounded_rectangle([x0, y0, x1, y1], radius=18,
                        fill=(20, 22, 26, 215), outline=(255, 255, 255, 45),
                        width=2)
    # altigen logo
    import math
    cx, cy, r = x0 + 40, (y0 + y1) // 2, 22
    pts = [(cx + r * math.cos(math.radians(60 * i - 90)),
            cy + r * math.sin(math.radians(60 * i - 90))) for i in range(6)]
    d.polygon(pts, outline=BLUE, width=4)
    d.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], fill=GREEN)
    d.text((x0 + 78, y0 + 14), "ArcusBot", font=_font(26), fill=(245, 245, 247))
    d.text((x0 + 78, y0 + 44), "atradebot.xyz", font=_font(18, bold=False),
           fill=(134, 134, 139))


def compose(idx, scene):
    shot, _, arrows, circles = scene[0], scene[1], scene[2], scene[3]
    url_overlay = scene[4] if len(scene) > 4 else None
    img = Image.open(os.path.join(SHOTS, shot)).convert("RGB")
    d = ImageDraw.Draw(img, "RGBA")
    for (x0, y0), (x1, y1) in circles:
        d.rounded_rectangle([x0, y0, x1, y1], radius=16, outline=GREEN, width=6)
    for start, end in arrows:
        draw_arrow(d, start, end)
    if url_overlay:
        f = _font(72)
        tw = d.textlength(url_overlay, font=f)
        bx0, by0 = (1920 - tw) / 2 - 40, 700
        d.rounded_rectangle([bx0, by0, bx0 + tw + 80, by0 + 110], radius=26,
                            fill=(0, 113, 227, 235))
        d.text(((1920 - tw) / 2, by0 + 18), url_overlay, font=f,
               fill=(255, 255, 255))
    badge(img)
    out = os.path.join(WORK, f"frame_{idx:02d}.png")
    img.save(out)
    return out


async def tts(idx, text):
    out = os.path.join(AUDIO, f"voice_{idx:02d}.mp3")
    await edge_tts.Communicate(text, VOICE, rate="+4%").save(out)
    return out


def dur_of(path):
    out = subprocess.run(["ffprobe", "-v", "quiet", "-print_format", "json",
                          "-show_format", path], capture_output=True, text=True)
    return float(json.loads(out.stdout)["format"]["duration"])


def make_segment(idx, frame, voice, dur):
    seg = os.path.join(WORK, f"seg_{idx:02d}.mp4")
    total = dur + 0.7
    frames = int(total * 30)
    vf = (f"scale=2400:1350,zoompan=z='min(1.0+0.00045*on,1.10)':"
          f"x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':d={frames}:s=1920x1080:fps=30,"
          f"format=yuv420p")
    subprocess.run(["ffmpeg", "-y", "-loop", "1", "-i", frame, "-i", voice,
                    "-vf", vf, "-t", f"{total:.2f}", "-c:v", "libx264",
                    "-preset", "medium", "-crf", "19", "-c:a", "aac",
                    "-b:a", "192k", "-shortest", seg],
                   capture_output=True)
    return seg


async def main():
    segs = []
    for i, scene in enumerate(SCENES):
        frame = compose(i, scene)
        voice = await tts(i, scene[1])
        dur = dur_of(voice)
        segs.append(make_segment(i, frame, voice, dur))
        print(f"sahne {i+1}/{len(SCENES)} hazir ({dur:.1f}s)")

    lst = os.path.join(WORK, "list.txt")
    with open(lst, "w") as f:
        for s in segs:
            f.write(f"file '{s}'\n")
    final = os.path.join(DIR, "arcusbot_intro_en.mp4")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                    "-c", "copy", os.path.join(WORK, "raw.mp4")],
                   capture_output=True)
    # bas/son fade
    total = dur_of(os.path.join(WORK, "raw.mp4"))
    subprocess.run(["ffmpeg", "-y", "-i", os.path.join(WORK, "raw.mp4"),
                    "-vf", f"fade=t=in:d=0.8,fade=t=out:st={total-1:.2f}:d=1",
                    "-af", f"afade=t=in:d=0.6,afade=t=out:st={total-1:.2f}:d=1",
                    "-c:v", "libx264", "-crf", "19", "-c:a", "aac", final],
                   capture_output=True)
    print("VIDEO:", final, f"({dur_of(final):.1f} sn)")

asyncio.run(main())
