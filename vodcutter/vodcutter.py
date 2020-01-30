import pickle
import os
import sys
import datetime
import re
import json

import gdown

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


def auth():
    # Auth
    creds = None

    token_path = "creds/token.pickle"
    creds_path = "creds/credentials.json"

    if not os.path.exists(creds_path):
        raise Exception("<!!> Creds JSON cannot be found in %s" % creds_path)

    if os.path.exists(token_path):
        with open(token_path, "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "creds/credentials.json", SCOPES
            )

            creds = flow.run_console()
        
        with open(token_path, "wb") as token:
            pickle.dump(creds, token)

    return creds


def get_spreadsheet_service(creds):
    service = build("sheets", "v4", credentials=creds)
    return service.spreadsheets()
 

def get_sheet_name_by_id(spreadsheet_service, spreadsheet_id, sheet_id):
    spreadsheet = spreadsheet_service.get(
        spreadsheetId=spreadsheet_id,
    ).execute()
    
    for _sheet in spreadsheet["sheets"]:
        if str(_sheet["properties"]["sheetId"]) == str(sheet_id):
            return _sheet["properties"]["title"]
    else:
        raise Exception("Can't find sheet with id %s" % sheet_id)


def get_info(creds, spreadsheet_id, sheet_id):
    spreadsheet_service = get_spreadsheet_service(creds) 

    sheet_name = get_sheet_name_by_id(spreadsheet_service, spreadsheet_id, sheet_id)

    spreadsheet = spreadsheet_service.values().get(
        spreadsheetId=spreadsheet_id,
        range=sheet_name + "!A3:G12"
    ).execute()
    
    return spreadsheet.get("values", [])


def get_vod_source_address(creds, spreadsheet_id, sheet_id):
    spreadsheet_service = get_spreadsheet_service(creds)

    spreadsheet = spreadsheet_service.get(
        spreadsheetId=spreadsheet_id,
    ).execute()
    
    sheet_name = get_sheet_name_by_id(spreadsheet_service, spreadsheet_id, sheet_id)

    gdrive_link_range = spreadsheet_service.values().get(
        spreadsheetId=spreadsheet_id,
        range=sheet_name + "!K1"
    ).execute()
    
    values = gdrive_link_range.get("values", [])
    return values[0][0]


def make_vod_name(vod_name, title, streamer_name, date, time):
    date_parsed  = datetime.datetime.strptime(date, "%d/%m/%Y")
    time_parsed  = datetime.datetime.strptime(time, "%H:%M")
    new_date = date_parsed.strftime("%Y%m%d")
    new_time = time_parsed.strftime("%H%M")
    title = title.strip(" \n\t").replace(" ", "")
    streamer_name = streamer_name.strip(" \n\t").replace(" ", "")
    return "_".join([vod_name, new_date, new_time, streamer_name, title])


def cut_video(input_video, tc_start, tc_end, output_video):
    cmd = 'ffmpeg -i "%s" -ss "%s" -to "%s" -c:v copy -c:a copy "%s"' % (input_video, tc_start, tc_end, output_video)
    print("<i> Executing command %s" % cmd)
    os.system(cmd)
    print()


def download(gdrive_file_url):
    url_reg = re.search(r"id=([^&]*)", gdrive_file_url)
    if not url_reg:
        raise Exception("Invalid Google Drive url: %s" % url_reg)
    
    gdrive_file_id = url_reg.group(1)
    gdrive_file_url = "https://drive.google.com/uc?id=%s" % gdrive_file_id
    
    output_file = gdown.download(gdrive_file_url, None, False, None)
    return output_file


def main(input_video, output_path, spreadsheet_id, sheet_id):
    creds = auth()
    values = get_info(creds, spreadsheet_id, sheet_id)

    spreadsheet_service = get_spreadsheet_service(creds)
    sheet_name = get_sheet_name_by_id(spreadsheet_service, spreadsheet_id, sheet_id)

    abs_output_path = os.path.abspath(output_path)

    if not os.path.exists(abs_output_path):
        os.makedirs(abs_output_path)
    
    for v in values:
        tc_start = v[0]
        tc_end   = v[1]
        streamer = v[2]
        title    = v[3]
        date     = v[4]
        time     = v[5]

        vod_name = make_vod_name(
            sheet_name,
            title,
            streamer,
            date,
            time,
        )

        output_video_full_path = "%s/%s.%s" % (abs_output_path, vod_name, "mp4")

        cut_video(input_video, tc_start, tc_end, output_video_full_path)


if __name__ == "__main__":
    input_video = sys.argv[1]
    sheet_name = sys.argv[2]

    main(input_video, sheet_name)
    
