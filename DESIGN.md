---
name: BULLOADER+
description: The app as a precision instrument, one huge live count and one signal-orange action on a graphite or paper console.
colors:
  bg-dark: "#0b0c0e"
  bg-light: "#f6f4ef"
  surface-dark: "#131519"
  surface-light: "#fdfcf9"
  surface-2-dark: "#1b1e23"
  surface-2-light: "#efebe3"
  line-dark: "#262a30"
  line-light: "#dcd8cf"
  line-strong-dark: "#5c626b"
  line-strong-light: "#8c8a84"
  ink-dark: "#f2f3f5"
  ink-light: "#121316"
  ink-2-dark: "#b9bec6"
  ink-2-light: "#3d4148"
  ink-3-dark: "#959ba4"
  ink-3-light: "#5b6069"
  off-dark: "#7d838c"
  off-light: "#6c6f75"
  accent-dark: "#ff7a1f"
  accent-light: "#e65c00"
  accent-ink-dark: "#ff8a3a"
  accent-ink-light: "#a84300"
  on-accent: "#0b0c0e"
  on-tone: "#0b0c0e"
  slow: "#3fc6f2"
  slow-ink-light: "#00698f"
  ok: "#3ddc84"
  ok-ink-light: "#13773d"
  jam: "#ff4f8b"
  jam-ink-light: "#c2134f"
  warn: "#ffd23f"
  warn-ink-light: "#7a5a00"
typography:
  count:
    fontFamily: "Geist Mono, ui-monospace, SF Mono, Menlo, monospace"
    fontSize: "clamp(4.5rem, 28vw, 8rem)"
    fontWeight: 600
    lineHeight: 0.95
    letterSpacing: "-0.04em"
    fontFeature: "tnum"
  action:
    fontFamily: "Geist, system-ui, sans-serif"
    fontSize: "2.25rem"
    fontWeight: 700
    letterSpacing: "0.06em"
  wordmark:
    fontFamily: "Geist, system-ui, sans-serif"
    fontSize: "2.25rem"
    fontWeight: 700
    lineHeight: 1
    letterSpacing: "-0.03em"
  state:
    fontFamily: "Geist, system-ui, sans-serif"
    fontSize: "1.625rem"
    fontWeight: 650
    lineHeight: 1.15
    letterSpacing: "-0.02em"
  title:
    fontFamily: "Geist, system-ui, sans-serif"
    fontSize: "1.375rem"
    fontWeight: 650
    letterSpacing: "-0.02em"
  button:
    fontFamily: "Geist, system-ui, sans-serif"
    fontSize: "1.125rem"
    fontWeight: 600
    letterSpacing: "-0.01em"
  body:
    fontFamily: "Geist, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 500
    lineHeight: 1.4
  data:
    fontFamily: "Geist Mono, ui-monospace, SF Mono, Menlo, monospace"
    fontSize: "1.125rem"
    fontWeight: 600
    fontFeature: "tnum"
  label:
    fontFamily: "Geist Mono, ui-monospace, SF Mono, Menlo, monospace"
    fontSize: "0.8125rem"
    fontWeight: 500
    letterSpacing: "0.08em"
rounded:
  sm: "6px"
  md: "8px"
  dialog: "12px"
  switch: "16px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "24px"
  touch: "56px"
  action: "96px"
components:
  button-go:
    backgroundColor: "{colors.accent-dark}"
    textColor: "{colors.on-accent}"
    typography: "{typography.action}"
    rounded: "{rounded.md}"
    height: "96px"
    width: "100%"
  button-stop:
    backgroundColor: "{colors.ink-dark}"
    textColor: "{colors.bg-dark}"
    typography: "{typography.action}"
    rounded: "{rounded.md}"
    height: "96px"
    width: "100%"
  button-default:
    backgroundColor: "{colors.surface-2-dark}"
    textColor: "{colors.ink-dark}"
    typography: "{typography.button}"
    rounded: "{rounded.sm}"
    padding: "0 16px"
    height: "56px"
  button-primary:
    backgroundColor: "{colors.accent-dark}"
    textColor: "{colors.on-accent}"
    typography: "{typography.button}"
    rounded: "{rounded.sm}"
    padding: "0 16px"
    height: "56px"
  button-step:
    backgroundColor: "{colors.surface-2-dark}"
    textColor: "{colors.ink-dark}"
    rounded: "{rounded.sm}"
    height: "64px"
    width: "72px"
  chip-preset:
    backgroundColor: "{colors.surface-2-dark}"
    textColor: "{colors.ink-dark}"
    typography: "{typography.data}"
    rounded: "{rounded.sm}"
    height: "56px"
  field:
    backgroundColor: "{colors.bg-dark}"
    textColor: "{colors.ink-dark}"
    rounded: "{rounded.sm}"
    padding: "0 8px"
    height: "56px"
  panel:
    backgroundColor: "{colors.surface-dark}"
    rounded: "{rounded.md}"
    padding: "14px"
  dialog:
    backgroundColor: "{colors.surface-dark}"
    textColor: "{colors.ink-dark}"
    rounded: "{rounded.dialog}"
    padding: "20px"
