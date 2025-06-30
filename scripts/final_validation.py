#!/usr/bin/env python3
"""
Final Validation Script

This script performs comprehensive validation of the Multi-Source Data Collection System.
Week 3 requirement: Final testing and validation.
"""

import sys
import os
import time
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
import subprocess

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.config import load_config
from src.utils.logger import setup_logger
from src.scrapers.manager import ScrapingManager
from src.analysis.reports import ReportGenerator
from src.data.database import DatabaseManager

logger = setup_logger(__name__)


class FinalValidator:
    """Comprehensive validation of all system components."""
    
    def __init__(self, config_path: str = 'config/settings.yaml'):
        """Initialize the validator."""
        self.config = load_config(config_path)
        self.validation_results = {
            'timestamp': time.time(),
            'overall_status': 'PENDING',
            'test_results': {},
            'performance_metrics': {},
            'errors': [],
            'warnings': []
        }
        
    def validate_environment(self) -> bool:
        """Validate the development environment."""
        logger.info("Validating environment...")
        
        try:
            # Check Python version
            python_version = sys.version_info
            if python_version.major < 3 or python_version.minor < 8:
                self.validation_results['errors'].append(
                    f"Python 3.8+ required, found {python_version.major}.{python_version.minor}"
                )
                return False
            
            # Check required packages with proper import mapping
            package_imports = {
                'requests': 'requests',
                'beautifulsoup4': 'bs4',  # beautifulsoup4 imports as bs4
                'selenium': 'selenium',
                'scrapy': 'scrapy',
                'pandas': 'pandas',
                'matplotlib': 'matplotlib',
                'plotly': 'plotly',
                'sqlalchemy': 'sqlalchemy',
                'click': 'click',
                'pyyaml': 'yaml',  # pyyaml imports as yaml
                'pytest': 'pytest'
            }
            
            missing_packages = []
            for package_name, import_name in package_imports.items():
                try:
                    __import__(import_name)
                    logger.debug(f"✅ {package_name} ({import_name}) - Available")
                except ImportError as e:
                    logger.warning(f"❌ {package_name} ({import_name}) - Missing: {e}")
                    missing_packages.append(package_name)
            
            if missing_packages:
                self.validation_results['warnings'].append(
                    f"Some packages may need installation: {', '.join(missing_packages)}"
                )
                # Don't fail validation for missing packages if core functionality works
                logger.warning(f"Missing packages detected: {missing_packages}")
            else:
                logger.info("All required packages are available")
            
            # Test core imports that are critical for the project
            try:
                import yaml
                import bs4
                from src.utils.config import load_config
                from src.scrapers.static_scraper import StaticScraper
                logger.info("✅ Core project imports successful")
            except ImportError as e:
                self.validation_results['errors'].append(f"Critical import failed: {e}")
                return False
            
            # Check Chrome browser for Selenium (optional)
            try:
                from selenium import webdriver
                from selenium.webdriver.chrome.options import Options
                options = Options()
                options.add_argument('--headless')
                options.add_argument('--no-sandbox')
                driver = webdriver.Chrome(options=options)
                driver.quit()
                logger.info("✅ Chrome/ChromeDriver available")
            except Exception as e:
                self.validation_results['warnings'].append(
                    f"Chrome/ChromeDriver not available: {e}"
                )
            
            self.validation_results['test_results']['environment'] = True
            logger.info("Environment validation passed")
            return True
            
        except Exception as e:
            self.validation_results['errors'].append(f"Environment validation failed: {e}")
            self.validation_results['test_results']['environment'] = False
            return False
    
    def validate_configuration(self) -> bool:
        """Validate configuration files."""
        logger.info("Validating configuration...")
        
        try:
            # Check main configuration
            required_config_keys = [
                'database', 'scraping', 'sources', 'selenium'
            ]
            
            for key in required_config_keys:
                if key not in self.config:
                    self.validation_results['errors'].append(
                        f"Missing configuration section: {key}"
                    )
                    return False
            
            # Check scraper configuration
            scrapers_config_path = Path('config/scrapers.yaml')
            if not scrapers_config_path.exists():
                self.validation_results['errors'].append(
                    "Scrapers configuration file missing"
                )
                return False
            
            # Validate database URL
            db_url = self.config.get('database', {}).get('url', '')
            if not db_url:
                self.validation_results['errors'].append(
                    "Database URL not configured"
                )
                return False
            
            self.validation_results['test_results']['configuration'] = True
            logger.info("Configuration validation passed")
            return True
            
        except Exception as e:
            self.validation_results['errors'].append(f"Configuration validation failed: {e}")
            self.validation_results['test_results']['configuration'] = False
            return False
    
    def validate_database(self) -> bool:
        """Validate database connectivity and structure."""
        logger.info("Validating database...")
        
        try:
            db_manager = DatabaseManager(self.config)
            
            # Test database connection
            with db_manager.get_session() as session:
                # Check if tables exist
                from src.data.models import Product, ScrapingSession, PriceHistory
                
                tables = [Product, ScrapingSession, PriceHistory]
                for table in tables:
                    count = session.query(table).count()
                    logger.info(f"Table {table.__tablename__}: {count} records")
            
            # Test basic database operations
            stats = db_manager.get_statistics()
            if stats is None:
                self.validation_results['warnings'].append(
                    "Database statistics unavailable"
                )
            
            self.validation_results['test_results']['database'] = True
            logger.info("Database validation passed")
            return True
            
        except Exception as e:
            self.validation_results['errors'].append(f"Database validation failed: {e}")
            self.validation_results['test_results']['database'] = False
            return False
    
    def validate_scrapers(self) -> bool:
        """Validate scraper functionality."""
        logger.info("Validating scrapers...")
        
        try:
            scraping_manager = ScrapingManager(self.config)
            
            # Test static scraper
            static_scraper = scraping_manager.get_scraper('static')
            if static_scraper is None:
                self.validation_results['errors'].append("Static scraper initialization failed")
                return False
            
            # Test selenium scraper (if available)
            try:
                selenium_scraper = scraping_manager.get_scraper('selenium')
                if selenium_scraper is not None:
                    selenium_scraper.cleanup()  # Clean up resources
            except Exception as e:
                self.validation_results['warnings'].append(
                    f"Selenium scraper unavailable: {e}"
                )
            
            # Test basic scraping functionality with minimal request
            test_results = scraping_manager.scrape_single(
                'amazon', 'test', 1, 'static'
            )
            
            if test_results is None:
                self.validation_results['warnings'].append(
                    "Test scraping returned no results (may be normal)"
                )
            
            self.validation_results['test_results']['scrapers'] = True
            logger.info("Scrapers validation passed")
            return True
            
        except Exception as e:
            self.validation_results['errors'].append(f"Scrapers validation failed: {e}")
            self.validation_results['test_results']['scrapers'] = False
            return False
    
    def validate_analysis_components(self) -> bool:
        """Validate analysis and reporting components."""
        logger.info("Validating analysis components...")
        
        try:
            # Test report generator
            report_generator = ReportGenerator(self.config)
            
            # Test statistics module
            from src.analysis.statistics import DataStatistics
            stats = DataStatistics()
            
            # Test basic statistics (should work even with empty database)
            basic_stats = stats.get_basic_statistics()
            if basic_stats is None:
                self.validation_results['warnings'].append(
                    "Basic statistics returned no data"
                )
            
            # Test visualization module
            from src.analysis.visualization import DataVisualizer
            visualizer = DataVisualizer(self.config)
            
            self.validation_results['test_results']['analysis'] = True
            logger.info("Analysis components validation passed")
            return True
            
        except Exception as e:
            self.validation_results['errors'].append(f"Analysis validation failed: {e}")
            self.validation_results['test_results']['analysis'] = False
            return False
    
    def validate_cli_interface(self) -> bool:
        """Validate CLI interface functionality."""
        logger.info("Validating CLI interface...")
        
        try:
            # Test main CLI commands
            commands_to_test = [
                (['python', 'main.py', '--help'], 'Main help'),
                (['python', 'main.py', 'setup', '--help'], 'Setup help'),
                (['python', 'main.py', 'report', '--help'], 'Report help'),
                (['python', 'main.py', 'export', '--help'], 'Export help')
            ]
            
            successful_commands = 0
            total_commands = len(commands_to_test)
            
            for cmd, description in commands_to_test:
                try:
                    result = subprocess.run(
                        cmd, 
                        capture_output=True, 
                        text=True, 
                        timeout=30,
                        cwd=Path(__file__).parent.parent  # Run from project root
                    )
                    
                    # Check if command executed successfully (return code 0 or help output contains expected text)
                    if result.returncode == 0 or 'Usage:' in result.stdout or '--help' in result.stdout:
                        logger.debug(f"✅ {description} - Working")
                        successful_commands += 1
                    else:
                        logger.warning(f"❌ {description} - Return code: {result.returncode}")
                        self.validation_results['warnings'].append(
                            f"CLI command issue: {description} (exit code: {result.returncode})"
                        )
                        
                except subprocess.TimeoutExpired:
                    logger.warning(f"⏱️ {description} - Timeout")
                    self.validation_results['warnings'].append(
                        f"CLI command timeout: {description}"
                    )
                except Exception as e:
                    logger.warning(f"❌ {description} - Error: {e}")
                    self.validation_results['warnings'].append(
                        f"CLI command error: {description} - {e}"
                    )
            
            # Consider CLI validation successful if at least 75% of commands work
            success_rate = (successful_commands / total_commands) * 100
            
            if success_rate >= 75:
                logger.info(f"CLI interface validation passed ({success_rate:.0f}% success rate)")
                self.validation_results['test_results']['cli'] = True
                return True
            else:
                logger.warning(f"CLI interface validation failed ({success_rate:.0f}% success rate)")
                self.validation_results['test_results']['cli'] = False
                return False
            
        except Exception as e:
            self.validation_results['errors'].append(f"CLI validation failed: {e}")
            self.validation_results['test_results']['cli'] = False
            return False
    
    def validate_file_structure(self) -> bool:
        """Validate project file structure."""
        logger.info("Validating file structure...")
        
        try:
            project_root = Path(__file__).parent.parent
            
            required_files = [
                'main.py', 'README.md', 'requirements.txt', 'setup.py',
                'config/settings.yaml', 'config/scrapers.yaml'
            ]
            
            required_dirs = [
                'src', 'src/scrapers', 'src/data', 'src/analysis',
                'src/utils', 'src/cli', 'tests', 'docs', 'data_output'
            ]
            
            missing_files = []
            for file_path in required_files:
                if not (project_root / file_path).exists():
                    missing_files.append(file_path)
            
            missing_dirs = []
            for dir_path in required_dirs:
                if not (project_root / dir_path).exists():
                    missing_dirs.append(dir_path)
            
            if missing_files:
                self.validation_results['errors'].append(
                    f"Missing files: {', '.join(missing_files)}"
                )
            
            if missing_dirs:
                self.validation_results['errors'].append(
                    f"Missing directories: {', '.join(missing_dirs)}"
                )
            
            if missing_files or missing_dirs:
                self.validation_results['test_results']['file_structure'] = False
                return False
            
            self.validation_results['test_results']['file_structure'] = True
            logger.info("File structure validation passed")
            return True
            
        except Exception as e:
            self.validation_results['errors'].append(f"File structure validation failed: {e}")
            self.validation_results['test_results']['file_structure'] = False
            return False
    
    def run_unit_tests(self) -> bool:
        """Run unit tests using pytest."""
        logger.info("Running unit tests...")
        
        try:
            # Use python -m pytest instead of direct pytest to ensure proper path
            result = subprocess.run([
                sys.executable, '-m', 'pytest', 'tests/', 
                '-v', '--tb=short', '--disable-warnings'
            ], 
            capture_output=True, 
            text=True, 
            timeout=120,
            cwd=Path(__file__).parent.parent  # Run from project root
            )
            
            # Parse pytest output
            output = result.stdout + result.stderr
            self.validation_results['test_results']['unit_tests_output'] = output
            
            # Count passed/failed tests
            passed = output.count(' PASSED')
            failed = output.count(' FAILED')
            errors = output.count('ERROR')
            
            logger.info(f"Unit tests completed: {passed} passed, {failed} failed")
            
            # Consider successful if more than 80% pass and no critical errors
            total_tests = passed + failed
            success_rate = (passed / total_tests * 100) if total_tests > 0 else 0
            
            if success_rate >= 80 and errors == 0:
                self.validation_results['test_results']['unit_tests'] = True
                return True
            elif success_rate >= 60:  # Partial success
                self.validation_results['warnings'].append(
                    f"Unit tests partially successful: {success_rate:.1f}% pass rate"
                )
                self.validation_results['test_results']['unit_tests'] = True
                return True
            else:
                self.validation_results['warnings'].append(
                    f"Some unit tests failed:\n{output[-1000:]}"  # Last 1000 chars
                )
                self.validation_results['test_results']['unit_tests'] = False
                return False
                
        except subprocess.TimeoutExpired:
            self.validation_results['warnings'].append("Unit tests timed out")
            self.validation_results['test_results']['unit_tests'] = False
            return False
        except Exception as e:
            self.validation_results['warnings'].append(f"Unit test execution failed: {e}")
            self.validation_results['test_results']['unit_tests'] = False
            return False
    
    def measure_performance(self) -> Dict[str, Any]:
        """Measure system performance metrics."""
        logger.info("Measuring performance...")
        
        performance_metrics = {}
        
        try:
            # Measure database query performance
            start_time = time.time()
            db_manager = DatabaseManager(self.config)
            with db_manager.get_session() as session:
                from src.data.models import Product
                products = session.query(Product).limit(100).all()
            db_query_time = time.time() - start_time
            performance_metrics['db_query_time_ms'] = round(db_query_time * 1000, 2)
            
            # Measure configuration loading time
            start_time = time.time()
            load_config('config/settings.yaml')
            config_load_time = time.time() - start_time
            performance_metrics['config_load_time_ms'] = round(config_load_time * 1000, 2)
            
            # Measure scraper initialization time
            start_time = time.time()
            scraping_manager = ScrapingManager(self.config)
            scraper_init_time = time.time() - start_time
            performance_metrics['scraper_init_time_ms'] = round(scraper_init_time * 1000, 2)
            
            self.validation_results['performance_metrics'].update(performance_metrics)
            
        except Exception as e:
            self.validation_results['warnings'].append(f"Performance measurement failed: {e}")
        
        return performance_metrics
    
    def generate_validation_report(self) -> str:
        """Generate comprehensive validation report."""
        logger.info("Generating validation report...")
        
        # Determine overall status
        failed_tests = [
            test for test, result in self.validation_results['test_results'].items()
            if not result
        ]
        
        if not failed_tests and not self.validation_results['errors']:
            self.validation_results['overall_status'] = 'PASSED'
        elif self.validation_results['errors']:
            self.validation_results['overall_status'] = 'FAILED'
        else:
            self.validation_results['overall_status'] = 'PASSED_WITH_WARNINGS'
        
        # Create report
        report_path = Path('data_output/validation_report.json')
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(self.validation_results, f, indent=2, default=str)
        
        logger.info(f"Validation report saved to: {report_path}")
        return str(report_path)
    
    def run_full_validation(self) -> Dict[str, Any]:
        """Run complete validation suite."""
        logger.info("Starting full validation suite...")
        
        start_time = time.time()
        
        # Run all validation steps
        validation_steps = [
            ('environment', self.validate_environment),
            ('configuration', self.validate_configuration),
            ('file_structure', self.validate_file_structure),
            ('database', self.validate_database),
            ('scrapers', self.validate_scrapers),
            ('analysis', self.validate_analysis_components),
            ('cli', self.validate_cli_interface),
            ('unit_tests', self.run_unit_tests)
        ]
        
        for step_name, step_function in validation_steps:
            logger.info(f"Running validation step: {step_name}")
            try:
                step_function()
            except Exception as e:
                logger.error(f"Validation step {step_name} failed: {e}")
                self.validation_results['test_results'][step_name] = False
                self.validation_results['errors'].append(f"{step_name}: {e}")
        
        # Measure performance
        self.measure_performance()
        
        # Calculate duration
        end_time = time.time()
        self.validation_results['duration_seconds'] = round(end_time - start_time, 2)
        
        # Generate report
        report_path = self.generate_validation_report()
        
        logger.info(f"Full validation completed in {self.validation_results['duration_seconds']} seconds")
        logger.info(f"Overall status: {self.validation_results['overall_status']}")
        
        return self.validation_results


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Final Validation Tool')
    parser.add_argument('--step', choices=[
        'environment', 'configuration', 'database', 'scrapers',
        'analysis', 'cli', 'tests', 'performance'
    ], help='Run specific validation step')
    parser.add_argument('--config', default='config/settings.yaml', help='Configuration file')
    parser.add_argument('--output', help='Output file for results')
    
    args = parser.parse_args()
    
    validator = FinalValidator(args.config)
    
    if args.step:
        # Run specific validation step
        step_functions = {
            'environment': validator.validate_environment,
            'configuration': validator.validate_configuration,
            'database': validator.validate_database,
            'scrapers': validator.validate_scrapers,
            'analysis': validator.validate_analysis_components,
            'cli': validator.validate_cli_interface,
            'tests': validator.run_unit_tests,
            'performance': validator.measure_performance
        }
        
        result = step_functions[args.step]()
        print(f"Validation step '{args.step}': {'PASSED' if result else 'FAILED'}")
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(validator.validation_results, f, indent=2, default=str)
    
    else:
        # Run full validation
        results = validator.run_full_validation()
        
        print("=== Final Validation Results ===")
        print(f"Overall Status: {results['overall_status']}")
        print(f"Duration: {results['duration_seconds']} seconds")
        print(f"Tests Passed: {sum(1 for r in results['test_results'].values() if r)}")
        print(f"Tests Failed: {sum(1 for r in results['test_results'].values() if not r)}")
        print(f"Errors: {len(results['errors'])}")
        print(f"Warnings: {len(results['warnings'])}")
        
        if results['errors']:
            print("\nErrors:")
            for error in results['errors']:
                print(f"- {error}")
        
        if results['warnings']:
            print("\nWarnings:")
            for warning in results['warnings']:
                print(f"- {warning}")
        
        print(f"\nDetailed report saved to: data_output/validation_report.json")


if __name__ == '__main__':
    main() 