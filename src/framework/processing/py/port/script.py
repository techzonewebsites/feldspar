import port.api.props as props
from port.api.assets import *
from port.api.commands import (CommandSystemDonate, CommandSystemExit, CommandUIRender)

import pandas as pd
import zipfile
import json
import datetime
import pytz
import fnmatch
import hashlib
from collections import defaultdict, namedtuple
from contextlib import suppress
from datetime import datetime


def retry_confirmation():
    text = props.Translatable({
        "en": "Unfortunately, we cannot process your file. Continue, if you are sure that you selected the right file. Try again to select a different file.",
        "de": "Leider können wir Ihre Datei nicht bearbeiten. Fahren Sie fort, wenn Sie sicher sind, dass Sie die richtige Datei ausgewählt haben. Versuchen Sie, eine andere Datei auszuwählen.",
        "nl": "Helaas, kunnen we uw bestand niet verwerken. Weet u zeker dat u het juiste bestand heeft gekozen? Ga dan verder. Probeer opnieuw als u een ander bestand wilt kiezen."
    })
    ok = props.Translatable({
        "en": "Try again",
        "de": "Versuchen Sie es noch einmal",
        "nl": "Probeer opnieuw"
    })
    cancel = props.Translatable({
        "en": "Continue",
        "de": "Weiter",
        "nl": "Verder"
    })
    return props.PropsUIPromptConfirm(text, ok, cancel)

def hash_username(username):
    username_bytes = username.encode('utf-8')
    hash_object = hashlib.sha256()
    hash_object.update(username_bytes)
    hex_digest = hash_object.hexdigest()
    return hex_digest

def get_zipfile(filename):
    try:
        return zipfile.ZipFile(filename)
    except zipfile.error:
        return "invalid"
    
   
def get_files(zipfile_ref):
    try: 
        return zipfile_ref.namelist()
    except zipfile.error:
        return []

# =====================
def glob(zipfile, pattern):
    return fnmatch.filter(zipfile.namelist(), pattern)


def glob_json(zipfile, pattern):
    for name in glob(zipfile, pattern):
        with zipfile.open(name) as f:
            yield json.load(f)

def load_json(path):
    with open(path) as f:
        return json.load(f)

# =====================

def extract_file(zipfile_ref, filename):
    try:
        # make it slow for demo reasons only
        time.sleep(1)
        info = zipfile_ref.getinfo(filename)
        return (filename, info.compress_size, info.file_size)
    except zipfile.error:
        return "invalid"

def extract_id(jsonfile):
    try:
        username = jsonfile.get('Profile', {}).get('Profile Information', {}).get('ProfileMap').get('userName', [])
        username = hash_username(username)

    except Exception as e:
        print(f"Error extracting ID: {e}")

    return ExtractionResult(
        "id",
        props.Translatable({"en": "Your Random ID", "nl": "Your Random ID"}),
        pd.DataFrame([username])
    )

def extract_likes(jsonfile):

    like_list = []
    print('Trying to extract likes...')

    try:

        # Extract the "Like List"
        item_favorite_list = jsonfile.get('Activity', {}).get('Like List', {}).get('ItemFavoriteList', [])

        for idx, item in enumerate(item_favorite_list):
            date = item.get('Date', '')
            link = item.get('Link', '')
            if date and link:
                like_list.append({'Date': date, 'Link': link})
            else:
                print(f"Like {idx+1} is missing 'Date' or 'Link'. Skipping.")

    except Exception as e:
        print(f"Error extracting Like List: {e}")

    print(f"Total likes extracted: {len(like_list)}")
    return ExtractionResult(
        "likes",
        props.Translatable({"en": "Likes", "nl": "Likes"}),
        pd.DataFrame(like_list)
    )


def extract_watch_history(jsonfile):

    watch_history_list = []
    print('Trying to extract likes...')

    try:

        # Extract the "VideoList"
        json_videos = jsonfile.get('Activity', {}).get('Video Browsing History', {}).get('VideoList', [])

        for idx, item in enumerate(json_videos):
            date = item.get('Date', '')
            link = item.get('Link', '')
            if date and link:
                watch_history_list.append({'Date': date, 'Link': link})
            else:
                print(f"Like {idx+1} is missing 'Date' or 'Link'. Skipping.")

    except Exception as e:
        print(f"Error extracting Like List: {e}")

    print(f"Total videos extracted: {len(watch_history_list)}")
    return ExtractionResult(
        "WatchHistory",
        props.Translatable({"en": "Watch History", "nl": "Watch History"}),
        pd.DataFrame(watch_history_list)
    )

