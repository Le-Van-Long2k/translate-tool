import argparse
from pathlib import Path

import torch
from PIL import Image, ImageDraw, ImageFont

from transformers import (
    RTDetrImageProcessor,
    RTDetrV2ForObjectDetection,
)


REPO_ID = "ogkalu/comic-text-and-bubble-detector"

CLASSES = {
    0: "bubble",
    1: "text_bubble",
    2: "text_free",
}


def load_model():
    device = "cuda" if torch.cuda.is_available() else "cpu"

    print(f"Device: {device}")

    processor = RTDetrImageProcessor.from_pretrained(REPO_ID)

    model = RTDetrV2ForObjectDetection.from_pretrained(
        REPO_ID
    )

    model.to(device)
    model.eval()

    return processor, model, device


def get_font(size=24):
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ]

    for path in font_paths:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass

    return ImageFont.load_default()


def detect(
    image,
    processor,
    model,
    device,
    conf=0.3,
):
    inputs = processor(
        images=image,
        return_tensors="pt",
    )

    inputs = {
        key: value.to(device)
        for key, value in inputs.items()
    }

    with torch.inference_mode():
        outputs = model(**inputs)

    target_sizes = torch.tensor(
        [[image.height, image.width]],
        device=device,
    )

    results = processor.post_process_object_detection(
        outputs,
        target_sizes=target_sizes,
        threshold=conf,
    )[0]

    detections = []

    for score, label, box in zip(
        results["scores"],
        results["labels"],
        results["boxes"],
    ):
        class_id = int(label.item())
        score_value = float(score.item())

        x1, y1, x2, y2 = box.tolist()

        detections.append(
            {
                "class_id": class_id,
                "class_name": CLASSES.get(
                    class_id,
                    f"unknown_{class_id}",
                ),
                "score": score_value,
                "box": (
                    int(x1),
                    int(y1),
                    int(x2),
                    int(y2),
                ),
            }
        )

    return detections


def draw_detections(
    image,
    detections,
    output_path,
    selected_class=None,
):
    result = image.copy()
    draw = ImageDraw.Draw(result)

    font = get_font(24)

    # Thứ tự class chỉ để dễ phân biệt khi debug.
    # Không ảnh hưởng detection.
    class_widths = {
        0: 5,
        1: 4,
        2: 3,
    }

    class_counts = {
        0: 0,
        1: 0,
        2: 0,
    }

    for detection in detections:
        class_id = detection["class_id"]

        if selected_class is not None:
            if class_id != selected_class:
                continue

        class_name = detection["class_name"]
        score = detection["score"]

        x1, y1, x2, y2 = detection["box"]

        class_counts[class_id] = (
            class_counts.get(class_id, 0) + 1
        )

        width = class_widths.get(class_id, 3)

        # Dùng các màu khác nhau để phân biệt 3 class.
        if class_id == 0:
            outline = "red"
        elif class_id == 1:
            outline = "green"
        elif class_id == 2:
            outline = "blue"
        else:
            outline = "white"

        draw.rectangle(
            (x1, y1, x2, y2),
            outline=outline,
            width=width,
        )

        label = (
            f"{class_name} "
            f"{score:.3f}"
        )

        bbox = draw.textbbox(
            (0, 0),
            label,
            font=font,
        )

        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        label_x = x1
        label_y = max(
            0,
            y1 - text_height - 8,
        )

        draw.rectangle(
            (
                label_x,
                label_y,
                label_x + text_width + 8,
                label_y + text_height + 6,
            ),
            fill=outline,
        )

        draw.text(
            (
                label_x + 4,
                label_y + 2,
            ),
            label,
            fill="white",
            font=font,
        )

    result.save(output_path)

    return class_counts


def print_statistics(detections):
    counts = {
        0: 0,
        1: 0,
        2: 0,
    }

    print()
    print("=" * 60)
    print("RT-DETR RAW DETECTION")
    print("=" * 60)

    for detection in detections:
        class_id = detection["class_id"]

        counts[class_id] = (
            counts.get(class_id, 0) + 1
        )

        print(
            f"class={detection['class_name']:<12} "
            f"id={class_id} "
            f"score={detection['score']:.4f} "
            f"box={detection['box']}"
        )

    print()
    print("COUNTS")
    print("-" * 60)

    for class_id, class_name in CLASSES.items():
        print(
            f"{class_name:<15}: "
            f"{counts.get(class_id, 0)}"
        )

    print("=" * 60)
    print()


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "image",
        help="Input image",
    )

    parser.add_argument(
        "--output",
        default="rtdetr_debug",
        help="Output directory",
    )

    parser.add_argument(
        "--conf",
        type=float,
        default=0.3,
        help="Detection confidence threshold",
    )

    args = parser.parse_args()

    image_path = Path(args.image)
    output_dir = Path(args.output)

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    print(f"Image : {image_path}")
    print(f"Output: {output_dir}")
    print(f"Conf  : {args.conf}")

    image = Image.open(
        image_path
    ).convert("RGB")

    print(
        f"Image size: "
        f"{image.width}x{image.height}"
    )

    processor, model, device = load_model()

    detections = detect(
        image=image,
        processor=processor,
        model=model,
        device=device,
        conf=args.conf,
    )

    # --------------------------------------------------
    # RAW STATISTICS
    # --------------------------------------------------

    print_statistics(detections)

    # --------------------------------------------------
    # 1. CLASS 0 - BUBBLE
    # --------------------------------------------------

    output_path = (
        output_dir / "class_0_bubble.png"
    )

    counts = draw_detections(
        image=image,
        detections=detections,
        output_path=output_path,
        selected_class=0,
    )

    print(
        f"[0] bubble      : "
        f"{counts.get(0, 0)}"
        f" -> {output_path}"
    )

    # --------------------------------------------------
    # 2. CLASS 1 - TEXT BUBBLE
    # --------------------------------------------------

    output_path = (
        output_dir / "class_1_text_bubble.png"
    )

    counts = draw_detections(
        image=image,
        detections=detections,
        output_path=output_path,
        selected_class=1,
    )

    print(
        f"[1] text_bubble : "
        f"{counts.get(1, 0)}"
        f" -> {output_path}"
    )

    # --------------------------------------------------
    # 3. CLASS 2 - TEXT FREE
    # --------------------------------------------------

    output_path = (
        output_dir / "class_2_text_free.png"
    )

    counts = draw_detections(
        image=image,
        detections=detections,
        output_path=output_path,
        selected_class=2,
    )

    print(
        f"[2] text_free   : "
        f"{counts.get(2, 0)}"
        f" -> {output_path}"
    )

    # --------------------------------------------------
    # 4. ALL 3 CLASSES
    # --------------------------------------------------

    output_path = (
        output_dir / "all_classes.png"
    )

    counts = draw_detections(
        image=image,
        detections=detections,
        output_path=output_path,
        selected_class=None,
    )

    print()
    print(
        "ALL CLASSES"
    )
    print(
        f"bubble      : {counts.get(0, 0)}"
    )
    print(
        f"text_bubble : {counts.get(1, 0)}"
    )
    print(
        f"text_free   : {counts.get(2, 0)}"
    )
    print(
        f"output      : {output_path}"
    )

    # --------------------------------------------------
    # CLEANUP
    # --------------------------------------------------

    del model

    if torch.cuda.is_available():
        torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
