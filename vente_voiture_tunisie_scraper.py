from selenium import webdriver
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import re
import os
import logging
from urllib3.exceptions import ReadTimeoutError
from selenium.common.exceptions import TimeoutException, WebDriverException

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VenteVoitureTunisieScraper:
    
    BASE_URL = "https://www.vente-voiture-tunisie.com"
    LISTING_URL = "https://www.vente-voiture-tunisie.com/voiture-occasion/all-voiture-occasion-tunisie.aspx"
    
    def __init__(self):
        self.driver = None
        self.data = []
        self.consecutive_failures = 0
        self.failure_threshold = 5
        self.scraped_urls = set()
    
    def setup_driver(self):
        logger.info("Starting Firefox browser...")
        
        options = webdriver.FirefoxOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        
        self.driver = webdriver.Firefox(options=options)
        logger.info("Firefox started (headless)\n")
    
    def clean_text(self, text):
        if not text:
            return None
        text = re.sub(r'\s+', ' ', text).strip()
        return text if text and len(text) > 0 else None
    
    def extract_marque_modele(self, title):
        if not title:
            return None, None
        
        title = title.strip().upper()
        
        brands = [
            'ALFA ROMEO', 'AUDI', 'BAIC', 'BMW', 'CADILLAC', 'CHERY', 'CHEVROLET',
            'CITROEN', 'CITROËN', 'DACIA', 'DODGE', 'DONGFENG', 'DS', 'FIAT', 'FORD',
            'GREAT WALL', 'HAVAL', 'HONDA', 'HYUNDAI', 'ISUZU', 'JAGUAR', 'JEEP',
            'KIA', 'LADA', 'LANCIA', 'LAND ROVER', 'MAHINDRA', 'MAZDA', 'MERCEDES',
            'MERCEDES-BENZ', 'MG', 'MINI', 'MITSUBISHI', 'NISSAN', 'OPEL', 'PEUGEOT',
            'PORSCHE', 'PORSHE', 'RENAULT', 'ROVER', 'SEAT', 'SKODA', 'SMART',
            'SSANGYONG', 'SUZUKI', 'TATA', 'TOYOTA', 'VOLKSWAGEN', 'VOLVO'
        ]
        
        for brand in brands:
            if title.startswith(brand):
                model = title[len(brand):].strip()
                return brand.title(), model.title() if model else None
        
        
        parts = title.split(maxsplit=1)
        if len(parts) >= 2:
            return parts[0].title(), parts[1].title()
        elif len(parts) == 1:
            return parts[0].title(), None
        
        return None, None
    
    def extract_car_data(self, page_html, url):
        soup = BeautifulSoup(page_html, 'html.parser')
        car_data = {}
        
        for elem in soup.find_all(['script', 'style', 'noscript']):
            elem.decompose()
        
        
        title_elem = soup.find('h1')
        if title_elem:
            title = self.clean_text(title_elem.get_text())
            car_data['Title'] = title
            
            
            marque, modele = self.extract_marque_modele(title)
            if marque:
                car_data['Marque'] = marque
            if modele:
                car_data['Modele'] = modele
        
        page_text = soup.get_text(' ', strip=True)
        
        field_patterns = [
            (r'Prix\s*\(TND\)\s*([\d\s]+)', 'Price'),
            (r'Kilométrage\s*\(km\)\s*([\d\s]+)', 'Kilometrage'),
            (r'Mise en circulation\s*(\d{1,2}/\d{4})', 'Mise_en_circulation'),
            (r'Motorisation\s*(Essence|Diesel|Electrique|Électrique|Hybride)', 'Energie'),
            (r'Boite\s*(Automatique|Manuelle)', 'Boite_vitesse'),
            (r'Puissance fiscale\s*(\d+)\s*[Cc][Vv]', 'Puissance_fiscale'),
            (r'Puissance\s*\(ch\)\s*(\d+)', 'Puissance_ch'),
            (r'Transmission\s*(Traction|Propulsion|Int[ée]grale|4x4|AWD)', 'Transmission'),
            (r'Carrosserie\s*(Berline|SUV|Citadine|Compact[e]?|Cabriolet|Coup[ée]|Monospace|Break|Pick[- ]?up|Utilitaire|4x4|Crossover)', 'Carrosserie'),
            (r'[ÉE]tat g[ée]n[ée]ral\s*([A-Za-zÀ-ÿ\s]+?)(?=Kilom|Mise|Motori|Boite|Puiss|Trans|Carro|Nombre|Couleur|Gouvern|Autres|Sellerie|Propri|Contact|$)', 'Etat_general'),
            (r'Propri[ée]taires?\s*(\d+|[A-Za-zÀ-ÿ\s]+?)(?=Kilom|Mise|Motori|Boite|Puiss|Trans|Carro|Nombre|Couleur|Gouvern|Autres|Sellerie|[ÉE]tat|Contact|$)', 'Proprietaires'),
            (r'Sellerie\s*(Cuir|Tissu|Alcantara|Simili|Mixte|[A-Za-zÀ-ÿ]+)', 'Sellerie'),
            (r'Nombre de places\s*(\d+)', 'Nombre_places'),
            (r'Nombre de portes\s*(\d+)\s*[Pp]ortes?', 'Nombre_portes'),
            (r'Cylindr[ée]e\s*(\d[\d\s]*)\s*(?:cm|cc|l)', 'Cylindree'),
            (r"Couleur\s*/\s*ext[ée]rieur\s*([A-Za-zÀ-ÿ\-]+)", 'Couleur_exterieure'),
            (r"Couleur\s*/\s*int[ée]rieur\s*([A-Za-zÀ-ÿ\-]+)", 'Couleur_interieure'),
            (r'Gouvernorat\s*([A-Za-zÀ-ÿ\s]+?)(?=Autres|Contact|$)', 'Gouvernorat'),
            (r'Soumise le\s*(\d{1,2}/\d{1,2}/\d{4})', 'Date_annonce'),
        ]
        
        for pattern, key in field_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                value = self.clean_text(match.group(1))
                if value and value != '-':
                    if key == 'Price':
                        price_val = value.replace(' ', '')
                        car_data[key] = f"{price_val} DT"
                    elif key == 'Kilometrage':
                        car_data[key] = value.replace(' ', '')
                    elif key == 'Mise_en_circulation':
                        
                        car_data[key] = value.replace('/', '.')
                    elif key == 'Date_annonce':
                        
                        parts = value.split('/')
                        if len(parts) == 3:
                            car_data[key] = f"{parts[0].zfill(2)}.{parts[1].zfill(2)}.{parts[2]}"
                        else:
                            car_data[key] = value
                    elif key == 'Gouvernorat':
                        car_data[key] = value.strip()
                    else:
                        car_data[key] = value
        
        autres_match = re.search(r'Autres informations\s*(.*?)(?=Contact|Afficher|$)', page_text, re.IGNORECASE | re.DOTALL)
        if autres_match:
            autres_text = self.clean_text(autres_match.group(1))
            if autres_text and len(autres_text) > 3:
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
                
                found_equipments = []
                for item in equipment_list:
                    if re.search(rf'(?<![A-Za-z]){re.escape(item)}(?![A-Za-z])', autres_text, re.IGNORECASE):
                        found_equipments.append(item)
                
                if found_equipments:
                    car_data['Equipements'] = ', '.join(sorted(set(found_equipments)))
        
        car_data['URL'] = url
        
        return car_data
    
    def load_page_with_retry(self, url, max_retries=3):
        for attempt in range(max_retries):
            try:
                self.driver.get(url)
                return True
            except (ReadTimeoutError, TimeoutException, WebDriverException) as e:
                if 'timeout' in str(e).lower() or isinstance(e, (ReadTimeoutError, TimeoutException)):
                    wait_time = 5 * (attempt + 1)
                    logger.warning(f"      Timeout (attempt {attempt + 1}/{max_retries}), waiting {wait_time}s...")
                    time.sleep(wait_time)
                    if attempt == max_retries - 1:
                        logger.error(f"      Max retries reached for {url}")
                        return False
                else:
                    raise
            except Exception as e:
                if 'Read timed out' in str(e) or 'timeout' in str(e).lower():
                    wait_time = 5 * (attempt + 1)
                    logger.warning(f"      Timeout (attempt {attempt + 1}/{max_retries}), waiting {wait_time}s...")
                    time.sleep(wait_time)
                    if attempt == max_retries - 1:
                        logger.error(f"      Max retries reached for {url}")
                        return False
                else:
                    raise
        return False

    def scrape_car(self, url):
        try:
            if url in self.scraped_urls:
                logger.info(f"      Already scraped, skipping...")
                return True
            
            original_window = self.driver.current_window_handle
            self.driver.execute_script("window.open('');")
            self.driver.switch_to.window(self.driver.window_handles[-1])
            
            if not self.load_page_with_retry(url):
                self.driver.close()
                self.driver.switch_to.window(original_window)
                self.consecutive_failures += 1
                self.check_vpn_needed()
                return False
            time.sleep(random.uniform(1.5, 2.5))
            
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(0.3)
            
            car_data = self.extract_car_data(self.driver.page_source, url)
            
            self.driver.close()
            self.driver.switch_to.window(original_window)
            
            field_count = len([v for v in car_data.values() if v is not None])
            
            if field_count >= 3:
                self.data.append(car_data)
                self.scraped_urls.add(url)
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
            try:
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
            except:
                pass
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
    
    def get_car_links_from_page(self, soup):
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if 'Annonce-vente-voiture-occasion-tunisie.aspx?ref=' in href:
                full_url = self.BASE_URL + '/voiture-occasion/' + href.split('/')[-1] if not href.startswith('http') else href
                if not full_url.startswith('http'):
                    full_url = self.BASE_URL + href if href.startswith('/') else self.BASE_URL + '/' + href
                if full_url not in links:
                    links.append(full_url)
        return links
    
    def has_next_page(self, soup):
        for a in soup.find_all('a', href=True):
            if '>>>' in a.get_text():
                return True
        return False
    
    def click_next_page(self, max_retries=10):
        for attempt in range(max_retries):
            try:
                next_link = self.driver.find_element("xpath", "//a[contains(text(), '>>>')]") 
                self.driver.execute_script("arguments[0].click();", next_link)
                time.sleep(random.uniform(2, 4))
                return True
            except Exception as e:
                error_str = str(e).lower()
                if 'timeout' in error_str or 'connectionpool' in error_str or 'read timed out' in error_str:
                    wait_time = 5 * (attempt + 1)
                    logger.warning(f"   Click timeout (attempt {attempt + 1}/{max_retries}), waiting {wait_time}s...")
                    time.sleep(wait_time)
                    if attempt == max_retries - 1:
                        logger.warning(f"   Max retries reached, trying to reload page...")
                        
                        try:
                            self.driver.refresh()
                            time.sleep(3)
                            next_link = self.driver.find_element("xpath", "//a[contains(text(), '>>>')]") 
                            self.driver.execute_script("arguments[0].click();", next_link)
                            time.sleep(random.uniform(2, 4))
                            return True
                        except:
                            pass
                        return False
                elif 'no such element' in error_str or 'unable to locate' in error_str:
                    logger.info(f"   No more pages available")
                    return False
                else:
                    logger.info(f"   No more pages or error: {str(e)[:50]}")
                    return False
        return False
    
    def scrape_all_pages(self):
        logger.info(f"\nStarting scraping from listing page...")
        
        if not self.load_page_with_retry(self.LISTING_URL):
            logger.error("Failed to load listing page")
            return
        time.sleep(random.uniform(3, 5))
        
        page_num = 1
        
        while True:
            logger.info(f"\nPage {page_num}")
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            links = self.get_car_links_from_page(soup)
            
            logger.info(f"   Found {len(links)} listings")
            
            if not links:
                logger.warning("   No links found on this page")
                break
            
            for idx, car_url in enumerate(links, 1):
                logger.info(f"   [{idx}/{len(links)}] Scraping...")
                self.scrape_car(car_url)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            if not self.has_next_page(soup):
                logger.info("   No more pages available")
                break
            
            if not self.click_next_page():
                break
            
            page_num += 1
    
    def save_data(self):
        if not self.data:
            logger.error("No data to save!")
            return False
        
        df = pd.DataFrame(self.data)
        
        required_columns = [
            'Title', 'Price', 'Marque', 'Modele', 'Kilometrage', 'Mise_en_circulation',
            'Energie', 'Boite_vitesse', 'Puissance_fiscale', 'Puissance_ch', 'Transmission',
            'Carrosserie', 'Etat_general', 'Proprietaires', 'Gouvernorat',
            'Couleur_exterieure', 'Couleur_interieure', 'Sellerie',
            'Nombre_places', 'Nombre_portes', 'Cylindree',
            'Equipements', 'Date_annonce', 'URL'
        ]
        
        
        for col in required_columns:
            if col not in df.columns:
                df[col] = None
        
        
        df = df[required_columns]
        
        filename = 'vente_voiture_tunisie_data.csv'
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        
        logger.info(f"\n{'='*70}")
        logger.info(f"SCRAPING COMPLETE")
        logger.info(f"{'='*70}")
        logger.info(f"Cars scraped: {len(df)}")
        logger.info(f"Columns: {list(df.columns)}")
        logger.info(f"Output file: {filename}")
        logger.info(f"{'='*70}\n")
        
        return True
    
    def run(self):
        logger.info("\n" + "="*70)
        logger.info("🚗 VENTE-VOITURE-TUNISIE.COM SCRAPER")
        logger.info("="*70 + "\n")
        
        self.setup_driver()
        
        try:
            self.scrape_all_pages()
            self.save_data()
        
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                    logger.info("Browser closed\n")
                except:
                    pass


def main():
    scraper = VenteVoitureTunisieScraper()
    scraper.run()


if __name__ == "__main__":
    main()
