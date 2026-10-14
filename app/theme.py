"""Design system for the Smart Parking application.

Every colour, font, spacing value and ttk style lives here. The screens never use raw
colour codes: they import these constants, so the whole look can be changed in one file.
"""
from tkinter import font as tkfont
from tkinter import ttk

# ------------------------------------------------------------------ colour palette
NAVY = "#17263C"          # header, table headings, headings
NAVY_2 = "#22344D"        # navigation bar
TEAL = "#117C78"          # primary actions, selected navigation
TEAL_DARK = "#0D625F"     # hover / pressed
BG = "#F3F6FA"            # application workspace
CARD = "#FFFFFF"          # panels and cards
TEXT = "#202B3C"          # primary text
MUTED = "#65748B"         # secondary text
BORDER = "#DCE3EC"        # borders and separators
STRIPE = "#F7F9FC"        # alternating table rows
ACCENT = "#F2B705"        # small highlights only
SUCCESS = "#198754"
WARNING = "#D97706"
ERROR = "#DC3545"
INFO = "#3478F6"

NAVY_TEXT = "#9FB0C4"     # muted text on navy
SELECT_BG = "#D5EDEB"     # selected table row
HOVER_BG = "#EAF1F8"      # hovered table row
INPUT_DISABLED = "#EEF2F7"

# soft backgrounds used for status messages, pills and icon circles
TINT = {
    "success": "#E6F4EC", "warning": "#FFF3DF", "error": "#FDECEE",
    "info": "#E7EFFE", "teal": "#DDF1F0", "neutral": "#EEF2F7", "navy": "#E3E8F0",
}
KIND_COLOR = {"success": SUCCESS, "warning": WARNING, "error": ERROR, "info": INFO, "teal": TEAL, "neutral": MUTED, "navy": NAVY}

# table status text -> (row background or None, text colour, strike-through)
STATUS_STYLES = {
    "ACTIVE": ("#E9F6EF", TEXT, False),
    "AVAILABLE": (None, TEXT, False),
    "PAID": (None, TEXT, False),
    "PARTIAL": ("#FFF4DD", TEXT, False),
    "UNPAID": ("#FDEBED", TEXT, False),
    "USED": (None, MUTED, False),
    "EXPIRED": ("#F1F3F6", "#7A8699", False),
    "CANCELLED": (None, "#8A97A8", True),
    "MAINTENANCE": ("#FFF4DD", TEXT, False),
    "OPEN": ("#E8F0FE", TEXT, False),
    "CLOSED": (None, MUTED, False),
}

# ------------------------------------------------------------------ zoom, spacing, typography
# ZOOM is the user's zoom (1.0 = 100 %). DPI is the Windows display scaling (1.0 = 96 dpi).
# Fonts are in points, so Tk already applies DPI to them; pixel sizes use px().
ZOOM = 1.0
DPI = 1.0
FONT_BOOST = 1            # every font is one point larger than its nominal size, for clarity
XS, S, M, L, XL = 4, 8, 12, 16, 24
ROW_HEIGHT = 32
CONTROL_HEIGHT = 36


def px(value):
    """Scale a pixel size by zoom and display DPI."""
    return max(1, round(value * ZOOM * DPI))


def set_scale(zoom_percent, dpi_factor=1.0):
    """Change zoom. The UI must be rebuilt afterwards (the App does this)."""
    global ZOOM, DPI, XS, S, M, L, XL, ROW_HEIGHT, CONTROL_HEIGHT
    ZOOM, DPI = zoom_percent / 100.0, dpi_factor
    XS, S, M, L, XL = px(4), px(8), px(12), px(16), px(24)
    ROW_HEIGHT, CONTROL_HEIGHT = px(32), px(36)


FAMILY = "Segoe UI"
_CANDIDATES = ("Segoe UI", "Inter", "Helvetica Neue", "SF Pro Text", "Roboto", "Open Sans",
               "Carlito", "Calibri", "Noto Sans", "DejaVu Sans", "Arial")


