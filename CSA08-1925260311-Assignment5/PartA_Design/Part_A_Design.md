# Assignment 5 - Part A: Data and Program Design (25 marks)

**Student:** V.Jaikrish  **Register number:** 1925260311
**Case study:** City Air-Quality Monitoring Network (12 stations, daily CSV files, SQLite, charts, citizen complaints)

All algorithms are written in pseudocode following the *SIMATS Engineering - Standard for Algorithmic Pseudocode*
(`ALGORITHM / INPUT / OUTPUT / BEGIN ... END`, `<-` for assignment, upper-case keywords).
Numbers quoted as "measured" come from `design_measurements.py` (this folder) and from the programs of
Part B; they vary from one computer to another.

---

## TASK A1 - DESIGN THE DATA ACQUISITION (7 marks)

### A1.1 - Inspect the source (2 marks)

**Structure of one station file** (one file per station per day, UTF-8, comma separated, one header line,
24 data lines - one per hour; the station name is also written in each line so that files can be merged):

```
station,date,hour,pm25,pm10,no2,temp
Adyar,2026-10-01,0,48.0,70.0,30.0,27.0
```

| Column | Meaning | Type / expected range |
|---|---|---|
| station | station name | text, one of the 12 stations |
| date | day of measurement | text `YYYY-MM-DD` |
| hour | hour of the day | integer 0-23 |
| pm25, pm10, no2 | pollutant readings, ug/m3 | decimal, 0 - 999 |
| temp | air temperature | decimal, degrees Celsius (Fahrenheit at two stations) |

**Expected data-quality problems** (each is present in the test file of Task B1):

| # | Problem | Example | What could go wrong |
|---|---|---|---|
| 1 | Missing value (blank) | `Adyar,2026-10-01,1,,72.0,31.0,26.5` | `float("")` raises ValueError; an average that treats it as 0 is too low |
| 2 | Missing value written `NA` | `...,2,NA,74.0,...` | same as above; "NA" is text, not a number |
| 3 | Negative value (sensor fault) | `...,3,-5.0,...` | lowers averages; a concentration cannot be negative |
| 4 | Impossibly large value | `...,4,9999,...` | one reading ruins a daily maximum and mean |
| 5 | Duplicate row | the same station/date/hour twice | counted twice, biases the mean towards that hour |
| 6 | Temperature in Fahrenheit (2 stations) | `Manali ... 82.4` | a 28 degC day looks like a 82 degC day; scatter plot and correlation are wrong |
| 7 | Untidy station name | `" GUINDY "`, `guindy` | one station becomes several groups |
| 8 | Different date format | `01/10/2026` | sorting and grouping by date fail |
| 9 | Damaged line (wrong number of fields) | `Manali,2026-10-01,2` | IndexError / misaligned columns |
| 10 | Missing hours (gaps) | hour 5 absent | daily mean uses fewer than 24 values without anyone knowing |
| 11 | Wrong delimiter, encoding, missing column, empty file | `station;date;pm25`, latin-1 bytes | the whole file is unreadable (tested in Task B2) |

### A1.2 - Design the storage (3 marks)

Two tables for the readings (a station is described once, not repeated in every reading) plus one for complaints.

```sql
CREATE TABLE stations (
    station_id INTEGER PRIMARY KEY,          -- surrogate key
    name       TEXT NOT NULL UNIQUE,         -- tidy name, e.g. 'Adyar'
    reports_fahrenheit INTEGER NOT NULL DEFAULT 0   -- 1 for the two stations that need conversion
);
CREATE TABLE readings (
    reading_id INTEGER PRIMARY KEY,
    station_id INTEGER NOT NULL REFERENCES stations(station_id),
    day        TEXT NOT NULL,                -- ISO date YYYY-MM-DD
    hour       INTEGER NOT NULL CHECK (hour BETWEEN 0 AND 23),
    pm25 REAL, pm10 REAL, no2 REAL, temp_c REAL      -- NULL = no valid reading
);
CREATE INDEX idx_station_day ON readings(station_id, day);   -- added after measuring (Task B4.2)
CREATE TABLE complaints (
    complaint_id INTEGER PRIMARY KEY,
    received_at  TEXT NOT NULL,
    station_id   INTEGER REFERENCES stations(station_id),
    text         TEXT NOT NULL,
    sentiment    TEXT                          -- 'positive' / 'negative' / 'neutral', filled by the AI step
);
```

