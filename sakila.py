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
    return (mo,)


@app.cell
def _(engine, mo):
    _df = mo.sql(
        f"""
        SELECT
            -- X축: 일자 (YYYY-MM-DD 형식)
            DATE_FORMAT(rental_date, '%Y-%m-%d') AS 대여_일자,

            -- Y축: 시간대 (0부터 23까지의 시간)
            HOUR(rental_date) AS 시간대,

            -- 색상 값: 해당 일자, 해당 시간대의 총 대여 발생 횟수 (건수)
            COUNT(rental_id) AS 대여_발생_횟수 -- 총_대여_건수와 동일한 의미, 명확화를 위해 변경
        FROM
            rental
        WHERE
            rental_date BETWEEN '2005-01-01' AND '2007-12-31' -- 분석 기간 설정
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
    import marimo as mo
    import pandas as pd
    import seaborn as sns
    import matplotlib.pyplot as plt

    data = {
        '대여_일자': ['2007-01-01', '2007-01-01', '2007-01-01', '2007-01-02', '2007-01-02', '2007-01-02', '2007-01-03'],
        '시간대': [10, 14, 20, 11, 15, 21, 12],
        '총_대여_건수': [5, 10, 12, 6, 9, 11, 7]
    }
    df_heatmap_data = pd.DataFrame(data)
    return (mo,)


@app.cell
def _(engine, mo):
    _df = mo.sql(
        f"""
        SELECT * FROM actor
        """,
        engine=engine
    )
    return


if __name__ == "__main__":
    app.run()