def extract_logins(jsonfile):
    logins_list = []
    print('Trying to extract logins...')

    try:

        # Extract the "VideoList"
        json_videos = jsonfile.get('Activity', {}).get('Login History', {}).get('LoginHistoryList', [])

        for idx, item in enumerate(json_videos):
            date = item.get('Date', '')
            device = item.get('DeviceModel', '')
            network = item.get('NetworkType', '')
            
            if date and device and network:
                logins_list.append({'Date': date, 
                                    'Device': device, 
                                    'Network': network})
            else:
                print(f"Like {idx+1} is missing 'Date' or 'Device'. Skipping.")

    except Exception as e:
        print(f"Error extracting Login List: {e}")

    print(f"Total logins extracted: {len(logins_list)}")
    return ExtractionResult(
        "LoginHistory",
        props.Translatable({"en": "Login History", "nl": "Login History"}),
        pd.DataFrame(logins_list)
    )

def extract_video_uploads(jsonfile):
    uploads_list = []
    print('Trying to extract logins...')

    try:
        # Extract the "VideoList"
        json_videos = jsonfile.get('Video', {}).get('Videos', {}).get('VideoList', [])

        for idx, video in enumerate(json_videos):
            date_str = video.get('Date', '')
            likes_str = video.get('Likes', '0')

            if date_str:
                try:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                    year = date_obj.year
                    week_num = date_obj.isocalendar()[1]
                except ValueError:
                    print(f"Invalid date format for video {idx+1}. Skipping.")
                    continue
            else:
                print(f"Video {idx+1} is missing 'Date'. Skipping.")
                continue

            try:
                likes = int(likes_str)
            except ValueError:
                print(f"Invalid likes count for video {idx+1}. Setting Likes to 0.")
                likes = 0

            uploads_list.append({'Year': year, 'Week': week_num, 'Likes': likes})
            print(f"Extracted Video {idx+1}: Year={year}, Week={week_num}, Likes={likes}")

    except Exception as e:
        print(f"Error extracting video uploads: {e}")

    print(f"Total uploads extracted: {len(uploads_list)}")
    return ExtractionResult(
        "UploadHistory",
        props.Translatable({"en": "Upload History", 
                            "nl": "Upload History"}),
        pd.DataFrame(uploads_list)
    )

def extract_purchases(jsonfile):

    gifts_list = []
    print('Trying to extract likes...')

    try:

        # Extract the "VideoList"
        json_gifts = jsonfile.get('Activity', {}).get('Purchase History', {}).get('BuyGifts', [])

        for idx, item in enumerate(json_gifts):
            date = item.get('Date', '')
            value = item.get('Value', '')
            if date and link:
                gifts_list.append({'Date': date, 'Value': value})
            else:
                print(f"Purchase {idx+1} is missing 'Date' or 'Value'. Skipping.")

    except Exception as e:
        print(f"Error extracting Purchase List: {e}")

    print(f"Total videos extracted: {len(gifts_list)}")
    return ExtractionResult(
        "PurchaseHistory",
        props.Translatable({"en": "Purchase History", "nl": "Purchase History"}),
        pd.DataFrame(gifts_list)
    )

# main function to extract all various data from the JSON file
def extract_data(path):
    print('started extracting data')
    extractors = [
        extract_id,
        extract_likes,
        extract_watch_history,
        extract_logins,
        extract_video_uploads,
        extract_purchases
    ]

    jsonfile = load_json(path)
    # zfile = zipfile.ZipFile(path)
    return [extractor(jsonfile) for extractor in extractors]

def prompt_consent(data, meta_data):

    table_title = props.Translatable({
        "en": "JSON file contents",
        "de": "Inhalt der JSON-Datei",
        "nl": "Inhoud JSON bestand"
    })

    log_title = props.Translatable({
        "en": "Log messages",
        "de": "Log Nachrichten",
        "nl": "Log berichten"
    })

    tables=[]
    if data is not None:
        data_frame = pd.DataFrame(data, columns=["filename", "compressed size", "size"])
        tables = [props.PropsUIPromptConsentFormTable("zip_content", table_title, data_frame)]

    meta_frame = pd.DataFrame(meta_data, columns=["type", "message"])
    meta_table = props.PropsUIPromptConsentFormTable("log_messages", log_title, meta_frame)
    return props.PropsUIPromptConsentForm(tables, [meta_table])


