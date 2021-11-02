#!/bin/bash

CREDENTIAL_FOLDER=$GITHUB_WORKSPACE/credentials
ENCRYPTED_CREDENTIAL_FOLDER=$GITHUB_WORKSPACE/.ci/encrypted_credential
mkdir ${CREDENTIAL_FOLDER}
gpg --quiet --batch --yes --decrypt --passphrase="$credential_passphrase" --output ${CREDENTIAL_FOLDER}/credential.json ${ENCRYPTED_CREDENTIAL_FOLDER}/credential.json.gpg
gpg --quiet --batch --yes --decrypt --passphrase="$credential_passphrase" --output ${CREDENTIAL_FOLDER}/drive_token.json ${ENCRYPTED_CREDENTIAL_FOLDER}/drive_token.json.gpg
gpg --quiet --batch --yes --decrypt --passphrase="$credential_passphrase" --output ${CREDENTIAL_FOLDER}/sheets_token.json ${ENCRYPTED_CREDENTIAL_FOLDER}/sheets_token.json.gpg
gpg --quiet --batch --yes --decrypt --passphrase="$credential_passphrase" --output ${CREDENTIAL_FOLDER}/gmail_token.json ${ENCRYPTED_CREDENTIAL_FOLDER}/gmail_token.json.gpg
gpg --quiet --batch --yes --decrypt --passphrase="$credential_passphrase" --output ${CREDENTIAL_FOLDER}/token.json ${ENCRYPTED_CREDENTIAL_FOLDER}/token.json.gpg
gpg --quiet --batch --yes --decrypt --passphrase="$credential_passphrase" --output ${CREDENTIAL_FOLDER}/cloud_service.json ${ENCRYPTED_CREDENTIAL_FOLDER}/cloud_service.json.gpg
ls ${CREDENTIAL_FOLDER}
