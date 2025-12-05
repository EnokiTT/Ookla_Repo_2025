"""
Data loading utilities for Natural Earth and Ookla datasets

This module provides classes to load and process geographic and connectivity data
for the Capstone Ookla connectivity analysis project.
"""

import geopandas as gpd
import pandas as pd
from pathlib import Path


class NaturalEarthLoader:
    """
    Load and filter Natural Earth geographic data
    
    This class provides methods to load country boundaries and administrative
    divisions (provinces/states) from Natural Earth datasets.
    
    Attributes:
        data_dir (Path): Directory containing Natural Earth data
        current_country (str): Currently selected country name
        current_country_geometry (GeoDataFrame): Currently selected country boundary
        current_provinces (GeoDataFrame): Currently loaded provinces
        
    Example:
        >>> loader = NaturalEarthLoader()
        >>> loader.set_country('Indonesia')
        >>> provinces = loader.get_provinces()
        >>> sumatra = loader.get_provinces_by_name(['Aceh', 'Sumatera Utara'])
    """
    
    def __init__(self, data_dir=None):
        """
        Initialize the Natural Earth data loader
        
        Parameters:
            data_dir (str or Path, optional): Path to Natural Earth data directory.
                If None, automatically detects based on project structure.
        """
        if data_dir is None:
            # Auto-detect project root
            if '__file__' in globals():
                # Running as a module
                current_file = Path(__file__).resolve()
                project_root = current_file.parent.parent
            else:
                # Running in notebook - go up from current directory
                project_root = Path.cwd().resolve().parent
            
            self.data_dir = project_root / 'data' / 'raw' / 'natural_earth'
        else:
            self.data_dir = Path(data_dir)
        
        # Ensure absolute path
        self.data_dir = self.data_dir.resolve()
        
        print(f"📁 NaturalEarthLoader initialized")
        print(f"   Data directory: {self.data_dir}")
        print(f"   Directory exists: {self.data_dir.exists()}")
        
        # Validate directory exists
        if not self.data_dir.exists():
            raise FileNotFoundError(
                f"❌ Natural Earth data directory not found!\n"
                f"   Looking at: {self.data_dir}\n\n"
                f"   Please either:\n"
                f"   1. Download data to this location, OR\n"
                f"   2. Provide correct path: NaturalEarthLoader(data_dir='your/path')\n\n"
                f"   To download: python scripts/download_natural_earth.py"
            )
        
        # Private attributes for lazy loading
        self._countries = None
        self._provinces = None
        
        # Current country context
        self.current_country = None
        self.current_country_geometry = None
        self.current_provinces = None
    
    @property
    def countries(self):
        """
        Lazy load country boundaries
        
        Returns:
            GeoDataFrame: All country boundaries from Natural Earth
        """
        if self._countries is None:
            self._countries = self._load_countries()
        return self._countries
    
    @property
    def provinces(self):
        """
        Lazy load province/state boundaries
        
        Returns:
            GeoDataFrame: All province boundaries from Natural Earth
        """
        if self._provinces is None:
            self._provinces = self._load_provinces()
        return self._provinces
    
    def _load_countries(self):
        """
        Internal method to load country boundaries from shapefile
        
        Returns:
            GeoDataFrame: Country boundaries
            
        Raises:
            FileNotFoundError: If shapefile not found
        """
        path = (self.data_dir / '10m_cultural' / 'ne_10m_admin_0_countries.shp').resolve()
        
        if not path.exists():
            # Try to help user find the file
            print(f"❌ Not found: {path}")
            cultural_dir = self.data_dir / '10m_cultural'
            if cultural_dir.exists():
                print(f"\n📁 Available shapefiles:")
                for f in sorted(cultural_dir.glob('*countries*.shp')):
                    print(f"   - {f.name}")
            raise FileNotFoundError(
                f"Countries shapefile not found at: {path}\n"
                f"Expected structure: {self.data_dir}/10m_cultural/ne_10m_admin_0_countries.shp"
            )
        
        print(f"✅ Loading countries from: {path.name}")
        return gpd.read_file(str(path))
    
    def _load_provinces(self):
        """
        Internal method to load province/state boundaries from shapefile
        
        Returns:
            GeoDataFrame: Province boundaries
            
        Raises:
            FileNotFoundError: If shapefile not found
        """
        path = (self.data_dir / '10m_cultural' / 'ne_10m_admin_1_states_provinces.shp').resolve()
        
        if not path.exists():
            raise FileNotFoundError(
                f"Provinces shapefile not found at: {path}\n"
                f"Expected structure: {self.data_dir}/10m_cultural/ne_10m_admin_1_states_provinces.shp"
            )
        
        print(f"✅ Loading provinces from: {path.name}")
        return gpd.read_file(str(path))
    
    def set_country(self, country_name):
        """
        Set the current country context
        
        This loads the country boundary and its provinces, setting the context
        for subsequent operations.
        
        Parameters:
            country_name (str): Name of country (e.g., 'Indonesia')
        
        Returns:
            self: Returns self for method chaining
            
        Example:
            >>> loader = NaturalEarthLoader()
            >>> loader.set_country('Indonesia')
            >>> provinces = loader.get_provinces()
        """
        print(f"\n🌍 Setting country context: {country_name}")
        print("=" * 60)
        
        # Load country boundary
        self.current_country_geometry = self.countries[
            self.countries['NAME'] == country_name
        ].copy()
        
        if len(self.current_country_geometry) == 0:
            available = sorted(self.countries['NAME'].unique()[:20])
            raise ValueError(
                f"❌ Country '{country_name}' not found.\n"
                f"   Sample available countries: {available}"
            )
        
        self.current_country = country_name
        print(f"✅ Country loaded: {country_name}")
        
        # Load provinces for this country
        self.current_provinces = self.provinces[
            self.provinces['admin'] == country_name
        ].copy()
        
        
        print(f"✅ Loaded {len(self.current_provinces)} provinces")
        print("=" * 60)
        
        return self
    
    def get_country(self, country_name=None):
        """
        Get boundary for a specific country
        
        Parameters:
            country_name (str, optional): Name of country. If None, returns current country.
        
        Returns:
            GeoDataFrame: Country boundary
            
        Example:
            >>> loader = NaturalEarthLoader()
            >>> loader.set_country('Indonesia')
            >>> indonesia = loader.get_country()  # Returns Indonesia
            >>> brazil = loader.get_country('Brazil')  # Loads Brazil without changing context
        """
        if country_name is None:
            # Return current country
            if self.current_country_geometry is None:
                raise ValueError(
                    "❌ No country context set!\n"
                    "   Use: loader.set_country('CountryName')"
                )
            return self.current_country_geometry
        
        # Load specific country without changing context
        result = self.countries[self.countries['NAME'] == country_name].copy()
        
        if len(result) == 0:
            available = sorted(self.countries['NAME'].unique()[:20])
            raise ValueError(
                f"❌ Country '{country_name}' not found.\n"
                f"   Sample available countries: {available}"
            )
        
        print(f"✅ Found country: {country_name}")
        return result
    
    def get_provinces(self, country_name=None):
        """
        Get provinces for current or specified country
        
        Parameters:
            country_name (str, optional): Country name. If None, uses current country.
        
        Returns:
            GeoDataFrame: Province boundaries
            
        Example:
            >>> loader = NaturalEarthLoader()
            >>> loader.set_country('Indonesia')
            >>> provinces = loader.get_provinces()  # Returns Indonesia provinces
        """
        if country_name is None:
            # Return current provinces
            if self.current_provinces is None:
                raise ValueError(
                    "❌ No country context set!\n"
                    "   Use: loader.set_country('CountryName')"
                )
            return self.current_provinces
        
        # Load provinces for specific country
        result = self.provinces[self.provinces['admin'] == country_name].copy()
        
        if len(result) == 0:
            raise ValueError(
                f"❌ No provinces found for country: {country_name}\n"
                f"   Check spelling or try get_country() first"
            )
        
        print(f"✅ Found {len(result)} provinces for {country_name}")
        return result

    def get_provinces_by_name(self, province_names):
        """
        Get specific provinces by name from current country
        
        Works with the current country context set by set_country().
        
        Parameters:
            province_names (list of str or str): Province name(s) to select
        
        Returns:
            GeoDataFrame: Selected province boundaries
            
        Example:
            >>> loader = NaturalEarthLoader()
            >>> loader.set_country('Indonesia')
            >>> sumatra_provinces = loader.get_provinces_by_name([
            ...     'Aceh', 'Sumatera Utara', 'Sumatera Barat'
            ... ])
            >>> # Or single province
            >>> aceh = loader.get_provinces_by_name('Aceh')
        """
        if self.current_provinces is None:
            raise ValueError(
                "❌ No country context set!\n"
                "   Use: loader.set_country('CountryName') first"
            )
        
        # Handle single province name
        if isinstance(province_names, str):
            province_names = [province_names]
        
        # Filter from current provinces
        selected = self.current_provinces[
            self.current_provinces['name'].isin(province_names)
        ].copy()
        
        found_count = len(selected)
        expected_count = len(province_names)
        
        print(f"✅ Found {found_count}/{expected_count} province(s) in {self.current_country}")
        
        if found_count < expected_count:
            missing = set(province_names) - set(selected['name'].values)
            all_provinces = sorted(self.current_provinces['name'].unique())
            print(f"⚠️  Missing provinces: {missing}")
            print(f"   Available provinces in {self.current_country} (Total: {len(all_provinces)}):")
            
            # Display all provinces in 3 columns
            cols = 3
            rows = (len(all_provinces) + cols - 1) // cols
            for i in range(rows):
                line = ""
                for j in range(cols):
                    idx = i + j * rows
                    if idx < len(all_provinces):
                        line += f"     {all_provinces[idx]:<30}"
                print(line.rstrip())
        
        return selected

    def get_states_by_name(self, state_names):
        """
        Alias for get_provinces_by_name (for US-style terminology)
        
        Parameters:
            state_names (list of str or str): State name(s) to select
        
        Returns:
            GeoDataFrame: Selected state boundaries
            
        Example:
            >>> loader = NaturalEarthLoader()
            >>> loader.set_country('United States of America')
            >>> states = loader.get_states_by_name(['California', 'Texas'])
        """
        return self.get_provinces_by_name(state_names)

    def list_provinces(self, search_term=None):
        """
        List all provinces in current country with optional search
        
        Parameters:
            search_term (str, optional): Search term to filter provinces
        
        Returns:
            list: Province names
            
        Example:
            >>> loader = NaturalEarthLoader()
            >>> loader.set_country('Indonesia')
            >>> loader.list_provinces()
            >>> loader.list_provinces('Sumatra')  # Search for Sumatra provinces
        """
        if self.current_provinces is None:
            raise ValueError(
                "❌ No country context set!\n"
                "   Use: loader.set_country('CountryName') first"
            )
        
        names = sorted(self.current_provinces['name'].unique())
        
        if search_term:
            names = [n for n in names if search_term.lower() in n.lower()]
            print(f"🔍 Found {len(names)} provinces matching '{search_term}' in {self.current_country}:")
        else:
            print(f"📋 {len(names)} provinces in {self.current_country}:")
        
        for idx, name in enumerate(names, 1):
            print(f"  {idx:2d}. {name}")
        
        return names

    def get_region_preset(self, preset_name):
        """
        Get provinces using predefined regional groupings
        
        Parameters:
            preset_name (str): Name of preset region
                For Indonesia: 'sumatra', 'java', 'kalimantan', 'sulawesi', 'eastern'
        
        Returns:
            GeoDataFrame: Provinces in the preset region
            
        Example:
            >>> loader = NaturalEarthLoader()
            >>> loader.set_country('Indonesia')
            >>> sumatra = loader.get_region_preset('sumatra')
        """
        if self.current_country is None:
            raise ValueError(
                "❌ No country context set!\n"
                "   Use: loader.set_country('CountryName') first"
            )
        
        # Define presets by country
        presets = {
            'Indonesia': {
                'sumatra': [
                    'Aceh', 'Sumatera Utara', 'Sumatera Barat', 'Riau',
                    'Jambi', 'Sumatera Selatan', 'Bengkulu', 'Lampung',
                    'Kepulauan Bangka Belitung', 'Kepulauan Riau'
                ],
                'java': [
                    'Banten', 'DKI Jakarta', 'Jawa Barat', 'Jawa Tengah',
                    'DI Yogyakarta', 'Jawa Timur'
                ],
                'kalimantan': [
                    'Kalimantan Barat', 'Kalimantan Tengah', 'Kalimantan Selatan',
                    'Kalimantan Timur', 'Kalimantan Utara'
                ],
                'sulawesi': [
                    'Sulawesi Utara', 'Sulawesi Tengah', 'Sulawesi Selatan',
                    'Sulawesi Tenggara', 'Gorontalo', 'Sulawesi Barat'
                ],
                'eastern': [
                    'Bali', 'Nusa Tenggara Barat', 'Nusa Tenggara Timur',
                    'Maluku', 'Maluku Utara', 'Papua', 'Papua Barat'
                ]
            }
        }
        
        # Get presets for current country
        if self.current_country not in presets:
            raise ValueError(
                f"❌ No presets defined for {self.current_country}\n"
                f"   Available countries: {list(presets.keys())}"
            )
        
        country_presets = presets[self.current_country]
        
        if preset_name not in country_presets:
            raise ValueError(
                f"❌ Preset '{preset_name}' not found for {self.current_country}\n"
                f"   Available presets: {list(country_presets.keys())}"
            )
        
        province_list = country_presets[preset_name]
        print(f"📍 Loading preset region: {preset_name} ({len(province_list)} provinces)")
        
        return self.get_provinces_by_name(province_list)


