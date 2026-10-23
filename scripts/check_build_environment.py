#!/usr/bin/env python3
"""Check the Sonoma-compatible build baseline without changing the host."""

import argparse
import re
import shutil
import subprocess
import sys


def output(*command):
    result = subprocess.run(command, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True)
    return result.returncode, result.stdout.strip()


def version(text):
    if "Swift version" in text:
        text = text.split("Swift version", 1)[1]
    match = re.search(r"\d+(?:\.\d+)+", text)
    return tuple(map(int, match.group().split("."))) if match else ()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compiler-only", action="store_true",
                        help="check SDK and compiler compatibility without requiring full Xcode")
    args = parser.parse_args()
    errors = []
    for label, command, minimum in [
        ("macOS", ("sw_vers", "-productVersion"), (14, 5)),
        ("macOS SDK", ("xcrun", "--show-sdk-version"), (15, 2)),
        ("Swift", ("xcrun", "swiftc", "--version"), (6, 0)),
    ]:
        code, value = output(*command)
        print(f"{label}: {value.splitlines()[0] if value else 'unavailable'}", flush=True)
        if code or version(value) < minimum:
            errors.append(f"{label} requires {'.'.join(map(str, minimum))} or later")

    if not args.compiler_only:
        code, value = output("xcodebuild", "-version")
        if code or version(value) < (16, 2):
            errors.append("Install full Xcode 16.2 (compatible with macOS 14.5+) and select it:\n"
                          "  sudo xcode-select --switch /Applications/Xcode.app/Contents/Developer\n"
                          "  sudo xcodebuild -runFirstLaunch\n"
                          "This target uses the Xcode build system. For the CLT alternative, see BUILDING-CLT.zh-TW.md.")
        else:
            print(value)
        for tool in ("xcodegen", "cmake", "xz", "ruby"):
            if not shutil.which(tool):
                errors.append(f"Missing build tool: {tool}")
        for tool, minimum in (("xcodegen", (2, 42, 0)), ("cmake", (3, 24, 0))):
            if shutil.which(tool):
                code, value = output(tool, "--version")
                if code or version(value) < minimum:
                    errors.append(f"{tool} requires {'.'.join(map(str, minimum))} or later")

    if errors:
        print("\nBuild environment is not ready:\n- " + "\n- ".join(errors), file=sys.stderr)
        return 1
    print("Compiler and SDK versions meet the baseline." if args.compiler_only else "Build environment is ready.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
