VERSION = `head -n 1 version`

all:
	@echo "Read a document at the following URL to build a distributable package."
	@echo "https://github.com/pqrs-org/Karabiner-Elements/#how-to-build"

package: check-build-environment
	$(MAKE) clean
	./make-package.sh
	$(MAKE) clean-launch-services-database

build: check-build-environment
	$(MAKE) -C src

.PHONY: check-build-environment check-compiler-environment build-clt package-clt
build-clt:
	/usr/bin/python3 scripts/build_with_clt.py $(CLT_BUILD_ARGS)

package-clt:
	/usr/bin/python3 scripts/build_with_clt.py --package --dmg $(CLT_BUILD_ARGS)

check-build-environment:
	/usr/bin/python3 scripts/check_build_environment.py

check-compiler-environment:
	/usr/bin/python3 scripts/check_build_environment.py --compiler-only

clean:
	$(MAKE) -C src clean
	$(MAKE) -C tests clean
	rm -rf pkgroot
	rm -f *.dmg

clean-launch-services-database:
	$(MAKE) -C tools/clean-launch-services-database

gitclean:
	git clean -f -x -d
	(cd vendor/cpm-cmake-package-lock && git clean -f -x -d)
	(cd vendor/Karabiner-DriverKit-VirtualHIDDevice && git clean -f -x -d)

notarize:
	xcrun notarytool \
		submit Karabiner-Elements-$(VERSION).dmg \
		--keychain-profile "pqrs.org notarization" \
		--wait
	$(MAKE) staple
	say "notarization completed"

staple:
	xcrun stapler staple Karabiner-Elements-$(VERSION).dmg

swift-format:
	find src/apps -name '*.swift' -print0 | xargs -0 swift-format -i

swiftlint:
	swiftlint

notarized-dmg: package notarize
