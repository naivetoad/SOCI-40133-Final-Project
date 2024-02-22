import pandas as pd
from lxml import etree
import os
import argparse

def extract_data_from_file(file_path):
    '''
    Extracts data from a downloaded NSF file.

    Inputs:
        1) file_path: file path of a specific NSF xml file
    
    Returns: a pandas DataFrame containing information about NSF awarded project
    '''

    # Extract data from the xml file
    tree = etree.parse(file_path)
    root = tree.getroot()

    extracted_data = {
        "first_name": "",
        "middle_name": "",
        "last_name": "",
        "email": "",
        "institution": "",
        "directorate": "",
        "division": "",
        "effective_date": "",
        "expiration_date": "",
        "award_amount": "",
        "award_title": "",
        "abstract": ""
    }

    award = root.find('Award')

    extracted_data["institution"] = award.findtext('Institution/Name') or ''
    extracted_data["award_title"] = award.findtext('AwardTitle') or ''
    extracted_data["effective_date"] = award.findtext('AwardEffectiveDate') or ''
    extracted_data["expiration_date"] = award.findtext('AwardExpirationDate') or ''
    extracted_data["award_amount"] = award.findtext('AwardTotalIntnAmount') or ''
    extracted_data["abstract"] = award.findtext('AbstractNarration') or ''
    extracted_data["directorate"] = award.findtext('Organization/Directorate/LongName') or ''
    extracted_data["division"] = award.findtext('Organization/Division/LongName') or ''
    # Iterate through Investigators to find the Principal Investigator
    for investigator in award.findall('Investigator'):
        role_code = investigator.findtext('RoleCode')
        if role_code == 'Principal Investigator':
            extracted_data["first_name"] = investigator.findtext('FirstName') or ''
            extracted_data["middle_name"] = investigator.findtext('PI_MID_INIT') or ''
            extracted_data["last_name"] = investigator.findtext('LastName') or ''
            extracted_data["email"] = investigator.findtext('EmailAddress').strip() if investigator.findtext(
                'EmailAddress') else ''
            # Stop after finding the principal investigator
            break  

    return extracted_data


def process_all_folders(base_path, start_year, end_year,
                        filter_directorate=None, filter_division=None):
    '''
    Processes yearly awarded data folders unzipped from NSF official website.

    Inputs:
        1) base_path: path storing all NSF awarded data
        2) start_year: starting year of NSF awards to focus on
        3) end_year: ending year of NSF awards to focus on
        4) filter_directorate: directorate of NSF to filter
        5) filter_division: division under directorate of NSF to filter

    Returns: a pandas DataFrame containing information about NSF awarded project (for given years)
    '''

    all_data = []
    for year in range(start_year, end_year + 1):  # Loop through each year
        print(f"Processing NSF data folder for year {year}:\n")
        folder_path = os.path.join(base_path, str(year))
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            for filename in os.listdir(folder_path):
                # Target the .xml file of NSF awards
                if filename.endswith('.xml'):
                    file_path = os.path.join(folder_path, filename)
                    try:
                        data = extract_data_from_file(file_path)
                    except:
                        pass
                    # Filter based on given directorate and directorate (if any)
                    # Assume data should be appended unless a condition fails
                    should_append = True  
                    if filter_directorate and data["directorate"] != filter_directorate:
                        should_append = False
                    if filter_division and data["division"] != filter_division:
                        should_append = False
                    
                    if should_append:
                        all_data.append(data)

    return pd.DataFrame(all_data)

# Use this function with the command-line interface
if __name__ == "__main__":
    # Initialize the parser
    parser = argparse.ArgumentParser(description='Process NSF data folders and create a dataset of funding_info.')

    # Add arguments
    parser.add_argument('--base_path', type=str, default="nsf_data", help='Base path storing all NSF awarded data.')
    parser.add_argument('--start_year', type=int, default=2011, help='Starting year of NSF awards to focus on.')
    parser.add_argument('--end_year', type=int, default=2020, help='Ending year of NSF awards to focus on.')
    parser.add_argument('--filter_directorate', type=str, default="Direct For Social, Behav & Economic Scie", help='Directorate of NSF to filter.')
    parser.add_argument('--filter_division', type=str, default="Division Of Behavioral and Cognitive Sci", help='Division under directorate of NSF to filter.')

    # Parse the arguments
    args = parser.parse_args()

    # Construct nsf_data_file_path based on start_year and end_year
    nsf_data_file_path = f'database/funding_info.csv'

    if os.path.exists(nsf_data_file_path):
        nsf_df = pd.read_csv(nsf_data_file_path)
    else:
        nsf_df = process_all_folders(base_path=args.base_path,
                                     start_year=args.start_year, end_year=args.end_year,
                                     filter_directorate=args.filter_directorate,
                                     filter_division=args.filter_division)
        # Ensure the directory exists before saving
        os.makedirs(os.path.dirname(nsf_data_file_path), exist_ok=True)
        nsf_df.to_csv(nsf_data_file_path, index=False)

# Sample usage of the command-line interface (using the default arguments)
# python scraping_helper_functions/get_all_NSF.py