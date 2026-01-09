Any Kurdish Kurmanji text data collector 

**Env variables**
Put the following environment variables to .env file

Get API key from https://scrapeops.io/app/headers
```
SCRAPEOPS_API_KEY=""
```

```
scrapy crawl xwebun -o {file}
```

**Create virtual environment**
```
pipenv --python 3.10
```

**Activate virtual environment**
```
pipenv shell
```

**Install requirements**
```
pipenv install
```

**Run recursive spider**
```
scrapy crawl recursive_spider -o news.csv
```

**Check rows count of a file**

```
python rows_count.py --file-name {file_name}
```