**Mapping of CSV columns to the tables**

| CSV column | Stored in | Transformation |
|---|---|---|
| station | `stations.name` (once) and `readings.station_id` | name tidied; looked up / inserted in `stations` |
| date | `readings.day` | converted to `YYYY-MM-DD` |
| hour | `readings.hour` | integer 0-23 |
| pm25, pm10, no2 | `readings.pm25 / pm10 / no2` | decimal; invalid -> NULL (after the fill rule of A2) |
| temp | `readings.temp_c` | Fahrenheit converted to Celsius where `reports_fahrenheit = 1` |

Choices: `readings` uses a simple integer primary key; duplicates are removed during cleaning (a UNIQUE
(station, day, hour) constraint would be a second safety net at the cost of an extra index); NULL is used for missing values,
because 0 would be a wrong measurement; the index on (station_id, day) is created only because Task B4.2 measured its benefit.

### A1.3 - CSV or SQL? (2 marks)

Three typical questions of the board, answered from CSV files and with SQL (12 stations, one year = 105,120 rows;
measured, milliseconds):

| Question | By reading the CSV (loop / pandas) | By an SQL query | Measured CSV loop / pandas / SQL |
|---|---|---|---|
| Q1 average PM2.5 of Adyar in October | open every file, test station and month, sum and count (O(n) in all rows) | `SELECT AVG(r.pm25) FROM readings r JOIN stations s USING(station_id) WHERE s.name=? AND r.day BETWEEN '2026-10-01' AND '2026-10-31'` | 118 / 80 / **0.1** ms |
| Q2 station with the highest mean PM2.5 | one pass, dictionary of sums and counts | `... GROUP BY s.name ORDER BY AVG(pm25) DESC LIMIT 1` | 128 / 60 / 12 ms |
| Q3 hour of the day with the worst air | one pass, dictionary per hour | `SELECT hour FROM readings GROUP BY hour ORDER BY AVG(pm25) DESC LIMIT 1` | 167 / 54 / 22 ms |

*Comparison.* Reading the CSV needs a complete scan for every question, and the files must be parsed again each time. SQL
loads the data once; after that a question about one station and one period uses the index and touches only the needed
rows (Q1: 0.1 ms against 118 ms). Questions that must look at every row (Q2, Q3) are still faster in SQL because they run in compiled
code and the text has already been converted to numbers. CSV remains the right format to *receive and archive* the data; SQL
is the right place to *query* it.

**Alternative concept and complexity analysis - CSV files read into a pandas DataFrame for every question, instead of SQLite**

```
ALGORITHM AnswerFromCSV(question)
INPUT  : question (station, period)      OUTPUT: answer
BEGIN
    frame <- READ every CSV file into one DataFrame        // O(n) time, O(n) memory, EVERY question
    RETURN compute(question) on frame                        // another O(n) scan
END
```

| | pandas from CSV for every question | SQLite, loaded once |
|---|---|---|
| Time per question | O(n): read + filter all n rows (measured 54-80 ms for n = 105,120) | with an index on (station_id, day): O(log n + k) for k matching rows (0.1 ms); without an index also O(n) |
| One-time cost | none | load O(n) (about 0.2 s here) + index build O(n log n) |
| Space | the whole table in memory, O(n), rebuilt for every question or kept in RAM | on disk (about 78 bytes per row including the index, measured in B4); memory only for the result |

With one question the DataFrame is simpler and as fast; with many questions every day, or data larger than memory, the database wins.

---

## TASK A2 - DESIGN THE CLEANING AND NORMALISATION (5 marks)

### A2.1 - Cleaning rules (2 marks)

