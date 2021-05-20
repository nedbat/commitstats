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

import matplotlib.pyplot as plt
import matplotlib.dates

fig, ax = plt.subplots()
fig.set_size_inches(12, 8)
ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%b'))

line1 = ax.plot(df.when, df.total, "*-", label="# Commits", color="black", linewidth=1)[0]

ax2 = ax.twinx()
ax2.set_ylim(-5, 105) 
line2 = ax2.plot(df.when, df.pctcon, label="% Conventional", color="green", linewidth=4)[0]

plt.legend([line1, line2], [line1.get_label(), line2.get_label()])
plt.show()
