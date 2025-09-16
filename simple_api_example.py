#!/usr/bin/env python3
"""
Simple API Example - Matches the exact API documentation format

This script shows how to use the API exactly as shown in the documentation.
"""

import iop
from config import API_URL, APP_KEY, APP_SECRET, ACCESS_TOKEN


def test_api_call():
    """
    Test the API call with the exact format from the documentation.
    """
    # Initialize the client
    client = iop.IopClient(API_URL, APP_KEY, APP_SECRET)
    
    # Create the request
    request = iop.IopRequest('/alibaba/icbu/product/update/v2')
    
    # Add the product_info parameter with the exact JSON from the documentation
    product_info_json = '{"category_info":{"category_name":"Apparel \\u0026 Accessories / Men\\u0027s Clothing / Men\\u0027s T-Shirts","category_id":"127734143","attributes":[{"attribute_name":"Brand Name","attribute_value":"Anki"},{"attribute_name":"Brand Name","attribute_value":"Anki"}]},"basic_info":{"keywords":"Red 8GB mp3 for sports","product_image":[{"image_url":"https://sc04.alicdn.com/kf/Hafea40435f2f4354b81fb4e5476fc65cT.png"},{"image_url":"https://sc04.alicdn.com/kf/Hafea40435f2f4354b81fb4e5476fc65cT.png"}],"product_id":"1601464242677","description":"this is a sample description","language":"en_US","model_number":"BCD126748","title":"this is a sample title"},"trade_info":{"unit":"Piece","sku_info":[{"sku_price":{"price":"10.0","currency":"USD"},"sku_id":"5929192","sale_attributes":[{"attribute_name":"Color","attribute_value":"Red"},{"attribute_name":"Color","attribute_value":"Red"}],"inventory":"999","sku_code":"123456"},{"sku_price":{"price":"10.0","currency":"USD"},"sku_id":"5929192","sale_attributes":[{"attribute_name":"Color","attribute_value":"Red"},{"attribute_name":"Color","attribute_value":"Red"}],"inventory":"999","sku_code":"123456"}],"price":{"price_type":"TIERED","currency":"USD","tiered_price":[{"quantity":"1","price":"10.0"},{"quantity":"1","price":"10.0"}],"range_price":{"max_price":"10","min_price":"5"}},"inventory":"999","moq":"1"},"logistics_info":{"shipping_template_id":"2060478001","tiered_lead_time":[{"quantity":"1","lead_time":"5"},{"quantity":"1","lead_time":"5"}],"weight":"5.0","desi":"1","dimension":{"length":"10.0","width":"10.0","height":"10.0"}}}'
    
    request.add_api_param('product_info', product_info_json)
    
    # Execute the request
    response = client.execute(request, ACCESS_TOKEN)
    
    print("API Response:")
    print(f"Type: {response.type}")
    print(f"Body: {response.body}")
    
    return response


if __name__ == "__main__":
    print("Testing API call with exact documentation format...")
    print("=" * 60)
    
    try:
        response = test_api_call()
        print("\n" + "=" * 60)
        print("API call completed successfully!")
    except Exception as e:
        print(f"\nError: {e}")
        print("=" * 60)
