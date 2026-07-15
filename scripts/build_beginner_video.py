"""Build full-feature ARL how-to video: slides + voiceover covering every module."""

from __future__ import annotations

import asyncio
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "samples" / "video-demo"
SLIDES = OUT / "slides"
AUDIO = OUT / "audio"
FFMPEG = ROOT / "tools" / "ffmpeg" / "ffmpeg.exe"
VIDEO_OUT = OUT / "ARL_Beginner_How_To_Use.mp4"

# SafeWatch-inspired desk palette
NAVY = "#0c2340"
NAVY_DEEP = "#071525"
BRAND = "#0a6e8a"
STEEL = "#e8edf3"
MUTED = "#8aa0b5"
WHITE = "#ffffff"
FOOTER = "#143a5c"


def ffmpeg_bin() -> str:
    if FFMPEG.exists():
        return str(FFMPEG)
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


SCENES = [
    {
        "file": "01_welcome",
        "title": "Welcome — Full Platform Tour",
        "bullets": [
            "Adverse Risk Lookup (ARL)",
            "Screen news → map risk → act",
            "We will use every main module",
            "Follow along in the live demo app",
        ],
        "narration": (
            "Welcome to Adverse Risk Lookup, or ARL. "
            "This is a full platform tour. "
            "You will see how each module works: detection dashboard, adverse media queue, "
            "investigation search, risk register, emerging risks, watchlist sources, "
            "alert rules, audit reports, case assistant, and administration. "
            "Open the demo app and follow each step as we go."
        ),
    },
    {
        "file": "02_signin",
        "title": "1 — Sign In",
        "bullets": [
            "Open arl-adverse-risk-lookup.netlify.app",
            "Email: admin@arl.local",
            "Password: ChangeMe123!",
            "Click Sign in to ARL",
        ],
        "narration": (
            "Step one: sign in. "
            "Open the website in your browser. "
            "Enter the demo email admin at ARL.local, "
            "and the password Change Me one two three, with an exclamation mark. "
            "Then click Sign in to ARL. "
            "You land in the screening console with a navy left menu."
        ),
    },
    {
        "file": "03_dashboard",
        "title": "2 — Detection Dashboard",
        "bullets": [
            "KPI tiles: news, critical, emerging",
            "Country and category charts",
            "Queue snapshot of recent hits",
            "Your daily compliance overview",
        ],
        "narration": (
            "Step two: Detection Dashboard. "
            "This is your daily overview. "
            "Read the KPI tiles for today's news, critical alerts, and emerging risks. "
            "Use the charts to see which countries and risk categories are active. "
            "The queue snapshot lists recent detections so you know what to open first."
        ),
    },
    {
        "file": "04_queue",
        "title": "3 — Adverse Media Queue",
        "bullets": [
            "Open Adverse Media Queue",
            "Filter by severity if needed",
            "Toggle English or original language",
            "Click a row to open the case",
        ],
        "narration": (
            "Step three: Adverse Media Queue. "
            "This is your working list of screened stories. "
            "Filter by severity, for example high or critical. "
            "Use the language toggle to view English or the original title. "
            "Click any row to open the full detection record."
        ),
    },
    {
        "file": "05_detail",
        "title": "4 — Detection Detail",
        "bullets": [
            "Executive and detailed summaries",
            "Severity score and confidence",
            "Recommended actions",
            "Explainable risk matches",
        ],
        "narration": (
            "Step four: read the detection detail. "
            "Check severity, score, and confidence. "
            "Read the executive summary, then the detailed summary. "
            "Review banks, regulators, departments, and tags. "
            "Under recommended actions, note immediate, short term, and long term next steps. "
            "Scroll to explainable risk matches to see similarity, confidence, and why a register risk was linked."
        ),
    },
    {
        "file": "06_search",
        "title": "5 — Investigation Search",
        "bullets": [
            "Open Investigation Search",
            "Keyword: bank, fraud, ransomware…",
            "Filter country and severity",
            "Open a result from the hit list",
        ],
        "narration": (
            "Step five: Investigation Search. "
            "Use this when you are hunting a theme, not browsing the full queue. "
            "Type a keyword such as ransomware, Pakistan, or A M L. "
            "Optionally set country and severity, then click Search. "
            "Open any result to continue the same case review flow."
        ),
    },
    {
        "file": "07_risks",
        "title": "6 — Risk Register Upload",
        "bullets": [
            "Open Risk Register",
            "File: VIDEO_DEMO_Risk_Register.csv",
            "Preview & Map Columns",
            "Import Risks — then review the table",
        ],
        "narration": (
            "Step six: Risk Register. "
            "This is how ARL learns your bank's risks for semantic matching. "
            "Choose the sample file VIDEO DEMO Risk Register C S V from the video demo pack. "
            "Click Preview and Map Columns. "
            "Confirm mappings for Risk I D, Risk Name, Description, Category, Owner, and Status. "
            "Then click Import Risks. "
            "The table below shows imported risks ready for matching against adverse media."
        ),
    },
    {
        "file": "08_emerging",
        "title": "7 — Emerging Risks",
        "bullets": [
            "Open Emerging Risks",
            "Themes not yet on the register",
            "Suggested category and owner",
            "Use confidence to prioritise",
        ],
        "narration": (
            "Step seven: Emerging Risks. "
            "Here ARL surfaces themes seen in media that may need a new register entry. "
            "Each card shows a suggested category, confidence, description, reasoning, "
            "and a suggested owner. "
            "Use this to discuss gaps with operational risk before they become formal KRIs."
        ),
    },
    {
        "file": "09_feeds",
        "title": "8 — Watchlist Sources",
        "bullets": [
            "Open Watchlist Sources",
            "Add an RSS feed name and URL",
            "Fetch now for a single source",
            "Or Collect from NewsAPI",
        ],
        "narration": (
            "Step eight: Watchlist Sources. "
            "This controls continuous intake. "
            "Add an R S S feed with a name and feed URL, then click Add R S S Feed. "
            "Use Fetch now to pull one source immediately. "
            "Or click Collect from News A P I to run broader news collection. "
            "Check status, success, and failure counts on each source row."
        ),
    },
    {
        "file": "10_alerts",
        "title": "9 — Alert Rules",
        "bullets": [
            "Open Alert Rules",
            "Name the subscription",
            "Severity ≥ high (or critical)",
            "Optional country — then Subscribe",
        ],
        "narration": (
            "Step nine: Alert Rules. "
            "Create a subscription so important hits are not missed. "
            "Give it a clear name, choose severity greater than or equal to high, "
            "optionally add a country, then click Subscribe. "
            "Subscriptions appear on the left. "
            "The inbox on the right shows notifications that matched your rules."
        ),
    },
    {
        "file": "11_reports",
        "title": "10 — Audit Reports",
        "bullets": [
            "Open Audit Reports",
            "Download PDF management report",
            "Download Excel for audit packs",
            "Download Word for board briefs",
        ],
        "narration": (
            "Step ten: Audit Reports. "
            "Export evidence for committees and boards. "
            "Download the P D F management report for executive summary and critical incidents. "
            "Use Excel for tabular audit packs. "
            "Use Word for a narrative management briefing. "
            "Keep these in your governance evidence folder."
        ),
    },
    {
        "file": "12_assistant",
        "title": "11 — Case Assistant",
        "bullets": [
            "Open Case Assistant",
            "Try a suggested prompt",
            "Or type your own question",
            "Example: Show today's cyber risks",
        ],
        "narration": (
            "Step eleven: Case Assistant. "
            "Ask natural language questions grounded in ARL context. "
            "Click a suggested prompt, or type your own. "
            "Try: Show today's cyber risks. "
            "Or: Summarize A M L news. "
            "Or: Generate executive summary. "
            "Click Run query and read the response panel."
        ),
    },
    {
        "file": "13_admin",
        "title": "12 — Administration",
        "bullets": [
            "Open Administration",
            "Review users and roles",
            "Check job logs",
            "Inspect RBAC role definitions",
        ],
        "narration": (
            "Step twelve: Administration. "
            "Admins review users, emails, and assigned roles. "
            "Job logs show scheduler activity and duration. "
            "The R B A C section lists role definitions so access stays auditable. "
            "Use this screen for control checks, not day-to-day case work."
        ),
    },
    {
        "file": "14_practice",
        "title": "Practice Checklist",
        "bullets": [
            "Login → Dashboard → Queue → Detail",
            "Search → Upload CSV → Emerging",
            "Sources → Alerts → Reports",
            "Assistant → Admin",
        ],
        "narration": (
            "Practice checklist. "
            "Sign in, then walk Detection Dashboard, Adverse Media Queue, and a detection detail. "
            "Run Investigation Search, upload the sample risk register C S V, then open Emerging Risks. "
            "Add or fetch a watchlist source, create an alert rule, download one report, "
            "ask the case assistant a question, and glance at Administration. "
            "That is how the full platform works end to end."
        ),
    },
    {
        "file": "15_thanks",
        "title": "Finish",
        "bullets": [
            "Live app: arl-adverse-risk-lookup.netlify.app",
            "Samples: samples/video-demo",
            "CSV + XLSX upload files included",
            "Thank you for watching ARL",
        ],
        "narration": (
            "You are done. "
            "The live demo is at ARL adverse risk lookup on Netlify. "
            "Sample upload files and this script live in the samples video demo folder. "
            "Thank you for watching Adverse Risk Lookup."
        ),
    },
]


