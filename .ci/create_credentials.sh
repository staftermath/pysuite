#!/bin/bash

CREDENTIAL_FOLDER=$(pwd)/credentials
mkdir ${CREDENTIAL_FOLDER}
printf '{"installed": {"client_id":"%s", "auth_uri": "https://accounts.google.com/o/oauth2/auth", "token_uri": "https://oauth2.googleapis.com/token", "client_secret": "%s", "project_id": "pysuite-test"}}' "$client_id" "$client_secret" > ${CREDENTIAL_FOLDER}/credential.json
printf '{"token": "%s", "refresh_token": "%s"}' "$drive_token" "$drive_refresh_token"> ${CREDENTIAL_FOLDER}/drive_token.json
printf '{"token": "%s", "refresh_token": "%s"}' "$sheets_token" "$sheets_refresh_token"> ${CREDENTIAL_FOLDER}/sheets_token.json
printf '{"token": "%s", "refresh_token": "%s"}' "$token", "$refresh_token"> ${CREDENTIAL_FOLDER}/token.json
ls ${CREDENTIAL_FOLDER}
