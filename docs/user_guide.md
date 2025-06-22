# User Guide - Multi-Source Data Collection System

## Table of Contents
1. [Quick Start](#quick-start)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Using the CLI](#using-the-cli)
5. [Data Collection](#data-collection)
6. [Analysis & Reports](#analysis--reports)
7. [Export Options](#export-options)
8. [Troubleshooting](#troubleshooting)
9. [Advanced Usage](#advanced-usage)

## Quick Start

Get started with the Multi-Source Data Collection System in 3 steps:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Initialize the system
python main.py setup

# 3. Start scraping
python main.py scrape --sources="amazon,ebay" --keywords="laptop,gaming" --max-pages=3
```

## Installation

### Prerequisites
- Python 3.8 or higher
- Chrome browser (for Selenium scraping)
- Git (for version control)

### Step-by-Step Installation

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/Multi-Source-Data-Collection-System.git
cd Multi-Source-Data-Collection-System
```

2. **Create virtual environment:**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Initialize the system:**
```bash
python main.py setup
```

## Configuration

The system uses YAML configuration files in the `config/` directory:

### Main Settings (`config/settings.yaml`)
```yaml
# Database configuration
database:
  url: "sqlite:///data/products.db"
  echo: false

# Scraping settings
scraping:
  delay:
    min: 1.0
    max: 3.0
  retries: 3
  timeout: 30
  max_workers: 5

# Sources configuration
sources:
  amazon:
    enabled: true
    base_urls:
      - "https://www.amazon.com/s"
  ebay:
    enabled: true
    base_urls:
      - "https://www.ebay.com/sch/i.html"
```

### Scraper Settings (`config/scrapers.yaml`)
Contains CSS selectors and extraction patterns for each website.

## Using the CLI

The system provides a comprehensive command-line interface:

### Available Commands

```bash
python main.py --help  # Show all commands
```

**Main Commands:**
- `scrape` - Collect data from sources
- `report` - Generate analysis reports
- `export` - Export data in various formats
- `setup` - Initialize system
- `test` - Run test suite
- `collect` - Advanced collection strategies

### Common Options
- `--verbose, -v` - Increase verbosity (use `-vv` for debug)
- `--config` - Specify custom configuration file

## Data Collection

### Basic Scraping
```bash
# Scrape from multiple sources
python main.py scrape --sources="amazon,ebay" --keywords="smartphone,tablet"

# Use different scraper types
python main.py scrape --scraper-type=selenium --keywords="laptop"

# Concurrent processing
python main.py scrape --concurrent --keywords="headphones" --max-pages=5
```

### Advanced Collection Strategies
```bash
# Comprehensive collection (5000+ products)
python main.py collect --strategy=comprehensive --target=5000

# Quick collection for testing
python main.py collect --strategy=quick --target=100

# Focused collection on specific categories
python main.py collect --strategy=focused --target=1000
```

### Scraper Types

1. **Static Scraper** (`--scraper-type=static`)
   - Fastest option
   - Uses BeautifulSoup4
   - Good for basic HTML content

2. **Selenium Scraper** (`--scraper-type=selenium`)
   - Handles JavaScript content
   - Slower but more comprehensive
   - Bypasses basic anti-bot measures

3. **Scrapy Framework** (`--scraper-type=scrapy`)
   - Most robust for large-scale scraping
   - Built-in anti-bot protection
   - Structured data extraction

4. **Concurrent Processing** (`--concurrent`)
   - Uses multiple threads
   - Faster overall collection
   - Automatic load balancing

## Analysis & Reports

### Generate Reports
```bash
# Summary report (default)
python main.py report --type=summary --period=30

# Price trend analysis
python main.py report --type=trend --period=7

# Source comparison report
python main.py report --type=comparison --period=14
```

### Report Types

1. **Summary Report**
   - Overall statistics
   - Price distributions
   - Source breakdown
   - Data quality metrics

2. **Trend Report**
   - Price changes over time
   - Market trends
   - Seasonal patterns
   - Forecast indicators

3. **Comparison Report**
   - Cross-source analysis
   - Price comparisons
   - Feature analysis
   - Competitive insights

### Report Outputs
Reports are saved in `data_output/reports/` and include:
- HTML report with interactive charts
- JSON data files
- Chart images (PNG/SVG)
- Raw data exports

## Export Options

### Export Formats
```bash
# CSV export (default)
python main.py export --format=csv --filter-days=7

# JSON export
python main.py export --format=json --output="custom_output/"

# Excel export with multiple sheets
python main.py export --format=excel --filter-days=30
```

### Export Features
- **Filtering**: Export data from specific time periods
- **Custom Output**: Specify output directories
- **Multiple Formats**: CSV, JSON, Excel support
- **Data Validation**: Automatic quality checks

## Troubleshooting

### Common Issues

#### 1. Installation Problems
```bash
# Update pip
python -m pip install --upgrade pip

# Install specific versions
pip install -r requirements.txt --force-reinstall
```

#### 2. Chrome Driver Issues
```bash
# Download ChromeDriver manually
# Place in system PATH or project directory
```

#### 3. Anti-Bot Detection
- Increase delays in `config/settings.yaml`
- Use different scraper types
- Check proxy settings
- Verify user agent rotation

#### 4. Database Errors
```bash
# Reset database
python main.py setup --force

# Check database status
python main.py test
```

### Debug Mode
```bash
# Enable detailed logging
python main.py -vv scrape --keywords="test"

# Check log files
tail -f logs/scraping.log
```

### Performance Issues
```bash
# Reduce concurrent workers
# Edit config/settings.yaml:
scraping:
  max_workers: 2  # Reduce from default 5

# Use lighter scraper
python main.py scrape --scraper-type=static
```

## Advanced Usage

### Custom Configuration
```bash
# Use custom config file
python main.py --config="my_config.yaml" scrape --keywords="laptop"
```

### Batch Operations
```bash
# Process multiple keyword sets
python main.py scrape --keywords="laptop,gaming laptop,ultrabook" --max-pages=10
```

### Scheduled Collection
```bash
# Use with cron for scheduled scraping
0 */6 * * * cd /path/to/project && python main.py collect --strategy=quick
```

### Integration with Other Tools
```python
# Python script integration
from src.scrapers.manager import ScrapingManager
from src.utils.config import load_config

config = load_config('config/settings.yaml')
manager = ScrapingManager(config)
results = manager.scrape_all(['amazon'], ['smartphone'], max_pages=5)
```

### Performance Monitoring
```bash
# Monitor system resources during scraping
python main.py scrape --verbose --keywords="monitor_test"

# Check collection statistics
python main.py report --type=summary
```

## Tips for Best Results

### 1. Respectful Scraping
- Use appropriate delays (1-3 seconds)
- Monitor server responses
- Respect robots.txt files
- Don't overwhelm servers

### 2. Data Quality
- Use multiple sources for validation
- Regular data quality checks
- Clean and normalize data
- Monitor for changes in website structure

### 3. Performance Optimization
- Start with small batches
- Monitor system resources
- Use appropriate scraper types
- Regular database maintenance

### 4. Legal Compliance
- Check website terms of service
- Only collect public data
- Respect copyright and trademarks
- Include proper attribution

## Getting Help

### Documentation
- `docs/architecture.md` - Technical architecture
- `docs/api_reference.md` - API documentation
- `README.md` - Project overview

### Community
- GitHub Issues: Report bugs or request features
- Project Wiki: Additional tutorials and examples

### Support
For technical support:
1. Check this user guide
2. Review the troubleshooting section
3. Enable verbose logging (`-vv`)
4. Create a GitHub issue with logs and configuration

---

**Happy scraping! 🚀** 