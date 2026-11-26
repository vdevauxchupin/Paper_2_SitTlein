# Fig. S2: 2019-2022 elevation change rate with contours of the ITS_LIVE v02 composite surface speed (2014-2022 climatology).
# Inputs: Data_Paper/elevation_change/dhdt_2022_2019.tif (02_elevation_change.ipynb), Data_Paper/DEMs/dem_dates_icesat2.json (01_dems.ipynb),
#         ITS_LIVE v02 composite speed v (External_Data/ITS_LIVE_composite, EPSG:3413), RGI 6.0 outlines (External_Data).
# Usage: cd figures; python figS2_dhdt_2019_2022.py  -> output/figS2.png
import os, json
import numpy as np
import pandas as pd
import xarray as xr
import geopandas as gpd
import rasterio
import matplotlib.pyplot as plt
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.warp import reproject

VMIN, VMAX = -10, 10
LEVELS = np.arange(50, 501, 50)   # speed contours (m a-1), on the speed clipped to 0-500 m a-1
SOURCE = 'composite'   # 'composite': ITS_LIVE v02 composite (2014-2022 climatology); 'annual': annual composites weighted by the fraction of each year in the interval (as 06); 'timeseries': corrected time series

dates = json.load(open('../../Data_Paper/DEMs/dem_dates_icesat2.json'))
t0, t1 = np.datetime64(dates['2019']), np.datetime64(dates['2022'])   # speed period: 2019-2022 DEM interval

with rasterio.open('../../Data_Paper/elevation_change/dhdt_2022_2019.tif') as r:
    b, crs = r.bounds, r.crs
    dhdt = r.read(1, out_shape=(r.height // 5, r.width // 5), resampling=Resampling.average, masked=True).filled(np.nan)

# surface speed
if SOURCE == 'composite':
    from pyproj import Transformer
    from rasterio.windows import from_bounds as win
    tr = Transformer.from_crs(crs, 'EPSG:3413', always_xy=True)
    bx, by = tr.transform([b.left, b.right, b.left, b.right], [b.bottom, b.bottom, b.top, b.top])
    with rasterio.open('../../External_Data/ITS_LIVE_composite/ITS_LIVE_velocity_120m_RGI01A_0000_v02_v.tif') as r:
        w = win(min(bx) - 5e3, min(by) - 5e3, max(bx) + 5e3, max(by) + 5e3, r.transform)
        v = r.read(1, window=w, masked=True).astype('float32').filled(np.nan); wT = r.window_transform(w)
    v[v < 0] = np.nan
    speed = xr.DataArray(v, dims=('y', 'x'), coords={'x': wT.c + wT.a * (np.arange(v.shape[1]) + 0.5), 'y': wT.f + wT.e * (np.arange(v.shape[0]) + 0.5)})
elif SOURCE == 'annual':
    from pyproj import Transformer
    tr = Transformer.from_crs(crs, 'EPSG:3413', always_xy=True)
    bx, by = tr.transform([b.left, b.right, b.left, b.right], [b.bottom, b.bottom, b.top, b.top])
    T0, T1 = pd.Timestamp(t0), pd.Timestamp(t1); num = 0; den = 0
    for yr in range(T0.year, T1.year + 1):
        w = (min(T1, pd.Timestamp(f'{yr + 1}-01-01')) - max(T0, pd.Timestamp(f'{yr}-01-01'))).days / 365.25
        v = xr.open_dataset(f'../../External_Data/ITS_LIVE/ITS_LIVE_velocity_120m_RGI01A_{yr}_v02.nc')['v'].sel(
            x=slice(min(bx) - 5e3, max(bx) + 5e3), y=slice(max(by) + 5e3, min(by) - 5e3)).astype('float32')
        num = num + w * v.fillna(0); den = den + w * v.notnull()
    speed = (num / den).where(den > 0)
else:   # monthly medians of the corrected time series, then their mean (as in 05_centerlines)
    sel = lambda v: xr.open_dataset(f'../../Data_Paper/velocity_corrected/{v}_5D_10modes_1e4_correction.nc')[v].sel(mid_date=slice(t0, t1))
    speed = np.sqrt(sel('vx') ** 2 + sel('vy') ** 2)
    speed = speed.where(speed >= 0).resample(mid_date='1M').median(dim='mid_date').mean(dim='mid_date')
xs, ys = speed.x.values, speed.y.values
src_T = from_origin(xs[0] - (xs[1] - xs[0]) / 2, ys[0] + (ys[0] - ys[1]) / 2, xs[1] - xs[0], ys[0] - ys[1])
res = 100.0
nx, ny = int((b.right - b.left) / res), int((b.top - b.bottom) / res)
spd = np.full((ny, nx), np.nan, 'float32')
reproject(speed.values.astype('float32'), spd, src_transform=src_T, src_crs='EPSG:3413', dst_transform=from_origin(b.left, b.top, res, res),
          dst_crs=crs, resampling=Resampling.bilinear, src_nodata=np.nan, dst_nodata=np.nan)

rgi = gpd.read_file('../../External_Data/RGI60/01_rgi60_Alaska.shp').to_crs(crs).cx[b.left:b.right, b.bottom:b.top]

fig, ax = plt.subplots(figsize=(8, 8))
im = ax.imshow(dhdt, cmap='RdYlBu', vmin=VMIN, vmax=VMAX, extent=(b.left, b.right, b.bottom, b.top))
rgi.boundary.plot(ax=ax, color='dimgrey', lw=0.8)
X = b.left + res * (np.arange(nx) + 0.5); Y = b.top - res * (np.arange(ny) + 0.5)
ax.contour(X, Y, np.clip(spd, 0, 500), levels=LEVELS, colors='black', linewidths=1.2)
ax.set_xlim(b.left, b.right); ax.set_ylim(b.bottom, b.top + 0.25 * (b.top - b.bottom))
ax.set_xticks([]); ax.set_yticks([])
ax.set_title('Elevation change rate 2019–2022 and velocity contours', fontsize=15, weight='bold')
fig.colorbar(im, ax=ax, fraction=0.046, pad=0.02).set_label(r'$\Delta h/\Delta t$ (m a$^{-1}$)')
os.makedirs('output', exist_ok=True)
fig.savefig('output/figS2.png', dpi=300, bbox_inches='tight')
print(f'saved output/figS2.png ({SOURCE} speed, contours {list(LEVELS)} m a-1)')
