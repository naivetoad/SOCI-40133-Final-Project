from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
import time
import pandas as pd
from .webdriver_setup import initialize_driver
import os
import argparse

def get_pub_url(awarded_year):
    '''
    Creates a csv of awarded authors' publication-related basic information 
    (title, number of citation, and, most importantly, paper url on the 
    Google Scholar) gained from going into author's Google Scholar Page.
    This paper url will be further "clicked" by selenium to extract the abstract.

    Inputs: 
        1) awarded_year: year at which the author is awarded NSF

    Returns: path for pub_url
    '''

    # Define the path storing author info (i.e., `author_info` table)
    author_info_path = f"database/author_info/author_info_{awarded_year}.csv"

    # Define the path for the output (primarily, publication url)
    pub_url_path = f"database/publication_info/pub_url_{awarded_year - 3}_{awarded_year + 3}.csv"

    # Make sure the author_info table exists
    try:
        df = pd.read_csv(author_info_path)
    except FileNotFoundError:
        print(f"Failed to run the function because {author_info_path} is not found.\n")
        print("Please get author_info first.")

        # Leave the function
        return

    # Create an empty DataFrame to store all authors' publication information
    all_publications = pd.DataFrame()

    for _, author_row in df.iterrows():
        # Configure webdriver (again) every time after quitted for each iteration
        driver = initialize_driver()

        url = author_row['url']

        # Visit the author's homepage
        driver.get(url)
        time.sleep(2)

        # Click the "Show more" button until all papers are loaded
        while True:
            try:
                show_more_button = driver.find_element(By.ID, "gsc_bpf_more")
                if show_more_button.is_displayed() and show_more_button.is_enabled():
                    show_more_button.click()
                    time.sleep(2)
                else:
                    break
            except (NoSuchElementException, ElementClickInterceptedException):
                break

        # Extract information about the papers
        publications = []
        rows = driver.find_elements(By.CSS_SELECTOR, "tr.gsc_a_tr")
        for row in rows:
            # Focus on 3 years before and after the awarded_year
            publication_year = row.find_element(By.CSS_SELECTOR, "span.gsc_a_hc").text
            if publication_year:
                publication_year = int(publication_year)
                # Check if publication_year falls within the desired range
                if awarded_year - 3 <= publication_year <= awarded_year + 3:
                    title = row.find_element(By.CSS_SELECTOR, "a.gsc_a_at").text
                    cited_by = row.find_element(By.CSS_SELECTOR, "a.gsc_a_ac").text
                    paper_url = row.find_element(By.CSS_SELECTOR, "a.gsc_a_at").get_attribute("href")

                    publications.append({
                        "Title": title,
                        "Year": publication_year,
                        "Cited by": cited_by,
                        "Paper URL": paper_url
                    })

        # Convert the author's publication information into a DataFrame
        author_publications_df = pd.DataFrame(publications)

        # Also append the author's email (number of times equal to numbe of rows)
        # to relate `author_info` table to later `pub_info` table
        df_len = len(author_publications_df)
        insert_columns = ["first_name", "middle_name", "last_name", "email"]
        for i, v in enumerate(insert_columns):
            author_publications_df.insert(loc=i, column=v, value=[author_row[v]] * df_len)

        # Add the author's publication information to the overall DataFrame
        all_publications = pd.concat([all_publications, author_publications_df], ignore_index=True)
        all_publications.to_csv(pub_url_path, index=False, encoding='utf-8-sig')
        driver.quit()

    # Save all authors' publication information as a CSV file
    all_publications.to_csv(pub_url_path, index=False, encoding='utf-8-sig')

    return pub_url_path


def extract_info_from_html(publication_url, driver):
    '''
    Builds on `get_pub_url` function to extract publication-related information.

    Note: The reaon for separating this scraping publication information 
    process into two steps is to prevent anti-scraping.

    Inputs: 
        1) publication_url: url that can lead to paper detail with an additional click of Google Scholar
        2) driver: selenium driver

    Returns: a dictionary containing authors' names, publication date, 
        journal name, paper abstract, and yearly breakdown of paper citation 
    '''

    driver.get(publication_url)
    # Wait for the page to load
    time.sleep(3)  

    # Initialize variables to store extracted information
    authors = ""
    publication_date = ""
    journal = ""
    abstract = ""
    year_citations = {}

    # Extract authors
    try:
        authors_element = driver.find_element(By.XPATH, "//div[@class='gs_scl'][div='Authors']/div[@class='gsc_oci_value']")
        authors = authors_element.text
    except:
        authors = "authors not found"

    # Extract publication date
    try:
        publication_date_element = driver.find_element(By.XPATH, "//div[@class='gs_scl'][div='Publication date']/div[@class='gsc_oci_value']")
        publication_date = publication_date_element.text
    except:
        publication_date = "date not found"

    # Extract journal
    try:
        journal_element = driver.find_element(By.XPATH, "//div[@class='gs_scl'][div='Journal']/div[@class='gsc_oci_value']")
        journal = journal_element.text
    except:
        journal = "journal not found"

    # Extract abstract
    try:
        abstract_element = driver.find_element(By.CSS_SELECTOR, "div.gsh_csp")
        abstract = abstract_element.text
    except:
        try:
            abstract_element = driver.find_element(By.CSS_SELECTOR, "div.gsh_small")
            abstract = abstract_element.text

        except:
            abstract = "Abstract not found"

    # Extract citations and years of the paper
    try:
        year_elements = driver.find_elements(By.CSS_SELECTOR, "div#gsc_oci_graph_bars span.gsc_oci_g_t")
        citation_elements = driver.find_elements(By.CSS_SELECTOR, "div#gsc_oci_graph_bars a.gsc_oci_g_a span.gsc_oci_g_al")
        for year, citation in zip(year_elements, citation_elements):
            citation_count = driver.execute_script("return arguments[0].textContent", citation)
            year_citations[year.text] = citation_count
    except:
        pass

    return {
        "Authors": authors,
        "Publication Date": publication_date,
        "Journal": journal,
        "Abstract": abstract,
        "Citations": year_citations
    }


