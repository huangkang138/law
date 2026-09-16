from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1] / "law_xiaozhi"
SOURCE = ROOT / "body_base.png"
OUTPUT = ROOT / "arm-components-v2"
RAW = OUTPUT / "raw"

CANVAS = (1024, 1536)
LEFT_SHOULDER = (356, 326)
RIGHT_SHOULDER = (668, 326)


LEFT_ARM_POLYGON = [
    (303, 260), (385, 250), (380, 388), (370, 495), (340, 642),
    (312, 745), (305, 806), (289, 844), (250, 820), (229, 780),
    (226, 733), (205, 710), (216, 654), (249, 546), (284, 448),
]

RIGHT_ARM_POLYGON = [
    (639, 250), (721, 260), (740, 448), (775, 546), (808, 654),
    (819, 710), (798, 733), (795, 780), (774, 820), (735, 844),
    (719, 806), (712, 745), (684, 642), (654, 495), (644, 388),
]

SHOULDER_OVERLAY_POLYGON = [
    (300, 245), (724, 245), (708, 360), (660, 450), (630, 540),
    (610, 650), (414, 650), (394, 540), (364, 450), (316, 360),
]


def subject_alpha(image: Image.Image, threshold: int = 18) -> Image.Image:
    alpha = image.getchannel("A")
    return alpha.point(lambda value: value if value >= threshold else 0)


def polygon_mask(points: list[tuple[int, int]], blur: float = 1.2) -> Image.Image:
    mask = Image.new("L", CANVAS, 0)
    ImageDraw.Draw(mask).polygon(points, fill=255)
    if blur:
        mask = mask.filter(ImageFilter.GaussianBlur(blur))
    return mask


def isolate(source: Image.Image, points: list[tuple[int, int]]) -> Image.Image:
    result = source.copy()
    mask = polygon_mask(points)
    alpha = Image.composite(subject_alpha(source), Image.new("L", CANVAS, 0), mask)
    result.putalpha(alpha)
    return result


def build_body(source: Image.Image) -> Image.Image:
    result = source.copy()
    remove = Image.new("L", CANVAS, 0)
    draw = ImageDraw.Draw(remove)
    draw.polygon(LEFT_ARM_POLYGON, fill=255)
    draw.polygon(RIGHT_ARM_POLYGON, fill=255)
    # These narrow rear-sleeve strips are hidden by the hanging arms in the source.
    # Remove them so they do not become exposed when an answer arm lifts away.
    draw.polygon([(318, 390), (372, 455), (354, 590), (338, 690), (318, 735)], fill=255)
    draw.polygon([(706, 390), (652, 455), (670, 590), (686, 690), (706, 735)], fill=255)
    remove = remove.filter(ImageFilter.MaxFilter(3))
    remove = remove.filter(ImageFilter.GaussianBlur(1.2))
    alpha = subject_alpha(source)
    alpha = Image.composite(Image.new("L", CANVAS, 0), alpha, remove)
    result.putalpha(alpha)
    return result


def crop_component(image: Image.Image, threshold: int = 96, padding: int = 8) -> tuple[Image.Image, tuple[int, int, int, int]]:
    alpha = image.getchannel("A").point(lambda value: 255 if value >= threshold else 0)
    bbox = alpha.getbbox()
    if bbox is None:
        raise ValueError("component has no visible pixels")
    left = max(0, bbox[0] - padding)
    top = max(0, bbox[1] - padding)
    right = min(image.width, bbox[2] + padding)
    bottom = min(image.height, bbox[3] + padding)
    cropped = image.crop((left, top, right, bottom))
    cropped_alpha = cropped.getchannel("A").point(lambda value: 0 if value < 18 else value)
    cropped.putalpha(cropped_alpha)
    return cropped, (left, top, right, bottom)


