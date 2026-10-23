[![Build Status](https://github.com/pqrs-org/Karabiner-Elements/workflows/Karabiner-Elements%20CI/badge.svg)](https://github.com/pqrs-org/Karabiner-Elements/actions)
[![License](https://img.shields.io/badge/license-Public%20Domain-blue.svg)](https://github.com/pqrs-org/Karabiner-Elements/blob/main/LICENSE.md)

# Karabiner-Elements

Karabiner-Elements is a powerful key remapper for macOS.

This fork is based on v15.9.0, and retains the original IOHID keyboard capture implementation.
It includes compatible bug backports, release-triggered Escape on the lock screen,
icons from @Zabriskije, and an AppKit sidebar with the existing appearance.
The upstream updater and its menu/settings entries have been removed.
See [backports and behavior](BACKPORTS.zh-TW.md), [CLT builds](BUILDING-CLT.zh-TW.md),
[Sonoma/Xcode builds](BUILDING-SONOMA.zh-TW.md), and [verification](VERIFICATION.zh-TW.md).
The upstream download links below provide official builds, not this fork.

## Download

You can download Karabiner-Elements from the [official site](https://karabiner-elements.pqrs.org/).

Alternatively, for users of [homebrew](https://brew.sh/), Karabiner-Elements may be installed with `brew install --cask karabiner-elements`.

### Old releases

You can download previous versions of Karabiner-Elements from [Release notes](https://karabiner-elements.pqrs.org/docs/releasenotes/).

## Supported systems

- macOS 26 Tahoe
    - Both Intel-based Macs and Apple Silicon Macs
- macOS 15 Sequoia
    - Both Intel-based Macs and Apple Silicon Macs
- macOS 14 Sonoma
    - Both Intel-based Macs and Apple Silicon Macs
- macOS 13 Ventura
    - Both Intel-based Macs and Apple Silicon Macs

## Usage

Documentation can be found here: <https://karabiner-elements.pqrs.org/docs/>

## Donations

If you would like to contribute financially to the development of Karabiner-Elements, donations can be made via <https://karabiner-elements.pqrs.org/docs/pricing/>

---

## For developers

### How to build

System requirements for the original Xcode build:

- macOS 14.5+ (including macOS 14.8.7)
- Full Xcode 16.2 (Swift 6.0, macOS 15.2 SDK), selected with `xcode-select`
- Command Line Tools for Xcode (`xcode-select --install`)
- xz (`brew install xz`)
- [XcodeGen](https://github.com/yonaskolb/XcodeGen) (`brew install xcodegen`)
- CMake (`brew install cmake`)

The runtime deployment target remains macOS 13.0. For a local build using only
Command Line Tools and the unchanged resources from installed 15.9.0 apps, use
`make package-clt`; see [BUILDING-CLT.zh-TW.md](BUILDING-CLT.zh-TW.md).
This branch pins Swift package versions for the Xcode 16.2 toolchain; keep those
pins when regenerating projects. See [BUILDING-SONOMA.zh-TW.md](BUILDING-SONOMA.zh-TW.md)
for setup and verification details.

Run `make check-build-environment` before building.

#### Steps

1.  Get source code by executing the following command in Terminal.app.

    ```shell
    git clone --depth 1 https://github.com/pqrs-org/Karabiner-Elements.git
    cd Karabiner-Elements
    git submodule update --init --recursive --depth 1
    ```

2.  (Optional) If you have a codesign identity:
    1.  Find your codesign identity.

        ```shell
        security find-identity -p codesigning -v | grep 'Developer ID Application'
        ```

        The result is as follows.

        ```text
        1) 8D660191481C98F5C56630847A6C39D95C166F22 "Developer ID Application: Fumihiko Takayama (G43BCU2T37)"
        ```

        Your codesign identity is `8D660191481C98F5C56630847A6C39D95C166F22` in the above case.

    2.  Set environment variable to use your codesign identity.

        ```shell
        export PQRS_ORG_CODE_SIGN_IDENTITY=8D660191481C98F5C56630847A6C39D95C166F22
        ```

    3.  Find your codesign identity for installer signing.

        ```shell
        security find-identity -p basic -v | grep 'Developer ID Installer'
        ```

        The result is as follows.

        ```text
        1) C86BB5F7830071C7B0B07D168A9A9375CC2D02C5 "Developer ID Installer: Fumihiko Takayama (G43BCU2T37)"
        ```

        Your codesign identity is `C86BB5F7830071C7B0B07D168A9A9375CC2D02C5` in the above case.

    4.  Set environment variable to use your codesign identity for installer signing.

        ```shell
        export PQRS_ORG_INSTALLER_CODE_SIGN_IDENTITY=C86BB5F7830071C7B0B07D168A9A9375CC2D02C5
        ```

3.  Build a package by executing the following command in Terminal.app.

    ```shell
    make package
    ```

    The `make` script will create a redistributable **Karabiner-Elements-VERSION.dmg** in the current directory.

#### Note about pre-built binaries in the source tree

Karabiner-Elements uses some pre-built binaries in the source tree.

- `vendor/Karabiner-DriverKit-VirtualHIDDevice/dist/Karabiner-DriverKit-VirtualHIDDevice-*.pkg` (the latest one)
- `Sparkle.framework` in `src/apps/SettingsWindow/`

The above `make package` command does not rebuild these binaries.<br/>
(These binaries will be copied in the distributed package.)

If you want to rebuild these binaries, you have to build them manually.<br/>
Please follow the instruction of these projects.
