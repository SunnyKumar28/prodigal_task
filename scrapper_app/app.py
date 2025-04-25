import os
import random
import time
import re
import json
import logging
from datetime import datetime
from typing import List, Type, Dict, Any
from urllib.parse import urlparse

import pandas as pd
from bs4 import BeautifulSoup
from pydantic import BaseModel, create_model
import html2text
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from groq import Groq

# Configuration constants
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
]

HEADLESS_OPTIONS = [
    "--disable-gpu",
    "--disable-dev-shm-usage",
    "--window-size=1920,1080",
    "--disable-search-engine-choice-screen",
    "--disable-blink-features=AutomationControlled",
]

# Improved system message for better extraction
SYSTEM_MESSAGE = """
You are an intelligent text extraction specialist. Your task is to carefully extract structured information 
from the provided web page content and return it in JSON format.

The content comes from government scheme websites. For each scheme, extract the following information:
- Scheme Name: The official name of the scheme
- Ministries/Departments: The ministry or department that runs the scheme
- Target Beneficiaries: Who the scheme is designed to help
- Eligibility Criteria: Requirements to qualify for the scheme
- Description & Benefits: What the scheme provides and its benefits
- Application Process: How to apply for the scheme
- Tags: Keywords related to the scheme

IMPORTANT: 
1. Extract exactly ONE scheme per URL
2. Use NULL for any field you cannot find information about
3. The output MUST be valid JSON with only the extracted data
4. Be concise but thorough in your extraction
5. Extract ALL relevant information for each field

Your output must follow this exact JSON structure:
{
  "listings": [
    {
      "Scheme Name": "extracted name",
      "Ministries/Departments": "extracted ministry",
      "Target Beneficiaries": "extracted beneficiaries",
      "Eligibility Criteria": "extracted criteria",
      "Description & Benefits": "extracted description",
      "Application Process": "extracted process",
      "Tags": "extracted tags"
    }
  ]
}
"""

USER_MESSAGE = "Extract the following information from this government scheme webpage content:\n\n"
MODEL_NAME = "llama-3.1-70b-versatile"
OUTPUT_FOLDER = "output"
MAX_SCROLLS = 5  # Increased to capture more content
PAGE_LOAD_TIMEOUT = 30
MAX_RETRIES = 3  # Number of retries for API calls

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("scraper.log"),
        logging.StreamHandler(),
    ],
)

def setup_selenium() -> webdriver.Chrome:
    """Configure Selenium WebDriver with random user agent and headless options."""
    options = Options()
    options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")
    for option in HEADLESS_OPTIONS:
        options.add_argument(option)
    options.page_load_timeout = PAGE_LOAD_TIMEOUT
    return webdriver.Chrome(options=options)

def click_cookie_consent(driver: webdriver.Chrome):
    """Attempt to click a cookie consent button if present."""
    try:
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        consent_patterns = ["accept", "agree", "allow", "consent", "continue", "ok", "got it"]
        for pattern in consent_patterns:
            for tag in ["button", "a", "div"]:
                elements = driver.find_elements(
                    By.XPATH,
                    f"//{tag}[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{pattern}')]",
                )
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        element.click()
                        logging.info(f"Clicked '{pattern}' cookie consent button")
                        time.sleep(2)
                        return
        logging.info("No cookie consent button found")
    except Exception as e:
        logging.warning(f"Error handling cookie consent: {e}")

def fetch_html_selenium(url: str) -> str:
    """Fetch HTML content from a URL using Selenium with human-like behavior."""
    driver = setup_selenium()
    try:
        logging.info(f"Fetching URL: {url}")
        driver.get(url)
        time.sleep(3)  # Increased wait time for page load
        driver.maximize_window()
        click_cookie_consent(driver)

        # Scroll to load dynamic content
        last_height = driver.execute_script("return document.body.scrollHeight")
        for i in range(MAX_SCROLLS):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                logging.info(f"Stopped scrolling after {i+1} scrolls: no new content")
                break
            last_height = new_height

        # Wait for main content to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "main"))
        )
        
        return driver.page_source
    except Exception as e:
        logging.error(f"Error fetching {url}: {e}")
        return ""
    finally:
        driver.quit()

def clean_html(html_content: str) -> str:
    """Remove headers, footers, scripts, and styles from HTML but keep main content."""
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        
        # Try to focus on main content (improved targeting)
        main_content = soup.find("main") or soup.find(id=re.compile("content|main", re.I)) or soup.find(class_=re.compile("content|main", re.I))
        
        # If found main content, use it instead of the whole page
        if main_content:
            return str(main_content)
            
        # Otherwise clean the whole page
        for element in soup.find_all(["script", "style", "nav", "footer"]):
            element.decompose()
        
        return str(soup)
    except Exception as e:
        logging.error(f"Error cleaning HTML: {e}")
        return html_content

def remove_urls(text: str) -> str:
    """Remove URLs from text using regex."""
    url_pattern = r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
    return re.sub(url_pattern, "", text)

def html_to_markdown(html_content: str) -> str:
    """Convert cleaned HTML to markdown and remove URLs."""
    if not html_content:
        return ""
    cleaned_html = clean_html(html_content)
    converter = html2text.HTML2Text()
    converter.ignore_links = False  # Keep links for context
    converter.ignore_images = True
    converter.body_width = 0  # Don't wrap text
    markdown = converter.handle(cleaned_html)
    
    # Some basic cleaning to improve readability
    markdown = re.sub(r'\n{3,}', '\n\n', markdown)  # Remove excessive newlines
    markdown = remove_urls(markdown)
    
    return markdown

