"""Fig. 7: lobe continuity terms (dh/dt, flux divergence, SMB) per DEM interval from cmb_tributaries.csv; dashed = direct 1999-2022 SMB.

Step lines per DEM interval with 1-sigma bands, surge periods as hatched grey bands, DEM dates as black vertical lines.
Uncertainty = 'mixed' scheme. Run as `cd figures; python fig7.py`.
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

TAB = "../../Data_Paper/tables/mass_continuity"
OUT = "output"
os.makedirs(OUT, exist_ok=True)

df = pd.read_csv(f"{TAB}/cmb_tributaries.csv")
# full-period SMB computed directly from the 1999 and 2022 DEMs (period key "2022-1999")
_full = df[(df.unit == "Lobe") & (df.period == "2022-1999")].iloc[0]
smb_full, smb_full_sig = _full["CMB_m_a"], _full["sig_CMB_mixed_m_a"]
print(f"SMB 1999-2022 (direct) = {smb_full:.2f} ± {smb_full_sig:.2f} m/a ice")

dates_dems = pd.to_datetime(["1999-09-01", "2002-08-04", "2012-08-30", "2019-10-10", "2022-09-18"])
periods = ["2002-1999", "2012-2002", "2019-2012", "2022-2019"]
surge_periods = {"Agassiz": [("2001-02-01", "2002-11-01")],
                 "Seward": [("2008-05-01", "2009-05-01"), ("2020-05-01", "2021-09-01")],
                 "Marvine": [("2001-07-01", "2002-07-01"), ("2013-05-01", "2013-09-01")]}
surge_periods["Lobe"] = [p for g in ["Agassiz", "Seward", "Marvine"] for p in surge_periods[g]]
# lobe areas (km2) from the continuity tables
_gates = pd.read_csv(f"{TAB}/fluxes_gates.csv").drop_duplicates("gate").set_index("gate")["area_km2"]
areas = {"Lobe": pd.read_csv(f"{TAB}/cmb_lobe.csv")["area_km2"].iloc[0], **_gates.to_dict()}
titles = {"Lobe": "Whole lobe (3 gates)", "Agassiz": "Agassiz", "Seward": "Seward", "Marvine": "Marvine"}

terms = [  # (column, sigma column, label, color, linewidth)
    ("dhdt_m_a", "sig_dhdt_m_a", r"$\Delta h/\Delta t$", "#2a78d6", 2),
    ("fluxdiv_m_a", "sig_fluxdiv_mixed_m_a", r"$\nabla\cdot q = -Q_{in}/A$ (flux divergence)", "#eb6834", 2),
    ("CMB_m_a", "sig_CMB_mixed_m_a", r"SMB $= \Delta h/\Delta t + \nabla\cdot q$", "black", 3),
]

fig, axs = plt.subplots(2, 2, figsize=(12, 8.6), sharex=True, sharey=True)
for ax, unit in zip(axs.flat, ["Lobe", "Agassiz", "Seward", "Marvine"]):
    d = df[df.unit == unit].set_index("period").loc[periods]
    for s0, s1 in surge_periods[unit]:
        ax.axvspan(pd.to_datetime(s0), pd.to_datetime(s1), facecolor="lightgrey", edgecolor="dimgrey",
                   hatch="///", linewidth=0, alpha=0.35, label="Surge" if (s0, s1) == surge_periods[unit][0] else None)
    for col, sig, label, color, lw in terms:
        for k, p in enumerate(periods):
            x = [dates_dems[k], dates_dems[k + 1]]
            m, s = d.loc[p, col], d.loc[p, sig]
            ax.fill_between(x, [m - s] * 2, [m + s] * 2, color=color, alpha=0.18, linewidth=0)
            ax.plot(x, [m, m], color=color, lw=lw, label=label if k == 0 else None, solid_capstyle="butt")
    if unit == "Lobe":
        wlabel = f"{smb_full:.2f} ± {smb_full_sig:.2f} m a$^{{-1}}$ ice"
        ax.axhline(smb_full, color="#1baf7a", lw=2.2, ls="--", label=f"SMB 1999–2022 ({wlabel})")
    for date in dates_dems:
        ax.axvline(date, color="black", lw=1)
    ax.axhline(0, color="black", lw=0.5, ls="--")
    ax.set_title(f"{titles[unit]} — {areas[unit]:.0f} km²", fontsize=17, weight="bold")
    ax.grid(axis="y", alpha=0.3)
    ax.tick_params(labelsize=15)
    ax.set_ylim(-8, 2)
for ax in axs[:, 0]:
    ax.set_ylabel(r"m a$^{-1}$ ice", fontsize=16)
fig.tight_layout(rect=(0, 0.11, 1, 1))
fig.legend(*axs[0, 0].get_legend_handles_labels(), loc="lower center", ncol=3, fontsize=15, frameon=False, columnspacing=1.5)
fig.savefig(f"{OUT}/fig7.png", dpi=300, bbox_inches="tight")
fig.savefig(f"{OUT}/fig7.pdf", bbox_inches="tight")
print("saved")
