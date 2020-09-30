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
:code:`Drive`, :code:`Sheets` and :code:`GMail`. If token file has not been created, it can be instantiated as follows:

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

    auth = Authentication(credential=credential_file, token=token_file, services=["drive", "sheets", "gmail"])
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
download a file to local.

.. code-block:: python

    drive.download(id="google drive object id", to_file="/tmp/test_file")

upload
++++++
upload a local file to google drive. you can provide a list of ids to place the uploaded file under these folders.

.. code-block:: python

    drive.upload(from_file="path/to/your/file/to/be/uploaded", name="google_drive_file_name",
                 parent_ids=["google drive folder id 1", "google drive folder id 2"])

delete
++++++
delete a google drive file/folder. parameter `recursive` has not been implemented.

.. code-block:: python

    drive.delete(id="id_of_target_file")

copy
++++
copy one google drive file to another. you can provide a list of ids to place the new file under these folders.

.. code-block:: python

    drive.copy(id="id_of_target_file", name="name of new file", parent_ids=["new parent folder id"])

list
++++
list files under the target folder. if the id is not a folder or there is no object in the folder, an empty list will be
returned. you can also pass a regular expression string to filter the result. note that this filter is done post-query.
you can also list recursively up to a maximum depth.

.. code-block:: python

    list_of_objects = drive.list(id="google drive folder id", regex="^test$", recursive=True, depth=5)

share
+++++
share a google drive object with a list of emails. you can grant the role as 'owner', 'organizer', 'fileOrganzier',
'writer', 'commenter' or 'reader'. you can also choose to notify the shared emails.

.. code-block:: python

    drive.share(id="google drive object id", emails=["user1@gmail.com", "user2@gmail.com"],
                role="reader", notify=True)

create_folder
+++++++++++++
create a folder on google drive.

.. code-block:: python

    drive.create_folder(name="awesome_new_folder", parent_ids=["parent_folder_id"])

Sheets
------
This class provides APIs used to access and operate with Google spreadsheet files

instantiate
+++++++++++

.. code-block:: python

    from pysuite import Sheets
    sheets = Sheets(service=sheets_auth.get_service_client())  # sheets_auth is an Authentication object with service='sheets'

If you prefer different method to create gsheet client, you may switch :code:`sheets_auth.get_service_client()` with a
google sheet service (See `Google Sheet API V4 <https://developers.google.com/sheets/api/quickstart/python>`_ for details):

.. code-block:: python

    service = build('sheets', 'v4', credentials=creds, cache_discovery=True)

to_sheet
++++++++
Upload a pandas dataframe to a specified range of sheet. This will clear the target range before uploading.

.. code-block:: python

    import pandas as pd
    df = pd.DataFrame({"col1": [1, 2], "col2": ['a', 'b']})
    sheets.to_sheet(df, id="your_sheet_id", sheet_range="yourtab!A1:B")

read_sheet
++++++++++
This api requires pandas.

.. code-block:: python

    df = sheets.read_sheet(id="your_sheet_id", sheet_range="yourtab!A1:D")

Note that Google sheet API ignores trailing empty cells in a row. This behavior causes the result that the values read
from the sheet may have fewer entries then expected. This furthur causes error when attempting to convert the values into
pandas DataFrame. This issue can be fixed by passing :code:`fill_row=True` (default) with some sacrifice of performance.
In addition, when both :code:`fill_row` and :code:`header` are :code:`True`, the method will attempt to fill missing
header with `_col{i}` where i is the index of the column. If you are certain no trailing cells exist in the target
range, you may turn it off for performance gain.

download
++++++++
Download sheet into a list of values either in **ROWS** format or in **COLUMNS** format. This is useful when you do not
want to add pandas as dependency.

.. code-block:: python

    values = sheets.download(id="your_sheet_id", sheet_range="yourtab!A1:D", dimension="ROWS")

Note that Google sheet API ignores trailing empty cells in a row. This behavior leads to the result that the values read
from the sheet may have fewer entries then expected. You can pass :code:`fill_row=True` to fill all such trailing empty
cells with empty strings. This comes with some sacrifice of performance but will guarantee to return homogeneous list.
:code:`fill_row=True` only works when :code:`dimension="ROWS"`. This is default to be False.

upload
++++++
Upload a list of lists to specified google sheet range. This is useful when you do not want to add pandas as dependency.

.. code-block:: python

    values = [[1, 2, 3], ["a", "b", "c"]]
    sheets.upload(values, id="your_sheet_id", sheet_range="yourtab!A1:B", dimension="ROWS")

clear
+++++
Remove contents of specified Goolge sheet range.

.. code-block:: python

    sheets.clear(id="your_sheet_id", sheet_range="yourtab!A1:B")

create_spreadsheet
++++++++++++++++++
Google api does not support create spreadsheet in a folder.

.. code-block:: python

    sheets.create_spreadsheet(name="new_spread_sheet_name")

create_sheet
++++++++++++
Create a tab (sheet) in a spreadsheet. return the id of created tab.

.. code-block:: python

    sheets.create_sheet(id="id_of_spreadsheet", title="new_tab_name")

delete_sheet
++++++++++++
delete a tab in a spreadsheet. you can find the id of the tab from URL

.. code-block:: python

    sheets.delete_sheet(id="id_of_spreadsheet", sheet_id="id_of_tab")

rename_sheet
++++++++++++
rename a tab in a spreadsheet.

.. code-block:: python

    sheets.rename_sheet(id="id_of_spreadsheet", sheet_id="id_of_tab", title="new_tab_name")


GMail
-----
This class provides APIs used to access and operate with Gmail API

instantiate
+++++++++++

.. code-block:: python

    from pysuite import GMail
    sheets = GMail(service=gmail_auth.get_service_client())  # gmail_auth is an Authentication object with service='gmail'

If you prefer different method to create gmail client, you may switch :code:`gmail_auth.get_service_client()` with a
google gmail service (See `Gmail API <https://developers.google.com/gmail/api/quickstart/python>`_ for details):

.. code-block:: python

    service = build('gmail', 'v1', credentials=creds, cache_discovery=True)

compose
+++++++
Write and send an email. You can attach local files and/or Google Drive files. The Google Drive files will be attached
directly in the body as external links.

.. code-block:: python

    gmail.compose(body="hello world",
                  sender="youremail@gmail.com",
                  subject="this is a test email",
                  to=["recipient1@gmail.com", "recipient2@hotmail.com"],
                  local_files=["/tmp/file.txt", "/tmp/another_file.csv"],
                  gdrive_ids=["gdrivefile_id1", "gdrive_file_id2"]
                  )
