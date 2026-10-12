from playwright.sync_api import sync_playwright
from dq import *
T="dqlab_oracle.default.dqlab."
TESTS = [
 ("EMPLOYEES","employees_staff_no_unique","Column Values To Be Unique","staff_no",{}),
 ("EMPLOYEES","employees_hire_date_format","Column Values To Match Regex Pattern","hire_date",{"regex":"^[0-9]{4}-[0-9]{2}-[0-9]{2}$"}),
 ("SALARIES","salaries_base_amount_between_1_and_100000","Column Values To Be Between","base_amount",{"min":1,"max":100000}),
 ("SALARIES","salaries_currency_sar","Column Values To Be In Set","currency",{"allowed":["SAR"],"match_enum":True}),
 ("ALLOWANCES","allowances_type_allowed","Column Values To Be In Set","alw_type",{"allowed":["HOUSING","TRANSPORT","OTHER"],"match_enum":True}),
 ("ALLOWANCES","allowances_amount_min_0","Column Values To Be Between","amount",{"min":0}),
]
with sync_playwright() as p:
    b, page = open_page(p)
    for tbl,name,tt,col,params in TESTS:
        create_test(page, T+tbl, name, tt, column=col, params=params)
        print("created", name)
    b.close()
