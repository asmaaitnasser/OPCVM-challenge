import os
import time
import requests
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ==========================================================
# 0) CONFIGURATION DES DOSSIERS
# ==========================================================

download_folder = "data/asfim_daily/"
os.makedirs(download_folder, exist_ok=True)

output_file = "performance_quotidienne_asfim.xlsx"

# ==========================================================
# 1) CONFIG SELENIUM
# ==========================================================

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=chrome_options
)

driver.get("https://www.asfim.ma/publications/tableaux-des-performances/")


# ==========================================================
# 2) SÉLECTIONNER L'ONGLET QUOTIDIEN
# ==========================================================

try:
    quotidien_btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Quotidien")]'))
    )
    quotidien_btn.click()
    time.sleep(2)
    print("✔ Onglet 'Quotidien' sélectionné.")
except Exception as e:
    print("❌ Impossible de sélectionner 'Quotidien' :", e)


# ==========================================================
# 3) SÉLECTIONNER 100 LIGNES PAR PAGE
# ==========================================================

try:
    select = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//select'))
    )
    Select(select).select_by_value("100")
    time.sleep(2)
    print("✔ 100 lignes sélectionnées.")
except:
    print("❌ Impossible de sélectionner 100 lignes.")


# ==========================================================
# 4) FONCTION D’EXTRACTION DES LIENS
# ==========================================================

def extract_links():
    rows = driver.find_elements(By.XPATH, '//tr[td/a[contains(text(), "Télécharger")]]')
    links = []

    for r in rows:
        nom = r.find_element(By.XPATH, './td[1]').text

        # GARDER UNIQUEMENT les fichiers quotidiens
        if "quotidien" not in nom.lower():
            continue

        url = r.find_element(By.XPATH, './/a[contains(text(), "Télécharger")]').get_attribute("href")
        links.append((nom.strip(), url))

    return links


# ==========================================================
# 5) TROUVER LE NOMBRE TOTAL DE PAGES
# ==========================================================

def get_total_pages():
    time.sleep(1)
    buttons = driver.find_elements(By.XPATH, '//button')
    pages = [int(btn.text.strip()) for btn in buttons if btn.text.strip().isdigit()]
    return max(pages) if pages else 1

total_pages = get_total_pages()
print(f"📌 Nombre total de pages : {total_pages}")


# ==========================================================
# 6) NAVIGATION PAGE PAR PAGE
# ==========================================================

all_links = []

for page in range(1, total_pages + 1):
    print(f"\n📄 Extraction page {page} ...")

    # Cliquer sur le bouton numéroté
    try:
        buttons = driver.find_elements(By.XPATH, '//button')
        for btn in buttons:
            if btn.text.strip() == str(page):
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(2)
                break
    except Exception as e:
        print(f"❌ Erreur page {page} :", e)
        continue

    all_links += extract_links()

driver.quit()

print(f"\n🔎 Total fichiers trouvés : {len(all_links)}")


# ==========================================================
# 7) TÉLÉCHARGER UNIQUEMENT LES NOUVEAUX FICHIERS
# ==========================================================

downloaded = []

for nom, url in all_links:
    safe = nom.replace(" ", "_").replace("/", "-") + ".xlsx"
    path = os.path.join(download_folder, safe)

    if os.path.exists(path):
        print(f"✔ Déjà présent, on saute : {safe}")
    else:
        try:
            print(f"⬇ Téléchargement : {safe}")
            r = requests.get(url)
            with open(path, "wb") as f:
                f.write(r.content)
        except Exception as e:
            print(f"❌ Erreur téléchargement {safe} :", e)

    downloaded.append(path)


# ==========================================================
# 8) FUSION RAPIDE DES EXCEL
# ==========================================================

print("\n📊 Fusion des fichiers ...")

dfs = []

for fpath in downloaded:
    try:
        # skip first row, second row is header
        df = pd.read_excel(fpath, skiprows=1)

        # insérer colonne source_file en premier
        df.insert(0, "source_file", os.path.basename(fpath))

        # réordonner CODE ISIN en deuxième colonne si présent
        if "CODE ISIN" in df.columns:
            cols = df.columns.tolist()
            cols.insert(1, cols.pop(cols.index("CODE ISIN")))
            df = df[cols]

        dfs.append(df)

    except Exception as e:
        print(f"❌ Erreur lecture {fpath} :", e)


# ==========================================================
# 9) SORTIE FINALE
# ==========================================================

if dfs:
    final = pd.concat(dfs, ignore_index=True)
    final.drop_duplicates(inplace=True)
    final.to_excel(output_file, index=False)
    print(f"🎉 Fichier final généré : {output_file}")
else:
    print("❌ Aucun fichier exploitable.")
