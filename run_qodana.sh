#!/bin/sh
docker run --rm -it \
-v ./:/data/project/ \
-e QODANA_TOKEN="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJvcmdhbml6YXRpb24iOiIzWDRSdyIsInByb2plY3QiOiJ6WmIyaiIsInRva2VuIjoiM0syeVkifQ.rHuCL2y1ymHToPqFSG5hJO0hpD-w6g7lI9HDRPiOdKs" \
-p 8080:8080 \
jetbrains/qodana-python:2023.2 \
--show-report --baseline=qodana.sarif.json