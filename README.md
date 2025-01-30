# PDF to Markdown

This project contains a command line tool to convert PDF to markdown. It uses image conversion and an LLM to convert the images to markdown.

## Install

Execute these commands in the base directory of this project.

On Windows download the poppler library (e.g. poppler-24.08.0) from [here](https://github.com/oschwartz10612/poppler-windows/releases) and then do this using PowerShell:

```
$env:PKG_CONFIG_PATH="<download_folder>\poppler-24.08.0\Library\lib\pkgconfig"
```

```bash
# conda remove -n pdf_to_markdown --all
conda create -n pdf_to_markdown python=3.13
conda activate pdf_to_markdown
pip install poetry
# Windows
pip install cmake
conda install poppler poppler-qt
# End Windows
# Linux
sudo apt update
sudo apt install g++ -y
sudo apt install pkg-config -y
sudo apt-get install poppler-utils libpoppler-cpp-dev
# End Linux
poetry install
```

There is an [installation script](./install.sh) for Linux in this repository.

## Configuration

The application is configured used environment variables which you can set in an `.env` file. Check the [.env_local](./.env_local) file for the names of the variables that you will need.

You will need an Open AI key to run the PDF conversion.

## Usage of the command line application

Example on how to convert multiple pdf files:

```
python ./pdf_to_markdown_llm/main/cli.py convert-files -f ./pdfs/oecd/002b3a39-en.pdf -f ./pdfs/oecd/ee6587fd-en.pdf
```

Example on how to convert all pdf files in a folder:

```
python ./pdf_to_markdown_llm/main/cli.py convert-in-dir --dirs ./pdfs/oecd
```