| Problem | Rule | Justification |
|---|---|---|
| Missing value (blank, `NA`, non-number) | **Fill with the previous valid value of the same station and column for at most 3 consecutive hours; if the gap is longer, leave NULL.** | Air quality changes slowly from hour to hour, so a short gap is well approximated by the last value; a long gap would repeat an old value for a whole shift and invent data, so NULL is more honest. (The median would flatten the daily peak pattern; dropping loses data.) |
| Impossible value (< 0 or > 999 for pollutants; temperature outside -10..60 degC after conversion) | **Treat as missing** (mark invalid first, then apply the previous rule) and count it in a report. | The value is certainly wrong, but the hour still happened; treating it like missing keeps the rule set small and makes every correction countable. |
| Duplicate rows (same station, date, hour) | **Keep the first, drop the others**, count them. | An hour can have only one reading; identical duplicates carry no new information, and keeping the first is deterministic. |
| Fahrenheit temperatures | **Detect per station: median of its valid temperatures > 45 -> Fahrenheit; convert with C = (F - 32) x 5/9**, round to 1 decimal; store the flag in `stations.reports_fahrenheit`. | Whole stations report in one unit, and no city has a median air temperature above 45 degC, so a median test is robust to a few bad readings. |
| Other (name, date format, damaged line) | Tidy the name (`strip`, single spaces, title case); accept `YYYY-MM-DD` and `DD/MM/YYYY` and convert to ISO; **reject** lines with the wrong number of fields and log them. | One entity must have one spelling and one format to be grouped correctly. |

```
ALGORITHM CleanReadings(raw_rows)
INPUT  : raw_rows - list of rows read from the station files
OUTPUT : clean_rows, report (counts of every correction)
BEGIN
    seen <- empty set ; parsed <- empty list
    FOR EACH row IN raw_rows DO
        IF number of fields in row != 7 THEN count a rejected row ; CONTINUE
        name <- TidyName(row.station) ; day <- ParseDate(row.date) ; hour <- ParseInteger(row.hour)
        IF day is invalid OR hour NOT IN 0..23 THEN count a rejected row ; CONTINUE
        IF (name, day, hour) IN seen THEN count a duplicate ; CONTINUE
        ADD (name, day, hour) TO seen
        FOR EACH pollutant value IN row DO
            IF value is blank OR "NA" THEN value <- NULL ; count a missing value
            ELSE IF value < 0 OR value > 999 THEN value <- NULL ; count an impossible value
        APPEND row TO parsed
    END FOR
    FOR EACH station IN parsed DO
        IF median(valid temperatures of station) > 45 THEN convert its temperatures to Celsius
    SORT parsed BY (station, day, hour)
    FOR EACH station, FOR EACH pollutant column DO
        last_valid <- NULL
        FOR EACH row IN order DO
            IF value is NULL AND last_valid exists AND row is within 3 hours of last_valid THEN value <- last_valid
            ELSE IF value is not NULL THEN last_valid <- value
    RETURN parsed, report
END
```

### A2.2 - Normalisation (2 marks)

For the PM2.5 values *x* of a station:

* **Min-max normalisation:** x' = (x - min) / (max - min), giving values in [0, 1]. Example: values 48, 95, 121 give 0, 0.644, 1.0 (Task B1).
  Rounded to 3 decimals. Algorithm: one pass to find min and max, a second pass to scale; if max = min the result is 0 for all (avoid dividing by zero).
* **Z-score standardisation:** z = (x - mean) / standard deviation; the result has mean 0 and standard deviation 1; values above +2 or below -2 are unusual.

```
ALGORITHM MinMax(values)                      ALGORITHM ZScore(values)
BEGIN                                         BEGIN
    lo <- MIN(values) ; hi <- MAX(values)         m <- MEAN(values) ; s <- STANDARD_DEVIATION(values)
    IF hi = lo THEN RETURN list of 0              IF s = 0 THEN RETURN list of 0
    RETURN [ (v - lo) / (hi - lo) FOR v IN values ]   RETURN [ (v - m) / s FOR v IN values ]
END                                           END
```

