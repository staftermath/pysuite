.. _user_manual:

User Manual
===========
This page provides a quick introduction of some basic classes in pysuite as well as some exmaple of their usages. For
detailed documentation, please refer to the corresponding pages for each class.

Installation
------------
pysuite is tested under linux for python 3.6, 3.7 and 3.8. It is also expected to run on MacOS. Certain efforts have
been spent to avoid OS dependencies. However, it has not been tested under Windows.

The easiest way to install pysuite is to use pip:

.. code-block:: bash

    pip install pysuite

Alternatively, you can clone `pysuite repo <https://github.com/staftermath/pysuite>`_ and run:

.. code-block:: bash

    python setup.py install

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

Once you created a credential file from the previous section, :code:`Authentication` can help authenticate your
credential and provide clients for API class such as :code:`Drive`, :code:`Sheets` and :code:`GMail`. Google API uses a
refresh token to periodically refresh your credential. By keeping a token file, you will not be needing to manually
authorize your credential file through browser. :code:`Authentication` helps you automatically refresh token when
expired. An :code:`Authentication` class can be instantiated as follows.

.. code-block:: python

  from pysuite import Authentication

  credential_file = "./credentials/credentials.json"
  token_file = "./credentials/token.json"

  drive_auth = Authentication(credential=credential_file, token=token_file, services="drive")

this will prompt a web browser confirmation for the first time if :code:`token` file is not created. Once
you confirm access, the token will be created/overwritten. Future authorization will automatically use the token file.
No manual confirmation will be needed.

You may provide a string or a list of services. Currently accepted services are 'drive', 'sheets' or 'gmail'. With
:code:`Authentication` class, You can generate different service used by corresponding API class such as :code:`Drive`,
:code:`Sheet` or :code:`GMail`. Only service whose service type is authorized in :code:`Authentication` can be created.
If more than one service was authorized at instantiation, you must specify service type in :code:`get_service_client`:
For example:

.. code-block:: python

    drive_and_sheet_auth = Authentication(credential=credential_file, token=token_file, services=["drive", "sheet"])
    sheet_and_gmail_auth = Authentication(credential=credential_file, token=token_file, services=["sheet", "gmail"])
    sheet_only_auth = Authentication(credential=credential_file, token=token_file, services="sheet")

    drive_and_sheet_auth.get_service_client("drive")  # get a service client for Drive
    drive_and_sheet_auth.get_service_client("sheet")  # get a service client for Sheet
    drive_and_sheet_auth.get_service_client("gmail")  # this will not work since gmail is not authorized
    drive_and_sheet_auth.get_service_client()  # this will not work since multiple types were authorized.
    sheet_only_auth.get_service_client()  # this works since there is only one auth type

The token file is associated with authorized services. In order to successfully authorize your credential, you need to
first enable API through `Google API Console <https://console.developers.google.com/apis/dashboard>`_.

Drive
-----
This class provides APIs used to access and operate with Google drive files. You may utilize :code:`Authentication`
class to create an authenticated API class:

.. code-block:: python

    from pysuite import Drive

    # drive_auth is an Authentication object with 'drive' service authorized.
    drive = Drive(service=drive_auth.get_service_client())

If you prefer different method to create gdrive client, you may switch :code:`drive_auth.get_service_client()` with a
gdrive service (See `Google Drive API V3 <https://developers.google.com/drive/api/v3/quickstart/python>`_ for detail):

.. code-block:: python

    service = build('drive', 'v3', credentials=creds)

Many methods in this class has parameter :code:`id`. This represent the gdrive object id. There are several ways to get
the id of a Google Drive object. Some methods in :code:`Drive` can also help you to find it. To do it manually, right
click on any Google Drive object (file or folder) and click `get link`, then copy the prompted link, it may look like
this: https://drive.google.com/drive/folders/1qcfrD7RqZWwPVO9C7tbL1PNRa2aUQlF8?usp=sharing. The id of this object is
**1qcfrD7RqZWwPVO9C7tbL1PNRa2aUQlF8**. You can get id of most Google Suite object this way.

All methods in :code:`Drive` that interacts with Google API can be configured to retry on Quota Error. Please refer to
:ref:`drive` to see how to control the number of retries and sleep time.

download
++++++++
Download a file to local.

.. code-block:: python

    drive.download(id="google drive object id", to_file="/tmp/test_file")

upload
++++++
Upload a local file to google drive. you can provide the id of a folder to place the uploaded file under that folder.

.. code-block:: python

    drive.upload(from_file="path/to/your/file/to/be/uploaded", name="google_drive_file_name",
                 parent_id="google drive folder id 1")

