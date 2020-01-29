from flask import Flask
import os
import json

import vodcutter.vodcutter as cutter


app = Flask(__name__)


def _load_config():
    fp = open("config.json", "r")
    config = json.load(fp)
    fp.close()
    return config


@app.route('/vodcutter/spreadsheet/<string:spreadsheet_id>/sheet/<int:sheet_id>')
def vodcutter(spreadsheet_id, sheet_id):
    config = _load_config()

    creds = cutter.auth()
    spreadsheet_service = cutter.get_spreadsheet_service(creds)
    sheet_name = cutter.get_sheet_name_by_id(spreadsheet_service, spreadsheet_id, sheet_id) 
    vod_target_filename = sheet_name + ".mp4"
    
    if config["vod_provider"] == "gdrive":
        if not os.path.exists(vod_target_filename):
            print("<i> VOD not existing, downloading")
            gdrive_link = cutter.get_gdrive_link(creds, spreadsheet_id, sheet_id)
            video_path = cutter.download(gdrive_link)
            os.rename(video_path, vod_target_filename)
        else:
            print("<i> VOD already exists, skipping download!")

    elif config["vod_provider"] == "file":
        pass

    cutter.main(vod_target_filename, spreadsheet_id, sheet_id)
    
    return ""