*When appropriate.* Min-max is used when a fixed 0-1 scale is needed - for example to show several pollutants on one chart or to feed a method that
expects bounded input; its weakness is that a single extreme value (a missed sensor fault) squeezes all other values together. Z-score is used
to compare stations or pollutants with different units and spreads, to spot outliers, and when the data are roughly bell-shaped;
it is less affected by one extreme value, and its result is not bounded.

### A2.3 - Formatting (1 mark)

| Item | Standard format |
|---|---|
| Date | ISO 8601 text `YYYY-MM-DD` (sorts correctly as text); hour a separate integer 0-23 |
| Station name | tidy text: no leading/trailing spaces, single spaces inside, title case (`Anna Nagar`); stored once in `stations` |
| Numbers | decimal point, no thousands separators; PM2.5, PM10, NO2 in ug/m3 with 1 decimal; temperature in degrees Celsius with 1 decimal; missing = NULL (never 0, never "NA") |

**Alternative concept and complexity analysis - dropping missing readings instead of filling them**

```
ALGORITHM DailyMeanDrop(rows)   BEGIN keep only rows whose value is valid ; group by (station, day) ; RETURN mean of each group END
```

| | Forward fill (3 h) / median fill | Drop |
|---|---|---|
| Time | forward fill O(n) (one ordered pass); median fill O(n log n) (sorting to find the median) | O(n) (a filter) |
| Space | O(n); the filled values replace NULLs | O(n) (a filtered copy); the fill values need no extra storage |
| Effect on the daily average | measured on 105,120 hourly readings with 3.4% invalid: difference from the *drop* result 0.27 ug/m3 on average (largest 2.9) for forward fill and 0.05 (largest 0.8) for median fill | uses only real measurements, but each day's mean rests on fewer than 24 readings, and a day with many drops can be dominated by the hours that happen to remain (e.g. only night hours) |
| Time measured | forward fill 18 ms, median fill 37 ms | 17 ms |

Dropping is the safest choice when the number of valid readings is stored and shown next to each mean (see A3.2); filling is
chosen here because the board wants a continuous hourly series for charts, and the gap limit of 3 hours bounds the invented data.

---

## TASK A3 - DESIGN THE ANALYSIS AND VISUALISATION (5 marks)

### A3.1 - Choose the charts (3 marks)

| Question of the board | Chart | Justification |
|---|---|---|
| Trend of PM2.5 over a month | **Line chart** (x = day, y = daily mean PM2.5, one line per station or one station) | the x-axis is ordered time and the eye follows the line to see rises, falls and spikes |
| Comparison of stations | **Bar chart** (horizontal, sorted by mean PM2.5) | compares one number per category; sorted bars show the ranking at a glance; horizontal bars keep the station names readable |
| Relationship between temperature and PM2.5 | **Scatter plot** (x = temperature, y = PM2.5, one dot per reading or a sample) with the correlation coefficient in the title | two numeric variables: the cloud shows the direction, strength and any outliers of a relationship |
| Hours with the worst air | **Box plot by hour** (24 boxes) (a bar chart of hourly means as a simpler alternative) | shows the median, spread and outliers of every hour, so the two rush-hour peaks and their variability are visible, not only the average |
| (extra) How PM2.5 values are distributed | **Histogram** | shows the shape (symmetric or skewed) and the share of readings above a limit |

Every chart needs a title, labelled axes with units, and a one- to three-sentence interpretation (done in Task B1.4).

### A3.2 - Design the summary table (2 marks)

`daily_summary(station_id, day, min_pm25, max_pm25, mean_pm25, n_valid)` - one row per station per day; `n_valid` (number of valid
readings, 0-24) tells the reader how much each mean can be trusted.

```sql
CREATE TABLE daily_summary AS
SELECT station_id, day, MIN(pm25) AS min_pm25, MAX(pm25) AS max_pm25,
       ROUND(AVG(pm25), 1) AS mean_pm25, COUNT(pm25) AS n_valid     -- COUNT(col) counts non-NULL values only
FROM readings GROUP BY station_id, day;
```

