import os
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime
import threading

class GoogleSheet:
    def __init__(self):
        self.credentials_json = 'house-appliance-status-8f7e0863c9c0.json'
        self.sheet_id = '1aSnYQlI7kVIgtsb5gRA0Jk9zHx8Qg_RoDlhDSqLODZ8'
        self.sheet_name = '모든제품'  # Replace with the name of the sheet you want to access
        self.change_parts_json = None
        self.clean_parts_json = None
        self.sheets_api = None
        self.loaded_data = None
        self.load_house_appliance_df()
        
    def _load_sheet(self, credentials_json, sheet_id, sheet_name):
        # Set the path to the downloaded JSON key file
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_json
        range_name = f'{sheet_name}!A1:Z'

        # Create the credentials object
        creds = service_account.Credentials.from_service_account_file(os.environ['GOOGLE_APPLICATION_CREDENTIALS'])

        # Create a Sheets API client
        self.sheets_api = build('sheets', 'v4', credentials=creds)

        # Fetch data from the Google Sheet
        response = self.sheets_api.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=range_name
        ).execute()

        # Display the fetched data
        self.loaded_data = response['values']
        return self.loaded_data

    def load_house_appliance_df(self):
        data = self._load_sheet(self.credentials_json, self.sheet_id, self.sheet_name)

        # Separator
        sep = '브랜드'

        sep_begin_idx = []
        sep_end_idx = []
        for i, row in enumerate(data):
            if sep in row:
                # print(i, sep)
                sep_begin_idx.append(i)
            elif len(sep_begin_idx) > len(sep_end_idx):
                if len(row) == 0:
                    sep_end_idx.append(i)
                else:
                    if row[0] == '':
                        # print('None')
                        sep_end_idx.append(i)
        # print(sep_begin_idx)
        # print(sep_end_idx)
        
        change_parts = data[sep_begin_idx[0]:sep_end_idx[0]]
        if len(sep_begin_idx) > len(sep_end_idx):
            clean_parts = data[sep_begin_idx[1]:]
        else:
            clean_parts = data[sep_begin_idx[1]:sep_end_idx[1]]

        self.change_parts_df = pd.DataFrame(change_parts[1:], columns=change_parts[0])
        self.clean_parts_df = pd.DataFrame(clean_parts[1:], columns=clean_parts[0])

    
    def _convert_df_to_json(self):
        self.change_parts_json = self.change_parts_df.to_json(orient='records')
        self.clean_parts_json = self.clean_parts_df.to_json(orient='records')


    def get_house_appliance_df(self):
        return self.change_parts_df, self.clean_parts_df
    
    def get_house_appliance_json(self):
        if self.change_parts_json is None or self.clean_parts_json is None:
            self._convert_df_to_json()
        return self.change_parts_json, self.clean_parts_json

    def _filter_rows(self, df_list, col_name, val):
        for i, df in enumerate(df_list):
            # print('df: ', df)
            df_list[i] = df.loc[df[col_name] == val]
        return df_list

    def get_item_by_stat_json(self, is_ok):
        selected_change_parts_df = self.change_parts_df[['종류', '내용', '비고', 'id']]
        selected_clean_parts_df = self.clean_parts_df[['종류', '내용', '비고', 'id']]
        # print(selected_change_parts_df)

        df_list = self._filter_rows([selected_change_parts_df, selected_clean_parts_df], 
                                    '비고', 
                                    '_' if is_ok else '교체 해야 함')
        # print(df_list)
        change_parts_json = df_list[0].to_json(orient='records')
        clean_parts_json = df_list[1].to_json(orient='records')
        # print(change_parts_json)
        return change_parts_json, clean_parts_json
    
    # change the last date to be today
    def update_item_status(self, item_id):
        if self.sheets_api is not None:
            # Find the cell position
            id_col_num = -1
            data_col_num = -1
            cell_position = ''
            for row_num, row_values in enumerate(self.loaded_data):
                # If no data in a row, it should skip searching
                if len(row_values) < 6:
                    continue
                # Find ID column
                if id_col_num < 0 and data_col_num < 0:
                    for col_num, value in enumerate(row_values):
                        if value == 'id':
                            id_col_num = col_num
                        if value == '완료':
                            data_col_num = col_num
                # Find ID value
                elif row_values[id_col_num] == item_id:
                    cell_position = chr(data_col_num + 65) + str(row_num + 1)
                    print('Cell position:', cell_position)
                    break
            # Today [yyyy-m-d] or [yyyy-mm-dd]
            today = datetime.today()
            date_string = today.strftime('%Y-%-m-%-d')

            cell_position = cell_position
            # Wrap data 
            range_name = f'{self.sheet_name}!{cell_position}'
            sending_val = [[date_string]]

            # print(id_col_num, data_col_num, cell_position)
            # print(date_string)
            # print(range_name)

            # Update the values in the sheet
            result = self.sheets_api.spreadsheets().values().update(
                spreadsheetId=self.sheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                body={
                    'values': sending_val
                }
            ).execute()

            print('{0} cells updated.'.format(result.get('updatedCells')))

    def load_once_a_day(self):
        print('Data Loading...')
        self.load_house_appliance_df()
        threading.Timer(84600 / 2, self.load_once_a_day).start()