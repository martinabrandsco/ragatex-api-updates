# -*- coding: utf-8 -*-
"""
Configuration template for Alibaba.com Product Updater
Copy this file to config.py and update with your actual credentials
"""

# Alibaba.com API Configuration
APP_KEY = "501504"  # Your App Key
APP_SECRET = "VYO05f6i6FCMAlDD6GpT3x3BOdEv6Cqv"  # Replace with your actual App Secret
ACCESS_TOKEN = "50000202005YOdq5O1d982d9btzFodOHZGQykFZktseKtxSOP0z5pCqa1N38Rr"  # Your Access Token

# API Endpoints
BASE_URL = "https://openapi-api.alibaba.com/rest"
INVENTORY_UPDATE_API = "/icbu/product/edit-inventory"
PRICE_UPDATE_API = "/icbu/product/edit-price"  # Adjust if different

# Request settings
REQUEST_DELAY = 1  # Delay between requests in seconds (to avoid rate limiting)
MAX_RETRIES = 3  # Maximum number of retries for failed requests
