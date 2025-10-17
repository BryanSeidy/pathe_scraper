"""
Script d'automatisation pour la mise à jour des showtimes sur IciCine
Auteur: Script généré pour l'administration IciCine
Date: 2025-10-14
Description: Ce script se connecte à l'interface d'administration IciCine,
             parcourt les showtimes et met à jour ceux dont le prix est 0 FCFA.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException,
    StaleElementReferenceException
)
import time
import logging
from typing import List, Optional

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('icicine_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class IciCineAutomation:
    """Classe pour l'automatisation des opérations sur IciCine."""
    
    # Constantes de configuration
    BASE_URL = "https://icicine.com/admin465-icicine/cinema/showtimes?page=4"
    LOGIN_EMAIL = "seidychris4@gmail.com"
    LOGIN_PASSWORD = "Password2@"
    DEFAULT_PRICE = "2500"  # Prix par défaut à définir
    TIMEOUT = 20
    
    def __init__(self, headless: bool = False):
        """
        Initialise l'instance d'automatisation.
        
        Args:
            headless (bool): Exécuter le navigateur en mode headless
        """
        self.driver: Optional[webdriver.Chrome] = None
        self.wait: Optional[WebDriverWait] = None
        self.headless = headless
        self.showtimes_updated = 0
        
    def setup_driver(self) -> None:
        """Configure et initialise le WebDriver Chrome."""
        try:
            options = webdriver.ChromeOptions()
            
            if self.headless:
                options.add_argument('--headless')
            
            # Options pour améliorer la stabilité
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--start-maximized')
            
            # Désactiver les notifications
            prefs = {
                "profile.default_content_setting_values.notifications": 2
            }
            options.add_experimental_option("prefs", prefs)
            
            self.driver = webdriver.Chrome(options=options)
            self.wait = WebDriverWait(self.driver, self.TIMEOUT)
            
            logger.info("WebDriver initialisé avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du WebDriver: {e}")
            raise
    
    def login(self) -> bool:
        """
        Effectue la connexion à l'interface d'administration.
        
        Returns:
            bool: True si la connexion réussit, False sinon
        """
        try:
            logger.info(f"Accès à la page: {self.BASE_URL}")
            self.driver.get(self.BASE_URL)
            
            # Attendre que la page soit chargée
            time.sleep(3)
            
            # Vérifier si on est déjà connecté ou si on doit se connecter
            if "login" in self.driver.current_url.lower():
                logger.info("Page de connexion détectée, saisie des identifiants...")
                
                # Localiser le champ email
                email_input = self.wait.until(
                    EC.presence_of_element_located((
                        By.CSS_SELECTOR,
                        "input.fi-input[type='email'], input.fi-input[type='text']"
                    ))
                )
                email_input.clear()
                email_input.send_keys(self.LOGIN_EMAIL)
                logger.info("Email saisi avec succès")
                
                # Localiser le champ mot de passe
                password_inputs = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "input.fi-input[type='password']"
                )
                
                if password_inputs:
                    password_input = password_inputs[0]
                    password_input.clear()
                    password_input.send_keys(self.LOGIN_PASSWORD)
                    logger.info("Mot de passe saisi avec succès")
                else:
                    raise NoSuchElementException("Champ mot de passe non trouvé")
                
                # Cliquer sur le bouton de connexion
                login_button = self.wait.until(
                    EC.element_to_be_clickable((
                        By.CSS_SELECTOR,
                        "button[type='submit']"
                    ))
                )
                login_button.click()
                logger.info("Bouton de connexion cliqué")
                
                # Attendre la redirection après connexion
                time.sleep(5)
                
            logger.info("Connexion réussie")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la connexion: {e}")
            return False
    
    def get_showtimes_with_zero_price(self) -> List[tuple]:
        """
        Identifie tous les showtimes avec un prix de 0 FCFA.
        
        Returns:
            List[tuple]: Liste de tuples (élément_ligne, prix_actuel)
        """
        zero_price_showtimes = []
        
        try:
            # Attendre que le tableau soit chargé
            time.sleep(3)
            
            # Localiser toutes les lignes du tableau
            table_rows = self.driver.find_elements(
                By.CSS_SELECTOR,
                "table tbody tr"
            )
            
            logger.info(f"Nombre de lignes trouvées: {len(table_rows)}")
            
            for index, row in enumerate(table_rows, start=1):
                try:
                    # Chercher le span contenant le prix
                    price_spans = row.find_elements(
                        By.CSS_SELECTOR,
                        "span.fi-ta-text-item-label"
                    )
                    
                    for price_span in price_spans:
                        price_text = price_span.text.strip()
                        
                        # Vérifier si le prix est 0 ou FCFA 0
                        if price_text in ["FCFA 1,500", "FCFA 1500", "FCFA\xa01550", "1500 FCFA"]:
                            logger.info(f"Showtime avec prix 0 trouvé à la ligne {index}")
                            zero_price_showtimes.append((row, price_text))
                            break
                            
                except StaleElementReferenceException:
                    logger.warning(f"Élément obsolète à la ligne {index}, passage à la suivante")
                    continue
                except Exception as e:
                    logger.warning(f"Erreur lors du traitement de la ligne {index}: {e}")
                    continue
            
            logger.info(f"Total de showtimes à mettre à jour: {len(zero_price_showtimes)}")
            return zero_price_showtimes
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche des showtimes: {e}")
            return []
    
    def update_showtime(self, row_element) -> bool:
        """
        Met à jour un showtime spécifique.
        
        Args:
            row_element: L'élément de ligne contenant le showtime
            
        Returns:
            bool: True si la mise à jour réussit, False sinon
        """
        try:
            # Trouver le bouton "Modifier" avec plusieurs tentatives
            edit_button = None
            
            # Méthode 1: Chercher par attribut wire:click contenant 'edit'
            try:
                edit_button = row_element.find_element(
                    By.CSS_SELECTOR,
                    "button[wire\\:click*='edit'], button[wire\\:click*='Edit']"
                )
                logger.info("Bouton trouvé via wire:click")
            except NoSuchElementException:
                pass
            
            # Méthode 2: Chercher le bouton avec le texte "Modifier"
            if not edit_button:
                try:
                    buttons = row_element.find_elements(
                        By.CSS_SELECTOR,
                        "button.fi-link"
                    )
                    for btn in buttons:
                        if "Modifier" in btn.text or "modifier" in btn.get_attribute("wire:click"):
                            edit_button = btn
                            logger.info("Bouton trouvé via texte 'Modifier'")
                            break
                except:
                    pass
            
            # Méthode 3: Chercher dans la cellule d'actions
            if not edit_button:
                try:
                    actions_cell = row_element.find_element(
                        By.CSS_SELECTOR,
                        "td.fi-ta-actions-cell"
                    )
                    edit_button = actions_cell.find_element(
                        By.CSS_SELECTOR,
                        "button.fi-link.fi-color-primary"
                    )
                    logger.info("Bouton trouvé via cellule d'actions")
                except:
                    pass
            
            if not edit_button:
                raise NoSuchElementException("Impossible de trouver le bouton Modifier")
            
            # Scroll vers l'élément pour s'assurer qu'il est visible
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", edit_button)
            time.sleep(1)
            
            # Attendre que le bouton soit cliquable
            self.driver.execute_script("arguments[0].click();", edit_button)
            logger.info("Bouton 'Modifier' cliqué avec JavaScript")
            time.sleep(3)
            
            # Attendre que le modal s'ouvre complètement
            modal = self.wait.until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR,
                    "div.fi-modal, form[wire\\:submit]"
                ))
            )
            logger.info("Modal ouvert")
            time.sleep(10)
            
            # Chercher l'input du prix avec plusieurs méthodes
            price_input = None
            
            try:
                # Méthode 1: Par ID contenant 'price'
                price_input = self.driver.find_element(
                    By.CSS_SELECTOR,
                    "input[id*='price']"
                )
            except NoSuchElementException:
                try:
                    # Méthode 2: Par placeholder ou label
                    price_input = self.driver.find_element(
                        By.XPATH,
                        "//label[contains(text(), 'Prix')]/following::input[1] | //input[@placeholder='Prix']"
                    )
                except:
                    # Méthode 3: Tous les inputs text dans le modal
                    inputs = modal.find_elements(By.CSS_SELECTOR, "input[type='text']")
                    if inputs:
                        price_input = inputs[0]  # Premier input trouvé
            
            if not price_input:
                raise NoSuchElementException("Champ prix non trouvé")
            
            # Mettre à jour le prix
            self.driver.execute_script("arguments[0].value = '';", price_input)
            price_input.clear()
            price_input.send_keys(self.DEFAULT_PRICE)
            logger.info(f"Prix mis à jour: {self.DEFAULT_PRICE}")
            time.sleep(1)
            
            # Sélectionner la langue (VF - option 1)
            try:
                # Chercher le select de langue
                language_select = None
                
                try:
                    language_select = self.driver.find_element(
                        By.CSS_SELECTOR,
                        "select[id*='language']"
                    )
                except NoSuchElementException:
                    try:
                        language_select = self.driver.find_element(
                            By.XPATH,
                            "//label[contains(text(), 'Langue')]/following::select[1]"
                        )
                    except:
                        language_selects = modal.find_elements(By.TAG_NAME, "select")
                        if language_selects:
                            language_select = language_selects[0]
                
                if language_select:
                    select = Select(language_select)
                    # Essayer de sélectionner par valeur, puis par index
                    try:
                        select.select_by_value("1")
                    except:
                        try:
                            select.select_by_index(1)
                        except:
                            select.select_by_visible_text("VF")
                    logger.info("Langue VF sélectionnée")
                    time.sleep(1)
            except Exception as lang_error:
                logger.warning(f"Erreur lors de la sélection de langue: {lang_error}")
            
            # Cliquer sur le bouton "Sauvegarder"
            save_button = None
            
            # Méthode 1: Par texte
            try:
                buttons = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "button.fi-btn"
                )
                for btn in buttons:
                    if "Sauvegarder" in btn.text or "Save" in btn.text:
                        save_button = btn
                        break
            except:
                pass
            
            # Méthode 2: Par classe et type
            if not save_button:
                try:
                    save_button = self.driver.find_element(
                        By.CSS_SELECTOR,
                        "button.fi-btn-color-primary[type='submit']"
                    )
                except:
                    pass
            
            # Méthode 3: Bouton submit dans le modal
            if not save_button:
                try:
                    save_button = modal.find_element(
                        By.CSS_SELECTOR,
                        "button[type='submit']"
                    )
                except:
                    pass
            
            if not save_button:
                raise NoSuchElementException("Bouton Sauvegarder non trouvé")
            
            # Cliquer avec JavaScript pour plus de fiabilité
            self.driver.execute_script("arguments[0].click();", save_button)
            logger.info("Bouton 'Sauvegarder' cliqué")
            
            # Attendre la confirmation de la sauvegarde
            time.sleep(20)
            
            self.showtimes_updated += 1
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du showtime: {e}")
            
            # Tenter de fermer le modal en cas d'erreur
            # try:
            #     close_button = self.driver.find_element(
            #         By.CSS_SELECTOR,
            #         "button[aria-label='Close'], button.fi-modal-close-btn"
            #     )
            #     close_button.click()
            #     time.sleep(10)
            # except:
            #     pass
            
            # return False
    
    def process_all_showtimes(self) -> None:
        """Traite tous les showtimes avec un prix de 0 FCFA."""
        try:
            logger.info("Début du traitement des showtimes...")
            
            # Obtenir la liste des showtimes à mettre à jour
            showtimes_to_update = self.get_showtimes_with_zero_price()
            
            if not showtimes_to_update:
                logger.info("Aucun showtime avec prix 0 trouvé")
                return
            
            # Traiter chaque showtime
            for index, (row, price) in enumerate(showtimes_to_update, start=1):
                logger.info(f"Traitement du showtime {index}/{len(showtimes_to_update)}")
                
                try:
                    success = self.update_showtime(row)
                    
                    if success:
                        logger.info(f"Showtime {index} mis à jour avec succès")
                    else:
                        logger.warning(f"Échec de la mise à jour du showtime {index}")
                    
                    # Pause entre les mises à jour pour éviter la surcharge
                    time.sleep(2)
                    
                    # Recharger la page tous les 5 showtimes pour éviter les éléments obsolètes
                    if index % 5 == 0 and index < len(showtimes_to_update):
                        logger.info("Rechargement de la page...")
                        self.driver.refresh()
                        time.sleep(3)
                        showtimes_to_update = self.get_showtimes_with_zero_price()
                        
                except Exception as e:
                    logger.error(f"Erreur lors du traitement du showtime {index}: {e}")
                    continue
            
            logger.info(f"Traitement terminé. Total mis à jour: {self.showtimes_updated}")
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement des showtimes: {e}")
    
    def run(self) -> None:
        """Exécute le processus complet d'automatisation."""
        try:
            logger.info("=" * 60)
            logger.info("DÉMARRAGE DE L'AUTOMATISATION ICICINE")
            logger.info("=" * 60)
            
            # Configuration du driver
            self.setup_driver()
            
            # Connexion
            if not self.login():
                raise Exception("Échec de la connexion")
            
            # Traitement des showtimes
            self.process_all_showtimes()
            
            logger.info("=" * 60)
            logger.info("AUTOMATISATION TERMINÉE AVEC SUCCÈS")
            logger.info(f"Total de showtimes mis à jour: {self.showtimes_updated}")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Erreur critique lors de l'exécution: {e}")
            raise
        
        finally:
            self.cleanup()
    
    def cleanup(self) -> None:
        """Nettoie les ressources et ferme le navigateur."""
        if self.driver:
            try:
                logger.info("Fermeture du navigateur...")
                time.sleep(2)
                self.driver.quit()
                logger.info("Navigateur fermé avec succès")
            except Exception as e:
                logger.error(f"Erreur lors de la fermeture du navigateur: {e}")


def main():
    """Point d'entrée principal du script."""
    try:
        # Créer une instance de l'automatisation
        # headless=False pour voir le navigateur, True pour mode invisible
        automation = IciCineAutomation(headless=False)
        
        # Exécuter l'automatisation
        automation.run()
        
    except KeyboardInterrupt:
        logger.info("\n\nInterruption par l'utilisateur")
    except Exception as e:
        logger.error(f"Erreur fatale: {e}")
    finally:
        logger.info("Fin du script")


if __name__ == "__main__":
    main()