```
ALGORITHM BuildDailySummary(database)
BEGIN
    EXECUTE the GROUP BY query above          // the database groups, aggregates and ignores NULLs
    CREATE INDEX ON daily_summary(station_id, day)
    FOR EACH new day, INSERT only that day's rows      // incremental update, not a rebuild
END
```

**Alternative concept and complexity analysis - Python loops after reading all rows, instead of SQL GROUP BY**

```
ALGORITHM SummaryByLoops(rows)
BEGIN  groups <- empty dictionary
       FOR EACH row IN rows DO APPEND row.pm25 TO groups[(station, day)]
       FOR EACH key, values IN groups DO result[key] <- (MIN, MAX, MEAN, COUNT of values)
END
```

| | Python loops | SQL GROUP BY |
|---|---|---|
| Time for n readings | O(n) to group + O(n) to aggregate; measured 2.70 s for 1.05 million rows (including reading the CSV) | O(n) in the database engine; measured 0.63 s for the query after loading |
| Memory | storing all values: O(n) (4.6 MB for 105,120 rows, measured); with a running sum/count/min/max per group only O(stations x days) (1.4 MB) | the rows stay on disk; memory for the groups only |
| Notes | needs all rows in the program; more code to write and test | one declarative statement; NULL handling built in |

---

## TASK A4 - PLAN DEBUGGING AND PROFILING (4 marks)

### A4.1 - Debugging plan (2 marks)

| Tool | How it will be used on the cleaning code |
|---|---|
| `print` | Quick look while writing: print one raw row and its cleaned version; print the counts of the cleaning report. Removed afterwards. |
| `assert` | States what must be true after each step: `assert all(r[3] is None or 0 <= r[3] <= 999 for r in clean)`, `assert len(set(keys)) == len(keys)` (no duplicates remain), `assert 0 <= hour <= 23`. A broken rule stops the program at the exact step; `python -O` switches asserts off in production. |
| `logging` | `logging.info` for counts per file (rows read, rejected, filled); `logging.warning` for each rejected line with file and line number; `logging.error` for unreadable files; `logging.debug` for per-row details; written to a file with time stamps and a level. |
| `pdb` / IDE debugger | When an assertion fails or a result is wrong: `breakpoint()` (or an IDE breakpoint with the condition `station == "Manali"`) just before the suspect step; step with `n`, inspect with `p value`, view the call stack with `w`; check the rule against the offending row and fix it. |

Order of use: tests with small files that contain every problem first; asserts and logging stay in the program; the debugger is used only to find the cause when an assertion or test fails.

### A4.2 - Profiling plan (2 marks)

1. **`time.perf_counter()`** around each stage (read, clean, store, query, chart) to find which stage dominates.
2. **`timeit`** on small competing code fragments inside the slow stage (for example `statistics.mean(v)` against `sum(v) / len(v)`), repeated many times for a stable result.
3. **`cProfile`** on the whole program (`python -m cProfile -s tottime script.py` or `cProfile.Profile().runcall(...)`), reading `tottime` (own time) and `cumtime` (with callees) for the slowest functions and the number of calls.
4. Change only the proven slow part, then measure again and check that the results are unchanged.

(Applied in Task B3.3: of 0.71 s in the loop version, `statistics.mean` took 37% and the CSV reader the largest own time; replacing the mean by `sum()/len()` reduced the time from 0.27 s to 0.18 s.)

**Alternative concept and complexity analysis - print statements for all debugging instead of logging and a debugger**

Measured for 200,000 calls: `print` into a memory buffer 0.31 us per call (printing on a real terminal is much slower); `logging.debug` writing to a file
7.7 us per call (1.5 s in total, because every call builds a log record, formats it and writes it); `logging.debug` with the level set to WARNING 0.12 us
per call (0.02 s); `if DEBUG:` around a print 0.03 us per call. Complexity: every approach is O(c) for c calls, with a different constant.
*Switching off:* print statements must be found and deleted (or wrapped in `if DEBUG:`), and forgotten ones slow a production run and
spoil its output; logging is switched off or down by changing the level (`logger.setLevel(logging.WARNING)`) with no code change, and asserts by running with `python -O`.
The debugger costs nothing when it is not started. The price of logging when on is higher, but it is the only one that gives
time stamps, levels, file output and a permanent record of a run.

