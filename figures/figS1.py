# Fig. S1: 2002-2012 surface velocity vs elevation change rate (hexbin) for the whole lobe and each surface cover.
# Masks = surface-cover polygons intersected with the RGI 6.0 tributary outlines, pooled over Agassiz | Seward | Marvine.
# Inputs: Data_Paper/elevation_change/dhdt_2012_2002.tif, Data_Paper/tables/surface_cover/velocity_2002_2012.tif
# (04_surface_cover.ipynb), Data_Paper/vectors/Area_*.shp, External_Data/RGI60.
# Also writes output/velocity_percentiles_by_surface_2002_2012.csv (velocity statistics per surface cover quoted in the mass continuity section).
# Usage: cd figures; python figS1.py  -> output/figS1.png
import os
import numpy as np
import geopandas as gpd
import geoutils as gu
import matplotlib.pyplot as plt
from shapely import intersection
from shapely.ops import unary_union

dhdt_0212 = gu.Raster('../../Data_Paper/elevation_change/dhdt_2012_2002.tif')

_outl = gu.Vector('../../External_Data/RGI60/01_rgi60_Alaska.shp').ds
_goi = _outl[_outl['RGIId'].isin(['RGI60-01.13696', 'RGI60-01.23653', 'RGI60-01.23649'])]
_tribs = {'Agassiz': _goi[_goi['RGIId'] == 'RGI60-01.23649'].reset_index(drop=True),
          'Seward': _goi[_goi['RGIId'] == 'RGI60-01.13696'].reset_index(drop=True),
          'Marvine': _goi[_goi['RGIId'] == 'RGI60-01.23653'].reset_index(drop=True)}
_areas = {'Vegetation-covered ice': gpd.read_file('../../Data_Paper/vectors/Area_forelands.shp'),
          'Active ice': gpd.read_file('../../Data_Paper/vectors/Area_cleanice.shp'),
          'Debris-covered ice': gpd.read_file('../../Data_Paper/vectors/Area_moraines.shp')}

def _union_mask(glacier_gdf, area_gdf):  # as create_union_mask in 04_surface_cover.ipynb
    if glacier_gdf.crs != area_gdf.crs:
        glacier_gdf = glacier_gdf.to_crs(area_gdf.crs)
    geom = intersection(glacier_gdf.geometry.iloc[0], unary_union(area_gdf.geometry.tolist()))
    return gpd.GeoDataFrame({'geometry': [geom]}, crs=glacier_gdf.crs)

_trib = {g: {a: gu.Vector(_union_mask(gdf, adf)).create_mask(dhdt_0212) for a, adf in _areas.items()} for g, gdf in _tribs.items()}
pooled_v5 = {a: (_trib['Agassiz'][a] | _trib['Seward'][a] | _trib['Marvine'][a]).data.filled(False).astype(bool) for a in _areas}

vel_0212 = gu.Raster('../../Data_Paper/tables/surface_cover/velocity_2002_2012.tif').reproject(dhdt_0212)
vel_h = vel_0212.data.filled(np.nan).astype(float)
vel_h[vel_h < 0] = np.nan  # negative -> NaN
titles = ["Whole lobe", "Vegetation-covered ice", "Clean ice", "Debris-covered ice"]
masks_v5 = [pooled_v5['Vegetation-covered ice'] | pooled_v5['Active ice'] | pooled_v5['Debris-covered ice'],
            pooled_v5['Vegetation-covered ice'], pooled_v5['Active ice'], pooled_v5['Debris-covered ice']]

fig, axes = plt.subplots(2, 2, figsize=(13, 10))
for ax, title, m in zip(axes.flatten(), titles, masks_v5):
    x = dhdt_0212.data.filled(np.nan).astype(float)[m]; y = vel_h[m]
    ok = np.isfinite(x) & np.isfinite(y); x, y = x[ok], y[ok]
    ytop = y.max() * 1.02  # data maximum: no hexes cut off in y
    hb = ax.hexbin(x, y, gridsize=(80, 50), extent=(-20, 20, 0, ytop), bins='log', mincnt=1, cmap='viridis')
    fig.colorbar(hb, ax=ax, pad=0.01).set_label('Pixel count (log)')
    ax.axvline(-5, color='red', linestyle='--', linewidth=2, label=r'Threshold (−5 m a$^{-1}$)')
    ax.text(0.02, 0.97, f'{np.mean(x < -5) * 100:.1f}% of pixels < −5', transform=ax.transAxes, va='top', fontsize=10)
    ax.legend(loc='upper right')
    ax.set_xlim(-20, 20); ax.set_ylim(0, ytop)
    ax.set_title(title, fontsize=13, weight='bold')
    ax.set_xlabel(r'Elevation change rate (m a$^{-1}$)')
    ax.set_ylabel(r'Velocities (m a$^{-1}$)')
    print(f'{title}: n = {len(x)}, fraction < -5 = {np.mean(x < -5):.4f}')
fig.suptitle('Velocities vs surface change rates, 2002 to 2012', fontsize=15, weight='bold')
plt.tight_layout()
os.makedirs('output', exist_ok=True)
fig.savefig('output/figS1.png', dpi=300)
print('saved output/figS1.png')

# Velocity percentiles per surface cover: S1 masks, and the same restricted to the lobe mask downstream of the gates
_lobe = gu.Raster('../../Data_Paper/vectors/lobe_mask_downstream_of_gates.tif').reproject(dhdt_0212, resampling='nearest')
_lobe = _lobe.data.filled(0).astype(bool)
_rows = []
for _t, _m in zip(titles, masks_v5):
    for _sc, _mm in [('S1 mask', _m), ('S1 mask & lobe below gates', _m & _lobe)]:
        _v = vel_h[_mm]; _v = _v[np.isfinite(_v)]
        _rows.append({'surface': _t, 'domain': _sc, 'n': _v.size, 'p50': np.percentile(_v, 50), 'p90': np.percentile(_v, 90),
                      'p95': np.percentile(_v, 95), 'p99': np.percentile(_v, 99), 'max': _v.max(),
                      'pct_below_10': 100 * np.mean(_v < 10), 'pct_below_50': 100 * np.mean(_v < 50)})
import pandas as pd
_pct = pd.DataFrame(_rows); _pct.to_csv('output/velocity_percentiles_by_surface_2002_2012.csv', index=False)
print(_pct.round(1).to_string(index=False))
