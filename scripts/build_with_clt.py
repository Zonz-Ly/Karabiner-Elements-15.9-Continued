#!/usr/bin/env python3
"""Build a local Karabiner 15.9 fork with CLT and existing 15.9 resources.

No Xcode, XcodeGen, actool or SwiftPM build system is invoked. Only Resources
directories are reused; executables, service plists and app metadata are built
from this checkout. See BUILDING-CLT.zh-TW.md for prerequisites and limitations.
"""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import plistlib
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SUPPORT = Path('Library/Application Support/org.pqrs/Karabiner-Elements')
PACKAGES = {
    'swift-collections': ('https://github.com/apple/swift-collections', '1.1.4', '671108c96644956dddcd89dd59c203dcdb36cec7'),
    'swift-async-algorithms-1.0.4': ('https://github.com/apple/swift-async-algorithms', '1.0.4', '042e1c4d9d19748c9c228f8d4ebc97bb1e339b0b'),
    'Highlightr': ('https://github.com/raspu/Highlightr', '2.1.2', '93199b9e434f04bda956a613af8f571933f9f037'),
    'CodeEditor': ('https://github.com/ZeeZide/CodeEditor', '1.2.6', 'f5c076b94f4ceb05abff88ba91d75a8d57143f0c'),
    'SettingsAccess': ('https://github.com/orchetect/SettingsAccess', '2.1.0', '08e80c35501f273afa2f5d6f737429bbe395ff81'),
}


def capture(cmd):
    return subprocess.check_output([str(x) for x in cmd], cwd=ROOT, text=True).strip()


