# Code: Surges and debris cover cannot outpace melt and calving on Sít’ Tlein (Devaux-Chupin et al., The Cryosphere)

Notebooks and scripts that produce the ICESat-2 DEMs, elevation change rates, tables and figures of the paper (Python 3.12.8).

## Folder layout

Keep all sub-folders in one folder. Paths are relative.

```
<root>/
  Code_Paper/      this folder
  Data_Paper/      deposited data: inputs to later steps and outputs of the notebooks
  External_Data/   public inputs to download (list below)
```

Environment: `conda env create -f environment.yml`, then `conda activate sittlein-paper2`.

## Running

Run the notebooks in order from `Code_Paper/`, then the figure scripts from `Code_Paper/figures/` (`cd figures; python fig3.py`). Each notebook writes its products into `Data_Paper/`; steps 03, 04 and 06 read the dh/dt, uncertainty and variogram files written by step 02; the figure scripts read only `Data_Paper/` (plus RGI outlines and backdrop imagery from `External_Data/`) and write to `figures/output/`.

| Step | Content | Writes |
|---|---|---|
| `01_dems.ipynb` | ICESat-2 ATL06 download (SlideRule) and filtering; ICESat-2 outlier removal; coregistration of the SRTM X-SAR (two passes), IfSAR 2002 and 2012 DEMs (GEOID09 for 2012); 2019 and 2022 DEMs from ICESat-2 (multiquadric RBF) | `External_Data/ICESat-2/icesat_2_data.shp`, `Data_Paper/ICESat-2/`, `Data_Paper/DEMs/` |
| `02_elevation_change.ipynb` | Elevation change rates and uncertainties (xDEM, Hugonnet et al., 2022) for 1999–2002, 2002–2012, 2012–2019, 2019–2022 and 1999–2022 | `Data_Paper/elevation_change/` |
| `03_surge_transfer.ipynb` | Volume transfer between surge reservoirs and receiving areas; tributary hypsometry (Fig. 3) | `Data_Paper/tables/surge_transfer/` |
| `04_surface_cover.ipynb` | Elevation change rates per surface cover and the −5 m a⁻¹ melt-feature threshold (Fig. 6); 2002–2012 velocity (Fig. S1) | `Data_Paper/tables/surface_cover/` |
| `05_centerlines.ipynb` | OIB, velocity and bed profiles along the centerline and transverse line; zones (Table 2) | `Data_Paper/tables/centerlines/` |
| `06_mass_continuity.ipynb` | Ice flux through the gates, flux divergence and surface mass balance per lobe (Table 4, Fig. 7); surface mass balance by surface cover | `Data_Paper/tables/mass_continuity/`, `Data_Paper/vectors/lobe_mask_downstream_of_gates.tif` |

| Figure script | Figure | Needs steps |
|---|---|---|
| `fig3.py` | Fig. 3, elevation change rates and tributary hypsometry | 02, 03 |
| `fig4_5_profiles.py` | Figs. 4 and 5, centerline and transverse profiles (`python fig4_5_profiles.py centerline` or `crossline`; both by default) | 05 |
| `fig6.py` | Fig. 6, elevation change rates per surface cover | 04 |
| `fig7.py` | Fig. 7, mass continuity per lobe | 06 |
| `figS1.py` | Fig. S1, 2002–2012 velocity vs elevation change rate; also writes the velocity percentiles per surface cover | 02, 04, 06 |
| `figS3_ndvi.py` | Fig. S3, NDVI vegetation change 1974–2024 | none |

Figs. 1, 2, S2 and S4–S6 are maps or ITS_LIVE plots made outside this code.

## External_Data

| Path | Content | Source |
|---|---|---|
| `raw_DEMs/1999.tif` | SRTM X-SAR DEM | DLR, https://download.geoservice.dlr.de/SRTM_XSAR/ |
| `raw_DEMs/2002-08-04.tif`, `raw_DEMs/2012-08-30.tif` | IfSAR 2002 and 2012 DEMs | USGS EROS, IfSAR Alaska |
| `raw_DEMs/us_noaa_geoid09_ak.tif` | GEOID09 Alaska | NOAA, via PROJ data |
| `ITS_LIVE/ITS_LIVE_velocity_120m_RGI01A_<year>_v02.nc` | ITS_LIVE annual velocity mosaics, 120 m | https://its-live.jpl.nasa.gov |
| `velocity_corrected/vx_5D_10modes_1e4_correction.nc`, `vy_…` | Corrected velocity time series | Devaux-Chupin et al. (2025) |
| `RGI60/01_rgi60_Alaska.shp` | RGI 6.0, region 01 | NSIDC-0770 |
| `imagery/Sat_im.tiff`, `imagery/Sat_Im.tiff` | Sentinel-2 / Landsat backdrops (figures only) | Copernicus / USGS |
| `landsat_ndvi/*.TIF` | Landsat Collection 2 Level-1 bands (green, red, NIR) of LM01_L1TP_068018_19740701_20200908_02_T2, LM05_L1TP_062018_19840921_20200902_02_T2, LM05_L1TP_062018_19940816_20200823_02_T2, LE07_L1TP_062018_20040803_20200915_02_T1, LC08_L1TP_062018_20140924_20200910_02_T1, LC09_L1TP_063018_20240614_20240615_02_T1 | USGS EarthExplorer |

ICESat-2 ATL06 data are downloaded by `01_dems.ipynb` through SlideRule (NSIDC) to `ICESat-2/icesat_2_data.shp`.
