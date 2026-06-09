import SwiftUI

// MARK: - Color tokens

/// Semantic color tokens for the OS1 / Element Software design system.
///
/// Tokens are derived from `OS-1`'s canonical CSS variables. SwiftUI views
/// should reference these by role (`palette.surface`) rather than raw hex,
/// so swapping individual values doesn't ripple across the app.
struct OS1Palette: Sendable {
    // Cream / beige — the desk-and-wall background
    let bgCream: Color
    let bgBeige: Color

    // Coral — the warm-orange family (the OS1 viewport color is the hero)
    let coral: Color          // #c65a43 — the canonical viewport
    let coral500: Color       // #c1553d
    let coral400: Color       // #d87660
    let coral300: Color       // #e6ad86
    let coral600: Color       // #a84832 — deepest, hover/pressed

    // Warm tan icon family — for chrome on cream
    let iconStroke: Color
    let iconStrokeHover: Color
    let iconWarm: Color
    let iconTan: Color
    let iconCoral: Color
    let iconPurple: Color

    // On-coral text (the canonical OS1 text-on-viewport color)
    let onCoralPrimary: Color    // ~95% white
    let onCoralSecondary: Color  // ~70% white
    let onCoralMuted: Color      // ~50% white

    // On-cream text (warm browns that read on the bg, not pure black)
    let onCreamPrimary: Color
    let onCreamSecondary: Color
    let onCreamMuted: Color

    // Translucent overlays for glassy surfaces on coral
    let glassFill: Color
    let glassBorder: Color
    let glassFillHover: Color
    let glassBorderHover: Color

    // Subtle dark overlays for inset chips on coral
    let darkOverlay: Color

    // Accent / status hints
    let warning: Color
    let danger: Color
    let success: Color

    static let standard = OS1Palette(
        bgCream: Color(hex: 0xD9C9AD),
        bgBeige: Color(hex: 0xCFC0A6),

        coral:    Color(hex: 0xC65A43),
        coral500: Color(hex: 0xC1553D),
        coral400: Color(hex: 0xD87660),
        coral300: Color(hex: 0xE6AD86),
        coral600: Color(hex: 0xA84832),

        iconStroke:      Color(red: 160/255, green: 130/255, blue: 110/255, opacity: 0.90),
        iconStrokeHover: Color(red: 140/255, green: 100/255, blue:  80/255, opacity: 1.00),
        iconWarm:        Color(red: 180/255, green: 145/255, blue: 120/255, opacity: 0.85),
        iconTan:         Color(red: 165/255, green: 135/255, blue: 115/255, opacity: 0.80),
        iconCoral:       Color(hex: 0xC65A43),
        iconPurple:      Color(red: 150/255, green: 120/255, blue: 180/255, opacity: 0.85),

        onCoralPrimary:   .white.opacity(0.95),
        onCoralSecondary: .white.opacity(0.70),
        onCoralMuted:     .white.opacity(0.50),

        onCreamPrimary:   Color(red:  56/255, green:  40/255, blue:  30/255, opacity: 0.92),
        onCreamSecondary: Color(red:  72/255, green:  56/255, blue:  44/255, opacity: 0.72),
        onCreamMuted:     Color(red:  88/255, green:  72/255, blue:  60/255, opacity: 0.50),

        glassFill:        .white.opacity(0.10),
        glassBorder:      .white.opacity(0.30),
        glassFillHover:   .white.opacity(0.20),
        glassBorderHover: .white.opacity(0.50),

        darkOverlay:      Color(red:  40/255, green:  30/255, blue:  24/255, opacity: 0.18),

        warning:          Color(hex: 0xE2A042),
        danger:           Color(hex: 0xC65A43),  // re-uses the coral so errors blend into the palette
        success:          Color(hex: 0x7BA88E)
    )

