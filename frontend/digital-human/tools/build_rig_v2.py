from __future__ import annotations

from pathlib import Path
from typing import Iterable

from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lvxiaozhi_digital_human_assets"
OUTPUT = ROOT / "lvxiaozhi_rig_v2"

CANVAS = (2000, 2400)
ARTBOARD_CENTER = (CANVAS[0] // 2, CANVAS[1] // 2)


def transparent_layer() -> Image.Image:
    return Image.new("RGBA", CANVAS, (0, 0, 0, 0))


def open_rgba(path: Path) -> Image.Image:
    return Image.open(path).convert("RGBA")


def resize(image: Image.Image, scale: float) -> Image.Image:
    size = (round(image.width * scale), round(image.height * scale))
    return image.resize(size, Image.Resampling.LANCZOS)


def place_full_canvas(
    source: Path,
    scale: float,
    top_left: tuple[int, int],
    *,
    mirror: bool = False,
) -> Image.Image:
    image = open_rgba(source)
    if mirror:
        image = ImageOps.mirror(image)
    image = resize(image, scale)
    layer = transparent_layer()
    layer.alpha_composite(image, top_left)
    return layer


def place_cropped(
    source: Path,
    scale: float,
    top_left: tuple[int, int],
) -> Image.Image:
    image = open_rgba(source)
    bbox = image.getchannel("A").getbbox()
    if bbox is None:
        raise ValueError(f"No visible pixels in {source}")
    image = resize(image.crop(bbox), scale)
    layer = transparent_layer()
    layer.alpha_composite(image, top_left)
    return layer


def save(layer: Image.Image, relative_path: str) -> None:
    target = OUTPUT / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    layer.save(target, "PNG")


def composite(layers: Iterable[Image.Image]) -> Image.Image:
    result = transparent_layer()
    for layer in layers:
        result.alpha_composite(layer)
    return result


def fit_inside(image: Image.Image, max_size: tuple[int, int]) -> Image.Image:
    image = image.copy()
    image.thumbnail(max_size, Image.Resampling.LANCZOS)
    return image


def centered_feature(image: Image.Image, center: tuple[int, int]) -> Image.Image:
    layer = transparent_layer()
    x = center[0] - image.width // 2
    y = center[1] - image.height // 2
    layer.alpha_composite(image, (x, y))
    return layer


def build_mouth_layers() -> dict[str, Image.Image]:
    sheet = open_rgba(SOURCE / "components" / "05_mouth_expression_sheet.png")
    x_edges = [0, sheet.width // 2, sheet.width]
    y_edges = [round(sheet.height * i / 4) for i in range(5)]
    names = [
        "smile",
        "serious_long",
        "surprised",
        "serious_short",
        "happy",
        "worried",
        "thinking",
        "open",
    ]
    layers: dict[str, Image.Image] = {}
    index = 0
    for row in range(4):
        for col in range(2):
            cell = sheet.crop(
                (x_edges[col], y_edges[row], x_edges[col + 1], y_edges[row + 1])
            )
            bbox = cell.getchannel("A").getbbox()
            if bbox is None:
                raise ValueError(f"Mouth cell {index} is empty")
            feature = fit_inside(cell.crop(bbox), (360, 185))
            layers[names[index]] = centered_feature(feature, (1000, 770))
            index += 1
    return layers


def main() -> None:
    components = SOURCE / "components"

    # Head shell and screen deliberately share the exact same source transform.
    head_shell = place_full_canvas(
        components / "02_head_shell.png", 0.78, (511, 140)
    )
    face_screen = place_full_canvas(
        components / "03_face_screen.png", 0.78, (511, 140)
    )
    body = place_full_canvas(components / "06_body_base.png", 0.83, (549, 880))

    # Source 07 is the raised arm on the viewer's right.
    arm_viewer_right_up = place_full_canvas(
        components / "07_arm_left_component.png", 0.58, (1230, 727)
    )
    # Source 08 is mirrored to form the lowered arm on the viewer's left.
    arm_viewer_left_down = place_full_canvas(
        components / "08_arm_right_component.png", 0.55, (244, 918), mirror=True
    )

    hand_viewer_right_open = place_full_canvas(
        components / "09_hand_left_open.png", 0.36, (1568, 493)
    )
    hand_viewer_left_open = place_full_canvas(
        components / "10_hand_right_open.png", 0.32, (320, 1387)
    )

    save(head_shell, "components/head_shell.png")
    save(face_screen, "components/face_screen.png")
    save(body, "components/body_base.png")
    save(arm_viewer_right_up, "components/arm_viewer_right_up.png")
    save(arm_viewer_left_down, "components/arm_viewer_left_down.png")
    save(hand_viewer_right_open, "components/hand_viewer_right_open.png")
    save(hand_viewer_left_open, "components/hand_viewer_left_open.png")

    eye_layers: dict[str, Image.Image] = {}
    for eye_file in sorted((SOURCE / "eyes").glob("eyes_*.png")):
        eye = open_rgba(eye_file)
        bbox = eye.getchannel("A").getbbox()
        if bbox is None:
            continue
        feature = fit_inside(eye.crop(bbox), (470, 205))
        layer = centered_feature(feature, (1000, 620))
        eye_layers[eye_file.stem.removeprefix("eyes_")] = layer
        save(layer, f"eyes/{eye_file.name}")

    mouth_layers = build_mouth_layers()
    for name, layer in mouth_layers.items():
        save(layer, f"mouth/mouth_{name}.png")

    preview_layers = [
        arm_viewer_left_down,
        arm_viewer_right_up,
        body,
        hand_viewer_left_open,
        hand_viewer_right_open,
        face_screen,
        head_shell,
        eye_layers["idle"],
        mouth_layers["smile"],
    ]
    rig_preview = composite(preview_layers)
    save(rig_preview, "preview/assembled_transparent.png")

    background = Image.new("RGBA", CANVAS, (238, 244, 252, 255))
    background.alpha_composite(rig_preview)
    save(background, "preview/assembled_on_light.png")

    readme = f"""Lvxiaozhi Rive rig v2

Canvas: {CANVAS[0]} x {CANVAS[1]} px
Rive artboard: {CANVAS[0]} x {CANVAS[1]}
Every PNG layer uses the same full-size transparent canvas.

Import rule:
1. Drag every asset onto an EMPTY area of the artboard.
2. Set every image layer to Position X={ARTBOARD_CENTER[0]}, Y={ARTBOARD_CENTER[1]}.
3. Set Scale X=100%, Y=100%, Rotation=0.

Recommended draw order, back to front:
arm_viewer_left_down
arm_viewer_right_up
body_base
hand_viewer_left_open
hand_viewer_right_open
face_screen
head_shell
one eyes layer
one mouth layer

Only one eyes layer and one mouth layer should be visible at a time.
Original assets are preserved unchanged.
"""
    (OUTPUT / "README.txt").write_text(readme, encoding="utf-8")


if __name__ == "__main__":
    main()
