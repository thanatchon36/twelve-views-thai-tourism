"""Plot style shared by all twelve figures."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.patheffects as pe  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.colors import to_hex, to_rgb  # noqa: E402

from .config import FIGURES, FONTS  # noqa: E402

# Widths in inches for an A4 page with 2.5 cm margins
FULL, HALF = 6.3, 3.05

INK, MUTED, AXIS, GRID = "#1F1F1F", "#6B6B6B", "#9A9A9A", "#E3E1DA"

# Colour follows the entity. Each palette serves one family of categories.
ORIGIN_COLORS = ["#2A78D6", "#1BAF7A", "#EB6834", "#D99A00", "#6250D6", "#E06C9F"]   # labels.ORIGIN_REGIONS
THAI_COLORS = ["#5B8E3E", "#D49A2A", "#C2414B", "#3A7DC2", "#8E5BB5", "#17A2A2"]     # labels.THAI_REGIONS
DEST_COLORS = ["#C2414B", "#17A2A2", "#5FB8CF", "#3A7DC2", "#5B8E3E", "#D49A2A"]     # labels.DEST_CLUSTERS
PERSONA_COLORS = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#56B4E9", "#E69F00"]  # labels.PERSONAS
SPEND_COLORS = ["#3A7DC2", "#C2414B", "#D49A2A", "#8E5BB5", "#17A2A2", "#9A9A9A"]    # spending categories
NODE_GRAY = "#4A4A4A"


def setup() -> None:
    """Register IBM Plex Sans (shipped as IBM Plex Sans Thai) or fall back to DejaVu Sans."""
    files = sorted(FONTS.glob("IBMPlexSansThai-*.ttf"))
    for f in files:
        font_manager.fontManager.addfont(str(f))
    if not files:
        print("note: IBM Plex fonts not found (run scripts/get_fonts.sh); falling back to DejaVu Sans")
    matplotlib.rcParams.update({
        "font.family": "IBM Plex Sans Thai" if files else "DejaVu Sans",
        "font.size": 7.5,
        "axes.labelsize": 7.5, "xtick.labelsize": 7, "ytick.labelsize": 7,
        "axes.edgecolor": AXIS, "axes.linewidth": 0.6,
        "axes.spines.top": False, "axes.spines.right": False,
        "xtick.color": MUTED, "ytick.color": MUTED,
        "xtick.major.width": 0.6, "ytick.major.width": 0.6,
        "xtick.major.size": 2.5, "ytick.major.size": 2.5,
        "text.color": INK, "axes.labelcolor": INK,
        "legend.frameon": False,
        "pdf.fonttype": 42,
        "figure.dpi": 150, "savefig.dpi": 300,
        "savefig.bbox": "tight", "savefig.pad_inches": 0.03,
    })


def lighten(color, t: float) -> str:
    """Mix a colour with white; t=0 keeps it, t=1 gives white."""
    r, g, b = to_rgb(color)
    return to_hex((r + (1 - r) * t, g + (1 - g) * t, b + (1 - b) * t))


def halo(width: float = 2.2, color: str = "white"):
    return [pe.withStroke(linewidth=width, foreground=color)]


def save(fig, name: str) -> None:
    fig.savefig(FIGURES / f"{name}.pdf")
    fig.savefig(FIGURES / f"{name}.png", dpi=220)
    plt.close(fig)
