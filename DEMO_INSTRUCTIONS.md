# 🎬 VIDEO DEMO INSTRUCTIONS

## How to Run the Complete Project Demonstration

### Prerequisites
1. Make sure you're in the project directory: `Multi-Source-Data-Collection-System`
2. Ensure your virtual environment is activated: `venv\Scripts\activate`
3. Verify all dependencies are installed: `pip install -r requirements.txt`

### Running the Demo

**Option 1: Run the Complete Demo Script (RECOMMENDED)**
```powershell
.\video_demo_script.ps1
```

**Option 2: Run Individual Commands (if script fails)**
```powershell
# 1. Show database status
python -c "import sqlite3; conn = sqlite3.connect('data/products.db'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM products'); total = cursor.fetchone()[0]; cursor.execute('SELECT source, COUNT(*) FROM products GROUP BY source'); sources = cursor.fetchall(); print(f'Total: {total:,}'); [print(f'{s}: {c:,}') for s, c in sources]; conn.close()"

# 2. Show CLI help
python main.py --help

# 3. Generate reports
python main.py generate-report --format all

# 4. Run tests
python -m pytest tests/test_anti_bot.py -v

# 5. Show project structure
dir
tree src /F
```

## Demo Script Features

The script demonstrates **all 10 steps** of your project:

1. **Project Structure** - Shows file organization
2. **Database Status** - Current data collection (12,000+ records)
3. **CLI Interface** - Help commands and usage
4. **Data Analysis** - Report generation with statistics
5. **Visualizations** - Charts created with matplotlib/seaborn
6. **Anti-Bot Testing** - Protection mechanism validation
7. **Data Export** - CSV, Excel, JSON, HTML formats
8. **Architecture** - Code structure and design patterns
9. **Performance Stats** - Collection rates and success metrics
10. **Final Summary** - Complete requirements checklist

## Video Recording Tips

1. **Screen Resolution**: Set to 1920x1080 for best quality
2. **Terminal Size**: Make it large enough to read clearly
3. **Pause Points**: The script includes pause points - use them to explain features
4. **Browser Demo**: Script will offer to open HTML report - great for showing visualizations
5. **File Explorer**: Have file explorer open to show generated files

## What to Highlight in Your Video

- **12,879 products** collected from 3 sources (Amazon, eBay, Walmart)
- **Multiple scraping methods** (Static, Selenium, Scrapy)
- **Professional visualizations** with matplotlib/seaborn
- **Anti-bot protection** working (9/9 tests passing)
- **Comprehensive reports** in multiple formats
- **Concurrent processing** capabilities
- **Database integration** with SQLite
- **Professional code architecture**

## Estimated Demo Time: 8-12 minutes

Perfect for the required video length! 🎬 