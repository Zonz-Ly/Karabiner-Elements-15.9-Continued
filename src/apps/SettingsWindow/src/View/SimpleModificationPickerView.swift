import SwiftUI

struct SimpleModificationPickerView: View {
  private(set) var categories: LibKrbn.SimpleModificationDefinitionCategories
  private(set) var label: String
  private(set) var action: (_ json: String) -> Void
  private(set) var showUnsafe: Bool

  var body: some View {
    Menu(label) {
      ForEach(categories.categories) { category in
        Menu {
          ForEach(category.entries) { e in
            if !e.unsafe || showUnsafe {
              Button(
                action: {
                  action(e.json)
                },
                label: {
                  Text(verbatim: selectionLabel(e.label, selected: e.label == label))
                })
            }
          }
        } label: {
          Text(verbatim: selectionLabel(category.name, selected: category.include(label: label)))
        }
      }
    }
    .frame(maxWidth: .infinity, alignment: .leading)
  }

  // macOS 27 can omit menu images; keep selection markers in the text.
  private func selectionLabel(_ label: String, selected: Bool) -> String {
    (selected ? "◉ " : "○ ") + label
  }
}
