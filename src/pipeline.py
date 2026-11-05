import subprocess
import sys


def run_step(script: str, *args: str) -> None:
    label = " ".join([script, *args])
    print(f"\n=== Etape : {label} ===")
    subprocess.run([sys.executable, script, *args], check=True)


if __name__ == "__main__":
    run_step("src/collect.py")
    run_step("src/collect.py", "amc")
    run_step("src/validate.py")
    run_step("src/transform.py")
    run_step("src/validate_amc.py")
    run_step("src/transform_amc.py")
    print("\nPipeline termine avec succes.")