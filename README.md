# Finance & Recruiting Dashboard

A modern Flask-based dashboard for analyzing financial and recruitment data with interactive visualizations and KPI tracking.

## Features

- **📊 Interactive Data Analysis**: Upload CSV files for P&L, Balance Sheet, Recruitment, and Margin statements
- **🎯 Flexible Column Mapping**: No strict schema required - map your columns dynamically
- **📈 Real-time Visualizations**: Interactive charts powered by Plotly
- **💰 KPI Tracking**: Key performance indicators with financial metrics
- **📱 Responsive Design**: Works seamlessly on desktop and mobile devices
- **🎨 Modern UI**: Clean, professional interface with TECHGENE branding

## Tech Stack

- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, JavaScript (jQuery)
- **Charts**: Plotly.js
- **Data Processing**: Pandas, NumPy
- **Styling**: Custom CSS with responsive design

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/praneethkukunuru/recruitment-dashboard.git
   cd recruitment-dashboard
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python app.py
   ```

4. **Access the dashboard**
   Open your browser and navigate to `http://localhost:5003`

## Usage

### 1. Upload Data
- Use the sidebar to upload your CSV files
- Supported file types: P&L, Balance Sheet, Recruitment, and Margin statements
- Drag and drop or click to browse files

### 2. Map Columns
- After uploading, map your CSV columns to the appropriate fields
- The system will auto-suggest common column names
- No strict schema required - flexibility for different data formats

### 3. View KPIs
- Key performance indicators are automatically calculated
- Revenue, Gross Profit, Net Income, and Balance Sheet metrics
- Real-time updates as you modify mappings

### 4. Explore Visualizations
- Interactive charts for trend analysis
- P&L waterfall charts
- Balance sheet comparisons
- Recruitment placement tracking

### 5. Export Reports
- Download HTML reports with embedded charts
- Save configuration for future use

## Project Structure

```
recruitment-dashboard/
├── app.py                 # Flask application
├── requirements.txt       # Python dependencies
├── README.md             # Project documentation
├── .gitignore            # Git ignore rules
├── templates/
│   └── index.html        # Main dashboard template
├── static/
│   ├── css/
│   │   └── style.css     # Dashboard styling
│   ├── js/
│   │   └── dashboard.js  # Frontend functionality
│   └── techgene-logo-new.png  # TECHGENE logo
└── uploads/              # File upload directory (auto-created)
```

## API Endpoints

- `GET /` - Main dashboard page
- `POST /upload` - File upload endpoint
- `POST /process` - Data processing and chart generation

## Configuration

The application can be configured by modifying the following:

- **Port**: Change the port in `app.py` (default: 5003)
- **Upload folder**: Modify `UPLOAD_FOLDER` in `app.py`
- **Secret key**: Update `app.secret_key` for production

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions, please open an issue on GitHub or contact the development team.

---

**Built with ❤️ by TECHGENE** 