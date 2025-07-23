🎬 IMDb Top-250 Scraper
Lightweight, streaming-first scraper that fetches the IMDb Top-250 movies page-by-page and persists them to:

    PostgreSQL (movie & actor tables)
    CSV (one file per run)

Features

    Parallel HTTP with ThreadPoolExecutor
    Optional NordVPN or custom proxies
    Environment-driven configuration
    Runs locally or in Docker with Python 3.12

Scraping approach / technical decisions

    Found an API endpoint for the top 250 chart wich returned the first 125 titles with pagination, 
    modifiying the query on the endpoint i got to fetch all the 250 titles in a single request, 
    then i proceeded to scrape all the movie details for each title via request + bs4 using the
    json found in the __NEXT_DATA__ field present in the HTML.
    During my tests no proxy/ip rotation was needed since the volume of request was low,
    but the functionality is there if needed.
    This could also be achieved using Selenium/Playwright by getting the chart url 
    and fetching the movie ids from the source of the page to then 
    iterate over the detail page of each movie, but compared to the requests approach 
    it woud be significantly slower and more resource intensive

🏁 Quick start (Docker)
bash
Copy

# 1. Clone & enter
git clone <repo-url> imdb-scraper
cd imdb-scraper

# 2. Configure
cp .env.example .env          # edit values as needed

# 3. Build & run
docker compose up --build     # no VPN
#   or
docker compose --profile vpn up --build  # with NordVPN
Take into acount that a NordVPN token is needed for this approach, you should add it to the .env

The first build will create PostgreSQL and the scraper containers automatically.
🔧 Local run (no Docker)

    Install
    Python 3.12+ and PostgreSQL (or use the provided Docker Postgres).
    Virtual environment
    bash

Copy

python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

Environment
bash
Copy

cp .env.example .env
# adjust POSTGRES_HOST=localhost, etc.

Run
bash

    Copy

    python main.py

<pre lang="markdown"><code>
```text
📁 Project layout
├── main.py                       # entry point
├── docker-compose.yml            # all services + optional VPN
├── Dockerfile                    # Python 3.12 slim
├── queries.sql                   # advanced SQL queries
├── .env.example                  # template with every config
├── requirements.txt              # dependencies for the project
├── data/
│   └── imdb_movies_example.csv   # output CSV from the scraper
├── factories/
│   ├── persistence_factory.py    # factory to generate persistence handlers
│   └── scraper_factory.py        # factory to generate scraper adapters
├── logs/
│   └── example.log               # folder containing logs
├── models/
│   ├── movie_model.py            # data model for movies and actor objects
│   └── proxy_config.py           # data model for proxies
├── persistence/
│   ├── base_persistence.py       # persistence interface / abstraction
│   ├── postgres_handler.py       # streaming Postgres
│   └── csv_handler.py            # streaming CSV
├── scrapers/
│   ├── base_scraper.py           # scraper interface / abstraction
│   └── imdb.py                   # IMDb GraphQL scraper
├── utils/
│   ├── logging_config.py         # rotating file & console logs
│   ├── proxy_handler.py          # NordVPN / custom proxy logic
│   └── request_handler.py        # handler for requests
└── data/                         # CSV output (empty folder)
```
</code></pre>

⚙️ Environment variables table

| Variable                 | Default                       | Purpose                                      |
|--------------------------|------------------------------|----------------------------------------------|
| **Scraping**             |                              |                                              |
| `IMDB_URL`               | (see `.env.example`)         | IMDb GraphQL endpoint URL                    |
| `MAX_CONCURRENT_REQUESTS`| `5`                          | parallel threads                             |
| `BATCH_SIZE`             | `1000`                       | rows per DB commit                           |
| **Postgres**             |                              |                                              |
| `POSTGRES_HOST`          | `localhost` / `postgres`     | DB host                                      |
| `POSTGRES_DB`            | `imdb_db`                    | database name                                |
| `POSTGRES_USER`          | `postgres`                   | username                                     |
| `POSTGRES_PASSWORD`      | `postgres`                   | password                                     |
| **CSV**                  |                              |                                              |
| `CSV_OUTPUT_DIR`         | `data`                       | output folder                                |
| **Proxy / VPN**          |                              |                                              |
| `PROXY_ENABLED`          | `false`                      | turn on/off                                  |
| `PROXY_TYPE`             | `none`                       | `nordvpn` \| `custom`                        |
| `NORDVPN_TOKEN`          | —                            | NordVPN token                                |
| `NORDVPN_COUNTRY`        | `us`                         | country code                                 |
| `PROXY_1_*`, `PROXY_2_*` | —                            | custom proxy list                            |

🧪 Advanced SQL  
All queries live in `queries.sql`.

    5 longest movies per decade
    Standard deviation of ratings per year
    Movies with > 20 % IMDb vs Metascore gap
    Actor-lead detection view
    Indexes & window-function examples

Run them in psql or any client after the first scrape.
🛠️ Development tips

    Logs → logs/ (rotating daily, 5 MB each, 3 backups)
    Testing → small BATCH_SIZE (e.g. 10) to speed up iterations
    Docker → docker compose logs -f scraper for live output
    Database → docker exec -it imdb_postgres psql -U postgres -d imdb_db

