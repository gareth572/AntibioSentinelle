import subprocess
import sys


def run_step(script: str) -> None:
    print(f"\n=== Etape : {script} ===")
    subprocess.run([sys.executable, script], check=True)


if __name__ == "__main__":
    run_step("src/collect.py")
    run_step("src/validate.py")
    print("\nPipeline termine avec succes.")