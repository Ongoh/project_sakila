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

    _password = os.environ.get("MYSQL_PASSWORD", "mysql")
    DATABASE_URL = f"mysql+pymysql://root:{_password}@127.0.0.1:3306/sakila"
    engine = sqlalchemy.create_engine(DATABASE_URL)
    return (engine,)


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _():
    import polars as pl
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap
    import seaborn as sns
    import koreanize_matplotlib  # 한글 깨짐 방지
    import pyarrow

    from IPython.core.interactiveshell import InteractiveShell
    InteractiveShell.ast_node_interactivity = "all"

    # 날짜 다루는 데 필요한 라이브러리들
    from datetime import datetime, timedelta
    from dateutil.parser import parse
    from dateutil.relativedelta import relativedelta
    return np, pd, plt, sns


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # [1] 문제 인식
    - 가정 1) 2005년 9월 ~ 2006년 1월까지 매출감소 해결을 위한 sakila 내부 재정비 기간이었음.
    - 가정 2) 2006년 2월 14일 자료가 2006년 2월 자료의 전부임 (자료의 소실 등이 없었음)
    - 가정 3) 해당 데이터는 Sakila 전체 데이터에서 층화계층 추출을 통해 선정된 표본, 대표성이 확보된다고 가정
    - 가정 4) Sakila DVD 대여점은 유인매장
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 1. 월별 대여횟수 및 매출액
    - 대여건수와 매출액 모두 2005년 5월부터 7월까지 증가하다가 2005년 8월부터 하락
    - 대여건수와 매출의 변동성이 심함 -> 고정비 감당하기 어려운 구조로 이어질 가능성이 높음
    - 한계 : 데이터 수집 기간이 짧아 패턴 확인이 어려움
    """
    )
    return


@app.cell
def _(engine, mo, payment, rental):
    month = mo.sql(
        f"""
        SELECT
            DATE_FORMAT(r.rental_date, '%Y-%m') AS 연도_월,
            COUNT(r.rental_id) AS 월별_대여건수,
            ROUND(SUM(p.amount), 2) AS 월별_매출액
        FROM rental r
        JOIN payment p ON r.rental_id = p.rental_id
        GROUP BY 연도_월
        ORDER BY 연도_월;
        """,
        engine=engine
    )
    return (month,)


@app.cell
def _(month, plt):
    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax1.bar(month['연도_월'], month['월별_대여건수'],
            color='#FF4C4C', label='대여건수')

    ax1.set_ylabel('대여건수', color='#FF4C4C')
    ax1.tick_params(axis='y', labelcolor='#FF4C4C')

    custom_labels = [f"{x[:4]}년 {int(x[5:]):d}월" for x in month['연도_월']]
    ax1.set_xticks(range(len(month)))
    ax1.set_xticklabels(custom_labels, rotation=0)

    for i, value in enumerate(month['월별_대여건수']):
        ax1.text(i, value + 100, f'{value:,}건',
                 ha='center', va='bottom', fontsize=9, color='black')

    ax2 = ax1.twinx()
    ax2.plot(range(len(month)), month['월별_매출액'],
             color='#444444', marker='o', linewidth=2, label='매출액')

    ax2.set_ylabel('매출액 ($)', color='#444444')
    ax2.tick_params(axis='y', labelcolor='#444444')

    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines + lines2, labels + labels2, loc='upper right')

    plt.title('월별 SakilaDVD 대여건수 및 매출액 추이', fontsize=14)
    fig.tight_layout()
    plt.show();
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## 2. 매장별 영업일수 및 평균매출 확인""")
    return


