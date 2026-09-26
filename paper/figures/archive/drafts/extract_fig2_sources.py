"""Extract the two Fig. 2 photographs from the author's original PPTX.

This is a provenance helper for the archived draft deck. The active Fig. 2
script reads the resulting JPEGs directly and does not require python-pptx.
"""

from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps
from pptx import Presentation


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "fig1_pipeline.pptx"
TARGET = HERE.parents[1] / "fig02"


def main() -> None:
    shapes = Presentation(str(SOURCE)).slides[0].shapes
    for shape_number, name in [(7, "source_real93_a.jpg"),
                               (9, "source_real93_b.jpg")]:
        image = Image.open(BytesIO(shapes[shape_number].image.blob)).convert("RGB")
        image = ImageOps.fit(image, (1000, 750), method=Image.Resampling.LANCZOS)
        image.save(TARGET / name, format="JPEG", quality=91, optimize=True)


if __name__ == "__main__":
    main()
