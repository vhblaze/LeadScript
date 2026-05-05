import subprocess
import sys
from pathlib import Path


def main():
    projeto = Path(__file__).resolve().parent
    entrada_cli = projeto / "cli.py"

    comando = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--name",
        "leadscript",
        "--clean",
        "--hidden-import",
        "asyncio",
        str(entrada_cli),
    ]

    print("Compilando runner LeadScript com PyInstaller...")
    print(" ".join(comando))
    subprocess.run(comando, cwd=projeto, check=True)

    print("\nBuild finalizado.")
    print("Executavel gerado em:")
    print(f"  {projeto / 'dist' / _nome_executavel()}")


def _nome_executavel():
    return "leadscript.exe" if sys.platform.startswith("win") else "leadscript"


if __name__ == "__main__":
    main()
