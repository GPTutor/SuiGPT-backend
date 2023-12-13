import pandas as pd
import os
from datetime import datetime
from uuid import uuid4

import gspread
import numpy as np
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

auth_json_path = "./savvy-hall-270205-7624fd8449a8.json"

# 我們使用的範圍僅有 Google Sheet
gss_scopes = ["https://spreadsheets.google.com/feeds"]

# 連線
credentials = ServiceAccountCredentials.from_json_keyfile_name(
    auth_json_path, gss_scopes
)
gss_client = gspread.authorize(credentials)

df_key = "1DrjLQnYGKMtJHt0B0jfU3I7MuQPadUYxHnbVZKSNH9w"
gss = gss_client.open_by_key(df_key)



def get_sheet(sheet_name, key = df_key):
    gss_client = gspread.authorize(credentials)
    gss = gss_client.open_by_key(key)
    
    sheet = None
    sheets = gss.worksheets()
    for target_sheet in sheets:
        if sheet_name == target_sheet.title:
            sheet = target_sheet
    if sheet == None:
        sheet = gss.add_worksheet(sheet_name, 0, 0)
    return sheet


def get_sheet_df(sheet_name, key = df_key):
    gss_client = gspread.authorize(credentials)
    gss = gss_client.open_by_key(key)
    sheet = get_sheet(sheet_name)
    df = pd.DataFrame(sheet.get_all_records())
    return df

def get_gss(key = df_key):
    gss_client = gspread.authorize(credentials)
    gss = gss_client.open_by_key(key)
    return gss

def overwrite_sheet(sheet, output_df, key = df_key):
    gss_client = gspread.authorize(credentials)
    gss = gss_client.open_by_key(key)
    sheet.clear()
    sheet.update([output_df.columns.values.tolist()] + output_df.values.tolist())