@app.cell
def _(engine, mo, payment, staff):
    _df = mo.sql(
        f"""
        SELECT
          store_id AS 매장ID,
          월,
          ROUND(SUM(amount), 2) AS 총매출,
            COUNT(DISTINCT rental_id) AS 대여건수,
            COUNT(DISTINCT payment_날짜) AS 영업일수,
          ROUND(SUM(amount) / DAY(LAST_DAY(STR_TO_DATE(CONCAT(월, '-01'), '%Y-%m-%d'))), 2) AS 일별_평균매출
        FROM (
          SELECT
            s.store_id,
            p.amount,
            p.rental_id,
            DATE_FORMAT(p.payment_date, '%Y-%m') AS 월,
            DATE(p.payment_date) AS payment_날짜
          FROM payment p
          JOIN staff s ON p.staff_id = s.staff_id
        ) AS 서브
        GROUP BY store_id, 월
        ORDER BY store_id, 월;
        """,
        engine=engine
    )
    return


@app.cell
def _(engine, mo, rental):
    rental_by_day = mo.sql(
        f"""
        SELECT
          DATE(rental_date) AS 날짜,
          COUNT(*) AS 대여건수
        FROM rental
        GROUP BY 날짜
        ORDER BY 날짜;
        """,
        engine=engine
    )
    return (rental_by_day,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## 3. DVD 대여건수의 일별/시간대별 분포""")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### (1) 일별 DVD 대여건수 
    - 7~8월에 수요가 몰림
    - 영업 일수가 일정하지 않고 변동성이 심함
    - 영업일수 자체가 적음 : 사실상 매출을 올릴 수 있는 날은 달의 절반도 채 되지 않음
    """
    )
    return


@app.cell
def _(pd, plt, rental_by_day, sns):
    rental_heatmap_df = rental_by_day.to_pandas()
    rental_heatmap_df['날짜'] = pd.to_datetime(rental_heatmap_df['날짜'])
    rental_heatmap_df['일'] = rental_heatmap_df['날짜'].dt.day
    rental_heatmap_df['년월'] = rental_heatmap_df['날짜'].dt.to_period('M').dt.to_timestamp()
    rental_heatmap_df['년월_label'] = rental_heatmap_df['년월'].dt.strftime('%Y년 %#m월') 

    sorted_index = rental_heatmap_df[['년월', '년월_label']].drop_duplicates().sort_values('년월')['년월_label']

    pivot = rental_heatmap_df.pivot_table(
        index='년월_label',
        columns='일',
        values='대여건수',
        aggfunc='sum',
        fill_value=0)

    for day in range(1, 32):
        if day not in pivot.columns:
            pivot[day] = 0
    pivot = pivot[sorted(pivot.columns)]
    pivot = pivot.loc[sorted_index]

    pivot.index.name = None

    plt.figure(figsize=(14, 6))
    sns.heatmap(pivot, cmap='OrRd', annot=True, fmt='d', linewidths=0.5)
    plt.title('일별 Sakila DVD 대여건수 히트맵')
    plt.xlabel('일(day)')
    plt.ylabel('')  
    plt.yticks(rotation=0)
    plt.xticks(ticks=[i for i in range(31)], labels=[str(i+1) for i in range(31)])

    plt.tight_layout()
    plt.show();

    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""### (2) 시간대별 DVD 대여건수 (전체기간)""")
    return


@app.cell
def _(engine, mo):
    rental = mo.sql(
        f"""
        SELECT * FROM rental
        """,
        engine=engine
    )
    return (rental,)


@app.cell
def _(np, pd, plt, rental, sns):
    rental_df = rental.to_pandas()
    rental_df['rental_date'] = pd.to_datetime(rental_df['rental_date'])
    rental_df['일'] = rental_df['rental_date'].dt.day
    rental_df['시간'] = rental_df['rental_date'].dt.hour  # 0~23시
    pivot_hour = rental_df.pivot_table(
        index='시간',
        columns='일',
        values='rental_id',  # rental_id 개수로 대여건수 집계
        aggfunc='count',
        fill_value=0)
    for h in range(24):
        if h not in pivot_hour.index:
            pivot_hour.loc[h] = 0
    for d in range(1, 32):
        if d not in pivot_hour.columns:
            pivot_hour[d] = 0

    pivot_hour = pivot_hour.sort_index().sort_index(axis=1)

    plt.figure(figsize=(14, 6))
    sns.heatmap(pivot_hour, cmap='YlOrBr', annot=True, fmt='d', linewidths=0.5)

    plt.title('시간대별 Sakila DVD 대여건수 히트맵')
    plt.xlabel('일(day)')
    plt.ylabel('시간(hour)')
    plt.xticks(ticks=np.arange(31), labels=[str(i+1) for i in range(31)])
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.show();
    return (rental_df,)


