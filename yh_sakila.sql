use sakila;--

show tables;
show tables;

--  1.소비자 맞춤 서비스의 어려움.
--      기존 DVD 대여점은 고객의 개별적인 취향을 파악하고 이에 맞는 콘텐츠를 선별하여 추천하는 데 한계가 있음.
--      오프라인 DVD대여점에서는 직원의 경험이나 진열 상품 위주의 콘텐츠 제안만 가능. 


-- 고객별 최다 대여 장르 분석
use sakila;
SELECT
    cgr.customer_id,
    cgr.first_name,
    cgr.last_name,
    cgr.genre_name AS preferred_genre,
    cgr.rental_count
FROM (
    SELECT
        c.customer_id,
        c.first_name,
        c.last_name,
        cat.name AS genre_name,
        COUNT(r.rental_id) AS rental_count,
        ROW_NUMBER() OVER (PARTITION BY c.customer_id ORDER BY COUNT(r.rental_id) DESC) AS rn
    FROM
        customer AS c
    JOIN
        rental AS r ON c.customer_id = r.customer_id
    JOIN
        inventory AS i ON r.inventory_id = i.inventory_id
    JOIN
        film AS f ON i.film_id = f.film_id
    JOIN
        film_category AS fc ON f.film_id = fc.film_id
    JOIN
        category AS cat ON fc.category_id = cat.category_id
    GROUP BY
        c.customer_id, c.first_name, c.last_name, cat.name
) AS cgr
WHERE
    cgr.rn = 1
ORDER BY
    cgr.customer_id, cgr.rental_count DESC;
    --  데이터 분석을 통해 실제로 개인이 선호하는 장르를 구분할 수 있었지만, 오프라인 매장에서 바로바로 이 데이터를 사용해 추천할수는 없음.
    --  개인별 정리한 데이터는 존재하나 이를 실시간으로, 개별 고객에게 즉각적이며 차별된 경험으로 제공하는 시스템이 부재.
    --  2007년도 기준으로는 즉각적인 데이터 조회가 보편화 되지 않음.

--2. 매출 및 수익확인이 용이하지 않음
    --  2005~2007년도 오프라인 매장은 주로 하루 영업이 끝나면, 일괄적으로 매출데이터를 본사에 제출했을 것으로 예상됨.
    --  이로인해 즉각적인 의사결정에 제약이 생김.
    --  특정 매장의 매출이 떨어지거나, 급증하는 상황을 캐치하지 못해, 적절한 프로모션 제공, 인력배치가 어려움
    --  주로 지난 기간의 실적을 분석하기에 매출변화가 발생해도, 뒤늦게 매출데이터를 확인할수 있어 대응이 늦어짐.
    --  온라인으로 매출집계를 했을시 실시간으로 얻어지는 프로모션별 매출이라던지, 급증하는 영화DVD수요에 따른 대응책등 기민한 대응이 어려움을 시사.

use sakila;
--  매장별 월별 매출액과 월별 대여건수 분석
SELECT
    s.store_id,
    DATE_FORMAT(p.payment_date, '%Y-%m') AS payment_month,
    SUM(p.amount) AS total_monthly_revenue_by_store,
    COUNT(p.payment_id) AS total_payments_by_store
FROM
    store AS s
JOIN
    staff AS st ON s.store_id = st.store_id
JOIN
    payment AS p ON st.staff_id = p.staff_id
GROUP BY
    s.store_id, payment_month
ORDER BY
    s.store_id, payment_month;
    --  가게별 월 매출은 확인이 가능하나 어떤방식으로 결제했는지,프로모션의 영향을 받았는지,
    --  매출과 관련해서 총액은 파악이 가능하나 분류별 파악은 어려움.


--  ***3.편리하지 못함
    --  DVD 대여는 매장방문-재고확인-대여-반납의 단계를 거쳐야함.
    --  원하는DVD가 없거나,반납기한을 놓치는등 불편함을 경험.
    --  이런 불편함들은 직원의 추가 업무부담(재고확인,반납처리 등)으로 이어짐.
    --  새로운 대안을 찾게 만드는 요인이됨.
use sakila;
--  월별 연체 건수와 연체율
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
    -- dvd대여의 연체율이 무려 50%에 육박함을 보여줌.
    -- 이는 추가적인 업무와 비효율적인 운영을 초래함.


-- ***4.DVD대여점 운영의 높은 비용 발생
    --  DVD대여점은 인건비,임대료,상품관리비 등 고정적으로 발생하는 비용부담이 큼.
    --  오프라인 매장 특성상 매출의 변동폭과 달리 고정비용은 계속발생하고 수익성을 악화시키는 요인이 됨.
    --  수정한 이유는 데이터 분석결과 임대료나 상품관리비 고정비용등 데이터분석만으로는 나올수 없는 데이터들이 있음,

-- ***4.(수정)DVD 대여점 운영을 하며 놓치는 기회비용
    --  DVD라는 실제 상품을 대여하기때문에 재고가 없을시 대여 할 수 없음.
    --  지역적 한계로 인해 다양한 고객들을 끌어들일 기회를 놓침.
    --  시간적 한계도 있기 때문에 24시간 언제든 고객의 니즈를 충족 시키기 어려움
use sakila;

SELECT
    HOUR(rental_date) AS rental_hour_of_day, -- 대여 발생 시각 (시간 단위)
    COUNT(rental_id) AS total_rentals_at_hour
FROM
    rental
-- 특정 기간을 제한하려면 WHERE 절을 사용하세요 (예: WHERE rental_date BETWEEN '2007-01-01' AND '2007-12-31')
GROUP BY
    rental_hour_of_day
ORDER BY
    rental_hour_of_day; x축을 일자 y축을 시간 -> 사람들이 운영할때만 오기떄무넹 운영하지 않는 시간에는 수익을 놓치고 있다. 영업일자가 많은 8월을 기준으로
    가정을 잡음. 연결고리를 좀 잡았으면 좋겠음 컨셉을 쭉 유지할것. 샤킬라 튜브를 어떤식으로 만들것에 대한 비지니스적 설명. as to be 사이에 설명을 좀더 추가하면 좋을듯
    구독 비지니스 모델에 대해 찾아볼것(공부를 좀 해야될듯?)-지표,중요 키 등 ,Erd,KPI

use sakila;

select *
from customer;