class OoklaLoader:
    """
    Load and process Ookla speed test data
    
    This class provides methods to load Ookla's open datasets for fixed
    and mobile network performance.
    
    Attributes:
        data_dir (Path): Directory containing Ookla data
        
    Example:
        >>> loader = OoklaLoader()
        >>> data = loader.load_processed_data()
    """
    
    def __init__(self, data_dir=None):
        """
        Initialize the Ookla data loader
        
        Parameters:
            data_dir (str or Path, optional): Path to Ookla data directory.
                If None, automatically detects based on project structure.
        """
        if data_dir is None:
            # Auto-detect project root
            if '__file__' in globals():
                current_file = Path(__file__).resolve()
                project_root = current_file.parent.parent
            else:
                project_root = Path.cwd().resolve().parent
            
            self.data_dir = project_root / 'data' / 'raw' / 'ookla'
        else:
            self.data_dir = Path(data_dir)
        
        # Ensure absolute path
        self.data_dir = self.data_dir.resolve()
        
        print(f"📁 OoklaLoader initialized")
        print(f"   Data directory: {self.data_dir}")
        print(f"   Directory exists: {self.data_dir.exists()}")
    
    def load_processed_data(self, filename=None):
        """
        Load previously downloaded Ookla data
        
        Parameters:
            filename (str, optional): Specific file to load. If None, loads most recent file.
        
        Returns:
            GeoDataFrame: Ookla data
        """
        processed_dir = self.data_dir.parent / 'processed'
        
        if filename:
            file_path = processed_dir / filename
        else:
            # Find most recent file
            files = list(processed_dir.glob('*_ookla_*.geoparquet'))
            if not files:
                raise FileNotFoundError(
                    f"No Ookla data files found in {processed_dir}\n"
                    f"Run: python scripts/download_ookla.py"
                )
            file_path = max(files, key=lambda p: p.stat().st_mtime)
        
        print(f"📂 Loading Ookla data from: {file_path.name}")
        data = gpd.read_parquet(file_path)
        print(f"✅ Loaded {len(data):,} records")
        
        return data


if __name__ == "__main__":
    # Test the loader when run directly
    print("Testing NaturalEarthLoader...")
    print("=" * 60)
    
    try:
        loader = NaturalEarthLoader()
        
        # Test new stateful approach
        print("\n1️⃣ Testing set_country()...")
        loader.set_country('Indonesia')
        
        print("\n2️⃣ Testing get_provinces() without parameter...")
        provinces = loader.get_provinces()
        print(f"Provinces: {len(provinces)}")
        
        print("\n3️⃣ Testing get_provinces_by_name()...")
        sumatra = loader.get_provinces_by_name([
            'Aceh', 'Sumatera Utara', 'Sumatera Barat'
        ])
        print(f"Selected: {len(sumatra)} provinces")
        
        print("\n4️⃣ Testing single province...")
        aceh = loader.get_provinces_by_name('Aceh')
        print(f"Single province: {len(aceh)}")
        
        print("\n5️⃣ Testing region preset...")
        sumatra_full = loader.get_region_preset('sumatra')
        print(f"Sumatra preset: {len(sumatra_full)} provinces")
        
        print("\n6️⃣ Testing list_provinces()...")
        loader.list_provinces('Sumatra')
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")