@app.cell
def _(rental_df):
    # 14일 15시에 대한 정보 확인 : 2006년 2월에만 182건
    spike_df = rental_df[(rental_df['일'] == 14) & (rental_df['시간'] == 15)].copy()
    spike_df['년월'] = spike_df['rental_date'].dt.to_period('M')
    monthly_count = spike_df.groupby('년월').size().reset_index(name='대여건수')
    monthly_count.sort_values('년월')

    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### (3) 시간대별 DVD 대여건수 (2005년)
    - 2006년 2월 14일 매출 182건이 모두 15시에 확인됨 -> 해당 값을 이상치로 간주하여 제외하고 분석 재시행
    - 야간에도 DVD 대여건수가 많음 = 야간에도 DVD 수요가 높음 -> 야간 운영시 직원 야간수당 등 추가 고정비용이 지속적으로 발생
    """
    )
    return


@app.cell
def _(engine, mo, rental):
    _2006 = mo.sql(
        f"""
        SELECT
          HOUR(rental_date) AS 시간,
          COUNT(*) AS 대여건수
        FROM rental
        WHERE DATE(rental_date) = '2006-02-14'
        GROUP BY 시간
        ORDER BY 시간;
        """,
        engine=engine
    )
    return


@app.cell
def _(np, plt, rental_df, sns):
    # 2006년 2월 제외한 데이터 필터링
    filtered_df = rental_df[~((rental_df['rental_date'].dt.year == 2006) & (rental_df['rental_date'].dt.month == 2))].copy()
    filtered_df['일'] = filtered_df['rental_date'].dt.day
    filtered_df['시간'] = filtered_df['rental_date'].dt.hour
    pivot_hour_filtered = filtered_df.pivot_table(
        index='시간',
        columns='일',
        values='rental_id',
        aggfunc='count',
        fill_value=0)
    for hour in range(24):
        if hour not in pivot_hour_filtered.index:
            pivot_hour_filtered.loc[hour] = 0
    for day_num in range(1, 32):
        if day_num not in pivot_hour_filtered.columns:
            pivot_hour_filtered[day_num] = 0
    pivot_hour_filtered = pivot_hour_filtered.sort_index().sort_index(axis=1)
    plt.figure(figsize=(14, 6))
    sns.heatmap(pivot_hour_filtered, cmap='OrRd', annot=True, fmt='d', linewidths=0.5)
    plt.title('시간대별 Sakila DVD 대여건수 히트맵 (2006년 2월 제외)')
    plt.xlabel('일(day)')
    plt.ylabel('시간(hour)')
    plt.xticks(ticks=np.arange(31), labels=[str(i+1) for i in range(31)])
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.show();
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""###""")
    return


