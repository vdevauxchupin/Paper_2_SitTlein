# Fig. 3: dh/dt maps (1999-2022 and the four DEM intervals) with the surge reservoirs / receiving areas and their volume
# changes; below, per tributary, the area change per 100 m band for each interval (heatmap) and the 1999-2022 change
# on the 1999 band areas (bars). Hypsometries use the pixels valid in all five DEMs.
# Inputs: Data_Paper/elevation_change/dhdt_*.tif, Data_Paper/tables/surge_transfer/{surge_transfer.csv,
# hypsometry_bins_5dem_footprint.csv}, Data_Paper/vectors/surge_areas, External_Data/RGI60.
# Usage: cd figures; python fig3.py  -> output/fig3.png
import os
import numpy as np
import pandas as pd
import geopandas as gpd
import geoutils as gu
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.lines import Line2D
from matplotlib.colors import TwoSlopeNorm

# outlines: reservoir green, receiving area magenta, both solid with a black halo
LINE_C, REC_C, REC_LS = '#00ff00', 'magenta', '-'
HALO = [pe.Stroke(linewidth=5.5, foreground='black'), pe.Normal()]

data = '../../Data_Paper'
tab = f'{data}/tables/surge_transfer'
surge_dir = f'{data}/vectors/surge_areas'
PERIODS = [(1999, 2002), (2002, 2012), (2012, 2019), (2019, 2022)]
plab = lambda y0, y1: f"{y1}-{y0}"

# dh/dt maps from 02_elevation_change.ipynb
dhdt = {}
for (y0, y1) in PERIODS + [(1999, 2022)]:
    dhdt[plab(y0, y1)] = gu.Raster(f'{data}/elevation_change/dhdt_{y1}_{y0}.tif')
_rgi = gu.Vector('../../External_Data/RGI60/01_rgi60_Alaska.shp').reproject(dhdt['2022-1999']).ds
glaciers_of_interest = _rgi[_rgi['RGIId'].isin(['RGI60-01.13696', 'RGI60-01.23653', 'RGI60-01.23649'])]
mask_names = ['Agassiz', 'Seward', 'Marvine']

# surge volume changes (km3)
st = pd.read_csv(f'{tab}/surge_transfer.csv')
dict_surge = {}
for _, r in st.iterrows():
    g, per = r['surge'].split(' ')
    dict_surge.setdefault(per, {})[g] = {'reservoir': (r['dV_res'], r['sig_dV_res']), 'receiver': (r['dV_sink'], r['sig_dV_sink'])}

FS_TICK, FS_LAB, FS_NAME, FS_TITLE, FS_LEG, FS_TXT, FS_CBAR, FS_CELL = 19, 20, 20, 22, 18, 17, 21, 18
bins = np.arange(0, 1100, 100)

# area per band (km2) on the five-DEM footprint, and its change per tributary and period
hyp = pd.read_csv(f'{tab}/hypsometry_bins_5dem_footprint.csv')
hist = lambda y, name: hyp[(hyp.lobe == name) & (hyp.dem == y)].sort_values('bin_lo').area_km2.values
dA = {name: {(y0, y1): hist(y1, name) - hist(y0, name) for (y0, y1) in PERIODS + [(1999, 2022)]} for name in mask_names}

b = dhdt["2022-1999"].bounds
R = (b.top - b.bottom) / (b.right - b.left)
W, MARGIN = 16.0, 0.15
SW = 2.8; SH = SW * R                      # small (period) maps
TITLE, MGAP = 0.55, 0.2
BH = 2 * SH + TITLE; BW = BH / R           # large map: as tall as the 2x2 block
CBAR_H, CBAR_LAB = 0.32, 1.0
STRIP_TOP_GAP, STRIP_H, STRIP_XLAB = 0.9, 4.2, 0.9
H = CBAR_H + CBAR_LAB + TITLE + BH + STRIP_TOP_GAP + STRIP_H + STRIP_XLAB
fig = plt.figure(figsize=(W, H))
add_ax = lambda x, y, w, h, **kw: fig.add_axes([x / W, y / H, w / W, h / H], **kw)

