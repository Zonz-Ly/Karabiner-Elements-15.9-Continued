import Foundation
import ServiceManagement

enum Subcommand: String {
  case registerCoreDaemons = "register-core-daemons"
  case unregisterCoreDaemons = "unregister-core-daemons"
  case coreDaemonsEnabled = "core-daemons-enabled"

  case unregisterLegacyCoreDaemon = "unregister-legacy-core-daemon"

  case status
  case running
}

RunLoop.main.perform {
  let coreDaemonServiceNames = [
    "org.pqrs.service.daemon.Karabiner-VirtualHIDDevice-Daemon",
    "org.pqrs.service.daemon.Karabiner-Core-Service",
  ]

  // Local ad-hoc builds use the package-owned LaunchDaemon for the core.
  // Registering it with SMAppService would restore its stale parent constraint.
  let localBuild = Bundle.main.object(forInfoDictionaryKey: "KELocalBuild") != nil
  let corePlist = "/Library/LaunchDaemons/org.pqrs.service.daemon.Karabiner-Core-Service.plist"
  let coreDaemons = coreDaemonServiceNames.filter {
    !localBuild || $0 != "org.pqrs.service.daemon.Karabiner-Core-Service"
  }.map {
    SMAppService.daemon(plistName: "\($0).plist")
  }

  var allServices: [SMAppService] = []
  for s in coreDaemons {
    allServices.append(s)
  }

  if CommandLine.arguments.count > 1 {
    let subcommand = CommandLine.arguments[1]

    switch Subcommand(rawValue: subcommand) {
    case .registerCoreDaemons:
      ServiceManagementHelper.register(services: coreDaemons)
      exit(0)

    case .unregisterCoreDaemons:
      ServiceManagementHelper.unregister(services: coreDaemons)
      exit(0)

    case .coreDaemonsEnabled:
      if ServiceManagementHelper.enabled(services: coreDaemons)
        && (!localBuild || FileManager.default.fileExists(atPath: corePlist)) {
        print("enabled")
        exit(0)
      } else {
        print("There are services that are not enabled")
        exit(1)
      }

    case .unregisterLegacyCoreDaemon:
      guard localBuild && geteuid() == 0 else { exit(1) }
      let legacy = SMAppService.daemon(plistName: "org.pqrs.service.daemon.Karabiner-Core-Service.plist")
      if legacy.status != .notRegistered && legacy.status != .notFound {
        do {
          try legacy.unregister()
        } catch {
          print("Unable to unregister legacy Core Service: \(error)")
          exit(1)
        }
      }
      exit(0)

    case .status:
      if localBuild {
        print("Core Service: package-owned LaunchDaemon (installed: \(FileManager.default.fileExists(atPath: corePlist)))")
      }
      ServiceManagementHelper.printStatuses(services: allServices)
      exit(0)

    case .running:
      var exitCode: Int32 = 0
      for n in coreDaemonServiceNames {
        n.withCString {
          if !libkrbn_services_daemon_running($0) {
            print("\(n) is not running")
            exitCode = 1
          }
        }
      }
      exit(exitCode)

    default:
      print("Unknown subcommand \(subcommand)")
      exit(1)
    }
  }

  print("Usage:")
  print("    'Karabiner-Elements Privileged Daemons v2' subcommand")
  print("")
  print("Subcommands:")
  print("    \(Subcommand.registerCoreDaemons.rawValue)")
  print("    \(Subcommand.unregisterCoreDaemons.rawValue)")
  print("    \(Subcommand.coreDaemonsEnabled.rawValue)")

  print("    \(Subcommand.status.rawValue)")
  print("    \(Subcommand.running.rawValue)")

  exit(0)
}

RunLoop.main.run()