---

# Design System: BULLOADER+

<!-- Scope: the app at /app/ (web/src/app.tsx, web/src/style.css). The Starlight docs site does not use this world yet; moving it over is planned. -->

## Overview

**Creative North Star: "The Field Instrument"**

The app is a measuring instrument, not a remote control. One number fills the screen: the count, in very large tabular mono, read from a metre away in the sun. Under the thumb sits one action, signal orange to start, solid ink to stop. Everything else is quiet: a graphite near-black ground in dark, a warm paper-white ground in light, hairline borders, tight corners, a faint drafting grid behind the header that fades out before the count.

The references are developer consoles like Neon and Supabase: flat panels, 1 px lines, mono for numbers and labels, one saturated accent. The world refuses the generic dark IoT remote with a stack of equal-weight cards. Hierarchy comes from size and position, not from boxes.

Both themes are first class. Auto (follow the phone) is the default; Réglages can pin Clair or Sombre. Every token has a light and a dark value, picked by the CSS `light-dark()` function, so a component is written once.

**Key Characteristics:**
- One giant mono count with "/ target" at half size, and a thin progress rule with a tick every tenth.
- One full-width 96 px action bar fixed at the bottom, in the thumb zone.
- Signal orange is the only action colour; state colours are reserved and always come with a glyph and a word.
- Hairline borders, 6-8 px corners, no decorative shadows.
- Motion is short, transform-only and means something: digits tick, the leading edge glows while the motor runs, the bar pulses once on done.
- Dark and light themes from one token set; Auto by default.

## Colors

A graphite or paper ground, three steps of ink, one orange that means "act", and four state colours that each mean exactly one thing.

### Primary
- **Signal Orange** (`accent-dark` / `accent-light`): the fill of GO and of primary buttons, the switch when on, and the running state. The airsoft orange tip. Text on it is always the near-black `on-accent`.
- **Signal Orange Ink** (`accent-ink-dark` / `accent-ink-light`): orange as text or stroke on the ground: focus rings, the selected chip's edge, the test-spin line, the caret, the « + » of the wordmark. Darker in light so it passes contrast on paper.
- **Orange Tint** (16% accent mixed into the surface): the fill of the selected preset chip and the selected segment.

### State colours
Each state has a bright fill (badges, rule edge, battery-low chip, with dark `on-tone` text) and an ink for text and strokes on the ground (the same bright value in dark, a deeper one in light).
- **Slowdown Cyan** (`slow`, `slow-ink-light`): ralentissement, the last BBs before the target.
- **Done Green** (`ok`, `ok-ink-light`): terminé, with a check. Green means done and nothing else; a healthy battery is neutral, not green.
- **Jam Magenta-Red** (`jam`, `jam-ink-light`): bourrage, errors, a lost link, an invalid field, with a warning triangle.
- **Battery Yellow** (`warn`, `warn-ink-light`): low battery (with the battery glyph), a link being restored, a clamped value note.

### Neutral
- **Graphite / Paper ground** (`bg-dark` / `bg-light`): the page, the bottom dock, the inside of fields. Also the browser bar colour (`theme-color`).
- **Surface** (`surface-*`): panels, the segmented control, the dialog.
- **Raised surface** (`surface-2-*`): default buttons, steppers, chips, the switch track.
- **Hairline** (`line-*`): panel borders, the rule track, dividers between settings rows.
- **Strong line** (`line-strong-*`): edges of controls (3:1 on the ground), rule ticks, disabled dashes.
- **Ink / Ink 2 / Ink 3** (`ink-*`, `ink-2-*`, `ink-3-*`): main text; secondary text and quiet buttons; labels, the "/ target", idle glyphs. All pass 4.5:1 on their ground.
- **Off** (`off-*`): text of disabled controls.

### Named Rules
**The One Orange Rule.** Orange means "act" or "acting": GO, the primary button, the selected choice, the switch on, and the running state that GO started. Nothing decorative is orange except the « + » of the wordmark.

**The Never Colour Alone Rule.** Every state colour comes with its glyph and its word (badge, banner, field error, battery chip). A colour-blind player in sunlight reads the word.

