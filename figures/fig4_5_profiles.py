# Figs. 4-5: elevation change, bed and velocity along Seward's centerline (Fig. 4) and transverse line (Fig. 5).
# One fixed discrete colour per OIB date; map top left, all legends top right; figure 12 in wide.
# Reads the profile tables written by 05_centerlines.ipynb.
# Usage: python fig4_5_profiles.py [centerline|crossline]   (no argument: both)
import os
import sys
import json
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import cmocean
import xdem
import geoutils as gu

T = '../../Data_Paper/tables/centerlines'
OUTDIR = 'output'
os.makedirs(OUTDIR, exist_ok=True)

FS_TICK, FS_LAB, FS_LEG, FS_TITLE, FS_PANEL, FS_MARK = 14, 15, 13.5, 16, 16, 15
SHADE = 0.15
DATE_COLORS = {'2000-08-26': '#7f7f7f', '2003-08-25': '#1f77b4', '2007-08-26': '#2ca02c', '2009-08-22': '#d62728',
               '2010-08-23': '#9467bd', '2012-08-21': '#8c564b', '2013-08-27': '#e377c2', '2014-08-20': '#17becf',
               '2016-08-17': '#bcbd22', '2018-08-17': '#ff7f0e', '2019-09-28': '#b8860b', '2021-05-02': '#000000'}
VEL = [('2000-2012', '#027562'), ('2012-2020', '#FFC107'), ('2020-2022', '#1E88E5')]
plasma = plt.cm.plasma

# map backdrop and bed masked to the RGI outlines of Seward, Agassiz and Marvine
sat_image = gu.Raster('../../External_Data/imagery/Sat_im.tiff').reproject(crs=32607)
bed_complete = xdem.DEM('../../Data_Paper/bed/malaspina_bed_epsg3338.tif').reproject(crs=32607)
glacier_bed = gu.Vector(gpd.read_file(f'{T}/rgi_outlines_map.geojson')).create_mask(bed_complete)
bed_complete.set_mask(~glacier_bed)
bed_map = np.ma.masked_invalid(bed_complete.reproject(sat_image).data.astype(float))


def panel_label(ax, s):
    ax.text(0.012, 0.97, s, transform=ax.transAxes, fontsize=FS_PANEL, fontweight='bold', va='top', ha='left',
            bbox=dict(boxstyle='round,pad=0.15', facecolor='lightgrey', alpha=0.9), zorder=10)


def velocity(ax, V):
    for lab, c in VEL:
        if f'mean_{lab}' in V:
            mean, std = V[f'mean_{lab}'].values, V[f'std_{lab}'].values
            ax.plot(V.km, mean, color=c, linewidth=1.8, label=f'{lab} Mean')
            ax.fill_between(V.km, mean - std, mean + std, color=c, alpha=0.3)
    ax.set_ylabel('Velocity\n(m a$^{-1}$)', fontsize=FS_LAB)
    ax.grid(True, alpha=0.2)
    ax.set_ylim(0, 3000)