---

## TASK A5 - DESIGN AN AI APPLICATION FOR CITIZEN COMPLAINTS (4 marks)

### A5.1 - Sentiment and summary (2 marks)

```
ALGORITHM SentimentScore(text)
INPUT  : text - one complaint        OUTPUT: score (integer), label
DATA   : POSITIVE <- {good, clean, fast, helpful, improved}
         NEGATIVE <- {bad, dirty, slow, rude, smoke, broken}        NEGATORS <- {not, never, no}
BEGIN
    words <- lower-case text, punctuation replaced by spaces, split into words
    total <- 0
    FOR i <- 0 TO length(words) - 1 DO
        IF words[i] IN POSITIVE THEN value <- +1 ELSE IF words[i] IN NEGATIVE THEN value <- -1 ELSE value <- 0
        IF value != 0 AND i > 0 AND words[i - 1] IN NEGATORS THEN value <- -value       // "not good" -> -1
        total <- total + value
    END FOR
    label <- "positive" IF total > 0 ELSE "negative" IF total < 0 ELSE "neutral"
    RETURN total, label
END
```

```
ALGORITHM ExtractiveSummary(text, k)
INPUT  : text (several sentences), k       OUTPUT: the k most important sentences, in original order
BEGIN
    sentences <- split text at . ! ?
    frequency <- count of every word of text that is not a stop word (the, a, is, ...)
    FOR EACH sentence DO  score <- (sum of frequency[w] for important words w in sentence) / SQRT(number of important words)
    RETURN the k sentences with the highest score, sorted by their position in the text
END
```

### A5.2 - Basic chatbot (2 marks)

```
ALGORITHM Chatbot(question, database)
INPUT  : question text       OUTPUT: reply text
BEGIN
    q <- lower-case question
    station <- the station name found inside q (or NONE)
    metric <- "pm10" IF q contains "pm10", "no2" IF contains "no2", temperature IF contains "temp", ELSE "pm25"
    IF station = NONE THEN RETURN "Which station?" followed by the list of known stations
    day <- latest day in the database ("today"), or the day before IF q contains "yesterday"
    value <- SELECT AVG(metric) FROM readings WHERE station = ? AND day = ?        // parameterised
    IF value is NULL THEN RETURN "No data for <station> on <day>"
    RETURN "<metric> in <station> on <day>: average <value>"
END
```

Example: "What is the PM2.5 in Adyar today?" -> `Adyar` found, metric PM2.5, SELECT with placeholders -> "PM25 in Adyar on 2026-10-03: average 57.9 ug/m3."

**Limitations:** it understands only the words it was given (a misspelling "Adyaar" or the Tamil name finds nothing); no grammar or
context (it cannot answer "and yesterday?" after a first question); "today" is the latest day in the database, not the clock; it cannot compare
or explain ("why is it worse than last week?"); one station per question; a question about two things at once gets
one answer; it cannot say when it does not understand except by asking for a station; answers are only as good as the data in the database.

**Alternative concept and complexity analysis - a trained machine-learning model instead of the word list**

| | Word-list (lexicon) scorer | Trained model (e.g. Naive Bayes, or a pre-trained language model) |
|---|---|---|
| Time per complaint | O(w) for w words, set look-ups: measured 2 us | Naive Bayes O(w x classes): measured 18 us; a pre-trained language model: milliseconds to tens of milliseconds per complaint and usually a GPU for large volumes |
| Memory | a 14-word list: almost none | Naive Bayes: counts for every word seen, 28 KB for 190 words; a language model: hundreds of MB to several GB |
| Expected accuracy | measured 71% agreement with my reading of 56 complaints (misses words not in the list, sarcasm, mixed opinions) | can learn new words and context from labelled examples and normally does better, **but only with enough labelled data**: the Naive Bayes trained on 56 examples reached only 41% (Task B4.3); it needs thousands of labelled complaints |
| Other | easy to explain: every score can be traced to words | needs labelled data, training, monitoring and retraining; harder to explain |
