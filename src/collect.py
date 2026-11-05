from datetime import datetime, timezone
from pathlib import Path
import sys
import time
import requests

# l'url de ma source
DEFAULT_URL = "https://zenodo.org/records/14224680/files/summary_AMR_filtered.csv?download=1"
RAW_DIR = Path("data/raw")


def collect(url: str = DEFAULT_URL) -> Path:
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
    output = RAW_DIR / f"amr_resistance_{stamp}.csv"
    output.write_bytes(response.content)

    print(f"Collecte reussie : {output} ({len(response.content)} octets)")
    return output


# le point d'entree
if __name__ == "__main__":
    target_url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL
    collect(target_url)