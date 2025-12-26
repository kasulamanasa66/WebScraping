# -*- coding: utf-8 -*-
"""
Created on Thu Dec 25 19:48:26 2025

@author: Manasa Kasula
"""

# -*- coding: utf-8 -*-
"""
Created on Sat Dec 20 15:48:58 2025

@author: Manasa Kasula
"""
import time 
import csv
import regex as re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from webdriver_manager.chrome import ChromeDriverManager

# =========================
# CONFIG
# =========================
URL = "https://www3.shoalhaven.nsw.gov.au/masterviewUI/modules/ApplicationMaster/Default.aspx"
FROM_DATE = "01/10/2025"
TO_DATE = "31/10/2025"


# =========================
# CHROME OPTIONS (FIX #2)
# =========================
options = Options()
options.add_argument("--headless=new")

options.add_argument("--start-maximized")
options.add_argument("--disable-notifications")
options.add_argument("--disable-infobars")
options.add_argument("--disable-extensions")

driver = webdriver.Chrome(options=options)

wait = WebDriverWait(driver, 20)

data = []
seen = set()

# =========================
# STEP 1: OPEN + AGREE
# =========================
driver.get(URL)

wait.until(
    EC.element_to_be_clickable((By.XPATH, "//input[@value='Agree']"))
).click()

# =========================
# FIX #1: AUTO-ACCEPT REDIRECT ALERT
# =========================
try:
    WebDriverWait(driver, 5).until(EC.alert_is_present())
    driver.switch_to.alert.accept()
except TimeoutException:
    pass

# =========================
# FIX #3: FORCE NAVIGATION (FALLBACK)
# =========================
driver.get(URL)

# =========================
# STEP 2: DA TRACKING
# =========================
wait.until(
    EC.element_to_be_clickable((By.LINK_TEXT, "DA Tracking"))
).click()

# =========================
# STEP 3: ADVANCED SEARCH
# =========================
wait.until(
    EC.element_to_be_clickable((By.LINK_TEXT, "Advanced Search"))
).click()

# =========================
# STEP 4: DATE RANGE + SEARCH
# =========================
from_box = wait.until(
    EC.presence_of_element_located(
        (By.ID, "ctl00_cphContent_ctl00_ctl03_dateInput_text")
    )
)
to_box = driver.find_element(By.ID, "ctl00_cphContent_ctl00_ctl05_dateInput_text")

from_box.clear()
from_box.send_keys(FROM_DATE)

to_box.clear()
to_box.send_keys(TO_DATE)

driver.find_element(
    By.NAME, "ctl00$cphContent$ctl00$btnSearch"
).click()

# =========================
# STEP 5: SHOW RESULTS
# =========================
#to explore/view a single application by clicking on the show button
# wait.until(
#     EC.element_to_be_clickable((By.XPATH, "//input[@value='Show']"))
# ).click()

# time.sleep(2)

# =========================
# SCRAPE ALL PAGES
# =========================
while True:

    rows = wait.until(
        EC.presence_of_all_elements_located(
            (By.XPATH, "//tr[contains(@class,'rgRow') or contains(@class,'rgAltRow')]")
        )
    )

    for row in rows:
        # link = row.text
        # Text = link.split('')
        # da_number= Text[0]
        # detail_url = link.get_attribute("href")
        
        link = row.find_element(By.TAG_NAME, "a")
       # da_number = link.text.strip()
        da_number = row.text.strip()
        da_number=da_number.split(' ')
        da_number=da_number[0]
     #   print(da_number)
        detail_url = link.get_attribute("href")

        if da_number in seen:
            continue

        seen.add(da_number)

        driver.execute_script(
            "window.open(arguments[0]);", detail_url
        )
        driver.switch_to.window(driver.window_handles[1])

        wait.until(
            EC.presence_of_element_located(
                (By.ID, "ctl00_cphContent_ctl00_lblApplicationHeader")
            )
        )
        #html_content=driver.page_source
        xpathref=driver.find_element(By.ID,"ctl00_cphContent_ctl00_lblApplicationHeader")
    #    print(xpathref.text)
        details = driver.find_element(By.ID, "lblDetails").text.strip()
        details=details.split("\n")
        Description=details[0].replace("Description:","")
        Submitted=details[1].replace("Submitted:","")
        decision = driver.find_element(By.ID, "lblDecision").text.strip()
        #decision= re.search(r'\d{2}/\d{2}/\d{4}',decision).group()
      #  print(decision)
      #  decision = driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_lblDecision").text.strip()
        categories = driver.find_element(By.ID, "lblCat").text.strip()
        Prop_address = driver.find_element(By.ID, "lblProp").text.strip()
        applicant = driver.find_element(By.ID, "lblPeople")
        applicant=applicant.get_attribute("textContent").replace("\n", "")
        applicant=applicant.replace("Applicant:","").strip()


