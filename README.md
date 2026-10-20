### Setup

Clone the repo:

`
https://github.com/June-Skeeter/fluxDataPipeline.git
`

Setup and activate the venv

`
cd fluxDataPipeline
python -m venv .venv
source .venv/bin/activate
`

Cromple the requirements (makeRequirements.py ensures all submodule dependencies included)

`
pip install pip-tools
python makeRequirments.py
pip-compile requirements.in
pip install -r requirements.txt
`