def write_if_changed(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.read_text() != data:
        path.write_text(data)


class Builder:
    def __init__(self, args):
        self.args = args
        self.out = args.build_dir.resolve()
        self.out.mkdir(parents=True, exist_ok=True)
        stage_name = 'karabiner-clt-' + hashlib.sha256(str(self.out).encode()).hexdigest()[:12]
        self.stage = (args.staging_dir or Path(tempfile.gettempdir()) / stage_name).resolve()
        self.logs = self.out / 'logs'
        self.logs.mkdir(exist_ok=True)
        self.modules = self.out / 'modules'
        self.modules.mkdir(exist_ok=True)
        self.deps = args.dependencies.resolve()
        self.arch = args.arch
        self.sdk = Path(capture(['xcrun', '--sdk', 'macosx', '--show-sdk-path']))
        self.swiftc = capture(['xcrun', '--find', 'swiftc'])
        self.clang = capture(['xcrun', '--find', 'clang'])
        self.clangxx = capture(['xcrun', '--find', 'clang++'])
        self.libtool = capture(['xcrun', '--find', 'libtool'])
        self.target = self.arch + '-apple-macosx13.0'
        self.version = (ROOT / 'version').read_text().strip()
        self.manifest = {'version': self.version, 'architecture': self.arch,
                         'sdk': str(self.sdk), 'swift': capture([self.swiftc, '--version']),
                         'resource_root': str(args.resource_root.resolve()),
                         'resources': {}, 'targets': {}, 'dependencies': PACKAGES}
        # Some CLT 16.2 installations contain both module maps with an identical
        # SwiftBridging declaration. Hide only the duplicate through a local VFS
        # overlay, leaving the installed toolchain untouched.
        self.swift_flags = []
        include = Path(self.swiftc).parent.parent / 'include/swift'
        maps = [include / 'module.modulemap', include / 'bridging.modulemap']
        if all(p.exists() and 'module SwiftBridging' in p.read_text() for p in maps):
            empty = self.out / 'empty.modulemap'
            empty.write_text('')
            overlay = self.out / 'modulemap-overlay.json'
            overlay.write_text(json.dumps({'version': 0, 'case-sensitive': 'false',
                'use-external-names': False, 'roots': [{'type': 'file',
                'name': str(maps[0]), 'external-contents': str(empty)}]}))
            self.swift_flags += ['-vfsoverlay', str(overlay)]
        self.swift_base = [self.swiftc, '-sdk', str(self.sdk), '-target', self.target,
                           '-module-cache-path', str(self.out / 'module-cache'),
                           *self.swift_flags, '-I', str(self.modules), '-O']
        headers = hashlib.sha256()
        for folder in ('src/share', 'src/lib/libkrbn/include',
                       'vendor/vendor/include', 'vendor/Karabiner-DriverKit-VirtualHIDDevice/include'):
            for path in sorted((ROOT / folder).rglob('*')):
                if path.is_file() and path.suffix in ('.h', '.hpp', '.hxx', '.inc', '.ipp'):
                    headers.update(str(path.relative_to(ROOT)).encode())
                    headers.update(path.read_bytes())
        self.headers = headers.hexdigest()

    def run(self, cmd, label):
        cmd = [str(x) for x in cmd]
        log = self.logs / (re.sub(r'[^A-Za-z0-9_.-]', '_', label) + '.log')
        with log.open('w') as f:
            f.write(json.dumps(cmd) + '\n')
            f.flush()
            result = subprocess.run(cmd, cwd=ROOT, stdout=f, stderr=subprocess.STDOUT)
        if result.returncode:
            print(log.read_text()[-12000:], file=sys.stderr)
            raise RuntimeError(f'{label} failed ({result.returncode}); log: {log}')

    def compile(self, cmd, output, sources, label):
        digest = hashlib.sha256(json.dumps([str(x) for x in cmd]).encode())
        digest.update(self.manifest['swift'].encode())
        digest.update(self.headers.encode())
        for source in sorted(set(sources)):
            digest.update(str(source).encode())
            digest.update(source.read_bytes())
        module_dependencies = {
            'InternalCollectionsUtilities': [], 'DequeModule': ['InternalCollectionsUtilities'],
            'OrderedCollections': ['InternalCollectionsUtilities', 'DequeModule'],
            'AsyncAlgorithms': ['InternalCollectionsUtilities', 'DequeModule', 'OrderedCollections'],
            'Highlightr': [], 'CodeEditor': ['Highlightr'], 'SettingsAccess': [],
        }
        required = None
        if '-emit-library' in cmd and '-module-name' in cmd:
            required = module_dependencies[cmd[cmd.index('-module-name') + 1]]
        for path in sorted(self.modules.glob('*.a')):
            if required is not None and path.stem.removeprefix('lib') not in required:
                continue
            digest.update(str((path.name, path.stat().st_mtime_ns)).encode())
        stamp = output.with_suffix(output.suffix + '.sha256')
        key = digest.hexdigest()
        if output.exists() and stamp.exists() and stamp.read_text() == key:
            print('Cached ' + label, flush=True)
            return
        output.parent.mkdir(parents=True, exist_ok=True)
        print('Building ' + label, flush=True)
        self.run(cmd, label)
        stamp.write_text(key)

    def dependencies(self):
        self.deps.mkdir(parents=True, exist_ok=True)
        for name, (url, tag, commit) in PACKAGES.items():
            folder = self.deps / name
            if not folder.exists():
                self.run(['git', 'clone', '--depth', '1', '--branch', tag, url, folder], 'fetch-' + name)
            actual = capture(['git', '-C', folder, 'rev-parse', 'HEAD'])
            dirty = capture(['git', '-C', folder, 'status', '--porcelain', '--untracked-files=no'])
            if actual != commit or dirty:
                raise RuntimeError(f'{folder}: expected clean {tag} ({commit}), got {actual}')
        accessor = self.out / 'Highlightr-resource-accessor.swift'
        write_if_changed(accessor, '''import Foundation
extension Bundle {
  static let module: Bundle = {
    guard let url = Bundle.main.resourceURL?.appendingPathComponent("Highlightr_Highlightr.bundle"),
          let bundle = Bundle(url: url) else {
      fatalError("Missing Highlightr_Highlightr.bundle")
    }
    return bundle
  }()
}
''')
        plans = [
            ('InternalCollectionsUtilities', 'swift-collections/Sources/InternalCollectionsUtilities', []),
            ('DequeModule', 'swift-collections/Sources/DequeModule', []),
            ('OrderedCollections', 'swift-collections/Sources/OrderedCollections', []),
            ('AsyncAlgorithms', 'swift-async-algorithms-1.0.4/Sources/AsyncAlgorithms',
             ['-enable-experimental-feature', 'AvailabilityMacro=AsyncAlgorithms 1.0:macOS 10.15, iOS 13.0, tvOS 13.0, watchOS 6.0']),
            ('Highlightr', 'Highlightr/Pod/Classes', ['-DSWIFT_PACKAGE', str(accessor)]),
            ('CodeEditor', 'CodeEditor/Sources/CodeEditor', []),
            ('SettingsAccess', 'SettingsAccess/Sources/SettingsAccess', []),
        ]
        for name, path, flags in plans:
            sources = sorted((self.deps / path).rglob('*.swift'))
            output = self.modules / ('lib' + name + '.a')
            cmd = self.swift_base + ['-swift-version', '5', '-parse-as-library',
                '-package-name', 'karabiner_clt', '-module-name', name, '-emit-library',
                '-static', '-emit-module', '-emit-module-path', str(self.modules / (name + '.swiftmodule')),
                *flags, '-o', str(output), *map(str, sources)]
            self.compile(cmd, output, sources + ([accessor] if name == 'Highlightr' else []), name)

    def spec(self, path):
        data = json.loads(capture(['ruby', '-ryaml', '-rjson', '-e',
            'puts JSON.generate(YAML.load_file(ARGV[0]))', path]))
        return next(iter(data['targets'].items()))

    def build_target(self, spec):
        name, target = self.spec(spec)
        settings = target.get('settings', {})
        settings = settings.get('base', settings)
        module = re.sub(r'[^A-Za-z0-9_]', '_', name)
        folder = spec.parent
        objdir = self.out / 'objects' / module
        objdir.mkdir(parents=True, exist_ok=True)
        sources = []
        for item in target.get('sources', []):
            path = folder / (item if isinstance(item, str) else item['path'])
            sources += list(path.rglob('*')) if path.is_dir() else [path]
        native = sorted(set(p.resolve() for p in sources if p.suffix in ('.c', '.cpp', '.m', '.mm')))
        swift = sorted(set(p.resolve() for p in sources if p.suffix == '.swift'))
        incs = []
        for key, flag in [('HEADER_SEARCH_PATHS', '-I'), ('SYSTEM_HEADER_SEARCH_PATHS', '-isystem')]:
            for inc in settings.get(key, []):
                incs += [flag, str((folder / inc).resolve())]
        bridge = settings.get('SWIFT_OBJC_BRIDGING_HEADER')
        if isinstance(bridge, list):
            bridge = bridge[0]
        swift_incs = [part for inc in incs for part in ('-Xcc', inc)]
        if bridge:
            swift_incs += ['-import-objc-header', str((folder / bridge).resolve())]
        objects = []
        if swift:
            swiftobj = objdir / 'swift.o'
            cmd = self.swift_base + ['-swift-version', str(settings.get('SWIFT_VERSION', '5')).split('.')[0],
                '-warnings-as-errors', '-whole-module-optimization', '-emit-object',
                '-module-name', module, *swift_incs, '-o', str(swiftobj), *map(str, swift)]
            if not any(p.name == 'main.swift' for p in swift):
                cmd += ['-parse-as-library']
            self.compile(cmd, swiftobj, swift + ([folder / bridge] if bridge else []), module + '-swift')
            objects.append(swiftobj)
        for index, source in enumerate(native):
            output = objdir / f'{index}-{source.stem}.o'
            cpp = source.suffix in ('.cpp', '.mm')
            cmd = [self.clangxx if cpp else self.clang, '-isysroot', str(self.sdk),
                   '-target', self.target, '-O2', '-Wall', '-fmodules',
                   '-fmodules-cache-path=' + str(self.out / 'clang-cache'), *incs]
            # The Xcode specs apply -Werror to our sources, not vendored C.
            if source.is_relative_to(ROOT / 'src'):
                cmd.insert(cmd.index('-fmodules'), '-Werror')
            if cpp:
                cmd += ['-std=c++20']
            if source.suffix in ('.m', '.mm'):
                cmd += ['-fobjc-arc']
            cmd += ['-c', str(source), '-o', str(output)]
            headers = [p for base in ('include', 'src') for p in (folder / base).rglob('*')
                       if p.is_file() and p.suffix in ('.h', '.hpp', '.hxx', '.inc', '.ipp')]
            if source.suffix == '.c':
                headers += list((ROOT / 'vendor/duktape-2.7.0').rglob('*.h'))
            self.compile(cmd, output, [source, *headers], module + '-' + source.name)
            objects.append(output)
        islib = target['type'] == 'library.static'
        executable = self.out / 'products' / ('libkrbn.a' if islib else module)
        if islib:
            cmd = [self.libtool, '-static', '-o', executable, *objects]
        else:
            cmd = self.swift_base + ['-o', str(executable), *map(str, objects),
                 '-L', str(self.modules), '-L', str(self.out / 'products'), '-lc++',
                 '-Xlinker', '-dead_strip']
            if settings.get('OTHER_LDFLAGS'):
                cmd += ['-lkrbn']
            deps = target.get('dependencies', [])
            packages = {d.get('package') for d in deps}
            if 'AsyncAlgorithms' in packages:
                cmd += ['-lAsyncAlgorithms', '-lOrderedCollections', '-lDequeModule', '-lInternalCollectionsUtilities']
            if 'CodeEditor' in packages:
                cmd += ['-lCodeEditor', '-lHighlightr']
            if 'SettingsAccess' in packages:
                cmd += ['-lSettingsAccess']
            frameworks = {'AppKit', 'Foundation', 'IOKit', 'Carbon', 'Security', 'SystemConfiguration',
                          'ApplicationServices', 'CoreServices', 'ServiceManagement'}
            for dep in deps:
                value = dep.get('framework', dep.get('sdk', ''))
                if value.endswith('.framework'):
                    frameworks.add(Path(value).stem)
                    if value.startswith('/'):
                        cmd += ['-F', str(Path(value).parent)]
            for framework in sorted(frameworks):
                cmd += ['-framework', framework]
        link_inputs = objects + ([self.out / 'products/libkrbn.a'] if settings.get('OTHER_LDFLAGS') else [])
        self.compile(cmd, executable, link_inputs, module + '-link')
        if not islib:
            self.run(['codesign', '--force', '--sign', '-', executable], module + '-sign-binary')
        self.manifest['targets'][name] = str(executable)
        if target['type'] == 'application':
            self.bundle(name, target, settings, folder, executable)
        return executable

    def bundle(self, name, target, settings, folder, executable):
        rel = Path('Applications') if name in ('Karabiner-Elements', 'Karabiner-EventViewer') else SUPPORT
        source = self.args.resource_root / rel / (name + '.app')
        source_info = plistlib.loads((source / 'Contents/Info.plist').read_bytes())
        source_version = source_info.get('CFBundleShortVersionString')
        if source_version != '15.9.0' and not (
                source_version == self.version and source_info.get('KELocalBuild')):
            raise RuntimeError(f'{source} is neither 15.9.0 nor this version of the local fork')
        dest = self.stage / rel / (name + '.app')
        contents = dest / 'Contents'
        if dest.exists():
            shutil.rmtree(dest)
        (contents / 'MacOS').mkdir(parents=True)
        original_resources = source / 'Contents/Resources'
        if original_resources.exists():
            shutil.copytree(original_resources, contents / 'Resources', symlinks=True)
            for path in sorted(original_resources.rglob('*')):
                if path.is_file():
                    self.manifest['resources'][str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
        for obsolete in [contents / 'Resources/app.icns', contents / 'Resources/icons']:
            if obsolete.is_dir():
                shutil.rmtree(obsolete)
            elif obsolete.exists():
                obsolete.unlink()
        for obsolete in (contents / 'Resources').glob('00[0-2]-*'):
            obsolete.unlink()
        text = (folder / 'Resources/Info.plist.in').read_text()
        variables = {'DEVELOPMENT_LANGUAGE': 'en', 'EXECUTABLE_NAME': name,
                     'PRODUCT_BUNDLE_IDENTIFIER': settings['PRODUCT_BUNDLE_IDENTIFIER'],
                     'PRODUCT_NAME': name, 'PRODUCT_BUNDLE_PACKAGE_TYPE': 'APPL',
                     'MACOSX_DEPLOYMENT_TARGET': str(target['deploymentTarget'])}
        text = text.replace('@VERSION@', self.version)
        for key, value in variables.items():
            text = text.replace('$(' + key + ')', value)
        if '$(' in text:
            raise RuntimeError(f'Unexpanded variable in {name} Info.plist')
        info = plistlib.loads(text.encode())
        info['KELocalBuild'] = 'CLT; local fork; updater removed'
        icon_name = {'Karabiner-EventViewer': 'KarabinerEventViewer.icns',
                     'Karabiner-MultitouchExtension': 'MultitouchExtension.icns'}.get(
                         name, 'KarabinerElements.icns')
        icon = ROOT / 'files/icons' / icon_name
        if not icon.is_file():
            raise RuntimeError(f'Missing application icon: {icon}')
        shutil.copy2(icon, contents / 'Resources' / icon.name)
        info['CFBundleIconFile'] = icon.name
        info.pop('CFBundleIconName', None)
        self.manifest.setdefault('local_icons', {})[name] = hashlib.sha256(icon.read_bytes()).hexdigest()
        (contents / 'Info.plist').write_bytes(plistlib.dumps(info))
        shutil.copy2(executable, contents / 'MacOS' / name)
        for kind in ['LaunchAgents', 'LaunchDaemons']:
            plists = list((folder / kind).glob('*.plist'))
            if kind == 'LaunchDaemons' and plists:
                plists += list((ROOT / 'vendor/Karabiner-DriverKit-VirtualHIDDevice/files/LaunchDaemons').glob('*.plist'))
            for path in plists:
                to = contents / 'Library' / kind
                to.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, to / path.name)
        # Finder custom icons in an installed app can add metadata that codesign
        # rejects. Clean metadata only on the copied, locally built app.
        self.run(['/usr/bin/xattr', '-cr', dest], name + '-clean-build-metadata')
        self.run(['codesign', '--force', '--deep', '--sign', '-', dest], name + '-sign-app')
        self.run(['codesign', '--verify', '--deep', '--strict', dest], name + '-verify-app')

    def package(self):
        stage = self.stage
        support = stage / SUPPORT
        support.mkdir(parents=True, exist_ok=True)
        for path in ['version', 'src/scripts/uninstall.sh', 'src/scripts/uninstall_core.sh',
                     'src/scripts/repair.sh', 'files/complex_modifications_rules_example.json']:
            source = ROOT / path
            shutil.copy2(source, support / ('package-version' if path == 'version' else source.name))
        for name in ['copy_current_profile_to_system_default_profile.applescript',
                     'remove_system_default_profile.applescript', 'uninstaller.applescript']:
            to = support / 'scripts'
            to.mkdir(exist_ok=True)
            shutil.copy2(ROOT / 'src/scripts' / name, to / name)
        for name in ['karabiner_cli', 'karabiner_console_user_server', 'karabiner_session_monitor']:
            to = support / 'bin'
            to.mkdir(exist_ok=True)
            shutil.copy2(self.out / 'products' / name, to / name)
        # Keep the original driver installer byte-for-byte, including Apple's
        # approved DriverKit entitlements and the upstream Developer ID signature.
        driver = ROOT / 'vendor/Karabiner-DriverKit-VirtualHIDDevice/dist/Karabiner-DriverKit-VirtualHIDDevice-6.8.0.pkg'
        self.manifest['driver_sha256'] = hashlib.sha256(driver.read_bytes()).hexdigest()
        parts = self.out / 'package-parts'
        parts.mkdir(exist_ok=True)
        (parts / 'Installer.pkg').unlink(missing_ok=True)
        self.run(['pkgbuild', '--root', stage, '--component-plist', ROOT / 'pkginfo/pkgbuild.plist',
            '--scripts', ROOT / 'pkginfo/Scripts', '--identifier', 'org.pqrs.Karabiner-Elements',
            '--version', self.version, '--install-location', '/', parts / 'Installer.pkg'], 'pkgbuild')
        shutil.copy2(driver, parts / 'Karabiner-DriverKit-VirtualHIDDevice.pkg')
        distribution = (ROOT / 'pkginfo/Distribution.xml').read_text().replace(
            'hostArchitectures="x86_64,arm64"', f'hostArchitectures="{self.arch}"')
        distribution = re.sub(r'<title>[^<]+</title>',
            f"<title>Karabiner-Elements {self.version} (Zonz's fork)</title>", distribution)
        (parts / 'Distribution.xml').write_text(distribution)
        release = self.out / 'release'
        release.mkdir(exist_ok=True)
        for stale in release.glob(f'Karabiner-Elements-*-backports-{self.arch}.pkg'):
            if stale.name != f'Karabiner-Elements-{self.version}-backports-{self.arch}.pkg':
                stale.unlink()
        pkg = release / f'Karabiner-Elements-{self.version}-backports-{self.arch}.pkg'
        pkg.unlink(missing_ok=True)
        self.run(['productbuild', '--distribution', parts / 'Distribution.xml',
                  '--package-path', parts, pkg], 'productbuild')
        self.save_manifest()
        shutil.copy2(self.out / 'build-manifest.json', release / 'build-manifest.json')
        if self.args.dmg:
            dmg = self.out / f'Karabiner-Elements-{self.version}-backports-{self.arch}.dmg'
            self.run(['hdiutil', 'create', '-ov', '-nospotlight', '-srcfolder', release,
                      '-volname', 'Karabiner-Elements local backports', '-format', 'UDZO', dmg], 'hdiutil')
        print('Installer: ' + str(pkg), flush=True)

    def save_manifest(self):
        (self.out / 'build-manifest.json').write_text(json.dumps(self.manifest, indent=2) + '\n')

    def build(self):
        self.run([sys.executable, ROOT / 'scripts/check_build_environment.py', '--compiler-only'], 'preflight')
        self.run([sys.executable, ROOT / 'scripts/update_version.py'], 'update-version')
        for name in ['Karabiner-AppIconSwitcher', 'Karabiner-Updater']:
            obsolete = self.stage / SUPPORT / (name + '.app')
            if obsolete.exists():
                shutil.rmtree(obsolete)
        self.dependencies()
        specs = [ROOT / 'src/lib/libkrbn/project.yml']
        specs += sorted(ROOT.glob('src/apps/*/project.yml'))
        specs += sorted(ROOT.glob('src/core/*/project.yml'))
        specs += [ROOT / 'src/bin/cli/project.yml']
        for spec in specs:
            self.build_target(spec)
            self.save_manifest()
        if self.args.package:
            self.package()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-dir', type=Path, default=ROOT / 'build-clt')
    parser.add_argument('--dependencies', type=Path, default=ROOT / 'build-clt/dependencies')
    parser.add_argument('--staging-dir', type=Path,
                        help='app assembly directory (defaults to local temporary storage to avoid file-provider metadata)')
    parser.add_argument('--resource-root', type=Path, default=Path('/'),
                        help='root containing the official 15.9 apps under Applications/Library')
    parser.add_argument('--arch', choices=['arm64', 'x86_64'], default=platform.machine())
    parser.add_argument('--package', action='store_true')
    parser.add_argument('--dmg', action='store_true')
    args = parser.parse_args()
    if args.dmg:
        args.package = True
    try:
        Builder(args).build()
    except (RuntimeError, subprocess.CalledProcessError, FileNotFoundError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