def generate_pub_info_table(awarded_year):
    '''
    Generates the final csv table storing publication-related information after 
    relating it to NSF award table and author_info table.

    Note: The reaon for separating this scraping publication information 
    process into two steps is to prevent anti-scraping.

    Inputs: 
        1) awarded_year: year at which the author is awarded NSF
        2) pub_url_path: path storing the temporarily stored csv containing pub_url

    Returns: None
    '''

    # Configure Selenium WebDriver
    driver = initialize_driver()

    # Run the function to generate pub_url table and get the pub_url_path
    pub_url_path = get_pub_url(awarded_year)    

    # Defines the path for the final pub_info table
    pub_info_path = pub_url_path.replace("pub_url", "pub_info")

    # Build the output pub_info table based on the previous pub_url dataframe
    try:
        # Make sure the pub_url_path table exists
        df = pd.read_csv(pub_url_path)
    except FileNotFoundError:
        print(f"Failed to run the function because {pub_url_path} is not found.\n")
        print("Please get pub_url first.")
        # Leave the function
        return

    # Create new columns to store extracted information
    df["Authors"] = ""
    df["Publication Date"] = ""
    df["Journal"] = ""
    df["Abstract"] = ""
    df["Citations"] = ""

    # Iterate through each row, execute the scraping function, and update the DataFrame
    for index, row in df.iterrows():
        publication_url = row["Paper URL"]
        try:
            info = extract_info_from_html(publication_url, driver)
            print(info)
            df.at[index, "Authors"] = info["Authors"]
            df.at[index, "Publication Date"] = info["Publication Date"]
            df.at[index, "Journal"] = info["Journal"]
            df.at[index, "Abstract"] = info["Abstract"]
            df.at[index, "Citations"] = str(info["Citations"])
        except:
            pass

        time.sleep(2)
        # Save data every 50 rows
        if (index + 1) % 50 == 0:
            df.to_csv(pub_info_path, index=False, encoding='utf-8-sig')
            print(f"Saved data for {index + 1} rows.")

        # Close and restart WebDriver
        if (index + 1) % 50 == 0:
            driver.quit()
            print("Driver closed. Sleeping for 20 seconds...")
            time.sleep(20)
            # Restart WebDriver
            driver = initialize_driver()

    # Save remaining data
    df.to_csv(pub_info_path, index=False, encoding='utf-8-sig')

    # Close WebDriver
    driver.quit()

    # Remove the intermediate pub_url file after finish running this function
    os.remove(pub_url_path)
    print(f"The intermediate file {pub_url_path} has been deleted.")


# Use this function with the command-line interface
if __name__ == "__main__":
    # Initialize the parser
    parser = argparse.ArgumentParser(description='Generate a CSV of publication-related information from Google Scholar for a specified awarded year.')

    # Add the 'awarded_year' argument
    parser.add_argument('awarded_year', type=int, help='The year for which to retrieve publication information.')

    # Parse the arguments
    args = parser.parse_args()

    # Extract the awarded year from the command-line arguments
    awarded_year = args.awarded_year

    # File path check and function call
    pub_info_file_path = f"database/publication_info/pub_info_{awarded_year}.csv"
    if not os.path.exists(pub_info_file_path):
        generate_pub_info_table(awarded_year)
    else:
        print(f"Publication info for year {awarded_year} already exists at {pub_info_file_path}.")

# Sample usage of the command-line interface (using 2011 as the year to scrape)
# python scraping_helper_functions/get_pub_info.py 2011
        
# Sample usage of the command-line interface to scrape from 2011 to 2020
# for year in {2011..2020}; do python scraping_helper_functions/get_pub_info.py $year; done