@app.cell
def _(engine, mo, rental):
    _df = mo.sql(
        f"""
        SELECT rental_date, return_date FROM rental
        """,
        engine=engine
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # [2] Action Plan
    - 요일과 시간대별 대여 패턴을 분석하여 DVD 수요가 집중되는 피크 시간대 확인
    - 피크 시간대를 활용하여 신작 론칭 or 푸시 알림 타이밍을 발송함으로써 고객 반응 극대화 가능할 것으로 예상 (새벽시간은 제외)
    - [결과]
      - 15시가 가장 높으나, 그 중 182건은 모두 2006년 2월 14일 데이터..
    """
    )
    return


@app.cell
def _(mo):
    mo.md(r"""## 1. 시간별 패턴 분석""")
    return


@app.cell
def _(engine, mo, rental):
    hour_count = mo.sql(
        f"""
        SELECT
          HOUR(rental_date) AS 대여_시간대,
          COUNT(*) AS 대여_건수
        FROM rental
        GROUP BY HOUR(rental_date)
        ORDER BY 대여_시간대;
        """,
        engine=engine
    )
    return (hour_count,)


@app.cell
def _(hour_count, plt):
    hour_count_df = hour_count.to_pandas()
    avg_count = hour_count_df['대여_건수'].mean()
    max_row = hour_count_df.loc[hour_count_df['대여_건수'].idxmax()]
    max_hour = max_row['대여_시간대']
    max_count = max_row['대여_건수']

    plt.figure(figsize=(12, 6))

    plt.bar(hour_count_df['대여_시간대'], hour_count_df['대여_건수'],
            color='#FF4C4C', label='시간대별 대여 건수')

    plt.bar(max_hour, max_count, color='#FF4C4C', edgecolor='black', linewidth=2.5)

    for a in range(len(hour_count_df)):
        x = hour_count_df['대여_시간대'][a]
        y = hour_count_df['대여_건수'][a]
        plt.text(x, y + 5, f'{y}', ha='center', va='bottom', fontsize=9, color='black')

    plt.axhline(y=avg_count, color='#999999', linestyle='--', linewidth=2,
                label=f'평균 대여 건수 ({avg_count:.1f})')

    plt.xticks(range(0, 24))
    plt.xlabel('대여 시간대 (시)')
    plt.ylabel('대여 건수')
    plt.ylim(400, 920)
    plt.title('시간대별 DVD 대여 건수 분포 (SakilaTube 스타일)', fontsize=14)
    plt.legend()
    plt.grid(axis='y', linestyle=':', alpha=0.6)
    plt.tight_layout()
    plt.show();
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## 2. 요일별 패턴 분석""")
    return


@app.cell
def _(engine, mo, rental):
    weekday = mo.sql(
        f"""
        SELECT
          DATE_FORMAT(rental_date, '%W') AS 요일,
          COUNT(*) AS 대여_건수
        FROM rental
        GROUP BY 요일
        ORDER BY FIELD(요일, 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday');
        """,
        engine=engine
    )
    return (weekday,)


@app.cell
def _(pd, plt, weekday):
    weekday_df = weekday.to_pandas()
    max_value = weekday_df['대여_건수'].max()
    max_day = weekday_df.loc[weekday_df['대여_건수'].idxmax(), '요일']
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekday_df['요일'] = pd.Categorical(weekday_df['요일'], categories=day_order, ordered=True)
    weekday_df = weekday_df.sort_values('요일')
    fig_weekday, ax_weekday = plt.subplots(figsize=(10, 6))

    bar_color = '#FF4C4C'
    bars = ax_weekday.bar(weekday_df['요일'], weekday_df['대여_건수'], color=bar_color)

    for bar_idx, bar_obj in enumerate(bars):
        if weekday_df.iloc[bar_idx]['요일'] == max_day:
            bar_obj.set_edgecolor('black')
            bar_obj.set_linewidth(2.5)

    for bar_idx, bar_obj in enumerate(bars):
        height = bar_obj.get_height()
        ax_weekday.text(bar_obj.get_x() + bar_obj.get_width() / 2, height + 10,
                        f"{height:,}", ha='center', va='bottom', fontsize=9, color='black')

    ax_weekday.set_title("요일별 SakilaTube DVD 대여 건수", fontsize=14)
    ax_weekday.set_xlabel("요일")
    ax_weekday.set_ylabel("대여 건수")
    ax_weekday.grid(axis='y', linestyle=':', alpha=0.5)

    plt.tight_layout()
    plt.show();
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 3. 요일 + 시간대별 패턴 분석 
    ### (1) 전체기간
    """
    )
    return


@app.cell
def _(engine, mo, rental):
    weekday_hour = mo.sql(
        f"""
        SELECT
          DATE_FORMAT(rental_date, '%W') AS 요일,
          HOUR(rental_date) AS 시간대,
          COUNT(*) AS 대여_건수
        FROM rental
        GROUP BY 요일, 시간대
        ORDER BY 대여_건수 DESC;
        """,
        engine=engine
    )
    return (weekday_hour,)


@app.cell
def _(pd, plt, sns, weekday_hour):
    weekday_hour_df = weekday_hour.to_pandas()
    weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekday_hour_df['요일'] = pd.Categorical(weekday_hour_df['요일'], categories=weekday_order, ordered=True)
    pivot_weekday_hour = weekday_hour_df.pivot_table(
        index='요일',
        columns='시간대',
        values='대여_건수',
        aggfunc='sum',
        fill_value=0)

    for hr in range(24):
        if hr not in pivot_weekday_hour.columns:
            pivot_weekday_hour[hr] = 0
    pivot_weekday_hour = pivot_weekday_hour[sorted(pivot_weekday_hour.columns)]

    plt.figure(figsize=(14, 6))
    sns.heatmap(
        pivot_weekday_hour,
        cmap='Reds', 
        annot=True,
        fmt='d',
        linewidths=0.5,
        linecolor='lightgray',
        cbar_kws={"label": "대여 건수"})

    plt.title("요일 & 시간대별 Sakila DVD 대여건수 히트맵", fontsize=14)
    plt.xlabel("시간대 (시)")
    plt.ylabel("요일")
    plt.yticks(rotation=0)
    plt.xticks(ticks=range(24), labels=[str(i) for i in range(24)])

    plt.tight_layout()
    plt.show();
    return (weekday_hour_df,)


@app.cell
def _(mo):
    mo.md(r"""### (2) 2006/2/14 제외""")
    return


@app.cell
def _(engine, mo, rental):
    weekday_hour_filter = mo.sql(
        f"""
        SELECT
          DATE_FORMAT(rental_date, '%W') AS 요일,
          HOUR(rental_date) AS 시간대,
          COUNT(*) AS 대여_건수
        FROM rental
        WHERE YEAR(rental_date) != 2006
        GROUP BY 요일, 시간대
        ORDER BY 대여_건수 DESC;
        """,
        engine=engine
    )
    return (weekday_hour_filter,)


@app.cell
def _(pd, plt, sns, weekday_hour_filter):
    weekday_hour_filter_df = weekday_hour_filter.to_pandas()
    ordered_weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekday_hour_filter_df['요일'] = pd.Categorical(
        weekday_hour_filter_df['요일'],
        categories=ordered_weekdays,
        ordered=True)
    pivot_heatmap_filtered = weekday_hour_filter_df.pivot_table(
        index='요일',
        columns='시간대',
        values='대여_건수',
        aggfunc='sum',
        fill_value=0)
    for b in range(24):
        if b not in pivot_heatmap_filtered.columns:
            pivot_heatmap_filtered[b] = 0

    pivot_heatmap_filtered = pivot_heatmap_filtered[sorted(pivot_heatmap_filtered.columns)]

    fig_heatmap_filtered = plt.figure(figsize=(14, 6))
    sns.heatmap(
        pivot_heatmap_filtered,
        cmap='Reds',                     
        annot=True,
        fmt='d',
        linewidths=0.5,
        linecolor='lightgray',
        cbar_kws={"label": "대여 건수"})

    plt.title("요일 & 시간대별 SakilaTube DVD 대여건수 히트맵 (2006년 제외)", fontsize=14)
    plt.xlabel("시간대 (시)")
    plt.ylabel("요일")
    plt.yticks(rotation=0)
    plt.xticks(ticks=range(24), labels=[str(i) for i in range(24)])

    plt.tight_layout()
    plt.show();
    return (weekday_hour_filter_df,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""### (3) 상위 5% 요일 & 시간대 확인""")
    return


@app.cell
def _(weekday_hour_df, weekday_hour_filter_df):
    # 상위 5% 시간대 확인
    cutoff = weekday_hour_df['대여_건수'].quantile(0.95)

    top_5_percent_df = weekday_hour_df[weekday_hour_filter_df['대여_건수'] >= cutoff]

    top_5_percent_df.sort_values('대여_건수', ascending=False)
    return


if __name__ == "__main__":
    app.run()