def font(size=10, weight="normal", **kw):
    """Return a Tk font tuple in the application font, scaled by the zoom."""
    points = max(7, round((size + FONT_BOOST) * ZOOM))
    spec = [FAMILY, points, weight]
    spec.extend(k for k, v in kw.items() if v)
    return tuple(spec)


def _resolve_family(root):
    global FAMILY
    available = {f.lower(): f for f in tkfont.families(root)}
    for name in _CANDIDATES:
        if name.lower() in available:
            FAMILY = available[name.lower()]
            return


# ------------------------------------------------------------------ ttk styling
def apply_theme(root):
    """Configure ttk styles once. Call right after creating the root window."""
    _resolve_family(root)
    root.configure(bg=BG)
    root.option_add("*Font", font(10))
    root.option_add("*TCombobox*Listbox.font", font(10))
    root.option_add("*TCombobox*Listbox.background", CARD)
    root.option_add("*TCombobox*Listbox.foreground", TEXT)
    root.option_add("*TCombobox*Listbox.selectBackground", TEAL)
    root.option_add("*TCombobox*Listbox.selectForeground", "#FFFFFF")

    st = ttk.Style(root)
    st.theme_use("clam")
    st.configure(".", font=font(10), background=CARD, foreground=TEXT, bordercolor=BORDER)

    # text fields
    st.configure("Modern.TEntry", fieldbackground=CARD, foreground=TEXT, bordercolor=BORDER,
                 lightcolor=BORDER, darkcolor=BORDER, insertcolor=TEXT, padding=(px(9), px(7)), relief="flat")
    st.map("Modern.TEntry",
           bordercolor=[("focus", TEAL)], lightcolor=[("focus", TEAL)], darkcolor=[("focus", TEAL)],
           fieldbackground=[("disabled", INPUT_DISABLED)], foreground=[("disabled", MUTED)])

    # drop-downs
    st.configure("Modern.TCombobox", fieldbackground=CARD, background=CARD, foreground=TEXT,
                 bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER, arrowcolor=MUTED,
                 arrowsize=px(16), padding=(px(9), px(7)), relief="flat")
    st.map("Modern.TCombobox",
           fieldbackground=[("readonly", CARD), ("disabled", INPUT_DISABLED)],
           background=[("readonly", CARD)],
           selectbackground=[("readonly", CARD)], selectforeground=[("readonly", TEXT)],
           bordercolor=[("focus", TEAL)], lightcolor=[("focus", TEAL)], darkcolor=[("focus", TEAL)],
           arrowcolor=[("hover", TEAL), ("focus", TEAL)])

    # tables
    st.configure("Modern.Treeview", background=CARD, fieldbackground=CARD, foreground=TEXT,
                 rowheight=ROW_HEIGHT, borderwidth=0, font=font(10), relief="flat")
    st.map("Modern.Treeview", background=[("selected", SELECT_BG)], foreground=[("selected", TEXT)])
    st.configure("Modern.Treeview.Heading", background=NAVY, foreground="#FFFFFF", relief="flat",
                 font=font(10, "bold"), padding=(px(10), px(8)), borderwidth=0)
    st.map("Modern.Treeview.Heading", background=[("active", NAVY_2)])

    # slim scrollbars without arrow buttons
    for orient, name in (("Vertical", "Modern.Vertical.TScrollbar"), ("Horizontal", "Modern.Horizontal.TScrollbar")):
        side = "ns" if orient == "Vertical" else "ew"
        st.layout(name, [(f"{orient}.Scrollbar.trough",
                          {"sticky": side, "children": [(f"{orient}.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"})]})])
        st.configure(name, background="#C3CEDB", troughcolor=STRIPE, bordercolor=STRIPE,
                     lightcolor="#C3CEDB", darkcolor="#C3CEDB", relief="flat", gripcount=0, width=px(12))
        st.map(name, background=[("active", "#9DB0C6"), ("pressed", TEAL)])
    return st
