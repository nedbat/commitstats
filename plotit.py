import matplotlib.pyplot as plt
import matplotlib.dates
import pandas as pd
import sqlite3

QUERY = """\
    select
    weekend, total, con, cast((con*100.0)/total as integer) pctcon, bod, cast((bod*100.0)/total as integer) pctbod
    from (
        select
        strftime("%Y%m%d", date, "weekday 0") as weekend,
        count(*) total,
        sum(conventional) as con, sum(bodylines > 0) as bod
        from commits where repo = "edx/edx-platform" group by weekend
    )
    where weekend > '202009';
    """

# Read sqlite query results into a pandas DataFrame
with sqlite3.connect("commits.db") as con:
    df = pd.read_sql_query(QUERY, con)

# Make the date nice
df["when"] = pd.to_datetime(df["weekend"], format="%Y%m%d")
# Drop the last row, because it's probably incomplete
df = df[:-1]
df.tail()

fig, ax = plt.subplots()
fig.set_size_inches(12, 8)
ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%b'))

line1 = ax.plot(df.when, df.total, "*-", label="# Commits", color="gray", linewidth=1)[0]

ax2 = ax.twinx()
ax2.set_ylim(-5, 105) 
line2 = ax2.plot(df.when, df.pctcon, label="% Conventional", color="green", linewidth=4)[0]

ax3 = ax.twinx()
ax3.set_ylim(-5, 105)
line3 = ax3.plot(df.when, df.pctbod, label="% with bodies", color="blue", linewidth=2)[0]

lines = [line1, line2, line3]
plt.legend(lines, [l.get_label() for l in lines])
plt.show()
