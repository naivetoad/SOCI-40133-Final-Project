# This python script is used to generate author's personal information linking 
# from NSF awards (using awarded author's email as the identifier).
# Resources consulted online:
    # 1) https://www.selenium.dev/documentation/webdriver/
    # 2) https://docs.python.org/3/library/argparse.html

from selenium.webdriver.common.by import By
import time
from .webdriver_setup import initialize_driver # Use absolute path to avoid importing issues
import pandas as pd
import argparse
import os

def find_url(driver, full_name, email_domain):
    '''
    Finds awarded author's Google Scholar url (for further web scraping).

    Inputs:
        1) driver: selenium webdriver
        2) full_name: full name of the awared author
        3) email_domain: email domain name of the awared author

    Returns: awarded author's Google Scholar url
    '''

    # Starting point to search for author's Google Scholar url
    url = f"https://scholar.google.com/citations?hl=en&view_op=search_authors&mauthors={full_name}"
    driver.get(url)
    time.sleep(7)

    authors = driver.find_elements(By.CSS_SELECTOR, "div.gs_ai.gs_scl.gs_ai_chpr")
    if len(authors) == 1:
        link_element = authors[0].find_element(By.CSS_SELECTOR, "a.gs_ai_pho")
        return link_element.get_attribute('href')
    else:
        for author in authors:
            author_email_text = author.find_element(By.CSS_SELECTOR, "div.gs_ai_eml").text
            if 'Verified email at ' in author_email_text:
                author_email_domain = author_email_text.split('Verified email at ')[1]
                # Make sure the email domain matches
                if email_domain == author_email_domain:
                    link_element = author.find_element(By.CSS_SELECTOR, "a.gs_ai_pho")
                    return link_element.get_attribute('href')

    return None


def find_citations(driver, url):
    '''
    Finds awarded author's citation-related indices.

    Inputs:
        1) driver: selenium webdriver
        2) url: awarded author's Google Scholar url

    Returns: a tuple of 1) awarded author's total number of citation 
        (as of the date when the info is scraped); 2) awarded author's h-index;
        3) awarded author's yearly citation number (from the year he/she 
        publishes the first paper to 2024)
    '''

    driver.set_window_size(800, 1000)
    driver.get(url)
    time.sleep(3)

    cited_by_tab = driver.find_element(By.ID, "gsc_prf_t-cit")
    cited_by_tab.click()
    time.sleep(3)

    # Extract total number of citation and h-index
    total_citations = driver.find_element(By.XPATH, '//*[@id="gsc_rsb_st"]/tbody/tr[1]/td[2]').text
    h_index = driver.find_element(By.XPATH, '//*[@id="gsc_rsb_st"]/tbody/tr[2]/td[2]').text

    # Extract yearly citation number
    year_citations = {}
    year_elements = driver.find_elements(By.CSS_SELECTOR, "div.gsc_md_hist_w .gsc_g_t")
    citation_elements = driver.find_elements(By.CSS_SELECTOR, "div.gsc_md_hist_w .gsc_g_a")

    for year, citation in zip(year_elements, citation_elements):
        citation_count = driver.execute_script("return arguments[0].textContent", citation)
        year_citations[year.text] = citation_count

    return total_citations, h_index, year_citations


def find_interests(driver, url):
    '''
    Finds awarded author's research interest(s) on the Google Scholar page.
    
    Inputs:
        1) driver: selenium webdriver
        2) url: awarded author's Google Scholar url

    Returns: a list of awarded author's research interests
    '''

    driver.get(url)
    time.sleep(3)

    interests = []

    try:
        interest = driver.find_elements(By.CSS_SELECTOR, "div#gsc_prf_int a.gsc_prf_inta")
        interests = [i.text for i in interest] if interest else None

    except Exception as e:
        print(f"Error occurred: {e}")

    return interests


