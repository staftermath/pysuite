# pysuite: A data scientist's toolbox for Google Suite App

[![PyPI version](https://badge.fury.io/py/pysuite.svg)](https://badge.fury.io/py/pysuite)
[![codecov](https://codecov.io/gh/staftermath/pysuite/branch/master/graph/badge.svg)](https://codecov.io/gh/staftermath/pysuite)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/pysuite)](https://pypi.org/project/pysuite/)

A python wrapper for Google Suite and Google Cloud Service API. This provides classes with user-friendly apis to 
operate with several Google API services. Currently, the supported services are:

- [Google Drive](https://developers.google.com/drive)
- [Gmail](https://developers.google.com/gmail/api)
- [Google Spreadsheet](https://developers.google.com/sheets/api)
- [Google Vision](https://cloud.google.com/vision)
- [Google Cloud Storage](https://cloud.google.com/storage/docs/apis)

For example, you can upload a pandas dataframe to a Google sheet as simple as:

```python
sheets_client.write_sheet(df, id='{sheet_id}', sheet_range='tab!A1:F')
```
Or download sheet to a pandas dataframe:
```python
df = sheets_client.read_sheet(id='{sheet_id}', sheet_range='tab!A1:F')
```

For details on how to use pysuite, please view the 
[documentation page](https://staftermath.github.io/pysuite/user_manual.html).

## Get credentials
Credential files are necessary to access all Google Services supported in pysuite.

You need to first get a client secret file from
<a href=https://console.cloud.google.com/apis/credentials>Google API Console</a>. The credential looks like:

```json
{
  "web": {
    "client_id": "xxxxx",
    "project_id": "xxxxx",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "xxx",
    "redirect_uris": [
      "https://console.developers.google.com/apis/credentials"
    ]
  }
}
```

You can then populate the oauth credential file that looks like:

```json
{"client_id": "xxx",
 "client_secret": "xxx",
 "expiry": "2022-12-31T00:00:00.000000Z",
 "refresh_token": "xxx",
 "scopes": ["https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/gmail.compose",
            "https://www.googleapis.com/auth/cloud-vision",
            "https://www.googleapis.com/auth/cloud-platform"],
 "token": "xxx",
 "token_uri": "https://oauth2.googleapis.com/token"}
```

`auth.get_token_from_secrets_file` is a helper function to populate OAuth credential json from
client secret file. For details, please see documentation.

`Authentication` class provides one-stop-shop to prepare credentials and authentications
for all clients in pysuite.

```python
from pysuite import Authentication

credential_json_file = "/tmp/credential.json"
auth = Authentication(credential=credential_json_file, project_id='my_project_id')
```
