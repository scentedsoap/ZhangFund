import requests
from bs4 import BeautifulSoup, Comment
import re
import copy
import numpy as np


def generate_url(cik:str, unknown:str, ticker:str, date:str,) -> str:
    
    """
    Creates A URL Pointing To A Report In The EDGAR Database.

    each url is composed of the following
        1. base
        2. cik
        3. cik with leading zeros
        4. unknown sequence of numbers???
        5. ticker
        6. date
    """
    
    base_url = "https://www.sec.gov/Archives/edgar/data"            # base url that every document starts with  
    url = f"{base_url}/{cik}/{cik}{unknown}/{ticker}-{date}.htm"    # actual url endpoint,
                                                                    # TODO: leading zeros and unknown
    return url

def scrape_annual_report(url:str):

    """
    Scrapes EDGAR For An Annual Report Using The Provided URL And Stores Data In Text File.

    parameters:
        url: the url of the annual report
    
    returns:
        parsed_annual_report: the entire html document (BeautifulSoup Object)
        parsed_parts_clean: a list of bs4.element.NavigableString that split the parts of the annual report
    """

    "Step 1. Scrape The HTML File"

    annual_report = requests.get(url, headers={"User-Agent": "bzhang14@umd.edu"})   # sends get request to URL endpoint (html file)
    parsed_annual_report = BeautifulSoup(annual_report.text, 'html.parser')         # parse the response using BeautifulSoup 

    "Step 2. Split into Parts"

    parts = ["PART I", "PART II", "PART III", "PART IV"]        # lists of parts for annual report
    parsed_parts = parsed_annual_report.find_all(string=parts)  # list of all elements that contain any of the parts in the list above
    
    # list of actual part seperating elements
    # note that the the actual seperating elements are stored in spans!
    parsed_parts_clean = [part for part in parsed_parts if part.parent.name != "a"]                              

    return parsed_annual_report, parsed_parts_clean

def extract_parts(parsed_parts):

    """
    Extracts The Elements Between The Parts (1,2,3,4)
    """

    part1 = parsed_parts[0].parent.parent       # access the grand parent because the first parent is the tag
    part2 = parsed_parts[1].parent.parent       # that wraps the text "PART I", this is usually the <span>
    part3 = parsed_parts[2].parent.parent       # the tag that wraps the <span> is usually a <div>
    part4 = parsed_parts[3].parent.parent

    elements_part1_to_part2 = find_elements_inbetween(part1, part2)     # 
    elements_part2_to_part3 = find_elements_inbetween(part2, part3)
    elements_part3_to_part4 = find_elements_inbetween(part3, part4)

    print(type(elements_part1_to_part2))

def find_elements_inbetween(element_1, element_2) -> list:

    """
    Useful Function To Find All The Elements Between Two Elements 
    """
    element_list = [element_1]

    for element in element_1.next_siblings:                 # iterate through the all of the elements that come after 
        element_list.append(copy.copy(element))             # element_1, this is in element_1.next_siblings
    
        if element == element_2:                            # if the second element is encountered then break out of loop
            break
    
    ## TODO: Write String Converter and HTML Parser get the elements in between!##

    return element_list


def financial_statements():

    """
    retrieve all information related to the financial statements of a company
    """

