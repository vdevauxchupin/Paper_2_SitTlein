# Fig. 6: map of the surface-cover areas per tributary (RGI 6.0 outline intersected with the clean-ice / debris /
# vegetation polygons) on a Sentinel-2 backdrop, and dh/dt per surface cover and DEM interval for each tributary.
# Inputs: Data_Paper/tables/surface_cover/table1_dhdt_mean.csv, Data_Paper/vectors/Area_*.shp, External_Data/RGI60,
# External_Data/imagery/Sat_Im.tiff.
# Usage: cd figures; python fig6.py  -> output/fig6.png
import os
import numpy as np
import pandas as pd
import geopandas as gpd
import geoutils as gu
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from shapely import intersection
from shapely.ops import unary_union

FS_TICK, FS_LAB, FS_TITLE, FS_LEG = 14, 15, 16, 14
YLIM = (-12, 10)
t = pd.read_csv('../../Data_Paper/tables/surface_cover/table1_dhdt_mean.csv')
PERIODS = ['2002-1999', '2012-2002', '2019-2012', '2022-2019']
dates = pd.to_datetime(['1999-09-01', '2002-08-04', '2012-08-30', '2019-08-30', '2022-08-30'])
AREAS = [('Active ice', 'Clean ice', '#87cef3'), ('Debris-covered ice', 'Debris-covered ice', '#846146'),
         ('Vegetation-covered ice', 'Vegetation-covered ice', 'green'), ('Lobe', 'Lobe', 'black'),
         ('Thermo./Calving', 'Cryokarst/Calving', 'purple')]
dynamic_state = {"Agassiz": ["Quiescence + Surge", "Quiescence + Surge", "Quiescence", "Quiescence"],
                 "Seward": ["Quiescence + Surge", "Quiescence + Surge", "Quiescence", "Surge"],
                 "Marvine": ["Quiescence + Surge", "Quiescence", "Quiescence + Surge", "Quiescence"]}
state_styling = {"Quiescence": ("white", None), "Surge": ("grey", None), "Quiescence + Surge": ("lightgrey", "///")}

# surface-cover polygons per tributary
rgi = gpd.read_file('../../External_Data/RGI60/01_rgi60_Alaska.shp')
ids = {'Agassiz': 'RGI60-01.23649', 'Seward': 'RGI60-01.13696', 'Marvine': 'RGI60-01.23653'}
gois = rgi[rgi['RGIId'].isin(ids.values())].to_crs(32607)
shp = '../../Data_Paper/vectors/'
covers = {'Vegetation-covered ice': gpd.read_file(shp + 'Area_forelands.shp'), 'Active ice': gpd.read_file(shp + 'Area_cleanice.shp'),
          'Debris-covered ice': gpd.read_file(shp + 'Area_moraines.shp')}
cover_union = {k: unary_union(v.geometry.tolist()) for k, v in covers.items()}

W = 12.0
fig = plt.figure(figsize=(W, 1))
sat = gu.Raster('../../External_Data/imagery/Sat_Im.tiff')
b = sat.bounds
MAP_H = 5.2
MAP_W = MAP_H * (b.right - b.left) / (b.top - b.bottom)
TITLE, GAP, TS_H, XLAB = 0.45, 0.9, 3.4, 0.6
H = TITLE + MAP_H + GAP + TS_H + XLAB
fig.set_size_inches(W, H)
add_ax = lambda x, y, w, h, **kw: fig.add_axes([x / W, y / H, w / W, h / H], **kw)

L = 1.0
ax_map = add_ax(L, H - TITLE - MAP_H, MAP_W, MAP_H)
sat.plot(cmap='grey', add_cbar=False, ax=ax_map)
for _, g in gois.iterrows():
    for key, lab, c in AREAS[:3]:
        geom = intersection(g.geometry, cover_union[key])
        gpd.GeoSeries([geom], crs=32607).plot(ax=ax_map, facecolor=c, edgecolor='none', alpha=0.45)
