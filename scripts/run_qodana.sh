#!/usr/bin/env bash
docker run --rm -it \
-v $(pwd)/:/data/project/ \
-e QODANA_TOKEN=$(QODANA_TOKEN) \
-p 8080:8080 \
jetbrains/qodana-python:2023.2 \
--baseline /data/project/qodana.sarif.json \
--baseline-include-absent
