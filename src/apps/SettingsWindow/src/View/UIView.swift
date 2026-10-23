import SwiftUI

struct UIView: View {
  @ObservedObject private var settings = LibKrbn.Settings.shared

  var body: some View {
    ScrollView {
      VStack(alignment: .leading, spacing: 24.0) {
        GroupBox(label: Text("Menu bar")) {
          VStack(alignment: .leading, spacing: 12.0) {
            Toggle(isOn: $settings.showIconInMenuBar) {
              Text("Show icon in menu bar (Default: on)")
            }
            .switchToggleStyle()

            Toggle(isOn: $settings.showProfileNameInMenuBar) {
              Text("Show profile name in menu bar (Default: off)")
            }
            .switchToggleStyle()

            Toggle(isOn: $settings.askForConfirmationBeforeQuitting) {
              Text("Ask for confirmation when quitting (Default: on)")
            }
            .switchToggleStyle()
          }
          .padding()
          .frame(maxWidth: .infinity, alignment: .leading)
        }

        GroupBox(label: Text("Karabiner Notification Window")) {
          VStack(alignment: .leading, spacing: 12.0) {
            Toggle(isOn: $settings.enableNotificationWindow) {
              Text("Enable Karabiner Notification Window (Default: on)")
            }
            .switchToggleStyle()

            Toggle(isOn: $settings.virtualHIDKeyboardIndicateStickyModifierKeysState) {
              Text("Indicate sticky modifier keys state (Default: on)")
            }
            .switchToggleStyle()

            VStack(alignment: .leading, spacing: 12.0) {
              Label(
                "What is the Karabiner Notification Window?\n\n"
                  + "Karabiner Notification Window is a window that displays messages, located at the bottom right of the screen."
                  + "It is used for temporary alerts, displaying the status of sticky modifiers, and showing messages for some complex modifications.",
                systemImage: InfoBorder.icon
              )

              Image(decorative: "notification-window")
                .resizable()
                .aspectRatio(contentMode: .fit)
                .frame(height: 100)
                .background(
                  RoundedRectangle(cornerRadius: 9)
                    .stroke(
                      Color(NSColor.separatorColor),
                      lineWidth: 4
                    )
                )
            }
            .modifier(InfoBorder())
          }
          .padding()
          .frame(maxWidth: .infinity, alignment: .leading)
        }


      }
      .padding()
    }
  }
}