def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for name in (
        r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\calibri.ttf",
    ):
        p = Path(name)
        if p.exists():
            return ImageFont.truetype(str(p), size=size)
    return ImageFont.load_default()


def make_slide(scene: dict, idx: int, total: int) -> Path:
    SLIDES.mkdir(parents=True, exist_ok=True)
    w, h = 1280, 720
    img = Image.new("RGB", (w, h), NAVY)
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, 6, h], fill=BRAND)
    draw.rectangle([0, 0, w, 4], fill=BRAND)
    draw.rectangle([0, h - 52, w, h], fill=NAVY_DEEP)

    title_f = font(42)
    body_f = font(28)
    small_f = font(18)
    brand_f = font(16)

    draw.text((56, 36), "ADVERSE RISK LOOKUP", fill=BRAND, font=brand_f)
    draw.text((56, 62), "Screening · GRC tutorial", fill=MUTED, font=small_f)
    draw.text((56, 110), scene["title"], fill=WHITE, font=title_f)

    y = 190
    for bullet in scene["bullets"]:
        draw.rectangle([56, y + 10, 64, y + 28], fill=BRAND)
        draw.text((80, y), bullet, fill=STEEL, font=body_f)
        y += 54

    draw.text((56, h - 34), f"Full platform tour  ·  {idx}/{total}", fill=MUTED, font=small_f)
    draw.text((920, h - 34), "Follow in the live app", fill=MUTED, font=small_f)

    path = SLIDES / f"{scene['file']}.png"
    img.save(path)
    return path