delete
++++++
Delete a google drive file/folder. Parameter :code:`recursive` has not been implemented.

.. code-block:: python

    drive.delete(id="id_of_target_object")

copy
++++
Copy one google drive file to another. The new file will be named by :code:`name`. You can provide the id of a folder
to place the new file under that folder.

.. code-block:: python

    drive.copy(id="id_of_target_file", name="name of new file", parent_id="new parent folder id")

list
++++
List files under the target folder. If the id is not a folder or there is no object in the folder, an empty list will be
returned. You can also pass a regular expression string to filter the result. Note that this filter is done post-query.
Which means list of all files under the target folder will still be downloaded first. You can also list recursively up
to a maximum depth. This may save some time if you do not intend to search deeply nested folders.

.. code-block:: python

    list_of_objects = drive.list(id="google drive folder id", regex="^test$", recursive=True, depth=5)

share
+++++
Share a google drive object with a list of emails. You can grant the role such as **owner**, **organizer**,
**fileOrganzier**, **writer**, **commenter** or **reader**. You can also choose to notify the shared emails.

.. code-block:: python

    drive.share(id="google drive object id", emails=["user1@gmail.com", "user2@gmail.com"],
                role="reader", notify=True)

create_folder
+++++++++++++
Create a folder on google drive.

.. code-block:: python

    drive.create_folder(name="awesome_new_folder", parent_ids=["parent_folder_id"])

Sheets
------
This class provides APIs used to access and operate with Google spreadsheet files. Many `Sheets` methods has parameter
:code:`range`. This needs to follow `A1 Notation <https://developers.google.com/sheets/api/guides/concepts#a1_notation>`_.
To instantiate Sheets class:

.. code-block:: python

    from pysuite import Sheets
    # sheets_auth is an Authentication object with 'sheets' type of service authorized
    sheets = Sheets(service=sheets_auth.get_service_client())

If you prefer different method to create gsheet client, you may switch :code:`sheets_auth.get_service_client()` with a
google sheet service (See `Google Sheet API V4 <https://developers.google.com/sheets/api/quickstart/python>`_ for details):

.. code-block:: python

    service = build('sheets', 'v4', credentials=creds, cache_discovery=True)

All methods in :code:`Sheets` that calls Google API can be configured to retry on Quota Error. Please refer to
:ref:`sheets` to see how to control the number of retries and sleep time

to_sheet
++++++++
Upload a pandas dataframe to a specified range of sheet. This will clear the target range before uploading. The data in
the provided dataframe must be serializable. For example, date type may not be correctly uploaded. In such cases, you
might need to convert these columns to strings first.

.. code-block:: python

    import pandas as pd
    df = pd.DataFrame({"col1": [1, 2], "col2": ['a', 'b']})
    sheets.to_sheet(df, id="your_sheet_id", sheet_range="yourtab!A1:B")

read_sheet
++++++++++
Download target sheet range into a pandas DataFrame. This api requires pandas.

.. code-block:: python

    df = sheets.read_sheet(id="your_sheet_id", sheet_range="yourtab!A1:D")

The raw data downloaded are all of string type, hence the dtypes of all columns in the created dataframe will be `object`.
The parameter :code:`dtypes` can be utilized to columns to the desired types.

Note that Google sheet API ignores trailing empty cells in a row. As A result, the values read from the sheet may have
fewer entries then expected. As a result, it causes error when attempting to convert the values into
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
The target range will be cleared before new content is uploaded. All entries in the provided list must be serializable.

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
Delete a tab (sheet) in a spreadsheet. You can find the id of the tab from URL. For example, if URL of a tab is
https://docs.google.com/spreadsheets/d/1CNOH3o2Zz05mharkLXuwX72FpRka8-KFpIm9bEaja50/edit#gid=388610320, then the tab id
is `388610320`

.. code-block:: python

    sheets.delete_sheet(id="id_of_spreadsheet", sheet_id="id_of_tab")

rename_sheet
++++++++++++
Rename a tab in a spreadsheet.

.. code-block:: python

    sheets.rename_sheet(id="id_of_spreadsheet", sheet_id="id_of_tab", title="new_tab_name")


GMail
-----
This class provides APIs used to access and operate with Gmail API. This class uses Google API istead of more commonly
used SMTP. To instantiate a :code:`GMail` class:

.. code-block:: python

    from pysuite import GMail
    # gmail_auth is an Authentication object with 'gmail' type service authorized.
    sheets = GMail(service=gmail_auth.get_service_client())

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

Credential for Google Cloud
---------------------------
Pysuite also provides python apis for some Google Cloud services such as Google Vision. These class requires Google Cloud
Service credential. It is a completely different credential from that for drive, gmail and sheets API. You can find
the steps to obtain the credential file from `this page <https://cloud.google.com/vision/docs/before-you-begin>`_.