#        progress = driver.find_element(By.ID, "lblprog").text.strip()
       # progress = driver.find_element(By.XPATH, "//*[@id=\"lblProg\"]/table/tbody/tr").text.strip()
        progress = driver.find_elements(By.XPATH, "//*[@id=\"lblProg\"]/table/tbody/tr")
        progress_data=[]
        for i in progress:
            cells=i.find_elements(By.TAG_NAME,"td")
            if cells:
                row_text="|".join(cell.text.strip() for cell in cells)
                progress_data.append(row_text)
               # print(table_data)
                                  

        

        #fees = driver.find_element(By.XPATH, "//*[@id=\"lblFees\"]").text.strip()
        fees = driver.find_element(By.XPATH, "//*[@id=\"lblFees\"]")
        fees_info=fees.get_attribute("textContent").replace("\n", "")

        documents = driver.find_element(By.ID, "lblDocs").text.strip()
        documents=documents.replace("     ♦ ","  *").replace("--> [View]","")
        print(documents)
        contact = driver.find_element(By.ID, "lbl91").text.strip()
        
        
        # =========================
        # STEP 6: CLEANING RULES
        # =========================
        if fees_info == "No fees recorded against this application.":
            fees_info = "Not required"
        elif (m:=re.search('\$\d+(?:\.\d{2})?',fees_info)):
            print(m.group())
            fees_info=m.group()

        if contact == (
            "Application Is Not on exhibition, please call Council on 1300 293 111 if you require assistance."
        ):
            contact = "Not required"

        data.append([
            da_number,
            detail_url,
            Description,
            Submitted,
           decision,
            categories,
            Prop_address,
            applicant,
            progress_data,
            fees_info,
            documents,
            contact
        ])
       # print(data)

        driver.close()
        driver.switch_to.window(driver.window_handles[0])

    # =========================
    # PAGINATION
    # =========================
    try:
      #  next_btn = driver.find_element(By.LINK_TEXT, "Next")
        next_btn = driver.find_element(By.XPATH, "//input[contains(@class,'rgPageNext')]")

        # if "disabled" in next_btn.get_attribute("class"):
        #     break
        onclick_value = next_btn.get_attribute("onclick")
        if onclick_value.strip().startswith("return false"):
        #    print("Last page reached")
            break
        next_btn.click()
        time.sleep(2)
    except:
        break
    
    

CSV_FILE = "shoalhaven_da.csv"
headers = [
    "DA_Number",
    "Detail_URL",
    "Description",
    "Submitted_Date",
    "Decision",
    "Categories",
    "Property_Address",
    "Applicant",
    "Progress",
    "Fees",
    "Documents",
    "Contact_Council"
]

# =========================     ♦
# STEP 7: SAVE CSV
# =========================
with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
     writer = csv.writer(f)
     writer.writerow(headers)
     writer.writerows(data)

driver.quit()

print(f"Finished. {len(data)} records saved to {CSV_FILE}")