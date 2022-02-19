#!/bin/bash
set -x
#doesn't currently work using varaibles
COMMON_NAME="localhost"
SUBJECT_CLIENT="/C=SE/ST=Stockholm/L=Stockholm/O=himinds/OU=Client/CN=$COMMON_NAME"
CERTS_DIR="./../certs/"


echo "Creating Client Key"
openssl genrsa -out client.key 2048
echo "Creating certificate request"
openssl req -new -subj "$SUBJECT_CLIENT" -out client.csr -key client.key
echo "Signing client certificate with CA key"
openssl x509 -req -in client.csr -CA $CERTS_DIR/server-certs/ca.crt -CAkey $CERTS_DIR/server-certs/ca.key -CAcreateserial -out client.crt -days 720

if [ -d $CERTS_DIR ];then
 mv client.* $CERTS_DIR/client-certs
else
 mkdir $CERTS_DIR
 echo "=====Include ca.crt and ca.key in ~/certs/server-certs/======="
fi
