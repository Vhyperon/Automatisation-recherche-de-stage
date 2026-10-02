import os
import json
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

SEARCH_KEYWORDS = "robotics intern OR robotics internship"
COUNTRIES = ["de", "nl", "dk", "es", "ch","at","pl","se","cz","us","ca"] # Allemagne, Pays-Bas, Danemark, Espagne, Suisse
TECH_FILTER = ["ros", "ros2", "python", "c++", "embedded", "vision","CAD","3D design"]

ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")
SHEET_ID = os.getenv("GOOGLE_SHEET_ID") # Trouvable dans l'URL de ton tableur
GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")

def get_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = json.loads(GOOGLE_CREDS_JSON)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client.open_by_key(SHEET_ID).sheet1

def scan_and_export():
    sheet = get_sheet()
    
    # Récupération des URLs dans la 7ème colonne ("Lien / Contact") pour éviter les doublons
    existing_urls = sheet.col_values(7) 
    
    for country in COUNTRIES:
        url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
        params = {
            "app_id": ADZUNA_APP_ID,
            "app_key": ADZUNA_APP_KEY,
            "what": SEARCH_KEYWORDS,
            "content-type": "application/json"
        }
        response = requests.get(url, params=params)
        if response.status_code != 200:
            continue
            
        for job in response.json().get("results", []):
            job_url = job["redirect_url"]
            desc = job["description"].lower()
            
            # Vérification technique et unicité
            if job_url not in existing_urls and any(tech in desc for tech in TECH_FILTER):
                
                # Création de la ligne avec les 12 colonnes exactes de ton tableur
                row = [
                    job.get('company', {}).get('display_name', 'N/A'),  # 1. Entreprise
                    job['title'],                                       # 2. Intitulé de l'offre
                    "Robotique",                                        # 3. Secteur d'activité (par défaut)
                    "Stage",                                            # 4. Poste visé (par défaut)
                    job.get('location', {}).get('display_name', 'N/A'), # 5. Localisation
                    "",                                                 # 6. Numéro de téléphone (vide)
                    job_url,                                            # 7. Lien / Contact
                    "À analyser",                                       # 8. Statut (par défaut)
                    datetime.now().strftime("%d/%m/%Y"),                # 9. Date d'ajout
                    "",                                                 # 10. Date de contact (vide)
                    "",                                                 # 11. Date de relance (vide)
                    ""                                                  # 12. Notes / Prochaines étapes (vide)
                ]
                
                sheet.append_row(row)
                existing_urls.append(job_url)

if __name__ == "__main__":
    scan_and_export()
