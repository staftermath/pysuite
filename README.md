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

For details on how to use pysuite, please view the 
[documentation page](https://staftermath.github.io/pysuite/user_manual.html)

## Get credentials
Credential files are necessary to access all Google Services supported in pysuite. There are two categories. Each 
requires its own credential file. 

- Google Suite: This includes Google Drive, Gmail and Spreadsheet.
- Google Cloud: This includes Google Vision and Cloud Storage

### Google Suite
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

### Google Cloud Service

You need to get a credential json from [Google Cloud](https://cloud.google.com/docs/authentication/api-keys). The 
credential looks like:

```json
{
  "type": "service_account",
  "project_id": "your_project_id",
  "private_key_id": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "private_key": "-----BEGIN PRIVATE KEY-----xxxxxxxxxxx-----END PRIVATE KEY-----\n",
  "client_email": "some@email.address",
  "client_id": "xxxxxxxxxxxxxxxx",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/xxxxxxxxx"
}
```

You can use `Authentication` class similarly. Note that token file is not needed for Cloud
Service.

```python
from pysuite import Authentication

credential_json_file = "/tmp/credential.json"
client = Authentication(credential=credential_json_file, token=None, services=["storage", "vision"])
```



