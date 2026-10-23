import SwiftUI

// Keep SwiftUI content, but let AppKit own sidebar collapse and its animation.
// Separate hosting controllers prevent a SwiftUI split-view layout transaction
// from propagating through both columns on every animation frame.
struct NativeSidebarSplitView<Sidebar: View, Detail: View>: NSViewControllerRepresentable {
  let sidebar: Sidebar
  let detail: Detail

  init(@ViewBuilder sidebar: () -> Sidebar, @ViewBuilder detail: () -> Detail) {
    self.sidebar = sidebar()
    self.detail = detail()
  }

  func makeNSViewController(context: Context) -> NSSplitViewController {
    let controller = NativeSidebarController()
    let sidebarController = NSHostingController(rootView: sidebar)
    let sidebarItem = NSSplitViewItem(sidebarWithViewController: sidebarController)
    sidebarItem.minimumThickness = 250
    sidebarItem.maximumThickness = 250
    sidebarItem.canCollapse = true
    sidebarItem.allowsFullHeightLayout = true
    sidebarItem.titlebarSeparatorStyle = .none
    controller.addSplitViewItem(sidebarItem)
    controller.addSplitViewItem(NSSplitViewItem(viewController: NSHostingController(rootView: detail)))
    return controller
  }

  func updateNSViewController(_ controller: NSSplitViewController, context: Context) {
    (controller.splitViewItems[0].viewController as? NSHostingController<Sidebar>)?.rootView = sidebar
    (controller.splitViewItems[1].viewController as? NSHostingController<Detail>)?.rootView = detail
  }
}

private final class NativeSidebarController: NSSplitViewController, NSToolbarDelegate {
  override func viewDidAppear() {
    super.viewDidAppear()
    guard let window = view.window else { return }
    let toolbar = NSToolbar(identifier: "KarabinerSidebarToolbar")
    toolbar.delegate = self
    toolbar.displayMode = .iconOnly
    window.styleMask.insert(.fullSizeContentView)
    window.titlebarAppearsTransparent = false
    window.toolbar = toolbar
  }

  func toolbarDefaultItemIdentifiers(_ toolbar: NSToolbar) -> [NSToolbarItem.Identifier] {
    [.toggleSidebar, .sidebarTrackingSeparator]
  }

  func toolbarAllowedItemIdentifiers(_ toolbar: NSToolbar) -> [NSToolbarItem.Identifier] {
    toolbarDefaultItemIdentifiers(toolbar)
  }

  func toolbar(_ toolbar: NSToolbar, itemForItemIdentifier identifier: NSToolbarItem.Identifier,
               willBeInsertedIntoToolbar flag: Bool) -> NSToolbarItem? {
    if identifier == .sidebarTrackingSeparator {
      return NSTrackingSeparatorToolbarItem(identifier: identifier, splitView: splitView, dividerIndex: 0)
    }
    if identifier == .toggleSidebar {
      let item = NSToolbarItem(itemIdentifier: identifier)
      item.label = "Toggle Sidebar"
      item.toolTip = "Show or hide sidebar"
      item.image = NSImage(systemSymbolName: "sidebar.left", accessibilityDescription: "Toggle Sidebar")
      item.target = self
      item.action = #selector(toggleSidebar(_:))
      return item
    }
    return nil
  }
}
