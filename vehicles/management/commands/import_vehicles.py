# COMPLETE NEW FILE: vehicles/management/commands/import_vehicles.py
# Uses WordPress JSON API with local image downloading

from django.core.management.base import BaseCommand
from vehicles.models import Vehicle
import requests
import re
import os
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import uuid
from urllib.parse import urlparse
import time
from bs4 import BeautifulSoup


# ─── helpers ──────────────────────────────────────────────────
def get_text(field, fallback=''):
    """
    Accept WordPress field that is either a dict {'rendered': '…'}
    or already a string, and always return plain text.
    """
    if isinstance(field, dict):
        return field.get('rendered', fallback)
    return str(field) if field else fallback


def get_list(field):
    """Return a list even if field is None or scalar."""
    return field if isinstance(field, (list, tuple)) else []


# ───────────────────────────────────────────────────────────────

class Command(BaseCommand):
    help = 'Import vehicles from Richmonds JSON API with local image storage'

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
            response.raise_for_status()
            vehicles_data = response.json()

            self.stdout.write(f"Found {len(vehicles_data)} vehicles in API")

            for vehicle_data in vehicles_data:
                self.process_vehicle(vehicle_data)
                # Small delay to be respectful
                time.sleep(0.5)

        except requests.RequestException as e:
            self.stderr.write(f"Failed to fetch API data: {e}")
            return
        except Exception as e:
            self.stderr.write(f"Error processing API data: {e}")
            return

        self.stdout.write(self.style.SUCCESS("All vehicles imported with local images!"))

    def process_vehicle(self, api_data):
        """
        Process a single vehicle from the JSON API data.

        Args:
            api_data: Dictionary containing vehicle data from WordPress API
        """
        try:
            # Extract basic info from API response
            title = get_text(api_data.get('title'))
            vehicle_link = str(api_data.get('link', ''))

            # Parse year from title (e.g. "2021 Mercedes Benz X167 GLS 400d...")
            year_match = re.match(r'^(\d{4})\s+', title)
            year = int(year_match.group(1)) if year_match else 0

            # Get featured image from API response
            featured_media_id = api_data.get('featured_media', 0)
            image_url = self.get_featured_image_url(featured_media_id)

            # Check if this is a "for sale" vehicle (not "under offer" or "sold")
            portfolio_types = get_list(api_data.get('portfolio-type'))
            # From the JSON, 18 = "cars-for-sale", 20 = "under-offer"
            is_for_sale = 18 in portfolio_types

            if not is_for_sale:
                self.stdout.write(f"Skipping {title} - not for sale")
                return

            # Now we need to scrape the individual vehicle page for detailed specs
            vehicle_details = self.scrape_vehicle_details(vehicle_link)

            if not vehicle_details:
                self.stdout.write(f"Could not get details for {title}")
                return

            # Download and store image locally
            local_image_url = None
            if image_url:
                local_image_url = self.download_image(image_url, {
                    'make': vehicle_details.get('make', 'unknown'),
                    'model': vehicle_details.get('model', 'unknown'),
                    'year': year
                })

            # Prepare final vehicle data
            vehicle_data = {
                'make': vehicle_details.get('make', ''),
                'model': vehicle_details.get('model', ''),
                'year': year,
                'km': vehicle_details.get('km', 0),
                'engine_size': vehicle_details.get('engine_size', 0),
                'transmission': vehicle_details.get('transmission', ''),
                'price': vehicle_details.get('price', 0),
                'photo_link': local_image_url or image_url or '',  # Use local first, fallback to original
                'link': vehicle_link,
                'description': vehicle_details.get('description', ''),
                'is_active': True,
            }

            # Update or create the Vehicle
            vehicle, created = Vehicle.objects.update_or_create(
                link=vehicle_link,
                defaults=vehicle_data
            )

            action = 'Created' if created else 'Updated'
            image_status = '(with local image)' if local_image_url else '(original image URL)'
            self.stdout.write(f"{action}: {year} {vehicle_data['make']} {vehicle_data['model']} {image_status}")

        except Exception as e:
            self.stderr.write(f"Error processing vehicle {api_data.get('title', {}).get('rendered', 'unknown')}: {e}")

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

        except Exception as e:
            self.stderr.write(f"Failed to get image for media ID {media_id}: {e}")

        return None

    def scrape_vehicle_details(self, vehicle_url):
        """
        Scrape detailed vehicle specifications from individual vehicle page.

        Args:
            vehicle_url: URL to individual vehicle page

        Returns:
            dict: Vehicle details including make, model, km, price, etc.
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }

            response = requests.get(vehicle_url, headers=headers, timeout=30)
            if response.status_code != 200:
                return None

            soup = BeautifulSoup(response.content, 'html.parser')

            # Look for the vehicle details table (same as before)
            postclass_div = soup.select_one('div.postclass')
            if not postclass_div:
                return None

            table = postclass_div.find('table')
            if not table:
                return None

            # Default values
            details = {
                'make': '',
                'model': '',
                'km': 0,
                'engine_size': 0,
                'transmission': '',
                'price': 0,
                'description': '',
            }

            # Parse table rows for vehicle specs
            for tr in table.find_all('tr'):
                tds = tr.find_all('td')
                if len(tds) != 2:
                    continue

                label = tds[0].get_text(strip=True).replace(':', '').lower()
                value = tds[1].get_text(strip=True)

                if label == 'make':
                    details['make'] = value
                elif label == 'model':
                    details['model'] = value
                elif label == 'built':
                    try:
                        details['year'] = int(value)
                    except ValueError:
                        pass
                elif label == 'km':
                    try:
                        details['km'] = int(value.replace(',', '').replace('km', '').strip())
                    except ValueError:
                        details['km'] = 0
                elif label == 'engine size':
                    try:
                        details['engine_size'] = int(re.sub(r'[^\d]', '', value))
                    except ValueError:
                        details['engine_size'] = 0
                elif label == 'transmission':
                    details['transmission'] = value
                elif label == 'price':
                    try:
                        details['price'] = int(re.sub(r'[^\d]', '', value))
                    except ValueError:
                        details['price'] = 0

            # Extract description (between HR tags as before)
            hrs = postclass_div.find_all('hr')
            if len(hrs) >= 2:
                start_hr, end_hr = hrs[0], hrs[1]
                paragraphs = []
                current = start_hr.next_sibling
                count = 0

                while current and current != end_hr and count < 3:
                    if hasattr(current, 'name') and current.name == 'p':
                        text = current.get_text(strip=True)
                        if text:
                            paragraphs.append(text)
                            count += 1
                    current = current.next_sibling

                details['description'] = "\n\n".join(paragraphs)

            return details

        except Exception as e:
            self.stderr.write(f"Error scraping {vehicle_url}: {e}")
            return None

    def download_image(self, image_url, vehicle_info):
        """
        Download image from external URL and store locally in media folder.

        Args:
            image_url: URL of the image to download
            vehicle_info: Dict containing vehicle info for filename

        Returns:
            str: Local URL path to the downloaded image, or None if failed
        """
        if not image_url:
            return None

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://richmonds.com.au/',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
            }

            response = requests.get(image_url, headers=headers, timeout=30)
            if response.status_code != 200:
                self.stderr.write(f"Failed to download image: {image_url} - Status: {response.status_code}")
                return None

            # Get file extension from URL
            parsed_url = urlparse(image_url)
            file_extension = os.path.splitext(parsed_url.path)[1]
            if not file_extension:
                file_extension = '.jpg'

            # Generate safe filename
            safe_make = re.sub(r'[^\w\-_]', '', vehicle_info.get('make', 'unknown'))
            safe_model = re.sub(r'[^\w\-_]', '', vehicle_info.get('model', 'unknown'))
            year = vehicle_info.get('year', 'unknown')
            unique_id = uuid.uuid4().hex[:8]

            filename = f"vehicles/{year}_{safe_make}_{safe_model}_{unique_id}{file_extension}"

            # Save to Django media storage
            file_path = default_storage.save(filename, ContentFile(response.content))

            # Return the full URL that can be used in templates
            local_url = default_storage.url(file_path)

            self.stdout.write(f"  ✓ Downloaded image: {filename}")
            return local_url

        except requests.RequestException as e:
            self.stderr.write(f"Network error downloading image {image_url}: {str(e)}")
            return None
        except Exception as e:
            self.stderr.write(f"Error downloading image {image_url}: {str(e)}")
            return None