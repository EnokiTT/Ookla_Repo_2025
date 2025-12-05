"""
Prepare Ookla data for Tableau visualization
Aggregates data and exports to optimized Excel format
"""

import pandas as pd
import geopandas as gpd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime
import xlsxwriter
from src.config import OUTPUT_DIR, OOKLA_DIR, TABLEAU_CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TableauDataPreparer:
    """
    Prepare Ookla data for Tableau by aggregating and optimizing
    
    Example:
        >>> preparer = TableauDataPreparer()
        >>> preparer.prepare_from_files(['mobile_file.geoparquet', 'fixed_file.geoparquet'])
    """
    
    def __init__(self, output_dir=None):
        """
        Initialize the Tableau data preparer
        
        Parameters:
            output_dir (Path, optional): Output directory for Excel files
        """
        self.output_dir = Path(output_dir) if output_dir else OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"TableauDataPreparer initialized")
        logger.info(f"Output directory: {self.output_dir}")
    
    def prepare_from_files(self, file_paths, combine=False):
        """
        Prepare Tableau files from downloaded Ookla geoparquet files
        Each file is converted to its own Excel file to preserve data separation
        
        Parameters:
            file_paths (list): List of file paths or filenames
            combine (bool): If True, combine all files into one Excel. Default False.
        
        Returns:
            dict: Paths to generated Excel files
        
        Example:
            >>> # Process files individually (default)
            >>> files = ['sumatra_2024_Q3_mobile.geoparquet', 
            ...          'sumatra_2024_Q3_fixed.geoparquet']
            >>> preparer.prepare_from_files(files)
            
            >>> # Combine all files
            >>> preparer.prepare_from_files(files, combine=True)
        """
        print(f"\n{'='*70}")
        print(f"PREPARING OOKLA DATA FOR TABLEAU")
        print(f"{'='*70}\n")
        
        # Normalize file paths
        normalized_paths = []
        for file_path in file_paths:
            # Handle both Path objects and strings
            if isinstance(file_path, str):
                if not Path(file_path).exists():
                    # Try in OOKLA_DIR
                    file_path = OOKLA_DIR / file_path
                else:
                    file_path = Path(file_path)
            
            if not file_path.exists():
                logger.warning(f"File not found: {file_path}")
                continue
            
            normalized_paths.append(file_path)
        
        if not normalized_paths:
            raise ValueError("No valid data files found!")
        
        output_files = {}
        
        if combine:
            # Original behavior: combine all files
            print(f"📦 Mode: COMBINE - All files merged into one Excel")
            output_files = self._prepare_combined(normalized_paths)
        else:
            # New default: process each file separately
            print(f"📦 Mode: INDIVIDUAL - Each file gets its own Excel")
            print(f"   Processing {len(normalized_paths)} file(s)...\n")
            
            for file_path in normalized_paths:
                print(f"\n{'─'*70}")
                print(f"Processing: {file_path.name}")
                print(f"{'─'*70}")
                
                file_outputs = self._prepare_single_file(file_path)
                output_files.update(file_outputs)
        
        print(f"\n{'='*70}")
        print(f"✅ TABLEAU FILES READY!")
        print(f"{'='*70}")
        print(f"Created {len(output_files)} Excel file(s) in: {self.output_dir}")
        print(f"\n📁 Output files:")
        for file_type, file_path in output_files.items():
            size_mb = file_path.stat().st_size / (1024 * 1024)
            print(f"   • {file_path.name} ({size_mb:.1f} MB)")
        print(f"{'='*70}\n")
        
        return output_files
    
    def _prepare_single_file(self, file_path):
        """Prepare a single file for Tableau"""
        logger.info(f"Loading: {file_path.name}")
        df = pd.read_parquet(file_path)
        
        print(f"   Records: {len(df):,}")
        
        # Aggregate data
        aggregated = self._aggregate_data(df)
        
        # Generate output name from filename
        output_name = file_path.stem  # Remove .geoparquet extension
        
        # Export to Excel
        output_path = self._create_excel_file(
            aggregated,
            self.output_dir / f"{output_name}.xlsx",
            "Data"
        )
        
        print(f"   ✅ Created: {output_path.name}")
        
        return {file_path.stem: output_path}
    
    def _prepare_combined(self, file_paths):
        """Original behavior: combine all files into one"""
        all_data = []
        for file_path in file_paths:
            logger.info(f"Loading: {file_path.name}")
            df = pd.read_parquet(file_path)
            all_data.append(df)
        
        # Combine all data
        combined = pd.concat(all_data, ignore_index=True)
        logger.info(f"✅ Combined {len(combined):,} total records")
        
        # Prepare data
        aggregated = self._aggregate_data(combined)
        
        # Generate output name
        timestamp = datetime.now().strftime('%Y%m%d')
        if 'region' in combined.columns:
            region = combined['region'].iloc[0].lower().replace(' ', '_')
            output_name = f"{region}_tableau_{timestamp}"
        else:
            output_name = f"ookla_tableau_{timestamp}"
        
        # Export to Excel
        output_files = self._export_to_excel(aggregated, output_name)
        
        # Generate summary statistics
        self._print_summary(combined, aggregated)
        
        return output_files
    
    def _decode_quadkey_to_latlon(self, quadkey):
        """
        Decode Bing Maps quadkey to latitude/longitude (center of tile)
        
        Uses the official Bing Maps Tile System algorithm:
        https://docs.microsoft.com/en-us/bingmaps/articles/bing-maps-tile-system
        
        Parameters:
            quadkey (str): Quadkey string (e.g., "3101020323112312")
            
        Returns:
            tuple: (latitude, longitude)
        """
        tile_x = tile_y = 0
        level_of_detail = len(str(quadkey))
        
        # Decode quadkey to tile X,Y coordinates
        for i in range(level_of_detail):
            mask = 1 << (level_of_detail - 1 - i)
            digit = int(str(quadkey)[i])
            
            if digit == 1:
                tile_x |= mask
            elif digit == 2:
                tile_y |= mask
            elif digit == 3:
                tile_x |= mask
                tile_y |= mask
        
        # Convert tile coordinates to pixel coordinates (center of tile)
        map_size = 256 << level_of_detail
        pixel_x = (tile_x * 256) + 128
        pixel_y = (tile_y * 256) + 128
        
        # Convert pixel coordinates to lat/lon
        x = (pixel_x / map_size) - 0.5
        y = 0.5 - (pixel_y / map_size)
        
        longitude = 360 * x
        latitude = 90 - 360 * np.arctan(np.exp(-y * 2 * np.pi)) / np.pi
        
        return latitude, longitude
    
    def _aggregate_data(self, df):
        """
        Aggregate data by bin (quadkey) and time period
        
        Parameters:
            df (DataFrame): Raw Ookla data
        
        Returns:
            DataFrame: Aggregated data
        """
        print(f"\n📦 Aggregating data to bins...")
        
        # Decode quadkeys to lat/lon if not already present
        if 'latitude' not in df.columns or 'longitude' not in df.columns:
            print(f"   🗺️  Decoding quadkeys to lat/lon coordinates...")
            import numpy as np
            latlon_data = df['quadkey'].apply(self._decode_quadkey_to_latlon)
            df['latitude'] = [x[0] for x in latlon_data]
            df['longitude'] = [x[1] for x in latlon_data]
            print(f"   ✅ Added lat/lon columns for Tableau mapping")
        
        # Define aggregation rules
        agg_dict = {
            'avg_d_kbps': ['mean', 'min', 'max', 'std'],
            'avg_u_kbps': ['mean', 'min', 'max', 'std'],
            'avg_lat_ms': ['mean', 'min', 'max'],
            'tests': 'sum',
            'devices': 'sum',
        }
        
        # Add optional columns if they exist
        if 'avg_d_mbps' in df.columns:
            agg_dict['avg_d_mbps'] = ['mean', 'min', 'max']
        if 'avg_u_mbps' in df.columns:
            agg_dict['avg_u_mbps'] = ['mean', 'min', 'max']
        
        # Group by bin and time period
        group_cols = ['quadkey', 'year', 'quarter', 'data_type']
        
        # Add optional grouping columns
        for col in ['name', 'region', 'country', 'latitude', 'longitude']:
            if col in df.columns:
                group_cols.append(col)
        
        # Filter agg_dict to only include existing columns
        agg_dict = {k: v for k, v in agg_dict.items() if k in df.columns}
        
        # Perform aggregation
        aggregated = df.groupby(group_cols, dropna=False).agg(agg_dict)
        
        # Flatten column names
        aggregated.columns = ['_'.join(col).strip('_') if isinstance(col, tuple) else col 
                              for col in aggregated.columns.values]
        aggregated = aggregated.reset_index()
        
        logger.info(f"✅ Aggregated to {len(aggregated):,} bins")
        logger.info(f"   Compression: {len(df):,} → {len(aggregated):,} "
                   f"({100*len(aggregated)/len(df):.1f}%)")
        
        return aggregated
    
    def _export_to_excel(self, df, output_name):
        """
        Export data to Excel with proper formatting
        
        Parameters:
            df (DataFrame): Aggregated data
            output_name (str): Base name for output files
        
        Returns:
            dict: Paths to created files
        """
        print(f"\n💾 Exporting to Excel format...")
        
        output_files = {}
        
        # 1. Combined file (all data)
        output_files['combined'] = self._create_excel_file(
            df,
            self.output_dir / f"{output_name}_combined.xlsx",
            "All Data"
        )
        
        # 2. Mobile only
        if 'data_type' in df.columns:
            mobile_data = df[df['data_type'] == 'mobile']
            if len(mobile_data) > 0:
                output_files['mobile'] = self._create_excel_file(
                    mobile_data,
                    self.output_dir / f"{output_name}_mobile.xlsx",
                    "Mobile"
                )
        
        # 3. Fixed only
        if 'data_type' in df.columns:
            fixed_data = df[df['data_type'] == 'fixed']
            if len(fixed_data) > 0:
                output_files['fixed'] = self._create_excel_file(
                    fixed_data,
                    self.output_dir / f"{output_name}_fixed.xlsx",
                    "Fixed"
                )
        
        # 4. Time comparison (if multiple periods)
        if 'year' in df.columns and 'quarter' in df.columns:
            time_periods = df.groupby(['year', 'quarter']).size()
            if len(time_periods) > 1:
                output_files['comparison'] = self._create_comparison_file(
                    df,
                    self.output_dir / f"{output_name}_comparison.xlsx"
                )
        
        print(f"\n✅ Created {len(output_files)} Excel file(s):")
        for file_type, file_path in output_files.items():
            size_mb = file_path.stat().st_size / (1024 * 1024)
            print(f"   • {file_type:15s}: {file_path.name} ({size_mb:.1f} MB)")
        
        return output_files
    
    def _create_excel_file(self, df, output_path, sheet_name="Data"):
        """Create a single Excel file with proper formatting"""
        
        # Handle large files - split into multiple sheets
        max_rows = TABLEAU_CONFIG['excel_row_limit']
        
        with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
            workbook = writer.book
            
            # Define formats
            header_format = workbook.add_format({
                'bg_color': '#4472C4',
                'font_color': 'white',
                'bold': True,
                'border': 1,
                'align': 'center',
                'valign': 'vcenter'
            })
            
            number_format = workbook.add_format({'num_format': '#,##0.00'})
            
            # Split into chunks if needed
            num_chunks = (len(df) - 1) // max_rows + 1
            
            for chunk_idx in range(num_chunks):
                start_row = chunk_idx * max_rows
                end_row = min((chunk_idx + 1) * max_rows, len(df))
                chunk_data = df.iloc[start_row:end_row]
                
                chunk_sheet_name = f"{sheet_name}_{chunk_idx+1}" if num_chunks > 1 else sheet_name
                
                # Write data
                chunk_data.to_excel(writer, sheet_name=chunk_sheet_name, index=False)
                
                worksheet = writer.sheets[chunk_sheet_name]
                
                # Format header
                for col_num, value in enumerate(chunk_data.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                
                # Auto-fit columns
                for i, col in enumerate(chunk_data.columns):
                    max_length = min(
                        max(chunk_data[col].astype(str).str.len().max(), len(col)) + 2,
                        50
                    )
                    worksheet.set_column(i, i, max_length)
                
                # Freeze header row
                worksheet.freeze_panes(1, 0)
                
                logger.info(f"   Sheet '{chunk_sheet_name}': {len(chunk_data):,} rows")
        
        return output_path
    
    def _create_comparison_file(self, df, output_path):
        """Create comparison file with baseline calculations"""
        
        print(f"\n⏰ Creating time period comparison...")
        
        # Find earliest period as baseline
        df_sorted = df.sort_values(['year', 'quarter'])
        baseline_year = df_sorted['year'].iloc[0]
        baseline_quarter = df_sorted['quarter'].iloc[0]
        
        # Calculate baseline averages
        baseline = df[
            (df['year'] == baseline_year) & (df['quarter'] == baseline_quarter)
        ].copy()
        
        if len(baseline) == 0:
            logger.warning("No baseline period found")
            return None
        
        # Calculate baseline metrics per quadkey
        baseline_metrics = baseline.groupby('quadkey').agg({
            'avg_d_kbps_mean': 'mean',
            'avg_u_kbps_mean': 'mean',
        }).rename(columns={
            'avg_d_kbps_mean': 'baseline_d_kbps',
            'avg_u_kbps_mean': 'baseline_u_kbps'
        }).reset_index()
        
        # Merge with all data
        comparison = df.merge(baseline_metrics, on='quadkey', how='left')
        
        # Calculate percent changes from baseline (Q1)
        comparison['d_kbps_pct_change'] = (
            (comparison['avg_d_kbps_mean'] - comparison['baseline_d_kbps']) 
            / comparison['baseline_d_kbps'] * 100
        )
        comparison['u_kbps_pct_change'] = (
            (comparison['avg_u_kbps_mean'] - comparison['baseline_u_kbps']) 
            / comparison['baseline_u_kbps'] * 100
        )
        
        # Calculate consecutive quarter changes (Q1→Q2→Q3→Q4→next year Q1)
        # Sort by quadkey, then year, then quarter to ensure proper chronological order
        comparison = comparison.sort_values(['quadkey', 'year', 'quarter'])
        
        # Create a time_period column for easier sequential tracking (e.g., 2019.1, 2019.2, 2020.1)
        comparison['time_period'] = comparison['year'] + (comparison['quarter'] - 1) * 0.25
        
        # Get previous quarter's values for each quadkey (works across years)
        comparison['prev_d_kbps'] = comparison.groupby('quadkey')['avg_d_kbps_mean'].shift(1)
        comparison['prev_u_kbps'] = comparison.groupby('quadkey')['avg_u_kbps_mean'].shift(1)
        comparison['prev_year'] = comparison.groupby('quadkey')['year'].shift(1)
        comparison['prev_quarter'] = comparison.groupby('quadkey')['quarter'].shift(1)
        
        # Calculate quarter-over-quarter percent change
        comparison['d_kbps_qoq_change'] = (
            (comparison['avg_d_kbps_mean'] - comparison['prev_d_kbps']) 
            / comparison['prev_d_kbps'] * 100
        )
        comparison['u_kbps_qoq_change'] = (
            (comparison['avg_u_kbps_mean'] - comparison['prev_u_kbps']) 
            / comparison['prev_u_kbps'] * 100
        )
        
        # Add a flag to identify year transitions (2019 Q4 → 2020 Q1)
        comparison['is_year_transition'] = (
            (comparison['quarter'] == 1) & 
            (comparison['prev_quarter'] == 4) & 
            (comparison['year'] != comparison['prev_year'])
        )
        
        # Clean up temporary columns
        comparison = comparison.drop(columns=['prev_d_kbps', 'prev_u_kbps', 'prev_year', 'prev_quarter'])
        
        # Add cumulative change from baseline
        comparison['d_kbps_cumulative_change'] = comparison['d_kbps_pct_change']
        comparison['u_kbps_cumulative_change'] = comparison['u_kbps_pct_change']
        
        # Save to Excel
        self._create_excel_file(comparison, output_path, "Comparison")
        
        logger.info(f"✅ Created comparison file with baseline: {baseline_year} Q{baseline_quarter}")
        
        return output_path
    
    def _print_summary(self, raw_df, agg_df):
        """Print summary statistics"""
        
        print(f"\n{'='*70}")
        print(f"SUMMARY STATISTICS")
        print(f"{'='*70}")
        
        print(f"\n📊 Data Overview:")
        print(f"   Raw records:        {len(raw_df):,}")
        print(f"   Aggregated bins:    {len(agg_df):,}")
        print(f"   Compression ratio:  {100*len(agg_df)/len(raw_df):.1f}%")
        
        if 'region' in raw_df.columns:
            print(f"   Region:             {raw_df['region'].iloc[0]}")
        
        if 'year' in raw_df.columns and 'quarter' in raw_df.columns:
            periods = raw_df.groupby(['year', 'quarter']).size().to_dict()
            print(f"\n📅 Time Periods:")
            for (year, quarter), count in sorted(periods.items()):
                print(f"   • {year} Q{quarter}: {count:,} records")
        
        if 'data_type' in raw_df.columns:
            types = raw_df.groupby('data_type').size().to_dict()
            print(f"\n📱 Data Types:")
            for dtype, count in types.items():
                print(f"   • {dtype}: {count:,} records")
        
        if 'avg_d_mbps' in raw_df.columns:
            print(f"\n⚡ Average Speeds:")
            print(f"   Download: {raw_df['avg_d_mbps'].mean():.2f} Mbps")
            print(f"   Upload:   {raw_df['avg_u_mbps'].mean():.2f} Mbps")
        
        if 'tests' in raw_df.columns:
            print(f"\n🧪 Total Tests: {raw_df['tests'].sum():,}")
        
        print(f"\n{'='*70}")
        print(f"✅ DATA READY FOR TABLEAU!")
        print(f"{'='*70}")
        print(f"\n📁 Output location: {self.output_dir}")
        print(f"\n🎨 Next steps:")
        print(f"   1. Open Excel file in Tableau")
        print(f"   2. Create map visualization using latitude/longitude")
        print(f"   3. Color by connectivity metrics")
        print(f"   4. Filter by time period")
        print(f"\n")


def prepare_tableau_data(file_paths, output_name=None):
    """
    Convenience function to prepare Tableau data
    
    Parameters:
        file_paths (list): List of Ookla geoparquet files
        output_name (str, optional): Base name for output files
    
    Returns:
        dict: Paths to generated Excel files
    
    Example:
        >>> files = ['sumatra_2024_Q3_mobile.geoparquet']
        >>> prepare_tableau_data(files, 'sumatra_analysis')
    """
    preparer = TableauDataPreparer()
    return preparer.prepare_from_files(file_paths, output_name)


if __name__ == '__main__':
    # Example usage
    print("Tableau Data Preparer - Example Usage")
    print("="*70)
    
    # Find all downloaded Ookla files
    ookla_files = list(OOKLA_DIR.glob('*.geoparquet'))
    
    if not ookla_files:
        print("❌ No Ookla data files found!")
        print(f"   Location: {OOKLA_DIR}")
        print(f"\nRun download_ookla.py first to download data.")
    else:
        print(f"Found {len(ookla_files)} Ookla file(s)")
        
        # Prepare Tableau data
        preparer = TableauDataPreparer()
        output_files = preparer.prepare_from_files(ookla_files)
        
        print(f"\n✅ Created {len(output_files)} Tableau file(s)")
