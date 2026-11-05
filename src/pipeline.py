import subprocess
import sys


def run_step(script: str, *args: str) -> None:
    print(f"\n=== Etape : {script} {' '.join(args)} ===")
    subprocess.run([sys.executable, script, *args], check=True)


if __name__ == "__main__":
    run_step("src/collect.py")
    run_step("src/validate.py")
    run_step("src/transform.py")
    print("\nPipeline termine avec succes.")