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

    vod_provider = config.get("vod_provider", None)
    vod_path_cutted = config.get("vod_path_cutted", None)


    vod_src_address = cutter.get_vod_source_address(creds, spreadsheet_id, sheet_id)
    
    if vod_provider == "gdrive":
        sheet_name = cutter.get_sheet_name_by_id(spreadsheet_service, spreadsheet_id, sheet_id) 
        vod_filename = sheet_name + ".mp4"
        vod_full_path = "%s/%s" % (vod_path_full, vod_filename)

        if not os.path.exists(vod_filename):
            print("<i> VOD not existing, downloading")

            gdrive_link = vod_src_address
            video_path = cutter.download(gdrive_link)

            os.rename(video_path, vod_full_path)

        else:
            print("<i> VOD already exists, skipping download!")

    elif vod_provider == "file":
        vod_path_full = config.get("vod_path_full", None)

        vod_filename = vod_src_address

        vod_full_path = "%s/%s" % (vod_path_full, vod_filename)

    else:
        raise Exception("<!!> Unknown VOD provider '" + vod_provider + "'")

    cutter.main(vod_full_path, vod_path_cutted, spreadsheet_id, sheet_id)
    
    return ""