def income_statement(parsed_annual_report: BeautifulSoup):

    """
    Retrieve The Income Statements For A Company.
    """

    statement_names = [re.compile("^Consolidated Statements of $", re.I), 
                       re.compile("^Consolidated Statements of Income", re.I),
                       re.compile("^Consolidated Statements of Operations", re.I)]  # possible names for the income statement in annual report

    for statement_name in statement_names:
        elements = parsed_annual_report.find_all(string=statement_name)
        print(elements)
        if len(list(elements)) != 0:
            break

    # print(len(elements))
    # print(elements)
    # print(elements[0].descendents)

    # filter out the elements that have the same string but are not the headings in the annual report!
    # TODO: The <span> element above does not have any descendents, why???
    # filtered_elements = [element for element in elements if len(list(element.descendents)) == 1]


    table = elements[0].find_next("table")      # find the income statement table 
                                                # (we assume its the table after the span element)
    
    "data structures"
    xbrl_dictionary = {}                        # dictionary to define xbrl concepts
                                                # key: name in Income Statement, value: XBRL concept name
    
    metric_values = {}                          # dictionary that stores the metric as reported in the income statement
                                                # key: name in Income Statement, value: Value of Metric for the year
    
    statement_name_list = []                    # ordered list of metrics reported in Income Statement

    for tr in table.findAll("tr"):                          # iterate through the rows of the table
        for td in tr:                                       # iterate through the entries of the table row

            if td.string != None and td.string != "$":              # ignore the entries that are empty or are just placeholders
                
                income_statement_name = td.string                   # td.string is the metric used in the income statement (Net Revenues, COGS, etc.)                

                #print(td.string)                                    # print the value of the name in the income statement
            
            elif td.find("ix:nonfraction") != None:                 # tries finding a XBRL Element <ix:nonfraction>
                
                xbrl_element = td.find("ix:nonfraction")            # xbrl_element is the html element <ix:nonfraction>
                xbrl_concept_name = xbrl_element["name"]            # xbrl_element["name"] is the value of the name attribute in the XBRL element tag                                                       
                xbrl_concept_value = xbrl_element.string            # the actual value of the XBRL concept

                if income_statement_name not in xbrl_dictionary.keys():
                    xbrl_dictionary[income_statement_name] = xbrl_concept_name   # store the concept name in dictionary
                    statement_name_list.append(income_statement_name)   # adds the metric name as reported to the list 
                    metric_values[income_statement_name] = []           # create initial key value pair

                metric_values[income_statement_name].append(xbrl_concept_value)

                #print(td.find("ix:nonfraction")["name"])       # print the name of the (XBRL) concept 
                #print(td.find("ix:nonfraction").string)        # print the value of the (XBRL) element

    return xbrl_dictionary, metric_values, statement_name_list



# def balance_sheet():

# def cash_flow_statement():

# TODO: Figure out solution to problem where the files are not populating due to the index-header.html page not existing!!

def find_annual_reports(cik):

    annual_reports = []
    header = {"User-Agent": "bzhang14@umd.edu"}
    base_url = "https://www.sec.gov/Archives/edgar/data"            # base url that every document starts with  
    directory_url = f"{base_url}/{cik}"                             # base Directoy List URL

    req = requests.get(directory_url, headers=header)   # sends get request to URL endpoint (html file)

    directory_webpage = BeautifulSoup(req.text, "html.parser")
    directory_table = directory_webpage.find("table")
    
    directory_links = directory_table.find_all("a")

    for a_tag in directory_links:
        subdirectory_url = f"{directory_url}/{a_tag.text}"
        req = requests.get(subdirectory_url, headers=header)
        subdirectory_webpage = BeautifulSoup(req.text, "html.parser")
        form_type, form_name = check_file_type(subdirectory_webpage, header, subdirectory_url)
        print(form_type)
        if form_type == None:
            print("error, form type is None")
        elif form_type == "Form 10-K":
            document_url = f"{subdirectory_url}/{form_name}"
            print(document_url)
            annual_reports.append(document_url)
    
    return annual_reports

def check_file_type(subdirectory_webpage: BeautifulSoup, header: dict, subdirectory_url: str) -> str:

    """
    Finds The File Type That Is Stored In A Sub-Directory Within The SEC EDGAR Directory Listing.

    Every subdirectory in the EDGAR Directory Listing has a index-headers.html file
    which is the first file in the subdirectory that has metadata about the filing itself!
    """
    subdirectory_table = subdirectory_webpage.find("table")
    subdirectory_link = list(subdirectory_table.find_all("a"))[1]   # gets the index.html file in the subdirectory
    file_name = subdirectory_link.text

    file_url = f"{subdirectory_url}/{file_name}"                # URL of the actual filed stored in Directory Listing

    # print(file_url)
    req = requests.get(file_url, headers=header)    
    index_file = BeautifulSoup(req.text, "html.parser")   

    form_type = index_file.find("div", {"id": "formName"}).find("strong").text    # check if the form is 10-K
    form_name = find_document_on_index_page(index_file)

    return form_type, form_name

