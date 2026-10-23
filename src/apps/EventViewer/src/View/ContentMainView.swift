import SwiftUI

enum SidebarItem: String, CaseIterable, Identifiable, Hashable {
  case main
  case frontmostApplication
  case variables
  case devices
  case unknownEvents
  case settings

  var id: Self { self }

  var title: String {
    switch self {
    case .main: return "Main"
    case .frontmostApplication: return "Frontmost Application"
    case .variables: return "Variables"
    case .devices: return "Devices"
    case .unknownEvents: return "Unknown Events"
    case .settings: return "Settings"
    }
  }

  var systemImage: String {
    switch self {
    case .main: return "magnifyingglass"
    case .frontmostApplication: return "triangle.circle"
    case .variables: return "cube"
    case .devices: return "keyboard"
    case .unknownEvents: return "questionmark.square.dashed"
    case .settings: return "gear"
    }
  }
}

struct ContentMainView: View {
  @State private var selection: SidebarItem = .main

  var body: some View {
    NativeSidebarSplitView(
      sidebar: {
        List(SidebarItem.allCases, selection: $selection) { item in
          Label(item.title, systemImage: item.systemImage)
            .padding(.vertical, 8)
        }
        .listStyle(.sidebar)
      },
      detail: {
        switch selection {
        case .main:
          MainView()
        case .frontmostApplication:
          FrontmostApplicationView()
        case .variables:
          VariablesView()
        case .devices:
          DevicesView()
        case .unknownEvents:
          UnknownEventsView()
        case .settings:
          SettingsView()
        }
      }
    )
    .ignoresSafeArea(.container, edges: .top)
    .frame(
      minWidth: 1100,
      maxWidth: .infinity,
      minHeight: 650,
      maxHeight: .infinity)
  }
}
