# Cyclone Impact Analysis - Data Extraction Toolkit

A complete toolkit for extracting cyclone track data from IBTrACS, downloading Ookla connectivity data, and exporting everything to Excel for Tableau analysis. This system enables rapid cyclone impact assessment using real-world connectivity measurements.

## 🎯 What This Does

This project provides **two interactive Jupyter notebooks** that handle all data extraction:

1. **Cyclone_Extractor.ipynb** - Extract cyclone tracks from IBTrACS database
2. **Ookla_Extractor.ipynb** - Download Ookla connectivity data for any region

Both notebooks export directly to **Excel (.xlsx)** format ready for Tableau visualization.

## 🚀 Features

- **Cyclone Track Extraction**: Search IBTrACS database by year and region, export tracks to Excel
- **Region-Agnostic Design**: Works with any geographic region worldwide (8+ Indonesia regions pre-configured)
- **Automated Ookla Download**: Fetch connectivity data directly from AWS S3 (no credentials needed)
- **Geographic Filtering**: Uses Natural Earth boundaries for precise regional data extraction
- **Tableau-Ready Exports**: All outputs are Excel files optimized for Tableau
- **Interactive Workflow**: Complete analysis through Jupyter notebooks

## 📋 Prerequisites

- Python 3.8 or higher
- Internet connection for downloading data
- ~2GB free disk space for raw data

## ⚡ Quick Start

### Installation

#### macOS/Linux:
```bash
./setup.sh
```

#### Windows:
```cmd
setup.bat
```

#### Manual Installation:
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt
```

### Usage

#### Option 1: Extract Cyclone Tracks
```bash
# Activate environment
source venv/bin/activate  # Windows: venv\Scripts\activate.bat

# Launch Cyclone Extractor
jupyter notebook notebook/Cyclone_Extractor.ipynb
```

**In the notebook:**
1. Set your search parameters (year, region)
2. Run cells to search IBTrACS database
3. Select cyclone from results
4. Export track to Excel with temporal progression

**Output:** `data/output/cyclone_tracks/YYYY_Region/CYCLONE_NAME_track.xlsx`

#### Option 2: Download Ookla Data
```bash
# Launch Ookla Extractor
jupyter notebook notebook/Ookla_Extractor.ipynb
```

**In the notebook:**
1. Choose region preset (or define custom region)
2. Select time period (years/quarters)
3. Download Natural Earth boundaries
4. Download and filter Ookla data
5. Export to Excel for Tableau

**Output:** `data/output/ookla_REGION_YYYY_QQ.xlsx`

## 📁 Project Structure

```
Ookla_final/
├── notebook/
│   ├── Cyclone_Extractor.ipynb   # Extract cyclone tracks from IBTrACS
│   └── Ookla_Extractor.ipynb     # Download & process Ookla data
├── src/
│   ├── config.py                 # Region presets & configuration
│   ├── ibtracs_extractor.py      # IBTrACS database interface
│   ├── data_loader.py            # Natural Earth data loader
│   ├── download_ookla.py         # Ookla S3 data downloader
│   ├── download_natural_earth.py # Natural Earth downloader
│   └── prepare_tableau.py        # Excel export for Tableau
├── data/
│   ├── raw/                      # Downloaded raw data
│   │   ├── ibtracs/             # IBTrACS database
│   │   ├── natural_earth/       # Country/province boundaries
│   │   └── ookla/               # Ookla connectivity data
│   └── output/                   # Processed Excel files
│       ├── cyclone_tracks/      # Cyclone track exports
│       └── shapefiles/          # Geographic boundaries
├── requirements.txt              # Python dependencies
├── setup.sh / setup.bat          # Setup scripts
└── README.md                     # This file
```

## ⚙️ Configuration

### Pre-configured Regions (in `src/config.py`)

Indonesia regions ready to use:
- `indonesia_sumatra` - 10 Sumatra provinces
- `indonesia_java` - 6 Java provinces
- `indonesia_kalimantan` - 5 Kalimantan provinces
- `indonesia_sulawesi` - 6 Sulawesi provinces
- `indonesia_bali_nusa_tenggara` - 3 provinces
- `indonesia_maluku` - 2 Maluku provinces
- `indonesia_papua` - 2 Papua provinces

### Adding Custom Regions

Edit `src/config.py`:
```python
REGION_PRESETS = {
    'my_custom_region': {
        'name': 'My Study Area',
        'country': 'Country Name',
        'provinces': ['Province 1', 'Province 2', ...]
    }
}
```

## 📊 Typical Workflow

### Cyclone Impact Analysis
```bash
# 1. Extract cyclone track
jupyter notebook notebook/Cyclone_Extractor.ipynb
# → Search for cyclones in your year/region
# → Export track: data/output/cyclone_tracks/2024_Southeast_Asia/ROBYN_2024_track.xlsx

