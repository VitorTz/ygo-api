from pathlib import Path
from PIL import Image
from datetime import datetime
import requests
import json
import os


VALID_SORT_COLUMNS = {"name", "attack", "defence", "level", "card_id"}
VALID_CARD_SETS_SORT_COLUMNS = {"name", "card_set_code", "price"}
VALID_SORT_ORDERS = {"asc", "desc"}
FILTERABLE_COLUMNS = {
    "archetype",
    "race",
    "type",
    "attribute",
    "frametype",
}


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


def normalize_card_sort_by(sort_by: str) -> str:
    sort_by = sort_by.lower()
    if sort_by not in VALID_SORT_COLUMNS:
        sort_by = "name"
    return sort_by


def normalize_card_sets_sort_by(sort_by: str) -> str:
    sort_by = sort_by.lower()
    if sort_by not in VALID_CARD_SETS_SORT_COLUMNS:
        sort_by = "card_set_code"
    return sort_by


def normalize_sort_order(sort_order: str) -> str:
    sort_order = sort_order.lower()
    if sort_order not in VALID_SORT_ORDERS:
        sort_order = "asc"
    return sort_order


def extract_card_filters(locals: dict, search: str | None) -> str:
    filters = []
    params = []

    for col in FILTERABLE_COLUMNS:
        value: str = locals.get(col)
        if col == 'attribute' and value is not None:
            value = value.upper()
        if value is not None:
            filters.append(f"{col} = %s")
            params.append(value)
    
    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ''
    if search:
        if where_clause == '':
            where_clause = "WHERE name ILIKE %s"
        else:
            where_clause += " AND name ILIKE %s"

    return where_clause, params


def load_ygoprodeck_data() -> None:
    print(f"[REQUESTING YGO DATA]")
    r = requests.get("https://db.ygoprodeck.com/api/v7/cardinfo.php")
    data = r.json()['data']
    with open(f"res/{datetime.now()}.json", "w+") as file:
        json.dump(data, file, indent=4, sort_keys=True)
    return data


def load_ygoprodeck_cardsets() -> None:
    print(f"[REQUESTING YGO CARD SET DATA]")
    r = requests.get("https://db.ygoprodeck.com/api/v7/cardsets.php")
    data = r.json()
    with open(f"res/cardsets-{datetime.now()}.json", "w+") as file:
        json.dump(data, file, indent=4, sort_keys=True)
    return data