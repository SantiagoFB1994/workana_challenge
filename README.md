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

| Variable | Default (example) | Purpose |
|---|---|---|
| **Scraping** |
| `IMDB_URL` | `https://caching.graphql.imdb.com/?operationName=Top250MoviesPagination&variables={"first":250,"isInPace":false,"locale":"es-MX"}&extensions={"persistedQuery":{"sha256Hash":"2db1d515844c69836ea8dc532d5bff27684fdce990c465ebf52d36d185a187b3","version":1}}` | IMDb GraphQL endpoint &#43; variables |
| `MAX_RETRIES` | `3` | max retry attempts per request |
| `MAX_CONCURRENT_REQUESTS` | `5` | parallel threads |
| `REQUEST_TIMEOUT` | `30` | seconds before timeout |
| `LOG_LEVEL` | `INFO` | Python logging level |
| `BATCH_SIZE` | `1000` | rows per DB commit |
| `VERIFY_LOCATION` | `true` | geo-check proxy IP |
| **PostgreSQL** |
| `POSTGRES_HOST` | `localhost` &#47; `postgres` | DB host |
| `POSTGRES_PORT` | `5433` | host port |
| `POSTGRES_DB` | `imdb_db` | database name |
| `POSTGRES_USER` | `postgres` | user |
| `POSTGRES_PASSWORD` | `postgres` | password |
| `POSTGRES_SCHEMA` | `public` | schema |
| **CSV** |
| `CSV_OUTPUT_DIR` | `data` | output folder |
| `CSV_FILENAME_PREFIX` | `imdb_movies` | file prefix |
| **Proxy / VPN** |
| `PROXY_ENABLED` | `false` | enable&#47;disable proxy |
| `PROXY_TYPE` | `nordvpn` | `nordvpn` &#124; `custom` &#124; `both` |
| `NORDVPN_TOKEN` | `your_nord_vpn_token` | NordVPN service token |
| `NORDVPN_COUNTRY` | `us` | country code (`us`, `jp`, `uk`, …) |
| `NORDVPN_TECHNOLOGY` | `nordlynx` | protocol (`nordlynx` &#124; `openvpn`) |
| `NORDVPN_CATEGORY` | `legacy_p2p` | server category (`p2p` &#124; `legacy_p2p` &#124; `normal`) |
| **Custom proxies** |
| `PROXY_1_ADDRESS` | `proxy1.example.com` | proxy #1 host |
| `PROXY_1_PORT` | `8080` | proxy #1 port |
| `PROXY_1_USER` | *(empty)* | proxy #1 username |
| `PROXY_1_PASSWORD` | *(empty)* | proxy #1 password |
| `PROXY_1_PROTOCOL` | `http` | `http` &#124; `https` &#124; `socks5` |
| `PROXY_2_ADDRESS` | `proxy2.example.com` | proxy #2 host |
| `PROXY_2_PORT` | `3128` | proxy #2 port |
| `PROXY_2_USER` | `user` | proxy #2 username |
| `PROXY_2_PASSWORD` | `pass123` | proxy #2 password |
| `PROXY_2_PROTOCOL` | `https` | proxy #2 protocol |

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