cbar_ax = add_ax(MARGIN + 0.5, H - CBAR_H - 0.05, W - 2 * MARGIN - 1.0, CBAR_H)
cbar = fig.colorbar(plt.cm.ScalarMappable(cmap='RdYlBu', norm=plt.Normalize(vmin=-10, vmax=10)), cax=cbar_ax, orientation='horizontal')
cbar.set_label(r"$\Delta h/\Delta t$ (m a$^{-1}$)", fontsize=FS_CBAR)
cbar.ax.tick_params(labelsize=FS_CBAR)


def map_ax(x, y, w, h, y0, y1, surge_outlines=True):
    ax = add_ax(x, y, w, h)
    dhdt[f"{y1}-{y0}"].plot(ax=ax, vmin=-10, vmax=10, cmap="RdYlBu", add_cbar=False)
    glaciers_of_interest.plot(ax=ax, facecolor="none", edgecolor="black", linewidth=1.0)
    d = f"{surge_dir}/{y1}_{y0}/"
    if surge_outlines and os.path.exists(d):
        for shp in [f for f in os.listdir(d) if f.endswith('.shp')]:
            rec = shp.split('.')[0].endswith('Receiver')
            gpd.read_file(d + shp).boundary.plot(ax=ax, color=REC_C if rec else LINE_C, linewidth=2.5, linestyle=REC_LS if rec else '-',
                                                 path_effects=HALO)
    ax.set_xlim(b.left, b.right); ax.set_ylim(b.bottom, b.top)
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_title(plab(y0, y1), fontsize=FS_TITLE, weight='bold')
    return ax


top = H - CBAR_H - CBAR_LAB - TITLE                      # top edge of the map block
map_ax(MARGIN, top - BH, BW, BH, 1999, 2022, surge_outlines=False)
x2 = MARGIN + BW + 0.3
for k, (y0, y1) in enumerate(PERIODS):
    r, c = divmod(k, 2)
    map_ax(x2 + c * (SW + MGAP), top - SH - r * (SH + TITLE), SW, SH, y0, y1)

# right column: outline legend + surge volumes
info_x = x2 + 2 * SW + MGAP + 0.3
ax_info = add_ax(info_x, top - BH, W - MARGIN - info_x, BH + 0.3); ax_info.axis('off')
ax_info.legend(handles=[Line2D([], [], color=LINE_C, lw=2.5, path_effects=HALO, label='Surge reservoir'),
                        Line2D([], [], color=REC_C, lw=2.5, ls=REC_LS, path_effects=HALO, label='Receiving area')],
               loc='upper left', fontsize=FS_LEG, handlelength=1.6, framealpha=0.9, borderaxespad=0)
LINE = FS_TXT * 1.25
yy = 3.4 * LINE
def _txt(s, **kw):
    ax_info.annotate(s, xy=(0.0, 1.0), xycoords='axes fraction', xytext=(2, -yy), textcoords='offset points',
                     va='top', fontsize=FS_TXT, **kw)
_txt('Net volume change (km³)', style='italic'); yy += 1.4 * LINE
for (y0, y1) in PERIODS:
    sd = dict_surge.get(f"{y1}-{y0}", {})
    if not sd:
        continue
    _txt(plab(y0, y1), weight='bold'); yy += LINE
    for g in sorted(sd):
        _txt(g); yy += LINE
        for key, lab in (("reservoir", "Reservoir"), ("receiver", "Receiving area")):
            if key in sd[g]:
                _txt(f"  {lab}: {sd[g][key][0]:.2f} ± {sd[g][key][1]:.2f}"); yy += LINE
    yy += 0.4 * LINE

