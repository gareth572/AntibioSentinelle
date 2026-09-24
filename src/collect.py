from datetime import datetime, timezone
from pathlib import Path
import sys 
import requests

# l'url de ma source
DEFAULT_URL = "https://zenodo.org/records/14224680/files/summary_AMR_filtered.csv?download=1"
RAW_DIR = Path("data/raw")

# la fonction de collecte avec gestion d'erreur explicite
def collect(url: str = DEFAULT_URL) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        print(f"Erreur lors de la collecte : {exc}", files=sys.stderr)
        raise

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = RAW_DIR / f"amr_resistance_{stamp}.csv"
    output.write_bytes(response.content)

    print (f"Collecte reussie : {output} ({len(response.content)} octets)")
    return output

# le point d'entrée
if __name__ == "__main__":
    target_url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL
    collect(target_url)