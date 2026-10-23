# App icons

These three ICNS files are the source assets for this fork. Both Xcode project
specifications and the CLT builder use them directly; no icon-generation tool is
required.

| File | Applications |
| --- | --- |
| `KarabinerElements.icns` | Settings, Core Service, Menu, Notification Window, service managers |
| `KarabinerEventViewer.icns` | EventViewer |
| `MultitouchExtension.icns` | Multitouch Extension |

The application icon is selected by `CFBundleIconFile` at build time. There is no
runtime icon picker or Finder custom-icon helper. DriverKit's separately signed
upstream package is preserved as supplied.
