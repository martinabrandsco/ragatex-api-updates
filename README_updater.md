# Alibaba Product Updater

This script updates product information on Alibaba using the ICBU Product Update API v2. It reads product data from a CSV file and updates pricing and inventory information.

## Features

- **CSV-based updates**: Read product data from a CSV file
- **SKU support**: Handle products with multiple SKU IDs
- **Flexible pricing**: Support both SKU-based and direct pricing
- **Error handling**: Comprehensive error reporting and logging
- **Batch processing**: Update multiple products in one run

## Files

- `alibaba_product_updater.py` - Main script
- `config.py` - Configuration file with API credentials
- `sample_product_updates.csv` - Sample CSV file for testing
- `test_updater.py` - Test script to verify JSON structure
- `README_updater.md` - This documentation

## CSV Format

The CSV file must contain the following columns:

| Column | Description | Required | Example |
|--------|-------------|----------|---------|
| Product_ID | Alibaba product ID to update | Yes | 1601464242677 |
| SPU_ID | SPU identifier (not used in API) | Yes | SPU001 |
| SKU_IDs | Semicolon-separated SKU IDs | No | 5929192;5929193 |
| price | Price to set | Yes | 15.50 |
| inventory | Inventory quantity | Yes | 500 |

### SKU Handling

- **With SKU IDs**: Uses `sku_info` structure with individual SKU pricing
- **Without SKU IDs**: Uses direct `price` with `TIERED` pricing type

## Setup

1. **Install dependencies**:
   ```bash
   pip install iop-sdk-python
   ```

2. **Configure API credentials**:
   - Copy `config.py` and update with your actual API credentials
   - Update `API_URL`, `APP_KEY`, `APP_SECRET`, and `ACCESS_TOKEN`

3. **Prepare your CSV file**:
   - Create a CSV file with the required columns
   - Use the sample file as a template

## Usage

### Basic Usage

```bash
python alibaba_product_updater.py
```

### Test JSON Structure

Before running with real data, test the JSON structure:

```bash
python test_updater.py
```

This will show you the exact JSON that would be sent to the API for different product types.

## API Request Structure

The script generates JSON in the following format:

### For Products with SKU IDs

```json
{
  "trade_info": {
    "unit": "Piece",
    "inventory": "500",
    "moq": "1",
    "sku_info": [
      {
        "sku_price": {
          "price": "15.50",
          "currency": "USD"
        },
        "sku_id": "5929192",
        "sale_attributes": [
          {
            "attribute_name": "Color",
            "attribute_value": "Default"
          }
        ],
        "inventory": "500",
        "sku_code": "5929192"
      }
    ]
  }
}
```

### For Products without SKU IDs

```json
{
  "trade_info": {
    "unit": "Piece",
    "inventory": "200",
    "moq": "1",
    "price": {
      "price_type": "TIERED",
      "currency": "USD",
      "tiered_price": [
        {
          "quantity": "1",
          "price": "25.00"
        }
      ],
      "range_price": {
        "max_price": "25.00",
        "min_price": "25.00"
      }
    }
  }
}
```

## Error Handling

The script provides comprehensive error handling:

- **File errors**: Missing CSV files, invalid file format
- **Data errors**: Missing required columns, invalid data types
- **API errors**: Network issues, authentication failures, API errors
- **Validation errors**: Invalid product IDs, malformed data

## Output

The script provides detailed output including:

- Progress information for each product
- Success/failure status for each update
- Error messages for failed updates
- Summary statistics at the end

## Example Output

```
Starting product updates...
==================================================
Processing row 1: Product ID 1601464242677
  SKU IDs: ['5929192', '5929193']
  Price: 15.50
  Inventory: 500
  ✓ Success: SUCCESS

Processing row 2: Product ID 1601464242678
  SKU IDs: None
  Price: 25.00
  Inventory: 200
  ✓ Success: SUCCESS

==================================================
UPDATE SUMMARY
==================================================
Total products processed: 2
Successful updates: 2
Failed updates: 0
==================================================
```

## Troubleshooting

### Common Issues

1. **Import Error**: Make sure `iop-sdk-python` is installed
2. **Config Error**: Ensure `config.py` exists with valid credentials
3. **CSV Error**: Check CSV file format and column names
4. **API Error**: Verify API credentials and network connectivity

### Debug Mode

To see more detailed information, you can modify the script to include debug logging or run the test script to verify JSON structure.

## Security Notes

- Keep your API credentials secure
- Don't commit `config.py` to version control
- Use environment variables for production deployments
- Regularly rotate your access tokens
