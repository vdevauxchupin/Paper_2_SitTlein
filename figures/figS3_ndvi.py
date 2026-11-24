"""Fig. S3: vegetation change on the lobe from Landsat NDVI, 1974-2024.

Run: cd figures; python figS3_ndvi.py
Inputs: ../../External_Data/landsat_ndvi/*.TIF (Landsat green/red/NIR bands, one scene per year),
        ../../Data_Paper/vectors/ndvi/AOI.shp, ../../Data_Paper/vectors/Area_cleanice.shp
Output: output/figS3.png
"""
import os
import geoutils as gu
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm

IMG_DIR = '../../External_Data/landsat_ndvi'
os.makedirs('output', exist_ok=True)

# 30 m grid over the AOI
AOI = gu.Vector('../../Data_Paper/vectors/ndvi/AOI.shp').rasterize(xres=30, yres=30)

# Group band files by year
files = os.listdir(IMG_DIR)
year_groups = {}
for file in files:
    date = file.split('_')[3]
    year = int(date[:4])
    band = file.split('_')[-1].split('.')[0]

    if year not in year_groups:
        year_groups[year] = {}

    year_groups[year][band] = file

# Sorted band numbers per sensor = green, red, NIR (MSS B4-6 / B1-3, ETM+ B2-4, OLI B3-5)
data = {}
for year in sorted(year_groups.keys()):
    bands = year_groups[year]
    band_nums = [int(b[1:]) for b in bands.keys()]
    band_nums.sort()

    data[year] = {
        'green': gu.Raster(f"{IMG_DIR}/{bands[f'B{band_nums[0]}']}").reproject(AOI),
        'red': gu.Raster(f"{IMG_DIR}/{bands[f'B{band_nums[1]}']}").reproject(AOI),
        'NIR': gu.Raster(f"{IMG_DIR}/{bands[f'B{band_nums[2]}']}").reproject(AOI)
    }

# NDVI and binary vegetation mask (1 where 0 < NDVI <= 1)
ndvi_data = {}
for year in data.keys():
    nir = data[year]['NIR']
    red = data[year]['red']
    ndvi = (nir - red) / (nir + red)

    ndvi_binary = ndvi.data.data.copy()
    ndvi_binary[ndvi.data.data > 1] = 0
    ndvi_binary[ndvi_binary > 0] = 1
    ndvi_binary = ndvi_binary.astype(np.float32)
    ndvi_binary[red.data.mask] = np.nan

    ndvi_binary = gu.Raster.from_array(ndvi_binary, transform=ndvi.transform, crs=ndvi.crs)
    ndvi_data[year] = ndvi_binary

filter_cleanice = gu.Vector('../../Data_Paper/vectors/Area_cleanice.shp').rasterize(AOI)

# Pair comparison: 1 both vegetated, 2 only 1st year, 3 only 2nd year, NaN neither / no data / clean ice
comparison_data = {}

year_pairs = [
    (1974, 1984),
    (1984, 1994),
    (1994, 2004),
    (2004, 2014),
    (2014, 2024),
    (1974, 2024)  # Long-term comparison
]

for year1, year2 in year_pairs:
    arr1 = ndvi_data[year1].data.data
    arr2 = ndvi_data[year2].data.data

    comparison = np.zeros_like(arr1, dtype=np.float32)

    valid1 = ~np.isnan(arr1)
    valid2 = ~np.isnan(arr2)
    both_valid = valid1 & valid2

    both_vegetation = both_valid & (arr1 == 1) & (arr2 == 1)
    comparison[both_vegetation] = 1

    only_year1 = both_valid & (arr1 == 1) & (arr2 == 0)
    comparison[only_year1] = 2

    only_year2 = both_valid & (arr1 == 0) & (arr2 == 1)
    comparison[only_year2] = 3

    both_no_vegetation = both_valid & (arr1 == 0) & (arr2 == 0)
    comparison[both_no_vegetation] = np.nan

    no_data = (~valid1) | (~valid2)
    comparison[no_data] = np.nan

    # Filter out clean ice areas
    comparison[filter_cleanice.data.data > 0] = np.nan

    comparison_raster = gu.Raster.from_array(
        comparison,
        transform=ndvi_data[year1].transform,
        crs=ndvi_data[year1].crs
    )

    pair_key = f"{year2}-{year1}"
    comparison_data[pair_key] = comparison_raster

colors = [
    'black',    # value 1 (stable vegetation)
    '#d73027',  # value 2 (vegetation loss)
    '#1a9850'   # value 3 (vegetation gain)
]
cmap = ListedColormap(colors)
bounds = [0.5, 1.5, 2.5, 3.5]
norm = BoundaryNorm(bounds, cmap.N)

n_plots = len(comparison_data)
n_cols = 2
n_rows = (n_plots + n_cols - 1) // n_cols

fig = plt.figure(figsize=(12, 4 * n_rows + 1))

gs_main = fig.add_gridspec(n_rows, n_cols, hspace=0.3, wspace=0.3,
                          top=0.85, bottom=0.05, left=0.05, right=0.95)

gs_cbar = fig.add_gridspec(1, 1, top=0.95, bottom=0.88, left=0.2, right=0.8)
cbar_ax = fig.add_subplot(gs_cbar[0, 0])

for i, (pair_key, raster) in enumerate(comparison_data.items()):
    row = i // n_cols
    col = i % n_cols
    ax = fig.add_subplot(gs_main[row, col])

    raster.plot(ax=ax, cmap=cmap, add_cbar=False)
    ax.set_title(f'Vegetation Change {pair_key}', fontsize=16, fontweight='bold')

    ax.set_xticks([])
    ax.set_yticks([])

cbar = plt.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap),
                   cax=cbar_ax, orientation='horizontal')

cbar.set_ticks([])
cbar.set_ticklabels([])

label_positions = [1, 2, 3]
labels = ['Stable vegetation', 'Vegetation loss', 'Vegetation gain']
for pos, label in zip(label_positions, labels):
    cbar_ax.text(pos, 0.5, label, ha='center', va='center',
                fontsize=12, fontweight='bold', transform=cbar_ax.transData, color='white')

# Original S3.png (1100x1157 px) was saved from the inline notebook figure (dpi 100, tight bbox)
fig.savefig('output/figS3.png', dpi=100, bbox_inches='tight')

# Summary statistics
for pair_key, raster in comparison_data.items():
    data = raster.data.data
    valid_data = data[~np.isnan(data)]
    if len(valid_data) > 0:
        stable_count = np.sum(valid_data == 1)
        loss_count = np.sum(valid_data == 2)
        gain_count = np.sum(valid_data == 3)
        total_valid = len(valid_data)

        print(f"\n{pair_key}:")
        print(f"  Stable vegetation: {stable_count:,} pixels ({stable_count/total_valid*100:.1f}%)")
        print(f"  Vegetation loss: {loss_count:,} pixels ({loss_count/total_valid*100:.1f}%)")
        print(f"  Vegetation gain: {gain_count:,} pixels ({gain_count/total_valid*100:.1f}%)")
        print(f"  Total valid pixels: {total_valid:,}")
