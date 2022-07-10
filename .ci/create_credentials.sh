#!/bin/bash

CREDENTIAL_FOLDER=$GITHUB_WORKSPACE/credentials
ENCRYPTED_CREDENTIAL_FOLDER=$GITHUB_WORKSPACE/.ci/encrypted_credential
mkdir ${CREDENTIAL_FOLDER}
gpg --quiet --batch --yes --decrypt --passphrase="$credential_passphrase" --output ${CREDENTIAL_FOLDER}/credential.json ${ENCRYPTED_CREDENTIAL_FOLDER}/credential.json.gpg
gpg --quiet --batch --yes --decrypt --passphrase="$credential_passphrase" --output ${CREDENTIAL_FOLDER}/secret_file.json ${ENCRYPTED_CREDENTIAL_FOLDER}/secret_file.json.gpg
ls ${CREDENTIAL_FOLDER}
