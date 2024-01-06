from annualreport import AnnualReport

class Company:

    name = None
    ticker = None
    cik = None

    annual_reports = None
    
    financial_statements_dict = {}
    income_statement_dict = {}
    balance_sheet_statement_dict = {}
    cash_flow_statement_dict = {}
    
    
    def __init__(self, name:str, annual_reports: AnnualReport) -> None:
        self.name = name
        self.annual_reports = annual_reports