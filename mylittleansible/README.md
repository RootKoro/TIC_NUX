# My Little Ansible Project (MLA)

This project has been made in python3.10

## Prerequists

You should have at least on your local machine `python3.10` installed, on your local and your distant machines the `SSH` service installed and running.

On windows, you can install `python` with the following link: https://www.python.org/downloads/

## Dependences

after cloning the project repository, follow the next steps to install the dependencies.

```bash
python3 -m venv .env

pip install -r build/requirements.txt
```

## Running MLA

```bash
python3 src/mla.py -f <todos_file_path.yml> -i <inventory_file_path.yml>
```
