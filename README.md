# pysuite: A data scientist's toolbox for Google Suite App

[![PyPi version](https://pypip.in/v/pysuite/badge.png)](https://pypi.org/project/pysuite/)
[![PyPi downloads](https://pypip.in/d/pysuite/badge.png)](https://pypi.org/project/pysuite/)

A python wrapper for google suite API. This provides a few classes with user friendly apis to operate with Google Suite
applications such as Google Drive and Google Spreadsheet.

## Get credentials
You need to get a credential from 
<a href=https://console.developers.google.com/apis/dashboard>Google API Console</a>. The credential looks like:

```json
{
  "installed": {
    "client_id": "xxxxxxxxxxxxxxxxx.apps.googleusercontent.com",
    "project_id": "xxxxxxxxxxxxx-xxxxxxxxxxxx",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "xxxxxxxxxxxxxxxx",
    "redirect_uris": [
      "urn:ietf:wg:oauth:2.0:oob",
      "http://localhost"
    ]
  }
}
```

You can also provide a token json file if possible, the token file looks like:

```json
{
     "token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
     "refresh_token": "xxxxxxxxx"
}
```

If token file doesn't exist, a confirmation is needed from browser prompt. Then the token file will be created.
```python
from pysuite import Authentication

credential_json_file = "/tmp/credential.json"
token_path_file = "/tmp/token.json"
client = Authentication(credential=credential_json_file, token=token_path_file, services="sheets")
```

## Authenticate

`Authentication` blass can help authenticate your credential and provide service client for API. Such as "drive" and 
"sheets". 
```python
from pysuite import Authentication

credential_file = "./credentials/credentials.json"
token_file = "./credentials/token.json"

drive_auth = Authentication(credential=credential_file, token=token_file, services="drive")
sheets_auth = Authentication(credential=credential_file, token=token_file, services="sheets")
```

You can generate a gdrive client now from authentication object.
```python
service = drive_auth.get_service_client()  # 'service' needed if not provided when initiating Authenciation object 
```

## API
API classes aim to provide quick and simple access to Google Suite App such as Google Drive and Google Spreadsheet. 

### Drive

```python
from pysuite import Drive

drive = Drive(service=drive_auth.get_service_client())  # drive_auth is an Authenticaion class with `service='drive'`
```

If you prefer different method to create gdrive client, you may switch `drive_auth.get_service()` with a gdrive service 
(See <a href=https://developers.google.com/drive/api/v3/quickstart/python>Google Drive API V3</a> for detail):
```python
service = build('drive', 'v3', credentials=creds)
```

Some example apis are shown as follows:

#### Download file
```python
drive.download(id="google drive object id", to_file="/tmp/test_file")
```
#### Upload file
```python
drive.upload(from_file="path/to/your/file/to/be/uploaded", name="google_drive_file_name", 
             parent_ids=["google drive folder id 1", "google drive folder id 2"])
```
#### List file in folder
```python
list_of_objects = drive.list(id="google drive folder id")
```

### Sheets
```python
from pysuite import Sheets

sheets = Sheets(service=sheets_auth.get_service_client())  # sheets_auth is an Authenticaion class with `service='sheets'`
```

If you prefer different method to create gdrive client, you may switch `sheets_auth.get_service()` with a gsheet service 
(See <a href=https://developers.google.com/sheets/api/quickstart/python>Google Sheet API V4</a> for detail):
```python
service = build('sheets', 'v4', credentials=creds, cache_discovery=True)
```

Some examples can be found below:
#### upload pandas dataframe

```python
import pandas as pd 
df = pd.DataFrame({"col1": [1, 2], "col2": ['a', 'b']})
sheets.to_sheet(df, id="your_sheet_id", sheet_range="yourtab!A1:B")
```

#### download sheet to dataframe
This api requires pandas.
```python
df = sheets.read_sheet(id="your_sheet_id", sheet_range="yourtab!A1:D")
```
