from playwright.sync_api import sync_playwright
from dq import *
T="dqlab_mysql.default.dqlab."
EMAIL=r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+[.][A-Za-z]{2,}$"
C=lambda **k: dict(compute_row_count=True, **k)
TESTS = [
 ("customers","customers_full_name_not_null","Column Values To Be Not Null","full_name",C(),"Every customer has a name."),
 ("customers","customers_email_unique","Column Values To Be Unique","email",C(),"No two customers share an email."),
 ("customers","customers_email_format","Column Values To Match Regex Pattern","email",C(regex=EMAIL),"Email looks like an email address."),
 ("customers","customers_age_between_18_and_90","Column Values To Be Between","age",C(min=18,max=90),"Customer age is between 18 and 90."),
 ("customers","customers_country_allowed","Column Values To Be In Set","country",C(allowed=["SA","AE","KW","EG","QA","BH","OM","JO","GB","US"],match_enum=True),"Country is one of the ten served."),
 ("products","products_sku_unique","Column Values To Be Unique","sku",C(),"Every product has its own SKU."),
 ("products","products_unit_price_min_1","Column Values To Be Between","unit_price",C(min=1),"Unit price is at least 1."),
 ("products","products_category_not_null","Column Values To Be Not Null","category",C(),"Every product has a category."),
 ("orders","orders_amount_min_1","Column Values To Be Between","amount",C(min=1),"Order amount is at least 1."),
 ("orders","orders_quantity_min_1","Column Values To Be Between","quantity",C(min=1),"Order quantity is at least 1."),
 ("orders","orders_status_allowed","Column Values To Be In Set","status",C(allowed=["pending","shipped","delivered","cancelled"],match_enum=True),"Order status is one of the four allowed."),
]
SQL = [
 ("orders","orders_no_orphans","""SELECT o.order_id, o.customer_id, o.product_id
FROM dqlab.orders o
LEFT JOIN dqlab.customers c ON c.customer_id = o.customer_id
LEFT JOIN dqlab.products p ON p.product_id = o.product_id
WHERE c.customer_id IS NULL OR p.product_id IS NULL""","Every order points at a real customer and product."),
 ("orders","orders_no_future_dates","SELECT order_id, order_date FROM dqlab.orders WHERE order_date > NOW()","No order is dated in the future."),
]
with sync_playwright() as p:
    b, page = open_page(p)
    for tbl,name,tt,col,params,desc in TESTS:
        create_test(page, T+tbl, name, tt, column=col, params=params, description=desc); print("created", name)
    for tbl,name,sql,desc in SQL:
        create_test(page, T+tbl, name, "Custom SQL Query", sql=sql, params={"strategy":"ROWS","operator":"<=","threshold":0,"compute_row_count":True}, description=desc); print("created", name)
    b.close()
