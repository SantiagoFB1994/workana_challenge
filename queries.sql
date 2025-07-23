-- 1. Schema (already exists, included for refernce)
CREATE TABLE IF NOT EXISTS movies (
    movie_id   TEXT PRIMARY KEY,
    title      VARCHAR(255) NOT NULL,
    year       INTEGER      NOT NULL,
    rating     NUMERIC(3,1) NOT NULL,
    duration   INTEGER,
    metascore  NUMERIC(4,1),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS actors (
    movie_id  TEXT REFERENCES movies(movie_id) ON DELETE CASCADE,
    actor_id  TEXT NOT NULL,
    name      VARCHAR(255) NOT NULL,
    PRIMARY KEY (movie_id, actor_id)
);

-- 2. Top-5 longest average duration per decade
WITH decade AS (
    SELECT *, (year / 10) * 10 AS decade_start
    FROM   movies
),
ranked AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY decade_start ORDER BY duration DESC) AS rn
    FROM   decade
)
SELECT decade_start, title, duration
FROM   ranked
WHERE  rn <= 5
ORDER  BY decade_start, rn;

-- 3. Standard deviation of ratings per year
SELECT year,
       STDDEV_POP(rating)::NUMERIC(4,2) AS stddev_rating
FROM   movies
GROUP  BY year
ORDER  BY year;

-- 4. Movies with > 20 % difference (IMDB vs Metascore)
SELECT movie_id,
       title,
       year,
       rating,
       metascore,
       ABS(rating - metascore) / GREATEST(rating, metascore) * 100 AS diff_pct
FROM   movies
WHERE  ABS(rating - metascore) / GREATEST(rating, metascore) > 0.2
ORDER  BY diff_pct DESC;

-- 5. View: movies + actors (flagging the first stored actor as lead)
CREATE OR REPLACE VIEW movies_actors AS
SELECT m.movie_id,
       m.title,
       m.year,
       m.rating,
       a.actor_id,
       a.name,
       a.actor_id = (
           SELECT MIN(actor_id)
           FROM   actors
           WHERE  actors.movie_id = m.movie_id
       ) AS is_lead
FROM   movies m
JOIN   actors a ON a.movie_id = m.movie_id;

-- 6. Recommended indexes for frequent filters
CREATE INDEX IF NOT EXISTS idx_movies_year   ON movies(year);
CREATE INDEX IF NOT EXISTS idx_actors_name   ON actors(name);

-- 7. Window-function example: top-3 longest films per decade
SELECT *
FROM (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY (year/10)*10 ORDER BY duration DESC) AS rn
    FROM   movies
) t
WHERE  rn <= 3
ORDER  BY (year/10)*10, rn;