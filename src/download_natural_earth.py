"""
Download Natural Earth geographic boundary data.

This module provides functionality to download Natural Earth vector data,
which is used for geographic boundary filtering in the Ookla analysis workflow.

Usage:
    # From notebook or script
    from src.download_natural_earth import download_natural_earth
    download_natural_earth()
    
    # From command line
    python src/download_natural_earth.py
"""

import subprocess
from pathlib import Path
import sys

def download_natural_earth(force_redownload=False):
    """
    Download and extract Natural Earth vector data.
    
    This downloads the complete Natural Earth vector dataset containing
    country boundaries, province/state boundaries, and other geographic features
    at multiple scales (10m, 50m, 110m).
    
    Args:
        force_redownload (bool): If True, re-download even if data exists
        
    Returns:
        bool: True if successful, False otherwise
    """
    
    # Define paths
    try:
        # Try to get project root from __file__ (when run as script)
        project_root = Path(__file__).parent.parent
    except NameError:
        # Fallback for notebook environment
        project_root = Path.cwd().parent
    
    data_dir = project_root / 'data' / 'raw'
    data_dir.mkdir(parents=True, exist_ok=True)
    
    ne_dir = data_dir / 'natural_earth'
    zip_file = data_dir / 'natural_earth_vector.zip'
    
    print("=" * 70)
    print("Natural Earth Vector Data Download")
    print("=" * 70)
    
    # Check if already downloaded
    if not force_redownload and ne_dir.exists() and any(ne_dir.rglob('*.shp')):
        print(f"\n✅ Natural Earth data already exists at:")
        print(f"   {ne_dir}")
        
        # Count files
        shp_count = len(list(ne_dir.rglob('*.shp')))
        print(f"\n   Found {shp_count} shapefiles")
        print("\n   This data is used for all regions worldwide.")
        print("   No need to re-download unless data is corrupted.")
        return True
    
    print("\n📥 Downloading Natural Earth Vector data...")
    print("   Dataset: Complete vector package (all regions worldwide)")
    print("   Size: ~150 MB")
    print(f"   Destination: {data_dir}")
    print("\n   This is a one-time download. Data works for ALL geographic regions.")
    
    ne_dir.mkdir(parents=True, exist_ok=True)
    
    url = "https://naciscdn.org/naturalearth/packages/natural_earth_vector.zip"
    
    # Try multiple download methods
    download_success = False
    
    # Method 1: curl (usually available on macOS/Linux)
    if not download_success:
        try:
            print("\n   Trying curl...")
            subprocess.run(
                ['curl', '-L', '-o', str(zip_file), url],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            download_success = True
            print("   ✅ Download successful (curl)")
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
    
    # Method 2: wget (fallback)
    if not download_success:
        try:
            print("   Trying wget...")
            subprocess.run(
                ['wget', '-O', str(zip_file), url],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            download_success = True
            print("   ✅ Download successful (wget)")
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
    
    # Method 3: Python urllib (last resort, works everywhere)
    if not download_success:
        try:
            print("   Trying Python downloader...")
            import urllib.request
            urllib.request.urlretrieve(url, str(zip_file))
            download_success = True
            print("   ✅ Download successful (Python)")
        except Exception as e:
            print(f"   ❌ Download failed: {e}")
            return False
    
    if not download_success:
        print("\n❌ Failed to download Natural Earth data")
        print("   Please check your internet connection and try again")
        return False
    
    print("\n📦 Extracting data...")
    
    # Try to extract
    try:
        # Method 1: unzip (macOS/Linux)
        try:
            subprocess.run(
                ['unzip', '-q', '-o', str(zip_file), '-d', str(ne_dir)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            print("   ✅ Extraction successful (unzip)")
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Method 2: Python zipfile (works everywhere)
            import zipfile
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                zip_ref.extractall(ne_dir)
            print("   ✅ Extraction successful (Python zipfile)")
    except Exception as e:
        print(f"   ❌ Extraction failed: {e}")
        return False
    
    # Clean up zip file
    try:
        zip_file.unlink()
        print("   🗑️  Cleaned up zip file")
    except:
        pass
    
    print("\n" + "=" * 70)
    print("✅ Verification")
    print("=" * 70)
    
    # Verify key files exist
    required_files = [
        ('10m_cultural', 'ne_10m_admin_0_countries.shp', 'Country Boundaries'),
        ('10m_cultural', 'ne_10m_admin_1_states_provinces.shp', 'Province/State Boundaries'),
        ('10m_physical', 'ne_10m_coastline.shp', 'Coastlines'),
    ]
    
    all_exist = True
    for subdir, filename, description in required_files:
        file_path = ne_dir / subdir / filename
        if file_path.exists():
            print(f"   ✅ {description:30} - Found")
        else:
            print(f"   ❌ {description:30} - MISSING")
            all_exist = False
    
    print("\n" + "=" * 70)
    if all_exist:
        print("✅ SUCCESS! Natural Earth data is ready.")
        print("   This data supports ALL geographic regions worldwide.")
        print("=" * 70)
        return True
    else:
        print("⚠️  Some files are missing. The extraction may have failed.")
        print("   Try running with force_redownload=True")
        print("=" * 70)
        return False

if __name__ == "__main__":
    success = download_natural_earth()
    sys.exit(0 if success else 1)