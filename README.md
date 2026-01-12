# 💰 DuoFinance: Smart Personal Accounting

A modern, glassmorphism-styled personal accounting application for MacOS, designed to manage monthly expenses for two users (Masha and Pablo).

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.0+-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## ✨ Features

- **👥 Dual User Support** - Separate expense tracking for Masha and Pablo
- **📤 Smart CSV Import** - Handles semicolon-delimited bank statements with Spanish number formatting
- **🧠 Learning Engine** - Remembers your category corrections for future uploads
- **📊 Interactive Analytics** - Beautiful Plotly charts with individual and joint views
- **🎨 Glassmorphism UI** - Modern, dark-themed interface with smooth animations

## 📁 Folder Structure

```
personal-finance/
├── data/
│   ├── masha/          # Masha's monthly expense CSVs
│   └── pablo/          # Pablo's monthly expense CSVs
├── config/
│   └── category_mapping.json   # Learning engine storage
├── src/
│   ├── app.py          # Main Streamlit application
│   ├── categories.py   # Category definitions & regex engine
│   ├── data_processor.py # CSV parsing & preprocessing
│   ├── storage.py      # File I/O operations
│   └── analytics.py    # Charts & KPI calculations
├── setup.sh            # Installation script
├── run.sh              # Application launcher
└── README.md           # This file
```

## 🚀 Quick Start

### 1. Setup (One-time)

```bash
chmod +x setup.sh run.sh
./setup.sh
```

This will:
- Create a Python virtual environment
- Install all dependencies (pandas, streamlit, plotly, openpyxl)
- Initialize the directory structure

### 2. Run the Application

```bash
./run.sh
```

The app will open in your default browser at `http://localhost:8501`

## 📤 Input Format

The application expects bank statement files with the following format:

### CSV Format (Semicolon-delimited)

```csv
Concepto;Tarjeta;Fecha;Importe
Mercadona Compra;**** 1234;15/01/2024;-45,67EUR
Netflix Subscription;**** 1234;01/01/2024;-12,99EUR
```

### Supported Column Names

| Expected | Alternatives |
|----------|--------------|
| `Concepto` | `Concept`, `Description` |
| `Tarjeta` | `Card` |
| `Fecha` | `Date` |
| `Importe` | `Amount`, `Cantidad` |

### Amount Format

The app handles Spanish number formatting:
- `-20,37EUR` → `-20.37`
- `1.234,56 EUR` → `1234.56`

## 🏷️ Categories

The app automatically categorizes transactions using keyword matching:

| Category | Keywords (Examples) |
|----------|---------------------|
| 🏠 Housing & Bills | alquiler, luz, agua, internet, seguro |
| 🛒 Groceries | mercadona, lidl, carrefour, supermercado |
| 🍔 Food & Dining | restaurante, uber eats, glovo, bar |
| 📺 Subscriptions | netflix, spotify, gym, hbo |
| 🚗 Transport | gasolina, taxi, uber, renfe, parking |
| 🎮 Leisure & Entertainment | cine, hotel, viaje, concierto |
| 🛍️ Shopping | zara, amazon, ikea, primark |
| ❤️ Health & Wellness | farmacia, medico, dentista, gym |
| 💰 Financial | transferencia, bizum, comision |
| ❓ Others | Manual selection only |

## 🧠 Learning Engine

The Learning Engine makes the app smarter over time:

1. **First Upload**: The app auto-categorizes transactions using keyword patterns
2. **Manual Correction**: If you change a category, the app remembers it
3. **Future Uploads**: Your corrections are applied automatically

### How It Works

```
User uploads CSV → Auto-categorization → User corrects "IKEA Store" from "Others" to "Shopping"
                                                    ↓
                           Saved to config/category_mapping.json
                                                    ↓
Next upload with "IKEA Store" → Automatically assigned to "Shopping"
```

### Storage Location

Learned mappings are stored in `/config/category_mapping.json`:

```json
{
  "learned_mappings": {
    "IKEA Store Purchase": "Shopping",
    "Monthly Gym Fee": "Subscriptions"
  }
}
```

## 📊 Analytics Dashboard

### Individual View
- **KPIs**: Total expenses, transaction count, average transaction, top category
- **Pie Chart**: Expense distribution by category
- **Trend Chart**: Monthly spending over time

### Joint View
- **Comparison KPIs**: Side-by-side totals for Masha and Pablo
- **Bar Chart**: Category-by-category comparison between users

## 🛠️ Manual Installation

If you prefer not to use the setup script:

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install pandas streamlit plotly openpyxl

# Run the app
streamlit run src/app.py
```

## 📝 Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| pandas | Latest | Data processing |
| streamlit | Latest | Web UI framework |
| plotly | Latest | Interactive charts |
| openpyxl | Latest | Excel file support |

## 🔧 Troubleshooting

### "Module not found" error
```bash
source venv/bin/activate
pip install pandas streamlit plotly openpyxl
```

### Port already in use
```bash
streamlit run src/app.py --server.port 8502
```

### File encoding issues
Ensure your CSV file is UTF-8 encoded. Most modern spreadsheet apps support "Save as CSV UTF-8".

## 📄 License

MIT License - Feel free to use and modify for personal use.

---

Made with ❤️ for Masha and Pablo
