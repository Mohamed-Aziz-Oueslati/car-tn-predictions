from selenium import webdriver
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import re
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AutomobileScraperDynamic:
    
    BASE_URL = "https://www.automobile.tn"
    LISTING_URL = "https://www.automobile.tn/fr/occasion?page={}"
    
    def __init__(self):
        self.driver = None
        self.data = []
        self.consecutive_failures = 0
        self.failure_threshold = 5
    
    def setup_driver(self):
        logger.info("Starting Firefox browser...")
        
        options = webdriver.FirefoxOptions()
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        
        self.driver = webdriver.Firefox(options=options)
        logger.info("Firefox started\n")
    
    def clean_text(self, text):
        if not text:
            return None
        text = re.sub(r'\s+', ' ', text).strip()
        return text if text and len(text) > 0 else None
    
    def normalize_key(self, key):
        if not key:
            return None
        key = key.strip()
        key = re.sub(r'[^\w\s]', '', key)
        key = re.sub(r'\s+', '_', key)
        return key if len(key) > 1 else None
    
    def extract_car_data(self, page_html):
        soup = BeautifulSoup(page_html, 'html.parser')
        car_data = {}
        
        for elem in soup.find_all(['script', 'style', 'noscript']):
            elem.decompose()
        
        title_elem = soup.find('h1')
        if title_elem:
            car_data['Title'] = self.clean_text(title_elem.get_text())
        
        page_text = soup.get_text(' ', strip=True)
        
        price_match = re.search(r'Prix\s+demandé\s+([\d\s]+)\s*DT', page_text)
        if price_match:
            price_val = price_match.group(1).replace(' ', '')
            car_data['Price'] = f"{price_val} DT"
        
        spec_patterns = [
            (r'Kilométrage\s*([\d\s]+)\s*(?:KM|km)', 'Kilometrage'),
            (r'Mise en circulation\s*(\d{2}[./]\d{4})', 'Mise_en_circulation'),
            (r'[ÉE]nergie\s*(Diesel|Essence|Electrique|Électrique|Hybride[^A-Z]*)', 'Energie'),
            (r'Boite\s*vitesse\s*(Automatique|Manuelle)', 'Boite_vitesse'),
            (r'Puissance\s*fiscale\s*(\d+)\s*(?:CV|cv)', 'Puissance_fiscale'),
            (r'Transmission\s*(Traction|Propulsion|Int[ée]grale)', 'Transmission'),
            (r'Carrosserie\s*(SUV|Berline|Break|Coup[ée]|Cabriolet|Monospace)', 'Carrosserie'),
            (r'[ÉE]tat\s*g[ée]n[ée]ral\s*(Tr[eè]s\s*bon|Bon|Moyen|Neuf)', 'Etat_general'),
            (r'Anciens\s*propri[ée]taires\s*(\d+[èe]?r?e?\s*main)', 'Proprietaires'),
            (r'Gouvernorat\s*(\w+)', 'Gouvernorat'),
            (r"Date\s*de\s*l.annonce\s*(\d{2}[./]\d{2}[./]\d{4})", 'Date_annonce'),
            (r'Marque\s*([A-Za-z][A-Za-z\s\-]+?)(?=Mod[èe]le|$)', 'Marque'),
            (r'Mod[èe]le\s*([A-Za-z0-9][A-Za-z0-9\s\-]+?)(?=G[ée]n[ée]ration|Carrosserie|$)', 'Modele'),
            (r'Couleur\s*ext[ée]rieure\s*(\w+)', 'Couleur_exterieure'),
            (r'Couleur\s*int[ée]rieure\s*(\w+)', 'Couleur_interieure'),
            (r'Sellerie\s*(Cuir|Tissu|Similicuir|Alcantara|Cuir\s*int[ée]gral)', 'Sellerie'),
            (r'Nombre\s*de\s*places\s*(\d+)', 'Nombre_places'),
            (r'Nombre\s*de\s*portes\s*(\d+)', 'Nombre_portes'),
            (r'Puissance\s*(\d+)\s*(?:CH|ch)\s*(?:DYN|dyn)?', 'Puissance_ch'),
            (r'Cylindr[ée]e\s*([\d\s]+)\s*cm', 'Cylindree'),
        ]
        
        for pattern, key in spec_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                value = self.clean_text(match.group(1))
                if value and key not in car_data:
                    car_data[key] = value
        
        equipments = []
        equipment_list = [
            'ABS', 'Airbags frontaux', 'Airbags latéraux', 'ESP',
            'Climatisation', 'Climatisation automatique', 
            'Sièges chauffants', 'Sièges électriques',
            'Toit ouvrant', 'Toit panoramique',
            'Régulateur de vitesse', 'Navigation', 'GPS', 
            'Bluetooth', 'Apple Carplay', 'Android Auto',
            'Caméra de recul', 'Radar de recul',
            'Jantes en alliage', 'Feux à LED', 'Phares LED',
            'Direction assistée', 'Vitres électriques',
            'Fermeture centralisée', 'Ordinateur de bord'
        ]
        
        for item in equipment_list:
            if re.search(rf'(?<![A-Za-z]){re.escape(item)}(?![A-Za-z])', page_text, re.IGNORECASE):
                equipments.append(item)
        
        if equipments:
            car_data['Equipements'] = ', '.join(sorted(set(equipments)))
        
        return car_data
    
    def scrape_car(self, url):
        try:
            car_id = url.split('/')[-1]
            
            self.driver.get(url)
            time.sleep(random.uniform(1.5, 2.5))
            
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(0.5)
            
            car_data = self.extract_car_data(self.driver.page_source)
            car_data['URL'] = url
            
            field_count = len([v for v in car_data.values() if v is not None])
            
            if field_count >= 3:
                self.data.append(car_data)
                title = car_data.get('Title', 'Unknown')
                logger.info(f"      {title[:40]} ({field_count} fields)")
                self.consecutive_failures = 0
                return True
            else:
                logger.warning(f"      Not enough data ({field_count} fields)")
                self.consecutive_failures += 1
                self.check_vpn_needed()
                return False
        
        except Exception as e:
            logger.error(f"      Error: {str(e)[:60]}")
            self.consecutive_failures += 1
            self.check_vpn_needed()
            return False
    
    def check_vpn_needed(self):
        if self.consecutive_failures >= self.failure_threshold:
            logger.warning(f"\n{'='*70}")
            logger.warning(f"SITE MAY BE BLOCKING - {self.consecutive_failures} consecutive failures")
            logger.warning(f"{'='*70}")
            input("\nPlease change your VPN and press ENTER to continue...")
            self.consecutive_failures = 0
            logger.info("Resuming scraping...\n")
    
    def scrape_page(self, page_num, max_retries=10):
        try:
            url = self.LISTING_URL.format(page_num)
            logger.info(f"\nPage {page_num}")
            
            links = []
            for attempt in range(max_retries):
                self.driver.get(url)
                time.sleep(random.uniform(3, 5))
                
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                
                links = []
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    if '/fr/occasion/' in href:
                        car_id = href.split('/')[-1]
                        if car_id.isdigit() and len(car_id) >= 4:
                            full_url = self.BASE_URL + href if href.startswith('/') else href
                            if full_url not in links:
                                links.append(full_url)
                
                logger.info(f"   Found {len(links)} listings")
                
                if links:
                    break
                
                if attempt < max_retries - 1:
                    logger.warning(f"   No links found, retrying ({attempt + 1}/{max_retries})...")
                    time.sleep(random.uniform(2, 4))
            
            if not links:
                logger.warning("   No links found after all retries")
                return False
            
            for idx, car_url in enumerate(links, 1):
                if len(self.data) >= 1500:
                    return True
                logger.info(f"   [{idx}/{len(links)}] Scraping...")
                self.scrape_car(car_url)
            
            return True
        
        except Exception as e:
            logger.error(f"Error on page {page_num}: {e}")
            return False
    
    def save_data(self):
        if not self.data:
            logger.error("No data to save!")
            return False
        
        df = pd.DataFrame(self.data)
        
        preferred_order = [
            'Title', 'Price', 'Marque', 'Modele', 'Kilometrage', 'Mise_en_circulation',
            'Energie', 'Boite_vitesse', 'Puissance_fiscale', 'Puissance_ch', 'Transmission',
            'Carrosserie', 'Etat_general', 'Proprietaires', 'Gouvernorat',
            'Couleur_exterieure', 'Couleur_interieure', 'Sellerie',
            'Nombre_places', 'Nombre_portes', 'Moteur', 'Cylindree',
            'Equipements', 'Date_annonce', 'URL'
        ]
        
        existing_cols = df.columns.tolist()
        ordered_cols = [c for c in preferred_order if c in existing_cols]
        other_cols = [c for c in existing_cols if c not in preferred_order]
        final_cols = ordered_cols + other_cols
        
        df = df[final_cols]
        
        filename = 'automobile_tn_data.csv'
        import os
        if os.path.exists(filename):
            existing_df = pd.read_csv(filename, encoding='utf-8-sig')
            df = pd.concat([existing_df, df], ignore_index=True)
            df = df.drop_duplicates(subset=['URL'], keep='last')
            logger.info(f"   Appended to existing CSV (total: {len(df)} cars)")
        
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        
        logger.info(f"\n{'='*70}")
        logger.info(f"SCRAPING COMPLETE")
        logger.info(f"{'='*70}")
        logger.info(f"Cars scraped: {len(df)}")
        logger.info(f"Columns: {list(df.columns)}")
        logger.info(f"Output file: {filename}")
        logger.info(f"{'='*70}\n")
        
        return True
    
    def run(self, pages=3, max_cars=100, start_page=1):
        logger.info("\n" + "="*70)
        logger.info("AUTOMOBILE.TN SCRAPER - DYNAMIC EXTRACTION")
        logger.info(f"   Starting from page {start_page}")
        logger.info("="*70 + "\n")
        
        self.setup_driver()
        
        try:
            page = start_page
            while len(self.data) < max_cars and page <= pages:
                if page == 300:
                    page += 1
                    continue
                success = self.scrape_page(page)
                if not success:
                    break
                page += 1
            
            self.save_data()
        
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                    logger.info("Browser closed\n")
                except:
                    pass

def main():
    scraper = AutomobileScraperDynamic()
    scraper.run(
        pages=182,
        max_cars=3000,
        start_page=1
    )

if __name__ == "__main__":
    main()