**The Reserved State Rule.** Cyan is slowdown, green is done, magenta-red is jam or error, yellow is low battery or a warning. Do not borrow them for anything else.

## Typography

**UI Font:** Geist (with system-ui, -apple-system, Segoe UI, Roboto)
**Mono Font:** Geist Mono (with ui-monospace, SF Mono, Menlo)

Both are variable woff2 files self-hosted in `web/public/fonts/` (SIL OFL), preloaded and precached by the service worker, so the field with no network gets the real fonts.

**Character:** Geist is the console voice, tight and neutral; Geist Mono carries everything measured: the count, the target, presets, battery, device name, units and small uppercase labels.

### Hierarchy
- **Count** (Mono 600, clamp(4.5rem, 28vw, 8rem), line-height 0.95, -0.04em, tabular): the live BB count. "/ target" is the same line at 0.5em, weight 500, in ink 3.
- **Action** (Geist 700, 2.25rem, +0.06em): GO and STOP. A mono uppercase sub-line (0.9375rem, +0.04em) under it.
- **Wordmark** (Geist 700, 2.25rem, -0.03em): BULLOADER with an orange « + », on the connect screen.
- **State** (Geist 650, 1.625rem, line-height 1.15, -0.02em): the state word in its badge.
- **Title** (Geist 650, 1.375rem, -0.02em): the Réglages header, dialog titles.
- **Button** (Geist 600, 1.125rem, -0.01em): default buttons; 1.25rem on the large Réglages buttons.
- **Body** (Geist 500, 1-1.0625rem, line-height 1.4): hints, notes, banners. Nothing smaller than 0.8125rem.
- **Data** (Mono 500-600, 1.125-1.375rem, tabular): battery, chips, fields (2rem for the big target field).
- **Label** (Mono 500, 0.8125rem, +0.08em, uppercase, ink 3): group titles and small labels.

### Named Rules
**The Numbers Are Mono Rule.** Any number the device measures or the player sets is in Geist Mono with tabular figures, so digits never shift as they change.

## Layout

A single column, at most 30rem wide, centred, with 1rem side gutters and safe-area insets. Spacing steps are 4, 8, 12, 16 and 24 px; panels pad 14 px inside.

The main screen reads top to bottom: a header row (device name in mono, battery chip, settings button), then the hero, which takes the free height (state badge, count, progress rule), then the target panel (stepper and four preset chips), then the dock. The dock is sticky at the bottom, edge to edge, with a hairline top border and the ground as its fill; it holds the one 96 px action and, when needed, a one-line hint above it.

Touch targets are 56 px at least (`--touch`). Steppers are 64 px tall, the big buttons in Réglages 64-72 px, GO and STOP 96 px. Lines that can appear (state sub-line, clamp note) keep their height reserved so the count does not jump; field errors take no room while empty.

**The Thumb Bar Rule.** The main action of a screen lives in the bottom dock, full width, 96 px tall. Only one main action is shown at a time: STOP while the motor turns, GO otherwise.

## Elevation & Depth

Flat. Depth comes from tonal steps (ground, surface, raised surface) and 1 px lines, not from shadows. There are three exceptions, each with a job:

