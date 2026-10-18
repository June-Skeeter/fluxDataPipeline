### Setup

`
python -m venv .venv
source .venv/bin/activate
pip install pip-tools
python makeRequirments.py
pip-compile requirements.in
pip install -r requirements.txt
`