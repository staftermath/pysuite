.. _user_manual:

User Manual
===========

Authentication
--------------

Get credentials
+++++++++++++++

You need to get a credential from `Google API Console <https://console.developers.google.com/apis/dashboard>`_. The
credential looks like:

.. code-block:: json

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

You need to save this credential to a json file and pass to :code:`Authentication` class.
In addition, you need to have a file to store refresh token. A json object will be written to the token file every time
Authentication file is instantiated.

The token file will be written in the following json format:

.. code-block:: json

    {
        "token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "refresh_token": "xxxxxxxxxxxx"
    }

Authenticate
++++++++++++

:code:`Authentication` can help authenticate your credential and provide clients for API class such as
:code:`Drive` and :code:`Sheets`. If token file has not been created, it can be instantiated as follows:

.. code-block:: python

  from pysuite import Authentication

  credential_file = "./credentials/credentials.json"
  token_file = "./credentials/token.json"

  drive_auth = Authentication(credential=credential_file, token=token_file, services="drive")

this will prompt web browser confirmation for the first time if :code:`token` file is not created. Once
you confirm access, the token will be created/overwritten. You may provide a string or a list of services. Currently
accepted services are 'drive' or 'sheets'.

You can generate a gdrive service object or sheets service object now from authentication object.

.. code-block:: python

    drive_service = drive_auth.get_service_client()

If more than one service was authorized at instantiation, you must specify service type in :code:`get_service_client`:

.. code-block:: python

    auth = Authentication(credential=credential_file, token=token_file, services=["drive", "sheets"])
    drive_service = auth.get_service_client("drive")


Drive
-----
This class provides APIs used to access and operate with Google drive files

instantiate
+++++++++++
You may utilize :code:`Authentication` class to create an authenticated API class:

.. code-block:: python

    from pysuite import Drive

    drive = Drive(service=drive_auth.get_service_client())  # drive_auth is an Authentication object with service='drive'

If you prefer different method to create gdrive client, you may switch :code:`drive_auth.get_service_client()` with a gdrive service
(See `Google Drive API V3 <https://developers.google.com/drive/api/v3/quickstart/python>`_ for detail):

.. code-block:: python

    service = build('drive', 'v3', credentials=creds)

download
++++++++

.. code-block:: python

    drive.download(id="google drive object id", to_file="/tmp/test_file")

upload
++++++

.. code-block:: python

    drive.upload(from_file="path/to/your/file/to/be/uploaded", name="google_drive_file_name",
                 parent_ids=["google drive folder id 1", "google drive folder id 2"])

list
++++

.. code-block:: python

    list_of_objects = drive.list(id="google drive folder id")

Sheets
------
This class provides APIs used to access and operate with Google spreadsheet files

instantiate
+++++++++++

.. code-block:: python

    from pysuite import Sheets
    sheets = Sheets(service=sheets_auth.get_service_client())  # sheets_auth is an Authentication object with service='sheets'

If you prefer different method to create gdrive client, you may switch :code:`sheets_auth.get_service_client()` with a
google sheet service (See `Google Sheet API V4 <https://developers.google.com/sheets/api/quickstart/python>`_ for details):

.. code-block:: python

    service = build('sheets', 'v4', credentials=creds, cache_discovery=True)

to_sheet
++++++++
Upload a pandas dataframe to a specified range of sheet. This will clear the target range before uploading.

.. code-block:: python

    import pandas as pd
    df = pd.DataFrame({"col1": [1, 2], "col2": ['a', 'b']})
    sheets.to_sheet(df, id="your_sheet_id", range="yourtab!A1:B")

read_sheet
++++++++++
This api requires pandas.

.. code-block:: python

    df = sheets.read_sheet(id="your_sheet_id", range="yourtab!A1:D")

download
++++++++
Download sheet into a list of values either in **ROWS** format or in **COLUMNS** format. This is useful when you do not
want to add pandas as dependency.

.. code-block:: python

    values = sheets.download(id="your_sheet_id", range="yourtab!A1:D", dimension="ROWS")

upload
++++++
Upload a list of lists to specified google sheet range. This is useful when you do not want to add pandas as dependency.

.. code-block:: python

    values = [[1, 2, 3], ["a", "b", "c"]]
    sheets.upload(values, id="your_sheet_id", range="yourtab!A1:B", dimension="ROWS")

clear
+++++
Remove contents of specified Goolge sheet range.

.. code-block:: python

    sheets.clear(id="your_sheet_id", range="yourtab!A1:B")