### Shadow Vocabulary
- **Dialog lift** (`box-shadow: 0 1.5rem 3rem -1rem rgb(0 0 0 / 0.5)`, backdrop `rgb(0 0 0 / 0.65)`): the confirm dialog only.
- **Banner mask** (`box-shadow: 0 0 0 0.75rem var(--bg)`): a ring of ground colour that hides content scrolling under the sticky banner. Not a visible shadow.
- **State glow** (two-layer orange or cyan glow on the rule's leading edge; one green pulse on done): see Components.

### Named Rules
**The Glow Is State Rule.** Glow appears only to say what the machine is doing: the leading edge glows while the motor loads (running or slowdown) and the bar pulses once on done. Never as decoration, hover or emphasis.

## Shapes

Tight, technical corners: 6 px on controls (buttons, fields, chips, battery and pill badges), 8 px on panels, banners, the state badge and the 96 px action, 12 px on the dialog. The switch is fully round. The progress track is a 6 px rounded bar. Borders are 1 px everywhere; 2 px only on the test-spin state badge. A dashed border means "off": disabled buttons and fields.

## Components

### Buttons
- **Default:** raised surface, strong-line border, ink text, 56 px min height, 6 px corners. Hover (pointer devices only) lightens the border; press moves it down 1 px and scales to 0.99 in 120 ms.
- **Primary:** orange fill and border, near-black text. Hover mixes 12% ink into the orange.
- **GO:** the primary at 96 px, full width, 8 px corners, 2.25rem bold spaced caps, play glyph, mono sub-line.
- **STOP:** same size, the ground's opposite (ink fill, ground-coloured text) with a square glyph: the loudest thing on screen, never orange. In Réglages it sits idle as a default button and only turns ink while a test spin runs.
- **Quiet / Icon:** transparent, no fill; icon buttons keep a hairline border and a 56 px square.
- **Disabled:** no fill, dashed strong-line border, off text. Reads as "not now" in sunlight where a faded colour still looks live.
- **Focus:** 2 px orange-ink outline, 2 px offset, on every control.

### Stepper
Three columns: a 72 px minus, the big mono target field, a 72 px plus, all 64 px tall. Smaller mono steppers (56 px) in Réglages.

### Preset chips
Four equal chips in a row, mono 1.25rem tabular. The current one gets the orange tint fill, an orange-ink border plus a 1 px inset ring, and ink text.

### Segmented control (language, theme)
A surface track with a hairline border and 4 px inner padding; transparent segments in ink 2; the current segment takes the same orange tint and ring as a chip.

### Fields
Ground fill, strong-line border, mono centred tabular text. Focus: orange-ink border plus a 1 px ring (no outline). Invalid: jam-ink border and ring, with a field error line (glyph and words) under it. Disabled: dashed border, off text.

### Switch (Sens inversé)
A full-width row: the label on the left, a mono word (OUI / NON) and a 48 × 28 px switch on the right. Off is the raised surface with an ink-2 knob; on is an orange track with a near-black knob. The word carries the meaning.

### Badges
- **State badge:** 52 px tall, 8 px corners, the state's bright fill with dark text and its glyph; idle is the surface with a strong-line border and ink text; test spin is a transparent badge with a 2 px orange-ink border and orange text.
- **Battery chip:** mono percentage with a battery glyph, hairline border, neutral ink while fine; yellow ink when getting low; solid yellow with dark text when low; ink 2 on USB.
- **Pill:** the small state badge in the Réglages header, same colour logic as the state badge.

### Banners and alerts
Sticky at the top while the screen scrolls. A tint of the state colour (20% into the ground) with a state-ink border, a bold title with its glyph, a short note and two buttons. Yellow while the link is being restored, magenta-red once it is lost. While stale, the last known values stay on screen at 45% opacity in greyscale. The connect-screen alert is the same idea, a jam tint with a glyph and words.

### Dialog
The native `<dialog>` for "leave with unsaved changes": surface fill, strong-line border, 12 px corners, the one real shadow, 65% black backdrop. It fades and rises 8 px in over 180 ms. Actions are stacked full-width buttons.

### Progress rule (signature)
A 6 px track in hairline colour; the fill in the state's ink, grown with `scaleX` (160 ms linear); a 2 px leading edge that only shows while running or slowing down, with an orange or cyan glow; under it a row of eleven ticks, one every tenth, the 1st, 6th and 11th taller. Ticks the fill has passed take the state's ink. Entering done, the full green bar pulses once (700 ms).

### Count digits (signature)
Each digit that changes drops 0.12em into place in 90 ms, transform only, like a mechanical counter. Short on purpose: at ten BBs a second the units digit restarts every ~100 ms and must still read solid. Mono digits never change width, so nothing reflows. A count from a run made for another target dims to ink 3.

### Motion and haptics
One easing (`cubic-bezier(0.16, 1, 0.3, 1)`), 120-200 ms for state changes, 90 ms for digits, 700 ms for the done pulse. `prefers-reduced-motion: reduce` turns off every animation and transition. The phone buzzes once (150 ms) on done and three times (300/150/300 ms) on a jam.

## Do's and Don'ts

### Do:
- **Do** write every colour as one token with a light and a dark value (`light-dark()`), and test both themes plus Auto.
- **Do** pair every state colour with its glyph and its word.
- **Do** put the screen's one main action in the bottom dock, full width, 96 px.
- **Do** keep every touch target at 56 px or more and every text at 4.5:1 on its ground.
- **Do** set numbers in Geist Mono with tabular figures.
- **Do** animate with transform and opacity only, keep it under 200 ms for anything that repeats, and honour reduced motion.
- **Do** mark "off" with a dashed border and no fill, not with fading.

### Don't:
- **Don't** use orange for anything that is not an action, a selection, or the running state.
- **Don't** use green for "fine" (a healthy battery is neutral); green means done.
- **Don't** add glow or shadow for decoration; glow encodes state, the dialog is the only lifted surface.
- **Don't** stack equal-weight cards; the count and the action dominate, the rest is one quiet panel.
- **Don't** load fonts or anything else from the network; the app works offline.
- **Don't** let a line appearing or a digit changing move the count.