######################
# Data donation flow #
######################


ExtractionResult = namedtuple("ExtractionResult", ["id", "title", "data_frame"])
# ExtractionResult = namedtuple("ExtractionResult", ["id", "title", "data_frame", "visualizations"])


class SkipToNextStep(Exception):
    pass


class DataDonationProcessor:
    
    def __init__(self, platform, mime_types, extractor, session_id):
        self.platform = platform
        self.mime_types = mime_types
        self.extractor = extractor
        self.session_id = session_id
        self.progress = 0
        self.meta_data = []

    def process(self):
    
        with suppress(SkipToNextStep):
            while True:
                
                file_result = yield from self.prompt_file()

                self.log(f"extracting file")
                print('made it to DataDonationProcessor.process()')
                try:
                    extraction_result = self.extract_data(file_result.value)
                    print("made it past extract_data(), now what")
                except (IOError, zipfile.BadZipFile):
                    self.log(f"prompt confirmation to retry file selection")
                    try_again = yield from self.prompt_retry()
                    if try_again:
                        continue
                    return
                else: # execute if no exception
                    if extraction_result is None:
                        try_again = yield from self.prompt_retry()
                        if try_again:
                            continue
                        else:
                            return
                    self.log(f"extraction successful, go to consent form")
                    yield from self.prompt_consent(extraction_result)
                    return


    def prompt_retry(self):
        retry_result = yield render_donation_page(
            self.platform, retry_confirmation(self.platform), self.progress
        )
        return retry_result.__type__ == "PayloadTrue"

    # def prompt_file(self):
    #     description = props.Translatable(
    #         {
    #             "en": f"Please follow the download instructions and choose the file that you stored on your device. Click “Skip” at the right bottom, if you do not have a {self.platform} file. ",
    #             "nl": f"Volg de download instructies en kies het bestand dat u opgeslagen heeft op uw apparaat. Als u geen {self.platform} bestand heeft klik dan op “Overslaan” rechts onder.",
    #         }
    #     )
    #     prompt_file = props.PropsUIPromptFileInput(description, self.mime_types)
    #     file_result = yield render_donation_page(
    #         self.platform, prompt_file, self.progress
    #     )
    #     if file_result.__type__ != "PayloadString":
    #         self.log(f"skip to next step")
    #         raise SkipToNextStep()
    #     return file_result

    def prompt_file(self):
        description = props.Translatable({
            "en": "Please select your TikTok JSON file.",
            "de": "Wählen Sie eine beliebige Zip-Datei aus, die Sie auf Ihrem Gerät gespeichert haben.",
            "nl": "Selecteer een willekeurige zip file die u heeft opgeslagen op uw apparaat."
        })
        return props.PropsUIPromptFileInput(description, extensions)
    
    def prompt_extraction_message(message, percentage):
        description = props.Translatable({
            "en": "One moment please. Information is now being extracted from the selected file.",
            "de": "Einen Moment bitte. Es werden nun Informationen aus der ausgewählten Datei extrahiert.",
            "nl": "Een moment geduld. Informatie wordt op dit moment uit het geselecteerde bestaand gehaald."
        })

        return props.PropsUIPromptProgress(description, message, percentage)

    def prompt_file(self):
        
        description = props.Translatable(
            {
                "en": f"Please follow the download instructions and choose the file that you stored on your device.",
                "nl": f"Volg de download instructies en kies het bestand dat u opgeslagen heeft op uw apparaat.",
            }
        )
        prompt_file = props.PropsUIPromptFileInput(description, self.mime_types)
        print(f"trying to load UI file input")
        file_result = yield render_donation_page(
            self.platform, prompt_file, self.progress
        )
        if file_result.__type__ != "PayloadString":
            print(f"payload is not string")
            self.log(f"skip to next step")
            raise SkipToNextStep()
        return file_result

    def log(self, message):
        self.meta_data.append(("debug", f"{self.platform}: {message}"))
        print(f"DEBUG: {self.platform}: {message}")

    def extract_data(self, file):
        return self.extractor(file)

    def prompt_consent(self, data):
        log_title = props.Translatable({"en": "Log messages", "nl": "Log berichten"})

        tables = [
            # props.PropsUIPromptConsentFormTable(table.id, table.title, table.data_frame, table.visualizations)
            props.PropsUIPromptConsentFormTable(table.id, table.title, table.data_frame)
            for table in data
        ]
        meta_frame = pd.DataFrame(self.meta_data, columns=["type", "message"])
        meta_table = props.PropsUIPromptConsentFormTable(
            "log_messages", log_title, meta_frame
        )
        self.log(f"prompt consent")
        consent_result = yield render_donation_page(
            self.platform,
            props.PropsUIPromptConsentForm(tables, [meta_table]),
            self.progress,
        )

        self.log(consent_result.__type__)
        if consent_result.__type__ == "PayloadJSON":
            self.log(f"trying to donate consent data")
            yield donate(f"{self.session_id}-{self.platform}", consent_result.value)
            print("DataDonationProcessor CONSENT completed.")
            return


