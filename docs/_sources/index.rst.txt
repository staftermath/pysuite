.. pysuite documentation master file, created by
   sphinx-quickstart on Wed Aug 26 10:14:59 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to pysuite's documentation!
===================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   user_manual
   auth
   drive
   sheets
   gmail
   vision
   storage
   utilities

Google Suite Applications have gained popularity among small to medium scaled companies. Many data science team also
rely on Google Suite to share data, files and analyses. While manually distribute data are easy with Google Suite, there
are many use cases when data scientists need to incorporate Google Suite into their automation pipeline, or even simple
deployments. With a few set ups, Google Suite can be a quick, simple, yet powerful way to automate many data science jobs.
Google has provided APIs that allow comprehensive and flexible use of almost all commen Googe Suite applications, such as
Google Drive, Google Spreadsheet and GMail. However, to directly use the Python library (
`google-api-python-client <https://github.com/googleapis/google-api-python-client>`_) may require quite some engineering
efforts not all data science teams can afford. This library aims to fill the gap. :code:`pysuite` is designed to provide
simple interfaces that covers commonly used Google Suite functionalities.

Use case 1: Alerts
------------------
Trigger an email from scheduled python jobs to alert stakeholders. (Of course, there are already many email clients for
this.)

Use case 2: Report Sharing
--------------------------
After executing daily BAU scripts, upload the created csv file to a target Spreadsheet with built-in formula and graphs,
while stakeholders get the daily refreshed contents.

Use case 3: Cloud Storage
-------------------------
Use Google Drive as storage to transfer output data from one job to downstream jobs: The upstream jobs will automatically
upload a file to a folder. The downstream jobs or stakeholders can work from the uploaded content without knowing details
of how it is generated.

Use case 4: Simple UI
---------------------
Use Google Spreadsheet as an interface. Set up a few validated cells in a spreadsheet, users can enter or select from
a pull down menu to control the specifications. A scheduled job can read from target cells and parse the values as input
configuration for automated scripts or pipelines.


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
