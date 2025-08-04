from django.core.management.base import BaseCommand
from vehicles.models import Vehicle
from bs4 import BeautifulSoup, Tag
import requests
import re

class Command(BaseCommand):
    help = 'Import all vehicles and their details from Richmonds'

    def handle(self, *args, **options):
        main_url = 'https://richmonds.com.au/cars-for-sale/'
        self.stdout.write("Fetching cars list...")
        resp = requests.get(main_url)
        if resp.status_code != 200:
            self.stderr.write(f"Failed list: {resp.status_code}")
            return

        # Find each car on the main listing page
        soup = BeautifulSoup(resp.content, 'html.parser')
        portfolio_items = soup.select('div.portfolio_item')
        self.stdout.write(f"Found {len(portfolio_items)} cars")

        for item in portfolio_items:
            link_a = item.select_one('.imghoverclass a')
            if not link_a:
                continue

            car_link = link_a['href']
            title = link_a.get('title') or link_a.text.strip()
            # Note: car_link should be unique in DB
            img_tag = link_a.find('img')
            photo_link = img_tag['data-src'] if img_tag and 'data-src' in img_tag.attrs else ""

            # Attempt to parse "year" from the title (e.g. "2010 BMW E89 Z4 sDrive 35is Roadster (MY11) – DCT")
            year_match = re.match(r'^(\d{4})\s+', title)
            year = int(year_match.group(1)) if year_match else None

            # Now fetch the car detail page
            car_resp = requests.get(car_link)
            if car_resp.status_code != 200:
                self.stderr.write(f"Failed to load car {car_link}: {car_resp.status_code}")
                continue

            car_soup = BeautifulSoup(car_resp.content, 'html.parser')
            postclass_div = car_soup.select_one('div.postclass')
            if not postclass_div:
                self.stderr.write(f"No vehicle details found at {car_link}")
                continue

            if postclass_div:
                # Find the first <a> tag inside the postclass div
                a_tag = postclass_div.find('a')
                if a_tag and 'href' in a_tag.attrs:
                    photo_link = a_tag['href']


            table = postclass_div.find('table')
            if not table:
                self.stderr.write(f"No detail table found at {car_link}")
                continue

            # Default fields
            detail_data = {
                'make': '',
                'model': '',
                'year': year,
                'km': 0,
                'engine_size': 0,
                'transmission': '',
                'price': 0,
                'photo_link': photo_link,
                'link': car_link,
                'description': '',
                'is_active': True,
            }

            for tr in table.find_all('tr'):
                tds = tr.find_all('td')
                if len(tds) != 2:
                    continue
                label = tds[0].get_text(strip=True).replace(':', '').lower()
                value = tds[1].get_text(strip=True)

                if label == 'make':
                    detail_data['make'] = value
                elif label == 'model':
                    detail_data['model'] = value
                elif label == 'built' and year is None:
                    try:
                        detail_data['year'] = int(value)
                    except ValueError:
                        detail_data['year'] = 0
                elif label == 'km':
                    try:
                        detail_data['km'] = int(value.replace(',', '').replace('km', '').strip())
                    except ValueError:
                        detail_data['km'] = 0
                elif label == 'engine size':
                    # Example: '3000cc'
                    try:
                        detail_data['engine_size'] = int(re.sub(r'[^\d]', '', value))
                    except ValueError:
                        detail_data['engine_size'] = 0
                elif label == 'transmission':
                    detail_data['transmission'] = value
                elif label == 'price':
                    # Example: '$41,900'
                    detail_data['price'] = int(re.sub(r'[^\d]', '', value))

            # Parse 5 paragraphs of description
            # Find the two <hr> tags inside postclass_div
            hrs = postclass_div.find_all('hr')
            if len(hrs) < 2:
                description = ""  # Not enough <hr> tags found
            else:
                start_hr, end_hr = hrs[0], hrs[1]

                count = 0
                paragraphs = []
                current = start_hr.next_sibling

                while current and current != end_hr and count < 3:
                    if isinstance(current, Tag) and current.name == 'p':
                        paragraphs.append(current.get_text(strip=True))
                        count += 1
                    current = current.next_sibling

                # Join the first 5 paragraph texts into a single string (with newlines or spaces)
                description = "\n\n".join(paragraphs)
                detail_data['description'] = description

            # Update or create the Vehicle
            vehicle, created = Vehicle.objects.update_or_create(
                link=car_link,
                defaults=detail_data
            )
            self.stdout.write(f"{'Created' if created else 'Updated'}: {detail_data['year']} {detail_data['make']} {detail_data['model']}")

        self.stdout.write(self.style.SUCCESS("All vehicles imported!"))