# 2. Download connectivity data
jupyter notebook notebook/Ookla_Extractor.ipynb  
# → Select region and time periods
# → Export: data/output/ookla_sumatra_2024.xlsx

# 3. Analyze in Tableau
# → Import both Excel files
# → Create maps, time series, dashboards
```

## 🔑 Key Components

### Cyclone Extractor Features
- **IBTrACS Integration**: Automatic download of global cyclone database
- **Smart Search**: Find cyclones by year, region, and intensity
- **Temporal Export**: Track points ordered by time for animation in Tableau
- **Wind Data**: Includes wind speed and pressure measurements

### Ookla Extractor Features
- **S3 Direct Access**: No AWS credentials needed (public data)
- **Multiple Regions**: Download data for any area worldwide
- **Time Series**: Download multiple years/quarters in one run
- **Mobile + Fixed**: Separate downloads for cellular and broadband
- **Province Tagging**: Automatically associates data with administrative regions

## 📦 Data Outputs

### Cyclone Track Excel Format
```
Columns: ISO_TIME, LAT, LON, BASIN, NAME, USA_WIND, USA_PRES
Sorted by: ISO_TIME (for temporal progression in Tableau)
Purpose: Overlay cyclone path on connectivity maps
```

### Ookla Excel Format
```
Columns: latitude, longitude, avg_d_kbps, avg_u_kbps, avg_lat_ms,
         tests, devices, province_name, year, quarter
Grouped by: Geographic tile + time period
Purpose: Create heatmaps and time series in Tableau
```

## 🛠️ Dependencies

### Core Libraries
- **pandas & numpy** - Data manipulation
- **geopandas & shapely** - Geospatial operations  
- **s3fs & boto3** - AWS S3 data access
- **openpyxl & xlsxwriter** - Excel export
- **jupyter** - Interactive notebooks
- **requests** - IBTrACS database download

See `requirements.txt` for complete list with versions.

## 🐛 Troubleshooting

### Installation Issues

**"Python not found"**
- Install Python 3.8+ from [python.org](https://www.python.org/)

**Permission denied (macOS/Linux)**
```bash
chmod +x setup.sh
./setup.sh
```

**Module not found**
- Make sure virtual environment is activated
- Re-run: `pip install -r requirements.txt`

### Data Download Issues

**S3 access errors**
- Check internet connection
- No AWS credentials needed (public data)
- Try again later if AWS S3 is temporarily unavailable

**Disk space warnings**
- Ookla data: ~500MB per region/year
- IBTrACS database: ~200MB
- Ensure 2GB free space minimum

**Slow downloads**
- Normal for first time (downloads full IBTrACS database)
- Subsequent runs use cached data
- Ookla downloads ~50-100MB/min depending on connection

### Notebook Issues

**Kernel crashes with large datasets**
- Reduce time range (fewer quarters)
- Process one region at a time
- Increase system memory if possible

**"No cyclones found"**
- Check year/region parameters
- Expand search bounding box
- Try adjacent years (cyclones may span year boundaries)

## 🎓 Use Cases

1. **Disaster Impact Assessment** - Measure connectivity changes during/after cyclones
2. **Infrastructure Resilience** - Compare recovery times across regions
3. **Network Planning** - Identify vulnerable areas for infrastructure investment
4. **Academic Research** - Correlate environmental events with connectivity patterns

## 🔄 Integration with Ookla_Cyclones

This toolkit **extracts and prepares data**. For advanced analysis:
- Full impact analysis pipeline → See `Ookla_Cyclones` project
- AppEEARS satellite integration → See `Ookla_Cyclones` project  
- Automated Tableau exports → See `Ookla_Cyclones` project
- Multi-cyclone comparisons → See `Ookla_Cyclones` project

## 📚 Related Documentation

- **Cyclone Search Parameters** - See `notebook/Cyclone_Extractor.ipynb`
- **Region Configuration** - See `src/config.py`
- **Ookla Data Structure** - Ookla Open Data documentation
- **IBTrACS Documentation** - [NOAA IBTrACS](https://www.ncei.noaa.gov/products/international-best-track-archive)

## 📄 License

This project is for academic and research purposes.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-region`)
3. Commit changes (`git commit -m 'Add new region preset'`)
4. Push to branch (`git push origin feature/new-region`)
5. Open a Pull Request

## 📧 Contact

For questions or issues, please open a GitHub issue.

---

**Next Steps:** After extracting data with this toolkit, use **Ookla_Cyclones** for comprehensive impact analysis and automated reporting.