Vision
------
This class provides python apis to access Google Vision api. You can get started to understand what Google Vision
provides from this `quickstarts <https://cloud.google.com/vision/docs/quickstarts>`_. Currently please note that
asynchronized apis are not supported. This will be supported in the future update.

Authentication
++++++++++++++
You can authenticate the connection in the same way as drive, gmail or sheets. Since the vision service credential file
is different from that for drive, gmail or sheets, you cannot authenticate them together. Additionally, `token` is not
required for vision.

.. code-block:: python

    vision_auth = Authentication(credential=cloud_service_file, services="vision")

Instantiate Vision Class
++++++++++++++++++++++++
Using the authenticated object, you can instantiate a vision class by:

.. code-block:: python

    vision = Vision(service=vision_auth.get_service_client())

Service Types
+++++++++++++
All vision annotation services provided by Google Vision API are supported. You can find some examples from the official
document, such as `OCR <https://cloud.google.com/vision/docs/ocr>`_,
`label detection <https://cloud.google.com/vision/docs/labels>`_ and more. Please see the following sections for examples
of making various annotation requests. You can find the complete list of features from
`google vision github <https://github.com/googleapis/python-vision/blob/main/google/cloud/vision_v1/types/image_annotator.py#L105-L119>`_.
For example, "TEXT_DETECTION" is listed as one of the service, hence you can pass a string of `"TEXT_DETECTION"` or
`["TEXT_DETECTION"]` to `methods` to request a test detection annotation. This is case insensitive.

Annotate One Image
++++++++++++++++++
If you want to annotate just one image, you can utilize `annotate_image` method:

.. code-block:: python

    result = vision.annotate_image(test_image, methods=["text_detection"])

Here `test_image` is the path to the image file to be annotated. You can pass a single string or a list of strings to
`methods`. They will be allowed vision services. The returned object is an `AnnotateImageResponse` object containing
very granular information on the results.

Batch Annotations
+++++++++++++++++
If you have a few images, you can utlize `add_request` and `batch_annotate_image` methods to annotate them in one api
call:

.. code-block:: python

    vision.add_request(image_path=first_test_image, methods="text_detection")
    vision.add_request(image_path=second_test_image, methods=["text_detection", "label_detection"])
    result = vision.batch_annotate_image()

Convert To Json
+++++++++++++++
The results from API calls are `AnnotateImageResponse` objects. While they have many convenient methods to help operate
on them, they are not directly serializable. You can use `to_json` method to store these objects to serializable object:

.. code-block:: python

    json_result = Vision.to_json(result)


Storage
-------
This class provides python apis to work with Google Cloud Storage. It provides intuitive methods to move files and
folders between local environment and Google Cloud Storage. This class uses Google Cloud Service authentication.

Authentication
++++++++++++++
Google storage service credential file is similar to Google Vision credentials. You cannot authenticate it with Google
Suite classes (drive, gmail and sheets).

.. code-block:: python

    storage_auth = Authentication(credential=cloud_service_file, services="storage")

Instantiate Storage Class
+++++++++++++++++++++++++
Using the authenticated object, you can instantiate a storage class by:

.. code-block:: python

    storage = Storage(service=storage_auth.get_service_client())

Upload, Download, Move and Remove Files
+++++++++++++++++++++++++++++++++++++++
You can upload a single file:

.. code-block:: python

    result = storage.upload(from_object="/home/user/my_local_file.txt",
                            to_object="gs://my_bucket/my/path/to/target_file.txt")

You can also upload a folder. This will recursively upload every file in the folder

.. code-block:: python

    result = storage.upload(from_object="/home/user/my_local_folder",
                            to_object="gs://my_bucket/my/path/to/target_folder")

You can download file or folder from Google Cloud.

.. code-block:: python

    result = storage.download(from_object="gs://my_bucket/my/path/to/target_folder",
                              to_object="/home/user/my_local_folder")

To copy files or folders from one Google Storage location to another:

.. code-block:: python

    result = storage.copy(from_object="gs://my_bucket/my/path/to/source_folder",
                          to_object="gs://my_bucket/my/path/to/destination_folder")


To remove files or folders on Google Cloud:

.. code-block:: python

    storage.remove(target_object="gs://my_bucket/my/path/to/target_folder")

Create, Remove and Get Bucket
+++++++++++++++++++++++++++++

.. code-block:: python

    storage.create_bucket(bucket_name="my_bucket")
    bucket = storage.get_bucket(bucket_name="my_bucket")
    storage.remove_bucket(bucket_name="my_bucket")

