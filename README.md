# FeliCa Tool

A tool to extract and display data of Japan's transportation card (Suica, PASMO, etc.).

## How to use

### install dependencies

install pipenv if you don't have it, in MacOS:
```bash
brew install pipenv
```

for other platforms, check [pipenv's document](https://github.com/pypa/pipenv#installation)

install libusb:
```bash
brew install libusb
```

install python packages
```bash
pipenv install
```

### download station data file

download the Japanse station data file from here: [station file repo](), move it to the local .data folder:
```bash
mkdir .data
mv Stations.csv .data/station.csv
```

### start the app

```bash
pipenv shell

python ./run.py
```

open webpage: http://localhost:5000, plugin your card reader and put your card on it, you will see the transactions
data in the web page.

## License

[MIT](LICENSE)