    static let highContrast = OS1Palette(
        bgCream: Color(hex: 0x121212),
        bgBeige: Color(hex: 0x1A1A1A),

        coral:    Color(hex: 0x141414),
        coral500: Color(hex: 0x181818),
        coral400: Color(hex: 0x222222),
        coral300: Color(hex: 0x2E2E2E),
        coral600: Color(hex: 0x0A0A0A),

        iconStroke:      Color.white.opacity(0.88),
        iconStrokeHover: Color.white.opacity(1.00),
        iconWarm:        Color.white.opacity(0.80),
        iconTan:         Color.white.opacity(0.75),
        iconCoral:       Color.white.opacity(0.92),
        iconPurple:      Color.white.opacity(0.82),

        onCoralPrimary:   .white.opacity(0.96),
        onCoralSecondary: .white.opacity(0.78),
        onCoralMuted:     .white.opacity(0.55),

        onCreamPrimary:   .white.opacity(0.96),
        onCreamSecondary: .white.opacity(0.78),
        onCreamMuted:     .white.opacity(0.55),

        glassFill:        .white.opacity(0.08),
        glassBorder:      .white.opacity(0.22),
        glassFillHover:   .white.opacity(0.14),
        glassBorderHover: .white.opacity(0.36),

        darkOverlay:      Color.black.opacity(0.28),

        warning:          Color(hex: 0xF0B429),
        danger:           Color(hex: 0xFF6B6B),
        success:          Color(hex: 0x6BCB77)
    )
}

// MARK: - Typography roles

/// Typography roles for OS1. Each role wraps a SwiftUI `Font` plus the
/// tracking (letter-spacing) the OS-1 design system applies.
struct OS1Typography: Sendable {
    static let dmSans = "DMSans"           // PostScript family name (no space)
    static let dmSansSpaced = "DM Sans"    // Display family name (some macOS APIs use this)

    /// Cinematic outlined hero title. Used sparingly — the `Begin` screen
    /// pattern from OS-1's StartScene.
    let titleHero: OS1FontStyle
    /// Section headers — workspace name, page titles in the hero coral
    /// surface.
    let titleSection: OS1FontStyle
    /// Smaller heading — panel titles, host card headers.
    let titlePanel: OS1FontStyle
    /// Body paragraph copy.
    let body: OS1FontStyle
    /// Body emphasis (medium weight).
    let bodyEmphasis: OS1FontStyle
    /// Field/property labels above inputs and metadata.
    let label: OS1FontStyle
    /// Small uppercase status / hint / button-secondary text.
    let smallCaps: OS1FontStyle
    /// Status/console-style monospaced read-only text.
    let mono: OS1FontStyle
    /// "Element Software" — italic Arial 800/400 wordmark.
    let brandLockupName: OS1FontStyle
    /// "OS¹ · COMPUTER USE" — uppercase 8 px Arial 700 descriptor.
    let brandLockupDescriptor: OS1FontStyle

    static let standard = OS1Typography(
        titleHero: OS1FontStyle(
            font: .custom(OS1Typography.dmSans, size: 96, relativeTo: .largeTitle)
                .weight(.thin),
            tracking: 8,
            lineSpacing: 4
        ),
        titleSection: OS1FontStyle(
            font: .custom(OS1Typography.dmSans, size: 32, relativeTo: .largeTitle)
                .weight(.light),
            tracking: 1.5,
            lineSpacing: 2
        ),
        titlePanel: OS1FontStyle(
            font: .custom(OS1Typography.dmSans, size: 17, relativeTo: .title3)
                .weight(.regular),
            tracking: 0.6,
            lineSpacing: 1
        ),
        body: OS1FontStyle(
            font: .custom(OS1Typography.dmSans, size: 14, relativeTo: .body)
                .weight(.light),
            tracking: 0.4,
            lineSpacing: 2
        ),
        bodyEmphasis: OS1FontStyle(
            font: .custom(OS1Typography.dmSans, size: 14, relativeTo: .body)
                .weight(.medium),
            tracking: 0.4,
            lineSpacing: 2
        ),
        label: OS1FontStyle(
            font: .custom(OS1Typography.dmSans, size: 11, relativeTo: .caption)
                .weight(.regular),
            tracking: 1.4,
            lineSpacing: 0,
            transform: .uppercase
        ),
        smallCaps: OS1FontStyle(
            font: .custom(OS1Typography.dmSans, size: 11, relativeTo: .footnote)
                .weight(.regular),
            tracking: 1.6,
            lineSpacing: 0,
            transform: .uppercase
        ),
        mono: OS1FontStyle(
            font: .system(.caption, design: .monospaced).weight(.regular),
            tracking: 0,
            lineSpacing: 1
        ),
        brandLockupName: OS1FontStyle(
            font: Font.custom("Helvetica-BoldOblique", size: 18),  // resolved through fallback for Element/Software weights
            tracking: 0,
            lineSpacing: 0
        ),
        brandLockupDescriptor: OS1FontStyle(
            font: Font.custom("Helvetica-Bold", size: 8),
            tracking: 1.4,
            lineSpacing: 0,
            transform: .uppercase
        )
    )
}