def make(MODE):
    P = pd.read_csv(f'{T}/{MODE}_profiles.csv')
    V = pd.read_csv(f'{T}/{MODE}_velocity.csv')
    M = pd.read_csv(f'{T}/{MODE}_markers.csv')
    lay = json.load(open(f'{T}/profile_layout.json'))[MODE]
    line, x, shown, xmax = P[['x', 'y']].values, P.km.values, lay['shown'], lay['length_km']
    marks, mark_inds = list(M.km), list(M.sample_index)

    if MODE == 'centerline':
        b_lobe, b_trunk, ind_40, ind_70 = lay['b_lobe_km'], lay['b_trunk_km'], lay['ind_40'], lay['ind_70']
        zones = [(0, xmax - b_trunk, plasma(0.8)), (xmax - b_trunk, xmax - b_lobe, plasma(0.5)), (xmax - b_lobe, xmax, plasma(0.0))]
        line_cols = [(slice(None, ind_40), plasma(0.0)), (slice(ind_40, ind_70), plasma(0.5)), (slice(ind_70, None), plasma(0.8))]
        map_title, prof_title = 'Centerline and glacier bed', 'Elevation, bed, and velocity changes along the centerline'
        xlabel = 'Distance along centerline from its upper end (km)'
        heights = [3.0, 1.5, 1.5]
    else:
        ind_25 = lay['ind_25']
        zones = [(0, marks[2], plasma(0.5)), (marks[2], xmax, plasma(0.0))]
        line_cols = [(slice(None, ind_25), plasma(0.5)), (slice(ind_25, None), plasma(0.0))]
        map_title, prof_title = 'Transverse profile and glacier bed', 'Elevation, bed, and velocity changes along the transverse profile'
        xlabel = 'Distance along transverse line from its western end (km)'
        heights = [2.5, 1.2, 1.2, 1.2]

    W = 12.0
    L, R = 1.05, 0.15                      # left margin (y labels), right margin
    PW = W - L - R                         # profile panel width
    b = sat_image.bounds
    MAP_H = 4.0 if MODE == 'centerline' else 3.8
    MAP_W = MAP_H * (b.right - b.left) / (b.top - b.bottom)
    GAP_PANEL, TOP_TITLE, PROF_TITLE, XLAB = 0.18, 0.4, 0.95, 0.75
    H = TOP_TITLE + MAP_H + PROF_TITLE + sum(heights) + GAP_PANEL * (len(heights) - 1) + XLAB
    fig = plt.figure(figsize=(W, H))

    def add_ax(x0, y0, w, h, **kw):
        return fig.add_axes([x0 / W, y0 / H, w / W, h / H], **kw)

    # ---- a: map ----
    map_y = H - TOP_TITLE - MAP_H
    ax_map = add_ax(L, map_y, MAP_W, MAP_H)
    sat_image.plot(cmap='grey', add_cbar=False, ax=ax_map)
    im = ax_map.imshow(bed_map, cmap=cmocean.cm.delta, vmin=-1500, vmax=1500,
                       extent=[b.left, b.right, b.bottom, b.top], interpolation='nearest')
    for sl, c in line_cols:
        ax_map.scatter(line[sl, 0], line[sl, 1], color=c, s=2)
    for n, i in enumerate(mark_inds, 1):
        off = (-30, 26) if (MODE == 'crossline' and n == 1) else (0, 0)
        if MODE == 'centerline' and n in (6, 7, 8):   # three points within ~2 km: fan them out to the right
            off = {6: (26, 18), 7: (34, 0), 8: (26, -18)}[n]
        ax_map.annotate(str(n), (line[i, 0], line[i, 1]), xytext=off, textcoords='offset points', ha='center', va='center',
                        fontsize=FS_MARK - 1, zorder=6, bbox=dict(boxstyle='circle,pad=0.2', fc='white', ec='black', lw=1.0),
                        arrowprops=dict(arrowstyle='-', lw=1.8, color='black') if off != (0, 0) else None)
    ax_map.set_xlim(b.left, b.right); ax_map.set_ylim(b.bottom, b.top)
    ax_map.set_xticks([]); ax_map.set_yticks([])
    ax_map.set_title(map_title, fontsize=FS_TITLE, weight='bold', pad=16)
    panel_label(ax_map, 'a')
    cax = add_ax(L + MAP_W + 0.12, map_y, 0.22, MAP_H)
    cb = fig.colorbar(im, cax=cax)
    cb.set_label('Bed elevation (m)', fontsize=FS_LAB)
    cb.ax.tick_params(labelsize=FS_TICK)

    # date legend for panel b, beside the map
    leg_x = L + MAP_W + 0.12 + 0.22 + 1.25
    ax_leg = add_ax(leg_x, map_y, W - R - leg_x, MAP_H); ax_leg.axis('off')
    LEGENDS = [('b', r'OIB survey ($dh_{95}$)', [Line2D([], [], color=DATE_COLORS[d], lw=3, label=d) for d in shown], 3)]

    # ---- profile panels ----
    y = map_y - PROF_TITLE
    axs = []
    for h in heights:
        y -= h
        axs.append(add_ax(L, y, PW, h, sharex=axs[0] if axs else None))
        y -= GAP_PANEL
    ax_b = axs[0]
    ax_b.set_xlim(0, xmax)
    for d in shown:
        ax_b.plot(x, P[f'dh95_{d}'], color=DATE_COLORS[d], linewidth=1.5)
    ax_b.set_ylabel(r'$dh_{95}$ (m)', fontsize=FS_LAB)
    for n, p in enumerate(marks, 1):
        stagger = (MODE == 'centerline') * 19 * (n % 2)
        dx = {6: -6, 8: 6}.get(n, 0) if MODE == 'centerline' else 0
        ax_b.annotate(str(n), (p, 1.0), xycoords=('data', 'axes fraction'), xytext=(dx, 4 + stagger), textcoords='offset points',
                      ha='center', va='bottom', fontsize=FS_MARK, annotation_clip=False,
                      bbox=dict(boxstyle='circle,pad=0.15', fc='white', ec='black', lw=0.8))
    ax_b.set_title(prof_title, fontsize=FS_TITLE, weight='bold', pad=52 if MODE == 'centerline' else 32)

    nxt = 1
    if MODE == 'crossline':                  # c: elevation difference between the profiles bracketing each surge
        ax_dh = axs[1]; nxt = 2
        ok95 = np.isfinite(P['surf_1995-06-05'].values)
        for a_, b_ in [('2007-08-26', '2010-08-23'), ('2018-08-17', '2021-05-02')]:
            d = np.where(ok95, P[f'surf_{b_}'].values - P[f'surf_{a_}'].values, np.nan)
            ax_dh.fill_between(x, 0, d, where=np.isfinite(d), color=DATE_COLORS[b_], alpha=0.15, linewidth=0, interpolate=False)
            ax_dh.plot(x, d, color=DATE_COLORS[b_], linewidth=1.6, label=f'{a_[:4]}-{a_[5:7]} → {b_[:4]}-{b_[5:7]}')
        ax_dh.axhline(0, color='black', linewidth=0.8)
        ax_dh.set_ylabel('Δh (m)', fontsize=FS_LAB)
        LEGENDS.append(('c', 'Elevation difference', ax_dh.get_legend_handles_labels()[0], 2))

    ax_bed = axs[nxt]
    ax_bed.plot(x, P.bed_m, label='Bed', color='black', linewidth=2)
    ax_bed.plot(x, P['surf_1995-06-05'], label='1995 Ice Surface', color='blue', linewidth=2)
    ax_bed.set_ylabel('Elevation\n(m)', fontsize=FS_LAB)
    LEGENDS.append(('cd'[nxt - 1], 'Bed and surface', ax_bed.get_legend_handles_labels()[0], 2))

    ax_v = axs[nxt + 1]
    velocity(ax_v, V)
    LEGENDS.append(('de'[nxt - 1], 'Velocity (ITS_LIVE)', ax_v.get_legend_handles_labels()[0], 2))
    ax_v.set_xlabel(xlabel, fontsize=FS_LAB)

    for k, ax in enumerate(axs):
        for lo, hi, c in zones:
            ax.axvspan(lo, hi, color=c, alpha=SHADE, zorder=0, linewidth=0)
        for p in marks:
            ax.axvline(p, color='black', linestyle='--', linewidth=1.0)
        ax.tick_params(axis='both', which='major', labelsize=FS_TICK)
        if ax is not ax_v:
            ax.tick_params(axis='x', labelbottom=False)
        panel_label(ax, 'bcde'[k])

    # all legends stacked in the top-right block, one per panel
    fig.canvas.draw()
    ytop = 1.0
    for letter, title, handles, ncol in LEGENDS:
        lg = ax_leg.legend(handles=handles, title=f'({letter}) {title}', title_fontsize=FS_LEG, loc='upper left',
                           bbox_to_anchor=(0, ytop), ncol=ncol, fontsize=FS_LEG, handlelength=1.8, columnspacing=1.2,
                           labelspacing=0.4, frameon=False, borderaxespad=0)
        lg._legend_box.align = 'left'
        ax_leg.add_artist(lg)
        fig.canvas.draw()
        bb = lg.get_window_extent().transformed(ax_leg.transAxes.inverted())
        ytop = bb.y0 - 0.05

    out = os.path.join(OUTDIR, {'centerline': 'fig4_centerline.png', 'crossline': 'fig5_crossline.png'}[MODE])
    fig.savefig(out, bbox_inches='tight', dpi=300)
    plt.close(fig)
    print('saved', out)


for MODE in sys.argv[1:] or ['centerline', 'crossline']:
    make(MODE)