async def synthesize(scene: dict) -> Path:
    AUDIO.mkdir(parents=True, exist_ok=True)
    out = AUDIO / f"{scene['file']}.mp3"
    import edge_tts

    communicate = edge_tts.Communicate(scene["narration"], voice="en-US-JennyNeural")
    await communicate.save(str(out))
    return out


def concat_video(pairs: list[tuple[Path, Path]]) -> None:
    ffmpeg = ffmpeg_bin()
    list_file = OUT / "concat.txt"
    parts: list[Path] = []

    for i, (slide, audio) in enumerate(pairs):
        part = OUT / f"part_{i:02d}.mp4"
        cmd = [
            ffmpeg,
            "-y",
            "-loop",
            "1",
            "-i",
            str(slide),
            "-i",
            str(audio),
            "-c:v",
            "libx264",
            "-tune",
            "stillimage",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-pix_fmt",
            "yuv420p",
            "-shortest",
            "-vf",
            "scale=1280:720",
            str(part),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(result.stderr[-2000:] or result.stdout[-2000:])
        parts.append(part)

    lines = []
    for p in parts:
        lines.append("file '" + p.name.replace("\\", "/") + "'")
    list_file.write_text("\n".join(lines), encoding="utf-8")
    cmd = [
        ffmpeg,
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(list_file.name),
        "-c",
        "copy",
        str(VIDEO_OUT.name),
    ]
    result = subprocess.run(cmd, cwd=str(OUT), capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-2000:] or result.stdout[-2000:])
    print(f"Wrote {VIDEO_OUT}")


async def main() -> None:
    # Clean old numbered parts so concat doesn't pick stale scenes
    for old in OUT.glob("part_*.mp4"):
        old.unlink(missing_ok=True)
    pairs: list[tuple[Path, Path]] = []
    total = len(SCENES)
    for i, scene in enumerate(SCENES, start=1):
        print(f"Scene {i}/{total}: {scene['title']}")
        slide = make_slide(scene, i, total)
        audio = await synthesize(scene)
        pairs.append((slide, audio))
    concat_video(pairs)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        print("ERROR:", exc, file=sys.stderr)
        raise
