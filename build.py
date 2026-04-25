import subprocess

def build_executable():

    subprocess.run([
        "pyinstaller",
        "--name=VoicePhrase",
        "--windowed",
        "--hide-console=hide-early",
        "--icon=assets/VoicePhrase.ico",
        "--add-data", ".env:.",
        "--add-data", "utils/config.ini:.",
        "--add-data", "data/replacements.txt:.",
        "--add-data", "data/ophthalmology_phrases.txt:.",
        "main.py"
    ])

    print(f"Executable built successfully.")

if __name__ == "__main__":
    build_executable()