/// A typography role bundles font + tracking + transform. Use
/// `Text("…").os1(theme.typography.body)` to apply.
struct OS1FontStyle: Sendable {
    enum Transform: Sendable {
        case none, uppercase, lowercase
    }

    let font: Font
    let tracking: CGFloat
    let lineSpacing: CGFloat
    let transform: Transform

    init(font: Font, tracking: CGFloat = 0, lineSpacing: CGFloat = 0, transform: Transform = .none) {
        self.font = font
        self.tracking = tracking
        self.lineSpacing = lineSpacing
        self.transform = transform
    }
}

// MARK: - Motion timing

/// Motion timing — kept as constants so animations land in Phase 5+
/// reading from the same source.
struct OS1Motion: Sendable {
    let fast: Double         // 300 ms — hover, click feedback
    let medium: Double       // 600 ms — scene fades, panel transitions
    let slow: Double         // 1200 ms — ambient, hero reveals

    static let standard = OS1Motion(fast: 0.3, medium: 0.6, slow: 1.2)
}

// MARK: - Theme bundle

struct OS1Theme: Sendable {
    var palette: OS1Palette
    var typography: OS1Typography
    var motion: OS1Motion

    static let standard = OS1Theme(
        palette: .standard,
        typography: .standard,
        motion: .standard
    )

    static let highContrast = OS1Theme(
        palette: .highContrast,
        typography: .standard,
        motion: .standard
    )
}

enum UIThemeStyle: String, Codable, CaseIterable, Identifiable {
    case standard
    case highContrast

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .standard: "Original"
        case .highContrast: "High contrast"
        }
    }

    var resolved: OS1Theme {
        switch self {
        case .standard: .standard
        case .highContrast: .highContrast
        }
    }
}

// MARK: - Environment integration

private struct OS1ThemeKey: EnvironmentKey {
    static let defaultValue: OS1Theme = .standard
}

extension EnvironmentValues {
    var os1Theme: OS1Theme {
        get { self[OS1ThemeKey.self] }
        set { self[OS1ThemeKey.self] = newValue }
    }
}

extension View {
    /// Applies the standard OS1 theme to a subtree.
    func os1Theme(_ theme: OS1Theme = .standard) -> some View {
        environment(\.os1Theme, theme)
    }

    /// Applies an `OS1FontStyle` (font + tracking + transform).
    func os1Style(_ style: OS1FontStyle) -> some View {
        modifier(OS1FontStyleModifier(style: style))
    }
}

private struct OS1FontStyleModifier: ViewModifier {
    let style: OS1FontStyle

    func body(content: Content) -> some View {
        let base = content
            .font(style.font)
            .tracking(style.tracking)
            .lineSpacing(style.lineSpacing)

        switch style.transform {
        case .none:
            base
        case .uppercase:
            base.textCase(.uppercase)
        case .lowercase:
            base.textCase(.lowercase)
        }
    }
}

extension Text {
    /// Apply font + tracking from an `OS1FontStyle` directly to a `Text`.
    /// Use `.os1Style(_:)` on the parent view for full styling including
    /// case transforms.
    func os1(_ style: OS1FontStyle) -> Text {
        self
            .font(style.font)
            .tracking(style.tracking)
    }
}

// MARK: - Color hex helper

extension Color {
    /// `Color(hex: 0xC65A43)` for terse palette declarations.
    init(hex: UInt32, opacity: Double = 1.0) {
        let r = Double((hex >> 16) & 0xFF) / 255.0
        let g = Double((hex >>  8) & 0xFF) / 255.0
        let b = Double((hex >>  0) & 0xFF) / 255.0
        self.init(.sRGB, red: r, green: g, blue: b, opacity: opacity)
    }
}
