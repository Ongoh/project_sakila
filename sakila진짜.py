import marimo

__generated_with = "0.14.11"
app = marimo.App(width="medium")


@app.cell
def _():
    return


@app.cell
def _():
    import os
    import sqlalchemy

    _password = os.environ.get("MYSQL_PASSWORD", "034652585aa##")
    DATABASE_URL = f"mysql+pymysql://root:{_password}@127.0.0.1:3306/sakila"
    engine = sqlalchemy.create_engine(DATABASE_URL)
    return (engine,)


@app.cell
def _():
    import marimo as mo
    import marimo as mo
    import pandas as pd
    import seaborn as sns
    import matplotlib.pyplot as plt
    import sqlite3 # SQLite 
    return (mo,)


@app.cell
def _(engine, mo):
    _df = mo.sql(
        f"""
        SELECT
            DATE_FORMAT(r.rental_date, '%Y-%m-%d') AS 대여_일자, -- YYYY-MM-DD 형식의 날짜
            HOUR(r.rental_date) AS 시간대, -- 0-23시 형식의 시간
            COUNT(r.rental_id) AS 총_대여_건수 -- 해당 일자/시간대의 총 대여 건수
        FROM
            rental AS r
        WHERE
            r.rental_date BETWEEN '2005-01-01' AND '2007-12-31' -- 분석 기간 설정 (필요에 따라 변경)
        GROUP BY
            대여_일자, 시간대
        ORDER BY
            대여_일자, 시간대;
        """,
        engine=engine
    )
    return


@app.cell
def _():
    return


@app.cell
def _(engine, mo):
    _df = mo.sql(
        f"""
        SELECT
        DATE_FORMAT(r.rental_date, '%Y-%m') AS rental_month,
        COUNT(r.rental_id) AS total_rentals,
        SUM(CASE
            WHEN DATEDIFF(r.return_date, r.rental_date) > f.rental_duration THEN 1
            ELSE 0
        END) AS total_overdue_rentals,
        (SUM(CASE
            WHEN DATEDIFF(r.return_date, r.rental_date) > f.rental_duration THEN 1
            ELSE 0
        END) * 100.0 / COUNT(r.rental_id)) AS overdue_rate_percentage
        FROM
        rental AS r
        JOIN
        inventory AS i ON r.inventory_id = i.inventory_id
        JOIN
        film AS f ON i.film_id = f.film_id
        WHERE
        r.return_date IS NOT NULL
        GROUP BY
        rental_month
        ORDER BY
        rental_month;
        """,
        engine=engine
    )
    return


if __name__ == "__main__":
    app.run()
