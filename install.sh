!#/bin/bash

conda create -n pdf_to_markdown python=3.13
conda activate pdf_to_markdown
pip install poetry
sudo apt update
sudo apt install g++ -y
sudo apt install pkg-config -y
sudo apt-get install poppler-utils libpoppler-cpp-dev
poetry install