def retrieve_author_info(nsf_df, year, driver):
    '''
    Retrieve awarded author's basic information.
    Inputs:
        1) nsf_df: a pandas DataFrame of NSF awarded projects' information
        2) year: the awarded year
        3) driver: An instance of Selenium WebDriver for browser automation
     
   Returns: 
        A DataFrame containing awarded author's name, email, Google Scholar URL,
        citation-related indices, research interests, and citations by year
    '''
    # Filter the DataFrame for the specified year
    nsf_df_filtered = nsf_df[nsf_df['year'] == year].dropna(subset=['email'])
 
    # Define output DataFrame structure with basic columns
    base_columns = ["first_name", "middle_name", "last_name", "email",
                    "institution", "url", "total_citations", "h_index", "interests"]
    processed_df = pd.DataFrame(columns=base_columns)
 
     # First retrieve the author's Google Scholar's url from 
     # searching author's name on Google Scholar using selenium
     # (Remember to use Uchicago's vpn to prevent anti-scraping)
    for _, row in nsf_df_filtered.iterrows():
        full_name = f"{row['first_name']} {row['last_name']}".strip()
        email_domain = row['email'].split('@')[-1]

        try:
            url = find_url(driver, full_name, email_domain)
            if url:
                print(f"Returning {row['first_name']} {row['last_name']}'s Google Scholar url: {url}")
                total_citations, h_index, year_citations = find_citations(driver, url)
                interests = find_interests(driver, url)
            else:
                raise ValueError("URL not found")
        except Exception as e:
            print(f"Error processing {full_name}: {e}")
            url, total_citations, h_index, interests = None, None, None, None
            year_citations = {}

        new_row = {
            "first_name": row['first_name'],
            "middle_name": row.get('middle_name', ''),
            "last_name": row['last_name'],
            "email": row['email'],
            "institution": row['institution'],
            "url": url,
            "total_citations": total_citations,
            "h_index": h_index,
            "interests": interests
        }

        # Append the new row to the DataFrame
        new_index = len(processed_df)  # Get the new row's index
        processed_df = pd.concat([processed_df, pd.DataFrame([new_row])], ignore_index=True)

        for citation_year, citations in year_citations.items():
            citation_col_name = f"citation_{citation_year}"

            # Directly update the cell for the current author and year
            # If the column does not exist, it will be automatically added
            processed_df.loc[new_index, citation_col_name] = citations

    return processed_df


def safe_retrieve_author_info(nsf_df, year):
    '''
    Retrieve awarded author's basic information safely by dealing with potential
    errors using selenium webdriver (filtering out authors whose Google scholar
    url cannot be successfully retrieved).
 
    Inputs:
        1) nsf_df: a pandas DataFrame of NSF awarded projects' information
        2) year: the awarded year
 
    Returns: 
        A DataFrame containing awarded author's name, email, Google Scholar URL,
        citation-related indices, research interests, and citations by year
    '''
    processed_data_all = pd.DataFrame()

    # Pre-filter the nsf_df to focus on a specific year
    nsf_df_filtered = nsf_df[nsf_df['year'] == year]

    while not nsf_df_filtered.empty:
        try:
            driver = initialize_driver()
            processed_chunk = retrieve_author_info(nsf_df, year, driver)

            if not processed_chunk.empty:
                # Append processed_chunk to the consolidated DataFrame
                processed_data_all = pd.concat([processed_data_all, processed_chunk],
                                               ignore_index=True)
                # Drop rows from nsf_df using the emails from processed_chunk
                processed_emails = processed_chunk['email'].values
                nsf_df_filtered = nsf_df_filtered[~nsf_df_filtered['email'].isin(processed_emails)]
            
            # Check if nsf_df_filtered has only one row (i.e., last author to scrape)
            # If so, break out of the loop
            if len(nsf_df_filtered) <= 1:
                print("All data processed, exiting loop.")
                break
        except Exception as e:
            print(f"An error occurred: {e}")
            time.sleep(20)  # Wait a bit before retrying or proceeding
        finally:
            driver.quit()  # Ensure driver is closed after each iteration

    if not processed_data_all.empty:
        print(f"Scraped a total number of {len(processed_data_all)} authors.")
        # Drop authors whose Google Scholar page url is missing
        processed_data_all_filtered = processed_data_all.dropna(subset=["url"])
        print(f"{len(processed_data_all_filtered)} authors have intact Google scholar url.")

        # Save the consolidated data to a CSV file
        processed_data_all_filtered.to_csv(f"database/author_info_{year}.csv",
                                           index=False, encoding='utf-8-sig')
        print(f"Successfully processed and saved all data for year {year}.")
    else:
        print("No data processed.")


# Use this function with the command-line interface
if __name__ == "__main__":
    # Initialize the parser
    parser = argparse.ArgumentParser(description='Retrieve author information for a specified year from NSF data file.')

    # Add the 'file_path' argument for the NSF DataFrame
    parser.add_argument('--funding_info_file_path', type=str, default="database/funding_info.csv", help='The file path to the NSF data CSV file.')

    # Add the 'year' argument
    parser.add_argument('year', type=int, help='The year of interest for author information retrieval.')

    # Parse the arguments
    args = parser.parse_args()
    funding_info_file_path = args.funding_info_file_path
    year = args.year
    
    # Check if the specified NSF data file exists
    if not os.path.exists(funding_info_file_path):
        print(f"The file {funding_info_file_path} does not exist.")
    else:
        nsf_df = pd.read_csv(funding_info_file_path)

        # Construct the output file name based on the year
        author_info_file_path = f"database/author_info/author_info_{year}.csv"

        # Check if the file exists before attempting to retrieve author info
        if not os.path.exists(author_info_file_path):
            safe_retrieve_author_info(nsf_df, year)
        else:
            print(f"Author info for year {year} already exists at {author_info_file_path}.")
