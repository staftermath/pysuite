#!/bin/bash

CREDENTIAL_FOLDER=$GITHUB_WORKSPACE/credentials
mkdir ${CREDENTIAL_FOLDER}
printf '{"installed": {"client_id":"%s", "auth_uri": "https://accounts.google.com/o/oauth2/auth", "token_uri": "https://oauth2.googleapis.com/token", "client_secret": "%s", "project_id": "pysuite-test"}}' "$client_id" "$client_secret" > ${CREDENTIAL_FOLDER}/credential.json
printf '{"token": "%s", "refresh_token": "%s"}' "$drive_token" "$drive_refresh_token"> ${CREDENTIAL_FOLDER}/drive_token.json
printf '{"token": "%s", "refresh_token": "%s"}' "$sheets_token" "$sheets_refresh_token"> ${CREDENTIAL_FOLDER}/sheets_token.json
printf '{"token": "%s", "refresh_token": "%s"}' "$gmail_token" "$gmail_refresh_token"> ${CREDENTIAL_FOLDER}/gmail_token.json
printf '{"token": "%s", "refresh_token": "%s"}' "$token" "$refresh_token"> ${CREDENTIAL_FOLDER}/token.json
printf '{"type": "service_account","project_id": "pysuite-test","private_key_id": "%s","private_key": "%s","client_email": "vision@pysuite-test.iam.gserviceaccount.com","client_id": "%s","auth_uri": "https://accounts.google.com/o/oauth2/auth","token_uri": "https://oauth2.googleapis.com/token","auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/vision%%40pysuite-test.iam.gserviceaccount.com"}' "$gc_private_key" "$gc_private_key_id" "$gc_client_id"> ${CREDENTIAL_FOLDER}/cloud_service.json
ls ${CREDENTIAL_FOLDER}
