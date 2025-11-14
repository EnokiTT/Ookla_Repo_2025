"""
Ookla Data Downloader
Downloads and filters Ookla connectivity data for any specified region
"""

import pandas as pd
import geopandas as gpd
from pathlib import Path
from datetime import datetime
from src.config import OOKLA_CONFIG, OOKLA_DIR
from src.data_loader import NaturalEarthLoader


class OoklaDownloader:
    """
    Download Ookla connectivity data for specified regions and time periods
    
    Example:
        >>> downloader = OoklaDownloader()
        >>> downloader.set_region('indonesia_sumatra')
        >>> data = downloader.download(year=2024, quarter=4, data_type='mobile')
    """
    
    def __init__(self):
        """Initialize the Ookla downloader"""
        self.region_info = None
        self.boundaries = None
        self.geo_loader = NaturalEarthLoader()
        
    def set_region(self, region_key=None, country=None, provinces=None):
        """
        Set the region for data download
        
        Parameters:
            region_key (str, optional): Key from config.REGION_PRESETS
            country (str, optional): Country name (if custom region)
            provinces (list, optional): List of province names (if custom region)
        
        Example:
            >>> downloader.set_region('indonesia_sumatra')
            >>> # OR custom region:
            >>> downloader.set_region(country='Indonesia', provinces=['Aceh', 'Bali'])
        """
        if region_key:
            # Load from preset
            from src.config import get_region_info
            self.region_info = get_region_info(region_key)
        elif country and provinces:
            # Custom region
            self.region_info = {
                'name': f"{country} Custom Region",
                'country': country,
                'provinces': provinces
            }
        else:
            raise ValueError(
                "Must provide either region_key OR (country + provinces)"
            )
        
        # Load geographic boundaries
        print(f"\n🌍 Loading geographic boundaries...")
        self.geo_loader.set_country(self.region_info['country'])
        self.boundaries = self.geo_loader.get_provinces_by_name(
            self.region_info['provinces']
        )
        
        print(f"✅ Region configured: {self.region_info['name']}")
        print(f"   Country: {self.region_info['country']}")
        print(f"   Provinces: {len(self.region_info['provinces'])}")
        
        return self
    
    def download(self, year, quarter, data_type='mobile', columns=None):
        """
        Download Ookla data for specified parameters
        
        Parameters:
            year (int): Year (e.g., 2024)
            quarter (int): Quarter (1, 2, 3, or 4)
            data_type (str): 'mobile' or 'fixed'
            columns (list, optional): Columns to extract. If None, uses defaults.
        
        Returns:
            GeoDataFrame: Filtered Ookla data
        
        Example:
            >>> data = downloader.download(2024, 4, 'mobile')
        """
        if self.region_info is None:
            raise ValueError("❌ Region not set! Call set_region() first.")
        
        # Validate inputs
        from src.config import validate_year_quarter
        validate_year_quarter(year, quarter)
        
        if data_type not in OOKLA_CONFIG['data_types']:
            raise ValueError(
                f"data_type must be one of {OOKLA_CONFIG['data_types']}"
            )
        
        if columns is None:
            columns = OOKLA_CONFIG['default_columns']
        
        print(f"\n{'='*70}")
        print(f"DOWNLOADING OOKLA DATA")
        print(f"{'='*70}")
        print(f"Region:   {self.region_info['name']}")
        print(f"Period:   {year} Q{quarter}")
        print(f"Type:     {data_type}")
        print(f"{'='*70}\n")
        
        # Construct S3 URI
        s3_uri = (
            f"{OOKLA_CONFIG['base_url']}/"
            f"type={data_type}/year={year}/quarter={quarter}/"
        )
        
        print(f"📥 Downloading from S3...")
        print(f"   {s3_uri}")
        
        try:
            # Read from S3
            storage_options = {"anon": True}
            df = pd.read_parquet(s3_uri, storage_options=storage_options)
            print(f"   ✅ Downloaded {len(df):,} global tiles")
            
            # Convert to GeoDataFrame
            print(f"\n🗺️  Converting to geographic data...")
            gdf = gpd.GeoDataFrame(
                df,
                geometry=gpd.GeoSeries.from_wkt(df['tile']),
                crs="EPSG:4326"
            )
            
            # Filter to region using bounding box first (fast)
            print(f"\n🎯 Filtering to region boundaries...")
            bounds = self.boundaries.total_bounds
            min_x, min_y, max_x, max_y = bounds
            
            gdf_bbox = gdf.cx[min_x:max_x, min_y:max_y]
            print(f"   Bounding box filter: {len(gdf_bbox):,} tiles")
            
            if len(gdf_bbox) == 0:
                print(f"   ⚠️  No data found in region bounding box")
                return None
            
            # Precise spatial join (slower but accurate)
            print(f"   Performing precise spatial join...")
            gdf_filtered = gpd.sjoin(
                gdf_bbox,
                self.boundaries[['geometry', 'name']],
                how='inner',
                predicate='intersects'
            )
            
            print(f"   ✅ Filtered to {len(gdf_filtered):,} tiles in region")
            
            if len(gdf_filtered) == 0:
                print(f"   ⚠️  No data found in specified provinces")
                return None
            
            # Select requested columns + metadata
            available_cols = [c for c in columns if c in gdf_filtered.columns]
            metadata_cols = ['name']  # Province name from spatial join
            
            final_cols = list(set(available_cols + metadata_cols))
            gdf_result = gdf_filtered[final_cols].copy()
            
            # Add metadata
            gdf_result['year'] = year
            gdf_result['quarter'] = quarter
            gdf_result['data_type'] = data_type
            gdf_result['region'] = self.region_info['name']
            gdf_result['country'] = self.region_info['country']
            
            # Convert speeds to Mbps for easier interpretation
            if 'avg_d_kbps' in gdf_result.columns:
                gdf_result['avg_d_mbps'] = gdf_result['avg_d_kbps'] / 1000
            if 'avg_u_kbps' in gdf_result.columns:
                gdf_result['avg_u_mbps'] = gdf_result['avg_u_kbps'] / 1000
            
            # Save to file
            output_file = self._get_output_filename(year, quarter, data_type)
            gdf_result.to_parquet(output_file, index=False)
            
            print(f"\n💾 Saved to: {output_file.name}")
            print(f"\n📊 Summary Statistics:")
            print(f"   Total tiles: {len(gdf_result):,}")
            print(f"   Provinces covered: {gdf_result['name'].nunique()}")
            if 'avg_d_mbps' in gdf_result.columns:
                print(f"   Avg download speed: {gdf_result['avg_d_mbps'].mean():.2f} Mbps")
            if 'avg_u_mbps' in gdf_result.columns:
                print(f"   Avg upload speed: {gdf_result['avg_u_mbps'].mean():.2f} Mbps")
            if 'tests' in gdf_result.columns:
                print(f"   Total tests: {gdf_result['tests'].sum():,}")
            
            print(f"\n✅ Download complete!")
            
            return gdf_result
            
        except Exception as e:
            print(f"\n❌ Error downloading data: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def download_multiple(self, year, quarters, data_types=None):
        """
        Download multiple quarters and/or data types
        
        Parameters:
            year (int): Year
            quarters (list): List of quarters [1, 2, 3, 4]
            data_types (list, optional): ['mobile', 'fixed'] or subset
        
        Returns:
            dict: {period_key: GeoDataFrame}
        
        Example:
            >>> data = downloader.download_multiple(2024, [3, 4], ['mobile', 'fixed'])
        """
        if data_types is None:
            data_types = ['mobile', 'fixed']
        
        results = {}
        
        for quarter in quarters:
            for data_type in data_types:
                key = f"{year}_Q{quarter}_{data_type}"
                print(f"\n{'='*70}")
                print(f"Downloading: {key}")
                print(f"{'='*70}")
                
                data = self.download(year, quarter, data_type)
                if data is not None:
                    results[key] = data
        
        print(f"\n{'='*70}")
        print(f"✅ Downloaded {len(results)} datasets")
        print(f"{'='*70}")
        
        return results
    
    def _get_output_filename(self, year, quarter, data_type):
        """Generate output filename"""
        region_slug = self.region_info['name'].lower().replace(' ', '_')
        timestamp = datetime.now().strftime('%Y%m%d')
        filename = f"{region_slug}_{year}_Q{quarter}_{data_type}_{timestamp}.geoparquet"
        return OOKLA_DIR / filename
    
    def list_downloaded_files(self):
        """List all downloaded Ookla files"""
        files = sorted(OOKLA_DIR.glob('*.geoparquet'))
        
        if not files:
            print("No downloaded files found in:")
            print(f"  {OOKLA_DIR}")
            return []
        
        print(f"\nDownloaded Ookla Files ({len(files)}):")
        print("="*70)
        
        for f in files:
            size_mb = f.stat().st_size / (1024 * 1024)
            print(f"  • {f.name:50s} ({size_mb:>6.1f} MB)")
        
        print("="*70)
        return files


def quick_download(region_key, year, quarter, data_type='mobile'):
    """
    Convenience function for quick downloads
    
    Example:
        >>> data = quick_download('indonesia_sumatra', 2024, 4, 'mobile')
    """
    downloader = OoklaDownloader()
    downloader.set_region(region_key)
    return downloader.download(year, quarter, data_type)


if __name__ == '__main__':
    # Example usage
    print("Ookla Downloader - Example Usage")
    print("="*70)
    
    # Initialize downloader
    downloader = OoklaDownloader()
    
    # Set region
    downloader.set_region('indonesia_sumatra')
    
    # Download data
    data = downloader.download(
        year=2024,
        quarter=4,
        data_type='mobile'
    )
    
    if data is not None:
        print(f"\n✅ Successfully downloaded {len(data):,} records")
    
    # List downloaded files
    downloader.list_downloaded_files()
