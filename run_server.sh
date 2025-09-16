#!/bin/bash
export PYTHONPATH=$PYTHONPATH:/Users/kianrahbari/EasyInterns-1
cd /Users/kianrahbari/EasyInterns-1/backend
python3 -m uvicorn main:app --reload --port 8001 --log-level debug
