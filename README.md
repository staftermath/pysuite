# pysuite: A data scientist's toolbox for Google Suite App

[![PyPi version](https://pypip.in/v/pysuite/badge.png)](https://crate.io/packages/pysuite/)
[![PyPi downloads](https://pypip.in/d/pysuite/badge.png)](https://crate.io/packages/pysuite/)

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
You need to save this credential to a json file and pass to `Authentication` class (For example, `DriveAuth`). 
In addition, you need to have a file to store refresh token. A pickle object will be written to the token file when 
needed.
```python
from pysuite import DriveAuth

credential_json_file = "/tmp/credential.json"
token_path_file = "/tmp/refresh_token.pickle"
client = DriveAuth(credential=credential_json_file, token=token_path_file)
```

## Authenticate

Subclasses of `Authentication` can help authenticate your credential and provide clients for API class such as `Drive` and 
`Sheet`. 
```python
from pysuite import DriveAuth

credential_file = "./credentials/credentials.json"
token_file = "./credentials/token.pickle"

drive_auth = DriveAuth(credentials=credential_file, token_file=token_file)
```
this may prompt web browser confirmation for the first time if token_file is not created or is expired. Once you confirm
access, the token will be created/overwritten.

You can generate a gdrive client now from authentication object.
```python
service = drive_auth.get_service()
```

## API
API classes aim to provide quick and simple access to Google Suite App such as Google Drive and Google Spreadsheet. 

### Drive

```python
from pysuite import Drive

drive = Drive(service=drive_auth.get_service()) # drive_auth is an DriveAuth class
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

### Sheet
```python
from pysuite import Sheet

sheet = Sheet(service=sheet_auth.get_service())  # sheet_auth is an SheetAuth class
```

If you prefer different method to create gdrive client, you may switch `sheet_auth.get_service()` with a gsheet service 
(See <a href=https://developers.google.com/sheets/api/quickstart/python>Google Sheet API V4</a> for detail):
```python
service = build('sheets', 'v4', credentials=creds, cache_discovery=True)
```

Some examples can be found below:
#### upload pandas dataframe

```python
import pandas as pd 
df = pd.DataFrame({"col1": [1, 2], "col2": ['a', 'b']})
sheet.to_sheet(df, id="your_sheet_id", range="yourtab!A1:B")
```

#### download sheet to dataframe
This api requires pandas.
```python
df = sheet.read_sheet(id="your_sheet_id", range="yourtab!A1:D")
```
