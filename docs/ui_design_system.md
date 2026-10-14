# UI Design System

The screen is plain Tkinter with ttk (no new library). All styling is centralised in two files.

| File | Role |
|---|---|
| `app/theme.py` | Colour palette, font helper, spacing scale, status colours, and the one-time ttk style set-up (`apply_theme`) |
| `app/widgets.py` | Reusable widgets: `Btn`, `Panel`, `DataTable`, `OccupancyTable`, `KpiCard`, `NavBar`, `StatusBar`, `ResultBox`, `Pill`, `Pick`, `draw_bar_chart` |
| `app/gui.py` | Arranges the pages and connects buttons to `app/services.py`. Business logic is unchanged |

## Palette

| Use | Colour |
|---|---|
| Header, table headings | Navy `#17263C` |
| Navigation bar | Secondary navy `#22344D` |
| Primary actions, selected tab | Teal `#117C78` (hover `#0D625F`) |
| Workspace / panels | `#F3F6FA` / `#FFFFFF` |
| Text / secondary text | `#202B3C` / `#65748B` |
| Borders, zebra rows | `#DCE3EC`, `#F7F9FC` |
| Highlight (rare: logo accent, peak-hour bar) | Yellow `#F2B705` |
| Success, warning, error, info | `#198754`, `#D97706`, `#DC3545`, `#3478F6` |

## Rules used on every screen

- **Buttons:** teal = main action, white = secondary, red = destructive (delete, cancel), plain text = clear. Rounded, with hover, pressed, focus and disabled states.
- **Inputs:** same height, grey border that turns teal on focus, label above the field.
- **Tables:** navy header, zebra rows, hover and selected highlight, numbers right-aligned, ids and statuses centred, empty-state message, scroll bar only when needed.
- **Status colours in tables:** ACTIVE green tint, PARTIAL and MAINTENANCE amber tint, UNPAID red tint, EXPIRED grey, CANCELLED grey with strike-through. Each status also has a dot and its word, so colour is never the only signal.
- **Messages:** green bar for success, red for errors, shown in the status bar and, on the Gate and Reservations pages, in a result box.
- **Spacing:** 4, 8, 12, 16, 24 px scale (`T.XS` to `T.XL`).

## Changing the look

Edit the constants at the top of `app/theme.py` (colours, fonts, row height). Every screen follows.
The font is Segoe UI on Windows; other systems fall back to the first installed font in the list in `theme.py`.

## Zoom and sharp text

- `enable_hidpi()` in `app/gui.py` tells Windows the program handles high-DPI screens, so text is drawn sharp instead of stretched.
- `theme.set_scale(zoom, dpi)` sets one scale for fonts, row heights, buttons, icons and spacing. Changing the zoom rebuilds the screen on the same tab.
- Every font is one point larger than its nominal size for readability.
- Tables fit their width by themselves, cards and the dashboard panels re-flow when space is tight, and each page scrolls vertically when zoomed content does not fit.
- `app/settings.py` stores the chosen zoom in a small file in the user's home folder.