gois.plot(ax=ax_map, facecolor='none', edgecolor='black', linewidth=0.8)
ax_map.set_xlim(b.left, b.right); ax_map.set_ylim(b.bottom, b.top)
ax_map.set_xticks([]); ax_map.set_yticks([])
ax_map.set_title('Areas by surface cover type', fontsize=FS_TITLE, weight='bold')

ax_leg = add_ax(L + MAP_W + 0.5, H - TITLE - MAP_H, W - (L + MAP_W + 0.5) - 0.1, MAP_H); ax_leg.axis('off')
h_area = [Patch(facecolor=c, alpha=0.45, edgecolor='black', linewidth=0.5, label=lab) for key, lab, c in AREAS[:3]] + \
         [Line2D([], [], color='black', lw=3, ls=':', label='Lobe'), Line2D([], [], color='purple', lw=2.5, label='Cryokarst/Calving')]
h_state = [Patch(facecolor=c, alpha=0.7 if s != 'Quiescence' else 1, hatch=h, edgecolor='black', linewidth=0.5, label=s)
           for s, (c, h) in state_styling.items()]
lg1 = ax_leg.legend(handles=h_area, title='Area type', title_fontsize=FS_LEG + 1, loc='upper left', fontsize=FS_LEG,
                    frameon=False, handlelength=2.2, handleheight=1.2, labelspacing=0.7, alignment='left')
ax_leg.add_artist(lg1)
ax_leg.legend(handles=h_state, title='Dynamic state', title_fontsize=FS_LEG + 1, loc='upper left', bbox_to_anchor=(0, 0.48), fontsize=FS_LEG,
              frameon=False, handlelength=2.2, handleheight=1.2, labelspacing=0.7, alignment='left')

# time series, one panel per tributary
PW = (W - L - 0.1 - 2 * 0.15) / 3
axs = []
for j, gname in enumerate(['Agassiz', 'Seward', 'Marvine']):
    ax = add_ax(L + j * (PW + 0.15), XLAB, PW, TS_H, sharey=axs[0] if axs else None)
    axs.append(ax)
    for k, per in enumerate(PERIODS):
        c, h = state_styling[dynamic_state[gname][k]]
        ax.axvspan(dates[k], dates[k + 1], color=c, hatch=h, alpha=0.25 if c != 'white' else 0, zorder=0, linewidth=0)
    for key, lab, c in AREAS:
        r = t[(t.glacier == gname) & (t.area == key)].set_index('period').loc[PERIODS]
        m, s = r.dhdt_mean.values, r.dhdt_sig.values
        xs = np.repeat(dates, 2)[1:-1]
        ax.plot(xs, np.repeat(m, 2), color=c, lw=3 if key == 'Lobe' else 2, ls=':' if key == 'Lobe' else '-', zorder=3)
        for k in range(len(PERIODS)):
            ax.fill_between([dates[k], dates[k + 1]], m[k] - s[k], m[k] + s[k], color=c, alpha=0.18, linewidth=0, zorder=2)
    for d in dates:
        ax.axvline(d, color='black', linestyle='--', linewidth=0.6)
    ax.axhline(0, color='black', linewidth=0.6, linestyle='--')
    ax.set_ylim(*YLIM)
    ax.set_yticks([-10, -5, 0, 5, 10])
    ax.set_xlim(dates[0] - pd.Timedelta(days=200), dates[-1] + pd.Timedelta(days=200))
    ax.set_xticks(pd.to_datetime(['2000-01-01', '2005-01-01', '2010-01-01', '2015-01-01', '2020-01-01']))
    ax.set_xticklabels(['2000', '2005', '2010', '2015', '2020'])
    ax.tick_params(labelsize=FS_TICK)
    ax.set_title(gname, fontsize=FS_TITLE, weight='bold')
    if j == 0:
        ax.set_ylabel(r'$\partial h/\partial t$ (m a$^{-1}$)', fontsize=FS_LAB)
    else:
        ax.tick_params(axis='y', labelleft=False)

os.makedirs('output', exist_ok=True)
fig.savefig('output/fig6.png', bbox_inches='tight', dpi=300)
print('saved output/fig6.png')
