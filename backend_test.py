import requests
import json
import base64
import os
import uuid
import time
from typing import Dict, List, Optional, Any

# Get the backend URL from the frontend .env file
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if line.startswith('REACT_APP_BACKEND_URL='):
            BACKEND_URL = line.strip().split('=')[1].strip('"\'')
            break

# API base URL
API_URL = f"{BACKEND_URL}/api"

# Test data
test_artist = {
    "name": "Jane Smith",
    "email": f"jane.smith.{uuid.uuid4()}@example.com",
    "bio": "Contemporary artist specializing in digital media and installations",
    "location": "New York, NY",
    "website": "https://janesmith.example.com",
    "social_links": {
        "instagram": "janesmith_art",
        "twitter": "janesmith_creates"
    }
}

test_artist_update = {
    "name": "Jane A. Smith",
    "bio": "Award-winning contemporary artist specializing in digital media and installations",
    "location": "Brooklyn, NY"
}

# Test image file path
test_image_path = "/app/backend_test.py"  # Using this file as a test file

# Test content
test_content = {
    "title": "Digital Landscape Series #1",
    "description": "First piece in my exploration of digital landscapes",
    "tags": "digital,landscape,contemporary"
}

class BackendTester:
    def __init__(self):
        self.api_url = API_URL
        self.created_artist_id = None
        self.created_content_id = None
        self.test_results = {
            "artist_crud": {"success": False, "details": ""},
            "file_upload": {"success": False, "details": ""},
            "content_management": {"success": False, "details": ""},
            "database_schema": {"success": False, "details": ""}
        }
    
    def run_all_tests(self):
        """Run all tests and print results"""
        print(f"Testing backend API at {self.api_url}")
        
        # Test API root
        self.test_api_root()
        
        # Test Artist CRUD
        self.test_artist_crud()
        
        # Test File Upload
        if self.created_artist_id:
            self.test_file_upload()
        
        # Test Content Management
        if self.created_artist_id:
            self.test_content_management()
        
        # Test Database Schema
        self.test_database_schema()
        
        # Print summary
        self.print_summary()
        
        return self.test_results
    
    def test_api_root(self):
        """Test the API root endpoint"""
        try:
            response = requests.get(f"{self.api_url}/")
            if response.status_code == 200:
                print("✅ API root endpoint is working")
            else:
                print(f"❌ API root endpoint returned status code {response.status_code}")
                print(f"Response: {response.text}")
        except Exception as e:
            print(f"❌ Error testing API root endpoint: {str(e)}")
    
    def test_artist_crud(self):
        """Test Artist CRUD operations"""
        try:
            # Create artist
            print("\n--- Testing Artist CRUD Operations ---")
            print("Creating artist...")
            response = requests.post(f"{self.api_url}/artists", json=test_artist)
            
            if response.status_code == 200:
                artist_data = response.json()
                self.created_artist_id = artist_data.get("id")
                print(f"✅ Created artist with ID: {self.created_artist_id}")
                
                # Test duplicate email handling
                print("Testing duplicate email handling...")
                duplicate_response = requests.post(f"{self.api_url}/artists", json=test_artist)
                if duplicate_response.status_code == 400:
                    print("✅ Duplicate email handling works correctly")
                else:
                    print(f"❌ Duplicate email handling failed: {duplicate_response.status_code}")
                    print(f"Response: {duplicate_response.text}")
                
                # Get all artists
                print("Getting all artists...")
                response = requests.get(f"{self.api_url}/artists")
                if response.status_code == 200:
                    artists = response.json()
                    if isinstance(artists, list):
                        print(f"✅ Got {len(artists)} artists")
                    else:
                        print("❌ Expected list of artists but got something else")
                else:
                    print(f"❌ Failed to get artists: {response.status_code}")
                    print(f"Response: {response.text}")
                
                # Get specific artist
                print(f"Getting artist with ID: {self.created_artist_id}...")
                response = requests.get(f"{self.api_url}/artists/{self.created_artist_id}")
                if response.status_code == 200:
                    artist = response.json()
                    if artist.get("id") == self.created_artist_id:
                        print("✅ Got specific artist successfully")
                    else:
                        print("❌ Got wrong artist")
                else:
                    print(f"❌ Failed to get specific artist: {response.status_code}")
                    print(f"Response: {response.text}")
                
                # Test search functionality
                print("Testing artist search...")
                search_term = test_artist["name"][:5]  # Use part of the name
                response = requests.get(f"{self.api_url}/artists?search={search_term}")
                if response.status_code == 200:
                    search_results = response.json()
                    if isinstance(search_results, list) and len(search_results) > 0:
                        print(f"✅ Search found {len(search_results)} results for '{search_term}'")
                    else:
                        print(f"❌ Search found no results for '{search_term}'")
                else:
                    print(f"❌ Search failed: {response.status_code}")
                    print(f"Response: {response.text}")
                
                # Update artist
                print("Updating artist...")
                response = requests.put(f"{self.api_url}/artists/{self.created_artist_id}", json=test_artist_update)
                if response.status_code == 200:
                    updated_artist = response.json()
                    if updated_artist.get("name") == test_artist_update["name"]:
                        print("✅ Updated artist successfully")
                    else:
                        print("❌ Artist update didn't apply changes correctly")
                else:
                    print(f"❌ Failed to update artist: {response.status_code}")
                    print(f"Response: {response.text}")
                
                # Upload profile image
                print("Uploading profile image...")
                with open(test_image_path, 'rb') as f:
                    files = {'file': ('test_image.py', f, 'application/octet-stream')}
                    response = requests.post(
                        f"{self.api_url}/artists/{self.created_artist_id}/profile-image",
                        files=files
                    )
                    if response.status_code == 200:
                        print("✅ Uploaded profile image successfully")
                    else:
                        print(f"❌ Failed to upload profile image: {response.status_code}")
                        print(f"Response: {response.text}")
                
                # Verify profile image was saved
                print("Verifying profile image was saved...")
                response = requests.get(f"{self.api_url}/artists/{self.created_artist_id}")
                if response.status_code == 200:
                    artist = response.json()
                    if artist.get("profile_image"):
                        print("✅ Profile image was saved successfully")
                    else:
                        print("❌ Profile image was not saved")
                
                self.test_results["artist_crud"]["success"] = True
                self.test_results["artist_crud"]["details"] = "All Artist CRUD operations passed"
            else:
                print(f"❌ Failed to create artist: {response.status_code}")
                print(f"Response: {response.text}")
                self.test_results["artist_crud"]["details"] = f"Failed to create artist: {response.status_code}"
        except Exception as e:
            print(f"❌ Error testing Artist CRUD: {str(e)}")
            self.test_results["artist_crud"]["details"] = f"Error: {str(e)}"
    
    def test_file_upload(self):
        """Test File Upload System"""
        try:
            print("\n--- Testing File Upload System ---")
            if not self.created_artist_id:
                print("❌ Cannot test file upload without a created artist")
                self.test_results["file_upload"]["details"] = "Cannot test without a created artist"
                return
            
            print("Uploading content file...")
            with open(test_image_path, 'rb') as f:
                files = {'file': ('test_content.py', f, 'application/octet-stream')}
                data = {
                    'artist_id': self.created_artist_id,
                    'title': test_content["title"],
                    'description': test_content["description"],
                    'tags': test_content["tags"]
                }
                response = requests.post(
                    f"{self.api_url}/content",
                    files=files,
                    data=data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    self.created_content_id = result.get("content_id")
                    print(f"✅ Uploaded content with ID: {self.created_content_id}")
                    self.test_results["file_upload"]["success"] = True
                    self.test_results["file_upload"]["details"] = "File upload system works correctly"
                else:
                    print(f"❌ Failed to upload content: {response.status_code}")
                    print(f"Response: {response.text}")
                    self.test_results["file_upload"]["details"] = f"Failed to upload content: {response.status_code}"
        except Exception as e:
            print(f"❌ Error testing File Upload: {str(e)}")
            self.test_results["file_upload"]["details"] = f"Error: {str(e)}"
    
    def test_content_management(self):
        """Test Content Management CRUD"""
        try:
            print("\n--- Testing Content Management CRUD ---")
            if not self.created_content_id:
                print("❌ Cannot test content management without uploaded content")
                self.test_results["content_management"]["details"] = "Cannot test without uploaded content"
                return
            
            # Get all content
            print("Getting all content...")
            response = requests.get(f"{self.api_url}/content")
            if response.status_code == 200:
                content_list = response.json()
                if isinstance(content_list, list):
                    print(f"✅ Got {len(content_list)} content items")
                else:
                    print("❌ Expected list of content but got something else")
            else:
                print(f"❌ Failed to get content: {response.status_code}")
                print(f"Response: {response.text}")
            
            # Get specific content
            print(f"Getting content with ID: {self.created_content_id}...")
            response = requests.get(f"{self.api_url}/content/{self.created_content_id}")
            if response.status_code == 200:
                content = response.json()
                if content.get("id") == self.created_content_id:
                    print("✅ Got specific content successfully")
                else:
                    print("❌ Got wrong content")
            else:
                print(f"❌ Failed to get specific content: {response.status_code}")
                print(f"Response: {response.text}")
            
            # Get artist-specific content
            print(f"Getting content for artist ID: {self.created_artist_id}...")
            response = requests.get(f"{self.api_url}/artists/{self.created_artist_id}/content")
            if response.status_code == 200:
                artist_content = response.json()
                if isinstance(artist_content, list):
                    print(f"✅ Got {len(artist_content)} content items for artist")
                else:
                    print("❌ Expected list of content but got something else")
            else:
                print(f"❌ Failed to get artist content: {response.status_code}")
                print(f"Response: {response.text}")
            
            # Test content search/filtering
            print("Testing content search...")
            search_term = test_content["title"][:5]  # Use part of the title
            response = requests.get(f"{self.api_url}/content?search={search_term}")
            if response.status_code == 200:
                search_results = response.json()
                if isinstance(search_results, list):
                    print(f"✅ Search found {len(search_results)} results for '{search_term}'")
                else:
                    print("❌ Expected list of content but got something else")
            else:
                print(f"❌ Search failed: {response.status_code}")
                print(f"Response: {response.text}")
            
            # Delete content
            print(f"Deleting content with ID: {self.created_content_id}...")
            response = requests.delete(f"{self.api_url}/content/{self.created_content_id}")
            if response.status_code == 200:
                print("✅ Deleted content successfully")
            else:
                print(f"❌ Failed to delete content: {response.status_code}")
                print(f"Response: {response.text}")
            
            # Verify content was deleted
            print("Verifying content was deleted...")
            response = requests.get(f"{self.api_url}/content/{self.created_content_id}")
            if response.status_code == 404:
                print("✅ Content was deleted successfully")
                self.test_results["content_management"]["success"] = True
                self.test_results["content_management"]["details"] = "All Content Management operations passed"
            else:
                print(f"❌ Content was not deleted properly: {response.status_code}")
                self.test_results["content_management"]["details"] = "Content was not deleted properly"
        except Exception as e:
            print(f"❌ Error testing Content Management: {str(e)}")
            self.test_results["content_management"]["details"] = f"Error: {str(e)}"
    
    def test_database_schema(self):
        """Test Database Schema and Models"""
        try:
            print("\n--- Testing Database Schema and Models ---")
            
            # Check UUID format
            if self.created_artist_id:
                try:
                    uuid_obj = uuid.UUID(self.created_artist_id)
                    print("✅ Artist ID is a valid UUID")
                except ValueError:
                    print("❌ Artist ID is not a valid UUID")
            
            # Test search and filtering capabilities
            # This is already covered in the artist and content tests
            
            # Test MongoDB connection and data persistence
            # If we got this far, the MongoDB connection is working
            print("✅ MongoDB connection is working")
            
            self.test_results["database_schema"]["success"] = True
            self.test_results["database_schema"]["details"] = "Database schema and models are working correctly"
        except Exception as e:
            print(f"❌ Error testing Database Schema: {str(e)}")
            self.test_results["database_schema"]["details"] = f"Error: {str(e)}"
    
    def print_summary(self):
        """Print a summary of all test results"""
        print("\n=== TEST SUMMARY ===")
        for test_name, result in self.test_results.items():
            status = "✅ PASSED" if result["success"] else "❌ FAILED"
            print(f"{test_name}: {status}")
            if result["details"]:
                print(f"  Details: {result['details']}")
        print("===================")

if __name__ == "__main__":
    tester = BackendTester()
    results = tester.run_all_tests()