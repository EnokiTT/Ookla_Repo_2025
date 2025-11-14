# Ookla Connectivity Data Analysis System

A scalable, region-agnostic system for downloading, processing, and analyzing Ookla connectivity data with geographic filtering capabilities.

## Features

- **Region-Agnostic Design**: Works with any geographic region worldwide
- **Automated Data Download**: Fetch Ookla data directly from AWS S3
- **Geographic Filtering**: Uses Natural Earth boundaries for precise regional data extraction
- **Tableau Integration**: Export processed data to Excel format for visualization
- **Interactive Notebook**: Jupyter notebook for complete workflow management

## Prerequisites

- Python 3.8 or higher
- Internet connection for downloading data
- AWS credentials (optional, for authenticated S3 access)

## Quick Start

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
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt
```

### Usage

1. **Activate your virtual environment** (if you created one):
   ```bash
   source venv/bin/activate  # On Windows: venv\Scripts\activate.bat
   ```

2. **Start Jupyter Notebook**:
   ```bash
   jupyter notebook notebook/Ookla_Extractor.ipynb
   ```

3. **Follow the notebook cells** to:
   - Configure your region of interest
   - Download Ookla data
   - Download Natural Earth boundaries
   - Process and filter data
   - Export to Excel for Tableau

## Project Structure

```
Ookla_final/
├── src/
│   ├── config.py           # Configuration and region presets
│   ├── data_loader.py      # Natural Earth data loader
│   ├── download_ookla.py   # Ookla S3 data downloader
│   └── prepare_tableau.py  # Excel export for Tableau
├── notebook/
│   └── Ookla_Extractor.ipynb  # Interactive workflow notebook
├── data/                   # Data directory (gitignored)
│   ├── raw/               # Downloaded raw data
│   └── output/            # Processed Excel files
├── requirements.txt        # Python dependencies
├── setup.sh               # Setup script for macOS/Linux
├── setup.bat              # Setup script for Windows
└── README.md              # This file
```

## Configuration

Edit `src/config.py` to:
- Add new region presets
- Customize output directories
- Adjust Tableau export settings

## Available Regions

Pre-configured regions include:
- Indonesia (Sumatra)
- Philippines (Luzon)

You can easily add more regions by defining bounding boxes in `config.py`.

## Dependencies

Key packages:
- **pandas & numpy**: Data manipulation
- **geopandas & shapely**: Geospatial processing
- **s3fs & boto3**: AWS S3 access
- **xlsxwriter**: Excel export
- **jupyter**: Interactive notebooks

See `requirements.txt` for complete list.

## Troubleshooting

### Installation Issues

1. **"Python not found"**: Install Python 3.8+ from [python.org](https://www.python.org/)
2. **Permission denied**: Run `chmod +x setup.sh` (macOS/Linux)
3. **Module not found**: Activate virtual environment first

### Data Download Issues

1. **S3 access errors**: Check internet connection; AWS credentials not required for public data
2. **Disk space**: Ensure sufficient space in `/data` directory

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is for academic/research purposes.

## Contact

For questions or issues, please open a GitHub issue.