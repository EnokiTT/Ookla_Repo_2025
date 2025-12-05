"""
Configuration module for Ookla Connectivity Analysis
Defines regions, time periods, and analysis parameters in a scalable way
"""

from pathlib import Path

# ═══════════════════════════════════════════════════════════════════
# PROJECT PATHS
# ═══════════════════════════════════════════════════════════════════

def get_project_root():
    """Get the project root directory"""
    if '__file__' in globals():
        return Path(__file__).parent.parent
    else:
        # Running in notebook
        return Path.cwd().parent if Path.cwd().name == 'notebook' else Path.cwd()

PROJECT_ROOT = get_project_root()
DATA_DIR = PROJECT_ROOT / 'data'
RAW_DIR = DATA_DIR / 'raw'
OUTPUT_DIR = DATA_DIR / 'output'
NATURAL_EARTH_DIR = RAW_DIR / 'natural_earth'
OOKLA_DIR = RAW_DIR / 'ookla'

# Ensure directories exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OOKLA_DIR.mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════════════════════════════
# REGION PRESETS
# Define your study regions here
# ═══════════════════════════════════════════════════════════════════

REGION_PRESETS = {
    'indonesia_sumatra': {
        'name': 'Sumatra Region',
        'country': 'Indonesia',
        'provinces': [
            'Aceh', 'Sumatera Utara', 'Sumatera Barat', 'Riau',
            'Jambi', 'Sumatera Selatan', 'Bengkulu', 'Lampung',
            'Bangka-Belitung', 'Kepulauan Riau'
        ]
    },
    'indonesia_java': {
        'name': 'Java Region',
        'country': 'Indonesia',
        'provinces': [
            'Banten', 'Jakarta Raya', 'Jawa Barat', 'Jawa Tengah',
            'Yogyakarta', 'Jawa Timur'
        ]
    },
    'indonesia_kalimantan': {
        'name': 'Kalimantan Region',
        'country': 'Indonesia',
        'provinces': [
            'Kalimantan Barat', 'Kalimantan Tengah', 'Kalimantan Selatan', 'Kalimantan Timur',
            'Kalimantan Utara'
        ]
    },
    'indonesia_sulawesi': {
        'name': 'Sulawesi Region',
        'country': 'Indonesia',
        'provinces': [
            'Sulawesi Utara', 'Gorontalo', 'Sulawesi Tengah', 'Sulawesi Selatan',
            'Sulawesi Tenggara', 'Sulawesi Barat'
        ]
    },
    'indonesia_bali_nusa_tenggara': {
        'name': 'Bali and Nusa Tenggara Region',
        'country': 'Indonesia',
        'provinces': [
            'Bali', 'Nusa Tenggara Barat', 'Nusa Tenggara Timur'
        ]
    },
    'indonesia_maluku': {
        'name': 'Maluku Region',
        'country': 'Indonesia',
        'provinces': [
            'Maluku', 'Maluku Utara'
        ]
    },
    'indonesia_papua': {
        'name': 'Papua Region',
        'country': 'Indonesia',
        'provinces': [
            'Papua', 'Papua Barat' ,
        ]
    },
    # Add more regions as needed
}

# ═══════════════════════════════════════════════════════════════════
# OOKLA DATA CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

OOKLA_CONFIG = {
    'base_url': 's3://ookla-open-data/parquet/performance',
    'data_types': ['mobile', 'fixed'],
    'available_years': list(range(2019, 2026)),  # 2019-2025
    'available_quarters': [1, 2, 3, 4],
    'default_columns': [
        'quadkey',
        'tile',
        'avg_d_kbps',
        'avg_u_kbps',
        'avg_lat_ms',
        'tests',
        'devices'
    ]
}

# ═══════════════════════════════════════════════════════════════════
# TABLEAU EXPORT CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

TABLEAU_CONFIG = {
    'excel_row_limit': 900000,  # Keep under 1M Excel limit
    'include_statistics': True,
    'create_separate_sheets': True,  # Mobile and Fixed in separate files
}

# ═══════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def get_region_info(region_key):
    """
    Get region configuration by key
    
    Parameters:
        region_key (str): Key from REGION_PRESETS
    
    Returns:
        dict: Region configuration
    """
    if region_key not in REGION_PRESETS:
        available = ', '.join(REGION_PRESETS.keys())
        raise ValueError(
            f"Region '{region_key}' not found.\n"
            f"Available regions: {available}"
        )
    return REGION_PRESETS[region_key]

def list_available_regions():
    """List all available region presets"""
    print("Available Regions:")
    print("=" * 60)
    for key, info in REGION_PRESETS.items():
        print(f"  • {key:25s} - {info['name']} ({info['country']})")
        print(f"    Provinces: {len(info['provinces'])}")
    print("=" * 60)

def validate_year_quarter(year, quarter):
    """Validate year and quarter selection"""
    if year not in OOKLA_CONFIG['available_years']:
        raise ValueError(
            f"Year {year} not available. "
            f"Available: {OOKLA_CONFIG['available_years']}"
        )
    if quarter not in OOKLA_CONFIG['available_quarters']:
        raise ValueError(
            f"Quarter {quarter} not valid. "
            f"Available: {OOKLA_CONFIG['available_quarters']}"
        )
    return True

if __name__ == '__main__':
    # Test configuration
    print("Configuration Loaded Successfully")
    print("=" * 60)
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Data Directory: {DATA_DIR}")
    print(f"Natural Earth: {NATURAL_EARTH_DIR}")
    print(f"Ookla Data: {OOKLA_DIR}")
    print()
    list_available_regions()
