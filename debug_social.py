#!/usr/bin/env python3
"""
Debug the social auth without email issue
"""

import requests
import json

BACKEND_URL = "https://career-mogul-1.preview.emergentagent.com/api"

def debug_social_auth_no_email():
    """Debug the social auth without email scenario"""
    
    response = requests.post(f"{BACKEND_URL}/auth/social", json={
        "provider": "google",
        "token": "no_email_token",
        "name": "No Email User"
    })
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    try:
        data = response.json()
        print(f"JSON Response: {data}")
    except:
        print("Could not parse JSON response")

if __name__ == "__main__":
    debug_social_auth_no_email()