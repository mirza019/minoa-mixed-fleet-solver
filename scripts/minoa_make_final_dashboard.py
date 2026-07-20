from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch


OUT_DIR = Path(__file__).resolve().parents[1] / "FAU_Thesis_temp" / "figures"


def add_card(ax, x, y, w, h, title, lines, *,
             face="#f7fbff", edge="#0057d8", accent="#0057d8",
             title_size=14, line_size=12.2, number_size=18):
    shadow = FancyBboxPatch(
        (x + 0.08, y - 0.08),
        w,
        h,
        boxstyle="round,pad=0.035,rounding_size=0.10",
        linewidth=0,
        facecolor="#d7e1ee",
        alpha=0.55,
        zorder=1,
    )
    ax.add_patch(shadow)
    card = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.035,rounding_size=0.10",
        linewidth=1.45,
        edgecolor=edge,
        facecolor=face,
        zorder=2,
    )
    ax.add_patch(card)
    ax.text(
        x + 0.28,
        y + h - 0.28,
        title,
        ha="left",
        va="top",
        fontsize=title_size,
        weight="bold",
        color="#0f2544",
        zorder=3,
    )
    number_mode = any(kind == "number" for _, kind in lines)
    yy = y + h - (0.54 if number_mode else 0.55)
    for text, kind in lines:
        if kind == "number":
            ax.text(
                x + 0.28,
                yy,
                text,
                ha="left",
                va="top",
                fontsize=number_size,
                weight="bold",
                color=accent,
                zorder=3,
            )
            yy -= 0.62
        else:
            ax.text(
                x + 0.28,
                yy,
                text,
                ha="left",
                va="top",
                fontsize=line_size,
                color="#26384f",
                zorder=3,
            )
            yy -= 0.45


def make_dashboard(path: Path) -> None:
    fig, ax = plt.subplots(figsize=(14.6, 8.9), dpi=220)
    ax.set_xlim(0, 14.2)
    ax.set_ylim(0, 8.8)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    blue = "#005bea"
    blue_dark = "#12395f"
    blue_soft = "#edf5ff"
    teal = "#148a7a"
    amber = "#b56b00"
    green = "#207744"

    ax.text(
        7.1,
        8.40,
        "Final Result Summary",
        ha="center",
        va="center",
        fontsize=21.0,
        weight="bold",
        color="#0f2544",
    )
    ax.text(
        7.1,
        8.05,
        "Validated multi-start weighted path-cover matheuristic on the MINOA Senior benchmark",
        ha="center",
        va="center",
        fontsize=12.8,
        color="#465a72",
    )

    add_card(
        ax,
        0.45,
        6.10,
        4.05,
        1.75,
        "Small",
        [("162.44 cost", "number"), ("2 used vehicle blocks", "text")],
        face=blue_soft,
        edge=blue,
        accent=blue,
        title_size=15.0,
        number_size=20,
    )
    add_card(
        ax,
        5.08,
        6.10,
        4.05,
        1.75,
        "Medium",
        [("371.35 cost", "number"), ("5 used vehicle blocks", "text")],
        face="#f1fbf8",
        edge=teal,
        accent=teal,
        title_size=15.0,
        number_size=20,
    )
    add_card(
        ax,
        9.71,
        6.10,
        4.05,
        1.75,
        "Large",
        [("1163.35 cost", "number"), ("15 used vehicle blocks", "text")],
        face="#fff7ed",
        edge=amber,
        accent=amber,
        title_size=15.0,
        number_size=20,
    )

    add_card(
        ax,
        0.45,
        3.92,
        8.30,
        2.02,
        "All 12 Senior instances",
        [
            ("Total validated cost: 10000.48", "number"),
            ("Used vehicle blocks: 126", "text"),
            ("Final no-regression archive", "text"),
        ],
        face=blue_soft,
        edge=blue_dark,
        accent=blue_dark,
        title_size=14.5,
        number_size=18.5,
    )
    add_card(
        ax,
        9.20,
        3.92,
        4.56,
        2.02,
        "Fleet split",
        [("32 EV + 94 ICE", "number"), ("EV share: 25.4%", "text")],
        face="#f1fbf8",
        edge=teal,
        accent=teal,
        title_size=14.5,
        number_size=18.5,
    )

    add_card(
        ax,
        0.45,
        1.85,
        4.05,
        1.66,
        "Objective audit",
        [("Small/Medium/Large: 0.00", "text"), ("All Senior: <= 0.01", "text"), ("Status: reconciled", "text")],
        face="#f8fbff",
        edge="#6c7f99",
        accent="#26384f",
        title_size=13.2,
        line_size=11.4,
        number_size=15,
    )
    add_card(
        ax,
        5.08,
        1.85,
        4.05,
        1.66,
        "Reproducibility",
        [("CPU-only local run", "text"), ("No GPU / No HPC cluster", "text"), ("No commercial solver required", "text")],
        face="#f8fbff",
        edge="#6c7f99",
        accent="#26384f",
        title_size=13.2,
        line_size=11.4,
        number_size=15,
    )
    add_card(
        ax,
        9.71,
        1.85,
        4.05,
        1.66,
        "Method identity",
        [("Multi-start weighted path cover", "text"), ("Best validated candidate retained", "text"), ("No optimality certificate claimed", "text")],
        face="#f8fbff",
        edge="#6c7f99",
        accent="#26384f",
        title_size=13.2,
        line_size=11.4,
        number_size=15,
    )

    strip_shadow = FancyBboxPatch(
        (0.53, 0.47),
        13.31,
        0.72,
        boxstyle="round,pad=0.025,rounding_size=0.08",
        linewidth=0,
        facecolor="#d7e1ee",
        alpha=0.45,
        zorder=1,
    )
    ax.add_patch(strip_shadow)
    strip = FancyBboxPatch(
        (0.45, 0.55),
        13.31,
        0.72,
        boxstyle="round,pad=0.025,rounding_size=0.08",
        linewidth=1.1,
        edgecolor="#b5c3d3",
        facecolor="#f7f9fc",
        zorder=2,
    )
    ax.add_patch(strip)
    ax.text(
        0.75,
        0.91,
        "All-instance cost structure",
        ha="left",
        va="center",
        fontsize=12.6,
        weight="bold",
        color="#0f2544",
        zorder=3,
    )
    ax.text(
        5.55,
        0.91,
        "Fixed 9450.00   |   Break 412.36   |   Pull 108.29   |   CO$_2$ 29.84",
        ha="left",
        va="center",
        fontsize=12.6,
        color="#26384f",
        zorder=3,
    )

    fig.savefig(path, bbox_inches="tight", pad_inches=0.12)
    fig.savefig(path.with_suffix(".png"), bbox_inches="tight", pad_inches=0.12, dpi=260)
    plt.close(fig)


if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    make_dashboard(OUT_DIR / "final_performance_dashboard.pdf")