# ---- strip below the maps: heatmap of the four periods + a 1999-2022 bar panel per tributary ----
SL, SGAP = 1.25, 0.35                                  # left margin for the elevation label, gap between panels
sw_ = (W - MARGIN - SL - 2 * SGAP) / 3
sy = STRIP_XLAB
axs = []
for j, name in enumerate(mask_names):
    x0 = SL + j * (sw_ + SGAP)
    HMW = sw_ * 0.6
    ax = add_ax(x0, sy, HMW, STRIP_H, sharey=axs[0] if axs else None)
    axs.append(ax)
    cols = PERIODS
    M = np.array([dA[name][p] for p in cols]).T            # bands x periods
    vmax = np.abs(M).max()
    ax.imshow(M, origin='lower', aspect='auto', cmap='RdBu', norm=TwoSlopeNorm(0, -vmax, vmax),
              extent=[-0.5, len(cols) - 0.5, 0, 1000])
    for i in range(M.shape[0]):
        for k in range(M.shape[1]):
            v = M[i, k]
            ax.text(k, 50 + 100 * i, ('0' if f'{v:.0f}' == '-0' else f'{v:.0f}'.replace('-', '−')), ha='center', va='center', fontsize=FS_CELL,
                    color='white' if abs(v) > 0.55 * vmax else 'black')
    for k in range(1, len(cols)):   # grey dashed separators between periods
        ax.axvline(k - 0.5, color='grey', linestyle='--', linewidth=1.2)
    # 1999-2022: area of each band in 1999 (grey) with the change coloured (blue gain, red loss), and the % change
    axb = add_ax(x0 + HMW + 0.12, sy, sw_ - HMW - 0.12, STRIP_H, sharey=ax)
    a0 = hist(1999, name); a1 = hist(2022, name)
    yc = bins[:-1] + 50
    # hatched fills with a slightly darker outline: gain = blue dots added to the bar, loss = red hatching over the part removed
    axb.barh(yc, np.minimum(a0, a1), height=80, facecolor='#dddddd', edgecolor='#808080', hatch='///', linewidth=0.8)
    gain = a1 > a0
    axb.barh(yc[gain], (a1 - a0)[gain], left=a0[gain], height=80, facecolor='#9ecae1', edgecolor='#08519c', hatch='...', linewidth=0.8)
    axb.barh(yc[~gain], (a0 - a1)[~gain], left=a1[~gain], height=80, facecolor='#fcbba1', edgecolor='#a50f15', hatch='///', linewidth=0.8)
    xm = max(a0.max(), a1.max())
    for i in range(len(yc)):
        pct = 100 * (a1[i] / a0[i] - 1) if a0[i] > 0 else np.nan
        axb.text(max(a0[i], a1[i]) + 0.04 * xm, yc[i], f'{pct:+.0f}%'.replace('-', '−'), va='center', ha='left', fontsize=FS_CELL - 1)
    axb.set_xlim(0, 1.75 * xm)
    axb.xaxis.set_major_locator(plt.MaxNLocator(2, integer=True))
    axb.tick_params(axis='y', labelleft=False)
    axb.tick_params(axis='both', which='major', labelsize=FS_TICK - 3)
    axb.set_title(plab(1999, 2022), fontsize=FS_TICK - 2)
    axb.set_xlabel('Area (km$^{2}$)', fontsize=FS_TICK - 2)
    axb.grid(True, axis='x', alpha=0.25)
    ax.set_xticks(range(len(cols)))
    ax.set_xticklabels([plab(*p).replace('-', '–\n') for p in cols], fontsize=FS_TICK - 5)
    ax.set_yticks(bins, minor=True)
    ax.tick_params(axis='y', which='minor', length=0)
    ax.set_yticks([0, 200, 400, 600, 800, 1000])
    ax.tick_params(axis='y', which='major', labelsize=FS_TICK)
    ax.set_title(name, fontsize=FS_NAME, weight='bold')
    if j == 0:
        ax.set_ylabel('Elevation (m a.s.l.)', fontsize=FS_LAB)
    else:
        ax.tick_params(axis='y', labelleft=False)
fig.text((SL + 1.5 * sw_ + SGAP) / W, (sy + STRIP_H + 0.42) / H, 'Area change per 100 m band (km²)',
         fontsize=FS_LAB, ha='center', va='bottom', weight='bold')

os.makedirs('output', exist_ok=True)
fig.savefig('output/fig3.png', bbox_inches='tight', dpi=300)
print('saved output/fig3.png')