class DataDonation:
    def __init__(self, platform, mime_types, extractor):
        self.platform = platform
        self.mime_types = mime_types
        self.extractor = extractor

    def __call__(self, session_id):
        processor = DataDonationProcessor(
            self.platform, self.mime_types, self.extractor, session_id
        )
        yield from processor.process()
        print("DataDonation completed.")
        return

# let's write this down 
# we call data_donation(session_id) and instantiate a DataDonation object
# the DataDonation object is a generator that yields from a DataDonationProcessor object
# the DataDonationProcessor first yields from prompt_file, then from extract_data, then from prompt_consent
# prompt_consent yields from render_donation_page, then from donate
# and when all that is done, we should be out of the whole loop and move onto render_end_page, and yet it doesn't happen. 

def process(session_id):
    progress = 0
    yield donate(f"{session_id}-tracking", '[{ "message": "user entered script" }]')
    print("yielded from donate user entered script")
    data_donation = DataDonation("TikTok", "application/json", extract_data)
    yield from data_donation(session_id)
    print("yielded from data_donation")
    yield render_end_page()

def render_end_page():
    print("arrived at render_end_page()")
    page = props.PropsUIPageEnd()
    return CommandUIRender(page)

def render_splash_pace():
    page = props.Props

def render_donation_page(platform, body, progress):
    header = props.PropsUIHeader(props.Translatable({"en": platform, "nl": platform}))
    # footer = props.PropsUIFooter(progress)
    page = props.PropsUIPageDonation(platform, header, body)
    return CommandUIRender(page)

def retry_confirmation(platform):
    text = props.Translatable(
        {
            "en": f"Unfortunately, we cannot process your data. Please make sure that you downloaded your data from TikTok in JSON format, and selected the correct file.",
            "nl": f"Helaas, kunnen we uw {platform} bestand niet verwerken. Weet u zeker dat u het juiste bestand heeft gekozen? Ga dan verder. Probeer opnieuw als u een ander bestand wilt kiezen.",
        }
    )
    ok = props.Translatable({"en": "Try again", "nl": "Probeer opnieuw"})
    cancel = props.Translatable({"en": "Continue", "nl": "Verder"})
    return props.PropsUIPromptConfirm(text, ok, cancel)


def prompt_consent(id, data, meta_data):
    table_title = props.Translatable(
        {"en": "JSON file contents", "nl": "Inhoud zip bestand"}
    )

    log_title = props.Translatable({"en": "Log messages", "nl": "Log berichten"})

    data_frame = pd.DataFrame(data, columns=["filename", "compressed size", "size"])
    table = props.PropsUIPromptConsentFormTable("zip_content", table_title, data_frame)
    meta_frame = pd.DataFrame(meta_data, columns=["type", "message"])
    meta_table = props.PropsUIPromptConsentFormTable(
        "log_messages", log_title, meta_frame
    )
    return props.PropsUIPromptConsentForm([table], [meta_table])


def donate(key, json_string):
    print(f"arrived at donate()")
    return CommandSystemDonate(key, json_string)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        print(extract_data(sys.argv[1]))
    else:
        print("please provide a JSON file as argument")
