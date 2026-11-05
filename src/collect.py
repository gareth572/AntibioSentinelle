from datetime import datetime, timezone
from pathlib import Path
import sys
import time
import requests

BASE_URL = "https://zenodo.org/records/14224680/files"

# nom court -> (fichier source, prefixe du fichier raw)
SOURCES = {
    "amr": ("summary_AMR_filtered.csv", "amr_resistance"),
    "amc": ("summary_AMC_byclass.csv", "amc_consumption"),
}
RAW_DIR = Path("data/raw")


def collect(source: str = "amr", url: str | None = None) -> Path:
    filename, prefix = SOURCES[source]
    url = url or f"{BASE_URL}/{filename}?download=1"
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    last_error = None
    for attempt in range(1, 4):
        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            break
        except requests.exceptions.RequestException as exc:
            last_error = exc
            print(f"Tentative {attempt}/3 echouee : {exc}", file=sys.stderr)
            time.sleep(5 * attempt)
    else:
        print("Collecte abandonnee apres 3 tentatives.", file=sys.stderr)
        raise last_error

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = RAW_DIR / f"{prefix}_{stamp}.csv"
    output.write_bytes(response.content)

    print(f"Collecte reussie : {output} ({len(response.content)} octets)")
    return output


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "amr"
    if arg in SOURCES:
        collect(arg)
    else:
        collect("amr", url=arg)  # compatibilite : une URL passee en argument