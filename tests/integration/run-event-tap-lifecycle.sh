#!/bin/bash
set -eu

# Optional WindowServer integration check; exit 77 means Input Monitoring is
# unavailable to this process. No key or pointer contents are recorded.
cd "$(dirname "$0")/../.."
mkdir -p tests/integration/build
clang++ -std=c++20 -Wall -Werror -O1 -fsanitize=address \
    -Isrc/share \
    -isystem vendor/vendor/include \
    -isystem vendor/Karabiner-DriverKit-VirtualHIDDevice/include \
    tests/integration/event_tap_lifecycle.cpp \
    -framework CoreFoundation -framework CoreGraphics -framework IOKit \
    -o tests/integration/build/event_tap_lifecycle
MallocNanoZone=0 tests/integration/build/event_tap_lifecycle
