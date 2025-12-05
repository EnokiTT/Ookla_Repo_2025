# src/ibtracs_extractor.py

"""
Dynamic IBTrACS data extraction
Works for any cyclone defined in config
"""

import pandas as pd
import geopandas as gpd
from pathlib import Path
import requests
from datetime import datetime, timedelta

from config.analysis_config import ANALYSIS_CONFIG
from src.path_manager import paths

class IBTracsExtractor:
    """
    Extract cyclone track from IBTrACS
    Fully dynamic based on config
    """
    
    def __init__(self, config=None):
        self.config = config or ANALYSIS_CONFIG
        self.cyclone = self.config['cyclone']
        self.cyclone_id = self.config['computed']['cyclone_id']
        
    def download_ibtracs_database(self):
        """Download IBTrACS database if not present"""
        
        ibtracs_file = paths.ibtracs_raw / 'IBTrACS.since1980.list.v04r01.csv'
        
        if ibtracs_file.exists():
            print(f"✅ IBTrACS database already exists")
            return ibtracs_file
        
        print("📥 Downloading IBTrACS database (this may take a few minutes)...")
        
        url = "https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs/v04r01/access/csv/ibtracs.since1980.list.v04r01.csv"
        
        try:
            response = requests.get(url, stream=True, timeout=300)
            response.raise_for_status()
            
            with open(ibtracs_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"✅ Downloaded IBTrACS database")
            return ibtracs_file
            
        except Exception as e:
            print(f"❌ Error downloading IBTrACS: {e}")
            print("   You can manually download from:")
            print("   https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs/")
            return None
    
    def extract_track(self):
        """
        Extract cyclone track from IBTrACS
        Returns GeoDataFrame with track points
        """
        
        print(f"\n🌀 Extracting {self.cyclone['name']} {self.cyclone['year']} from IBTrACS...")
        
        # Download database if needed
        ibtracs_file = self.download_ibtracs_database()
        if ibtracs_file is None:
            return self._create_synthetic_track()
        
        # Load IBTrACS
        try:
            df = pd.read_csv(ibtracs_file, skiprows=[1], low_memory=False)
        except Exception as e:
            print(f"❌ Error reading IBTrACS: {e}")
            return self._create_synthetic_track()
        
        # Filter for this cyclone
        # Note: Late-season cyclones may be listed in SEASON = year+1 (e.g., Nov 2024 → SEASON=2025)
        track = df[
            (df['NAME'].str.upper() == self.cyclone['name'].upper()) &
            ((df['SEASON'] == self.cyclone['year']) | (df['SEASON'] == self.cyclone['year'] + 1))
        ].copy()
        
        if len(track) == 0:
            print(f"⚠️  {self.cyclone['name']} not found in IBTrACS")
            print("   Cyclone may be too recent or not yet in database")
            print("   Creating synthetic track from config dates...")
            return self._create_synthetic_track()
        
        print(f"✅ Found {len(track)} track points")
        
        # Process track data
        track = self._process_track_data(track)
        
        # Save
        output_file = paths.get_file('ibtracs_processed', f'{self.cyclone_id}_track.csv')
        track.to_csv(output_file, index=False)
        print(f"✅ Saved track: {output_file}")
        
        self._print_track_summary(track)
        
        return track
    
    def _process_track_data(self, track):
        """Clean and process track data"""
        
        # Convert data types
        track['ISO_TIME'] = pd.to_datetime(track['ISO_TIME'], errors='coerce')
        track['LAT'] = pd.to_numeric(track['LAT'], errors='coerce')
        track['LON'] = pd.to_numeric(track['LON'], errors='coerce')
        track['WMO_WIND'] = pd.to_numeric(track['WMO_WIND'], errors='coerce')
        track['WMO_PRES'] = pd.to_numeric(track['WMO_PRES'], errors='coerce')
        
        # Add intensity categories
        track['intensity_category'] = track['WMO_WIND'].apply(self._categorize_intensity)
        
        # Add metadata
        track['cyclone_name'] = self.cyclone['name']
        track['cyclone_year'] = self.cyclone['year']
        track['analysis_id'] = self.cyclone_id
        
        # Sort by time
        track = track.sort_values('ISO_TIME').reset_index(drop=True)
        
        return track
    
    def _categorize_intensity(self, wind_kts):
        """Categorize cyclone intensity from wind speed"""
        if pd.isna(wind_kts):
            return 'Unknown'
        elif wind_kts < 34:
            return 'Tropical Depression'
        elif wind_kts < 64:
            return 'Tropical Storm'
        elif wind_kts < 83:
            return 'Category 1'
        elif wind_kts < 96:
            return 'Category 2'
        elif wind_kts < 113:
            return 'Category 3'
        elif wind_kts < 137:
            return 'Category 4'
        else:
            return 'Category 5'
    
    def _create_synthetic_track(self):
        """
        Create synthetic track when IBTrACS data unavailable
        Uses config dates and reasonable interpolation
        """
        
        print("🔧 Creating synthetic track from config...")
        
        formation = datetime.strptime(self.cyclone['formation_date'], '%Y-%m-%d')
        dissipation = datetime.strptime(self.cyclone['dissipation_date'], '%Y-%m-%d')
        peak = datetime.strptime(self.cyclone['peak_date'], '%Y-%m-%d')
        
        # Generate hourly points
        hours = int((dissipation - formation).total_seconds() / 3600)
        times = [formation + timedelta(hours=h) for h in range(0, hours, 6)]  # 6-hourly
        
        # Interpolate positions (you'll need to adjust these for your cyclone)
        # For now, create placeholder positions
        # In reality, you'd get these from satellite data or weather reports
        
        track_data = []
        for i, time in enumerate(times):
            progress = i / len(times)
            
            # Placeholder position (adjust based on actual cyclone path)
            lat = -10.0 - progress * 2  # Moving south
            lon = 100.0 + progress * 5  # Moving east
            
            # Intensity curve (peaks in middle)
            if time < peak:
                # Intensifying
                wind = 25 + (self.cyclone.get('max_wind_kts', 50) - 25) * (i / (len(times) / 2))
            else:
                # Weakening
                wind = self.cyclone.get('max_wind_kts', 50) - (self.cyclone.get('max_wind_kts', 50) - 25) * ((i - len(times)/2) / (len(times) / 2))
            
            pressure = 1010 - (wind / 2)  # Rough estimate
            
            track_data.append({
                'ISO_TIME': time,
                'LAT': lat,
                'LON': lon,
                'WMO_WIND': wind,
                'WMO_PRES': pressure,
                'NAME': self.cyclone['name'],
                'SEASON': self.cyclone['year'],
                'BASIN': self.cyclone['basin']
            })
        
        track = pd.DataFrame(track_data)
        track['intensity_category'] = track['WMO_WIND'].apply(self._categorize_intensity)
        track['cyclone_name'] = self.cyclone['name']
        track['cyclone_year'] = self.cyclone['year']
        track['analysis_id'] = self.cyclone_id
        track['data_source'] = 'synthetic'
        
        # Save
        output_file = paths.get_file('ibtracs_processed', f'{self.cyclone_id}_track_synthetic.csv')
        track.to_csv(output_file, index=False)
        print(f"✅ Saved synthetic track: {output_file}")
        print(f"   ⚠️  Note: Positions are approximate. Update with real data if available.")
        
        return track
    
    def _print_track_summary(self, track):
        """Print summary statistics"""
        print(f"\n📊 Track Summary:")
        print(f"   Duration: {track['ISO_TIME'].min()} to {track['ISO_TIME'].max()}")
        print(f"   Points: {len(track)}")
        print(f"   Peak wind: {track['WMO_WIND'].max():.0f} knots")
        
        if not track['WMO_PRES'].isna().all():
            print(f"   Min pressure: {track['WMO_PRES'].min():.0f} mb")
        
        print(f"   Intensity distribution:")
        for cat, count in track['intensity_category'].value_counts().items():
            print(f"      {cat}: {count} points")
    
    def get_track(self):
        """Get track (load if exists, extract if not)"""
        
        track_file = paths.get_file('ibtracs_processed', f'{self.cyclone_id}_track.csv')
        synthetic_file = paths.get_file('ibtracs_processed', f'{self.cyclone_id}_track_synthetic.csv')
        
        if track_file.exists():
            print(f"✅ Loading existing track: {track_file.name}")
            return pd.read_csv(track_file, parse_dates=['ISO_TIME'])
        elif synthetic_file.exists():
            print(f"✅ Loading existing synthetic track: {synthetic_file.name}")
            return pd.read_csv(synthetic_file, parse_dates=['ISO_TIME'])
        else:
            return self.extract_track()

# Convenience function
def get_cyclone_track(config=None):
    """Quick function to get cyclone track"""
    extractor = IBTracsExtractor(config)
    return extractor.get_track()