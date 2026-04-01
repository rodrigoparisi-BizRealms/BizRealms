#!/usr/bin/env python3
"""
Simple debug test for Business Empire API
"""

import requests
import json

BASE_URL = "https://career-mogul-1.preview.emergentagent.com/api"

def test_login():
    data = {
        'email': 'test_jobs@businessempire.com',
        'password': 'test123'
    }
    
    print("Testing login...")
    try:
        response = requests.post(f'{BASE_URL}/auth/login', 
                               json=data, 
                               headers={'Content-Type': 'application/json'}, 
                               timeout=30)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            token = data.get('token', '')
            print(f"Login successful! Token: {token[:50]}...")
            return token
        else:
            print(f"Login failed: {response.text}")
            return None
    except Exception as e:
        print(f"Exception during login: {e}")
        return None

def test_jobs(token):
    print("\nTesting jobs endpoint...")
    try:
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        response = requests.get(f'{BASE_URL}/jobs', headers=headers, timeout=30)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            jobs = response.json()
            print(f"Jobs retrieved: {len(jobs)}")
            
            # Check for ObjectId issues
            for job in jobs:
                if '_id' in job:
                    print("❌ CRITICAL: ObjectId found in job response!")
                    return False
            print("✅ No ObjectId serialization issues found")
            return True
        else:
            print(f"Jobs request failed: {response.text}")
            return False
    except Exception as e:
        print(f"Exception during jobs test: {e}")
        return False

def test_job_apply(token):
    print("\nTesting job apply endpoint...")
    try:
        # First get jobs
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        response = requests.get(f'{BASE_URL}/jobs', headers=headers, timeout=30)
        if response.status_code != 200:
            print("Could not get jobs list")
            return False
        
        jobs = response.json()
        if not jobs:
            print("No jobs available")
            return False
        
        # Find Estagiário job or use first job
        target_job = None
        for job in jobs:
            if "Estagiário" in job.get('title', ''):
                target_job = job
                break
        
        if not target_job:
            target_job = jobs[0]
        
        print(f"Applying to: {target_job['title']}")
        
        apply_data = {"job_id": target_job['id']}
        response = requests.post(f'{BASE_URL}/jobs/apply', 
                               json=apply_data, 
                               headers=headers, 
                               timeout=30)
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Application successful! Status: {data.get('status')}, Match: {data.get('match_score')}%")
            
            # Check for ObjectId issues
            if 'job' in data and '_id' in data['job']:
                print("❌ CRITICAL: ObjectId found in job apply response!")
                return False
            print("✅ No ObjectId serialization issues found")
            return True
        else:
            print(f"Job apply failed: {response.text}")
            return False
    except Exception as e:
        print(f"Exception during job apply test: {e}")
        return False

def main():
    print("=" * 50)
    print("BUSINESS EMPIRE API DEBUG TEST")
    print("=" * 50)
    
    # Test login
    token = test_login()
    if not token:
        print("❌ Login failed, cannot continue")
        return False
    
    # Test jobs endpoint
    if not test_jobs(token):
        print("❌ Jobs test failed")
        return False
    
    # Test job apply
    if not test_job_apply(token):
        print("❌ Job apply test failed")
        return False
    
    print("\n" + "=" * 50)
    print("✅ ALL CRITICAL TESTS PASSED!")
    print("✅ ObjectId serialization bug appears to be FIXED!")
    print("=" * 50)
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)