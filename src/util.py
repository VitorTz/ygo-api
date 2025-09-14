from pathlib import Path
from PIL import Image
import requests
import os


def convert_to_webp(
    path: Path,
    output: Path | None = None,
    force_compress: bool = False
) -> Path:
    if output is None: output = path.with_suffix(".webp")
    if force_compress or path.suffix != ".webp":
        try:
            with Image.open(path) as img:
                img.save(output, format='WEBP')
        except Exception as e:        
            print(f"[COULD NOT COVERT {path} TO WEBP] {e}")
            return path
        
    if path.suffix != ".webp":
        os.remove(str(path))    
    return output


def download_image(path: Path, url: str) -> Path:
    if isinstance(path, str):
        path = Path(path)
    r = requests.get(url, stream=True)    
    with open(path, "wb") as file:
        for chunk in r.iter_content(1024):
            file.write(chunk)
    return convert_to_webp(path)


def delete_file(path: Path) -> None:
    try:
        os.remove(str(path))
    except Exception:
        pass