"""BizRealms - Shared configuration and constants."""
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB
MONGO_URL = os.environ['MONGO_URL']
DB_NAME = os.environ['DB_NAME']

# JWT
JWT_SECRET = os.getenv('JWT_SECRET', 'your-super-secret-jwt-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_DAYS = 30

# Stripe
import stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

# Apple
APPLE_BUNDLE_ID = os.getenv('APPLE_BUNDLE_ID', 'com.bizrealms.app')