def normalize_generated(
    source_path: Path,
    output_name: str,
    shoulder_in_source: tuple[int, int],
    target_shoulder: tuple[int, int],
    scale: float,
) -> dict[str, object]:
    image = Image.open(source_path).convert("RGBA")
    crop, bbox = crop_component(image)
    resized = crop.resize(
        (round(crop.width * scale), round(crop.height * scale)),
        Image.Resampling.LANCZOS,
    )
    source_anchor = (
        round((shoulder_in_source[0] - bbox[0]) * scale),
        round((shoulder_in_source[1] - bbox[1]) * scale),
    )
    offset = (
        target_shoulder[0] - source_anchor[0],
        target_shoulder[1] - source_anchor[1],
    )
    canvas = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    canvas.alpha_composite(resized, offset)
    canvas.save(OUTPUT / output_name)
    return {
        "file": output_name,
        "canvas": list(CANVAS),
        "shoulderAnchor": list(target_shoulder),
        "sourceScale": scale,
        "sourceOffset": list(offset),
    }


def checker_preview(foreground: Image.Image) -> Image.Image:
    background = Image.new("RGBA", CANVAS, (232, 232, 232, 255))
    draw = ImageDraw.Draw(background)
    tile = 32
    for y in range(0, CANVAS[1], tile):
        for x in range(0, CANVAS[0], tile):
            if (x // tile + y // tile) % 2:
                draw.rectangle((x, y, x + tile - 1, y + tile - 1), fill=(198, 198, 198, 255))
    background.alpha_composite(foreground)
    return background


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    source = Image.open(SOURCE).convert("RGBA")

    body = build_body(source)
    left_idle = isolate(source, LEFT_ARM_POLYGON)
    right_idle = isolate(source, RIGHT_ARM_POLYGON)
    shoulder_overlay = isolate(source, SHOULDER_OVERLAY_POLYGON)

    body.save(OUTPUT / "body_static.png")
    left_idle.save(OUTPUT / "arm_viewer_left_idle.png")
    right_idle.save(OUTPUT / "arm_viewer_right_idle.png")
    shoulder_overlay.save(OUTPUT / "shoulder_overlay.png")

    manifest = {
        "coordinateSystem": "1024x1536 full canvas; screen/viewer left and right naming",
        "layerOrderBottomToTop": [
            "arm_viewer_left_*",
            "arm_viewer_right_*",
            "body_static.png",
            "shoulder_overlay.png",
            "existing head layers",
        ],
        "body": {"file": "body_static.png", "canvas": list(CANVAS)},
        "shoulderOverlay": {
            "file": "shoulder_overlay.png",
            "canvas": list(CANVAS),
            "purpose": "render above both arms to conceal the shoulder roots",
        },
        "idle": {
            "left": {
                "file": "arm_viewer_left_idle.png",
                "canvas": list(CANVAS),
                "shoulderAnchor": list(LEFT_SHOULDER),
            },
            "right": {
                "file": "arm_viewer_right_idle.png",
                "canvas": list(CANVAS),
                "shoulderAnchor": list(RIGHT_SHOULDER),
            },
        },
        "answer": {
            "left": normalize_generated(
                RAW / "arm_viewer_left_answer_generated.png",
                "arm_viewer_left_answer.png",
                shoulder_in_source=(930, 225),
                target_shoulder=(376, 326),
                scale=0.36,
            ),
            "right": normalize_generated(
                RAW / "arm_viewer_right_answer_generated.png",
                "arm_viewer_right_answer.png",
                shoulder_in_source=(120, 235),
                target_shoulder=(648, 326),
                scale=0.36,
            ),
        },
    }

    (OUTPUT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    idle_preview = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    idle_preview.alpha_composite(left_idle)
    idle_preview.alpha_composite(right_idle)
    idle_preview.alpha_composite(body)
    idle_preview.alpha_composite(shoulder_overlay)
    idle_preview.save(OUTPUT / "preview_idle.png")

    answer_preview = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    answer_preview.alpha_composite(Image.open(OUTPUT / "arm_viewer_left_answer.png").convert("RGBA"))
    answer_preview.alpha_composite(Image.open(OUTPUT / "arm_viewer_right_answer.png").convert("RGBA"))
    answer_preview.alpha_composite(body)
    answer_preview.alpha_composite(shoulder_overlay)
    answer_preview.save(OUTPUT / "preview_answer.png")
    checker_preview(answer_preview).save(OUTPUT / "preview_answer_checker.png")


if __name__ == "__main__":
    main()
