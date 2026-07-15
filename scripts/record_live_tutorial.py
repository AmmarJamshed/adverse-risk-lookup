"""
Record a live UI tutorial of the ARL regulatory-obligations workflow on Netlify.
Horizon scan → Applicability → Obligations → Gap cases → Library → Sources → Admin.
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "samples" / "video-demo"
RAW_DIR = OUT / "recording"
CHAPTERS_DIR = OUT / "chapters"
AUDIO_DIR = OUT / "audio_live"
FFMPEG = ROOT / "tools" / "ffmpeg" / "ffmpeg.exe"
VIDEO_OUT = OUT / "ARL_Beginner_How_To_Use.mp4"
BASE = "https://arl-adverse-risk-lookup.netlify.app"

CHAPTERS = [
    {
        "id": "01_signin",
        "title": "Sign in",
        "narration": (
            "Welcome to Adverse Risk Lookup. "
            "This tutorial shows the regulatory obligations workflow: "
            "horizon scanning, applicability, the obligations register, and gap analysis cases. "
            "Sign in with the demo email and password, then continue to the console."
        ),
    },
    {
        "id": "02_horizon",
        "title": "Horizon Scan",
        "narration": (
            "Horizon Scan is your regulatory change desk for the U K, U S A, E U, and Pakistan. "
            "KPI tiles show pending assessments, obligations, and open gap cases. "
            "Filter by jurisdiction, then open an instrument to review extracted candidates."
        ),
    },
    {
        "id": "03_detail",
        "title": "Assess a candidate",
        "narration": (
            "Open a horizon item to read the instrument summary and extracted obligation candidates. "
            "Mark a requirement Applicable to automatically create a register entry and open a gap analysis case. "
            "You can also mark Not applicable or leave it Under review."
        ),
    },
    {
        "id": "04_applicability",
        "title": "Applicability inbox",
        "narration": (
            "The Applicability inbox lists candidates waiting for a decision. "
            "Filter to Under review, then apply Applicable to push items into the obligations register and case queue."
        ),
    },
    {
        "id": "05_obligations",
        "title": "Obligations Register",
        "narration": (
            "The Obligations Register holds structured requirements created from applicable candidates. "
            "Each row shows code, statement, jurisdiction, owner, due date, and a link to its gap case."
        ),
    },
    {
        "id": "06_cases",
        "title": "Gap Analysis Cases",
        "narration": (
            "Gap Analysis Cases are opened automatically for each applicable obligation. "
            "Filter by gap status such as mapped, partial, or gap, then open a case to map policies and controls."
        ),
    },
    {
        "id": "07_case_map",
        "title": "Map policies and controls",
        "narration": (
            "Inside a case, review the obligation statement, then map policies and controls from your library. "
            "Set coverage to mapped, partial, or gap, and add notes for remediation."
        ),
    },
    {
        "id": "08_library",
        "title": "Policies and Controls",
        "narration": (
            "The Policies and Controls library is your inventory for mapping. "
            "Use it when building coverage against each regulatory requirement."
        ),
    },
    {
        "id": "09_sources",
        "title": "Regulatory Sources",
        "narration": (
            "Regulatory Sources are watchlists that feed the horizon scan — "
            "for example F C A, Fin C E N, E B A, S B P, and the Federal Reserve."
        ),
    },
    {
        "id": "10_admin",
        "title": "Administration",
        "narration": (
            "Administration covers users, roles, and job visibility. "
            "That completes the obligations workflow. Practice on the live demo: "
            "scan, assess, register, then close the control gap."
        ),
    },
]


def ffmpeg_bin() -> str:
    if FFMPEG.exists():
        return str(FFMPEG)
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def marker(markers: list[dict], chapter_id: str) -> None:
    markers.append({"id": chapter_id, "t": time.perf_counter()})
    print(f"  [mark] {chapter_id}", flush=True)


async def wait(page, ms: int = 2000) -> None:
    await page.wait_for_timeout(ms)


async def click_nav(page, *labels: str) -> None:
    for label in labels:
        link = page.get_by_role("link", name=label, exact=True)
        if await link.count():
            await link.first.click()
            await wait(page, 2200)
            return
        link = page.get_by_role("link", name=label, exact=False)
        if await link.count():
            await link.first.click()
            await wait(page, 2200)
            return
    raise RuntimeError(f"Nav link not found for any of: {labels}")


async def record_walkthrough() -> tuple[Path, list[dict]]:
    from playwright.async_api import async_playwright

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for old in RAW_DIR.glob("*"):
        if old.is_file():
            old.unlink()

    markers: list[dict] = []
    t0 = time.perf_counter()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            record_video_dir=str(RAW_DIR),
            record_video_size={"width": 1440, "height": 900},
            locale="en-US",
        )
        page = await context.new_page()

        # --- Sign in ---
        marker(markers, "01_signin")
        await page.goto(BASE + "/login", wait_until="networkidle")
        await wait(page, 3000)
        email = page.get_by_label("Email")
        if not await email.count():
            email = page.locator('input[type="email"]')
        await email.first.click()
        await email.first.fill("")
        await email.first.type("admin@arl.local", delay=40)
        await wait(page, 700)
        pwd = page.get_by_label("Password")
        if not await pwd.count():
            pwd = page.locator('input[type="password"]')
        await pwd.first.click()
        await pwd.first.fill("")
        await pwd.first.type("ChangeMe123!", delay=40)
        await wait(page, 700)
        for name in ("Continue to console", "Sign in to ARL", "Sign in"):
            btn = page.get_by_role("button", name=name)
            if await btn.count():
                await btn.first.click()
                break
        await page.wait_for_function("() => !location.pathname.includes('/login')", timeout=45000)
        await wait(page, 3000)

        # --- Horizon Scan (home) ---
        marker(markers, "02_horizon")
        await wait(page, 3500)
        jur = page.locator("select").first
        if await jur.count():
            try:
                await jur.select_option(label="UK")
                await wait(page, 1500)
                await jur.select_option(label="All jurisdictions")
                await wait(page, 1200)
            except Exception:
                pass
        await page.evaluate("window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'})")
        await wait(page, 2000)
        await page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
        await wait(page, 1000)

        # Prefer an under-review item for demo (PRA OR)
        row = page.locator("a[href*='/horizon/']").filter(has_text="Operational Resilience").first
        if not await row.count():
            row = page.locator("a[href*='/horizon/']").first
        await row.click()
        await wait(page, 2500)

        # --- Detail / assess ---
        marker(markers, "03_detail")
        await page.evaluate("window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'})")
        await wait(page, 2000)
        apply_btn = page.get_by_role(
            "button", name="Mark applicable → create obligation & case"
        ).first
        if not await apply_btn.count():
            apply_btn = page.get_by_role("button", name="Applicable → register & case").first
        if await apply_btn.count():
            await apply_btn.click()
            await wait(page, 3000)
        back = page.get_by_text("Back to Horizon Scan", exact=False)
        if await back.count():
            await back.first.click()
            await wait(page, 1500)

        # --- Applicability ---
        marker(markers, "04_applicability")
        await click_nav(page, "Applicability")
        await wait(page, 2500)
        filt = page.locator("select").first
        if await filt.count():
            try:
                await filt.select_option(label="Under review")
                await wait(page, 1500)
            except Exception:
                pass
        apply2 = page.get_by_role("button", name="Applicable → register & case").first
        if await apply2.count():
            await apply2.click()
            await wait(page, 2500)

        # --- Obligations ---
        marker(markers, "05_obligations")
        await click_nav(page, "Obligations Register")
        await wait(page, 3000)
        oj = page.locator("select").first
        if await oj.count():
            try:
                await oj.select_option(label="EU")
                await wait(page, 1500)
                await oj.select_option(label="All jurisdictions")
                await wait(page, 1200)
            except Exception:
                pass
        await page.evaluate("window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'})")
        await wait(page, 1500)

        # --- Cases list ---
        marker(markers, "06_cases")
        await click_nav(page, "Gap Analysis Cases")
        await wait(page, 2500)
        gs = page.locator("select").first
        if await gs.count():
            try:
                await gs.select_option(label="Gap")
                await wait(page, 1200)
                await gs.select_option(label="All gap statuses")
                await wait(page, 1000)
            except Exception:
                pass
        case_link = page.locator("a[href*='/cases/']").first
        if await case_link.count():
            await case_link.click()
            await wait(page, 2500)

        # --- Case mapping ---
        marker(markers, "07_case_map")
        await page.evaluate("window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'})")
        await wait(page, 1500)
        kind = page.locator("select").nth(0)
        ref = page.locator("select").nth(1)
        cov = page.locator("select").nth(2)
        if await kind.count() and await ref.count():
            try:
                await kind.select_option(value="policy")
                await wait(page, 600)
                options = await ref.locator("option").all()
                if len(options) > 1:
                    await ref.select_option(index=1)
                    await wait(page, 600)
                if await cov.count():
                    await cov.select_option(value="partial")
                notes = page.get_by_placeholder("Notes")
                if await notes.count():
                    await notes.fill("Tutorial mapping — review coverage with first line.")
                add = page.get_by_role("button", name="Add mapping")
                if await add.count() and await add.is_enabled():
                    await add.click()
                    await wait(page, 2500)
            except Exception:
                pass
        await wait(page, 1500)

        # --- Library ---
        marker(markers, "08_library")
        await click_nav(page, "Policies & Controls")
        await wait(page, 3500)
        await page.evaluate("window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'})")
        await wait(page, 1500)

        # --- Sources ---
        marker(markers, "09_sources")
        await click_nav(page, "Regulatory Sources")
        await wait(page, 3000)

        # --- Admin ---
        marker(markers, "10_admin")
        await click_nav(page, "Administration")
        await wait(page, 3500)

        marker(markers, "_end")

        video_path = Path(await page.video.path())
        await context.close()
        await browser.close()

    for m in markers:
        m["sec"] = round(m["t"] - t0, 3)

    markers_path = OUT / "recording_markers.json"
    markers_path.write_text(json.dumps(markers, indent=2), encoding="utf-8")
    print(f"Raw video: {video_path}")
    print(f"Markers: {markers_path}")
    return video_path, markers


async def synthesize_all() -> dict[str, Path]:
    import edge_tts

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for ch in CHAPTERS:
        out = AUDIO_DIR / f"{ch['id']}.mp3"
        communicate = edge_tts.Communicate(ch["narration"], voice="en-US-JennyNeural")
        await communicate.save(str(out))
        paths[ch["id"]] = out
        print(f"  audio {ch['id']}")
    return paths


def audio_duration(path: Path) -> float:
    ffmpeg = ffmpeg_bin()
    try:
        from mutagen.mp3 import MP3

        return float(MP3(str(path)).info.length)
    except Exception:
        pass
    result = subprocess.run([ffmpeg, "-i", str(path)], capture_output=True, text=True)
    import re

    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", result.stderr or "")
    if not m:
        return 8.0
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))


def build_final(raw_video: Path, markers: list[dict], audios: dict[str, Path]) -> None:
    ffmpeg = ffmpeg_bin()
    CHAPTERS_DIR.mkdir(parents=True, exist_ok=True)
    for old in CHAPTERS_DIR.glob("*.mp4"):
        old.unlink(missing_ok=True)

    raw_mp4 = OUT / "recording_raw.mp4"
    r = subprocess.run(
        [
            ffmpeg,
            "-y",
            "-i",
            str(raw_video),
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "20",
            "-pix_fmt",
            "yuv420p",
            "-an",
            str(raw_mp4),
        ],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-2000:])

    by_id = {m["id"]: m["sec"] for m in markers}
    end_t = by_id.get("_end", markers[-1]["sec"])
    parts: list[Path] = []

    for i, ch in enumerate(CHAPTERS):
        start = by_id[ch["id"]]
        stop = by_id[CHAPTERS[i + 1]["id"]] if i + 1 < len(CHAPTERS) else end_t
        narr_len = audio_duration(audios[ch["id"]]) + 0.8
        src_span = max(0.8, stop - start)
        seg_len = max(src_span, narr_len)
        if seg_len > narr_len + 18:
            seg_len = narr_len + 12

        clip = CHAPTERS_DIR / f"{ch['id']}_silent.mp4"
        mixed = CHAPTERS_DIR / f"{ch['id']}.mp4"
        src_len = min(src_span, seg_len)
        cmd_extract = [
            ffmpeg,
            "-y",
            "-ss",
            f"{start:.3f}",
            "-i",
            str(raw_mp4),
            "-t",
            f"{src_len:.3f}",
            "-vf",
            f"scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,fps=30,tpad=stop_mode=clone:stop_duration={max(0, seg_len - src_len):.3f}",
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "20",
            "-pix_fmt",
            "yuv420p",
            str(clip),
        ]
        r = subprocess.run(cmd_extract, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"extract {ch['id']}: {r.stderr[-2000:]}")

        cmd_mix = [
            ffmpeg,
            "-y",
            "-i",
            str(clip),
            "-i",
            str(audios[ch["id"]]),
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            str(mixed),
        ]
        r = subprocess.run(cmd_mix, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"mix {ch['id']}: {r.stderr[-2000:]}")
        parts.append(mixed)
        print(f"  chapter {ch['id']} ({seg_len:.1f}s)")

    list_in_chapters = CHAPTERS_DIR / "concat.txt"
    list_in_chapters.write_text("\n".join(f"file '{p.name}'" for p in parts), encoding="utf-8")
    r = subprocess.run(
        [ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", "concat.txt", "-c", "copy", str(VIDEO_OUT)],
        cwd=str(CHAPTERS_DIR),
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        r2 = subprocess.run(
            [
                ffmpeg,
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                "concat.txt",
                "-c:v",
                "libx264",
                "-c:a",
                "aac",
                "-pix_fmt",
                "yuv420p",
                str(VIDEO_OUT),
            ],
            cwd=str(CHAPTERS_DIR),
            capture_output=True,
            text=True,
        )
        if r2.returncode != 0:
            raise RuntimeError(r.stderr[-1500:] + "\n" + r2.stderr[-1500:])

    print(f"Wrote {VIDEO_OUT}")


async def main() -> None:
    print("1) Recording live obligations walkthrough…")
    raw, markers = await record_walkthrough()
    await asyncio.sleep(1)
    if not raw.exists():
        vids = sorted(RAW_DIR.glob("*.webm"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not vids:
            raise FileNotFoundError("No recorded video found")
        raw = vids[0]

    print("2) Synthesizing narration…")
    audios = await synthesize_all()

    print("3) Muxing chapters into tutorial MP4…")
    build_final(raw, markers, audios)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        print("ERROR:", exc, file=sys.stderr)
        raise
