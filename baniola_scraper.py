import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import re
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


LABEL_TO_COLUMN = {
    'marque': 'Marque',
    'modèle': 'Modele',
    'modele': 'Modele',
    'année': 'Mise_en_circulation',
    'annee': 'Mise_en_circulation',
    'kilométrage': 'Kilometrage',
    'kilometrage': 'Kilometrage',
    'carburant': 'Energie',
    'motorisation': 'Energie',
    'énergie': 'Energie',
    'energie': 'Energie',
    'boîte vitesse': 'Boite_vitesse',
    'boite vitesse': 'Boite_vitesse',
    'boîte': 'Boite_vitesse',
    'boite': 'Boite_vitesse',
    'puissance fiscale': 'Puissance_fiscale',
    'puissance (ch)': 'Puissance_ch',
    'puissance ch': 'Puissance_ch',
    'transmission': 'Transmission',
    'carrosserie': 'Carrosserie',
    'état général': 'Etat_general',
    'etat général': 'Etat_general',
    'etat general': 'Etat_general',
    'état general': 'Etat_general',
    'propriétaires': 'Proprietaires',
    'proprietaires': 'Proprietaires',
    'propriétaire': 'Proprietaires',
    'gouvernorat': 'Gouvernorat',
    'région': 'Gouvernorat',
    'region': 'Gouvernorat',
    'couleur extérieure': 'Couleur_exterieure',
    'couleur exterieure': 'Couleur_exterieure',
    'couleur / extérieur': 'Couleur_exterieure',
    'couleur / exterieur': 'Couleur_exterieure',
    'couleur intérieure': 'Couleur_interieure',
    'couleur interieure': 'Couleur_interieure',
    'couleur / intérieur': 'Couleur_interieure',
    'couleur / interieur': 'Couleur_interieure',
    'sellerie': 'Sellerie',
    'nombre de places': 'Nombre_places',
    'nombre places': 'Nombre_places',
    'nombre de portes': 'Nombre_portes',
    'nombre portes': 'Nombre_portes',
    'cylindrée': 'Cylindree',
    'cylindree': 'Cylindree',
}


