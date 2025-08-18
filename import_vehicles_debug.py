# DEBUG VERSION: vehicles/management/commands/import_vehicles.py
# This version will show exactly what the API is returning

from django.core.management.base import BaseCommand
from vehicles.models import Vehicle
import requests
import re
import os
import json
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import uuid
from urllib.parse import urlparse
import time
from bs4 import BeautifulSoup


class Command(BaseCommand):
    help = 'Import vehicles from Richmonds JSON API with local image storage (DEBUG VERSION)'

    def handle(self, *args, **options):
        # Use the JSON API endpoint you discovered
        api_url = 'https://richmonds.com.au/wp-json/wp/v2/portfolio?type=vehicle&per_page=100'
        
        self.stdout.write("Fetching vehicles from JSON API...")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
        try:
            response = requests.get(api_url, headers=headers, timeout=30)
            self.stdout.write(f"Response status: {response.status_code}")
            self.stdout.write(f"Response headers: {dict(response.headers)}")
            
            if response.status_code != 200:
                self.stderr.write(f"API returned status {response.status_code}")
                self.stderr.write(f"Response content: {response.text[:500]}...")
                return
            
            # Debug: Show raw response
            self.stdout.write(f"Raw response (first 500 chars): {response.text[:500]}")
            
            # Try to parse JSON
            try:
                vehicles_data = response.json()
                self.stdout.write(f"JSON parsed successfully. Type: {type(vehicles_data)}")
            except json.JSONDecodeError as e:
                self.stderr.write(f"Failed to parse JSON: {e}")
                self.stderr.write(f"Response content: {response.text[:1000]}")
                return
            
            # Debug: Show structure
            if isinstance(vehicles_data, list):
                self.stdout.write(f"Found {len(vehicles_data)} vehicles in API")
                if len(vehicles_data) > 0:
                    self.stdout.write(f"First vehicle type: {type(vehicles_data[0])}")
                    self.stdout.write(f"First vehicle keys: {list(vehicles_data[0].keys()) if isinstance(vehicles_data[0], dict) else 'Not a dict'}")
            elif isinstance(vehicles_data, dict):
                self.stdout.write(f"Response is a dict with keys: {list(vehicles_data.keys())}")
            else:
                self.stdout.write(f"Unexpected response type: {type(vehicles_data)}")
                return
            
            # Process each vehicle
            for i, vehicle_data in enumerate(vehicles_data):
                self.stdout.write(f"\n--- Processing vehicle {i+1} ---")
                self.stdout.write(f"Vehicle data type: {type(vehicle_data)}")
                
                if isinstance(vehicle_data, dict):
                    self.process_vehicle(vehicle_data)
                else:
                    self.stderr.write(f"Vehicle {i+1} is not a dict: {type(vehicle_data)}")
                    self.stderr.write(f"Content: {str(vehicle_data)[:200]}...")
                
                # Small delay to be respectful
                time.sleep(0.5)
                
        except requests.RequestException as e:
            self.stderr.write(f"Failed to fetch API data: {e}")
            return
        except Exception as e:
            self.stderr.write(f"Error processing API data: {e}")
            import traceback
            traceback.print_exc()
            return

        self.stdout.write(self.style.SUCCESS("Debugging complete!"))

    def process_vehicle(self, api_data):
        """
        Process a single vehicle from the JSON API data.
        
        Args:
            api_data: Dictionary containing vehicle data from WordPress API
        """
        try:
            self.stdout.write(f"Processing vehicle with keys: {list(api_data.keys())}")
            
            # Extract basic info from API response
            title_data = api_data.get('title', {})
            self.stdout.write(f"Title data: {title_data}")
            
            if isinstance(title_data, dict):
                title = title_data.get('rendered', '')
            else:
                title = str(title_data) if title_data else ''
                
            self.stdout.write(f"Extracted title: {title}")
            
            vehicle_link = api_data.get('link', '')
            self.stdout.write(f"Vehicle link: {vehicle_link}")
            
            # Parse year from title (e.g. "2021 Mercedes Benz X167 GLS 400d...")
            year_match = re.match(r'^(\d{4})\s+', title)
            year = int(year_match.group(1)) if year_match else 0
            self.stdout.write(f"Parsed year: {year}")
            
            # Get featured image from API response
            featured_media_id = api_data.get('featured_media', 0)
            self.stdout.write(f"Featured media ID: {featured_media_id}")
            
            # Check portfolio type
            portfolio_types = api_data.get('portfolio-type', [])
            self.stdout.write(f"Portfolio types: {portfolio_types}")
            
            # From the JSON, 18 = "cars-for-sale", 20 = "under-offer"
            is_for_sale = 18 in portfolio_types
            self.stdout.write(f"Is for sale: {is_for_sale}")
            
            if not is_for_sale:
                self.stdout.write(f"Skipping {title} - not for sale")
                return
            
            # Get featured image URL
            image_url = self.get_featured_image_url(featured_media_id)
            self.stdout.write(f"Image URL: {image_url}")
            
            # For debugging, let's not scrape the details page yet
            # Just show what we have so far
            self.stdout.write(f"SUCCESS: Would process {title} from {year}")
            
        except Exception as e:
            self.stderr.write(f"Error processing vehicle: {e}")
            import traceback
            traceback.print_exc()

    def get_featured_image_url(self, media_id):
        """
        Get the featured image URL from WordPress media API.
        
        Args:
            media_id: WordPress media ID
            
        Returns:
            str: Image URL or None if not found
        """
        if not media_id:
            return None
            
        try:
            media_api_url = f'https://richmonds.com.au/wp-json/wp/v2/media/{media_id}'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
            }
            
            response = requests.get(media_api_url, headers=headers, timeout=10)
            if response.status_code == 200:
                media_data = response.json()
                return media_data.get('source_url', '')
            else:
                self.stdout.write(f"Media API returned status {response.status_code} for ID {media_id}")
                
        except Exception as e:
            self.stderr.write(f"Failed to get image for media ID {media_id}: {e}")
            
        return None