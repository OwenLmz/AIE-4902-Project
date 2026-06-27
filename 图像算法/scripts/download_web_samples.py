from __future__ import annotations

from pathlib import Path
from urllib.request import Request, urlopen


SAMPLES = {
    "WEB-S3_free_empty_room.jpg": "https://library.udel.edu/ourspaces/wp-content/uploads/sites/32/2018/10/20090508_0192-405x270.jpg",
    "WEB-S4_suspected_backpack.jpg": "https://library.udel.edu/ourspaces/wp-content/uploads/sites/32/2018/10/IMG_1901-405x270.jpg",
    "WEB-S5_occupied_student.jpg": "https://library.udel.edu/ourspaces/wp-content/uploads/sites/32/2018/10/IMG_6552-405x270.jpg",
}


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    out_dir = root / "images" / "web_test"
    out_dir.mkdir(parents=True, exist_ok=True)

    for filename, url in SAMPLES.items():
        out_path = out_dir / filename
        request = Request(url, headers={"User-Agent": "SmartCampusCapstone/1.0"})
        print(f"Downloading {filename} ...")
        with urlopen(request, timeout=30) as response:
            out_path.write_bytes(response.read())
        print(f"Saved {out_path}")


if __name__ == "__main__":
    main()