class BaniolaScraper:

    BASE_URL = "https://baniola.tn"
    LISTING_URL = "https://baniola.tn/voitures"
    REFERENCE_CSV = "automobile_tn_data.csv"
    OUTPUT_CSV = "baniola_data.csv"

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
            if '/details/' in href and href.endswith('.html'):
                full = href if href.startswith('http') else self.BASE_URL + href
                if full not in links:
                    links.append(full)
        return links

    def get_next_page_url(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        for a in soup.find_all('a', href=True):
            text = a.get_text(strip=True).lower()
            if text in ('suivant', 'next', '›', '»', '>>'):
                href = a['href']
                return href if href.startswith('http') else self.BASE_URL + href
        return None

    def _parse_characteristics(self, soup):
        parsed = {}
        char_heading = soup.find(
            lambda tag: tag.name in ('h2', 'h3', 'h4', 'strong', 'b')
            and 'caract' in (tag.get_text(strip=True).lower())
        )
        if not char_heading:
            return parsed

        container = char_heading.find_parent(['div', 'section'])
        if not container:
            return parsed

        pairs = []
        for dt, dd in zip(container.find_all('dt'), container.find_all('dd')):
            pairs.append((dt.get_text(strip=True), dd.get_text(strip=True)))

        for row in container.find_all('tr'):
            cells = row.find_all(['th', 'td'])
            if len(cells) == 2:
                pairs.append((cells[0].get_text(strip=True), cells[1].get_text(strip=True)))

        if not pairs:
            text = container.get_text(' ', strip=True)
            tokens = []
            for label in LABEL_TO_COLUMN:
                pattern = re.compile(re.escape(label), re.IGNORECASE)
                for m in pattern.finditer(text):
                    tokens.append((m.start(), m.end(), label))
            tokens.sort(key=lambda x: x[0])

            for i, (start, end, label) in enumerate(tokens):
                val_end = tokens[i + 1][0] if i + 1 < len(tokens) else len(text)
                val = text[end:val_end].strip()
                val = re.sub(r'\s*(km|cv|ch|cm[³3]?|cc)\s*$', '', val, flags=re.IGNORECASE).strip()
                if val:
                    pairs.append((label, val))

        for label, value in pairs:
            normalized = label.lower().strip()
            col = LABEL_TO_COLUMN.get(normalized)
            if not col:
                for key, col_name in LABEL_TO_COLUMN.items():
                    if key in normalized or normalized in key:
                        col = col_name
                        break
            if col and value:
                clean_val = self.clean_text(value)
                if clean_val:
                    parsed[col] = clean_val

        return parsed

    def extract_car_data(self, html, url):
        soup = BeautifulSoup(html, 'html.parser')
        car = {}

        h1 = soup.find('h1')
        if h1:
            car['Title'] = self.clean_text(h1.get_text())

        page_text = soup.get_text(' ', strip=True)
        price_match = re.search(r'(\d[\d\s]*)\s*TND', page_text)
        if not price_match:
            price_match = re.search(r'(\d[\d\s]*)\s*DT', page_text)
        if price_match:
            price_val = price_match.group(1).replace(' ', '')
            car['Price'] = f"{price_val} DT"

        loc_match = re.search(
            r'([A-Za-zÀ-ÿ\s]+),\s*[A-Za-zÀ-ÿ\s]+?\s*Publi[ée]\s*le',
            page_text
        )
        if loc_match:
            car['Gouvernorat'] = self.clean_text(loc_match.group(1))

        date_match = re.search(r'Publi[ée]\s*le\s*[:\s]*(\d{1,2}/\d{1,2}/\d{4})', page_text)
        if date_match:
            parts = date_match.group(1).split('/')
            if len(parts) == 3:
                car['Date_annonce'] = f"{parts[0].zfill(2)}.{parts[1].zfill(2)}.{parts[2]}"

        specs = self._parse_characteristics(soup)

        if 'Kilometrage' in specs:
            specs['Kilometrage'] = specs['Kilometrage'].replace(' ', '')
        if 'Mise_en_circulation' in specs:
            val = specs['Mise_en_circulation']
            if re.match(r'^\d{4}$', val):
                specs['Mise_en_circulation'] = f"01.{val}"
        if 'Puissance_fiscale' in specs:
            specs['Puissance_fiscale'] = re.sub(r'[^\d]', '', specs['Puissance_fiscale'])
        if 'Nombre_portes' in specs:
            specs['Nombre_portes'] = re.sub(r'[^\d]', '', specs['Nombre_portes'])
        if 'Boite_vitesse' in specs:
            specs['Boite_vitesse'] = re.sub(r'\bvitesse\b', '', specs['Boite_vitesse'], flags=re.IGNORECASE).strip()

        car.update(specs)

        if 'Marque' not in car:
            brand_links = soup.find_all('a', href=re.compile(r'/voitures/marques/[^/]+$'))
            if brand_links:
                car['Marque'] = self.clean_text(brand_links[0].get_text())
        if 'Modele' not in car:
            model_links = soup.find_all('a', href=re.compile(r'/voitures/marques/[^/]+/[^/]+$'))
            if model_links:
                car['Modele'] = self.clean_text(model_links[0].get_text())

        if 'Marque' not in car and car.get('Title'):
            parts = car['Title'].split(maxsplit=1)
            if parts:
                car['Marque'] = parts[0].title()
                if len(parts) > 1:
                    car['Modele'] = parts[1].title()

        desc_heading = soup.find(
            lambda tag: tag.name in ('h2', 'h3', 'h4', 'strong')
            and 'description' in tag.get_text(strip=True).lower()
        )
        if desc_heading:
            desc_container = desc_heading.find_parent(['div', 'section'])
            if desc_container:
                desc_parts = []
                for child in desc_container.find_all(['p', 'li', 'span', 'div']):
                    t = child.get_text(strip=True)
                    if t and 'description' not in t.lower() and len(t) > 1:
                        desc_parts.append(t)
                if desc_parts:
                    car['Equipements'] = ', '.join(desc_parts)

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
        current_url = self.LISTING_URL

        while True:
            logger.info(f"\nPage {page_num}")

            html = self.get_page(current_url)
            if not html:
                logger.error(f"   Failed to load page {page_num}")
                break

            links = self.get_car_links(html)
            logger.info(f"   Found {len(links)} listings")

            if not links:
                logger.warning("   No links found, stopping.")
                break

            for idx, car_url in enumerate(links, 1):
                logger.info(f"   [{idx}/{len(links)}] Scraping...")
                self.scrape_car(car_url)
                time.sleep(random.uniform(0.3, 0.8))

            next_url = self.get_next_page_url(html)
            if not next_url:
                logger.info("   No more pages available")
                break

            current_url = next_url
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
        logger.info("BANIOLA.TN SCRAPER")
        logger.info("="*70 + "\n")

        try:
            self.scrape_all_pages()
            self.save_data()
        except KeyboardInterrupt:
            logger.info("\nInterrupted! Saving collected data...")
            self.save_data()


def main():
    scraper = BaniolaScraper()
    scraper.run()


if __name__ == "__main__":
    main()
