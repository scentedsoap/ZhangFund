import re
from bs4 import BeautifulSoup
import copy
import requests
import webscraper as ws

class AnnualReport:

  """
  Resembles An Annual Report (Form 10K) That Is Filed By Companies To SEC. 
  
  An annual report has the following structure:

      Part 1

          Item 1: Business
            Item 1A: Risk Factors
            Item 1B: Unresolved Staff Comments
          Item 2: Properties
          Item 3: Legal Proceedings
          Item 4: ???
          
      Part 2

          Item 5: Market, Stockholder, and Repurchasing
          Item 6: Selected Financial Data
          Item 7: MD&A
            Item 7A: Quantitative and Qualitative Disclosures about Market Risk
          Item 8: Financial Statements and Supplementary Data
          Item 9: Changes in and Disagreements with Accountants 
            Item 9A: Controls and Procedures
            Item 9B: Other Information
            
      Part 3

          Item 10: Directors, Executive Officers and Corporate Governance
          Item 11: Executive Compensation
          Item 12: Security Ownership of Certain Beneficial Owners and Management
          Item 13: Certain Relationships and Related Transactions and Director Independence
          Item 14: Principal Accountant Fees and Services

      Part 4

          Item 15: Exhibits, Financial Statement Schedules
  """

  report_dict = None  # stores annual report as Beautiful Soup Objects
  year = None         # year of annual report TODO: look into XBRL DocumentPeriodEndDate

  def __init__(self, url:str = None, is_url:bool = True):
     
     # TODO: Finish Constructor
     if is_url:
        self.report_dict = self.parse_annual_report(url)
        print("constructor finished")


  """
  Accessors (Getters)
  """
  def get_part(self, part_number:str):
     key = f"part{part_number}"
     return self.report_dict[key]
  
  def get_item(self, item_number:str):
      key = f"item{item_number}"
      return self.report_dict[key]
  
  def parse_annual_report(self, url: str) -> dict:
    
    """
    Scrapes An Annual Report On the SEC EDGAR Database Then Parses Through The HTML 
    And Stores Each Individual Part and Item Into A Dictionary

    parameters:
      url:str -> the url of the annual report in the SEC Directory Listing

    returns:
      dict -> dictionary whose keys are the names of the Parts (I,II,III,IV) and Items (1,2,3,etc.) 
    """
    
    annual_report_dict = {} # dictionary to store all the parts of the annual report

    parsed_annual_report, parsed_parts_clean = self.scrape_annual_report(url) # scrape the annual report 
    parts_dict = self.extract_parts(parsed_parts_clean)  # we have parsed parts

    
    print("parts dict")
    print(parts_dict.keys())

    part_items_dict = self.extract_all_items_from_table_contents(parsed_annual_report)
    items_dict = self.extract_all_items(parts_dict, part_items_dict)
    print(items_dict)

    return {"full report":parsed_annual_report, **parts_dict, **items_dict}
    # call a function that will take the elements between 2 parts (or the last part 4)
    # and returns a dictionary that has all the items and the corresponding BeautifulSoup 
    # Object for the elements(tags) in between!
        

  def scrape_annual_report(self, url:str) -> (BeautifulSoup, list):

    """
    Scrapes EDGAR For An Annual Report Using The Provided URL And Stores Data In Text File.

    parameters:
      url: the url of the annual report
    
    returns:
      tuple (parsed_annual_report, parsed_parts_clean)
        parsed_annual_report: the entire html document (BeautifulSoup Object)
        parsed_parts_clean: a list of Navigable Strings
    """

    "Step 1. Scrape The HTML File"

    annual_report = requests.get(url, headers={"User-Agent": "bzhang14@umd.edu"})   # sends get request to URL endpoint (html file)
    parsed_annual_report = BeautifulSoup(annual_report.text, 'html.parser')         # parse the response using BeautifulSoup 

    "Step 2. Split into Parts"

    parts = [re.compile("^PART.I$", re.I), re.compile("^PART.II$", re.I), 
             re.compile("^PART.III$", re.I), re.compile("^PART.IV$", re.I)]        # lists of parts for annual report
    parsed_parts = parsed_annual_report.find_all(string=parts)  # list of all elements that contain any of the parts in the list above

    # list of actual part seperating elements
    # note that the the actual seperating elements are stored in spans!
    parsed_parts_clean = [part for part in parsed_parts if part.parent.name != "a" and part.parent.parent.name != "a"]                              
    return parsed_annual_report, parsed_parts_clean # returns tuple 

 #############################################################################################
 ##################################### EXTRACTING PARTS ######################################
 #############################################################################################

  def extract_parts(self, parsed_parts):

    """
    Extracts The Elements Between The Parts (1,2,3,4)
    """

    part1 = parsed_parts[0].parent.parent       # access the grand parent because the first parent is the tag
    part2 = parsed_parts[1].parent.parent       # that wraps the text "PART I", this is usually the <span>
    part3 = parsed_parts[2].parent.parent       # the tag that wraps the <span> is usually a <div>
    part4 = parsed_parts[3].parent.parent

    elements_part1_to_part2 = self.find_elements_inbetween(part1, part2)     
    elements_part2_to_part3 = self.find_elements_inbetween(part2, part3)
    elements_part3_to_part4 = self.find_elements_inbetween(part3, part4)

    return {"part1":elements_part1_to_part2, 
            "part2":elements_part2_to_part3, 
            "part3":elements_part3_to_part4, 
            "part4":part4} # !! WARN: part 4 might not be a Beautiful Soup !!



  #############################################################################################
  ##################################### EXTRACTING ITEMS ######################################
  #############################################################################################

  def extract_all_items_from_table_contents(self, parsed_annual_report: BeautifulSoup): 
    """
    Extracts All The Item Names From Table Of Cotents.
    """
    table_of_contents_header = parsed_annual_report.find_all(string=re.compile("^Table.Of.Contents$", re.I))
    table_of_contents_header_clean = [header for header in table_of_contents_header if header.parent.name != "a" and header.parent.parent.name != "a"]
    parts_item_dict = {"part1":[], "part2": [], "part3":[], "part4":[]}

    if table_of_contents_header_clean == None:
      print("Error, no table of contents found (using the clean headers)")
    else:

      table_of_contents = table_of_contents_header_clean[0].find_next("table")

    # match each item here, and assign them to the corresponding part
    for tr in table_of_contents.find_all("tr"):
        for td in tr.find_all("td"):
          if td.string != None:
            if re.match(re.compile("^Item.[1-4]{1}[A-Z]?\.$",re.I), td.string) != None:
              parts_item_dict["part1"].append(re.search(re.compile("[0-9]+[A-Z]?", re.I),td.string).group())
            elif re.match(re.compile("^Item.[5-9]{1}[A-Z]?\.$",re.I), td.string) != None:
              parts_item_dict["part2"].append(re.search(re.compile("[0-9]+[A-Z]?", re.I),td.string).group())
            elif re.match(re.compile("^Item.1[0-4]{1}[A-Z]?\.$",re.I), td.string) != None:
              parts_item_dict["part3"].append(re.search(re.compile("[0-9]+[A-Z]?", re.I),td.string).group())
            elif re.match(re.compile("^Item.1[5-6]{1}[A-Z]?\.$",re.I), td.string) != None:
              parts_item_dict["part4"].append(re.search(re.compile("[0-9]+[A-Z]?", re.I),td.string).group())

    return parts_item_dict



  def extract_all_items(self, part_elements_dict: dict, part_items_dict: dict) -> dict:
    """
    Wrapper Function That Makes Calls To extract_items() To Extract Items From All Parts 
    Of The Annual Report.

    parameters: 
      part_elements_list -> list of all elements for every part

    returns:
      dict ->  dictionary with the following structure 
        1st layer (key: itme name, value: BeautifulSoup object )
    """
    print("part items dict")
    print(part_items_dict)
    item_dict = {}
    for part in range(1, 3):  # NOTE: Currently iterating through Part 1 and 2 only
       part_name = f"part{part}"
       print(f"part name: {part_name}")
       parts_item_dict = self.extract_items(part_elements_dict[part_name], part_items_dict[part_name])
       #print(parts_item_dict)
       item_dict = {**item_dict, **parts_item_dict}


    return item_dict


  def extract_items(self, part_elements: BeautifulSoup, items: list) -> dict:
    """
    Extracts the Items Within A Specific Part Of The Annual Report.

    parameters:
      parts_element:BeautifulSoup -> all of the elements for a specific part of the 10K
      part_number:int -> the number of the part 
    returns:
      dict -> key value pair (key: name of item, value: BeautifulSoup object of all elements in item)
    """

    items_dict = {}
    parsed_items = []
    for item in items:
    
         
   
      regex = re.compile(f"^Item.{item}\.?$", re.I)
      item_elements = list(part_elements.find_all(string=regex))

      if item == "1A":
         for element in item_elements:
            print(element.parent.parent.name)

      if len(item_elements) == 0:
          print(f"no element found for item: item{item}")
      else:
        parsed_items.extend(item_elements)  

    print(parsed_items)

    # list of actual part seperating elements
    # note that the the actual seperating elements are stored in spans!
    # these are just navigable strings
    print(len(parsed_items))
    parsed_items_clean = [part for part in parsed_items if part.parent.name != "a" and
                          part.parent.parent.name != "a" 
                          and len(list(part.parent.next_siblings)) == 0
                          and len(list(part.parent.previous_siblings)) == 0]   

    print(len(parsed_items_clean))
    print("parsed items clean")
    print(parsed_items_clean)
    # iterate through all of the items (expect for the last)
    for item_index in range(0, len(parsed_items_clean) - 1):
        start_item = self.find_tag_with_siblings(parsed_items_clean[item_index])
        end_item = self.find_tag_with_siblings(parsed_items_clean[item_index + 1])
        key = items[item_index]

        items_dict[key] = self.find_elements_inbetween(start_item, end_item)
  
    # TODO: figure out how to parse the last item in the part!!!

    return items_dict
  

  #############################################################################################
  ##################################### HELPER FUNCTIONS ######################################
  #############################################################################################


  def find_elements_inbetween(self, element_1, element_2) -> BeautifulSoup:

    """
    Useful Function To Find All The Elements Between Two Elements 
    """
    element_list = []      # list that stores bs4.element.Tag
    
    soup = BeautifulSoup(str(element_1), "html.parser")
    element_1_in_soup = soup.find(element_1.name)

    for element in element_1.next_siblings:                 # iterate through the all of the elements that come after 
        element_list.append(copy.copy(element))             # element_1, this is in element_1.next_siblings

        if element == element_2:                            # if the second element is encountered then break out of loop
            break
    
    for element in element_list[::-1]:

        element_1_in_soup.insert_after(element)
    
    return soup


  def find_tag_with_siblings(self, tag):
    curr_tag = tag

    while len(list(curr_tag.next_siblings)) == 0:
       curr_tag = curr_tag.parent

    return curr_tag


  def extract_specific_item(self, elements: BeautifulSoup, part_num:int, item:re.Pattern):
    
    """
    Extract A Specific Item For A Specific Part Of The Annual Report.
    """

    items_list = elements.find_all(string=item)
    items_list_cleaned = [item_element for item_element in items_list if item_element.parent != "a"]

  #############################################################################################
  ############################## EXTRACTING FINANCIAL STATEMENTS ##############################
  #############################################################################################
  def extract_income_statement(self):
     
    """
    Extracts The Income Statement From Part 2, Item 8 Financal Statements Of The Annual Report.

    parameters: None
    returns: ??? 
    """
    item8 = self.get_item("8")

    # possible names for the income statement in annual report
    statement_names = [re.compile("^Consolidated Statements of $", re.I), 
                       re.compile("^Consolidated Statements of Income", re.I),
                       re.compile("^Consolidated Statements of Operations", re.I)]  

    # loop through all the possible names for the Income Statement and break
    # from loop when one is found!
    for statement_name in statement_names:
        elements = item8.find_all(string=statement_name)
        print(elements)
        if len(list(elements)) != 0:
            break
        
    years = []
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


        # matches with not None String or $ sign
        if td.string != None and td.string != "$":   

          # match with year
          if re.match(re.compile(".*[0-9]{4}$"), td.string) != None:
            years.append(td.string)

          # matches with a value for a reported metric if XBRL doesn't exist
          elif re.match(re.compile("^\(?[0-9]{1,3}(,[0-9]{3})*\)?$"), td.string) != None:
            if income_statement_name not in statement_name_list:
              metric_values[income_statement_name] = [td.string]
            else:
              metric_values[income_statement_name].append(td.string)
        
          # otherwise this should be the name of a value in the income statement
          else:
            income_statement_name = td.string  # define income_statment_name here

        # matches with any XBRL element
        elif td.find("ix:nonfraction") != None: 
          xbrl_element = td.find("ix:nonfraction")  # xbrl_element is the html element <ix:nonfraction>
          xbrl_concept_name = xbrl_element["name"]  # xbrl_element["name"] is the value of the name attribute in the XBRL element tag                                                       
          xbrl_concept_value = xbrl_element.string  # the actual value of the XBRL concept

          if income_statement_name not in xbrl_dictionary.keys():
              xbrl_dictionary[income_statement_name] = xbrl_concept_name   # store the concept name in dictionary
              statement_name_list.append(income_statement_name)   # adds the metric name as reported to the list 
              metric_values[income_statement_name] = []           # create initial key value pair

          metric_values[income_statement_name].append(xbrl_concept_value)

          #print(td.find("ix:nonfraction")["name"])       # print the name of the (XBRL) concept 
          #print(td.find("ix:nonfraction").string)        # print the value of the (XBRL) element

    

    return xbrl_dictionary, metric_values, statement_name_list, years
  

  def find_item8(self, part2):
    item_8 = part2.find_all(string=re.compile("Item.8..Financial.Statements", re.I)) # note ignore case
    return item_8
  
  def find_income_statements(self, cik:str):
    
    urls = ws.json_submission_scraper(cik, "10-K")  # get all the URLS of the 10-Ks
    
    count = 1
    for url in urls:
      
      parsed_annual_report, parsed_parts_clean = self.scrape_annual_report(url)
      parts_list = self.extract_parts(parsed_parts_clean)
      item8 = self.find_item8(parts_list[1])
      xbrl_dictionary , metric_values, statement_name_list = income_statement(item8)
      
      xbrl_dictionary_string = ""
      for key,value in xbrl_dictionary.items:
         xbrl_dictionary_string += f"{key}:{value}\n"

      with open(f"../data/company data/LULU/annual report {count}.txt", "w+") as file:
        file.write(xbrl_dictionary_string)
          
