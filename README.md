# pysuite
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
You need to save this credential to a json file and pass to `Authentication` class (For example, `GoogleDriveClient`). 
In addition, you need to have a file to store refresh token. A pickle object will be written to the token file when 
needed.
```python
from pysuite.auth import GoogleDriveClient

credential_json_file = "/tmp/credential.json"
token_path_file = "/tmp/refresh_token.pickle"
client = GoogleDriveClient(credential=credential_json_file, token=token_path_file)
```
