import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import re
import os
import json
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


PRODUCT_KEY_TO_COLUMN = {
    'product_Marque de voiture': 'Marque',
    'product_model': 'Modele',
    'product_Année': 'Mise_en_circulation',
    'product_Carburant': 'Energie',
    'product_Boîte de vitesse': 'Boite_vitesse',
    'product_Couleur': 'Couleur_exterieure',
    'product_Puissance fiscale': 'Puissance_fiscale',
    'product_Cylindrée': 'Cylindree',
    'product_Kilométrage': 'Kilometrage',
    'product_Etat': 'Etat_general',
    'product_Transmission': 'Transmission',
    'product_Carrosserie': 'Carrosserie',
    'product_Nombre de portes': 'Nombre_portes',
    'product_Nombre de places': 'Nombre_places',
    'product_Sellerie': 'Sellerie',
    'product_Couleur intérieure': 'Couleur_interieure',
    'product_Propriétaires': 'Proprietaires',
    'product_Puissance ch': 'Puissance_ch',
    'product_Puissance (ch)': 'Puissance_ch',
}


class CavaScraper:

    BASE_URL = "https://www.cava.tn"
    LISTING_URL = "https://www.cava.tn/category/voitures"
    REFERENCE_CSV = "automobile_tn_data.csv"
    OUTPUT_CSV = "cava_data.csv"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.5',
            'Connection': 'keep-alive',
        })
        self.data = []
        self.scraped_urls = set()
        self.consecutive_failures = 0
        self.required_columns = self._load_columns()

    def _load_columns(self):
        ref = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.REFERENCE_CSV)
        if os.path.exists(ref):
            cols = list(pd.read_csv(ref, nrows=0).columns)
            logger.info(f"Loaded {len(cols)} columns from {self.REFERENCE_CSV}")
            return cols
        logger.warning(f"{self.REFERENCE_CSV} not found, using default column order")
        return [
            'Title', 'Price', 'Marque', 'Modele', 'Kilometrage',
            'Mise_en_circulation', 'Energie', 'Boite_vitesse',
            'Puissance_fiscale', 'Puissance_ch', 'Transmission',
            'Carrosserie', 'Etat_general', 'Proprietaires', 'Gouvernorat',
            'Couleur_exterieure', 'Couleur_interieure', 'Sellerie',
            'Nombre_places', 'Nombre_portes', 'Cylindree',
            'Equipements', 'Date_annonce', 'URL',
        ]

    @staticmethod
    def clean_text(text):
        if not text:
            return None
        text = re.sub(r'\s+', ' ', text).strip()
        return text if text else None

    def get_page(self, url, max_retries=3):
        for attempt in range(max_retries):
            try:
                resp = self.session.get(url, timeout=15)
                if resp.status_code == 200:
                    return resp.text
                logger.warning(f"   HTTP {resp.status_code} for {url}")
            except requests.RequestException as e:
                logger.warning(f"   Request error (attempt {attempt+1}): {str(e)[:60]}")
            time.sleep(2 * (attempt + 1))
        self.consecutive_failures += 1
        return None

    def get_car_links(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if '/voitures/' in href and href != '/voitures/' and not href.endswith('/voitures'):
                if '/search?' in href or '/category/' in href:
                    continue
                full = href if href.startswith('http') else self.BASE_URL + href
                if full not in links and full != self.LISTING_URL:
                    links.append(full)
        return links

    def extract_json_data(self, html):
        match = re.search(r'"product-details\d+"\s*:\s*(\{.*?)\s*,\s*"lang-data"', html, re.DOTALL)
        if not match:
            return None
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            return None

    def extract_car_data(self, html, url):
        car = {}

        json_data = self.extract_json_data(html)
        if not json_data:
            return car

        if json_data.get('name'):
            car['Title'] = self.clean_text(str(json_data['name']))

        if json_data.get('price') is not None:
            car['Price'] = f"{int(json_data['price'])} DT"

        region = json_data.get('region')
        if region and isinstance(region, dict) and region.get('name'):
            car['Gouvernorat'] = region['name']

        if json_data.get('createdAt'):
            created = json_data['createdAt']
            date_match = re.match(r'(\d{4}-\d{2}-\d{2})', created)
            if date_match:
                car['Date_annonce'] = date_match.group(1)

        if json_data.get('description'):
            car['Equipements'] = self.clean_text(str(json_data['description']))

        for json_key, csv_col in PRODUCT_KEY_TO_COLUMN.items():
            val = json_data.get(json_key)
            if val is not None:
                car[csv_col] = self.clean_text(str(val))

        if 'Kilometrage' in car:
            car['Kilometrage'] = re.sub(r'[^\d]', '', car['Kilometrage'])
        if 'Mise_en_circulation' in car:
            val = car['Mise_en_circulation']
            if re.match(r'^\d{4}(\.0)?$', val):
                year = val.split('.')[0]
                car['Mise_en_circulation'] = f"01.{year}"
        if 'Puissance_fiscale' in car:
            car['Puissance_fiscale'] = re.sub(r'[^\d]', '', car['Puissance_fiscale'])
        if 'Nombre_portes' in car:
            car['Nombre_portes'] = re.sub(r'[^\d]', '', car['Nombre_portes'])
        if 'Boite_vitesse' in car:
            car['Boite_vitesse'] = re.sub(
                r'\b(?:de\s+)?vitesse\b', '', car['Boite_vitesse'],
                flags=re.IGNORECASE
            ).strip()

        car['URL'] = url
        return car

    def scrape_car(self, url):
        if url in self.scraped_urls:
            return True

        html = self.get_page(url)
        if not html:
            return False

        car = self.extract_car_data(html, url)
        field_count = len([v for v in car.values() if v is not None])

        if field_count >= 3:
            self.data.append(car)
            self.scraped_urls.add(url)
            title = car.get('Title', 'Unknown')
            logger.info(f"      {title[:45]} ({field_count} fields)")
            self.consecutive_failures = 0
            return True
        else:
            logger.warning(f"      Not enough data ({field_count} fields)")
            self.consecutive_failures += 1
            return False

    def scrape_all_pages(self):
        logger.info("\nStarting scraping from listing page...")

        page_num = 1
        empty_pages = 0

        while True:
            current_url = f"{self.LISTING_URL}?page={page_num}"
            logger.info(f"\nPage {page_num} - {current_url}")

            html = self.get_page(current_url)
            if not html:
                logger.error(f"   Failed to load page {page_num}")
                empty_pages += 1
                if empty_pages >= 3:
                    logger.info("   3 consecutive failures, stopping.")
                    break
                page_num += 1
                continue

            links = self.get_car_links(html)
            logger.info(f"   Found {len(links)} listings")

            if not links:
                empty_pages += 1
                if empty_pages >= 3:
                    logger.info("   3 consecutive empty pages, stopping.")
                    break
                logger.warning("   No links found, trying next page...")
                page_num += 1
                continue

            empty_pages = 0

            for idx, car_url in enumerate(links, 1):
                logger.info(f"   [{idx}/{len(links)}] Scraping...")
                self.scrape_car(car_url)
                time.sleep(random.uniform(0.3, 0.8))

            page_num += 1
            time.sleep(random.uniform(1, 2))

    def save_data(self):
        if not self.data:
            logger.error("No data to save!")
            return False

        df = pd.DataFrame(self.data)

        for col in self.required_columns:
            if col not in df.columns:
                df[col] = None

        df = df[self.required_columns]
        df.to_csv(self.OUTPUT_CSV, index=False, encoding='utf-8-sig')

        logger.info(f"\n{'='*70}")
        logger.info("SCRAPING COMPLETE")
        logger.info(f"{'='*70}")
        logger.info(f"Cars scraped: {len(df)}")
        logger.info(f"Columns: {list(df.columns)}")
        logger.info(f"Output file: {self.OUTPUT_CSV}")
        logger.info(f"{'='*70}\n")
        return True

    def run(self):
        logger.info("\n" + "="*70)
        logger.info("CAVA.TN SCRAPER")
        logger.info("="*70 + "\n")

        try:
            self.scrape_all_pages()
            self.save_data()
        except KeyboardInterrupt:
            logger.info("\nInterrupted! Saving collected data...")
            self.save_data()


def main():
    scraper = CavaScraper()
    scraper.run()


if __name__ == "__main__":
    main()
