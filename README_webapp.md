# 🚀 Alibaba Product Updater Web Application

A modern, responsive web application for updating Alibaba.com product prices and inventory with ultra-high speed processing.

## ✨ Features

- **📁 File Upload**: Drag & drop CSV file upload with validation
- **⚙️ Update Types**: Choose between price updates or inventory updates
- **📊 Real-time Progress**: Live progress tracking with ETA calculations
- **🎯 High Performance**: Ultra-fast processing with adaptive rate limiting
- **📱 Responsive Design**: Works on desktop, tablet, and mobile devices
- **📈 Detailed Reports**: Download comprehensive update reports

## 🛠️ Installation

1. **Install Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Ensure Required Files**:
   - `product_skus_ultra_fast.csv` (SKU lookup file)
   - `alibaba_price_updater.py` (Price updater script)
   - `alibaba_inventory_updater.py` (Inventory updater script)

## 🚀 Usage

1. **Start the Web Application**:
   ```bash
   python3 app.py
   ```

2. **Open Your Browser**:
   Navigate to `http://localhost:5000`

3. **Upload CSV File**:
   - Drag & drop or click to select a CSV file
   - File must contain columns: `SPU_ID`, `price`, `inventory`

4. **Select Update Type**:
   - **💰 Update Prices**: Uses the price updater script
   - **📦 Update Inventory**: Uses the inventory updater script

5. **Monitor Progress**:
   - Real-time progress bar and statistics
   - Processing rate and ETA calculations
   - Success/failure counts

6. **Download Report**:
   - Get detailed CSV report after completion
   - Includes all update results and error details

## 📊 Performance

- **Processing Speed**: Up to 15+ updates per second
- **Concurrent Workers**: 50 parallel workers
- **Adaptive Rate Limiting**: Automatically adjusts to API limits
- **Memory Efficient**: Chunked processing for large files
- **Real-time Updates**: Live progress tracking

## 🔧 Configuration

The web application uses the same configuration as the command-line scripts:

- **API Credentials**: Set in the updater scripts
- **Rate Limiting**: Adaptive delays based on success rate
- **Chunk Size**: 10,000 rows per chunk
- **Max Workers**: 50 concurrent workers

## 📁 File Structure

```
├── app.py                          # Flask web application
├── templates/
│   └── index.html                  # Main web interface
├── uploads/                        # Temporary file storage
├── alibaba_price_updater.py        # Price update script
├── alibaba_inventory_updater.py    # Inventory update script
├── product_skus_ultra_fast.csv     # SKU lookup data
└── requirements.txt                # Python dependencies
```

## 🌐 Web Interface Features

### Upload Section
- Drag & drop file upload
- CSV validation
- File information display
- Support for large files (up to 100MB)

### Update Type Selection
- Clear visual selection
- Price vs Inventory updates
- Validation before starting

### Progress Tracking
- Real-time progress bar
- Live statistics (processed, successful, failed)
- Processing rate and ETA
- Status indicators

### Results & Reports
- Download detailed CSV reports
- Success/failure statistics
- Error details and troubleshooting

## 🔒 Security Features

- File type validation (CSV only)
- Secure filename handling
- Temporary file cleanup
- Input sanitization

## 📱 Mobile Support

- Responsive design
- Touch-friendly interface
- Mobile-optimized layout
- Cross-platform compatibility

## 🚨 Error Handling

- File validation errors
- API connection issues
- Rate limiting handling
- Progress tracking errors
- User-friendly error messages

## 🔄 Background Processing

- Non-blocking updates
- Real-time progress tracking
- Automatic cleanup
- Job management

## 📈 Monitoring

- Live progress updates
- Performance metrics
- Success rates
- Processing speeds

## 🎯 Use Cases

- **Bulk Price Updates**: Update thousands of product prices
- **Inventory Management**: Sync inventory levels
- **Data Migration**: Transfer pricing data
- **Regular Maintenance**: Scheduled updates

## 🛡️ Best Practices

1. **Test with Small Files**: Start with small CSV files
2. **Monitor Progress**: Watch for rate limiting
3. **Check Reports**: Review detailed results
4. **Backup Data**: Keep original files safe
5. **API Limits**: Respect Alibaba API limits

## 🚀 Getting Started

1. Install dependencies: `pip install -r requirements.txt`
2. Start the app: `python3 app.py`
3. Open browser: `http://localhost:5000`
4. Upload your CSV file
5. Select update type
6. Monitor progress
7. Download results

## 📞 Support

For issues or questions:
- Check the console output for errors
- Review the generated reports
- Ensure API credentials are correct
- Verify CSV file format

---

**🎉 Enjoy ultra-fast Alibaba product updates with our modern web interface!**
