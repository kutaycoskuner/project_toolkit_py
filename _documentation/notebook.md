# Notebook

# Links

# Keywords

# Structure

# Blackboard

# Todo Toolkits
- file renamer
- gif editor
- json editor
- cubemap converter
- german training app
- node graph builder/visualizer
- time spend calculaator
- graph visualizer

# How to
- <new project>
    - proje dosyasi yarat
    - cd <proje-dosyasi>
    - virtual environmet kur (py -m venv .venv)
    - .\.venv\scripts\activate
    - paketleri yukle ex. pip install dotenv
    - main.py yi yarat template den kopyala ve bazi yapistir
    - gerekirse ek klasorler olustur work file vs gibi
    - .env dosasi olusturup gizli degiskenleri onun icine at gtihuba gecmiyor

- <install virtual environment>
    - (opt) upgrade your pip ` python.exe -m pip install --upgrade pip`
    - installing virtual environment
        - install virtual environment  `py -m venv .venv`
        - activate virtual environment `.\.venv\scripts\activate` | deactivate
            - python version might cause a problem on venv
                - incase check vnev/pyenv.cfg paths and version of python interpreter
        - return to root `cd ../../`

- <problems>
    - tesseract yuklu degil veya path gormuyor
        - https://stackoverflow.com/questions/50951955/pytesseract-tesseractnotfound-error-tesseract-is-not-installed-or-its-not-i