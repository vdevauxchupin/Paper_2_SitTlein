# Fig. S7: 2002-2012 elevation change rate, whole lobe (location of the zoom) and zoom on the sinkhole texture of Agassiz's lobe.
# Inputs: Data_Paper/elevation_change/dhdt_2012_2002.tif (02_elevation_change.ipynb).
# Usage: cd figures; python figS7_texture.py  -> output/figS7.png
import os
import numpy as np
import rasterio
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from rasterio.enums import Resampling
from rasterio.windows import from_bounds

X0, Y0, SIZE = 498e3, 6636e3, 10e3   # zoom window (EPSG:32607, m)
VMIN, VMAX = -8, 8

with rasterio.open('../../Data_Paper/elevation_change/dhdt_2012_2002.tif') as r:
    b = r.bounds
    full = r.read(1, out_shape=(r.height // 5, r.width // 5), resampling=Resampling.average)
    zoom = r.read(1, window=from_bounds(X0, Y0, X0 + SIZE, Y0 + SIZE, r.transform))

fig, axs = plt.subplots(1, 2, figsize=(14, 6.5), gridspec_kw={'width_ratios': [1.45, 1]})
km = lambda v: v / 1e3
axs[0].imshow(full, cmap='RdBu', vmin=VMIN, vmax=VMAX, extent=(km(b.left), km(b.right), km(b.bottom), km(b.top)))
axs[0].add_patch(Rectangle((km(X0), km(Y0)), km(SIZE), km(SIZE), fill=False, ec='black', lw=2))
axs[0].set_xlim(490, 560); axs[0].set_ylim(6620, 6665)
im = axs[1].imshow(zoom, cmap='RdBu', vmin=VMIN, vmax=VMAX, extent=(km(X0), km(X0 + SIZE), km(Y0), km(Y0 + SIZE)))
for ax, lab in zip(axs, ['a', 'b']):
    ax.set_xlabel('Easting (km)'); ax.set_ylabel('Northing (km)')
    ax.text(0.02, 0.97, f'({lab})', transform=ax.transAxes, va='top', fontsize=14, weight='bold')
fig.colorbar(im, ax=axs, shrink=0.8, pad=0.02).set_label(r'$\Delta h/\Delta t$ 2002–2012 (m a$^{-1}$)')
os.makedirs('output', exist_ok=True)
fig.savefig('output/figS7.png', dpi=300, bbox_inches='tight')
print('saved output/figS7.png')
