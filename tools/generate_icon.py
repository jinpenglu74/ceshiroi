from pathlib import Path

from PIL import Image, ImageDraw


def main() -> None:
    output = Path("build")
    output.mkdir(exist_ok=True)

    image = Image.new("RGBA", (256, 256), (4, 20, 48, 255))
    draw = ImageDraw.Draw(image)

    draw.rounded_rectangle(
        (12, 12, 244, 244),
        radius=48,
        outline=(51, 204, 255, 255),
        width=8,
        fill=(6, 39, 83, 255),
    )

    for box in ((54, 142, 82, 188), (104, 110, 132, 188), (154, 78, 182, 188)):
        draw.rounded_rectangle(box, radius=5, fill=(77, 230, 255, 255))

    draw.line(
        [(53, 113), (101, 76), (137, 95), (203, 44)],
        fill=(117, 247, 255, 255),
        width=12,
        joint="curve",
    )
    draw.line(
        [(177, 44), (203, 44), (203, 70)],
        fill=(117, 247, 255, 255),
        width=12,
        joint="curve",
    )

    image.save(
        output / "roi_calculator.ico",
        sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )


if __name__ == "__main__":
    main()