def find_document_on_index_page(index_page: BeautifulSoup) -> str:
    file_table = index_page.find("table", {"class":"tableFile"})
    second_row = list(file_table.find_all("tr"))[1]
    document = list(second_row.find_all("td"))[2].find("a").text
    return document

"""
JSON Submission Scraper Stuff Below Here
"""

def json_submission_scraper(cik:str, form_type:str):
    
    """
    Scrape The JSON File That Has All The Information About Files That Have Been Submitted To EDGAR.
    """

    header = {"User-Agent": "bzhang14@umd.edu"}
    url_to_json = generate_json_submission_url(cik)

    req = requests.get(url_to_json, headers=header)
    submissions_json = req.json()

    recent_filings = submissions_json["filings"]["recent"]  # recent filings

    # the non-recent filings are not stored in the same JSON file so we need to
    # get those from another JSON file that is stored in the one that was just requested
    nonrecent_filings_name = submissions_json["filings"]["files"][0]["name"]
    nonrecent_filings_url = generate_json_submission_url(is_recent_submission=False,
                                                          name=nonrecent_filings_name)
    
    req = requests.get(nonrecent_filings_url, headers=header)
    non_recent_submissions_json = req.json()
    non_recent_filings = non_recent_submissions_json

    recent_filing_dates, recent_path_to_documents = find_forms(recent_filings, form_type)
    nonrecent_filing_dates, nonrecent_path_to_documents = find_forms(non_recent_filings, form_type)

    print(type(recent_path_to_documents))
    print(type(nonrecent_path_to_documents))

    path_to_documents = np.concatenate((recent_path_to_documents, nonrecent_path_to_documents))
    filing_dates = np.concatenate((recent_filing_dates, nonrecent_filing_dates))

    urls = generate_EDGAR_directory_listing_url(cik, path_to_documents)
    print(urls)

    return urls

def find_forms(filings: list[str], form_type:str):
    
    forms = np.array(filings["form"])
    accession_numbers = np.array([filing + "/" for filing in filings["accessionNumber"]])
    document_names = np.array(filings["primaryDocument"])
    filing_dates = np.array(filings["filingDate"])

    indexes = np.where(forms == form_type)
    form_accession_numbers = accession_numbers[indexes]
    form_document_names = document_names[indexes]

    form_accession_numbers = np.char.replace(form_accession_numbers, "-", "")
    path_to_documents = np.char.add(form_accession_numbers, form_document_names)

    return filing_dates, path_to_documents

    
def generate_json_submission_url(cik:str = "", is_recent_submission:bool = True, 
                                    name:str = None):
    
    base_url = "https://data.sec.gov/submissions/"
    
    cik_length = len(cik)
    num_leading_zeros = 10 - cik_length
    leading_zeros = num_leading_zeros * "0"
    leading_zeros_cik = leading_zeros + cik

    if is_recent_submission:                                    # the url is different for submisisons within 10 years
        url_to_json = f"{base_url}CIK{leading_zeros_cik}.json"  # and submissions over 10 years
    else:
        url_to_json = f"{base_url}/{name}"

    return url_to_json
    

def generate_EDGAR_directory_listing_url(cik: str, path_to_documents: np.ndarray):
    base_url = "https://www.sec.gov/Archives/edgar/data/"
    base_url_cik = f"{base_url}{cik}/"
    base_url_cik_list = np.array(base_url_cik)
    url_to_files = np.char.add(base_url_cik_list, path_to_documents)

    return url_to_files