def extract_data_from_model(markdown: str, fields: List[str], url: str) -> Dict[str, Any]:
    """Extract structured data from markdown using Groq's API with error handling and retry logic."""
    if not markdown:
        logging.warning("No markdown content to extract data from")
        return {"listings": []}
        
    retries = 0
    
    # Replace the decommissioned model with a current one
    current_model = "llama3-70b-8192"  # Updated to a currently available Groq model
    
    while retries < MAX_RETRIES:
        try:
            # Trim content if too long (model context limits)
            if len(markdown) > 24000:
                logging.info(f"Trimming content from {len(markdown)} to 24000 characters")
                markdown = markdown[:24000]
            
            # Prepare user message with URL for context
            user_content = f"{USER_MESSAGE}\nURL: {url}\n\nPage content:\n{markdown}"
            
            client = Groq(api_key="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")
            
            # Add temperature and retry
            completion = client.chat.completions.create(
                model=current_model,  # Using updated model
                messages=[
                    {"role": "system", "content": SYSTEM_MESSAGE},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.2,  # Lower temperature for more consistent outputs
                max_tokens=2048,   # Ensure enough tokens for response
            )

            response_content = completion.choices[0].message.content
            
            # Debug the raw response
            logging.info(f"Raw model response: {response_content[:200]}...")
            
            # Try to extract JSON from the response (handle cases where there's text before/after JSON)
            json_match = re.search(r'({[\s\S]*})', response_content)
            if json_match:
                response_content = json_match.group(1)
            
            # Parse the JSON response
            parsed_response = json.loads(response_content)
            
            # Validate the response structure
            if "listings" not in parsed_response:
                parsed_response = {"listings": [parsed_response]}
                
            # If listings is empty but we have data outside, fix structure
            if not parsed_response["listings"] and len(parsed_response.keys()) > 1:
                # Move top-level fields into a listing
                listing = {k: v for k, v in parsed_response.items() if k != "listings"}
                parsed_response = {"listings": [listing]}
                
            # Make sure listings contains all expected fields
            for listing in parsed_response["listings"]:
                for field in fields:
                    if field not in listing:
                        listing[field] = None
                
                # Add source URL to each listing
                listing["URL"] = url
                
            return parsed_response
            
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON response from model: {e}")
            retries += 1
            if retries < MAX_RETRIES:
                logging.info(f"Retrying extraction ({retries}/{MAX_RETRIES})...")
                time.sleep(2)
            
        except Exception as e:
            logging.error(f"Error extracting data: {e}")
            retries += 1
            if retries < MAX_RETRIES:
                logging.info(f"Retrying extraction ({retries}/{MAX_RETRIES})...")
                time.sleep(2)
    
    # If all retries failed, return empty listings
    logging.warning("All extraction attempts failed")
    return {"listings": []}

def save_data(data: dict, timestamp: str, url: str = "combined") -> None:
    """Save extracted data to JSON and CSV files."""
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    filename = f"data_{timestamp}_{urlparse(url).netloc if url != 'combined' else 'combined'}"

    # Save JSON
    json_path = os.path.join(OUTPUT_FOLDER, f"{filename}.json")
    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        logging.info(f"Saved JSON to {json_path}")
    except Exception as e:
        logging.error(f"Error saving JSON to {json_path}: {e}")

    # Save CSV
    listings = data.get("listings", [])
    if listings:
        try:
            df = pd.DataFrame(listings)
            csv_path = os.path.join(OUTPUT_FOLDER, f"{filename}.csv")
            df.to_csv(csv_path, index=False)
            logging.info(f"Saved CSV to {csv_path}")
        except Exception as e:
            logging.error(f"Error saving CSV to {csv_path}: {e}")
    else:
        logging.warning(f"No data to save for {url}")

def scrape_urls(urls: List[str], fields: List[str]) -> None:
    """Scrape multiple URLs, extract fields, and save results."""
    if not urls or not fields:
        logging.error("URLs and fields must not be empty")
        return

    all_data = {"listings": []}
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    for i, url in enumerate(urls):
        url = url.strip()
        if not url:
            logging.warning(f"Skipping empty URL at index {i}")
            continue

        logging.info(f"Processing URL {i+1}/{len(urls)}: {url}")

        # Fetch and process HTML
        html = fetch_html_selenium(url)
        if not html:
            logging.warning(f"No HTML content retrieved for {url}")
            continue

        markdown = html_to_markdown(html)

        # Save raw markdown for debugging
        raw_path = os.path.join(OUTPUT_FOLDER, f"raw_{timestamp}_{i}.md")
        try:
            with open(raw_path, "w", encoding="utf-8") as f:
                f.write(markdown)
            logging.info(f"Saved raw markdown to {raw_path}")
        except Exception as e:
            logging.error(f"Error saving raw markdown to {raw_path}: {e}")

        # Extract data using the improved extraction function
        data = extract_data_from_model(markdown, fields, url)
        save_data(data, timestamp, url)
        all_data["listings"].extend(data.get("listings", []))

        # Random delay between requests to avoid overloading servers
        if i < len(urls) - 1:
            delay = random.uniform(2, 5)
            time.sleep(delay)

    # Save combined data
    if all_data["listings"]:
        save_data(all_data, timestamp)
        logging.info(f"All URLs processed successfully. Extracted {len(all_data['listings'])} listings.")
    else:
        logging.warning("No data extracted from any URL")

if __name__ == "__main__":
    # Example usage
    urls = [
                    "https://www.myscheme.gov.in/schemes/ghcsscp",
        "https://www.myscheme.gov.in/schemes/dfhsscoebc",
        "https://www.myscheme.gov.in/schemes/gmgmach",
        "https://www.myscheme.gov.in/schemes/fampscb",
        "https://www.myscheme.gov.in/schemes/mvpy-bihar",
        "https://www.myscheme.gov.in/schemes/scasc",
        "https://www.myscheme.gov.in/schemes/pfeslpbtac",
        "https://www.myscheme.gov.in/schemes/mssp-vm",
        "https://www.myscheme.gov.in/schemes/sssvpy",
        "https://www.myscheme.gov.in/schemes/nsskvy",
        "https://www.myscheme.gov.in/schemes/famdpwog",
        "https://www.myscheme.gov.in/schemes/ignvpy",
        "https://www.myscheme.gov.in/schemes/hiip",
        "https://www.myscheme.gov.in/schemes/cmst",
        "https://www.myscheme.gov.in/schemes/cmfm",
        "https://www.myscheme.gov.in/schemes/apepc",
        "https://www.myscheme.gov.in/schemes/ssyc",
        "https://www.myscheme.gov.in/schemes/ssst-pts",
        "https://www.myscheme.gov.in/schemes/lpsup",
        "https://www.myscheme.gov.in/schemes/fagh",
        "https://www.myscheme.gov.in/schemes/amcsy",
        "https://www.myscheme.gov.in/schemes/alsias",
        "https://www.myscheme.gov.in/schemes/aelss",
        "https://www.myscheme.gov.in/schemes/thayi-bhagya",
        "https://www.myscheme.gov.in/schemes/dbsapbandocwwb",
        "https://www.myscheme.gov.in/schemes/sscssgi",
        "https://www.myscheme.gov.in/schemes/scpmsc",
        "https://www.myscheme.gov.in/schemes/faisbscbc",
        "https://www.myscheme.gov.in/schemes/cm-swaniyojan-yojana",
        "https://www.myscheme.gov.in/schemes/km",
        "https://www.myscheme.gov.in/schemes/fsppv",
        "https://www.myscheme.gov.in/schemes/favia",
        "https://www.myscheme.gov.in/schemes/sdfrs",
        "https://www.myscheme.gov.in/schemes/issfb",
        "https://www.myscheme.gov.in/schemes/casscsppnjg",
        "https://www.myscheme.gov.in/schemes/ak",
        "https://www.myscheme.gov.in/schemes/nsmedsy",
        "https://www.myscheme.gov.in/schemes/spytis-ii",
        "https://www.myscheme.gov.in/schemes/sdps",
        "https://www.myscheme.gov.in/schemes/mabay",
        "https://www.myscheme.gov.in/schemes/haps",
        "https://www.myscheme.gov.in/schemes/as-fadw",
        "https://www.myscheme.gov.in/schemes/awvsssi",
        "https://www.myscheme.gov.in/schemes/sskerala",
        "https://www.myscheme.gov.in/schemes/gs-west-bengal",
        "https://www.myscheme.gov.in/schemes/gtvtswsawwws",
        "https://www.myscheme.gov.in/schemes/mnssy",
        "https://www.myscheme.gov.in/schemes/sspmphmrp",
        "https://www.myscheme.gov.in/schemes/suurg",
        "https://www.myscheme.gov.in/schemes/skksbpa",
        "https://www.myscheme.gov.in/schemes/jms-11and12",
        "https://www.myscheme.gov.in/schemes/mrf",
        "https://www.myscheme.gov.in/schemes/jav",
        "https://www.myscheme.gov.in/schemes/aks",
        "https://www.myscheme.gov.in/schemes/sssghid",
        "https://www.myscheme.gov.in/schemes/dp-cmsguy",
        "https://www.myscheme.gov.in/schemes/fseg",
        "https://www.myscheme.gov.in/schemes/dbhs-2bhks",
        "https://www.myscheme.gov.in/schemes/cmdps-sikkim",
        "https://www.myscheme.gov.in/schemes/rcmrf-aa",
        "https://www.myscheme.gov.in/schemes/ysrln",
        "https://www.myscheme.gov.in/schemes/stiti",
        "https://www.myscheme.gov.in/schemes/py-jbocwwb",
        "https://www.myscheme.gov.in/schemes/wbrupashree",
        "https://www.myscheme.gov.in/schemes/bas",
        "https://www.myscheme.gov.in/schemes/fss",
        "https://www.myscheme.gov.in/schemes/fasuccu",
        "https://www.myscheme.gov.in/schemes/iwr",
        "https://www.myscheme.gov.in/schemes/isds",
        "https://www.myscheme.gov.in/schemes/eacp",
        "https://www.myscheme.gov.in/schemes/dbsheo",
        "https://www.myscheme.gov.in/schemes/skpsy",
        "https://www.myscheme.gov.in/schemes/dan",
        "https://www.myscheme.gov.in/schemes/a-pudu",
        "https://www.myscheme.gov.in/schemes/rrsdmsmecpu",
        "https://www.myscheme.gov.in/schemes/fapfpfoobm",
        "https://www.myscheme.gov.in/schemes/fatpomo2t5ffttfc",
        "https://www.myscheme.gov.in/schemes/spfappbga",
        "https://www.myscheme.gov.in/schemes/peacetp",
        "https://www.myscheme.gov.in/schemes/gifogc-fp",
        "https://www.myscheme.gov.in/schemes/faddbcbocwwb",
        "https://www.myscheme.gov.in/schemes/mmky-fanben",
        "https://www.myscheme.gov.in/schemes/bsy-pudu",
        "https://www.myscheme.gov.in/schemes/dbabocwwb",
        "https://www.myscheme.gov.in/schemes/vds",
        "https://www.myscheme.gov.in/schemes/fdbcsc",
        "https://www.myscheme.gov.in/schemes/caabocwwb",
        "https://www.myscheme.gov.in/schemes/svnspy",
        "https://www.myscheme.gov.in/schemes/sawh",
        "https://www.myscheme.gov.in/schemes/hmneh",
        "https://www.myscheme.gov.in/schemes/ssddap-pudu",
        "https://www.myscheme.gov.in/schemes/phms",
        "https://www.myscheme.gov.in/schemes/spadap",
        "https://www.myscheme.gov.in/schemes/rctpm",
        "https://www.myscheme.gov.in/schemes/arsls",
        "https://www.myscheme.gov.in/schemes/bhausaheb-fundkar-horticulture-plantataion-scheme",
        "https://www.myscheme.gov.in/schemes/sreehispshecioutp",
        "https://www.myscheme.gov.in/schemes/camvisoftrslshe",
        "https://www.myscheme.gov.in/schemes/mgtocpp",
        "https://www.myscheme.gov.in/schemes/oms",
        "https://www.myscheme.gov.in/schemes/ticcotdocs",
        "https://www.myscheme.gov.in/schemes/aius",
        "https://www.myscheme.gov.in/schemes/opetfesime-mp",
        "https://www.myscheme.gov.in/schemes/edp-dc",
        "https://www.myscheme.gov.in/schemes/gssa-ds",
        "https://www.myscheme.gov.in/schemes/gmmacl-dc",
        "https://www.myscheme.gov.in/schemes/aniadws",
        "https://www.myscheme.gov.in/schemes/srmp",
        "https://www.myscheme.gov.in/schemes/anioaas",
        "https://www.myscheme.gov.in/schemes/easppsccwrmbocwwb",
        "https://www.myscheme.gov.in/schemes/ddanwrasi",
        "https://www.myscheme.gov.in/schemes/nsklvrpbkpy",
        "https://www.myscheme.gov.in/schemes/atnmasfogi",
        "https://www.myscheme.gov.in/schemes/cmgcpsi",
        "https://www.myscheme.gov.in/schemes/atnmasfogii",
        "https://www.myscheme.gov.in/schemes/fmtsfpwd",
        "https://www.myscheme.gov.in/schemes/petro-subsidy-for-disabled",
        "https://www.myscheme.gov.in/schemes/spy-gbocwwb",
        "https://www.myscheme.gov.in/schemes/ei-mesifai",
        "https://www.myscheme.gov.in/schemes/msdsuyps",
        "https://www.myscheme.gov.in/schemes/sndaygbocwwb",
        "https://www.myscheme.gov.in/schemes/dmrnicmasii",
        "https://www.myscheme.gov.in/schemes/mvyspy",
        "https://www.myscheme.gov.in/schemes/mbbsgbocwwb",
        "https://www.myscheme.gov.in/schemes/vcsgbocwwb",
        "https://www.myscheme.gov.in/schemes/mvspy",
        "https://www.myscheme.gov.in/schemes/hssgbocwwb",
        "https://www.myscheme.gov.in/schemes/masglwb",
        "https://www.myscheme.gov.in/schemes/soefmgttfotdfa",
        "https://www.myscheme.gov.in/schemes/smts-glwb",
        "https://www.myscheme.gov.in/schemes/lpas-glwb",
        "https://www.myscheme.gov.in/schemes/sfpbttjp",
        "https://www.myscheme.gov.in/schemes/sfmcas-glwb",
        "https://www.myscheme.gov.in/schemes/gefm-mesifai-sa-msme",
        "https://www.myscheme.gov.in/schemes/otcild-sw",
        "https://www.myscheme.gov.in/schemes/mefarsi",
        "https://www.myscheme.gov.in/schemes/thrgrr-sw",
        "https://www.myscheme.gov.in/schemes/soefatfatftpomic",
        "https://www.myscheme.gov.in/schemes/soetya",
        "https://www.myscheme.gov.in/schemes/mlgs",
        "https://www.myscheme.gov.in/schemes/dr",
        "https://www.myscheme.gov.in/schemes/kt",
        "https://www.myscheme.gov.in/schemes/dpgsslampgdsc",
        "https://www.myscheme.gov.in/schemes/iasirfa-sw",
        "https://www.myscheme.gov.in/schemes/iocfortc",
        "https://www.myscheme.gov.in/schemes/sa-affdf",
        "https://www.myscheme.gov.in/schemes/socka",
        "https://www.myscheme.gov.in/schemes/oapc",
        "https://www.myscheme.gov.in/schemes/abn",
        "https://www.myscheme.gov.in/schemes/gfasgciwes1t4ssosu",
        "https://www.myscheme.gov.in/schemes/faspalscf",
        "https://www.myscheme.gov.in/schemes/apch-gbocwwb",
        "https://www.myscheme.gov.in/schemes/fmtaspsstc",
        "https://www.myscheme.gov.in/schemes/rhsmas",
        "https://www.myscheme.gov.in/schemes/mvspkdpy",
        "https://www.myscheme.gov.in/schemes/himayat",
        "https://www.myscheme.gov.in/schemes/apdccsifdsgc",
        "https://www.myscheme.gov.in/schemes/apdccsscspscc",
        "https://www.myscheme.gov.in/schemes/pdca",
        "https://www.myscheme.gov.in/schemes/tpa",
        "https://www.myscheme.gov.in/schemes/gnc",
        "https://www.myscheme.gov.in/schemes/absy",
        "https://www.myscheme.gov.in/schemes/obcpms",
        "https://www.myscheme.gov.in/schemes/amcmcy",
        "https://www.myscheme.gov.in/schemes/paapwd",
        "https://www.myscheme.gov.in/schemes/lcta",
        "https://www.myscheme.gov.in/schemes/sss-gujarat",
        "https://www.myscheme.gov.in/schemes/pmcup",
        "https://www.myscheme.gov.in/schemes/pb-gbocwwb",
        "https://www.myscheme.gov.in/schemes/ftstbdp",
        # "https://www.myscheme.gov.in/schemes/uatdap",
        # "https://www.myscheme.gov.in/schemes/sgpbj",
        # "https://www.myscheme.gov.in/schemes/matnpmsahip",
        # "https://www.myscheme.gov.in/schemes/eapfdap",
        # "https://www.myscheme.gov.in/schemes/ciwesm-as",
        # "https://www.myscheme.gov.in/schemes/mswcfpawcp",
        # "https://www.myscheme.gov.in/schemes/afm",
        # "https://www.myscheme.gov.in/schemes/ksp",
        # "https://www.myscheme.gov.in/schemes/ndacw",
        # "https://www.myscheme.gov.in/schemes/famtw",
        # "https://www.myscheme.gov.in/schemes/matdapmdap",
        # "https://www.myscheme.gov.in/schemes/wbmwwsad",
        # "https://www.myscheme.gov.in/schemes/bis",
        # "https://www.myscheme.gov.in/schemes/darw-hbocwwb",
        # "https://www.myscheme.gov.in/schemes/bmsmeps",
        # "https://www.myscheme.gov.in/schemes/spfhavip",
        # "https://www.myscheme.gov.in/schemes/gpt-hbocwwb",
        # "https://www.myscheme.gov.in/schemes/bbtbdftwodap",
        # "https://www.myscheme.gov.in/schemes/gbwodapd",
        # "https://www.myscheme.gov.in/schemes/bmsmesccs",
        # "https://www.myscheme.gov.in/schemes/fatngo",
        # "https://www.myscheme.gov.in/schemes/eicccpsrtcctd",
        # "https://www.myscheme.gov.in/schemes/mnskbhncsy",
        # "https://www.myscheme.gov.in/schemes/dhausy",
        # "https://www.myscheme.gov.in/schemes/fasmrwwhbocwwb",
        # "https://www.myscheme.gov.in/schemes/fahmhawd-hlwb",
        # "https://www.myscheme.gov.in/schemes/fahfptihbocwwb",
        # "https://www.myscheme.gov.in/schemes/wbafbsgics",
        # "https://www.myscheme.gov.in/schemes/fawgav",
        # "https://www.myscheme.gov.in/schemes/fac-hlwb",
        # "https://www.myscheme.gov.in/schemes/jfbf",
        # "https://www.myscheme.gov.in/schemes/pfjf",
        # "https://www.myscheme.gov.in/schemes/ddaps",
        # "https://www.myscheme.gov.in/schemes/dalps",
        # "https://www.myscheme.gov.in/schemes/wbafbssdm",
        # "https://www.myscheme.gov.in/schemes/hppky",
        # "https://www.myscheme.gov.in/schemes/catn",
        # "https://www.myscheme.gov.in/schemes/ssyh",
        # "https://www.myscheme.gov.in/schemes/ismpsswcec",
        # "https://www.myscheme.gov.in/schemes/ismpswfwa",
        # "https://www.myscheme.gov.in/schemes/ismpsistl",
        # "https://www.myscheme.gov.in/schemes/ismpsscis",
        # "https://www.myscheme.gov.in/schemes/sfaddta",
        # "https://www.myscheme.gov.in/schemes/mssavsy-haryana",
        # "https://www.myscheme.gov.in/schemes/oah",
        # "https://www.myscheme.gov.in/schemes/speoepsgugmmapuy",
        # "https://www.myscheme.gov.in/schemes/scdicmd",
        # "https://www.myscheme.gov.in/schemes/seh-tmdummapuy",
        # "https://www.myscheme.gov.in/schemes/bsjis",
        # "https://www.myscheme.gov.in/schemes/atmtrmr",
        # "https://www.myscheme.gov.in/schemes/sebpummapuy",
        # "https://www.myscheme.gov.in/schemes/aapd",
        # "https://www.myscheme.gov.in/schemes/siupd",
        # "https://www.myscheme.gov.in/schemes/gsfmoddw",
        # "https://www.myscheme.gov.in/schemes/cels-s",
        # "https://www.myscheme.gov.in/schemes/cmses",
        # "https://www.myscheme.gov.in/schemes/fawdsddaw",
        # "https://www.myscheme.gov.in/schemes/mukuy",
        # "https://www.myscheme.gov.in/schemes/udps",
        # "https://www.myscheme.gov.in/schemes/solap",
        # "https://www.myscheme.gov.in/schemes/jbcmcshsfdc",
        # "https://www.myscheme.gov.in/schemes/tbsshsfdc",
        # "https://www.myscheme.gov.in/schemes/sotooc",
        # "https://www.myscheme.gov.in/schemes/srshsfdc",
        # "https://www.myscheme.gov.in/schemes/sdpvc",
        # "https://www.myscheme.gov.in/schemes/sasss",
        # "https://www.myscheme.gov.in/schemes/sstsc",
        # "https://www.myscheme.gov.in/schemes/apdemnc",
        # "https://www.myscheme.gov.in/schemes/e-ggdcapfp",
        # "https://www.myscheme.gov.in/schemes/sys",
        # "https://www.myscheme.gov.in/schemes/wbisaige",
        # "https://www.myscheme.gov.in/schemes/wbisistl",
        # "https://www.myscheme.gov.in/schemes/pbftcw",
        # "https://www.myscheme.gov.in/schemes/wbissqi",
        # "https://www.myscheme.gov.in/schemes/wbiswed",
        # "https://www.myscheme.gov.in/schemes/mgmdwdesmd",
        # "https://www.myscheme.gov.in/schemes/fappesm",
        # "https://www.myscheme.gov.in/schemes/adc",
        # "https://www.myscheme.gov.in/schemes/mgwwdesm",
        # "https://www.myscheme.gov.in/schemes/bse-pg",
        # "https://www.myscheme.gov.in/schemes/bse-g",
        # "https://www.myscheme.gov.in/schemes/sfg",
        # "https://www.myscheme.gov.in/schemes/sgscs",
        # "https://www.myscheme.gov.in/schemes/isssppcp",
        # "https://www.myscheme.gov.in/schemes/gpcs",
        # "https://www.myscheme.gov.in/schemes/bpsabcpsg",
        # "https://www.myscheme.gov.in/schemes/cohaftcw",
        # "https://www.myscheme.gov.in/schemes/mbwb",
        # "https://www.myscheme.gov.in/schemes/ostf",
        # "https://www.myscheme.gov.in/schemes/estascs",
        # "https://www.myscheme.gov.in/schemes/kspyscg",
        # "https://www.myscheme.gov.in/schemes/cds",
        # "https://www.myscheme.gov.in/schemes/acaobocwwb",
        # "https://www.myscheme.gov.in/schemes/ntkjky",
        # "https://www.myscheme.gov.in/schemes/affeobocwwb",
        # "https://www.myscheme.gov.in/schemes/maobocwwb",
        # "https://www.myscheme.gov.in/schemes/mmmy",
        # "https://www.myscheme.gov.in/schemes/djkis",
        # "https://www.myscheme.gov.in/schemes/sflvisgpg",
        # "https://www.myscheme.gov.in/schemes/dfbsscsts",
        # "https://www.myscheme.gov.in/schemes/sfcssuds",
        # "https://www.myscheme.gov.in/schemes/mbpy",
        # "https://www.myscheme.gov.in/schemes/afpobbocwwb",
        # "https://www.myscheme.gov.in/schemes/mmny",
        # "https://www.myscheme.gov.in/schemes/sfmb",
        # "https://www.myscheme.gov.in/schemes/mmkvymp",
        # "https://www.myscheme.gov.in/schemes/bbsa",
        # "https://www.myscheme.gov.in/schemes/sppms",
        # "https://www.myscheme.gov.in/schemes/hpmvssp",
        # "https://www.myscheme.gov.in/schemes/mbs-t",
        # "https://www.myscheme.gov.in/schemes/gittpwd",
        # "https://www.myscheme.gov.in/schemes/satptc",
        # "https://www.myscheme.gov.in/schemes/nfaschh",
        # "https://www.myscheme.gov.in/schemes/slstt",
        # "https://www.myscheme.gov.in/schemes/cmpsmp",
        # "https://www.myscheme.gov.in/schemes/ignwpschh",
        # "https://www.myscheme.gov.in/schemes/igndpsb",
        # "https://www.myscheme.gov.in/schemes/gsspbocwwb",
        # "https://www.myscheme.gov.in/schemes/ks",
        # "https://www.myscheme.gov.in/schemes/mlsp",
        # "https://www.myscheme.gov.in/schemes/copkbocwwb",
        # "https://www.myscheme.gov.in/schemes/dbhchh",
        # "https://www.myscheme.gov.in/schemes/fp",
        # "https://www.myscheme.gov.in/schemes/docsos",
        # "https://www.myscheme.gov.in/schemes/fig",
        # "https://www.myscheme.gov.in/schemes/mmssy",
        # "https://www.myscheme.gov.in/schemes/dor",
        # "https://www.myscheme.gov.in/schemes/mns",
        # "https://www.myscheme.gov.in/schemes/mmajeajcspy",
        # "https://www.myscheme.gov.in/schemes/ddssy",
        # "https://www.myscheme.gov.in/schemes/sagb",
        # "https://www.myscheme.gov.in/schemes/gptbbocwwb",
        # "https://www.myscheme.gov.in/schemes/grhbbocwwb",
        # "https://www.myscheme.gov.in/schemes/obdopmtig",
        # "https://www.myscheme.gov.in/schemes/obdtdaattnau",
        # "https://www.myscheme.gov.in/schemes/pcwfstfpi",
        # "https://www.myscheme.gov.in/schemes/bsmssy",
        # "https://www.myscheme.gov.in/schemes/ptwadw",
        # "https://www.myscheme.gov.in/schemes/cmacs",
        # "https://www.myscheme.gov.in/schemes/sprcddrbw",
        # "https://www.myscheme.gov.in/schemes/paloadbocw",
        # "https://www.myscheme.gov.in/schemes/adtwdiap",
        # "https://www.myscheme.gov.in/schemes/sdtk",
        # "https://www.myscheme.gov.in/schemes/smsopm",
        # "https://www.myscheme.gov.in/schemes/sftfe",
        # "https://www.myscheme.gov.in/schemes/qpsd",
        # "https://www.myscheme.gov.in/schemes/stkk",
        # "https://www.myscheme.gov.in/schemes/adtwip",
        # "https://www.myscheme.gov.in/schemes/adtwstb",
        # "https://www.myscheme.gov.in/schemes/aspie",
        # "https://www.myscheme.gov.in/schemes/ahtn",
        # "https://www.myscheme.gov.in/schemes/subhadra",
        # "https://www.myscheme.gov.in/schemes/wicohppdjkbocwwb",
        # "https://www.myscheme.gov.in/schemes/lach",
        # "https://www.myscheme.gov.in/schemes/fesfpc",
        # "https://www.myscheme.gov.in/schemes/fesftydpc",
        # "https://www.myscheme.gov.in/schemes/rgis",
        # "https://www.myscheme.gov.in/schemes/pamatn",
        # "https://www.myscheme.gov.in/schemes/eafdc",
        # "https://www.myscheme.gov.in/schemes/eacrws11a12s",
        # "https://www.myscheme.gov.in/schemes/fafmjkbocwwb",
        # "https://www.myscheme.gov.in/schemes/pcardah",
        # "https://www.myscheme.gov.in/schemes/dccbssi",
        # "https://www.myscheme.gov.in/schemes/pfjkbocwwb",
        # "https://www.myscheme.gov.in/schemes/lsmpcltt",
        # "https://www.myscheme.gov.in/schemes/fes",
        # "https://www.myscheme.gov.in/schemes/pcardsia",
        # "https://www.myscheme.gov.in/schemes/pcardbif",
        # "https://www.myscheme.gov.in/schemes/akckvy",
        # "https://www.myscheme.gov.in/schemes/pcardbpt",
        # "https://www.myscheme.gov.in/schemes/nfasmp",
        # "https://www.myscheme.gov.in/schemes/iftdcmtst",
        # "https://www.myscheme.gov.in/schemes/nfbsm",
        # "https://www.myscheme.gov.in/schemes/wbtwssadpd",
        # "https://www.myscheme.gov.in/schemes/wbtwssfp",
        # "https://www.myscheme.gov.in/schemes/mkvb",
        # "https://www.myscheme.gov.in/schemes/cmbkyii",
        # "https://www.myscheme.gov.in/schemes/wbtwssp",
        # "https://www.myscheme.gov.in/schemes/excel",
        # "https://www.myscheme.gov.in/schemes/cvyb",
        # "https://www.myscheme.gov.in/schemes/blifrsa",
        # "https://www.myscheme.gov.in/schemes/mvpmeuy",
        # "https://www.myscheme.gov.in/schemes/pmcssc",
        # "https://www.myscheme.gov.in/schemes/csc",
        # "https://www.myscheme.gov.in/schemes/bsakai",
        # "https://www.myscheme.gov.in/schemes/bsaktpd",
        # "https://www.myscheme.gov.in/schemes/mbspy",
        # "https://www.myscheme.gov.in/schemes/wbtwsaps",
        # "https://www.myscheme.gov.in/schemes/cbpiaiscs",
        # "https://www.myscheme.gov.in/schemes/wbtwsfe",
        # "https://www.myscheme.gov.in/schemes/mgpy",
        # "https://www.myscheme.gov.in/schemes/aasgsmse",
        # "https://www.myscheme.gov.in/schemes/jpspn2019",
        # "https://www.myscheme.gov.in/schemes/jrpsbyn2021",
        # "https://www.myscheme.gov.in/schemes/jsstpmss",
        # "https://www.myscheme.gov.in/schemes/v-vhcs",
        # "https://www.myscheme.gov.in/schemes/jsscpmss-1",
        # "https://www.myscheme.gov.in/schemes/ooscs",
        # "https://www.myscheme.gov.in/schemes/jbsyb",
        # "https://www.myscheme.gov.in/schemes/majvpvpy",
        # "https://www.myscheme.gov.in/schemes/masabsn",
        # "https://www.myscheme.gov.in/schemes/podbhpbocwwb",
        # "https://www.myscheme.gov.in/schemes/afsispscupsce",
        # "https://www.myscheme.gov.in/schemes/pbhpbocwwb",
        # "https://www.myscheme.gov.in/schemes/mbhpbocwwb",
        # "https://www.myscheme.gov.in/schemes/kdscs",
        # "https://www.myscheme.gov.in/schemes/hnss",
        # "https://www.myscheme.gov.in/schemes/mksybb",
        # "https://www.myscheme.gov.in/schemes/gssby",
        # "https://www.myscheme.gov.in/schemes/spksy",
        # "https://www.myscheme.gov.in/schemes/pby",
        # "https://www.myscheme.gov.in/schemes/gtiar",
        # "https://www.myscheme.gov.in/schemes/cmhisn",
        # "https://www.myscheme.gov.in/schemes/spss",
        # "https://www.myscheme.gov.in/schemes/ma",
        # "https://www.myscheme.gov.in/schemes/mssg",
        # "https://www.myscheme.gov.in/schemes/beispgccpts",
        # "https://www.myscheme.gov.in/schemes/agsmais",
        # "https://www.myscheme.gov.in/schemes/pdycmfss",
        # "https://www.myscheme.gov.in/schemes/agsmnsgst",
        # "https://www.myscheme.gov.in/schemes/agmsmercgt",
        # "https://www.myscheme.gov.in/schemes/gsrfas",
        # "https://www.myscheme.gov.in/schemes/agfst",
        # "https://www.myscheme.gov.in/schemes/saepaep",
        # "https://www.myscheme.gov.in/schemes/sfailfcs",
        # "https://www.myscheme.gov.in/schemes/sdsj",
        # "https://www.myscheme.gov.in/schemes/toaifse",
        # "https://www.myscheme.gov.in/schemes/mmsfs",
        # "https://www.myscheme.gov.in/schemes/cmhr",
        # "https://www.myscheme.gov.in/schemes/caicoloabfabfa",
        # "https://www.myscheme.gov.in/schemes/lsmsscst",
        # "https://www.myscheme.gov.in/schemes/sfmstsa",
        # "https://www.myscheme.gov.in/schemes/sfasisd",
        # "https://www.myscheme.gov.in/schemes/fcbghpbocwwb",
        # "https://www.myscheme.gov.in/schemes/faitfci",
        # "https://www.myscheme.gov.in/schemes/faitsd",
        # "https://www.myscheme.gov.in/schemes/sfalp",
        # "https://www.myscheme.gov.in/schemes/isicsch",
        # "https://www.myscheme.gov.in/schemes/ferts",
        # "https://www.myscheme.gov.in/schemes/idp-u",
        # "https://www.myscheme.gov.in/schemes/iwp-andhra",
        # "https://www.myscheme.gov.in/schemes/setcmsuc",
        # "https://www.myscheme.gov.in/schemes/smsuggs",
        # "https://www.myscheme.gov.in/schemes/ssgff",
        # "https://www.myscheme.gov.in/schemes/ioap-u",
        # "https://www.myscheme.gov.in/schemes/gsfiicps",
        # "https://www.myscheme.gov.in/schemes/samsmeis",
        # "https://www.myscheme.gov.in/schemes/jmsy",
        # "https://www.myscheme.gov.in/schemes/bauuyseat",
        # "https://www.myscheme.gov.in/schemes/gms",
        # "https://www.myscheme.gov.in/schemes/bauuyata",
        # "https://www.myscheme.gov.in/schemes/aayr",
        # "https://www.myscheme.gov.in/schemes/samsmesme",
        # "https://www.myscheme.gov.in/schemes/freetablet",
        # "https://www.myscheme.gov.in/schemes/pbsbbocwwb",
        # "https://www.myscheme.gov.in/schemes/csfbscss",
        # "https://www.myscheme.gov.in/schemes/fpbbocwwb",
        # "https://www.myscheme.gov.in/schemes/cpsbocwwb",
        # "https://www.myscheme.gov.in/schemes/tuk-fasbc",
        # "https://www.myscheme.gov.in/schemes/tukpmsst",
        # "https://www.myscheme.gov.in/schemes/tukpmsfst",
        # "https://www.myscheme.gov.in/schemes/fapsfti",
        # "https://www.myscheme.gov.in/schemes/tuk-tpt",
        # "https://www.myscheme.gov.in/schemes/gtpaqc",
        # "https://www.myscheme.gov.in/schemes/tufs",
        # "https://www.myscheme.gov.in/schemes/gtccs",
        # "https://www.myscheme.gov.in/schemes/asr",
        # "https://www.myscheme.gov.in/schemes/gfihrtp",
        # "https://www.myscheme.gov.in/schemes/vbsy",
        # "https://www.myscheme.gov.in/schemes/sfatm",
        # "https://www.myscheme.gov.in/schemes/bpkpcckppy",
        # "https://www.myscheme.gov.in/schemes/glrmy",
        # "https://www.myscheme.gov.in/schemes/gtcisliu",
        # "https://www.myscheme.gov.in/schemes/mmspy",
        # "https://www.myscheme.gov.in/schemes/mmvyjsy",
        # "https://www.myscheme.gov.in/schemes/aldspsl",
        # "https://www.myscheme.gov.in/schemes/avg",
        # "https://www.myscheme.gov.in/schemes/sjpwds",
        # "https://www.myscheme.gov.in/schemes/sfasiss",
        # "https://www.myscheme.gov.in/schemes/slswe",
        # "https://www.myscheme.gov.in/schemes/apapusmc",
        # "https://www.myscheme.gov.in/schemes/wbtwsam",
        # "https://www.myscheme.gov.in/schemes/mbcbocwwb",
        # "https://www.myscheme.gov.in/schemes/asd",
        # "https://www.myscheme.gov.in/schemes/ipsaeusd",
        # "https://www.myscheme.gov.in/schemes/ipszed",
        # "https://www.myscheme.gov.in/schemes/ipsidev",
        # "https://www.myscheme.gov.in/schemes/ipsacesw",
        # "https://www.myscheme.gov.in/schemes/ipsafcis",
        # "https://www.myscheme.gov.in/schemes/ipsile",
        # "https://www.myscheme.gov.in/schemes/ipsafmsme",
        # "https://www.myscheme.gov.in/schemes/sdftcw",
        # "https://www.myscheme.gov.in/schemes/svyfdb",
        # "https://www.myscheme.gov.in/schemes/psoap",
        # "https://www.myscheme.gov.in/schemes/hamcftcw",
        # "https://www.myscheme.gov.in/schemes/psw",
        # "https://www.myscheme.gov.in/schemes/ss-dadra-and-nagar-haveli-and-daman-and-diu",
        # "https://www.myscheme.gov.in/schemes/cmkuy",
        # "https://www.myscheme.gov.in/schemes/tps",
        # "https://www.myscheme.gov.in/schemes/sstsppc",
        # "https://www.myscheme.gov.in/schemes/faphfts",
        # "https://www.myscheme.gov.in/schemes/pbs-hbocwwb",
        # "https://www.myscheme.gov.in/schemes/lssas",
        # "https://www.myscheme.gov.in/schemes/lly",
        # "https://www.myscheme.gov.in/schemes/agrasp",
        # "https://www.myscheme.gov.in/schemes/afccdwt",
        # "https://www.myscheme.gov.in/schemes/uadtas",
        # "https://www.myscheme.gov.in/schemes/mds",
        # "https://www.myscheme.gov.in/schemes/fsss",
        # "https://www.myscheme.gov.in/schemes/hmcc",
        # "https://www.myscheme.gov.in/schemes/mranmas1",
        # "https://www.myscheme.gov.in/schemes/cmkvy",
        # "https://www.myscheme.gov.in/schemes/cgsces",
        # "https://www.myscheme.gov.in/schemes/cpyr",
        # "https://www.myscheme.gov.in/schemes/olahwucf",
        # "https://www.myscheme.gov.in/schemes/saipcar",
        # "https://www.myscheme.gov.in/schemes/afqe",
        # "https://www.myscheme.gov.in/schemes/dvrsf",
        # "https://www.myscheme.gov.in/schemes/ifspeta",
        # "https://www.myscheme.gov.in/schemes/ipy",
        # "https://www.myscheme.gov.in/schemes/saisoarracgf",
        # "https://www.myscheme.gov.in/schemes/atwirftnbsep",
        # "https://www.myscheme.gov.in/schemes/pknsjbf",
        # "https://www.myscheme.gov.in/schemes/ciad",
        # "https://www.myscheme.gov.in/schemes/eotmaf",
        # "https://www.myscheme.gov.in/schemes/bpuk",
        # "https://www.myscheme.gov.in/schemes/kgsuk",
        # "https://www.myscheme.gov.in/schemes/dbwa",
        # "https://www.myscheme.gov.in/schemes/cmbccay",
        # "https://www.myscheme.gov.in/schemes/ssbutsc",
        # "https://www.myscheme.gov.in/schemes/eogu",
        # "https://www.myscheme.gov.in/schemes/sib",
        # "https://www.myscheme.gov.in/schemes/gspaa-dfwasaofbc",
        # "https://www.myscheme.gov.in/schemes/atpm",
        # "https://www.myscheme.gov.in/schemes/agr2fmsfotscst",
        # "https://www.myscheme.gov.in/schemes/fapsna",
        # "https://www.myscheme.gov.in/schemes/akpsy",
        # "https://www.myscheme.gov.in/schemes/sseg10scp",
        # "https://www.myscheme.gov.in/schemes/ses-goa",
        # "https://www.myscheme.gov.in/schemes/gspv",
        # "https://www.myscheme.gov.in/schemes/sm",
        # "https://www.myscheme.gov.in/schemes/icds-chandigarh",
        # "https://www.myscheme.gov.in/schemes/akbhcy",
        # "https://www.myscheme.gov.in/schemes/madilu",
        # "https://www.myscheme.gov.in/schemes/ap-msscssvixsgsgrpsutp",
        # "https://www.myscheme.gov.in/schemes/tjhis",
        # "https://www.myscheme.gov.in/schemes/spesp",
        # "https://www.myscheme.gov.in/schemes/vtvscsgit",
        # "https://www.myscheme.gov.in/schemes/scsfr",
        # "https://www.myscheme.gov.in/schemes/skpcsy",
        # "https://www.myscheme.gov.in/schemes/rgkny",
        # "https://www.myscheme.gov.in/schemes/mssfsbu",
        # "https://www.myscheme.gov.in/schemes/fhdfh",
        # "https://www.myscheme.gov.in/schemes/cmat-ap",
        # "https://www.myscheme.gov.in/schemes/gaoah",
        # "https://www.myscheme.gov.in/schemes/cm-cab",
        # "https://www.myscheme.gov.in/schemes/peaceap",
        # "https://www.myscheme.gov.in/schemes/farppgmc",
        # "https://www.myscheme.gov.in/schemes/kscstep-dfp",
        # "https://www.myscheme.gov.in/schemes/mnbmssy",
        # "https://www.myscheme.gov.in/schemes/plgsfsbu",
        # "https://www.myscheme.gov.in/schemes/fimdgc",
        # "https://www.myscheme.gov.in/schemes/naip",
        # "https://www.myscheme.gov.in/schemes/apchapbandocwwb",
        # "https://www.myscheme.gov.in/schemes/vbpa",
        # "https://www.myscheme.gov.in/schemes/maky",
        # "https://www.myscheme.gov.in/schemes/sasy",
        # "https://www.myscheme.gov.in/schemes/mabcstss",
        # "https://www.myscheme.gov.in/schemes/rcmrf-kp",
        # "https://www.myscheme.gov.in/schemes/gsblbla",
        # "https://www.myscheme.gov.in/schemes/mkusy",
        # "https://www.myscheme.gov.in/schemes/bsp",
        # "https://www.myscheme.gov.in/schemes/dtu-cmsguy",
        # "https://www.myscheme.gov.in/schemes/icdss",
        # "https://www.myscheme.gov.in/schemes/40shydcs",
        # "https://www.myscheme.gov.in/schemes/sasstsap",
        # "https://www.myscheme.gov.in/schemes/ps-west-bengal",
        # "https://www.myscheme.gov.in/schemes/ggay",
        # "https://www.myscheme.gov.in/schemes/fadse",
        # "https://www.myscheme.gov.in/schemes/ysrvm",
        # "https://www.myscheme.gov.in/schemes/cm-sky",
        # "https://www.myscheme.gov.in/schemes/islaaa",
        # "https://www.myscheme.gov.in/schemes/fadcs",
        # "https://www.myscheme.gov.in/schemes/aduw-hbocwwb",
        # "https://www.myscheme.gov.in/schemes/nhs-west-bengal",
        # "https://www.myscheme.gov.in/schemes/psmts",
        # "https://www.myscheme.gov.in/schemes/avgsy",
        # "https://www.myscheme.gov.in/schemes/sgatt",
        # "https://www.myscheme.gov.in/schemes/frs",
        # "https://www.myscheme.gov.in/schemes/pmssu",
        # "https://www.myscheme.gov.in/schemes/fasetdp",
        # "https://www.myscheme.gov.in/schemes/sisnhe",
        # "https://www.myscheme.gov.in/schemes/pmsvs-maharashtra",
        # "https://www.myscheme.gov.in/schemes/ksetsy",
        # "https://www.myscheme.gov.in/schemes/pmavssspc",
        # "https://www.myscheme.gov.in/schemes/e-m",
        # "https://www.myscheme.gov.in/schemes/kccy",
        # "https://www.myscheme.gov.in/schemes/mta",
        # "https://www.myscheme.gov.in/schemes/ofoe",
        # "https://www.myscheme.gov.in/schemes/akmeds",
        # "https://www.myscheme.gov.in/schemes/msps",
        # "https://www.myscheme.gov.in/schemes/sspsl",
        # "https://www.myscheme.gov.in/schemes/assy-goa",
        # "https://www.myscheme.gov.in/schemes/aay-goa",
        # "https://www.myscheme.gov.in/schemes/sdrs",
        # "https://www.myscheme.gov.in/schemes/bhay",
        # "https://www.myscheme.gov.in/schemes/msme-stes",
        # "https://www.myscheme.gov.in/schemes/cmchis",
        # "https://www.myscheme.gov.in/schemes/pi",
        # "https://www.myscheme.gov.in/schemes/mssy",
        # "https://www.myscheme.gov.in/schemes/mrcddv",
        # "https://www.myscheme.gov.in/schemes/lels",
        # "https://www.myscheme.gov.in/schemes/gras",
        # "https://www.myscheme.gov.in/schemes/spsfaoce",
        # "https://www.myscheme.gov.in/schemes/gqcrc",
        # "https://www.myscheme.gov.in/schemes/cmpsy",
        # "https://www.myscheme.gov.in/schemes/swlhps",
        # "https://www.myscheme.gov.in/schemes/aavy",
        # "https://www.myscheme.gov.in/schemes/ggssnc-goa",
        # "https://www.myscheme.gov.in/schemes/cmpvy",
        # "https://www.myscheme.gov.in/schemes/swcncp",
        # "https://www.myscheme.gov.in/schemes/msvy",
        # "https://www.myscheme.gov.in/schemes/skkuy",
        # "https://www.myscheme.gov.in/schemes/bpdf",
        # "https://www.myscheme.gov.in/schemes/gva",
        # "https://www.myscheme.gov.in/schemes/ciss",
        # "https://www.myscheme.gov.in/schemes/sacipsctmrgiia",
        # "https://www.myscheme.gov.in/schemes/pms",
        # "https://www.myscheme.gov.in/schemes/pudhumai-penn-scheme",
        # "https://www.myscheme.gov.in/schemes/ltpts",
        # "https://www.myscheme.gov.in/schemes/wrflsncs-idra",
        # "https://www.myscheme.gov.in/schemes/spwfrpsmb-faascdmf",
        # "https://www.myscheme.gov.in/schemes/gmawd",
        # "https://www.myscheme.gov.in/schemes/vstspdec",
        # "https://www.myscheme.gov.in/schemes/eacpppc",
        # "https://www.myscheme.gov.in/schemes/facpwfrpfvcf",
        # "https://www.myscheme.gov.in/schemes/lrss",
        # "https://www.myscheme.gov.in/schemes/mnsasy",
        # "https://www.myscheme.gov.in/schemes/kscste-ess",
        # "https://www.myscheme.gov.in/schemes/mdmss",
        # "https://www.myscheme.gov.in/schemes/faaadp",
        # "https://www.myscheme.gov.in/schemes/facvv-nfch",
        # "https://www.myscheme.gov.in/schemes/pmsfscs",
        # "https://www.myscheme.gov.in/schemes/ahs",
        # "https://www.myscheme.gov.in/schemes/hss",
        # "https://www.myscheme.gov.in/schemes/cm-awards-karmashree",
        # "https://www.myscheme.gov.in/schemes/ignwps-sikkim",
        # "https://www.myscheme.gov.in/schemes/mysy",
        # "https://www.myscheme.gov.in/schemes/cmlh-prem",
        # "https://www.myscheme.gov.in/schemes/asfcw",
        # "https://www.myscheme.gov.in/schemes/sss",
        # "https://www.myscheme.gov.in/schemes/mtyyd",
        # "https://www.myscheme.gov.in/schemes/kv",
        # "https://www.myscheme.gov.in/schemes/pmssts",
        # "https://www.myscheme.gov.in/schemes/ehsap",
        # "https://www.myscheme.gov.in/schemes/unnati",
        # "https://www.myscheme.gov.in/schemes/slg",
        # "https://www.myscheme.gov.in/schemes/atd",
        # "https://www.myscheme.gov.in/schemes/uea",
        # "https://www.myscheme.gov.in/schemes/bmfe",
        # "https://www.myscheme.gov.in/schemes/rsb",
        # "https://www.myscheme.gov.in/schemes/mtdip",
        # "https://www.myscheme.gov.in/schemes/mjspy",
        # "https://www.myscheme.gov.in/schemes/dpyup",
        # "https://www.myscheme.gov.in/schemes/sps-assam",
        # "https://www.myscheme.gov.in/schemes/uyegp",
        # "https://www.myscheme.gov.in/schemes/jbmpvy",
        # "https://www.myscheme.gov.in/schemes/agr4fmsscf",
        # "https://www.myscheme.gov.in/schemes/bys",
        # "https://www.myscheme.gov.in/schemes/dysrhis",
        # "https://www.myscheme.gov.in/schemes/oapsp",
        # "https://www.myscheme.gov.in/schemes/fgrmb-faascdmf",
        # "https://www.myscheme.gov.in/schemes/iprrs",
        # "https://www.myscheme.gov.in/schemes/svucy",
        # "https://www.myscheme.gov.in/schemes/mj-fapm",
        # "https://www.myscheme.gov.in/schemes/omps",
        # "https://www.myscheme.gov.in/schemes/vps",
        # "https://www.myscheme.gov.in/schemes/kss",
        # "https://www.myscheme.gov.in/schemes/trs-goa",
        # "https://www.myscheme.gov.in/schemes/eacvc",
        # "https://www.myscheme.gov.in/schemes/vssay",
        # "https://www.myscheme.gov.in/schemes/ngausy",
        # "https://www.myscheme.gov.in/schemes/cmat-sada",
        # "https://www.myscheme.gov.in/schemes/madp",
        # "https://www.myscheme.gov.in/schemes/sias",
        # "https://www.myscheme.gov.in/schemes/pmssfm",
        # "https://www.myscheme.gov.in/schemes/gwpss",
        # "https://www.myscheme.gov.in/schemes/gsp",
        # "https://www.myscheme.gov.in/schemes/kbvhsusy",
        # "https://www.myscheme.gov.in/schemes/css",
        # "https://www.myscheme.gov.in/schemes/sss-goa",
        # "https://www.myscheme.gov.in/schemes/isss-pot",
        # "https://www.myscheme.gov.in/schemes/bocs",
        # "https://www.myscheme.gov.in/schemes/csy",
        # "https://www.myscheme.gov.in/schemes/asy",
        # "https://www.myscheme.gov.in/schemes/haritha-haram",
        # "https://www.myscheme.gov.in/schemes/dk",
        # "https://www.myscheme.gov.in/schemes/oadp",
        # "https://www.myscheme.gov.in/schemes/yipb",
        # "https://www.myscheme.gov.in/schemes/dpps",
        # "https://www.myscheme.gov.in/schemes/stccbocwwb",
        # "https://www.myscheme.gov.in/schemes/rtftsccw",
        # "https://www.myscheme.gov.in/schemes/bpsaec",
        # "https://www.myscheme.gov.in/schemes/eacw",
        # "https://www.myscheme.gov.in/schemes/kvy",
        # "https://www.myscheme.gov.in/schemes/bpba",
        # "https://www.myscheme.gov.in/schemes/apmsscs",
        # "https://www.myscheme.gov.in/schemes/fds",
        # "https://www.myscheme.gov.in/schemes/gbsy",
        # "https://www.myscheme.gov.in/schemes/sicmtcpd",
        # "https://www.myscheme.gov.in/schemes/pcds",
        # "https://www.myscheme.gov.in/schemes/tds",
        # "https://www.myscheme.gov.in/schemes/tnztbtsfw",
        # "https://www.myscheme.gov.in/schemes/tncmbs",
        # "https://www.myscheme.gov.in/schemes/aillam",
        # "https://www.myscheme.gov.in/schemes/kbky",
        # "https://www.myscheme.gov.in/schemes/atwsfww",
        # "https://www.myscheme.gov.in/schemes/gsdat",
        # "https://www.myscheme.gov.in/schemes/midhhmneh-meghalaya",
        # "https://www.myscheme.gov.in/schemes/dspy",
        # "https://www.myscheme.gov.in/schemes/sams",
        # "https://www.myscheme.gov.in/schemes/gopinath-munde-shetkari-apghat-suraksha-sanugrah-audhan-yojana",
        # "https://www.myscheme.gov.in/schemes/maps",
        # "https://www.myscheme.gov.in/schemes/sdsspd",
        # "https://www.myscheme.gov.in/schemes/tpsftbp",
        # "https://www.myscheme.gov.in/schemes/sfs",
        # "https://www.myscheme.gov.in/schemes/bclptls",
        # "https://www.myscheme.gov.in/schemes/atihcdohs",
        # "https://www.myscheme.gov.in/schemes/maanbocwwb",
        # "https://www.myscheme.gov.in/schemes/gccsa-dc",
        # "https://www.myscheme.gov.in/schemes/faanbocwwb",
        # "https://www.myscheme.gov.in/schemes/dbanbocwwb",
        # "https://www.myscheme.gov.in/schemes/gsrmp-dc",
        # "https://www.myscheme.gov.in/schemes/ts-ds",
        # "https://www.myscheme.gov.in/schemes/igndpstn",
        # "https://www.myscheme.gov.in/schemes/dpmbocwwb",
        # "https://www.myscheme.gov.in/schemes/mbmbocwwb",
        # "https://www.myscheme.gov.in/schemes/mjsyakm",
        # "https://www.myscheme.gov.in/schemes/ignwpstn",
        # "https://www.myscheme.gov.in/schemes/sanfsosms",
        # "https://www.myscheme.gov.in/schemes/ignoapstn",
        # "https://www.myscheme.gov.in/schemes/asymp",
        # "https://www.myscheme.gov.in/schemes/asodgbocwwb",
        # "https://www.myscheme.gov.in/schemes/jvvd",
        # "https://www.myscheme.gov.in/schemes/eaphdsgbocwwb",
        # "https://www.myscheme.gov.in/schemes/stmas-pbaocwwb",
        # "https://www.myscheme.gov.in/schemes/hefas-pbaocwwb",
        # "https://www.myscheme.gov.in/schemes/amas-pbaocwwb",
        # "https://www.myscheme.gov.in/schemes/ddanwrasii",
        # "https://www.myscheme.gov.in/schemes/rcs-pbaocwwb",
        # "https://www.myscheme.gov.in/schemes/larlbas",
        # "https://www.myscheme.gov.in/schemes/wcdcls",
        # "https://www.myscheme.gov.in/schemes/ggtwsgbocwwb",
        # "https://www.myscheme.gov.in/schemes/eaanbocwwb",
    
    ]
    fields = ["Scheme Name", "Ministries/Departments", "Target Beneficiaries", 
              "Eligibility Criteria", "Description & Benefits", "Application Process", "Tags"]

    scrape_urls(urls, fields)