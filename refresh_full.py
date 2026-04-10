import sys, json
sys.stdout.reconfigure(encoding='utf-8')
from google.auth import default
from googleapiclient.discovery import build
from google.cloud import bigquery
from datetime import datetime

creds, _ = default()
bq_client = bigquery.Client(project='meli-bi-data', credentials=creds)
sheets_service = build('sheets', 'v4', credentials=creds)
sid = '1g8qn97cuprduUs8dvVcF5PHaBuYNxmY5dX5UyLGmf0c'

QUERY = """
WITH

-- ── FUNNEL CF ────────────────────────────────────────────────────────────────
-- Solo usuarios que también clickearon CUOTA_FIJA en Card Summary
BASE_FUNNEL_CF AS (
  SELECT f.CUST_ID, f.MES, f.SITE, f.N_FUNNEL, f.PATH
  FROM (
    SELECT
      CUS_CUST_ID                             AS CUST_ID,
      DATE_TRUNC(CRD_NAV_DS_DATE, MONTH)      AS MES,
      SIT_SITE_ID                             AS SITE,
      CRD_NAV_FLOW_ORDER                      AS N_FUNNEL,
      CRD_NAV_PATH                            AS PATH
    FROM `meli-bi-data.WHOWNER.BT_CRD_NAV_FUNNEL_ACQ_MC`
    WHERE CRD_NAV_PATH IN (
      '/credits/merchant/enrollment/fixed_term_loan/simulation',
      '/credits/merchant/enrollment/fixed_term_loan/simulation/payments_detail',
      '/credits/merchant/enrollment/fixed_term_loan/kyc_onboarding',
      '/credits/merchant/enrollment/fixed_term_loan/kyc_onboarding/continue',
      '/credits/merchant/enrollment/fixed_term_loan/kyc_user_challenges_onboarding',
      '/credits/merchant/enrollment/fixed_term_loan/summary',
      '/credits/merchant/enrollment/fixed_term_loan/summary/accept_loan_action',
      '/credits/merchant/enrollment/fixed_term_loan/error',
      '/credits/merchant/enrollment/fixed_term_loan/in_review',
      '/credits/merchant/enrollment/fixed_term_loan/congrats',
      '/credits/merchant/enrollment/hub',
      '/credits/merchant/enrollment/hub/ftl_continue',
      '/credits/merchant/fixed_term_loan/amount_input',
      '/credits/merchant/fixed_term_loan/term_selection',
      '/credits/merchant/fixed_term_loan/term_selection/requested_amount_changed',
      '/credits/merchant/fixed_term_loan/kyc_onboarding',
      '/credits/merchant/fixed_term_loan/kyc_onboarding/continue',
      '/credits/merchant/fixed_term_loan/summary',
      '/credits/merchant/fixed_term_loan/summary/accept_loan_action',
      '/credits/merchant/fixed_term_loan/summary/contract_accessed',
      '/credits/merchant/fixed_term_loan/congrats',
      '/credits/merchant/fixed_term_loan/loan_request_error',
      '/credits/merchant/fixed_term_loan/redirect'
    )
    AND DATE(CRD_NAV_DS_DATE) BETWEEN DATE '2026-01-21' AND CURRENT_DATE()
    AND SIT_SITE_ID IN ('MLB', 'MLA', 'MLM', 'MLC')
    QUALIFY ROW_NUMBER() OVER (PARTITION BY CUST_ID, SITE, MES ORDER BY N_FUNNEL DESC) = 1
  ) f
  INNER JOIN (
    SELECT CAST(CUS_CUST_ID_SEL AS STRING) AS CUST_ID,
           SIT_SITE_ID                     AS SITE,
           DATE_TRUNC(VIEW_DATE, MONTH)    AS MES
    FROM `meli-bi-data.WHOWNER.DM_SUPPLY_SELLER_RECOMMENDATIONS`
    WHERE CARD_KEY = 'CUOTA_FIJA'
      AND VIEW_DATE BETWEEN DATE '2026-01-21' AND CURRENT_DATE()
      AND SIT_SITE_ID IN ('MLB', 'MLA', 'MLM', 'MLC')
    GROUP BY 1, 2, 3
  ) s ON f.CUST_ID = s.CUST_ID AND f.SITE = s.SITE AND f.MES = s.MES
),

-- ── FUNNEL PPV ───────────────────────────────────────────────────────────────
-- Solo usuarios que también clickearon CREDITS_PPV en Card Summary
BASE_FUNNEL_PPV AS (
  SELECT f.CUST_ID, f.MES, f.SITE, f.N_FUNNEL, f.PATH
  FROM (
    SELECT
      CUS_CUST_ID                             AS CUST_ID,
      DATE_TRUNC(CRD_NAV_DS_DATE, MONTH)      AS MES,
      SIT_SITE_ID                             AS SITE,
      CRD_NAV_FLOW_ORDER                      AS N_FUNNEL,
      CRD_NAV_PATH                            AS PATH
    FROM `meli-bi-data.WHOWNER.BT_CRD_NAV_FUNNEL_ACQ_MC`
    WHERE CRD_NAV_PATH IN (
      '/credits/merchant/enrollment/sales_percentage_loan/onboarding',
      '/credits/merchant/enrollment/sales_percentage_loan/simulation',
      '/credits/merchant/enrollment/sales_percentage_loan/kyc_onboarding',
      '/credits/merchant/enrollment/sales_percentage_loan/kyc_onboarding/continue',
      '/credits/merchant/enrollment/sales_percentage_loan/kyc_user_challenges_onboarding',
      '/credits/merchant/enrollment/sales_percentage_loan/summary',
      '/credits/merchant/enrollment/sales_percentage_loan/summary/accept_loan_action',
      '/credits/merchant/enrollment/sales_percentage_loan/error',
      '/credits/merchant/enrollment/sales_percentage_loan/congrats',
      '/credits/merchant/enrollment/hub',
      '/credits/merchant/enrollment/hub/spl_continue'
    )
    AND DATE(CRD_NAV_DS_DATE) BETWEEN DATE '2026-01-21' AND CURRENT_DATE()
    AND SIT_SITE_ID IN ('MLB', 'MLA', 'MLM', 'MLC')
    QUALIFY ROW_NUMBER() OVER (PARTITION BY CUST_ID, SITE, MES ORDER BY N_FUNNEL DESC) = 1
  ) f
  INNER JOIN (
    SELECT CAST(CUS_CUST_ID_SEL AS STRING) AS CUST_ID,
           SIT_SITE_ID                     AS SITE,
           DATE_TRUNC(VIEW_DATE, MONTH)    AS MES
    FROM `meli-bi-data.WHOWNER.DM_SUPPLY_SELLER_RECOMMENDATIONS`
    WHERE CARD_KEY = 'CREDITS_PPV'
      AND VIEW_DATE BETWEEN DATE '2026-01-21' AND CURRENT_DATE()
      AND SIT_SITE_ID IN ('MLB', 'MLA', 'MLM', 'MLC')
    GROUP BY 1, 2, 3
  ) s ON f.CUST_ID = s.CUST_ID AND f.SITE = s.SITE AND f.MES = s.MES
),

-- ── FUNNEL DINERO_EXPRESS ────────────────────────────────────────────────────
-- Solo usuarios que también clickearon CREDIT_PLUS en Card Summary
BASE_FUNNEL_DE AS (
  SELECT f.CUST_ID, f.MES, f.SITE, f.N_FUNNEL, f.PATH
  FROM (
    SELECT
      CUS_CUST_ID                             AS CUST_ID,
      DATE_TRUNC(CRD_NAV_DS_DATE, MONTH)      AS MES,
      SIT_SITE_ID                             AS SITE,
      CRD_NAV_FLOW_ORDER                      AS N_FUNNEL,
      CRD_NAV_PATH                            AS PATH
    FROM `meli-bi-data.WHOWNER.BT_CRD_NAV_FUNNEL_ACQ_MC`
    WHERE CRD_NAV_PATH IN (
      '/credits/merchant/express_money/onboarding',
      '/credits/merchant/express_money/amount_input',
      '/credits/merchant/express_money/term_selection',
      '/credits/merchant/express_money/term_selection/requested_amount_changed',
      '/credits/merchant/express_money/kyc_onboarding',
      '/credits/merchant/express_money/kyc_onboarding/continue',
      '/credits/merchant/express_money/summary',
      '/credits/merchant/express_money/summary/accept_loan_action',
      '/credits/merchant/express_money/summary/contract_accessed',
      '/credits/merchant/express_money/congrats',
      '/credits/merchant/express_money/error',
      '/credits/merchant/express_money/loan_request_error',
      '/credits/merchant/express_money/loan_request_failed',
      '/credits/merchant/express_money/access_denied'
    )
    AND DATE(CRD_NAV_DS_DATE) BETWEEN DATE '2026-01-21' AND CURRENT_DATE()
    AND SIT_SITE_ID IN ('MLB', 'MLA', 'MLM', 'MLC')
    QUALIFY ROW_NUMBER() OVER (PARTITION BY CUST_ID, SITE, MES ORDER BY N_FUNNEL DESC) = 1
  ) f
  INNER JOIN (
    SELECT CAST(CUS_CUST_ID_SEL AS STRING) AS CUST_ID,
           SIT_SITE_ID                     AS SITE,
           DATE_TRUNC(VIEW_DATE, MONTH)    AS MES
    FROM `meli-bi-data.WHOWNER.DM_SUPPLY_SELLER_RECOMMENDATIONS`
    WHERE CARD_KEY = 'CREDIT_PLUS'
      AND VIEW_DATE BETWEEN DATE '2026-01-21' AND CURRENT_DATE()
      AND SIT_SITE_ID IN ('MLB', 'MLA', 'MLM', 'MLC')
    GROUP BY 1, 2, 3
  ) s ON f.CUST_ID = s.CUST_ID AND f.SITE = s.SITE AND f.MES = s.MES
),

-- ── FUNNEL SELLER_LINE (via MELIDATA.TRACKS) ─────────────────────────────────
-- Solo usuarios que también clickearon LINEA_SELLER_FONDEO_CONSUMO en Card Summary
BASE_FUNNEL_LS AS (
  SELECT f.CUST_ID, f.MES, f.SITE, f.N_FUNNEL, f.PATH
  FROM (
    SELECT
      CAST(usr.user_id AS STRING)   AS CUST_ID,
      DATE_TRUNC(ds, MONTH)         AS MES,
      site                          AS SITE,
      MAX(CASE
        WHEN path = '/credits/merchant/fixed_term_loan/congrats'                   THEN 5
        WHEN path = '/credits/merchant/fixed_term_loan/summary/accept_loan_action' THEN 4
        WHEN path = '/credits/merchant/fixed_term_loan/term_selection'             THEN 3
        WHEN path = '/credits/merchant/fixed_term_loan/amount_input'               THEN 2

        ELSE 0
      END)                          AS N_FUNNEL,
      CAST(NULL AS STRING)          AS PATH
    FROM `meli-bi-data.MELIDATA.TRACKS`
    WHERE ds BETWEEN DATE '2026-01-21' AND CURRENT_DATE()
      AND site IN ('MLB', 'MLA', 'MLM', 'MLC')
      AND path IN (
        '/credits/merchant/fixed_term_loan/amount_input',
        '/credits/merchant/fixed_term_loan/term_selection',
        '/credits/merchant/fixed_term_loan/summary/accept_loan_action',
        '/credits/merchant/fixed_term_loan/congrats'
      )
      AND JSON_VALUE(event_data, '$.credit_line.product') = 'funding_long_term_loan'
      AND usr.user_id IS NOT NULL
    GROUP BY CUST_ID, MES, SITE
  ) f
  INNER JOIN (
    SELECT CAST(CUS_CUST_ID_SEL AS STRING) AS CUST_ID,
           SIT_SITE_ID                     AS SITE,
           DATE_TRUNC(VIEW_DATE, MONTH)    AS MES
    FROM `meli-bi-data.WHOWNER.DM_SUPPLY_SELLER_RECOMMENDATIONS`
    WHERE CARD_KEY = 'LINEA_SELLER_FONDEO_CONSUMO'
      AND VIEW_DATE BETWEEN DATE '2026-01-21' AND CURRENT_DATE()
      AND SIT_SITE_ID IN ('MLB', 'MLA', 'MLM', 'MLC')
    GROUP BY 1, 2, 3
  ) s ON f.CUST_ID = s.CUST_ID AND f.SITE = s.SITE AND f.MES = s.MES
),

-- ── OFERTAS (universo: todos los BU=ON sellers con propuesta activa) ──────────
BASE_OFERTA AS (
  SELECT
    SIT_SITE_ID                                                      AS SITE,
    CRD_PROP_ID                                                      AS PROP_ID,
    CUS_CUST_ID_BORROWER                                             AS CUST_ID,
    CRD_CREDIT_SUBTYPE                                               AS PRODUCT,
    DATE_TRUNC(CAST(CRD_PROP_CREATION_DATE_ID AS DATE), MONTH)       AS MES_PROP,
    CAST(CRD_PROP_CREATION_DATE_ID AS DATE)                          AS DATE_PROP,
    STATUS_USERS_CREDITS                                             AS FLAG_NEW_OLD,
    CRD_PROP_TOTAL_AMOUNT                                            AS PROP_AMT_LC,
    CRD_PROP_TOTAL_AMOUNT_USD                                        AS PROP_AMT_USD
  FROM `meli-bi-data.WHOWNER.BT_MP_CREDITS_PROPOSAL_DETAIL`
  WHERE SIT_SITE_ID IN ('MLB', 'MLA', 'MLM', 'MLC')
    AND CRD_CREDIT_SUBTYPE IN ('CF', 'PPV', 'DINERO_EXPRESS', 'SELLER_LINE')
    AND CRD_PROP_CREATION_DATE_ID BETWEEN DATE '2026-01-21' AND CURRENT_DATE()
    AND FLAG_DUPLICADOS = 0
  -- Por usuario+site+mes+producto, queda la propuesta más reciente
  QUALIFY ROW_NUMBER() OVER (
    PARTITION BY CUS_CUST_ID_BORROWER, SIT_SITE_ID,
                 DATE_TRUNC(CAST(CRD_PROP_CREATION_DATE_ID AS DATE), MONTH),
                 CRD_CREDIT_SUBTYPE
    ORDER BY CAST(CRD_PROP_CREATION_DATE_ID AS DATE) DESC
  ) = 1
),

-- ── AUDIENCIA: sellers que vieron Y clickearon la card el mismo día ───────────
-- View: path del summary tab con component_id = credit_card (MELIDATA)
-- Click: registro en DM_SUPPLY para alguno de los 4 productos
AUDIENCIA AS (
  SELECT DISTINCT
    V.user_id,
    V.SITE,
    V.fecha,
    C.PRODUCT
  FROM (
    SELECT DISTINCT
      CAST(T.usr.user_id AS STRING)  AS user_id,
      T.site                         AS SITE,
      DATE(T.ds)                     AS fecha
    FROM `meli-bi-data.MELIDATA.TRACKS` T
    WHERE T.ds BETWEEN DATE '2026-01-21' AND CURRENT_DATE()
      AND T.site IN ('MLB', 'MLA', 'MLM', 'MLC')
      AND T.path = '/seller_central/new_seller_summary/component'
      AND JSON_VALUE(T.event_data, '$.component_id') = 'credit_card'
      AND T.usr.user_id IS NOT NULL
  ) V
  INNER JOIN (
    SELECT DISTINCT
      CAST(CUS_CUST_ID_SEL AS STRING)  AS user_id,
      SIT_SITE_ID                      AS SITE,
      VIEW_DATE                        AS fecha,
      CASE CARD_KEY
        WHEN 'CUOTA_FIJA'                  THEN 'CF'
        WHEN 'CREDITS_PPV'                 THEN 'PPV'
        WHEN 'CREDIT_PLUS'                 THEN 'DINERO_EXPRESS'
        WHEN 'LINEA_SELLER_FONDEO_CONSUMO' THEN 'SELLER_LINE'
      END                              AS PRODUCT
    FROM `meli-bi-data.WHOWNER.DM_SUPPLY_SELLER_RECOMMENDATIONS`
    WHERE CARD_KEY IN ('CUOTA_FIJA', 'CREDITS_PPV', 'CREDIT_PLUS', 'LINEA_SELLER_FONDEO_CONSUMO')
      AND VIEW_DATE BETWEEN DATE '2026-01-21' AND CURRENT_DATE()
      AND SIT_SITE_ID IN ('MLB', 'MLA', 'MLM', 'MLC')
  ) C
    ON  V.user_id = C.user_id
    AND V.SITE    = C.SITE
    AND V.fecha   = C.fecha
),

-- ── ORIGINACIONES con atribución de 5 días ────────────────────────────────────
-- Condición: el seller tuvo un evento view+click y originó en los 5 días siguientes
BASE_ORIG AS (
  SELECT DISTINCT
    O.SIT_SITE_ID                                                    AS SITE,
    O.CRD_PROP_ID                                                    AS PROP_ID,
    O.CUS_CUST_ID_BORROWER                                           AS CUST_ID,
    O.CRD_CREDIT_SUBTYPE                                             AS PRODUCT,
    O.CRD_CREDIT_AMOUNT                                              AS CRD_AMT_LC,
    O.CRD_CREDIT_AMOUNT_USD                                          AS CRD_AMT_USD
  FROM `meli-bi-data.WHOWNER.BT_MP_CREDITS_CREDIT_DETAIL` O
  INNER JOIN AUDIENCIA A
    ON  CAST(O.CUS_CUST_ID_BORROWER AS STRING) = A.user_id
    AND O.SIT_SITE_ID        = A.SITE
    AND O.CRD_CREDIT_SUBTYPE = A.PRODUCT
    AND O.CRD_CREDIT_CREATION_DATE_ID BETWEEN A.fecha
                                          AND DATE_ADD(A.fecha, INTERVAL 5 DAY)
  WHERE O.SIT_SITE_ID IN ('MLB', 'MLA', 'MLM', 'MLC')
    AND O.CRD_CREDIT_SUBTYPE IN ('CF', 'PPV', 'DINERO_EXPRESS', 'SELLER_LINE')
    AND O.CRD_CREDIT_CREATION_DATE_ID BETWEEN DATE '2026-01-21' AND CURRENT_DATE()
)

SELECT
  O.SITE,
  O.MES_PROP                                                         AS MES,
  O.PRODUCT,

  CASE
    WHEN S.SEL_SEGMENT = 'LONGTAIL'    THEN '1.LONGTAIL'
    WHEN S.SEL_SEGMENT = 'SMB'         THEN '2.SMB'
    WHEN S.SEL_SEGMENT = 'BIG SELLERS' THEN '3.BIG SELLERS'
    ELSE NULL
  END                                                                AS SEL_SEGMENT,

  CASE
    WHEN SS.CUST_PRODUCT_DETAIL = 'ON NEW'         THEN 'ML'
    WHEN SS.CUST_PRODUCT_DETAIL = 'TRANSFERENCIAS' THEN 'TRANSFERENCIAS'
    ELSE 'MP'
  END                                                                AS BU,

  COALESCE(
    CASE
      WHEN F.N_FUNNEL = 5 THEN '5.CONGRATS'
      WHEN F.N_FUNNEL = 4 THEN '4.RYC'
      WHEN F.N_FUNNEL = 3 THEN '3.SIMULADOR'
      WHEN F.N_FUNNEL = 2 THEN '2.ONBOARDING'
      WHEN F.N_FUNNEL = 1 THEN '1.ADMIN'
      WHEN F.N_FUNNEL = 0 THEN '0.ERROR'
    END,
    '0.SIN INGRESO'
  )                                                                  AS FUNNEL,

  F.N_FUNNEL                                                         AS N_FUNNEL_RAW,
  F.PATH                                                             AS PATH_RAW,

  O.FLAG_NEW_OLD                                                     AS FLAG_FST_CRED,

  COUNT(DISTINCT O.CUST_ID)    AS Q_OFERTADOS,
  ROUND(SUM(O.PROP_AMT_LC))    AS PROP_AMT_LC,
  ROUND(SUM(O.PROP_AMT_USD))   AS PROP_AMT_USD,
  COUNT(DISTINCT C.CUST_ID)    AS Q_ORIGINADOS,
  ROUND(SUM(C.CRD_AMT_LC))     AS CRD_AMT_LC,
  ROUND(SUM(C.CRD_AMT_USD))    AS CRD_AMT_USD

FROM BASE_OFERTA O

LEFT JOIN BASE_ORIG C
  ON  O.PROP_ID = C.PROP_ID
  AND O.SITE    = C.SITE

LEFT JOIN (
  SELECT CUST_ID, MES, SITE, N_FUNNEL, PATH, 'CF'            AS PRODUCT FROM BASE_FUNNEL_CF
  UNION ALL
  SELECT CUST_ID, MES, SITE, N_FUNNEL, PATH, 'PPV'           AS PRODUCT FROM BASE_FUNNEL_PPV
  UNION ALL
  SELECT CUST_ID, MES, SITE, N_FUNNEL, PATH, 'DINERO_EXPRESS' AS PRODUCT FROM BASE_FUNNEL_DE
  UNION ALL
  SELECT CUST_ID, MES, SITE, N_FUNNEL, PATH, 'SELLER_LINE'    AS PRODUCT FROM BASE_FUNNEL_LS
) F
  ON  CAST(O.CUST_ID AS STRING) = F.CUST_ID
  AND O.SITE     = F.SITE
  AND O.MES_PROP = F.MES
  AND O.PRODUCT  = F.PRODUCT

LEFT JOIN `meli-bi-data.WHOWNER.LK_MP_MAUS_SEGMENTATION` S
  ON  O.CUST_ID  = S.CUS_CUST_ID
  AND O.SITE     = S.SIT_SITE_ID
  AND EXTRACT(YEAR  FROM O.MES_PROP) * 100
    + EXTRACT(MONTH FROM O.MES_PROP) = S.TIM_MONTH_ID

LEFT JOIN `meli-bi-data.WHOWNER.LK_MP_SEGMENTATION_SELLERS` SS
  ON  S.CUS_CUST_ID  = SS.CUS_CUST_ID
  AND S.SIT_SITE_ID  = SS.SIT_SITE_ID
  AND S.TIM_MONTH_ID = SS.TIM_MONTH

WHERE S.CUST_TYPE_PYL = 'SELLER'
  AND SS.CUST_PRODUCT_DETAIL = 'ON NEW'

GROUP BY ALL
ORDER BY 1, 2, 3, 4, 5, 6
"""

# Query 2: Views (card summary) + Clicks (DM_SUPPLY) — solo sellers BU=ON
QUERY_VC = """
WITH
-- Sellers BU=ON por site/mes (precalculado para joins eficientes)
ON_SELLERS AS (
  SELECT DISTINCT
    S.CUS_CUST_ID,
    S.SIT_SITE_ID,
    S.TIM_MONTH_ID
  FROM `meli-bi-data.WHOWNER.LK_MP_MAUS_SEGMENTATION` S
  INNER JOIN `meli-bi-data.WHOWNER.LK_MP_SEGMENTATION_SELLERS` SS
    ON  S.CUS_CUST_ID  = SS.CUS_CUST_ID
    AND S.SIT_SITE_ID  = SS.SIT_SITE_ID
    AND S.TIM_MONTH_ID = SS.TIM_MONTH
  WHERE S.CUST_TYPE_PYL          = 'SELLER'
    AND SS.CUST_PRODUCT_DETAIL   = 'ON NEW'
    AND S.SIT_SITE_ID IN ('MLB','MLA','MLM','MLC')
),
-- Views totales (cualquier producto) — para card TOTAL
-- Join con DM_SUPPLY garantiza Views >= Clicks siempre
VIEWS_TOTAL AS (
  SELECT
    DATE_TRUNC(T.ds, MONTH)       AS MES,
    T.site                        AS SITE,
    COUNT(DISTINCT T.usr.user_id) AS Q_VIEWS_ALL
  FROM `meli-bi-data.MELIDATA.TRACKS` T
  INNER JOIN ON_SELLERS ON_S
    ON  CAST(T.usr.user_id AS STRING) = CAST(ON_S.CUS_CUST_ID AS STRING)
    AND T.site = ON_S.SIT_SITE_ID
    AND EXTRACT(YEAR FROM T.ds) * 100 + EXTRACT(MONTH FROM T.ds) = ON_S.TIM_MONTH_ID
  INNER JOIN (
    SELECT DISTINCT
      CAST(CUS_CUST_ID_SEL AS STRING)        AS CUST_ID,
      SIT_SITE_ID                            AS SITE,
      DATE_TRUNC(VIEW_DATE, MONTH)           AS MES
    FROM `meli-bi-data.WHOWNER.DM_SUPPLY_SELLER_RECOMMENDATIONS`
    WHERE CARD_KEY IN ('CUOTA_FIJA','CREDITS_PPV','CREDIT_PLUS','LINEA_SELLER_FONDEO_CONSUMO')
      AND VIEW_DATE BETWEEN DATE '2026-01-21' AND CURRENT_DATE()
      AND SIT_SITE_ID IN ('MLB','MLA','MLM','MLC')
  ) D
    ON  CAST(T.usr.user_id AS STRING) = D.CUST_ID
    AND T.site                        = D.SITE
    AND DATE_TRUNC(T.ds, MONTH)       = D.MES
  WHERE T.ds BETWEEN DATE '2026-01-21' AND CURRENT_DATE()
    AND T.site IN ('MLB','MLA','MLM','MLC')
    AND T.path = '/seller_central/new_seller_summary/component'
    AND JSON_VALUE(T.event_data, '$.component_id') = 'credit_card'
    AND T.usr.user_id IS NOT NULL
  GROUP BY 1, 2
),
-- Views por producto — para cards por producto
-- Join con DM_SUPPLY por product garantiza Views >= Clicks por producto
VIEWS_PROD AS (
  SELECT
    DATE_TRUNC(T.ds, MONTH)       AS MES,
    T.site                        AS SITE,
    D.PRODUCT                     AS PRODUCT,
    COUNT(DISTINCT T.usr.user_id) AS Q_VIEWS
  FROM `meli-bi-data.MELIDATA.TRACKS` T
  INNER JOIN ON_SELLERS ON_S
    ON  CAST(T.usr.user_id AS STRING) = CAST(ON_S.CUS_CUST_ID AS STRING)
    AND T.site = ON_S.SIT_SITE_ID
    AND EXTRACT(YEAR FROM T.ds) * 100 + EXTRACT(MONTH FROM T.ds) = ON_S.TIM_MONTH_ID
  INNER JOIN (
    SELECT DISTINCT
      CAST(CUS_CUST_ID_SEL AS STRING)        AS CUST_ID,
      SIT_SITE_ID                            AS SITE,
      DATE_TRUNC(VIEW_DATE, MONTH)           AS MES,
      CASE CARD_KEY
        WHEN 'CUOTA_FIJA'                  THEN 'CF'
        WHEN 'CREDITS_PPV'                 THEN 'PPV'
        WHEN 'CREDIT_PLUS'                 THEN 'DINERO_EXPRESS'
        WHEN 'LINEA_SELLER_FONDEO_CONSUMO' THEN 'SELLER_LINE'
      END                                    AS PRODUCT
    FROM `meli-bi-data.WHOWNER.DM_SUPPLY_SELLER_RECOMMENDATIONS`
    WHERE CARD_KEY IN ('CUOTA_FIJA','CREDITS_PPV','CREDIT_PLUS','LINEA_SELLER_FONDEO_CONSUMO')
      AND VIEW_DATE BETWEEN DATE '2026-01-21' AND CURRENT_DATE()
      AND SIT_SITE_ID IN ('MLB','MLA','MLM','MLC')
  ) D
    ON  CAST(T.usr.user_id AS STRING) = D.CUST_ID
    AND T.site                        = D.SITE
    AND DATE_TRUNC(T.ds, MONTH)       = D.MES
  WHERE T.ds BETWEEN DATE '2026-01-21' AND CURRENT_DATE()
    AND T.site IN ('MLB','MLA','MLM','MLC')
    AND T.path = '/seller_central/new_seller_summary/component'
    AND JSON_VALUE(T.event_data, '$.component_id') = 'credit_card'
    AND T.usr.user_id IS NOT NULL
  GROUP BY 1, 2, 3
),
CLICKS AS (
  SELECT
    DATE_TRUNC(D.VIEW_DATE, MONTH) AS MES,
    D.SIT_SITE_ID                  AS SITE,
    CASE D.CARD_KEY
      WHEN 'CUOTA_FIJA'                  THEN 'CF'
      WHEN 'CREDITS_PPV'                 THEN 'PPV'
      WHEN 'CREDIT_PLUS'                 THEN 'DINERO_EXPRESS'
      WHEN 'LINEA_SELLER_FONDEO_CONSUMO' THEN 'SELLER_LINE'
    END                            AS PRODUCT,
    COUNT(DISTINCT CAST(D.CUS_CUST_ID_SEL AS STRING)) AS Q_CLICKS
  FROM `meli-bi-data.WHOWNER.DM_SUPPLY_SELLER_RECOMMENDATIONS` D
  INNER JOIN ON_SELLERS ON_S
    ON  CAST(D.CUS_CUST_ID_SEL AS STRING) = CAST(ON_S.CUS_CUST_ID AS STRING)
    AND D.SIT_SITE_ID = ON_S.SIT_SITE_ID
    AND EXTRACT(YEAR FROM D.VIEW_DATE) * 100 + EXTRACT(MONTH FROM D.VIEW_DATE) = ON_S.TIM_MONTH_ID
  WHERE D.CARD_KEY IN ('CUOTA_FIJA','CREDITS_PPV','CREDIT_PLUS','LINEA_SELLER_FONDEO_CONSUMO')
    AND D.VIEW_DATE BETWEEN DATE '2026-01-21' AND CURRENT_DATE()
    AND D.SIT_SITE_ID IN ('MLB','MLA','MLM','MLC')
  GROUP BY 1, 2, 3
)
SELECT
  C.SITE, C.MES, C.PRODUCT,
  COALESCE(VT.Q_VIEWS_ALL, 0) AS Q_VIEWS_ALL,
  COALESCE(VP.Q_VIEWS, 0)     AS Q_VIEWS,
  C.Q_CLICKS
FROM CLICKS C
LEFT JOIN VIEWS_TOTAL VT ON C.MES = VT.MES AND C.SITE = VT.SITE
LEFT JOIN VIEWS_PROD  VP ON C.MES = VP.MES AND C.SITE = VP.SITE AND C.PRODUCT = VP.PRODUCT
ORDER BY 1, 2, 3
"""

# ── QUERY V2: todo anclado al mes de OFERTA ───────────────────────────────────
# Diferencias vs QUERY:
#   - BASE_FUNNEL_*: sin MES en join con DM_SUPPLY ni en QUALIFY
#   - JOIN con FUNNEL: sin AND O.MES_PROP = F.MES
#   - VIEWS_SELLERS / CLICKS_SELLERS: sin filtro de mes, joined a ofertados
#   - Q_VIEWS y Q_CLICKS salen del query principal (no de QUERY_VC)
QUERY_V2 = """
WITH

BASE_FUNNEL_CF AS (
  SELECT f.CUST_ID, f.SITE, f.N_FUNNEL, f.PATH
  FROM (
    SELECT
      CUS_CUST_ID        AS CUST_ID,
      SIT_SITE_ID        AS SITE,
      CRD_NAV_FLOW_ORDER AS N_FUNNEL,
      CRD_NAV_PATH       AS PATH
    FROM `meli-bi-data.WHOWNER.BT_CRD_NAV_FUNNEL_ACQ_MC`
    WHERE CRD_NAV_PATH IN (
      '/credits/merchant/enrollment/fixed_term_loan/simulation',
      '/credits/merchant/enrollment/fixed_term_loan/simulation/payments_detail',
      '/credits/merchant/enrollment/fixed_term_loan/kyc_onboarding',
      '/credits/merchant/enrollment/fixed_term_loan/kyc_onboarding/continue',
      '/credits/merchant/enrollment/fixed_term_loan/kyc_user_challenges_onboarding',
      '/credits/merchant/enrollment/fixed_term_loan/summary',
      '/credits/merchant/enrollment/fixed_term_loan/summary/accept_loan_action',
      '/credits/merchant/enrollment/fixed_term_loan/error',
      '/credits/merchant/enrollment/fixed_term_loan/in_review',
      '/credits/merchant/enrollment/fixed_term_loan/congrats',
      '/credits/merchant/enrollment/hub',
      '/credits/merchant/enrollment/hub/ftl_continue',
      '/credits/merchant/fixed_term_loan/amount_input',
      '/credits/merchant/fixed_term_loan/term_selection',
      '/credits/merchant/fixed_term_loan/term_selection/requested_amount_changed',
      '/credits/merchant/fixed_term_loan/kyc_onboarding',
      '/credits/merchant/fixed_term_loan/kyc_onboarding/continue',
      '/credits/merchant/fixed_term_loan/summary',
      '/credits/merchant/fixed_term_loan/summary/accept_loan_action',
      '/credits/merchant/fixed_term_loan/summary/contract_accessed',
      '/credits/merchant/fixed_term_loan/congrats',
      '/credits/merchant/fixed_term_loan/loan_request_error',
      '/credits/merchant/fixed_term_loan/redirect'
    )
    AND DATE(CRD_NAV_DS_DATE) BETWEEN DATE '2026-01-21' AND CURRENT_DATE()
    AND SIT_SITE_ID IN ('MLB', 'MLA', 'MLM', 'MLC')
    QUALIFY ROW_NUMBER() OVER (PARTITION BY CUS_CUST_ID, SIT_SITE_ID ORDER BY CRD_NAV_FLOW_ORDER DESC) = 1
  ) f
  INNER JOIN (
    SELECT DISTINCT CAST(CUS_CUST_ID_SEL AS STRING) AS CUST_ID, SIT_SITE_ID AS SITE
    FROM `meli-bi-data.WHOWNER.DM_SUPPLY_SELLER_RECOMMENDATIONS`
    WHERE CARD_KEY = 'CUOTA_FIJA'
      AND VIEW_DATE BETWEEN DATE '2026-01-21' AND CURRENT_DATE()
      AND SIT_SITE_ID IN ('MLB', 'MLA', 'MLM', 'MLC')
  ) s ON f.CUST_ID = s.CUST_ID AND f.SITE = s.SITE
),

BASE_FUNNEL_PPV AS (
  SELECT f.CUST_ID, f.SITE, f.N_FUNNEL, f.PATH
  FROM (
    SELECT
      CUS_CUST_ID        AS CUST_ID,
      SIT_SITE_ID        AS SITE,
      CRD_NAV_FLOW_ORDER AS N_FUNNEL,
      CRD_NAV_PATH       AS PATH
    FROM `meli-bi-data.WHOWNER.BT_CRD_NAV_FUNNEL_ACQ_MC`
    WHERE CRD_NAV_PATH IN (
      '/credits/merchant/enrollment/sales_percentage_loan/onboarding',
      '/credits/merchant/enrollment/sales_percentage_loan/simulation',
      '/credits/merchant/enrollment/sales_percentage_loan/kyc_onboarding',
      '/credits/merchant/enrollment/sales_percentage_loan/kyc_onboarding/continue',
      '/credits/merchant/enrollment/sales_percentage_loan/kyc_user_challenges_onboarding',
      '/credits/merchant/enrollment/sales_percentage_loan/summary',
      '/credits/merchant/enrollment/sales_percentage_loan/summary/accept_loan_action',
      '/credits/merchant/enrollment/sales_percentage_loan/error',
      '/credits/merchant/enrollment/sales_percentage_loan/congrats',
      '/credits/merchant/enrollment/hub',
      '/credits/merchant/enrollment/hub/spl_continue'
    )
    AND DATE(CRD_NAV_DS_DATE) BETWEEN DATE '2026-01-21' AND CURRENT_DATE()
    AND SIT_SITE_ID IN ('MLB', 'MLA', 'MLM', 'MLC')
    QUALIFY ROW_NUMBER() OVER (PARTITION BY CUS_CUST_ID, SIT_SITE_ID ORDER BY CRD_NAV_FLOW_ORDER DESC) = 1
  ) f
  INNER JOIN (
    SELECT DISTINCT CAST(CUS_CUST_ID_SEL AS STRING) AS CUST_ID, SIT_SITE_ID AS SITE
    FROM `meli-bi-data.WHOWNER.DM_SUPPLY_SELLER_RECOMMENDATIONS`
    WHERE CARD_KEY = 'CREDITS_PPV'
      AND VIEW_DATE BETWEEN DATE '2026-01-21' AND CURRENT_DATE()
      AND SIT_SITE_ID IN ('MLB', 'MLA', 'MLM', 'MLC')
  ) s ON f.CUST_ID = s.CUST_ID AND f.SITE = s.SITE
),

BASE_FUNNEL_DE AS (
  SELECT f.CUST_ID, f.SITE, f.N_FUNNEL, f.PATH
  FROM (
    SELECT
      CUS_CUST_ID        AS CUST_ID,
      SIT_SITE_ID        AS SITE,
      CRD_NAV_FLOW_ORDER AS N_FUNNEL,
      CRD_NAV_PATH       AS PATH
    FROM `meli-bi-data.WHOWNER.BT_CRD_NAV_FUNNEL_ACQ_MC`
    WHERE CRD_NAV_PATH IN (
      '/credits/merchant/express_money/onboarding',
      '/credits/merchant/express_money/amount_input',
      '/credits/merchant/express_money/term_selection',
      '/credits/merchant/express_money/term_selection/requested_amount_changed',
      '/credits/merchant/express_money/kyc_onboarding',
      '/credits/merchant/express_money/kyc_onboarding/continue',
      '/credits/merchant/express_money/summary',
      '/credits/merchant/express_money/summary/accept_loan_action',
      '/credits/merchant/express_money/summary/contract_accessed',
      '/credits/merchant/express_money/congrats',
      '/credits/merchant/express_money/error',
      '/credits/merchant/express_money/loan_request_error',
      '/credits/merchant/express_money/loan_request_failed',
      '/credits/merchant/express_money/access_denied'
    )
    AND DATE(CRD_NAV_DS_DATE) BETWEEN DATE '2026-01-21' AND CURRENT_DATE()
    AND SIT_SITE_ID IN ('MLB', 'MLA', 'MLM', 'MLC')
    QUALIFY ROW_NUMBER() OVER (PARTITION BY CUS_CUST_ID, SIT_SITE_ID ORDER BY CRD_NAV_FLOW_ORDER DESC) = 1
  ) f
  INNER JOIN (
    SELECT DISTINCT CAST(CUS_CUST_ID_SEL AS STRING) AS CUST_ID, SIT_SITE_ID AS SITE
    FROM `meli-bi-data.WHOWNER.DM_SUPPLY_SELLER_RECOMMENDATIONS`
    WHERE CARD_KEY = 'CREDIT_PLUS'
      AND VIEW_DATE BETWEEN DATE '2026-01-21' AND CURRENT_DATE()
      AND SIT_SITE_ID IN ('MLB', 'MLA', 'MLM', 'MLC')
  ) s ON f.CUST_ID = s.CUST_ID AND f.SITE = s.SITE
),

BASE_FUNNEL_LS AS (
  SELECT f.CUST_ID, f.SITE, f.N_FUNNEL, f.PATH
  FROM (
    SELECT
      CAST(usr.user_id AS STRING) AS CUST_ID,
      site                        AS SITE,
      MAX(CASE
        WHEN path = '/credits/merchant/fixed_term_loan/congrats'                   THEN 5
        WHEN path = '/credits/merchant/fixed_term_loan/summary/accept_loan_action' THEN 4
        WHEN path = '/credits/merchant/fixed_term_loan/term_selection'             THEN 3
        WHEN path = '/credits/merchant/fixed_term_loan/amount_input'               THEN 2

        ELSE 0
      END)                        AS N_FUNNEL,
      CAST(NULL AS STRING)        AS PATH
    FROM `meli-bi-data.MELIDATA.TRACKS`
    WHERE ds BETWEEN DATE '2026-01-21' AND CURRENT_DATE()
      AND site IN ('MLB', 'MLA', 'MLM', 'MLC')
      AND path IN (
        '/credits/merchant/fixed_term_loan/amount_input',
        '/credits/merchant/fixed_term_loan/term_selection',
        '/credits/merchant/fixed_term_loan/summary/accept_loan_action',
        '/credits/merchant/fixed_term_loan/congrats'
      )
      AND JSON_VALUE(event_data, '$.credit_line.product') = 'funding_long_term_loan'
      AND usr.user_id IS NOT NULL
    GROUP BY CUST_ID, SITE
  ) f
  INNER JOIN (
    SELECT DISTINCT CAST(CUS_CUST_ID_SEL AS STRING) AS CUST_ID, SIT_SITE_ID AS SITE
    FROM `meli-bi-data.WHOWNER.DM_SUPPLY_SELLER_RECOMMENDATIONS`
    WHERE CARD_KEY = 'LINEA_SELLER_FONDEO_CONSUMO'
      AND VIEW_DATE BETWEEN DATE '2026-01-21' AND CURRENT_DATE()
      AND SIT_SITE_ID IN ('MLB', 'MLA', 'MLM', 'MLC')
  ) s ON f.CUST_ID = s.CUST_ID AND f.SITE = s.SITE
),

BASE_OFERTA AS (
  SELECT
    SIT_SITE_ID                                                      AS SITE,
    CRD_PROP_ID                                                      AS PROP_ID,
    CUS_CUST_ID_BORROWER                                             AS CUST_ID,
    CRD_CREDIT_SUBTYPE                                               AS PRODUCT,
    DATE_TRUNC(CAST(CRD_PROP_CREATION_DATE_ID AS DATE), MONTH)       AS MES_PROP,
    CAST(CRD_PROP_CREATION_DATE_ID AS DATE)                          AS DATE_PROP,
    CRD_PROP_TOTAL_AMOUNT                                            AS PROP_AMT_LC,
    CRD_PROP_TOTAL_AMOUNT_USD                                        AS PROP_AMT_USD
  FROM `meli-bi-data.WHOWNER.BT_MP_CREDITS_PROPOSAL_DETAIL`
  WHERE SIT_SITE_ID IN ('MLB', 'MLA', 'MLM', 'MLC')
    AND CRD_CREDIT_SUBTYPE IN ('CF', 'PPV', 'DINERO_EXPRESS', 'SELLER_LINE')
    AND CRD_PROP_CREATION_DATE_ID BETWEEN DATE '2026-01-21' AND CURRENT_DATE()
    AND FLAG_DUPLICADOS = 0
  QUALIFY ROW_NUMBER() OVER (
    PARTITION BY CUS_CUST_ID_BORROWER, SIT_SITE_ID,
                 DATE_TRUNC(CAST(CRD_PROP_CREATION_DATE_ID AS DATE), MONTH),
                 CRD_CREDIT_SUBTYPE
    ORDER BY CAST(CRD_PROP_CREATION_DATE_ID AS DATE) DESC
  ) = 1
),

AUDIENCIA AS (
  SELECT DISTINCT V.user_id, V.SITE, V.fecha, C.PRODUCT
  FROM (
    SELECT DISTINCT CAST(T.usr.user_id AS STRING) AS user_id, T.site AS SITE, DATE(T.ds) AS fecha
    FROM `meli-bi-data.MELIDATA.TRACKS` T
    WHERE T.ds BETWEEN DATE '2026-01-21' AND CURRENT_DATE()
      AND T.site IN ('MLB', 'MLA', 'MLM', 'MLC')
      AND T.path = '/seller_central/new_seller_summary/component'
      AND JSON_VALUE(T.event_data, '$.component_id') = 'credit_card'
      AND T.usr.user_id IS NOT NULL
  ) V
  INNER JOIN (
    SELECT DISTINCT
      CAST(CUS_CUST_ID_SEL AS STRING) AS user_id, SIT_SITE_ID AS SITE, VIEW_DATE AS fecha,
      CASE CARD_KEY
        WHEN 'CUOTA_FIJA'                  THEN 'CF'
        WHEN 'CREDITS_PPV'                 THEN 'PPV'
        WHEN 'CREDIT_PLUS'                 THEN 'DINERO_EXPRESS'
        WHEN 'LINEA_SELLER_FONDEO_CONSUMO' THEN 'SELLER_LINE'
      END AS PRODUCT
    FROM `meli-bi-data.WHOWNER.DM_SUPPLY_SELLER_RECOMMENDATIONS`
    WHERE CARD_KEY IN ('CUOTA_FIJA', 'CREDITS_PPV', 'CREDIT_PLUS', 'LINEA_SELLER_FONDEO_CONSUMO')
      AND VIEW_DATE BETWEEN DATE '2026-01-21' AND CURRENT_DATE()
      AND SIT_SITE_ID IN ('MLB', 'MLA', 'MLM', 'MLC')
  ) C ON V.user_id = C.user_id AND V.SITE = C.SITE AND V.fecha = C.fecha
),

BASE_ORIG AS (
  SELECT DISTINCT
    O.SIT_SITE_ID AS SITE, O.CRD_PROP_ID AS PROP_ID, O.CUS_CUST_ID_BORROWER AS CUST_ID,
    O.CRD_CREDIT_SUBTYPE AS PRODUCT, O.CRD_CREDIT_AMOUNT AS CRD_AMT_LC,
    O.CRD_CREDIT_AMOUNT_USD AS CRD_AMT_USD, O.FLAG_FST_CRED AS FLAG_FST_CRED
  FROM `meli-bi-data.WHOWNER.BT_MP_CREDITS_CREDIT_DETAIL` O
  INNER JOIN AUDIENCIA A
    ON  CAST(O.CUS_CUST_ID_BORROWER AS STRING) = A.user_id
    AND O.SIT_SITE_ID        = A.SITE
    AND O.CRD_CREDIT_SUBTYPE = A.PRODUCT
    AND O.CRD_CREDIT_CREATION_DATE_ID BETWEEN A.fecha AND DATE_ADD(A.fecha, INTERVAL 5 DAY)
  WHERE O.SIT_SITE_ID IN ('MLB', 'MLA', 'MLM', 'MLC')
    AND O.CRD_CREDIT_SUBTYPE IN ('CF', 'PPV', 'DINERO_EXPRESS', 'SELLER_LINE')
    AND O.CRD_CREDIT_CREATION_DATE_ID BETWEEN DATE '2026-01-21' AND CURRENT_DATE()
),

-- Views: sellers que vieron la card en MELIDATA (sin filtro de mes)
VIEWS_SELLERS AS (
  SELECT DISTINCT CAST(T.usr.user_id AS STRING) AS user_id, T.site AS SITE
  FROM `meli-bi-data.MELIDATA.TRACKS` T
  WHERE T.ds BETWEEN DATE '2026-01-21' AND CURRENT_DATE()
    AND T.site IN ('MLB', 'MLA', 'MLM', 'MLC')
    AND T.path = '/seller_central/new_seller_summary/component'
    AND JSON_VALUE(T.event_data, '$.component_id') = 'credit_card'
    AND T.usr.user_id IS NOT NULL
),

-- Clicks: sellers que clickearon la card en DM_SUPPLY (sin filtro de mes, por producto)
CLICKS_SELLERS AS (
  SELECT DISTINCT
    CAST(CUS_CUST_ID_SEL AS STRING) AS user_id,
    SIT_SITE_ID                     AS SITE,
    CASE CARD_KEY
      WHEN 'CUOTA_FIJA'                  THEN 'CF'
      WHEN 'CREDITS_PPV'                 THEN 'PPV'
      WHEN 'CREDIT_PLUS'                 THEN 'DINERO_EXPRESS'
      WHEN 'LINEA_SELLER_FONDEO_CONSUMO' THEN 'SELLER_LINE'
    END                             AS PRODUCT
  FROM `meli-bi-data.WHOWNER.DM_SUPPLY_SELLER_RECOMMENDATIONS`
  WHERE CARD_KEY IN ('CUOTA_FIJA', 'CREDITS_PPV', 'CREDIT_PLUS', 'LINEA_SELLER_FONDEO_CONSUMO')
    AND VIEW_DATE BETWEEN DATE '2026-01-21' AND CURRENT_DATE()
    AND SIT_SITE_ID IN ('MLB', 'MLA', 'MLM', 'MLC')
)

SELECT
  O.SITE,
  O.MES_PROP AS MES,
  O.PRODUCT,

  CASE
    WHEN S.SEL_SEGMENT = 'LONGTAIL'    THEN '1.LONGTAIL'
    WHEN S.SEL_SEGMENT = 'SMB'         THEN '2.SMB'
    WHEN S.SEL_SEGMENT = 'BIG SELLERS' THEN '3.BIG SELLERS'
    ELSE NULL
  END AS SEL_SEGMENT,

  CASE
    WHEN SS.CUST_PRODUCT_DETAIL = 'ON NEW'         THEN 'ML'
    WHEN SS.CUST_PRODUCT_DETAIL = 'TRANSFERENCIAS' THEN 'TRANSFERENCIAS'
    ELSE 'MP'
  END AS BU,

  COALESCE(CASE
    WHEN F.N_FUNNEL = 5 THEN '5.CONGRATS'
    WHEN F.N_FUNNEL = 4 THEN '4.RYC'
    WHEN F.N_FUNNEL = 3 THEN '3.SIMULADOR'
    WHEN F.N_FUNNEL = 2 THEN '2.ONBOARDING'
    WHEN F.N_FUNNEL = 1 THEN '1.ADMIN'
    WHEN F.N_FUNNEL = 0 THEN '0.ERROR'
  END, '0.SIN INGRESO') AS FUNNEL,

  F.N_FUNNEL AS N_FUNNEL_RAW,
  F.PATH     AS PATH_RAW,
  C.FLAG_FST_CRED,
  K.KYC_ENTITY_TYPE,

  COUNT(DISTINCT CASE WHEN VS.user_id IS NOT NULL THEN O.CUST_ID END) AS Q_VIEWS,
  COUNT(DISTINCT CASE WHEN CS.user_id IS NOT NULL THEN O.CUST_ID END) AS Q_CLICKS,
  COUNT(DISTINCT O.CUST_ID)    AS Q_OFERTADOS,
  ROUND(SUM(O.PROP_AMT_LC))    AS PROP_AMT_LC,
  ROUND(SUM(O.PROP_AMT_USD))   AS PROP_AMT_USD,
  COUNT(DISTINCT C.CUST_ID)    AS Q_ORIGINADOS,
  ROUND(SUM(C.CRD_AMT_LC))     AS CRD_AMT_LC,
  ROUND(SUM(C.CRD_AMT_USD))    AS CRD_AMT_USD

FROM BASE_OFERTA O

LEFT JOIN BASE_ORIG C
  ON  O.PROP_ID = C.PROP_ID AND O.SITE = C.SITE

LEFT JOIN (
  SELECT CUST_ID, SITE, N_FUNNEL, PATH, 'CF'             AS PRODUCT FROM BASE_FUNNEL_CF
  UNION ALL
  SELECT CUST_ID, SITE, N_FUNNEL, PATH, 'PPV'            AS PRODUCT FROM BASE_FUNNEL_PPV
  UNION ALL
  SELECT CUST_ID, SITE, N_FUNNEL, PATH, 'DINERO_EXPRESS' AS PRODUCT FROM BASE_FUNNEL_DE
  UNION ALL
  SELECT CUST_ID, SITE, N_FUNNEL, PATH, 'SELLER_LINE'    AS PRODUCT FROM BASE_FUNNEL_LS
) F
  ON  CAST(O.CUST_ID AS STRING) = F.CUST_ID
  AND O.SITE    = F.SITE
  AND O.PRODUCT = F.PRODUCT

LEFT JOIN VIEWS_SELLERS VS
  ON  CAST(O.CUST_ID AS STRING) = VS.user_id AND O.SITE = VS.SITE

LEFT JOIN CLICKS_SELLERS CS
  ON  CAST(O.CUST_ID AS STRING) = CS.user_id AND O.SITE = CS.SITE AND O.PRODUCT = CS.PRODUCT

LEFT JOIN `meli-bi-data.WHOWNER.LK_KYC_VAULT_USER` K
  ON  CAST(O.CUST_ID AS STRING) = CAST(K.CUS_CUST_ID AS STRING)

LEFT JOIN `meli-bi-data.WHOWNER.LK_MP_MAUS_SEGMENTATION` S
  ON  O.CUST_ID = S.CUS_CUST_ID AND O.SITE = S.SIT_SITE_ID
  AND EXTRACT(YEAR FROM O.MES_PROP) * 100 + EXTRACT(MONTH FROM O.MES_PROP) = S.TIM_MONTH_ID

LEFT JOIN `meli-bi-data.WHOWNER.LK_MP_SEGMENTATION_SELLERS` SS
  ON  S.CUS_CUST_ID = SS.CUS_CUST_ID AND S.SIT_SITE_ID = SS.SIT_SITE_ID AND S.TIM_MONTH_ID = SS.TIM_MONTH

WHERE S.CUST_TYPE_PYL = 'SELLER'
  AND SS.CUST_PRODUCT_DETAIL = 'ON NEW'

GROUP BY ALL
ORDER BY 1, 2, 3, 4, 5, 6
"""

# ── QUERY_ON: Oferta y Originaciones totales del ON ──────────────────────────
QUERY_ON = """
WITH

TDC_DE AS (
  SELECT SIT_SITE_ID,
         DATE_TRUNC(TIM_DAY, MONTH) AS FIRST_DAY,
         CCO_TC_VALUE
  FROM `meli-bi-data.WHOWNER.LK_CURRENCY_CONVERTION`
  WHERE SIT_SITE_ID IN ('MLA','MLB','MLM','MLC')
    AND TIM_DAY >= DATE '2026-01-01'
  QUALIFY ROW_NUMBER() OVER (PARTITION BY SIT_SITE_ID, DATE_TRUNC(TIM_DAY, MONTH) ORDER BY TIM_DAY DESC) = 1
),

-- Oferta largo plazo (CF, PPV, SELLER_LINE, etc.)
OFERTA_LP AS (
  SELECT
    P.SIT_SITE_ID                                                   AS SITE,
    DATE_TRUNC(CAST(P.CRD_PROP_CREATION_DATE_ID AS DATE), MONTH)    AS MES,
    P.CUS_CUST_ID_BORROWER                                          AS CUST_ID,
    CASE WHEN UPPER(P.CRD_PROP_CATEGORY) LIKE '%RENOVA%' THEN 'CF' ELSE P.CRD_CREDIT_SUBTYPE END AS CRD_SUBTYPE,
    CASE
      WHEN UPPER(P.CRD_PROP_CATEGORY) LIKE '%RENOVA%'
        THEN (P.CRD_PROP_TOTAL_AMOUNT - IFNULL(J.DEBT_BALANCE,0)) / NULLIF(TDC.CCO_TC_VALUE,0)
      ELSE P.CRD_PROP_TOTAL_AMOUNT_USD
    END AS PROP_AMT_USD
  FROM `meli-bi-data.WHOWNER.BT_MP_CREDITS_PROPOSAL_DETAIL` AS P
  LEFT JOIN `SBOX_IT_CREDITS_CREDITSTBL.MC_JARVIS_HIST` AS J
    ON  P.CUS_CUST_ID_BORROWER = J.CUS_CUST_ID_SEL
    AND DATE(J.AUD_INS_DT) >= DATE_SUB(DATE_SUB(DATE_TRUNC(P.CRD_PROP_CREATION_DATE_ID, MONTH), INTERVAL 1 DAY), INTERVAL 1 MONTH)
  LEFT JOIN `meli-bi-data.WHOWNER.LK_CURRENCY_CONVERTION` TDC
    ON  P.CRD_PROP_CREATION_DATE_ID = TDC.TIM_DAY
    AND TRIM(UPPER(P.SIT_SITE_ID)) = TRIM(UPPER(TDC.SIT_SITE_ID))
  LEFT JOIN `meli-bi-data.WHOWNER.LK_MP_MAUS_SEGMENTATION` T
    ON  T.CUS_CUST_ID = P.CUS_CUST_ID_BORROWER
    AND EXTRACT(YEAR FROM P.CRD_PROP_CREATION_DATE_ID)*100 + EXTRACT(MONTH FROM P.CRD_PROP_CREATION_DATE_ID) = T.TIM_MONTH_ID
  LEFT JOIN `meli-bi-data.WHOWNER.LK_MP_SEGMENTATION_SELLERS` AS SS
    ON  T.CUS_CUST_ID = SS.CUS_CUST_ID AND T.TIM_MONTH_ID = SS.TIM_MONTH
  WHERE P.SIT_SITE_ID IN ('MLA','MLB','MLM','MLC')
    AND P.CRD_CREDIT_SUBTYPE NOT IN ('DINERO_EXPRESS','CAR_COLLATERAL_FINANCING_B2C','CONSUMER')
    AND P.CRD_CREDIT_SUBTYPE IS NOT NULL
    AND P.FLAG_DUPLICADOS = 0
    AND DATE(J.AUD_INS_DT) <= DATE(P.CRD_PROP_CREATION_DATE_ID)
    AND P.CRD_PROP_CREATION_DATE_ID BETWEEN DATE '2026-01-21' AND CURRENT_DATE()
    AND T.CUST_TYPE_PYL = 'SELLER'
    AND SS.CUST_PRODUCT_DETAIL = 'ON NEW'
  QUALIFY ROW_NUMBER() OVER (
    PARTITION BY P.CUS_CUST_ID_BORROWER, CRD_SUBTYPE, MES
    ORDER BY P.CRD_PROP_CREATION_DATE_ID DESC, J.AUD_INS_DT DESC
  ) = 1
),

-- Oferta Dinero Express
OFERTA_DE_BASE AS (
  SELECT
    M.SIT_SITE_ID,
    M.CUS_CUST_ID,
    CAST(M.VALID_FROM_DT AS DATE) AS DATE_FROM,
    CASE
      WHEN M.CRD_PROP_STATUS IN ('CANCELLED','EXPIRED','CANCELLED-MODIF')
        THEN CAST(P.CRD_PROP_EXPIR_DATE_CORREGIDO AS DATE)
      ELSE CAST(M.VALID_TO_DT AS DATE)
    END AS DATE_TO,
    M.TOTAL_AMT / NULLIF(T.CCO_TC_VALUE, 0) AS PROP_AMT_USD
  FROM `meli-bi-data.WHOWNER.BT_VU_PROPOSAL` AS M
  LEFT JOIN `meli-bi-data.WHOWNER.BT_MP_CREDITS_PROPOSAL_DETAIL` AS P ON P.CRD_PROP_ID = M.CRD_PROP_ID
  LEFT JOIN TDC_DE T
    ON  DATE_TRUNC(CAST(M.VALID_FROM_DT AS DATE), MONTH) = T.FIRST_DAY
    AND TRIM(UPPER(M.SIT_SITE_ID)) = TRIM(UPPER(T.SIT_SITE_ID))
  WHERE M.SIT_SITE_ID IN ('MLM','MLB','MLA','MLC')
    AND M.CRD_PROD_DEF_TYPE_SK = 4
),

OFERTA_DE AS (
  SELECT
    DATE_TRUNC(LAST_DAY(C.CALENDAR_DATE, MONTH), MONTH) AS MES,
    B.SIT_SITE_ID                                        AS SITE,
    B.CUS_CUST_ID                                        AS CUST_ID,
    B.PROP_AMT_USD
  FROM OFERTA_DE_BASE B
  LEFT JOIN `meli-bi-data.WHOWNER.SYS_CALENDAR` C ON C.CALENDAR_DATE BETWEEN B.DATE_FROM AND B.DATE_TO
  LEFT JOIN `meli-bi-data.WHOWNER.LK_MP_MAUS_SEGMENTATION` MS
    ON  B.CUS_CUST_ID = MS.CUS_CUST_ID
    AND EXTRACT(YEAR FROM LAST_DAY(C.CALENDAR_DATE,MONTH))*100 + EXTRACT(MONTH FROM LAST_DAY(C.CALENDAR_DATE,MONTH)) = MS.TIM_MONTH_ID
  LEFT JOIN `meli-bi-data.WHOWNER.LK_MP_SEGMENTATION_SELLERS` SS
    ON  MS.CUS_CUST_ID = SS.CUS_CUST_ID AND MS.TIM_MONTH_ID = SS.TIM_MONTH
  WHERE C.CALENDAR_DATE BETWEEN DATE '2026-01-21' AND CURRENT_DATE()
    AND MS.CUST_TYPE_PYL = 'SELLER'
    AND SS.CUST_PRODUCT_DETAIL = 'ON NEW'
  QUALIFY ROW_NUMBER() OVER (
    PARTITION BY B.CUS_CUST_ID, DATE_TRUNC(LAST_DAY(C.CALENDAR_DATE, MONTH), MONTH)
    ORDER BY B.DATE_FROM DESC, B.DATE_TO DESC
  ) = 1
),

-- Oferta Consumer
OFERTA_CONSUMER_BASE AS (
  SELECT
    p.CUS_CUST_ID_BORROWER AS CUST_ID,
    p.SIT_SITE_ID,
    p.CRD_PROP_CREATION_DATE_ID AS PROP_DATE,
    p.CRD_PROP_TOTAL_AMOUNT_USD AS PROP_AMT_USD,
    CASE
      WHEN p.CRD_PROP_STATUS_ID IN ('CANCELLED','EXPIRED','PAUSED','PENDING','APPROVED') THEN p.CRD_PROP_EXPIR_DATE_CORREGIDO
      WHEN p.CRD_PROP_STATUS_ID = 'CLOSED' THEN CAST(p.CRD_PROP_DATE_FINISHED_ID AS DATE)
      ELSE p.CRD_PROP_EXPIR_DATE_CORREGIDO
    END AS LAST_DATE
  FROM `meli-bi-data.WHOWNER.BT_MP_CREDITS_PROPOSAL_DETAIL` AS p
  LEFT JOIN `meli-bi-data.WHOWNER.LK_MP_MAUS_SEGMENTATION` T
    ON  T.CUS_CUST_ID = p.CUS_CUST_ID_BORROWER
    AND EXTRACT(YEAR FROM p.CRD_PROP_CREATION_DATE_ID)*100 + EXTRACT(MONTH FROM p.CRD_PROP_CREATION_DATE_ID) = T.TIM_MONTH_ID
  LEFT JOIN `meli-bi-data.WHOWNER.LK_MP_SEGMENTATION_SELLERS` AS SS
    ON  T.CUS_CUST_ID = SS.CUS_CUST_ID AND T.TIM_MONTH_ID = SS.TIM_MONTH AND T.SIT_SITE_ID = SS.SIT_SITE_ID
  WHERE p.SIT_SITE_ID IN ('MLA','MLB','MLM')
    AND p.CRD_CREDIT_SUBTYPE = 'CONSUMER'
    AND T.CUST_TYPE_PYL = 'SELLER'
    AND SS.CUST_PRODUCT_DETAIL = 'ON NEW'
),

OFERTA_CONSUMER AS (
  SELECT
    DATE_TRUNC(C.CALENDAR_DATE, MONTH) AS MES,
    O.SIT_SITE_ID                      AS SITE,
    O.CUST_ID,
    O.PROP_AMT_USD
  FROM OFERTA_CONSUMER_BASE O
  LEFT JOIN `meli-bi-data.WHOWNER.SYS_CALENDAR` C ON C.CALENDAR_DATE BETWEEN O.PROP_DATE AND O.LAST_DATE
  WHERE C.CALENDAR_DATE BETWEEN DATE '2026-01-21' AND CURRENT_DATE()
  QUALIFY ROW_NUMBER() OVER (
    PARTITION BY O.CUST_ID, O.SIT_SITE_ID, DATE_TRUNC(C.CALENDAR_DATE, MONTH)
    ORDER BY O.PROP_DATE DESC
  ) = 1
),

OFERTA_ON AS (
  SELECT SITE, MES, COUNT(DISTINCT CUST_ID) AS Q_OFERTA_ON, ROUND(SUM(PROP_AMT_USD)) AS MONTO_USD_OFERTA_ON
  FROM (
    SELECT SITE, MES, CUST_ID, PROP_AMT_USD FROM OFERTA_LP
    UNION ALL
    SELECT SITE, MES, CUST_ID, PROP_AMT_USD FROM OFERTA_DE
    UNION ALL
    SELECT SITE, MES, CUST_ID, PROP_AMT_USD FROM OFERTA_CONSUMER
  )
  GROUP BY 1, 2
),

-- Originaciones Loans
ORIG_LOANS AS (
  SELECT
    DATE_TRUNC(C.CRD_CREDIT_CREATION_DATE_ID, MONTH) AS MES,
    C.SIT_SITE_ID                                     AS SITE,
    COUNT(DISTINCT C.CUS_CUST_ID_BORROWER)           AS Q,
    ROUND(SUM(
      CASE
        WHEN RC.CRD_CREDIT_ID IS NOT NULL
          THEN RC.CRD_ADDITIONAL_REQUESTED_AMT / NULLIF(TDC.CCO_TC_VALUE,0)
        ELSE C.CRD_CREDIT_AMOUNT_USD
      END
    )) AS MONTO_USD
  FROM `meli-bi-data.WHOWNER.BT_MP_CREDITS_CREDIT_DETAIL` C
  LEFT JOIN `meli-bi-data.WHOWNER.BT_CRD_MCH_RENOVA_CREDITS` RC ON RC.CRD_RENOVA_NEW_CREDIT_ID = C.CRD_CREDIT_ID
  LEFT JOIN `meli-bi-data.WHOWNER.LK_CURRENCY_CONVERTION` TDC
    ON  C.CRD_CREDIT_CREATION_DATE_ID = TDC.TIM_DAY
    AND TRIM(UPPER(RC.SIT_SITE_ID)) = TRIM(UPPER(TDC.SIT_SITE_ID))
  LEFT JOIN `meli-bi-data.WHOWNER.LK_MP_MAUS_SEGMENTATION` T
    ON  T.CUS_CUST_ID = C.CUS_CUST_ID_BORROWER
    AND T.TIM_MONTH_ID = EXTRACT(YEAR FROM C.CRD_CREDIT_CREATION_DATE_ID)*100 + EXTRACT(MONTH FROM C.CRD_CREDIT_CREATION_DATE_ID)
    AND T.SIT_SITE_ID = C.SIT_SITE_ID
  LEFT JOIN `meli-bi-data.WHOWNER.LK_MP_SEGMENTATION_SELLERS` SEL
    ON  SEL.CUS_CUST_ID = T.CUS_CUST_ID AND SEL.TIM_MONTH = T.TIM_MONTH_ID AND SEL.SIT_SITE_ID = T.SIT_SITE_ID
  WHERE C.SIT_SITE_ID IN ('MLB','MLA','MLM','MLC')
    AND C.CRD_CREDIT_STATUS_ID NOT IN ('CANCELLED','ANNULLED','PENDING')
    AND C.CRD_PRODUCT_ID NOT LIKE '%REFI%'
    AND C.CRD_CREDIT_SUBTYPE NOT IN ('CAR_COLLATERAL_FINANCING_B2C')
    AND C.CRD_CREDIT_CREATION_DATE_ID BETWEEN DATE '2026-01-21' AND CURRENT_DATE()
    AND T.CUST_TYPE_PYL = 'SELLER'
    AND SEL.CUST_PRODUCT_DETAIL = 'ON NEW'
  GROUP BY 1, 2
),

-- Originaciones Tarjeta
ORIG_TC AS (
  SELECT
    DATE_TRUNC(CAST(C.CCARD_PURCH_OP_DT AS DATE), MONTH) AS MES,
    C.SIT_SITE_ID                                         AS SITE,
    COUNT(DISTINCT C.CUS_CUST_ID)                        AS Q,
    ROUND(SUM(C.CCARD_PURCH_OP_AMT_LC / NULLIF(TDC.CCO_TC_VALUE,0))) AS MONTO_USD
  FROM `meli-bi-data.WHOWNER.BT_CCARD_PURCHASE` C
  LEFT JOIN `meli-bi-data.WHOWNER.LK_CURRENCY_CONVERTION` TDC
    ON  CAST(C.CCARD_PURCH_OP_DT AS DATE) = TDC.TIM_DAY AND UPPER(TDC.SIT_SITE_ID) = UPPER(C.SIT_SITE_ID)
  LEFT JOIN `meli-bi-data.WHOWNER.BT_CCARD_ACCOUNT` A
    ON  C.CUS_CUST_ID = A.CUS_CUST_ID AND C.SIT_SITE_ID = A.SIT_SITE_ID
  LEFT JOIN `meli-bi-data.WHOWNER.LK_MP_MAUS_SEGMENTATION` T
    ON  T.CUS_CUST_ID = A.CUS_CUST_ID
    AND CAST(T.TIM_MONTH_ID AS STRING) = CAST((EXTRACT(YEAR FROM A.CCARD_ACCOUNT_CREATION_DT)*100 + EXTRACT(MONTH FROM A.CCARD_ACCOUNT_CREATION_DT)) AS STRING)
    AND T.SIT_SITE_ID = A.SIT_SITE_ID
  LEFT JOIN `meli-bi-data.WHOWNER.LK_MP_SEGMENTATION_SELLERS` SEL
    ON  SEL.CUS_CUST_ID = T.CUS_CUST_ID AND SEL.TIM_MONTH = T.TIM_MONTH_ID AND SEL.SIT_SITE_ID = T.SIT_SITE_ID
  WHERE UPPER(C.CCARD_PURCH_OP_STATUS) IN ('PROCESSED','PENDING','NORMAL')
    AND CAST(C.CCARD_PURCH_OP_DT AS DATE) BETWEEN DATE '2026-01-21' AND CURRENT_DATE()
    AND T.CUST_TYPE_PYL = 'SELLER'
    AND SEL.CUST_PRODUCT_DETAIL = 'ON NEW'
  GROUP BY 1, 2
),

ORIG_ON AS (
  SELECT SITE, MES, SUM(Q) AS Q_ORIG_ON, SUM(MONTO_USD) AS MONTO_USD_ORIG_ON
  FROM (
    SELECT SITE, MES, Q, MONTO_USD FROM ORIG_LOANS
    UNION ALL
    SELECT SITE, MES, Q, MONTO_USD FROM ORIG_TC
  )
  GROUP BY 1, 2
)

SELECT
  COALESCE(O.SITE, R.SITE)           AS SITE,
  COALESCE(O.MES,  R.MES)            AS MES,
  COALESCE(O.Q_OFERTA_ON, 0)         AS Q_OFERTA_ON,
  COALESCE(O.MONTO_USD_OFERTA_ON, 0) AS MONTO_USD_OFERTA_ON,
  COALESCE(R.Q_ORIG_ON, 0)           AS Q_ORIG_ON,
  COALESCE(R.MONTO_USD_ORIG_ON, 0)   AS MONTO_USD_ORIG_ON
FROM OFERTA_ON O
FULL OUTER JOIN ORIG_ON R ON O.SITE = R.SITE AND O.MES = R.MES
ORDER BY 1, 2
"""

# ── 1. Correr queries en BigQuery ────────────────────────────────────────────
import sys
from decimal import Decimal
import datetime as dt
def serialize(v):
    if isinstance(v, Decimal): return float(v)
    if isinstance(v, (dt.date, dt.datetime)): return str(v)
    return v

html_only = '--html-only' in sys.argv

if html_only:
    print('Modo HTML-only: cargando desde cache...')
    with open('C:/Users/criva/bq_data.json')      as f: raw_rows = json.load(f)
    with open('C:/Users/criva/bq_vc_cache.json')  as f: vc_rows  = json.load(f)
    with open('C:/Users/criva/bq_v2_cache.json')  as f: v2_rows  = json.load(f)
    with open('C:/Users/criva/bq_on_cache.json')  as f: on_rows  = json.load(f)
    print(f'Cache OK: raw={len(raw_rows)}, vc={len(vc_rows)}, v2={len(v2_rows)}, on={len(on_rows)}')
else:
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Corriendo query en BigQuery...')
    rows_iter = bq_client.query(QUERY).result()
    raw_rows = [{k: serialize(v) for k, v in dict(row).items()} for row in rows_iter]
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Query OK: {len(raw_rows)} filas')
    with open('C:/Users/criva/bq_data.json', 'w') as f: json.dump(raw_rows, f)

    # Query Views + Clicks
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Corriendo query Views/Clicks...')
    vc_rows = [{k: serialize(v) for k, v in dict(row).items()} for row in bq_client.query(QUERY_VC).result()]
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Views/Clicks OK: {len(vc_rows)} filas')
    with open('C:/Users/criva/bq_vc_cache.json', 'w') as f: json.dump(vc_rows, f)

    # Query V2: funnel anclado al mes de oferta
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Corriendo query V2...')
    v2_rows = [{k: serialize(v) for k, v in dict(row).items()} for row in bq_client.query(QUERY_V2).result()]
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Query V2 OK: {len(v2_rows)} filas')
    with open('C:/Users/criva/bq_v2_cache.json', 'w') as f: json.dump(v2_rows, f)

    # Query ON: oferta y originaciones totales del ON
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Corriendo query ON...')
    on_rows = [{k: serialize(v) for k, v in dict(row).items()} for row in bq_client.query(QUERY_ON).result()]
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Query ON OK: {len(on_rows)} filas')
    with open('C:/Users/criva/bq_on_cache.json', 'w') as f: json.dump(on_rows, f)

# Agregar MonthName
month_map = {1:'Enero',2:'Febrero',3:'Marzo',4:'Abril',5:'Mayo',6:'Junio',
             7:'Julio',8:'Agosto',9:'Septiembre',10:'Octubre',11:'Noviembre',12:'Diciembre'}
for r in raw_rows:
    mes_str = str(r.get('MES', ''))
    r['MonthName'] = month_map.get(int(mes_str[5:7]), '?') if len(mes_str) >= 7 else '?'
for r in vc_rows:
    mes_str = str(r.get('MES', ''))
    r['MonthName'] = month_map.get(int(mes_str[5:7]), '?') if len(mes_str) >= 7 else '?'
for r in v2_rows:
    mes_str = str(r.get('MES', ''))
    r['MonthName'] = month_map.get(int(mes_str[5:7]), '?') if len(mes_str) >= 7 else '?'
for r in on_rows:
    mes_str = str(r.get('MES', ''))
    r['MonthName'] = month_map.get(int(mes_str[5:7]), '?') if len(mes_str) >= 7 else '?'

month_names = ['Todos'] + sorted(set(r['MonthName'] for r in raw_rows),
                                  key=lambda x: list(month_map.values()).index(x))

# ── 2. Actualizar Google Sheet ──────────────────────────────────────────────
# Columnas RAW_DATA:
# A=SITE  B=MES  C=PRODUCT  D=SEL_SEGMENT  E=BU  F=FUNNEL  G=N_FUNNEL_RAW  H=PATH_RAW
# I=Q_OFERTADOS  J=PROP_AMT_LC  K=PROP_AMT_USD  L=Q_ORIGINADOS  M=CRD_AMT_LC  N=CRD_AMT_USD  O=MonthName
raw_headers = ['SITE','MES','PRODUCT','SEL_SEGMENT','BU','FUNNEL','N_FUNNEL_RAW','PATH_RAW',
               'FLAG_FST_CRED','Q_OFERTADOS','PROP_AMT_LC','PROP_AMT_USD','Q_ORIGINADOS','CRD_AMT_LC','CRD_AMT_USD','MonthName']
raw_values = [raw_headers]
for r in raw_rows:
    raw_values.append([r.get(h) if r.get(h) is not None else '' for h in raw_headers])

DASH_ID = None
if not html_only:
    meta = sheets_service.spreadsheets().get(spreadsheetId=sid).execute()
    sheet_ids = {s['properties']['title']: s['properties']['sheetId'] for s in meta['sheets']}
    DASH_ID = sheet_ids['DASHBOARD']

    sheets_service.spreadsheets().values().clear(spreadsheetId=sid, range='RAW_DATA!A:Z').execute()
    sheets_service.spreadsheets().values().update(
        spreadsheetId=sid, range='RAW_DATA!A1',
        valueInputOption='USER_ENTERED', body={'values': raw_values}
    ).execute()
    print(f'[{datetime.now().strftime("%H:%M:%S")}] RAW_DATA actualizado: {len(raw_rows)} filas')

N = str(len(raw_rows) + 1)

# ── Colores Meli ─────────────────────────────────────────────────────────────
YELLOW   = {'red':1.0,  'green':0.902,'blue':0.0}
YELLOW_L = {'red':1.0,  'green':0.976,'blue':0.6}
ML_DARK  = {'red':0.267,'green':0.267,'blue':0.267}
DARK     = {'red':0.2,  'green':0.2,  'blue':0.2}
WHITE    = {'red':1.0,  'green':1.0,  'blue':1.0}
GRAY     = {'red':0.95, 'green':0.95, 'blue':0.95}
FG_W     = {'red':1.0,  'green':1.0,  'blue':1.0}
FG_B     = {'red':0.2,  'green':0.2,  'blue':0.2}
FG_Y     = {'red':1.0,  'green':0.902,'blue':0.0}

def cv(val, bold=False, bg=None, fg=None, size=10, italic=False, formula=False):
    uev = {'formulaValue': str(val)} if formula else \
          ({'numberValue': float(val)} if isinstance(val,(int,float)) else {'stringValue': str(val)})
    fmt = {'textFormat':{'bold':bold,'fontSize':size,'italic':italic},
           'verticalAlignment':'MIDDLE','wrapStrategy':'CLIP'}
    if bg: fmt['backgroundColor'] = bg
    if fg: fmt['textFormat']['foregroundColor'] = fg
    return {'userEnteredValue': uev, 'userEnteredFormat': fmt}

def e(bg=None):
    c = {'userEnteredValue':{'stringValue':''}}
    if bg: c['userEnteredFormat'] = {'backgroundColor':bg}
    return c

def hdr(txt): return cv(txt, bold=True, bg=ML_DARK, fg=FG_W)

# ── Helpers SUMPRODUCT ───────────────────────────────────────────────────────
# Filters: C3=Site, C4=Mes
def mf():
    return f'IF($C$4="Todos";1;RAW_DATA!$O$2:$O${N}=$C$4)'
def sf_dyn():
    return f'IF($C$3="Todos";1;RAW_DATA!$A$2:$A${N}=$C$3)'
def sf(site):
    return f'(RAW_DATA!$A$2:$A${N}="{site}")'
def pf(prod):
    return f'(RAW_DATA!$C$2:$C${N}="{prod}")'

def sp2(col, f1, f2):
    return f'=SUMPRODUCT({f1}*{f2}*RAW_DATA!${col}$2:${col}${N})'
def sp3(col, f1, f2, f3):
    return f'=SUMPRODUCT({f1}*{f2}*{f3}*RAW_DATA!${col}$2:${col}${N})'

def cvr(f1, f2, f3='1'):
    num = f'SUMPRODUCT({f1}*{f2}*{f3}*RAW_DATA!$L$2:$L${N})'
    den = f'SUMPRODUCT({f1}*{f2}*{f3}*RAW_DATA!$I$2:$I${N})'
    return f'=IFERROR(ROUND({num}/{den}*100;2);0)'

# ── Armar filas del DASHBOARD ────────────────────────────────────────────────
rows_data = []
PRODUCTS = [('CF','CF'), ('PPV','PPV'), ('DINERO_EXPRESS','Dinero Express'), ('SELLER_LINE','Seller Line')]
SITES = ['MLA','MLB','MLC','MLM']

# Título
rows_data.append({'values':[e(DARK),cv('🟡',bg=DARK),
    cv('Card Summary - Performance Dashboard',bold=True,bg=DARK,fg=FG_Y,size=14),
    e(DARK),e(DARK),e(DARK),e(DARK),e(DARK)]})
rows_data.append({'values':[e()]})
rows_data.append({'values':[e(),cv('Site',bold=True,bg=YELLOW,fg=FG_B),cv('Todos',bg=WHITE)]})
rows_data.append({'values':[e(),cv('Mes', bold=True,bg=YELLOW,fg=FG_B),cv('Todos',bg=WHITE)]})
rows_data.append({'values':[e()]})

# ── Sección 1: Resumen General ───────────────────────────────────────────────
rows_data.append({'values':[e(),cv('Resumen General',bold=True,size=11,fg=DARK)]})
rows_data.append({'values':[e(ML_DARK),hdr(''),hdr('Q Ofertados'),hdr('Q Originados'),hdr('CVR %'),hdr('USD Propuesto'),hdr('USD Originado')]})
rows_data.append({'values':[e(YELLOW_L),cv('Total',bold=True,bg=YELLOW_L,fg=DARK),
    cv(sp2('I',sf_dyn(),mf()),bg=YELLOW_L,bold=True,formula=True),
    cv(sp2('L',sf_dyn(),mf()),bg=YELLOW_L,bold=True,formula=True),
    cv(cvr(sf_dyn(),mf()),bg=YELLOW_L,bold=True,formula=True),
    cv(sp2('K',sf_dyn(),mf()),bg=YELLOW_L,bold=True,formula=True),
    cv(sp2('N',sf_dyn(),mf()),bg=YELLOW_L,bold=True,formula=True)]})
rows_data.append({'values':[e()]})

# ── Sección 2: Por Producto ──────────────────────────────────────────────────
rows_data.append({'values':[e(),cv('Por Producto',bold=True,size=11,fg=DARK)]})
rows_data.append({'values':[e(ML_DARK),hdr('Producto'),hdr('Q Ofertados'),hdr('Q Originados'),hdr('CVR %'),hdr('USD Propuesto'),hdr('USD Originado')]})
for i,(prod_key, prod_label) in enumerate(PRODUCTS):
    bg = WHITE if i%2==0 else GRAY
    rows_data.append({'values':[e(bg),cv(prod_label,bold=True,bg=bg,fg=DARK),
        cv(sp3('I',sf_dyn(),mf(),pf(prod_key)),bg=bg,formula=True),
        cv(sp3('L',sf_dyn(),mf(),pf(prod_key)),bg=bg,formula=True),
        cv(cvr(sf_dyn(),mf(),pf(prod_key)),bg=bg,formula=True),
        cv(sp3('K',sf_dyn(),mf(),pf(prod_key)),bg=bg,formula=True),
        cv(sp3('N',sf_dyn(),mf(),pf(prod_key)),bg=bg,formula=True)]})
rows_data.append({'values':[e(YELLOW_L),cv('Total',bold=True,bg=YELLOW_L,fg=DARK),
    cv(sp2('I',sf_dyn(),mf()),bg=YELLOW_L,bold=True,formula=True),
    cv(sp2('L',sf_dyn(),mf()),bg=YELLOW_L,bold=True,formula=True),
    cv(cvr(sf_dyn(),mf()),bg=YELLOW_L,bold=True,formula=True),
    cv(sp2('K',sf_dyn(),mf()),bg=YELLOW_L,bold=True,formula=True),
    cv(sp2('N',sf_dyn(),mf()),bg=YELLOW_L,bold=True,formula=True)]})
rows_data.append({'values':[e()]})

# ── Sección 3: Por Site ──────────────────────────────────────────────────────
rows_data.append({'values':[e(),cv('Por Site',bold=True,size=11,fg=DARK)]})
rows_data.append({'values':[e(ML_DARK),hdr('Site'),hdr('Q Ofertados'),hdr('Q Originados'),hdr('CVR %'),hdr('USD Propuesto'),hdr('USD Originado')]})
for i,site in enumerate(SITES):
    bg = WHITE if i%2==0 else GRAY
    rows_data.append({'values':[e(bg),cv(site,bold=True,bg=bg,fg=DARK),
        cv(sp2('I',sf(site),mf()),bg=bg,formula=True),
        cv(sp2('L',sf(site),mf()),bg=bg,formula=True),
        cv(cvr(sf(site),mf()),bg=bg,formula=True),
        cv(sp2('K',sf(site),mf()),bg=bg,formula=True),
        cv(sp2('N',sf(site),mf()),bg=bg,formula=True)]})
rows_data.append({'values':[e(YELLOW_L),cv('Total',bold=True,bg=YELLOW_L,fg=DARK),
    cv(sp2('I',sf_dyn(),mf()),bg=YELLOW_L,bold=True,formula=True),
    cv(sp2('L',sf_dyn(),mf()),bg=YELLOW_L,bold=True,formula=True),
    cv(cvr(sf_dyn(),mf()),bg=YELLOW_L,bold=True,formula=True),
    cv(sp2('K',sf_dyn(),mf()),bg=YELLOW_L,bold=True,formula=True),
    cv(sp2('N',sf_dyn(),mf()),bg=YELLOW_L,bold=True,formula=True)]})
rows_data.append({'values':[e()]})

# Timestamp
rows_data.append({'values':[e(),cv(f'Última actualización: {datetime.now().strftime("%Y-%m-%d %H:%M")}',
    italic=True,fg={'red':0.4,'green':0.4,'blue':0.4})]})

# ── Formateo de números ──────────────────────────────────────────────────────
def nfmt(pattern, start_r, end_r, start_c, end_c):
    return {'repeatCell':{
        'range':{'sheetId':DASH_ID,'startRowIndex':start_r,'endRowIndex':end_r,
                 'startColumnIndex':start_c,'endColumnIndex':end_c},
        'cell':{'userEnteredFormat':{'numberFormat':{'type':'NUMBER','pattern':pattern}}},
        'fields':'userEnteredFormat.numberFormat'}}

# Row offsets (0-indexed): Resumen=row7(idx6), Producto starts row11(idx10), Site starts row18(idx17)
RESUMEN_R = 7  # row index of the "Total" resumen row
PROD_START = 11
PROD_END   = PROD_START + len(PRODUCTS) + 1
SITE_START = PROD_END + 4
SITE_END   = SITE_START + len(SITES) + 1

requests = [
    {'updateCells':{'range':{'sheetId':DASH_ID},'fields':'userEnteredValue,userEnteredFormat'}},
    {'updateCells':{'rows':rows_data,'fields':'userEnteredValue,userEnteredFormat',
                    'start':{'sheetId':DASH_ID,'rowIndex':0,'columnIndex':0}}},
    {'updateSheetProperties':{'properties':{'sheetId':DASH_ID,'gridProperties':{'frozenRowCount':1}},
                              'fields':'gridProperties.frozenRowCount'}},
    {'updateDimensionProperties':{'range':{'sheetId':DASH_ID,'dimension':'COLUMNS','startIndex':0,'endIndex':1},
                                  'properties':{'pixelSize':18},'fields':'pixelSize'}},
    {'updateDimensionProperties':{'range':{'sheetId':DASH_ID,'dimension':'COLUMNS','startIndex':1,'endIndex':2},
                                  'properties':{'pixelSize':200},'fields':'pixelSize'}},
    {'updateDimensionProperties':{'range':{'sheetId':DASH_ID,'dimension':'COLUMNS','startIndex':2,'endIndex':8},
                                  'properties':{'pixelSize':150},'fields':'pixelSize'}},
    {'updateDimensionProperties':{'range':{'sheetId':DASH_ID,'dimension':'ROWS','startIndex':0,'endIndex':40},
                                  'properties':{'pixelSize':24},'fields':'pixelSize'}},
    {'setDataValidation':{'range':{'sheetId':DASH_ID,'startRowIndex':2,'endRowIndex':3,'startColumnIndex':2,'endColumnIndex':3},
        'rule':{'condition':{'type':'ONE_OF_LIST','values':[{'userEnteredValue':v} for v in ['Todos','MLA','MLB','MLC','MLM']]},
                'showCustomUi':True,'strict':True}}},
    {'setDataValidation':{'range':{'sheetId':DASH_ID,'startRowIndex':3,'endRowIndex':4,'startColumnIndex':2,'endColumnIndex':3},
        'rule':{'condition':{'type':'ONE_OF_LIST','values':[{'userEnteredValue':v} for v in month_names]},
                'showCustomUi':True,'strict':True}}},
    # Números: Q = #,##0 / USD = $#,##0 / CVR = 0.00
    nfmt('#,##0',    RESUMEN_R, RESUMEN_R+1, 2, 4),
    nfmt('$#,##0',   RESUMEN_R, RESUMEN_R+1, 5, 7),
    nfmt('#,##0',    PROD_START, PROD_END,   2, 4),
    nfmt('0.00"%"',  PROD_START, PROD_END,   4, 5),
    nfmt('$#,##0',   PROD_START, PROD_END,   5, 7),
    nfmt('#,##0',    SITE_START, SITE_END,   2, 4),
    nfmt('0.00"%"',  SITE_START, SITE_END,   4, 5),
    nfmt('$#,##0',   SITE_START, SITE_END,   5, 7),
]

if not html_only:
    sheets_service.spreadsheets().batchUpdate(spreadsheetId=sid, body={'requests':requests}).execute()
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Dashboard actualizado OK')
    print('URL: https://docs.google.com/spreadsheets/d/' + sid)

# ── 3. Generar HTML dashboard ───────────────────────────────────────────────
updated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
html_data  = json.dumps(raw_rows)
vc_data    = json.dumps(vc_rows)

html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Card Summary - Performance Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{ font-family:'Segoe UI',system-ui,sans-serif; background:#f0f2f5; color:#333; font-size:14px; }}

  /* ─ Header ─ */
  header {{ background:#1a1a2e; color:#FFE600; padding:18px 32px; display:flex; align-items:center; justify-content:space-between; box-shadow:0 2px 8px rgba(0,0,0,.25); }}
  header h1 {{ font-size:20px; font-weight:700; letter-spacing:.5px; }}
  .meta {{ text-align:right; }}
  .meta .updated {{ font-size:11px; color:#aaa; }}
  .meta .badge {{ font-size:10px; background:#FFE600; color:#1a1a2e; border-radius:4px; padding:2px 7px; font-weight:700; letter-spacing:.4px; margin-top:4px; display:inline-block; }}

  /* ─ Filters ─ */
  .filters {{ background:#fff; padding:12px 32px; display:flex; gap:20px; align-items:center; flex-wrap:wrap; border-bottom:3px solid #FFE600; box-shadow:0 2px 4px rgba(0,0,0,.05); }}
  .filter-group {{ display:flex; align-items:center; gap:8px; }}
  .filters label {{ font-weight:700; font-size:11px; color:#777; text-transform:uppercase; letter-spacing:.5px; }}
  .filters select {{ padding:7px 12px; border:1.5px solid #e0e0e0; border-radius:8px; font-size:13px; cursor:pointer; background:#fafafa; min-width:140px; }}
  .filters select:focus {{ outline:none; border-color:#FFE600; }}

  /* ─ KPIs ─ */
  .kpis {{ display:grid; grid-template-columns:repeat(6,1fr); gap:12px; padding:20px 32px 8px; }}
  .kpi {{ background:#fff; border-radius:10px; padding:16px 18px; box-shadow:0 1px 4px rgba(0,0,0,.07); border-top:3px solid #FFE600; }}
  .kpi.hi {{ border-top-color:#1a1a2e; background:#1a1a2e; }}
  .kpi .label {{ font-size:10px; color:#aaa; text-transform:uppercase; letter-spacing:.6px; margin-bottom:6px; font-weight:600; }}
  .kpi.hi .label {{ color:#666; }}
  .kpi .value {{ font-size:22px; font-weight:700; color:#1a1a2e; line-height:1.1; }}
  .kpi.hi .value {{ color:#FFE600; }}
  .kpi .sub {{ font-size:10px; color:#bbb; margin-top:4px; }}
  .kpi.hi .sub {{ color:#555; }}

  /* ─ Insights bar ─ */
  .insights-bar {{ display:flex; gap:10px; padding:6px 32px 16px; flex-wrap:wrap; }}
  .chip {{ background:#fff; border-radius:8px; padding:7px 13px; font-size:12px; box-shadow:0 1px 3px rgba(0,0,0,.07); border-left:3px solid #FFE600; color:#666; }}
  .chip strong {{ color:#1a1a2e; }}

  /* ─ Section header ─ */
  .sec {{ padding:18px 32px 8px; display:flex; align-items:baseline; gap:10px; }}
  .sec h2 {{ font-size:12px; font-weight:700; color:#1a1a2e; text-transform:uppercase; letter-spacing:.7px; }}
  .sec span {{ font-size:11px; color:#bbb; }}

  /* ─ Funnel ─ */
  .funnel-section {{ background:#f0f2f5; padding:0 32px 28px; }}
  .funnel-section .sec {{ padding:18px 0 12px; }}

  /* TOTAL card — full width, 2-column layout */
  .funnel-total {{ background:#fff; border-radius:14px; padding:22px 28px; box-shadow:0 2px 8px rgba(0,0,0,.10); border-top:4px solid #1a1a2e; display:grid; grid-template-columns:1fr 1fr 1fr; gap:0; margin-bottom:16px; }}
  .ft-step {{ padding:14px 20px; border-right:1px solid #f2f2f2; }}
  .ft-step:last-child {{ border-right:none; }}
  .ft-label {{ font-size:10px; color:#aaa; text-transform:uppercase; letter-spacing:.6px; font-weight:600; margin-bottom:6px; }}
  .ft-value {{ font-size:26px; font-weight:800; color:#1a1a2e; line-height:1.1; }}
  .ft-sub {{ font-size:10px; color:#bbb; margin-top:3px; }}
  .ft-sub b {{ color:#888; }}
  .ft-bar-bg {{ height:4px; background:#f0f2f5; border-radius:2px; margin-top:8px; }}
  .ft-bar {{ height:4px; border-radius:2px; background:#1a1a2e; transition:width .5s; }}
  .total-label {{ grid-column:1/-1; padding:14px 20px 10px; border-bottom:1px solid #f2f2f2; margin-bottom:0; display:flex; align-items:center; gap:10px; }}
  .total-label h3 {{ font-size:15px; font-weight:800; text-transform:uppercase; letter-spacing:1px; color:#1a1a2e; }}
  .total-label span {{ font-size:11px; color:#aaa; }}

  /* Product funnel cards */
  .funnel-grid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:14px; }}
  .funnel-card {{ background:#fff; border-radius:12px; padding:18px 20px; box-shadow:0 1px 5px rgba(0,0,0,.07); }}
  .funnel-card.single {{ max-width:460px; margin:0 auto; }}
  .fc-title {{ font-size:12px; font-weight:800; letter-spacing:1.2px; text-transform:uppercase; margin-bottom:4px; }}
  .fc-line {{ height:3px; border-radius:2px; margin-bottom:14px; }}
  .f-step {{ margin-bottom:12px; }}
  .f-step-header {{ display:flex; justify-content:space-between; align-items:baseline; margin-bottom:3px; }}
  .f-step-label {{ font-size:12px; color:#999; font-weight:500; }}
  .f-step-value {{ font-size:18px; font-weight:700; }}
  .f-bar-bg {{ height:4px; background:#f0f2f5; border-radius:2px; margin-bottom:3px; }}
  .f-bar {{ height:4px; border-radius:2px; transition:width .5s ease; }}
  .f-pct {{ font-size:10px; color:#ccc; }}
  .f-pct b {{ color:#999; font-weight:600; }}

  /* ─ Charts ─ */
  .charts {{ display:grid; grid-template-columns:1fr 1fr; gap:14px; padding:0 32px 16px; }}
  .chart-card {{ background:#fff; border-radius:12px; padding:18px 20px; box-shadow:0 1px 4px rgba(0,0,0,.07); }}
  .chart-card h3 {{ font-size:10px; font-weight:700; color:#aaa; margin-bottom:14px; text-transform:uppercase; letter-spacing:.7px; }}

  /* ─ Table ─ */
  .tbl-wrap {{ padding:0 32px 40px; overflow-x:auto; }}
  table {{ width:100%; border-collapse:collapse; background:#fff; border-radius:12px; overflow:hidden; box-shadow:0 1px 4px rgba(0,0,0,.07); font-size:12px; }}
  thead th {{ background:#1a1a2e; color:#FFE600; padding:10px 12px; text-align:left; font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:.5px; white-space:nowrap; }}
  tbody td {{ padding:9px 12px; border-bottom:1px solid #f2f2f2; white-space:nowrap; }}
  tbody tr:nth-child(even) td {{ background:#fafbfc; }}
  tbody tr.total-row td {{ background:#fffde7; font-weight:700; border-top:2px solid #FFE600; }}
  tbody tr:hover:not(.total-row) td {{ background:#fff9e6; }}
  .tag {{ display:inline-block; padding:2px 7px; border-radius:4px; font-size:11px; font-weight:700; }}

  footer {{ text-align:center; padding:14px; font-size:11px; color:#bbb; background:#f0f2f5; }}
  @media(max-width:1100px) {{ .kpis{{ grid-template-columns:repeat(3,1fr); }} .funnel-grid{{ grid-template-columns:repeat(2,1fr); }} .funnel-total{{ grid-template-columns:repeat(2,1fr); }} }}
  @media(max-width:750px) {{ .kpis{{ grid-template-columns:repeat(2,1fr); }} .funnel-grid{{ grid-template-columns:1fr; }} .charts{{ grid-template-columns:1fr; }} }}
</style>
</head>
<body>

<header>
  <h1>&#9679; Card Summary &mdash; Performance Dashboard</h1>
  <div class="meta">
    <div class="updated">Última actualización: {updated_at}</div>
    <div class="badge">AUTO-REFRESH DIARIO</div>
  </div>
</header>

<div class="filters">
  <div class="filter-group">
    <label>Site</label>
    <select id="fSite" onchange="render()">
      <option value="Todos">Todos los sites</option>
      <option>MLA</option><option>MLB</option><option>MLC</option><option>MLM</option>
    </select>
  </div>
  <div class="filter-group">
    <label>Mes</label>
    <select id="fMes" onchange="render()"></select>
  </div>
  <div class="filter-group">
    <label>Producto</label>
    <select id="fProduct" onchange="render()">
      <option value="Todos">Todos los productos</option>
      <option value="CF">Cuota Fija</option>
      <option value="PPV">PPV</option>
      <option value="DINERO_EXPRESS">Dinero Express</option>
      <option value="SELLER_LINE">Seller Line</option>
    </select>
  </div>
</div>

<div id="kpis" class="kpis"></div>
<div id="insightsBar" class="insights-bar"></div>

<!-- Funnel -->
<div class="funnel-section">
  <div class="sec">
    <h2>Funnel de Adquisicion</h2>
    <span>Oferta &rarr; Views &rarr; Clicks &rarr; Simulador &rarr; R&amp;C &rarr; Congrats</span>
  </div>
  <div id="funnelContainer"></div>
</div>

<!-- Charts row 1 -->
<div class="charts">
  <div class="chart-card"><h3>Evolucion mensual de originaciones</h3><canvas id="chartTrend"></canvas></div>
  <div class="chart-card"><h3>CVR por etapa del funnel (% sobre Ofertados)</h3><canvas id="chartFunnelCVR"></canvas></div>
</div>
<!-- Charts row 2 -->
<div class="charts">
  <div class="chart-card"><h3>Ofertados vs Originados por Site</h3><canvas id="chartSite"></canvas></div>
  <div class="chart-card"><h3>Mix de Originaciones</h3><canvas id="chartMix"></canvas></div>
</div>

<!-- Table -->
<div class="sec"><h2>Detalle por Site &times; Producto</h2><span>Todas las etapas del funnel</span></div>
<div class="tbl-wrap">
  <table>
    <thead><tr>
      <th>Site</th><th>Producto</th><th>Ofertados</th><th>Views</th><th>Clicks</th>
      <th>Simulador+</th><th>R&amp;C+</th><th>Originados</th>
      <th>CVR %</th><th>USD Prop</th><th>USD Orig</th><th>Ticket USD</th>
    </tr></thead>
    <tbody id="tableBody"></tbody>
  </table>
</div>

<footer>Card Summary Performance Dashboard &mdash; Mercado Credito &mdash; Auto-refresh diario</footer>

<script>
const RAW  = {html_data};
const VC   = {vc_data};
const MONTH_ORDER = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'];
const SITES    = ['MLA','MLB','MLC','MLM'];
const PRODUCTS = ['CF','PPV','DINERO_EXPRESS','SELLER_LINE'];
const PLBL = {{'CF':'Cuota Fija','PPV':'PPV','DINERO_EXPRESS':'Dinero Express','SELLER_LINE':'Seller Line'}};
const PCLR = {{'CF':'#FFE600','PPV':'#00C9FF','DINERO_EXPRESS':'#FF6B6B','SELLER_LINE':'#A78BFA'}};
const PCLR2= {{'CF':'#9a7c00','PPV':'#006f8f','DINERO_EXPRESS':'#8f1f1f','SELLER_LINE':'#5a3daf'}};

const STEPS = [
  {{label:'Oferta',   min:null    }},
  {{label:'Views',    min:'views' }},
  {{label:'Clicks',   min:'clicks'}},
  {{label:'Simulador',min:2       }},
  {{label:'R&C',      min:4       }},
  {{label:'Congrats', min:'orig'  }},
];

// populate month filter
const months=[...new Set(RAW.map(r=>r.MonthName))].sort((a,b)=>MONTH_ORDER.indexOf(a)-MONTH_ORDER.indexOf(b));
const selMes=document.getElementById('fMes');
[{{value:'Todos',text:'Todos los meses'}},...months.map(m=>{{return{{value:m,text:m}}}})].forEach(o=>{{
  const el=document.createElement('option'); el.value=o.value; el.text=o.text; selMes.appendChild(el);
}});

let CH={{}};

function gf(){{
  return {{
    site:    document.getElementById('fSite').value,
    mes:     document.getElementById('fMes').value,
    product: document.getElementById('fProduct').value,
  }};
}}

function flt(rows,f,noProd){{
  return rows.filter(r=>
    (f.site==='Todos'    || r.SITE===f.site) &&
    (f.mes==='Todos'     || r.MonthName===f.mes) &&
    (noProd || f.product==='Todos' || r.PRODUCT===f.product)
  );
}}

function fltVC(rows,f){{
  return rows.filter(r=>
    (f.site==='Todos' || r.SITE===f.site) &&
    (f.mes==='Todos'  || r.MonthName===f.mes) &&
    (f.product==='Todos' || r.PRODUCT===f.product)
  );
}}

function agg(rows){{
  const d={{off:0,orig:0,up:0,uo:0}};
  rows.forEach(r=>{{d.off+=+r.Q_OFERTADOS||0; d.orig+=+r.Q_ORIGINADOS||0; d.up+=+r.PROP_AMT_USD||0; d.uo+=+r.CRD_AMT_USD||0;}});
  d.cvr   = d.off >0 ? +(d.orig/d.off*100).toFixed(2) : 0;
  d.ticket= d.orig>0 ? +(d.uo/d.orig).toFixed(0)       : 0;
  return d;
}}

function stepVal(pR,pV,s){{
  if(s.min===null)    return pR.reduce((a,r)=>a+(+r.Q_OFERTADOS||0),0);
  if(s.min==='orig')  return pR.reduce((a,r)=>a+(+r.Q_ORIGINADOS||0),0);
  if(s.min==='clicks')return pV.reduce((a,r)=>a+(+r.Q_CLICKS||0),0);
  if(s.min==='views') return pV.reduce((a,r)=>a+(+r.Q_VIEWS||0),0);
  return pR.filter(r=>r.N_FUNNEL_RAW!==null&&r.N_FUNNEL_RAW!==''&&+r.N_FUNNEL_RAW>=s.min)
           .reduce((a,r)=>a+(+r.Q_OFERTADOS||0),0);
}}

function stepValTotal(rows,vc,s){{
  if(s.min===null)    return rows.reduce((a,r)=>a+(+r.Q_OFERTADOS||0),0);
  if(s.min==='orig')  return rows.reduce((a,r)=>a+(+r.Q_ORIGINADOS||0),0);
  if(s.min==='clicks')return vc.reduce((a,r)=>a+(+r.Q_CLICKS||0),0);
  if(s.min==='views'){{
    const seen=new Set(); let t=0;
    vc.forEach(r=>{{const k=r.SITE+'_'+r.MES; if(!seen.has(k)){{seen.add(k);t+=+r.Q_VIEWS_ALL||0;}}}});
    return t;
  }}
  return rows.filter(r=>r.N_FUNNEL_RAW!==null&&r.N_FUNNEL_RAW!==''&&+r.N_FUNNEL_RAW>=s.min)
             .reduce((a,r)=>a+(+r.Q_OFERTADOS||0),0);
}}

function fmtK(n){{n=+n||0; if(n>=1e6)return(n/1e6).toFixed(1)+'M'; if(n>=1e3)return(n/1e3).toFixed(1)+'K'; return n.toLocaleString('es-AR');}}
function fmt(n)   {{return(+n||0).toLocaleString('es-AR');}}
function fmtU(n)  {{return'$'+(+n||0).toLocaleString('es-AR',{{maximumFractionDigits:0}});}}
function pct(a,b) {{return b>0?(a/b*100).toFixed(1):'0.0';}}

function mkCh(id,type,labels,datasets,opts={{}}){{
  if(CH[id])CH[id].destroy();
  const ctx=document.getElementById(id); if(!ctx)return;
  CH[id]=new Chart(ctx,{{type,data:{{labels,datasets}},options:{{responsive:true,plugins:{{legend:{{position:'bottom',labels:{{font:{{size:11}}}}}}}}, ...opts}}}});
}}

function buildFunnelCard(color,title,vals,isTotal){{
  const top=vals[0]||1;
  let stHtml='';
  STEPS.forEach((s,i)=>{{
    const v=vals[i];
    const bw=Math.min(100,Math.round(v/top*100));
    const pt=pct(v,top);
    const pp=i>0&&vals[i-1]>0?pct(v,vals[i-1]):null;
    const sub=i===0?'100% del total':`${{pt}}% de Oferta${{pp?' &middot; <b>'+pp+'%</b> prev':''}}`;
    stHtml+=`<div class="f-step">
      <div class="f-step-header"><span class="f-step-label">${{s.label}}</span><span class="f-step-value" style="color:${{color}}">${{fmtK(v)}}</span></div>
      <div class="f-bar-bg"><div class="f-bar" style="width:${{bw}}%;background:${{color}}"></div></div>
      <div class="f-pct">${{sub}}</div>
    </div>`;
  }});
  if(isTotal){{
    const top2=vals[0]||1;
    return `<div class="funnel-total">
      <div class="total-label"><h3>Total</h3><span>Todos los productos &mdash; views deduplicadas por site/mes</span></div>
      ${{STEPS.map((s,i)=>{{
        const v=vals[i]; const bw=Math.min(100,Math.round(v/top2*100));
        const pt=pct(v,top2); const pp=i>0&&vals[i-1]>0?pct(v,vals[i-1]):null;
        return`<div class="ft-step">
          <div class="ft-label">${{s.label}}</div>
          <div class="ft-value">${{fmtK(v)}}</div>
          <div class="ft-sub">${{i===0?'base':pt+'% de Oferta'}}${{pp?' &middot; <b>'+pp+'%</b> prev':''}}</div>
          <div class="ft-bar-bg"><div class="ft-bar" style="width:${{bw}}%"></div></div>
        </div>`;
      }}).join('')}}
    </div>`;
  }}
  return `<div class="funnel-card">
    <div class="fc-title" style="color:${{color}}">${{title}}</div>
    <div class="fc-line"  style="background:${{color}}"></div>
    ${{stHtml}}
  </div>`;
}}

function renderFunnel(rows,vc,prod){{
  let html='';
  if(prod==='Todos'){{
    const tv=STEPS.map(s=>stepValTotal(rows,vc,s));
    html+=buildFunnelCard('#1a1a2e','Total',tv,true);
    let grid='';
    PRODUCTS.forEach(p=>{{
      const pR=rows.filter(r=>r.PRODUCT===p); const pV=vc.filter(r=>r.PRODUCT===p);
      if(!pR.length&&!pV.length)return;
      grid+=buildFunnelCard(PCLR[p],PLBL[p],STEPS.map(s=>stepVal(pR,pV,s)),false);
    }});
    html+=`<div class="funnel-grid">${{grid}}</div>`;
  }} else {{
    const pR=rows.filter(r=>r.PRODUCT===prod); const pV=vc.filter(r=>r.PRODUCT===prod);
    html=`<div class="funnel-grid" style="justify-items:center">${{buildFunnelCard(PCLR[prod],PLBL[prod],STEPS.map(s=>stepVal(pR,pV,s)),false).replace('funnel-card"','funnel-card single"')}}</div>`;
  }}
  document.getElementById('funnelContainer').innerHTML=html;
}}

function renderInsights(rows,vc){{
  const chips=[];
  // top site CVR
  let ts='',tcvr=-1;
  SITES.forEach(s=>{{const d=agg(rows.filter(r=>r.SITE===s)); if(d.cvr>tcvr){{tcvr=d.cvr;ts=s;}}}});
  if(ts) chips.push(`<div class="chip">&#127942; Mayor CVR: <strong>${{ts}} (${{tcvr}}%)</strong></div>`);
  // top product orig
  let tp='',to=-1;
  PRODUCTS.forEach(p=>{{const d=agg(rows.filter(r=>r.PRODUCT===p)); if(d.orig>to){{to=d.orig;tp=p;}}}});
  if(tp) chips.push(`<div class="chip">&#128230; Producto lider: <strong>${{PLBL[tp]}} (${{fmtK(to)}} orig)</strong></div>`);
  // biggest funnel drop
  const tv=STEPS.map(s=>stepValTotal(rows,vc,s));
  let md=0,ds='';
  for(let i=1;i<tv.length;i++){{if(tv[i-1]>0){{const d=100-tv[i]/tv[i-1]*100;if(d>md){{md=d;ds=STEPS[i].label;}}}}}}
  if(ds) chips.push(`<div class="chip">&#128201; Mayor caida: <strong>&rarr;${{ds}} (${{md.toFixed(0)}}% drop)</strong></div>`);
  // total USD
  const tot=agg(rows);
  chips.push(`<div class="chip">&#128176; USD Originado total: <strong>${{fmtU(tot.uo)}}</strong></div>`);
  document.getElementById('insightsBar').innerHTML=chips.join('');
}}

function render(){{
  const f=gf();
  const rows=flt(RAW,f,false);
  const vc  =fltVC(VC,f);
  const tot =agg(rows);

  // views total (dedup if todos)
  let vTot=0;
  if(f.product==='Todos'){{const seen=new Set(); vc.forEach(r=>{{const k=r.SITE+'_'+r.MES; if(!seen.has(k)){{seen.add(k);vTot+=+r.Q_VIEWS_ALL||0;}}}});}}
  else vTot=vc.reduce((a,r)=>a+(+r.Q_VIEWS||0),0);
  const cTot=vc.reduce((a,r)=>a+(+r.Q_CLICKS||0),0);

  // KPIs
  document.getElementById('kpis').innerHTML=[
    ['Ofertados',  fmtK(tot.off),  'Usuarios con oferta activa',   false],
    ['Views',      fmtK(vTot),     'Vieron card en Seller Central', false],
    ['Clicks',     fmtK(cTot),     'Hicieron click en card',        false],
    ['Originados', fmtK(tot.orig), 'Creditos otorgados',            true ],
    ['CVR %',      tot.cvr+'%',    'Originados / Ofertados',        true ],
    ['Ticket USD', fmtU(tot.ticket),'Monto promedio por credito',   false],
  ].map(([l,v,s,hi])=>`<div class="kpi${{hi?' hi':''}}"><div class="label">${{l}}</div><div class="value">${{v}}</div><div class="sub">${{s}}</div></div>`).join('');

  // Insights
  renderInsights(rows,vc);

  // Funnel
  renderFunnel(rows,vc,f.product);

  // Chart trend: originaciones por mes por producto
  const tRows=flt(RAW,{{...f,mes:'Todos'}},false);
  const tMonths=[...new Set(tRows.map(r=>r.MonthName))].sort((a,b)=>MONTH_ORDER.indexOf(a)-MONTH_ORDER.indexOf(b));
  const tProds=f.product==='Todos'?PRODUCTS:[f.product];
  mkCh('chartTrend','line',tMonths,tProds.map(p=>{{
    const d=tMonths.map(m=>agg(tRows.filter(r=>r.PRODUCT===p&&r.MonthName===m)).orig);
    return {{label:PLBL[p],data:d,borderColor:PCLR[p],backgroundColor:PCLR[p]+'44',fill:true,tension:.3,pointRadius:5}};
  }}),{{scales:{{y:{{beginAtZero:true,title:{{display:true,text:'Originados'}}}}}},plugins:{{tooltip:{{callbacks:{{label:ctx=>ctx.dataset.label+': '+fmt(ctx.parsed.y)}}}}}}}});

  // Chart funnel CVR: cada step como % de ofertados, por producto
  const sLabels=STEPS.slice(1).map(s=>s.label);
  const cProds=f.product==='Todos'?PRODUCTS:[f.product];
  mkCh('chartFunnelCVR','bar',sLabels,cProds.map(p=>{{
    const pR=rows.filter(r=>r.PRODUCT===p); const pV=vc.filter(r=>r.PRODUCT===p);
    const base=stepVal(pR,pV,STEPS[0])||1;
    return {{label:PLBL[p],data:STEPS.slice(1).map(s=>+(stepVal(pR,pV,s)/base*100).toFixed(1)),
             backgroundColor:PCLR[p]+'BB',borderColor:PCLR[p],borderWidth:1.5}};
  }}),{{scales:{{y:{{beginAtZero:true,title:{{display:true,text:'% de Ofertados'}}}}}},
    plugins:{{tooltip:{{callbacks:{{label:ctx=>ctx.dataset.label+': '+ctx.parsed.y+'%'}}}}}}}});

  // Chart site bar
  const siteD=SITES.map(s=>agg(rows.filter(r=>r.SITE===s)));
  mkCh('chartSite','bar',SITES,[
    {{label:'Ofertados', data:siteD.map(d=>d.off), backgroundColor:'#d0d5dd'}},
    {{label:'Originados',data:siteD.map(d=>d.orig),backgroundColor:'#FFE600'}},
  ],{{scales:{{y:{{beginAtZero:true}}}},plugins:{{tooltip:{{callbacks:{{label:ctx=>ctx.dataset.label+': '+fmt(ctx.parsed.y)}}}}}}}});

  // Chart mix doughnut
  const mProds=f.product==='Todos'?PRODUCTS:[f.product];
  const mData=mProds.map(p=>agg(rows.filter(r=>r.PRODUCT===p)).orig);
  mkCh('chartMix','doughnut',mProds.map(p=>PLBL[p]),[
    {{data:mData,backgroundColor:mProds.map(p=>PCLR[p]),borderWidth:2}}
  ]);

  // Table
  const tProdsT=f.product==='Todos'?PRODUCTS:[f.product];
  let tbody='';
  SITES.forEach(site=>{{
    tProdsT.forEach(prod=>{{
      const d=agg(rows.filter(r=>r.SITE===site&&r.PRODUCT===prod));
      if(d.off===0&&d.orig===0)return;
      const pV=vc.filter(r=>r.SITE===site&&r.PRODUCT===prod);
      const vws=pV.reduce((a,r)=>a+(+r.Q_VIEWS||0),0);
      const clk=pV.reduce((a,r)=>a+(+r.Q_CLICKS||0),0);
      const pR=rows.filter(r=>r.SITE===site&&r.PRODUCT===prod);
      const sim=pR.filter(r=>r.N_FUNNEL_RAW!==null&&r.N_FUNNEL_RAW!==''&&+r.N_FUNNEL_RAW>=2).reduce((a,r)=>a+(+r.Q_OFERTADOS||0),0);
      const ryc=pR.filter(r=>r.N_FUNNEL_RAW!==null&&r.N_FUNNEL_RAW!==''&&+r.N_FUNNEL_RAW>=4).reduce((a,r)=>a+(+r.Q_OFERTADOS||0),0);
      tbody+=`<tr>
        <td><b>${{site}}</b></td>
        <td><span class="tag" style="background:${{PCLR[prod]}}33;color:${{PCLR2[prod]}}">${{PLBL[prod]}}</span></td>
        <td>${{fmt(d.off)}}</td><td>${{fmt(vws)}}</td><td>${{fmt(clk)}}</td>
        <td>${{fmt(sim)}}</td><td>${{fmt(ryc)}}</td><td><b>${{fmt(d.orig)}}</b></td>
        <td><b>${{d.cvr}}%</b></td><td>${{fmtU(d.up)}}</td><td>${{fmtU(d.uo)}}</td><td>${{fmtU(d.ticket)}}</td>
      </tr>`;
    }});
  }});
  const simT=rows.filter(r=>r.N_FUNNEL_RAW!==null&&r.N_FUNNEL_RAW!==''&&+r.N_FUNNEL_RAW>=2).reduce((a,r)=>a+(+r.Q_OFERTADOS||0),0);
  const rycT=rows.filter(r=>r.N_FUNNEL_RAW!==null&&r.N_FUNNEL_RAW!==''&&+r.N_FUNNEL_RAW>=4).reduce((a,r)=>a+(+r.Q_OFERTADOS||0),0);
  tbody+=`<tr class="total-row"><td>TOTAL</td><td>&mdash;</td>
    <td>${{fmt(tot.off)}}</td><td>${{fmt(vTot)}}</td><td>${{fmt(cTot)}}</td>
    <td>${{fmt(simT)}}</td><td>${{fmt(rycT)}}</td><td>${{fmt(tot.orig)}}</td>
    <td>${{tot.cvr}}%</td><td>${{fmtU(tot.up)}}</td><td>${{fmtU(tot.uo)}}</td><td>${{fmtU(tot.ticket)}}</td>
  </tr>`;
  document.getElementById('tableBody').innerHTML=tbody;
}}

render();
</script>
</body>
</html>"""

with open('C:/Users/criva/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)
print(f'[{datetime.now().strftime("%H:%M:%S")}] HTML generado: C:/Users/criva/dashboard.html')

# ── 3b. Generar Originations Dashboard ───────────────────────────────────────
orig_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Card Summary · Originations</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{ font-family:'Segoe UI',system-ui,sans-serif; background:#f0f2f5; color:#333; font-size:14px; }}
  header {{ background:#1a1a2e; color:#FFE600; padding:18px 32px; display:flex; align-items:center; justify-content:space-between; box-shadow:0 2px 8px rgba(0,0,0,.25); }}
  header h1 {{ font-size:20px; font-weight:700; letter-spacing:.5px; }}
  header a {{ font-size:12px; color:#FFE600; opacity:.7; text-decoration:none; }}
  header a:hover {{ opacity:1; }}
  .meta {{ text-align:right; }}
  .meta .updated {{ font-size:11px; color:#aaa; }}
  .meta .badge {{ font-size:10px; background:#FFE600; color:#1a1a2e; border-radius:4px; padding:2px 7px; font-weight:700; margin-top:4px; display:inline-block; }}
  .filters {{ background:#fff; padding:12px 32px; display:flex; gap:20px; align-items:center; flex-wrap:wrap; border-bottom:3px solid #FFE600; box-shadow:0 2px 4px rgba(0,0,0,.05); }}
  .filter-group {{ display:flex; align-items:center; gap:8px; }}
  .filters label {{ font-weight:700; font-size:11px; color:#777; text-transform:uppercase; letter-spacing:.5px; }}
  .filters select {{ padding:7px 12px; border:1.5px solid #e0e0e0; border-radius:8px; font-size:13px; cursor:pointer; background:#fafafa; min-width:130px; }}
  .filters select:focus {{ outline:none; border-color:#FFE600; }}
  .kpis {{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; padding:20px 32px 8px; }}
  .kpi {{ background:#fff; border-radius:10px; padding:16px 20px; box-shadow:0 1px 4px rgba(0,0,0,.07); border-top:3px solid #FFE600; }}
  .kpi.hi {{ border-top-color:#1a1a2e; background:#1a1a2e; }}
  .kpi .label {{ font-size:10px; color:#aaa; text-transform:uppercase; letter-spacing:.6px; margin-bottom:6px; font-weight:600; }}
  .kpi.hi .label {{ color:#666; }}
  .kpi .value {{ font-size:26px; font-weight:700; color:#1a1a2e; line-height:1.1; }}
  .kpi.hi .value {{ color:#FFE600; }}
  .kpi .sub {{ font-size:11px; color:#bbb; margin-top:4px; }}
  .sec {{ padding:20px 32px 10px; display:flex; align-items:baseline; gap:10px; }}
  .sec h2 {{ font-size:12px; font-weight:700; color:#1a1a2e; text-transform:uppercase; letter-spacing:.7px; }}
  .charts-row {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; padding:0 32px 24px; }}
  .chart-card {{ background:#fff; border-radius:12px; padding:22px 24px; box-shadow:0 1px 6px rgba(0,0,0,.07); }}
  .chart-card h3 {{ font-size:11px; font-weight:700; color:#1a1a2e; text-transform:uppercase; letter-spacing:.6px; margin-bottom:16px; }}
  .new-old-row {{ display:flex; flex-direction:column; gap:14px; }}
  .no-bar {{ display:flex; align-items:center; gap:12px; }}
  .no-label {{ font-size:12px; font-weight:700; width:50px; flex-shrink:0; }}
  .no-label.new {{ color:#1a1a2e; }}
  .no-label.old {{ color:#aaa; }}
  .no-track {{ flex:1; background:#f0f2f5; border-radius:4px; height:24px; overflow:hidden; }}
  .no-fill {{ height:100%; border-radius:4px; display:flex; align-items:center; padding-left:8px; font-size:11px; font-weight:700; transition:width .6s; }}
  .no-fill.new {{ background:#1a1a2e; color:#FFE600; }}
  .no-fill.old {{ background:#FFE600; color:#1a1a2e; }}
  .no-meta {{ font-size:11px; color:#aaa; width:80px; text-align:right; flex-shrink:0; }}
  .lift-badge {{ margin-top:16px; background:#f0f2f5; border-radius:8px; padding:12px 16px; display:flex; justify-content:space-between; align-items:center; }}
  .lift-badge .lbl {{ font-size:11px; color:#888; }}
  .lift-badge .val {{ font-size:18px; font-weight:700; color:#1a1a2e; }}
  .donut-wrap {{ position:relative; max-width:200px; margin:0 auto 16px; }}
  .prod-legend {{ display:flex; flex-direction:column; gap:8px; }}
  .prod-row {{ display:flex; align-items:center; gap:10px; }}
  .prod-dot {{ width:10px; height:10px; border-radius:50%; flex-shrink:0; }}
  .prod-name {{ font-size:12px; flex:1; }}
  .prod-pct {{ font-size:12px; font-weight:700; color:#1a1a2e; }}
  .prod-usd {{ font-size:11px; color:#aaa; }}
  .funnel-section {{ padding:0 32px 32px; }}
  .funnel-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:12px; }}
  .funnel-card {{ background:#fff; border-radius:12px; padding:20px; box-shadow:0 1px 6px rgba(0,0,0,.07); border-top:3px solid #FFE600; }}
  .funnel-card h4 {{ font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.5px; color:#888; margin-bottom:14px; }}
  .f-step {{ display:flex; justify-content:space-between; align-items:center; padding:7px 0; border-bottom:1px solid #f5f5f5; }}
  .f-step:last-child {{ border-bottom:none; }}
  .f-step-lbl {{ font-size:12px; color:#555; }}
  .f-step-val {{ font-size:13px; font-weight:700; color:#1a1a2e; }}
  .f-step-pct {{ font-size:10px; color:#aaa; margin-left:4px; }}
</style>
</head>
<body>
<header>
  <div>
    <h1>Card Summary &middot; Originations Analytics</h1>
    <a href="index.html">← Volver al funnel</a>
  </div>
  <div class="meta">
    <div class="updated">Actualizado: {updated_at}</div>
    <div class="badge">BU = ON · Card Summary</div>
  </div>
</header>

<div class="filters">
  <div class="filter-group"><label>Site</label>
    <select id="fSite" onchange="render()"><option>Todos</option>
      <option>MLA</option><option>MLB</option><option>MLC</option><option>MLM</option>
    </select></div>
  <div class="filter-group"><label>Mes</label>
    <select id="fMes" onchange="render()">
      {''.join(f'<option>{m}</option>' for m in month_names)}
    </select></div>
  <div class="filter-group"><label>Producto</label>
    <select id="fProd" onchange="render()"><option>Todos</option>
      <option>CF</option><option>PPV</option><option>DINERO_EXPRESS</option><option>SELLER_LINE</option>
    </select></div>
</div>

<div class="kpis" id="kpis"></div>

<div class="sec"><h2>New vs Old Users</h2><span>Originaciones por tipo de usuario</span></div>
<div class="charts-row">
  <div class="chart-card">
    <h3>New vs Old Originadores</h3>
    <div class="new-old-row" id="newOldBars"></div>
    <div class="lift-badge"><span class="lbl">% New Users sobre total originados</span><span class="val" id="pctNew">—</span></div>
  </div>
  <div class="chart-card">
    <h3>Split USD por Producto</h3>
    <div class="donut-wrap"><canvas id="donutChart" height="200"></canvas></div>
    <div class="prod-legend" id="prodLegend"></div>
  </div>
</div>

<div class="sec"><h2>Funnel Card Summary</h2><span>Por producto seleccionado</span></div>
<div class="funnel-section">
  <div class="funnel-grid" id="funnelGrid"></div>
</div>

<script>
const RAW = {json.dumps(raw_rows)};
const VC  = {json.dumps(vc_rows)};
const PROD_COLORS = {{'CF':'#1a1a2e','PPV':'#FFE600','DINERO_EXPRESS':'#FF6B35','SELLER_LINE':'#4CAF50'}};
const PROD_LABELS = {{'CF':'CF','PPV':'PPV','DINERO_EXPRESS':'Dinero Express','SELLER_LINE':'Seller Line'}};
const PRODUCTS = ['CF','PPV','DINERO_EXPRESS','SELLER_LINE'];
const FUNNEL_STEPS = [
  {{lbl:'Oferta',   min:null}},
  {{lbl:'Views',    min:'views'}},
  {{lbl:'Clicks',   min:'clicks'}},
  {{lbl:'Simulador',min:2}},
  {{lbl:'R&C',      min:4}},
  {{lbl:'Congrats', min:'orig'}}
];

function gf() {{
  return {{
    site: document.getElementById('fSite').value,
    mes:  document.getElementById('fMes').value,
    prod: document.getElementById('fProd').value
  }};
}}
function flt(rows, f) {{
  return rows.filter(r =>
    (f.site==='Todos' || r.SITE===f.site) &&
    (f.mes==='Todos'  || r.MonthName===f.mes) &&
    (f.prod==='Todos' || r.PRODUCT===f.prod)
  );
}}
function fltVC(vc, f) {{
  return vc.filter(r =>
    (f.site==='Todos' || r.SITE===f.site) &&
    (f.mes==='Todos'  || r.MonthName===f.mes) &&
    (f.prod==='Todos' || r.PRODUCT===f.prod)
  );
}}
function fmtK(n) {{ n=+n||0; if(n>=1e6)return(n/1e6).toFixed(1)+'M'; if(n>=1e3)return(n/1e3).toFixed(1)+'K'; return n.toLocaleString('es-AR'); }}
function fmtU(n)  {{ return '$'+(+n||0).toLocaleString('es-AR',{{maximumFractionDigits:0}}); }}
function pct(a,b) {{ return b>0?(a/b*100).toFixed(1):'0.0'; }}

function stepVal(rows, vc, s) {{
  if(s.min===null)    return rows.reduce((a,r)=>a+(+r.Q_OFERTADOS||0),0);
  if(s.min==='orig')  return rows.reduce((a,r)=>a+(+r.Q_ORIGINADOS||0),0);
  if(s.min==='clicks')return vc.reduce((a,r)=>a+(+r.Q_CLICKS||0),0);
  if(s.min==='views') {{
    const seen=new Set(); let t=0;
    vc.forEach(r=>{{const k=r.SITE+'_'+r.MES; if(!seen.has(k)){{seen.add(k);t+=+r.Q_VIEWS_ALL||0;}}}});
    return t;
  }}
  return rows.filter(r=>r.N_FUNNEL_RAW!==null&&r.N_FUNNEL_RAW!==''&&+r.N_FUNNEL_RAW>=s.min)
             .reduce((a,r)=>a+(+r.Q_OFERTADOS||0),0);
}}

let donutInst = null;

function render() {{
  const f = gf();
  const rows = flt(RAW, f);
  const vc   = fltVC(VC, f);

  const off  = rows.reduce((a,r)=>a+(+r.Q_OFERTADOS||0),0);
  const orig = rows.reduce((a,r)=>a+(+r.Q_ORIGINADOS||0),0);
  const usd  = rows.reduce((a,r)=>a+(+r.CRD_AMT_USD||0),0);
  const ticket = orig>0 ? usd/orig : 0;

  // KPIs
  document.getElementById('kpis').innerHTML = [
    ['Q Orig Totales', fmtK(orig),  'Originaciones atribuidas Card Summary', true],
    ['CVR Orig / ON',  pct(orig,off)+'%', 'Originados sobre total ofertados BU=ON', false],
    ['USD Total Orig', fmtU(usd),   'Monto total originado en USD', false],
    ['Ticket Prom',    fmtU(ticket),'USD promedio por originación', false],
  ].map(([lbl,val,sub,hi])=>`<div class="kpi${{hi?' hi':''}}">
    <div class="label">${{lbl}}</div>
    <div class="value">${{val}}</div>
    <div class="sub">${{sub}}</div>
  </div>`).join('');

  // New vs Old
  const newOrig = rows.filter(r=>+r.FLAG_FST_CRED===1).reduce((a,r)=>a+(+r.Q_ORIGINADOS||0),0);
  const oldOrig = rows.filter(r=>+r.FLAG_FST_CRED===0).reduce((a,r)=>a+(+r.Q_ORIGINADOS||0),0);
  const total   = newOrig + oldOrig || 1;
  const pNew = (newOrig/total*100).toFixed(1);
  const pOld = (oldOrig/total*100).toFixed(1);

  document.getElementById('newOldBars').innerHTML = `
    <div class="no-bar">
      <span class="no-label new">New</span>
      <div class="no-track"><div class="no-fill new" style="width:${{pNew}}%">${{fmtK(newOrig)}}</div></div>
      <span class="no-meta">${{pNew}}%</span>
    </div>
    <div class="no-bar">
      <span class="no-label old">Old</span>
      <div class="no-track"><div class="no-fill old" style="width:${{pOld}}%">${{fmtK(oldOrig)}}</div></div>
      <span class="no-meta">${{pOld}}%</span>
    </div>`;
  document.getElementById('pctNew').textContent = pNew + '%';

  // Donut USD por producto
  const prodUSD = {{}};
  PRODUCTS.forEach(p => {{
    prodUSD[p] = rows.filter(r=>r.PRODUCT===p).reduce((a,r)=>a+(+r.CRD_AMT_USD||0),0);
  }});
  const totalUSD = Object.values(prodUSD).reduce((a,v)=>a+v,0)||1;
  const dLabels = PRODUCTS.map(p=>PROD_LABELS[p]);
  const dData   = PRODUCTS.map(p=>prodUSD[p]);
  const dColors = PRODUCTS.map(p=>PROD_COLORS[p]);

  if(donutInst) donutInst.destroy();
  donutInst = new Chart(document.getElementById('donutChart'), {{
    type:'doughnut',
    data:{{ labels:dLabels, datasets:[{{data:dData, backgroundColor:dColors, borderWidth:2, borderColor:'#fff'}}] }},
    options:{{ plugins:{{legend:{{display:false}}}}, cutout:'65%' }}
  }});

  document.getElementById('prodLegend').innerHTML = PRODUCTS.map(p => {{
    const u = prodUSD[p];
    return `<div class="prod-row">
      <div class="prod-dot" style="background:${{PROD_COLORS[p]}}"></div>
      <span class="prod-name">${{PROD_LABELS[p]}}</span>
      <span class="prod-pct">${{pct(u,totalUSD)}}%</span>
      <span class="prod-usd">${{fmtU(u)}}</span>
    </div>`;
  }}).join('');

  // Funnel por producto (o total)
  const prods = f.prod==='Todos' ? PRODUCTS : [f.prod];
  document.getElementById('funnelGrid').innerHTML = prods.map(p => {{
    const pRows = rows.filter(r=>r.PRODUCT===p);
    const pVC   = vc.filter(r=>r.PRODUCT===p);
    const steps = FUNNEL_STEPS.map(s => {{
      let v;
      if(s.min==='views') {{
        const seen=new Set(); let t=0;
        pVC.forEach(r=>{{const k=r.SITE+'_'+r.MES; if(!seen.has(k)){{seen.add(k);t+=+r.Q_VIEWS_ALL||0;}}}});
        v=t;
      }} else {{
        v = stepVal(pRows, pVC, s);
      }}
      return {{lbl:s.lbl, val:v}};
    }});
    const base = steps[0].val || 1;
    return `<div class="funnel-card">
      <h4>${{PROD_LABELS[p]}}</h4>
      ${{steps.map((s,i) => `
        <div class="f-step">
          <span class="f-step-lbl">${{s.lbl}}</span>
          <span>
            <span class="f-step-val">${{fmtK(s.val)}}</span>
            <span class="f-step-pct">${{i===0?'100%':pct(s.val,base)+'%'}}</span>
          </span>
        </div>`).join('')}}
    </div>`;
  }}).join('');
}}

render();
</script>
</body>
</html>"""

with open('C:/Users/criva/originations.html', 'w', encoding='utf-8') as f:
    f.write(orig_html)
print(f'[{datetime.now().strftime("%H:%M:%S")}] HTML generado: C:/Users/criva/originations.html')

# ── 3c. Generar Dashboard V2 (funnel anclado al mes de oferta) ────────────────
v2_month_names = ['Todos'] + sorted(set(r['MonthName'] for r in v2_rows),
                                    key=lambda x: list(month_map.values()).index(x))
v2_data = json.dumps(v2_rows)
on_data = json.dumps(on_rows)

html_v2 = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Card Summary · Funnel V2</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{ font-family:'Segoe UI',system-ui,sans-serif; background:#f0f2f5; color:#333; font-size:14px; }}
  header {{ background:#1a1a2e; color:#FFE600; padding:18px 32px; display:flex; align-items:center; justify-content:space-between; box-shadow:0 2px 8px rgba(0,0,0,.25); }}
  header h1 {{ font-size:20px; font-weight:700; letter-spacing:.5px; }}
  .meta {{ text-align:right; }}
  .meta .updated {{ font-size:11px; color:#aaa; }}
  .meta .badge {{ background:#FFE600; color:#1a1a2e; border-radius:4px; padding:2px 7px; font-size:10px; font-weight:700; margin-top:4px; display:inline-block; }}
  .meta .badge2 {{ background:#4CAF50; color:#fff; border-radius:4px; padding:2px 7px; font-size:10px; font-weight:700; margin-top:4px; margin-left:4px; display:inline-block; }}
  .nav-link {{ font-size:12px; color:#FFE600; opacity:.7; text-decoration:none; margin-left:16px; }}
  .nav-link:hover {{ opacity:1; }}
  .filters {{ background:#fff; padding:12px 32px; display:flex; gap:20px; align-items:center; flex-wrap:wrap; border-bottom:3px solid #FFE600; box-shadow:0 2px 4px rgba(0,0,0,.05); }}
  .filter-group {{ display:flex; align-items:center; gap:8px; }}
  .filters label {{ font-weight:700; font-size:11px; color:#777; text-transform:uppercase; letter-spacing:.5px; }}
  .filters select {{ padding:7px 12px; border:1.5px solid #e0e0e0; border-radius:8px; font-size:13px; cursor:pointer; background:#fafafa; min-width:140px; }}
  .filters select:focus {{ outline:none; border-color:#FFE600; }}
  .kpis {{ display:grid; grid-template-columns:repeat(6,1fr); gap:12px; padding:20px 32px 8px; }}
  .kpi {{ background:#fff; border-radius:10px; padding:16px 18px; box-shadow:0 1px 4px rgba(0,0,0,.07); border-top:3px solid #FFE600; }}
  .kpi.hi {{ border-top-color:#1a1a2e; background:#1a1a2e; }}
  .kpi .label {{ font-size:10px; color:#aaa; text-transform:uppercase; letter-spacing:.6px; margin-bottom:6px; font-weight:600; }}
  .kpi.hi .label {{ color:#666; }}
  .kpi .value {{ font-size:22px; font-weight:700; color:#1a1a2e; line-height:1.1; }}
  .kpi.hi .value {{ color:#FFE600; }}
  .kpi .sub {{ font-size:10px; color:#bbb; margin-top:4px; }}
  .kpi.hi .sub {{ color:#555; }}
  .insights-bar {{ display:flex; gap:10px; padding:6px 32px 16px; flex-wrap:wrap; }}
  .chip {{ background:#fff; border-radius:8px; padding:7px 13px; font-size:12px; box-shadow:0 1px 3px rgba(0,0,0,.07); border-left:3px solid #FFE600; color:#666; }}
  .chip strong {{ color:#1a1a2e; }}
  .sec {{ padding:18px 32px 8px; display:flex; align-items:baseline; gap:10px; }}
  .sec h2 {{ font-size:12px; font-weight:700; color:#1a1a2e; text-transform:uppercase; letter-spacing:.7px; }}
  .sec span {{ font-size:11px; color:#bbb; }}
  .funnel-section {{ background:#f0f2f5; padding:0 32px 28px; }}
  .funnel-section .sec {{ padding:18px 0 12px; }}
  .funnel-total {{ background:#fff; border-radius:14px; padding:22px 28px; box-shadow:0 2px 8px rgba(0,0,0,.10); border-top:4px solid #1a1a2e; display:grid; grid-template-columns:repeat(6,1fr); gap:0; margin-bottom:16px; }}
  .ft-step {{ padding:14px 16px; border-right:1px solid #f2f2f2; }}
  .ft-step:last-child {{ border-right:none; }}
  .ft-label {{ font-size:10px; color:#aaa; text-transform:uppercase; letter-spacing:.6px; font-weight:600; margin-bottom:6px; }}
  .ft-value {{ font-size:24px; font-weight:800; color:#1a1a2e; line-height:1.1; }}
  .ft-sub {{ font-size:10px; color:#bbb; margin-top:3px; }}
  .ft-bar-bg {{ height:4px; background:#f0f2f5; border-radius:2px; margin-top:8px; }}
  .ft-bar {{ height:4px; border-radius:2px; background:#1a1a2e; }}
  .funnel-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:12px; }}
  .funnel-card {{ background:#fff; border-radius:12px; padding:20px; box-shadow:0 1px 6px rgba(0,0,0,.08); }}
  .fc-title {{ font-size:13px; font-weight:700; margin-bottom:6px; }}
  .fc-line {{ height:3px; border-radius:2px; margin-bottom:14px; }}
  .f-step {{ padding:8px 0; border-bottom:1px solid #f5f5f5; }}
  .f-step:last-child {{ border-bottom:none; }}
  .f-step-header {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:4px; }}
  .f-step-label {{ font-size:12px; color:#555; }}
  .f-step-value {{ font-size:13px; font-weight:700; }}
  .f-bar-bg {{ height:3px; background:#f0f2f5; border-radius:2px; }}
  .f-bar {{ height:3px; border-radius:2px; }}
  .f-pct {{ font-size:10px; color:#aaa; margin-top:2px; }}
  .funnel-card.single {{ max-width:320px; margin:0 auto; }}
  .charts-row {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; padding:0 32px 24px; }}
  .chart-card {{ background:#fff; border-radius:12px; padding:22px 24px; box-shadow:0 1px 4px rgba(0,0,0,.07); }}
  .chart-card h3 {{ font-size:11px; font-weight:700; color:#888; text-transform:uppercase; letter-spacing:.6px; margin-bottom:16px; }}
  .tbl-wrap {{ overflow-x:auto; padding:0 32px 32px; }}
  table {{ width:100%; border-collapse:collapse; background:#fff; border-radius:10px; overflow:hidden; box-shadow:0 1px 4px rgba(0,0,0,.07); font-size:13px; }}
  th {{ background:#1a1a2e; color:#FFE600; padding:10px 12px; text-align:left; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.5px; white-space:nowrap; }}
  td {{ padding:9px 12px; border-bottom:1px solid #f0f2f5; }}
  tr:hover td {{ background:#fffde7; }}
  .total-row td {{ background:#f9f9f9; font-weight:700; border-top:2px solid #FFE600; }}
  .tag {{ border-radius:4px; padding:2px 7px; font-size:11px; font-weight:600; }}
  footer {{ text-align:center; padding:20px; font-size:11px; color:#bbb; }}
  .penet-section {{ padding:0 32px 8px; }}
  .penet-grid {{ display:grid; grid-template-columns:repeat(5,1fr); gap:12px; margin-top:8px; }}
  .penet-card {{ background:#fff; border-radius:10px; padding:16px 18px; box-shadow:0 1px 4px rgba(0,0,0,.07); border-left:4px solid #FFE600; }}
  .penet-card.green {{ border-left-color:#4CAF50; }}
  .penet-card.blue  {{ border-left-color:#2196F3; }}
  .penet-label {{ font-size:11px; color:#777; text-transform:uppercase; letter-spacing:.4px; margin-bottom:6px; }}
  .penet-pct {{ font-size:26px; font-weight:800; color:#1a1a2e; }}
  .penet-detail {{ font-size:11px; color:#aaa; margin-top:4px; }}
  .filters select:disabled {{ background:#f0f0f0; color:#aaa; cursor:default; opacity:.6; }}
</style>
</head>
<body>
<header>
  <div>
    <h1>Card Summary &middot; Funnel V2</h1>
    <a href="index.html" class="nav-link">← Dashboard original</a>
    <a href="originations.html" class="nav-link">Originations →</a>
  </div>
  <div class="meta">
    <div class="updated">Actualizado: {updated_at}</div>
    <div class="badge">BU = ON</div>
    <div class="badge2">Funnel anclado al mes de oferta</div>
  </div>
</header>

<div class="filters">
  <div class="filter-group"><label>Site</label>
    <select id="fSite" onchange="render()">
      <option value="Todos">Todos los sites</option>
      <option>MLA</option><option>MLB</option><option>MLC</option><option>MLM</option>
    </select></div>
  <div class="filter-group"><label>Mes de Oferta</label>
    <select id="fMes" onchange="render()"></select></div>
  <div class="filter-group"><label>Producto</label>
    <select id="fProduct" onchange="render()">
      <option value="Todos">Todos</option>
      <option>CF</option><option>PPV</option><option>DINERO_EXPRESS</option><option>SELLER_LINE</option>
    </select></div>
  <div class="filter-group"><label>Segmento</label>
    <select id="fSeg" onchange="render()">
      <option value="Todos">Todos</option>
    </select></div>
  <div class="filter-group"><label>Tipo de Entidad</label>
    <select id="fEnt" onchange="render()">
      <option value="Todos">Todos</option>
      <option value="PF">PF</option>
      <option value="PJ">PJ</option>
    </select></div>
  <div class="filter-group"><label>Unidad</label>
    <select id="fUnit" onchange="onUnitChange()">
      <option value="Q">Cantidad</option>
      <option value="M">Monto</option>
    </select></div>
  <div class="filter-group"><label>Moneda</label>
    <select id="fCurr" onchange="render()" disabled>
      <option value="USD">USD</option>
      <option value="LC">Moneda Local</option>
    </select></div>
</div>

<div class="kpis" id="kpis"></div>
<div class="insights-bar" id="insightsBar"></div>

<div class="penet-section">
  <div class="sec"><h2>Penetración Card sobre ON</h2><span>La Card como % del universo ON total</span></div>
  <div class="penet-grid" id="penetGrid"></div>
</div>

<div class="funnel-section">
  <div class="sec"><h2>Funnel</h2><span>Cada paso es subconjunto de ofertados ese mes</span></div>
  <div id="funnelContainer"></div>
</div>

<div class="charts-row">
  <div class="chart-card"><h3>Tendencia Originaciones</h3><canvas id="chartTrend" height="160"></canvas></div>
  <div class="chart-card"><h3>CVR por etapa</h3><canvas id="chartFunnelCVR" height="160"></canvas></div>
</div>
<div class="charts-row">
  <div class="chart-card"><h3>Ofertados vs Originados por Site</h3><canvas id="chartSite" height="160"></canvas></div>
  <div class="chart-card"><h3>Mix Originaciones por Producto</h3><canvas id="chartMix" height="160"></canvas></div>
</div>

<div class="sec"><h2>Detalle por Site &times; Producto</h2></div>
<div class="tbl-wrap">
  <table>
    <thead><tr>
      <th>Site</th><th>Producto</th><th>Ofertados</th><th>Views</th><th>Clicks</th>
      <th>Simulador+</th><th>R&amp;C+</th><th>Originados</th>
      <th>CVR %</th><th id="thProp">Prop USD</th><th id="thOrig">Orig USD</th><th id="thTkt">Ticket USD</th>
    </tr></thead>
    <tbody id="tableBody"></tbody>
  </table>
</div>

<footer>Card Summary · Funnel V2 &mdash; Cada paso anclado al mes de oferta del seller</footer>

<script>
const RAW  = {v2_data};
const ON   = {on_data};
const MONTH_ORDER = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'];
const SITES    = ['MLA','MLB','MLC','MLM'];
const PRODUCTS = ['CF','PPV','DINERO_EXPRESS','SELLER_LINE'];
const PLBL = {{'CF':'Cuota Fija','PPV':'PPV','DINERO_EXPRESS':'Dinero Express','SELLER_LINE':'Seller Line'}};
const PCLR = {{'CF':'#FFE600','PPV':'#00C9FF','DINERO_EXPRESS':'#FF6B6B','SELLER_LINE':'#A78BFA'}};
const PCLR2= {{'CF':'#9a7c00','PPV':'#006f8f','DINERO_EXPRESS':'#8f1f1f','SELLER_LINE':'#5a3daf'}};

const STEPS = [
  {{label:'Oferta',   min:null    }},
  {{label:'Views',    min:'views' }},
  {{label:'Clicks',   min:'clicks'}},
  {{label:'Simulador',min:2       }},
  {{label:'R&C',      min:4       }},
  {{label:'Congrats', min:'orig'  }},
];

const months=[...new Set(RAW.map(r=>r.MonthName))].sort((a,b)=>MONTH_ORDER.indexOf(a)-MONTH_ORDER.indexOf(b));
const selMes=document.getElementById('fMes');
[{{value:'Todos',text:'Todos los meses'}},...months.map(m=>{{return{{value:m,text:m}}}})].forEach(o=>{{
  const el=document.createElement('option'); el.value=o.value; el.text=o.text; selMes.appendChild(el);
}});

// Populate Segmento dynamically
const segs=[...new Set(RAW.map(r=>r.SEL_SEGMENT).filter(s=>s&&s!=='null'&&s!==null))].sort();
const selSeg=document.getElementById('fSeg');
segs.forEach(s=>{{ const el=document.createElement('option'); el.value=s; el.text=s.replace(/^\\d\\./,''); selSeg.appendChild(el); }});

let CH={{}};

function onUnitChange(){{
  const isM=document.getElementById('fUnit').value==='M';
  document.getElementById('fCurr').disabled=!isM;
  render();
}}

function gf(){{
  return {{
    site:    document.getElementById('fSite').value,
    mes:     document.getElementById('fMes').value,
    product: document.getElementById('fProduct').value,
    seg:     document.getElementById('fSeg').value,
    ent:     document.getElementById('fEnt').value,
    unit:    document.getElementById('fUnit').value,
    curr:    document.getElementById('fCurr').value,
  }};
}}

function flt(rows,f,noProd){{
  return rows.filter(r=>
    (f.site==='Todos'    || r.SITE===f.site) &&
    (f.mes==='Todos'     || r.MonthName===f.mes) &&
    (noProd || f.product==='Todos' || r.PRODUCT===f.product) &&
    (f.seg==='Todos'     || r.SEL_SEGMENT===f.seg) &&
    (f.ent==='Todos'     || (f.ent==='PF'&&r.KYC_ENTITY_TYPE==='person') || (f.ent==='PJ'&&r.KYC_ENTITY_TYPE==='company'))
  );
}}

function agg(rows){{
  const d={{off:0,orig:0,up:0,uo:0,uplc:0,uolc:0}};
  rows.forEach(r=>{{
    d.off  +=+r.Q_OFERTADOS ||0; d.orig+=+r.Q_ORIGINADOS||0;
    d.up   +=+r.PROP_AMT_USD||0; d.uo  +=+r.CRD_AMT_USD ||0;
    d.uplc +=+r.PROP_AMT_LC ||0; d.uolc+=+r.CRD_AMT_LC  ||0;
  }});
  d.cvr      = d.off >0 ? +(d.orig/d.off *100).toFixed(2) : 0;
  d.ticket   = d.orig>0 ? +(d.uo  /d.orig    ).toFixed(0) : 0;
  d.ticketlc = d.orig>0 ? +(d.uolc/d.orig    ).toFixed(0) : 0;
  return d;
}}

function stepVal(pR,s){{
  if(s.min===null)     return pR.reduce((a,r)=>a+(+r.Q_OFERTADOS||0),0);
  if(s.min==='orig')   return pR.reduce((a,r)=>a+(+r.Q_ORIGINADOS||0),0);
  if(s.min==='clicks') return pR.reduce((a,r)=>a+(+r.Q_CLICKS||0),0);
  if(s.min==='views')  return pR.reduce((a,r)=>a+(+r.Q_VIEWS||0),0);
  return pR.filter(r=>r.N_FUNNEL_RAW!==null&&r.N_FUNNEL_RAW!==''&&+r.N_FUNNEL_RAW>=s.min)
           .reduce((a,r)=>a+(+r.Q_OFERTADOS||0),0);
}}

function fmtK(n){{n=+n||0; if(n>=1e6)return(n/1e6).toFixed(1)+'M'; if(n>=1e3)return(n/1e3).toFixed(1)+'K'; return n.toLocaleString('es-AR');}}
function fmt(n)  {{return(+n||0).toLocaleString('es-AR');}}
function fmtU(n) {{return'$'+(+n||0).toLocaleString('es-AR',{{maximumFractionDigits:0}});}}
function pct(a,b){{return b>0?(a/b*100).toFixed(1):'0.0';}}

function mkCh(id,type,labels,datasets,opts={{}}){{
  if(CH[id])CH[id].destroy();
  const ctx=document.getElementById(id); if(!ctx)return;
  CH[id]=new Chart(ctx,{{type,data:{{labels,datasets}},options:{{responsive:true,plugins:{{legend:{{position:'bottom',labels:{{font:{{size:11}}}}}}}}, ...opts}}}});
}}

function buildFunnelCard(color,title,vals,isTotal){{
  const top=vals[0]||1;
  let stHtml='';
  STEPS.forEach((s,i)=>{{
    const v=vals[i];
    const bw=Math.min(100,Math.round(v/top*100));
    const pt=pct(v,top);
    const pp=i>0&&vals[i-1]>0?pct(v,vals[i-1]):null;
    const sub=i===0?'100% del total':`${{pt}}% de Oferta${{pp?' &middot; <b>'+pp+'%</b> prev':''}}`;
    stHtml+=`<div class="f-step">
      <div class="f-step-header"><span class="f-step-label">${{s.label}}</span><span class="f-step-value" style="color:${{color}}">${{fmtK(v)}}</span></div>
      <div class="f-bar-bg"><div class="f-bar" style="width:${{bw}}%;background:${{color}}"></div></div>
      <div class="f-pct">${{sub}}</div>
    </div>`;
  }});
  if(isTotal){{
    return `<div class="funnel-total">
      ${{STEPS.map((s,i)=>{{
        const v=vals[i]; const bw=Math.min(100,Math.round(v/top*100));
        const pt=pct(v,top); const pp=i>0&&vals[i-1]>0?pct(v,vals[i-1]):null;
        return`<div class="ft-step">
          <div class="ft-label">${{s.label}}</div>
          <div class="ft-value">${{fmtK(v)}}</div>
          <div class="ft-sub">${{i===0?'base':pt+'% de Oferta'}}${{pp?' &middot; <b>'+pp+'%</b> prev':''}}</div>
          <div class="ft-bar-bg"><div class="ft-bar" style="width:${{bw}}%"></div></div>
        </div>`;
      }}).join('')}}
    </div>`;
  }}
  return `<div class="funnel-card">
    <div class="fc-title" style="color:${{color}}">${{title}}</div>
    <div class="fc-line" style="background:${{color}}"></div>
    ${{stHtml}}
  </div>`;
}}

function renderFunnel(rows,prod){{
  let html='';
  if(prod==='Todos'){{
    const tv=STEPS.map(s=>stepVal(rows,s));
    html+=buildFunnelCard('#1a1a2e','Total',tv,true);
    let grid='';
    PRODUCTS.forEach(p=>{{
      const pR=rows.filter(r=>r.PRODUCT===p);
      if(!pR.length)return;
      grid+=buildFunnelCard(PCLR[p],PLBL[p],STEPS.map(s=>stepVal(pR,s)),false);
    }});
    html+=`<div class="funnel-grid">${{grid}}</div>`;
  }} else {{
    const pR=rows.filter(r=>r.PRODUCT===prod);
    html=`<div class="funnel-grid" style="justify-items:center">${{buildFunnelCard(PCLR[prod],PLBL[prod],STEPS.map(s=>stepVal(pR,s)),false).replace('funnel-card"','funnel-card single"')}}</div>`;
  }}
  document.getElementById('funnelContainer').innerHTML=html;
}}

function render(){{
  const f=gf();
  const rows=flt(RAW,f,false);
  const tot=agg(rows);
  const isM  =f.unit==='M';
  const isUSD=f.curr==='USD';
  const getProp  =d=>isUSD?d.up   :d.uplc;
  const getOrig  =d=>isUSD?d.uo   :d.uolc;
  const getTkt   =d=>isUSD?d.ticket:d.ticketlc;
  const fmtAmt   =n=>isUSD?'$'+fmt(n):fmt(n)+' LC';
  const currLabel=isUSD?'USD':'LC';

  const vTot=rows.reduce((a,r)=>a+(+r.Q_VIEWS||0),0);
  const cTot=rows.reduce((a,r)=>a+(+r.Q_CLICKS||0),0);

  const kpiData = isM ? [
    ['Prop Oferta',      fmtAmt(getProp(tot)), `Monto ofertado (${{currLabel}})`,    false],
    ['Orig Monto',       fmtAmt(getOrig(tot)), `Monto originado (${{currLabel}})`,   true ],
    ['Ofertados',        fmtK(tot.off),        'Usuarios con oferta activa',          false],
    ['Originados',       fmtK(tot.orig),       'Créditos otorgados',                 false],
    ['CVR %',            tot.cvr+'%',          'Originados / Ofertados',              true ],
    [`Ticket ${{currLabel}}`, fmtAmt(getTkt(tot)), 'Monto promedio por crédito',    false],
  ] : [
    ['Ofertados',  fmtK(tot.off),   'Usuarios con oferta activa',    false],
    ['Views',      fmtK(vTot),      'Vieron card (ofertados)',        false],
    ['Clicks',     fmtK(cTot),      'Clickearon card (ofertados)',    false],
    ['Originados', fmtK(tot.orig),  'Créditos otorgados',             true ],
    ['CVR %',      tot.cvr+'%',     'Originados / Ofertados',         true ],
    ['Ticket USD', fmtU(tot.ticket),'Monto promedio por crédito',     false],
  ];
  document.getElementById('kpis').innerHTML=kpiData.map(([l,v,s,hi])=>`<div class="kpi${{hi?' hi':''}}"><div class="label">${{l}}</div><div class="value">${{v}}</div><div class="sub">${{s}}</div></div>`).join('');

  // Insights
  const chips=[];
  let ts='',tcvr=-1;
  SITES.forEach(s=>{{const d=agg(rows.filter(r=>r.SITE===s)); if(d.cvr>tcvr){{tcvr=d.cvr;ts=s;}}}});
  if(ts) chips.push(`<div class="chip">&#127942; Mayor CVR: <strong>${{ts}} (${{tcvr}}%)</strong></div>`);
  let tp='',to=-1;
  PRODUCTS.forEach(p=>{{const d=agg(rows.filter(r=>r.PRODUCT===p)); if(d.orig>to){{to=d.orig;tp=p;}}}});
  if(tp) chips.push(`<div class="chip">&#128230; Producto lider: <strong>${{PLBL[tp]}} (${{fmtK(to)}} orig)</strong></div>`);
  const tv2=STEPS.map(s=>stepVal(rows,s));
  let md=0,ds='';
  for(let i=1;i<tv2.length;i++){{if(tv2[i-1]>0){{const d=100-tv2[i]/tv2[i-1]*100;if(d>md){{md=d;ds=STEPS[i].label;}}}}}}
  if(ds) chips.push(`<div class="chip">&#128201; Mayor caida: <strong>&rarr;${{ds}} (${{md.toFixed(0)}}% drop)</strong></div>`);
  chips.push(`<div class="chip">&#128176; USD Originado: <strong>${{fmtU(tot.uo)}}</strong></div>`);
  document.getElementById('insightsBar').innerHTML=chips.join('');

  // ── Penetración Card / ON ────────────────────────────────────────────────
  let onR = ON;
  if(f.site !== 'Todos') onR = onR.filter(r => r.SITE === f.site);
  if(f.mes  !== 'Todos') onR = onR.filter(r => r.MonthName === f.mes);
  const onOffQ   = onR.reduce((a,r) => a+(+r.Q_OFERTA_ON||0), 0);
  const onOrigQ  = onR.reduce((a,r) => a+(+r.Q_ORIG_ON||0), 0);
  const onOrigU  = onR.reduce((a,r) => a+(+r.MONTO_USD_ORIG_ON||0), 0);
  const cardNewQ = rows.filter(r=>String(r.FLAG_FST_CRED)==='1').reduce((a,r)=>a+(+r.Q_ORIGINADOS||0),0);
  const cardNewU = rows.filter(r=>String(r.FLAG_FST_CRED)==='1').reduce((a,r)=>a+(+r.CRD_AMT_USD||0),0);
  const p = (a,b) => b>0 ? (a/b*100).toFixed(1)+'%' : '—';
  document.getElementById('penetGrid').innerHTML = [
    [false, 'Oferta Card / ON',       p(tot.off, onOffQ),  `Card: ${{fmtK(tot.off)}} &nbsp;|&nbsp; ON: ${{fmtK(onOffQ)}}`],
    [false, 'Orig Card / ON (Q)',      p(tot.orig, onOrigQ),`Card: ${{fmtK(tot.orig)}} &nbsp;|&nbsp; ON: ${{fmtK(onOrigQ)}}`],
    [false, 'Orig Card / ON (USD)',    p(tot.uo, onOrigU),  `Card: ${{fmtU(tot.uo)}} &nbsp;|&nbsp; ON: ${{fmtU(onOrigU)}}`],
    [true,  'New Users / Card Orig (Q)',  p(cardNewQ, tot.orig), `New: ${{fmtK(cardNewQ)}} &nbsp;|&nbsp; Total: ${{fmtK(tot.orig)}}`],
    [true,  'New Users / Card Orig (USD)',p(cardNewU, tot.uo),   `New: ${{fmtU(cardNewU)}} &nbsp;|&nbsp; Total: ${{fmtU(tot.uo)}}`],
  ].map(([green, lbl, pct, det]) =>
    `<div class="penet-card${{green?' green':''}}">`+
    `<div class="penet-label">${{lbl}}</div>`+
    `<div class="penet-pct">${{pct}}</div>`+
    `<div class="penet-detail">${{det}}</div>`+
    `</div>`
  ).join('');

  renderFunnel(rows,f.product);

  const tRows=flt(RAW,{{...f,mes:'Todos'}},false);
  const tMonths=[...new Set(tRows.map(r=>r.MonthName))].sort((a,b)=>MONTH_ORDER.indexOf(a)-MONTH_ORDER.indexOf(b));
  const tProds=f.product==='Todos'?PRODUCTS:[f.product];
  mkCh('chartTrend','line',tMonths,tProds.map(p=>{{
    const d=tMonths.map(m=>{{ const ag=agg(tRows.filter(r=>r.PRODUCT===p&&r.MonthName===m)); return isM?getOrig(ag):ag.orig; }});
    return {{label:PLBL[p],data:d,borderColor:PCLR[p],backgroundColor:PCLR[p]+'44',fill:true,tension:.3,pointRadius:5}};
  }}),{{scales:{{y:{{beginAtZero:true}}}},plugins:{{tooltip:{{callbacks:{{label:ctx=>ctx.dataset.label+': '+(isM?fmtAmt(ctx.parsed.y):fmt(ctx.parsed.y))}}}}}}}});

  const sLabels=STEPS.slice(1).map(s=>s.label);
  const cProds=f.product==='Todos'?PRODUCTS:[f.product];
  mkCh('chartFunnelCVR','bar',sLabels,cProds.map(p=>{{
    const pR=rows.filter(r=>r.PRODUCT===p);
    const base=stepVal(pR,STEPS[0])||1;
    return {{label:PLBL[p],data:STEPS.slice(1).map(s=>+(stepVal(pR,s)/base*100).toFixed(1)),
             backgroundColor:PCLR[p]+'BB',borderColor:PCLR[p],borderWidth:1.5}};
  }}),{{scales:{{y:{{beginAtZero:true,title:{{display:true,text:'% de Ofertados'}}}}}},plugins:{{tooltip:{{callbacks:{{label:ctx=>ctx.dataset.label+': '+ctx.parsed.y+'%'}}}}}}}});

  const siteD=SITES.map(s=>agg(rows.filter(r=>r.SITE===s)));
  if(CH['chartSite'])CH['chartSite'].destroy();
  CH['chartSite']=new Chart(document.getElementById('chartSite'),{{
    type:'bar',
    data:{{
      labels:SITES,
      datasets:[
        {{label:'Ofertados', data:siteD.map(d=>d.off),  backgroundColor:'#d0d5dd', yAxisID:'y'}},
        {{label:'Originados',data:siteD.map(d=>d.orig), backgroundColor:'#FFE600', yAxisID:'y2'}},
      ]
    }},
    options:{{
      responsive:true,
      plugins:{{
        legend:{{position:'bottom'}},
        tooltip:{{callbacks:{{label:ctx=>ctx.dataset.label+': '+fmt(ctx.parsed.y)}}}}
      }},
      scales:{{
        y:{{beginAtZero:true,position:'left',title:{{display:true,text:'Ofertados',color:'#999',font:{{size:10}}}},ticks:{{color:'#999'}}}},
        y2:{{beginAtZero:true,position:'right',title:{{display:true,text:'Originados',color:'#b8960a',font:{{size:10}}}},ticks:{{color:'#b8960a'}},grid:{{drawOnChartArea:false}}}}
      }}
    }}
  }});

  const mProds=f.product==='Todos'?PRODUCTS:[f.product];
  const mData=mProds.map(p=>agg(rows.filter(r=>r.PRODUCT===p)).orig);
  const mTotal=mData.reduce((a,v)=>a+v,0)||1;
  if(CH['chartMix'])CH['chartMix'].destroy();
  CH['chartMix']=new Chart(document.getElementById('chartMix'),{{
    type:'doughnut',
    data:{{
      labels:mProds.map(p=>PLBL[p]),
      datasets:[{{data:mData,backgroundColor:mProds.map(p=>PCLR[p]),borderWidth:2}}]
    }},
    options:{{
      responsive:true,
      plugins:{{
        legend:{{position:'bottom',labels:{{font:{{size:11}}}}}},
        tooltip:{{callbacks:{{label:ctx=>ctx.label+': '+fmt(ctx.parsed)+' ('+( ctx.parsed/mTotal*100).toFixed(1)+'%)'}}}},
        datalabels:{{
          display:false
        }}
      }}
    }},
    plugins:[{{
      id:'pctLabels',
      afterDatasetDraw(chart){{
        const {{ctx,data}}=chart;
        ctx.save();
        chart.getDatasetMeta(0).data.forEach((arc,i)=>{{
          const pct=(data.datasets[0].data[i]/mTotal*100);
          if(pct<3)return;
          const {{x,y}}=arc.getCenterPoint();
          ctx.fillStyle='#fff';
          ctx.font='bold 12px Segoe UI';
          ctx.textAlign='center';
          ctx.textBaseline='middle';
          ctx.fillText(pct.toFixed(1)+'%',x,y);
        }});
        ctx.restore();
      }}
    }}]
  }});

  // Table headers adapt to currency
  document.getElementById('thProp').textContent='Prop '+currLabel;
  document.getElementById('thOrig').textContent='Orig '+currLabel;
  document.getElementById('thTkt' ).textContent='Ticket '+currLabel;

  const tProdsT=f.product==='Todos'?PRODUCTS:[f.product];
  let tbody='';
  SITES.forEach(site=>{{
    tProdsT.forEach(prod=>{{
      const pR=rows.filter(r=>r.SITE===site&&r.PRODUCT===prod);
      const d=agg(pR);
      if(d.off===0&&d.orig===0)return;
      const vws=pR.reduce((a,r)=>a+(+r.Q_VIEWS||0),0);
      const clk=pR.reduce((a,r)=>a+(+r.Q_CLICKS||0),0);
      const sim=pR.filter(r=>r.N_FUNNEL_RAW!==null&&r.N_FUNNEL_RAW!==''&&+r.N_FUNNEL_RAW>=2).reduce((a,r)=>a+(+r.Q_OFERTADOS||0),0);
      const ryc=pR.filter(r=>r.N_FUNNEL_RAW!==null&&r.N_FUNNEL_RAW!==''&&+r.N_FUNNEL_RAW>=4).reduce((a,r)=>a+(+r.Q_OFERTADOS||0),0);
      tbody+=`<tr>
        <td><b>${{site}}</b></td>
        <td><span class="tag" style="background:${{PCLR[prod]}}33;color:${{PCLR2[prod]}}">${{PLBL[prod]}}</span></td>
        <td>${{fmt(d.off)}}</td><td>${{fmt(vws)}}</td><td>${{fmt(clk)}}</td>
        <td>${{fmt(sim)}}</td><td>${{fmt(ryc)}}</td><td><b>${{fmt(d.orig)}}</b></td>
        <td><b>${{d.cvr}}%</b></td><td>${{fmtAmt(getProp(d))}}</td><td>${{fmtAmt(getOrig(d))}}</td><td>${{fmtAmt(getTkt(d))}}</td>
      </tr>`;
    }});
  }});
  const simT=rows.filter(r=>r.N_FUNNEL_RAW!==null&&r.N_FUNNEL_RAW!==''&&+r.N_FUNNEL_RAW>=2).reduce((a,r)=>a+(+r.Q_OFERTADOS||0),0);
  const rycT=rows.filter(r=>r.N_FUNNEL_RAW!==null&&r.N_FUNNEL_RAW!==''&&+r.N_FUNNEL_RAW>=4).reduce((a,r)=>a+(+r.Q_OFERTADOS||0),0);
  tbody+=`<tr class="total-row"><td>TOTAL</td><td>&mdash;</td>
    <td>${{fmt(tot.off)}}</td><td>${{fmt(vTot)}}</td><td>${{fmt(cTot)}}</td>
    <td>${{fmt(simT)}}</td><td>${{fmt(rycT)}}</td><td>${{fmt(tot.orig)}}</td>
    <td>${{tot.cvr}}%</td><td>${{fmtAmt(getProp(tot))}}</td><td>${{fmtAmt(getOrig(tot))}}</td><td>${{fmtAmt(getTkt(tot))}}</td>
  </tr>`;
  document.getElementById('tableBody').innerHTML=tbody;
}}

render();
</script>
</body>
</html>"""

with open('C:/Users/criva/dashboard_v2.html', 'w', encoding='utf-8') as f:
    f.write(html_v2)
print(f'[{datetime.now().strftime("%H:%M:%S")}] HTML generado: C:/Users/criva/dashboard_v2.html')

# ── 3d. Generar Dashboard V3 (desde V2 con mejoras) ──────────────────────────
with open('C:/Users/criva/dashboard_v2.html', encoding='utf-8') as f:
    html_v3 = f.read()

# 1. Título y limpieza de nav links
html_v3 = html_v3.replace('Card Summary &middot; Funnel V2', 'Card Summary - Placement Dashboard')
html_v3 = html_v3.replace('Card Summary · Funnel V2', 'Card Summary - Placement Dashboard')
html_v3 = html_v3.replace('Funnel V2 &mdash;', 'Card Summary - Placement Dashboard &mdash;')
html_v3 = html_v3.replace('<title>Card Summary · Funnel V3</title>', '<title>Card Summary - Placement Dashboard</title>')
html_v3 = html_v3.replace('<title>Card Summary &middot; Funnel V2</title>', '<title>Card Summary - Placement Dashboard</title>')
html_v3 = html_v3.replace('\n    <a href="index.html" class="nav-link">← Dashboard original</a>', '')
html_v3 = html_v3.replace('\n    <a href="originations.html" class="nav-link">Originations →</a>', '')

# 2. Filtro Usuarios (New/Old) — agregar después de Tipo de Entidad
html_v3 = html_v3.replace(
    '      <option value="PJ">PJ</option>\n    </select></div>\n  <div class="filter-group"><label>Unidad</label>',
    '      <option value="PJ">PJ</option>\n    </select></div>\n'
    '  <div class="filter-group"><label>Usuarios</label>\n'
    '    <select id="fNew" onchange="render()">\n'
    '      <option value="Todos">Todos</option>\n'
    '      <option value="NEW">New Users</option>\n'
    '      <option value="OLD">Old Users</option>\n'
    '    </select></div>\n'
    '  <div class="filter-group"><label>Unidad</label>'
)

# 3. gf(): agregar newu
html_v3 = html_v3.replace(
    "    curr:    document.getElementById('fCurr').value,\n  };",
    "    curr:    document.getElementById('fCurr').value,\n    newu:    document.getElementById('fNew').value,\n  };"
)

# 4. flt(): filtrar por FLAG_FST_CRED
html_v3 = html_v3.replace(
    "(f.ent==='Todos'     || (f.ent==='PF'&&r.KYC_ENTITY_TYPE==='person') || (f.ent==='PJ'&&r.KYC_ENTITY_TYPE==='company'))\n  );",
    "(f.ent==='Todos'     || (f.ent==='PF'&&r.KYC_ENTITY_TYPE==='person') || (f.ent==='PJ'&&r.KYC_ENTITY_TYPE==='company')) &&\n"
    "    (f.newu==='Todos'    || r.FLAG_FST_CRED===f.newu)\n  );"
)

# 5. STEPS: reemplazar Simulador por Loan Amount + Loan Term
html_v3 = html_v3.replace(
    "const STEPS = [\n  {label:'Oferta',   min:null    },\n  {label:'Views',    min:'views' },\n  {label:'Clicks',   min:'clicks'},\n  {label:'Simulador',min:2       },\n  {label:'R&C',      min:4       },\n  {label:'Congrats', min:'orig'  },\n];",
    "const STEPS = [\n  {label:'Oferta',      min:null},\n  {label:'Views',       min:'views'},\n  {label:'Clicks',      min:'clicks'},\n  {label:'Loan Amount', min:3},\n  {label:'Loan Term',   min:3, xf:r=>{const p=r.PATH_RAW||'';return p.includes('term_selection')||p.includes('payments_detail')||+r.N_FUNNEL_RAW>=4;}},\n  {label:'R\\x26C',     min:4},\n  {label:'Congrats',    min:'orig'},\n];"
)

# 6. stepVal: soporte para xf (extra filter)
html_v3 = html_v3.replace(
    "  return pR.filter(r=>r.N_FUNNEL_RAW!==null&&r.N_FUNNEL_RAW!==''&&+r.N_FUNNEL_RAW>=s.min)\n           .reduce((a,r)=>a+(+r.Q_OFERTADOS||0),0);\n}",
    "  const base=pR.filter(r=>r.N_FUNNEL_RAW!==null&&r.N_FUNNEL_RAW!==''&&+r.N_FUNNEL_RAW>=s.min);\n  return(s.xf?base.filter(s.xf):base).reduce((a,r)=>a+(+r.Q_OFERTADOS||0),0);\n}"
)

# 7. chartTrend → tabla mensual (Ofertados, Originaciones, CVR%, Monto, Ticket)
html_v3 = html_v3.replace(
    '<div class="chart-card"><h3>Tendencia Originaciones</h3><canvas id="chartTrend" height="160"></canvas></div>',
    '<div class="chart-card" style="flex:1 1 100%"><h3>Tendencia Mensual</h3><div id="trendTableWrap"></div></div>',
    1
)
# CSS paleta profesional + tabla de tendencia
html_v3 = html_v3.replace('</style>', """
  /* ── V3 Palette Override ───────────────────── */
  body{background:#ffffff;}
  header{background:#FFE600;justify-content:center;position:relative;}
  header h1{color:#111111;}
  header>div:first-child{text-align:center;}
  header .meta{position:absolute;right:32px;}
  .meta .updated{color:rgba(0,0,0,.5);}
  .nav-link{color:#111111;}
  /* Filter bar subtle background */
  .filters{background:#f5f5f5;border-bottom:3px solid #FFE600;}
  .filters select:focus{border-color:#1565c0;}
  /* KPI section — fondo blanco, cards oscuras */
  .kpis{background:#ffffff;margin:0;padding:20px 32px 12px;}
  .insights-bar{background:#ffffff;padding-bottom:20px;}
  .kpi{background:#ffffff;border:1px solid #e8e8e8;border-top:3px solid #FFE600;box-shadow:0 4px 18px rgba(0,0,0,.13);}
  .kpi .label{color:#888;}
  .kpi .value{color:#111111;}
  .kpi .sub{color:#bbb;}
  .kpi.hi{background:#ffffff;border:1px solid #e8e8e8;border-top:3px solid #111111;}
  .kpi.hi .label{color:#888;}
  .kpi.hi .value{color:#111111;}
  .kpi.hi .sub{color:#bbb;}
  .chip{background:#ffffff;border:1px solid #e8e8e8;border-left:3px solid #FFE600;color:#555;box-shadow:0 1px 6px rgba(0,0,0,.07);}
  .chip strong{color:#111111;}
  /* Charts section — fondo blanco, cards con sombra */
  .charts-row{background:#ffffff;padding-top:4px;padding-bottom:24px;margin:0;}
  .chart-card{box-shadow:0 4px 18px rgba(0,0,0,.13);border:1px solid #e8e8e8;}
  .chart-card h3{color:#555;}
  /* Section dividers on black */
  .sec{background:#ffffff;padding-top:16px;padding-bottom:8px;}
  .sec h2{color:#333;}
  .sec span{color:#aaa;}
  /* Funnel section: cards con sombra para distinguirse del fondo */
  .funnel-section{background:#ffffff;}
  .funnel-card{background:#ffffff;box-shadow:0 4px 18px rgba(0,0,0,.13);border:1px solid #e8e8e8;}
  .funnel-total{background:#ffffff;border-top-color:#002147;box-shadow:0 4px 18px rgba(0,0,0,.13);border:1px solid #e8e8e8;}
  .ft-bar-bg{background:#f0f2f5;}
  .f-bar-bg{background:#f0f2f5;}
  /* Header badges visibles sobre amarillo */
  .meta .updated{color:rgba(0,0,0,.5);}
  .meta .badge{background:#111111;color:#FFE600;}
  .meta .badge2{background:#1a5c1a;color:#ffffff;}
  /* Filter labels more readable */
  .filters label{color:#444;}
  /* Rest */
  th{background:#002147;color:#ffffff;}
  tr:hover td{background:#f0f5fb;}
  .total-row td{border-top:2px solid #1565c0;}
  .penet-card{background:#ffffff;border:1px solid #e8e8e8;border-left:4px solid #FFE600;box-shadow:0 4px 18px rgba(0,0,0,.13);}
  .penet-label{color:#888;}
  .penet-pct{color:#111111;}
  .penet-detail{color:#bbb;}
  .penet-section{background:#ffffff;}
  .funnel-total{border-top-color:#002147;}
  .ft-bar{background:#1565c0;}
  /* ── Tabla tendencia ───────────────────────── */
  .tbl-trend{width:100%;border-collapse:collapse;font-size:13px;}
  .tbl-trend th{background:#002147;color:#ffffff;font-weight:700;padding:8px 12px;text-align:right;border-bottom:none;}
  .tbl-trend th:first-child{text-align:left;}
  .tbl-trend td{padding:7px 12px;text-align:right;border-bottom:1px solid #f0f0f0;}
  .tbl-trend td:first-child{text-align:left;font-weight:600;}
  .tbl-trend tr:hover td{background:#e8f0fb;}
</style>""", 1)

# 8b. chartSite → escala de grises
html_v3 = html_v3.replace(
    "{label:'Ofertados', data:siteD.map(d=>d.off),  backgroundColor:'#d0d5dd', yAxisID:'y'},",
    "{label:'Ofertados', data:siteD.map(d=>d.off),  backgroundColor:'#555555', yAxisID:'y'},"
)
html_v3 = html_v3.replace(
    "{label:'Originados',data:siteD.map(d=>d.orig), backgroundColor:'#FFE600', yAxisID:'y2'},",
    "{label:'Originados',data:siteD.map(d=>d.orig), backgroundColor:'#bbbbbb', yAxisID:'y2'},"
)

# 8. Colores de productos → escala de azules
html_v3 = html_v3.replace(
    "const PCLR = {'CF':'#FFE600','PPV':'#00C9FF','DINERO_EXPRESS':'#FF6B6B','SELLER_LINE':'#A78BFA'};",
    "const PCLR = {'CF':'#1a237e','PPV':'#1565c0','DINERO_EXPRESS':'#0288d1','SELLER_LINE':'#26c6da'};"
)
html_v3 = html_v3.replace(
    "const PCLR2= {'CF':'#9a7c00','PPV':'#006f8f','DINERO_EXPRESS':'#8f1f1f','SELLER_LINE':'#5a3daf'};",
    "const PCLR2= {'CF':'#0d1257','PPV':'#0a3d7a','DINERO_EXPRESS':'#015d8a','SELLER_LINE':'#007c8a'};"
)

old_trend = (
    "mkCh('chartTrend','line',tMonths,tProds.map(p=>{\n"
    "    const d=tMonths.map(m=>{ const ag=agg(tRows.filter(r=>r.PRODUCT===p&&r.MonthName===m)); return isM?getOrig(ag):ag.orig; });\n"
    "    return {label:PLBL[p],data:d,borderColor:PCLR[p],backgroundColor:PCLR[p]+'44',fill:true,tension:.3,pointRadius:5};\n"
    "  }),{scales:{y:{beginAtZero:true}},plugins:{tooltip:{callbacks:{label:ctx=>ctx.dataset.label+': '+(isM?fmtAmt(ctx.parsed.y):fmt(ctx.parsed.y))}}}});"
)
new_trend = (
    "const tTotals=tMonths.map(m=>{const ag=agg(tRows.filter(r=>r.MonthName===m));\n"
    "    return{mes:m,off:ag.off,orig:ag.orig,cvr:ag.off>0?+(ag.orig/ag.off*100).toFixed(1):0,\n"
    "           amt:getOrig(ag),tkt:ag.orig>0?Math.round(getOrig(ag)/ag.orig):0};});\n"
    "  const tHtml='<table class=\"tbl-trend\"><thead><tr>'\n"
    "    +'<th>Mes</th><th>Ofertados</th><th>Originaciones</th><th>CVR%</th><th>Monto Orig</th><th>Ticket Prom</th>'\n"
    "    +'</tr></thead><tbody>'\n"
    "    +tTotals.map(d=>{\n"
    "      return '<tr>'\n"
    "        +'<td>'+d.mes+'</td>'\n"
    "        +'<td>'+fmt(d.off)+'</td>'\n"
    "        +'<td>'+fmt(d.orig)+'</td>'\n"
    "        +'<td>'+d.cvr+'%</td>'\n"
    "        +'<td>'+fmtAmt(d.amt)+'</td>'\n"
    "        +'<td>'+fmtAmt(d.tkt)+'</td>'\n"
    "        +'</tr>';\n"
    "    }).join('')+'</tbody></table>';\n"
    "  document.getElementById('trendTableWrap').innerHTML=tHtml;"
)
html_v3 = html_v3.replace(old_trend, new_trend, 1)

# 8. Evolución Mensual (rename)
html_v3 = html_v3.replace('<h3>Tendencia Mensual</h3>', '<h3>Evolución Mensual</h3>')

# 9. Rename 'Congrats' → 'Originación' en STEPS
html_v3 = html_v3.replace("{label:'Congrats',    min:'orig'},", "{label:'Originación', min:'orig'},")

# 10. Eliminar chip de "Mayor caída" completamente
html_v3 = html_v3.replace(
    "  let md=0,ds='';\n"
    "  for(let i=1;i<tv2.length;i++){if(tv2[i-1]>0){const d=100-tv2[i]/tv2[i-1]*100;if(d>md){md=d;ds=STEPS[i].label;}}}\n"
    '  if(ds) chips.push(`<div class="chip">&#128201; Mayor caida: <strong>&rarr;${ds} (${md.toFixed(0)}% drop)</strong></div>`);',
    "  let md=0,ds='';\n"
    "  for(let i=1;i<tv2.length;i++){if(tv2[i-1]>0){const d=100-tv2[i]/tv2[i-1]*100;if(d>md){md=d;ds=STEPS[i].label;}}}"
)

# 11. Quitar CVR chart card de row 1
html_v3 = html_v3.replace(
    '\n  <div class="chart-card"><h3>CVR por etapa</h3><canvas id="chartFunnelCVR" height="160"></canvas></div>',
    ''
)

# 12. Reemplazar row 2 (Site + Mix) por 4 gráficos de evolución mensual
html_v3 = html_v3.replace(
    '<div class="charts-row">\n'
    '  <div class="chart-card"><h3>Ofertados vs Originados por Site</h3><canvas id="chartSite" height="160"></canvas></div>\n'
    '  <div class="chart-card"><h3>Mix Originaciones por Producto</h3><canvas id="chartMix" height="160"></canvas></div>\n'
    '</div>',
    '<div class="charts-row">\n'
    '  <div class="chart-card"><h3>Oferta — Producto</h3><canvas id="chartEvOffProd" height="180"></canvas></div>\n'
    '  <div class="chart-card"><h3>Oferta — Segmento</h3><canvas id="chartEvOffSeg" height="180"></canvas></div>\n'
    '</div>\n'
    '<div class="charts-row">\n'
    '  <div class="chart-card"><h3>Originación — Producto</h3><canvas id="chartEvOrigProd" height="180"></canvas></div>\n'
    '  <div class="chart-card"><h3>Originación — Segmento</h3><canvas id="chartEvOrigSeg" height="180"></canvas></div>\n'
    '</div>'
)

# 13. Reemplazar JS de 3 gráficos viejos por 4 de evolución mensual apilados
old_ev = (
    "  const sLabels=STEPS.slice(1).map(s=>s.label);\n"
    "  const cProds=f.product==='Todos'?PRODUCTS:[f.product];\n"
    "  mkCh('chartFunnelCVR','bar',sLabels,cProds.map(p=>{\n"
    "    const pR=rows.filter(r=>r.PRODUCT===p);\n"
    "    const base=stepVal(pR,STEPS[0])||1;\n"
    "    return {label:PLBL[p],data:STEPS.slice(1).map(s=>+(stepVal(pR,s)/base*100).toFixed(1)),\n"
    "             backgroundColor:PCLR[p]+'BB',borderColor:PCLR[p],borderWidth:1.5};\n"
    "  }),{scales:{y:{beginAtZero:true,title:{display:true,text:'% de Ofertados'}}},plugins:{tooltip:{callbacks:{label:ctx=>ctx.dataset.label+': '+ctx.parsed.y+'%'}}}});\n"
    "\n"
    "  const siteD=SITES.map(s=>agg(rows.filter(r=>r.SITE===s)));\n"
    "  if(CH['chartSite'])CH['chartSite'].destroy();\n"
    "  CH['chartSite']=new Chart(document.getElementById('chartSite'),{\n"
    "    type:'bar',\n"
    "    data:{\n"
    "      labels:SITES,\n"
    "      datasets:[\n"
    "        {label:'Ofertados', data:siteD.map(d=>d.off),  backgroundColor:'#555555', yAxisID:'y'},\n"
    "        {label:'Originados',data:siteD.map(d=>d.orig), backgroundColor:'#bbbbbb', yAxisID:'y2'},\n"
    "      ]\n"
    "    },\n"
    "    options:{\n"
    "      responsive:true,\n"
    "      plugins:{\n"
    "        legend:{position:'bottom'},\n"
    "        tooltip:{callbacks:{label:ctx=>ctx.dataset.label+': '+fmt(ctx.parsed.y)}}\n"
    "      },\n"
    "      scales:{\n"
    "        y:{beginAtZero:true,position:'left',title:{display:true,text:'Ofertados',color:'#999',font:{size:10}},ticks:{color:'#999'}},\n"
    "        y2:{beginAtZero:true,position:'right',title:{display:true,text:'Originados',color:'#b8960a',font:{size:10}},ticks:{color:'#b8960a'},grid:{drawOnChartArea:false}}\n"
    "      }\n"
    "    }\n"
    "  });\n"
    "\n"
    "  const mProds=f.product==='Todos'?PRODUCTS:[f.product];\n"
    "  const mData=mProds.map(p=>agg(rows.filter(r=>r.PRODUCT===p)).orig);\n"
    "  const mTotal=mData.reduce((a,v)=>a+v,0)||1;\n"
    "  if(CH['chartMix'])CH['chartMix'].destroy();\n"
    "  CH['chartMix']=new Chart(document.getElementById('chartMix'),{\n"
    "    type:'doughnut',\n"
    "    data:{\n"
    "      labels:mProds.map(p=>PLBL[p]),\n"
    "      datasets:[{data:mData,backgroundColor:mProds.map(p=>PCLR[p]),borderWidth:2}]\n"
    "    },\n"
    "    options:{\n"
    "      responsive:true,\n"
    "      plugins:{\n"
    "        legend:{position:'bottom',labels:{font:{size:11}}},\n"
    "        tooltip:{callbacks:{label:ctx=>ctx.label+': '+fmt(ctx.parsed)+' ('+( ctx.parsed/mTotal*100).toFixed(1)+'%)'}},\n"
    "        datalabels:{\n"
    "          display:false\n"
    "        }\n"
    "      }\n"
    "    },\n"
    "    plugins:[{\n"
    "      id:'pctLabels',\n"
    "      afterDatasetDraw(chart){\n"
    "        const {ctx,data}=chart;\n"
    "        ctx.save();\n"
    "        chart.getDatasetMeta(0).data.forEach((arc,i)=>{\n"
    "          const pct=(data.datasets[0].data[i]/mTotal*100);\n"
    "          if(pct<3)return;\n"
    "          const {x,y}=arc.getCenterPoint();\n"
    "          ctx.fillStyle='#fff';\n"
    "          ctx.font='bold 12px Segoe UI';\n"
    "          ctx.textAlign='center';\n"
    "          ctx.textBaseline='middle';\n"
    "          ctx.fillText(pct.toFixed(1)+'%',x,y);\n"
    "        });\n"
    "        ctx.restore();\n"
    "      }\n"
    "    }]\n"
    "  });\n"
)
new_ev = (
    "  const SCLR={'1.LONGTAIL':'#1a237e','2.SMB':'#1565c0','3.BIG SELLERS':'#26c6da'};\n"
    "  const SLBL={'1.LONGTAIL':'Longtail','2.SMB':'SMB','3.BIG SELLERS':'Big Sellers'};\n"
    "  const SEGS=['1.LONGTAIL','2.SMB','3.BIG SELLERS'];\n"
    "  const evOpts={scales:{x:{stacked:true},y:{stacked:true,beginAtZero:true}},plugins:{legend:{position:'bottom',labels:{font:{size:10}}},tooltip:{callbacks:{label:ctx=>ctx.dataset.label+': '+(isM?fmtAmt(ctx.parsed.y):fmt(ctx.parsed.y))}}}};\n"
    "  mkCh('chartEvOffProd','bar',tMonths,tProds.map(p=>{\n"
    "    const d=tMonths.map(m=>{const ag=agg(tRows.filter(r=>r.PRODUCT===p&&r.MonthName===m));return isM?getProp(ag):ag.off;});\n"
    "    return {label:PLBL[p],data:d,backgroundColor:PCLR[p],stack:'s'};\n"
    "  }),evOpts);\n"
    "  mkCh('chartEvOffSeg','bar',tMonths,SEGS.map(s=>{\n"
    "    const d=tMonths.map(m=>{const ag=agg(tRows.filter(r=>r.SEL_SEGMENT===s&&r.MonthName===m));return isM?getProp(ag):ag.off;});\n"
    "    return {label:SLBL[s],data:d,backgroundColor:SCLR[s],stack:'s'};\n"
    "  }),evOpts);\n"
    "  mkCh('chartEvOrigProd','bar',tMonths,tProds.map(p=>{\n"
    "    const d=tMonths.map(m=>{const ag=agg(tRows.filter(r=>r.PRODUCT===p&&r.MonthName===m));return isM?getOrig(ag):ag.orig;});\n"
    "    return {label:PLBL[p],data:d,backgroundColor:PCLR[p],stack:'s'};\n"
    "  }),evOpts);\n"
    "  mkCh('chartEvOrigSeg','bar',tMonths,SEGS.map(s=>{\n"
    "    const d=tMonths.map(m=>{const ag=agg(tRows.filter(r=>r.SEL_SEGMENT===s&&r.MonthName===m));return isM?getOrig(ag):ag.orig;});\n"
    "    return {label:SLBL[s],data:d,backgroundColor:SCLR[s],stack:'s'};\n"
    "  }),evOpts);\n"
)
html_v3 = html_v3.replace(old_ev, new_ev, 1)

# 14. Funnel: barras más altas (sin centrar para no romper valores pequeños)
html_v3 = html_v3.replace('</style>',
    '  .f-bar-bg{height:8px!important;border-radius:4px!important;}\n'
    '  .f-bar{height:8px!important;border-radius:4px!important;}\n'
    '  .ft-bar-bg{height:8px!important;border-radius:4px!important;}\n'
    '  .ft-bar{height:8px!important;border-radius:4px!important;}\n'
    '</style>', 1)

with open('C:/Users/criva/dashboard_v3.html', 'w', encoding='utf-8') as f:
    f.write(html_v3)
print(f'[{datetime.now().strftime("%H:%M:%S")}] HTML generado: C:/Users/criva/dashboard_v3.html')

# ── 3e. Generar Dashboard New vs Old ─────────────────────────────────────────
html_newold = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Card Summary · New vs Old Users</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{ font-family:'Segoe UI',system-ui,sans-serif; background:#f0f2f5; color:#333; font-size:14px; }}
  header {{ background:#1a1a2e; color:#FFE600; padding:18px 32px; display:flex; align-items:center; justify-content:space-between; box-shadow:0 2px 8px rgba(0,0,0,.25); }}
  header h1 {{ font-size:20px; font-weight:700; letter-spacing:.5px; }}
  .meta {{ text-align:right; }}
  .meta .updated {{ font-size:11px; color:#aaa; }}
  .meta .badge {{ background:#FFE600; color:#1a1a2e; border-radius:4px; padding:2px 7px; font-size:10px; font-weight:700; margin-top:4px; display:inline-block; }}
  .nav-link {{ font-size:12px; color:#FFE600; opacity:.7; text-decoration:none; margin-left:16px; }}
  .nav-link:hover {{ opacity:1; }}
  .filters {{ background:#fff; padding:12px 32px; display:flex; gap:20px; align-items:center; flex-wrap:wrap; border-bottom:3px solid #FFE600; box-shadow:0 2px 4px rgba(0,0,0,.05); }}
  .filter-group {{ display:flex; align-items:center; gap:8px; }}
  .filters label {{ font-weight:700; font-size:11px; color:#777; text-transform:uppercase; letter-spacing:.5px; }}
  .filters select {{ padding:7px 12px; border:1.5px solid #e0e0e0; border-radius:8px; font-size:13px; cursor:pointer; background:#fafafa; min-width:130px; }}
  .filters select:focus {{ outline:none; border-color:#FFE600; }}
  .section {{ padding:20px 32px 8px; }}
  .section-title {{ font-size:13px; font-weight:700; color:#666; text-transform:uppercase; letter-spacing:.5px; margin-bottom:14px; }}
  /* Comparison columns */
  .compare-grid {{ display:grid; grid-template-columns:1fr 1fr 1fr; gap:16px; margin-bottom:8px; }}
  .col-card {{ background:#fff; border-radius:12px; padding:20px; box-shadow:0 1px 4px rgba(0,0,0,.07); }}
  .col-card.total {{ border-top:4px solid #ccc; }}
  .col-card.new-u {{ border-top:4px solid #4CAF50; }}
  .col-card.old-u {{ border-top:4px solid #2196F3; }}
  .col-title {{ font-size:12px; font-weight:800; text-transform:uppercase; letter-spacing:.8px; margin-bottom:14px; color:#555; }}
  .col-title.new-u {{ color:#4CAF50; }}
  .col-title.old-u {{ color:#2196F3; }}
  .kpi-row {{ display:flex; justify-content:space-between; align-items:baseline; padding:8px 0; border-bottom:1px solid #f0f0f0; }}
  .kpi-row:last-child {{ border-bottom:none; }}
  .kpi-label {{ font-size:12px; color:#777; }}
  .kpi-val {{ font-size:18px; font-weight:700; color:#1a1a2e; }}
  .kpi-sub {{ font-size:11px; color:#aaa; }}
  /* Lift banner */
  .lift-banner {{ background:linear-gradient(135deg,#1a1a2e,#2d2d5e); color:#fff; border-radius:12px; padding:22px 32px; display:flex; align-items:center; justify-content:space-around; gap:24px; margin-bottom:24px; }}
  .lift-item {{ text-align:center; }}
  .lift-item .lbl {{ font-size:11px; color:#aaa; text-transform:uppercase; letter-spacing:.6px; margin-bottom:6px; }}
  .lift-item .val {{ font-size:28px; font-weight:800; }}
  .lift-item .val.green {{ color:#4CAF50; }}
  .lift-item .val.yellow {{ color:#FFE600; }}
  .lift-item .val.blue {{ color:#64B5F6; }}
  .lift-divider {{ width:1px; background:rgba(255,255,255,.15); height:50px; }}
  /* Charts */
  .charts-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-bottom:16px; }}
  .chart-card {{ background:#fff; border-radius:12px; padding:20px; box-shadow:0 1px 4px rgba(0,0,0,.07); }}
  .chart-title {{ font-size:12px; font-weight:700; color:#555; text-transform:uppercase; letter-spacing:.5px; margin-bottom:14px; }}
  .chart-full {{ background:#fff; border-radius:12px; padding:20px; box-shadow:0 1px 4px rgba(0,0,0,.07); margin-bottom:16px; }}
  /* Table */
  .tbl-wrap {{ background:#fff; border-radius:12px; padding:20px; box-shadow:0 1px 4px rgba(0,0,0,.07); overflow-x:auto; }}
  table {{ width:100%; border-collapse:collapse; font-size:13px; }}
  th {{ background:#f7f7f7; padding:10px 12px; text-align:left; font-size:11px; font-weight:700; color:#666; text-transform:uppercase; letter-spacing:.4px; border-bottom:2px solid #e0e0e0; white-space:nowrap; }}
  td {{ padding:9px 12px; border-bottom:1px solid #f0f0f0; }}
  tr:hover td {{ background:#fafafa; }}
  .tag-new {{ background:#E8F5E9; color:#2E7D32; border-radius:4px; padding:1px 7px; font-size:11px; font-weight:700; }}
  .tag-old {{ background:#E3F2FD; color:#1565C0; border-radius:4px; padding:1px 7px; font-size:11px; font-weight:700; }}
  .tag-lift-pos {{ background:#E8F5E9; color:#2E7D32; border-radius:4px; padding:1px 7px; font-size:11px; font-weight:700; }}
  .tag-lift-neg {{ background:#FFEBEE; color:#C62828; border-radius:4px; padding:1px 7px; font-size:11px; font-weight:700; }}
  .total-row td {{ font-weight:700; background:#fffde7; }}
</style>
</head>
<body>
<header>
  <div>
    <h1>Card Summary &mdash; New vs Old Users</h1>
    <div style="margin-top:4px">
      <a href="index.html" class="nav-link">Funnel</a>
      <a href="v2.html" class="nav-link">Funnel V2</a>
      <a href="originations.html" class="nav-link">Originations</a>
    </div>
  </div>
  <div class="meta">
    <div class="updated">Actualizado: {updated_at}</div>
    <div class="badge">BU = ON</div>
    <div style="display:inline-block" class="badge2">FLAG_FST_CRED</div>
  </div>
</header>

<div class="filters">
  <div class="filter-group"><label>Site</label>
    <select id="fSite" onchange="render()">
      <option>Todos</option>
      {chr(10).join(f'<option>{s}</option>' for s in sorted(set(r['SITE'] for r in v2_rows)))}
    </select>
  </div>
  <div class="filter-group"><label>Mes</label>
    <select id="fMonth" onchange="render()">
      {chr(10).join(f'<option>{m}</option>' for m in v2_month_names)}
    </select>
  </div>
  <div class="filter-group"><label>Producto</label>
    <select id="fProd" onchange="render()">
      <option>Todos</option>
      {chr(10).join(f'<option>{p}</option>' for p in sorted(set(r['PRODUCT'] for r in v2_rows)))}
    </select>
  </div>
</div>

<div class="section">
  <div class="section-title">Comparativa New vs Old</div>
  <div class="compare-grid" id="compareGrid"></div>
  <div class="lift-banner" id="liftBanner"></div>
</div>

<div class="section">
  <div class="section-title">Originaciones por Producto</div>
  <div class="charts-grid">
    <div class="chart-card">
      <div class="chart-title">Originaciones (New vs Old)</div>
      <canvas id="chartOrig" height="220"></canvas>
    </div>
    <div class="chart-card">
      <div class="chart-title">CVR (%) por Producto</div>
      <canvas id="chartCvr" height="220"></canvas>
    </div>
  </div>
</div>

<div class="section">
  <div class="section-title">Tendencia Mensual</div>
  <div class="chart-full">
    <div class="chart-title">CVR (%) New vs Old por Mes</div>
    <canvas id="chartTrend" height="120"></canvas>
  </div>
</div>

<div class="section" style="padding-bottom:32px">
  <div class="section-title">Detalle por Producto</div>
  <div class="tbl-wrap">
    <table id="detailTable"></table>
  </div>
</div>

<script>
const DATA = {v2_data};
const MONTHS_ORDER = {json.dumps(list(month_map.values()))};

const fmt   = n => n==null||isNaN(n)?'—':n>=1e6?(n/1e6).toFixed(1)+'M':n>=1e3?(n/1e3).toFixed(1)+'K':String(Math.round(n));
const fmtPct= n => n==null||isNaN(n)?'—':n.toFixed(2)+'%';
const fmtK  = n => n==null||isNaN(n)?'—':(n/1000).toFixed(0)+'K';

let chartOrig, chartCvr, chartTrend;

function flt(data) {{
  const site  = document.getElementById('fSite').value;
  const month = document.getElementById('fMonth').value;
  const prod  = document.getElementById('fProd').value;
  let r = data;
  if (site  !== 'Todos') r = r.filter(x => x.SITE      === site);
  if (month !== 'Todos') r = r.filter(x => x.MonthName === month);
  if (prod  !== 'Todos') r = r.filter(x => x.PRODUCT   === prod);
  return r;
}}

function isNew(r) {{ return String(r.FLAG_FST_CRED) === '1'; }}
function isOld(r) {{ return String(r.FLAG_FST_CRED) === '0'; }}

function metrics(rows) {{
  const off  = rows.reduce((a,r) => a + (+r.Q_OFERTADOS||0), 0);
  const origN= rows.filter(isNew).reduce((a,r) => a + (+r.Q_ORIGINADOS||0), 0);
  const origO= rows.filter(isOld).reduce((a,r) => a + (+r.Q_ORIGINADOS||0), 0);
  const origT= origN + origO;
  const usdN = rows.filter(isNew).reduce((a,r) => a + (+r.CRD_AMT_USD||0), 0);
  const usdO = rows.filter(isOld).reduce((a,r) => a + (+r.CRD_AMT_USD||0), 0);
  const cvrN = off > 0 ? origN / off * 100 : 0;
  const cvrO = off > 0 ? origO / off * 100 : 0;
  const cvrT = off > 0 ? origT / off * 100 : 0;
  const lift = cvrO > 0 ? cvrN / cvrO : null;
  const tkN  = origN > 0 ? usdN / origN : 0;
  const tkO  = origO > 0 ? usdO / origO : 0;
  return {{ off, origN, origO, origT, usdN, usdO, cvrN, cvrO, cvrT, lift, tkN, tkO }};
}}

function render() {{
  const rows = flt(DATA);
  const m    = metrics(rows);

  // ── Compare columns ──────────────────────────────────────────────────────
  document.getElementById('compareGrid').innerHTML = `
    <div class="col-card total">
      <div class="col-title">Total</div>
      <div class="kpi-row"><span class="kpi-label">Ofertados</span><span class="kpi-val">${{fmt(m.off)}}</span></div>
      <div class="kpi-row"><span class="kpi-label">Originados</span><span class="kpi-val">${{fmt(m.origT)}}</span></div>
      <div class="kpi-row"><span class="kpi-label">CVR</span><span class="kpi-val">${{fmtPct(m.cvrT)}}</span></div>
      <div class="kpi-row"><span class="kpi-label">USD Orig</span><span class="kpi-val">${{fmtK(m.usdN+m.usdO)}}</span></div>
    </div>
    <div class="col-card new-u">
      <div class="col-title new-u">New Users (1er crédito)</div>
      <div class="kpi-row"><span class="kpi-label">Originados</span><span class="kpi-val">${{fmt(m.origN)}}</span></div>
      <div class="kpi-row"><span class="kpi-label">CVR vs Oferta</span><span class="kpi-val">${{fmtPct(m.cvrN)}}</span></div>
      <div class="kpi-row"><span class="kpi-label">USD Orig</span><span class="kpi-val">${{fmtK(m.usdN)}}</span></div>
      <div class="kpi-row"><span class="kpi-label">Ticket USD</span><span class="kpi-val">${{fmt(m.tkN)}}</span></div>
    </div>
    <div class="col-card old-u">
      <div class="col-title old-u">Old Users (recurrentes)</div>
      <div class="kpi-row"><span class="kpi-label">Originados</span><span class="kpi-val">${{fmt(m.origO)}}</span></div>
      <div class="kpi-row"><span class="kpi-label">CVR vs Oferta</span><span class="kpi-val">${{fmtPct(m.cvrO)}}</span></div>
      <div class="kpi-row"><span class="kpi-label">USD Orig</span><span class="kpi-val">${{fmtK(m.usdO)}}</span></div>
      <div class="kpi-row"><span class="kpi-label">Ticket USD</span><span class="kpi-val">${{fmt(m.tkO)}}</span></div>
    </div>`;

  // ── Lift banner ───────────────────────────────────────────────────────────
  const liftVal  = m.lift != null ? m.lift.toFixed(2)+'x' : '—';
  const liftPct  = m.lift != null ? ((m.lift-1)*100).toFixed(1)+'%' : '—';
  const liftColor= m.lift != null && m.lift >= 1 ? 'green' : 'tag-lift-neg';
  document.getElementById('liftBanner').innerHTML = `
    <div class="lift-item"><div class="lbl">CVR New</div><div class="val green">${{fmtPct(m.cvrN)}}</div></div>
    <div class="lift-divider"></div>
    <div class="lift-item"><div class="lbl">CVR Old</div><div class="val blue">${{fmtPct(m.cvrO)}}</div></div>
    <div class="lift-divider"></div>
    <div class="lift-item"><div class="lbl">Lift (New / Old)</div><div class="val yellow">${{liftVal}}</div></div>
    <div class="lift-divider"></div>
    <div class="lift-item"><div class="lbl">Diferencia CVR</div><div class="val ${{m.lift>=1?'green':'val'}}" style="${{m.lift<1?'color:#f44336':''}}">+${{liftPct}}</div></div>
    <div class="lift-divider"></div>
    <div class="lift-item"><div class="lbl">Mix New</div><div class="val yellow">${{m.origT>0?(m.origN/m.origT*100).toFixed(1)+'%':'—'}}</div></div>`;

  // ── Per-product data ──────────────────────────────────────────────────────
  const products = [...new Set(rows.map(r => r.PRODUCT))].sort();
  const prodMetrics = products.map(p => {{ const pr = rows.filter(r=>r.PRODUCT===p); return {{p, ...metrics(pr)}}; }});

  // ── Chart: Orig by product ────────────────────────────────────────────────
  if (chartOrig) chartOrig.destroy();
  chartOrig = new Chart(document.getElementById('chartOrig'), {{
    type: 'bar',
    data: {{
      labels: prodMetrics.map(x => x.p),
      datasets: [
        {{ label:'New', data: prodMetrics.map(x=>x.origN), backgroundColor:'#4CAF50' }},
        {{ label:'Old', data: prodMetrics.map(x=>x.origO), backgroundColor:'#2196F3' }}
      ]
    }},
    options: {{ responsive:true, plugins:{{ legend:{{position:'top'}} }}, scales:{{ y:{{beginAtZero:true}} }} }}
  }});

  // ── Chart: CVR by product ─────────────────────────────────────────────────
  if (chartCvr) chartCvr.destroy();
  chartCvr = new Chart(document.getElementById('chartCvr'), {{
    type: 'bar',
    data: {{
      labels: prodMetrics.map(x => x.p),
      datasets: [
        {{ label:'CVR New (%)', data: prodMetrics.map(x=>+x.cvrN.toFixed(2)), backgroundColor:'#A5D6A7' }},
        {{ label:'CVR Old (%)', data: prodMetrics.map(x=>+x.cvrO.toFixed(2)), backgroundColor:'#90CAF9' }},
        {{ label:'CVR Total (%)', data: prodMetrics.map(x=>+x.cvrT.toFixed(2)), backgroundColor:'#FFE600', borderColor:'#ccc', borderWidth:1 }}
      ]
    }},
    options: {{ responsive:true, plugins:{{ legend:{{position:'top'}} }}, scales:{{ y:{{beginAtZero:true}} }} }}
  }});

  // ── Chart: Monthly trend ──────────────────────────────────────────────────
  const allMonths = [...new Set(DATA.map(r=>r.MonthName))].sort((a,b)=>MONTHS_ORDER.indexOf(a)-MONTHS_ORDER.indexOf(b));
  const trendN=[], trendO=[];
  allMonths.forEach(mon => {{
    const mr = flt(DATA.map(r=>r)).filter(r=>r.MonthName===mon);
    // re-apply site+product filters but not month
    const site = document.getElementById('fSite').value;
    const prod = document.getElementById('fProd').value;
    let mr2 = DATA.filter(r=>r.MonthName===mon);
    if (site !== 'Todos') mr2 = mr2.filter(r=>r.SITE===site);
    if (prod !== 'Todos') mr2 = mr2.filter(r=>r.PRODUCT===prod);
    const mm = metrics(mr2);
    trendN.push(+mm.cvrN.toFixed(2));
    trendO.push(+mm.cvrO.toFixed(2));
  }});
  if (chartTrend) chartTrend.destroy();
  chartTrend = new Chart(document.getElementById('chartTrend'), {{
    type: 'line',
    data: {{
      labels: allMonths,
      datasets: [
        {{ label:'CVR New (%)', data:trendN, borderColor:'#4CAF50', backgroundColor:'rgba(76,175,80,.1)', tension:.3, fill:true }},
        {{ label:'CVR Old (%)', data:trendO, borderColor:'#2196F3', backgroundColor:'rgba(33,150,243,.1)', tension:.3, fill:true }}
      ]
    }},
    options: {{ responsive:true, plugins:{{ legend:{{position:'top'}} }}, scales:{{ y:{{beginAtZero:true}} }} }}
  }});

  // ── Detail table ──────────────────────────────────────────────────────────
  let tbody = `<thead><tr>
    <th>Producto</th>
    <th>Ofertados</th>
    <th>Orig New</th><th>CVR New</th><th>USD New</th>
    <th>Orig Old</th><th>CVR Old</th><th>USD Old</th>
    <th>Lift</th><th>Mix New</th>
  </tr></thead><tbody>`;
  prodMetrics.forEach(x => {{
    const liftDisp = x.lift!=null ? x.lift.toFixed(2)+'x' : '—';
    const liftCls  = x.lift!=null && x.lift>=1 ? 'tag-lift-pos' : 'tag-lift-neg';
    const mix = x.origT>0 ? (x.origN/x.origT*100).toFixed(1)+'%' : '—';
    tbody += `<tr>
      <td><b>${{x.p}}</b></td>
      <td>${{fmt(x.off)}}</td>
      <td><span class="tag-new">${{fmt(x.origN)}}</span></td>
      <td>${{fmtPct(x.cvrN)}}</td>
      <td>${{fmtK(x.usdN)}}</td>
      <td><span class="tag-old">${{fmt(x.origO)}}</span></td>
      <td>${{fmtPct(x.cvrO)}}</td>
      <td>${{fmtK(x.usdO)}}</td>
      <td><span class="${{liftCls}}">${{liftDisp}}</span></td>
      <td>${{mix}}</td>
    </tr>`;
  }});
  // Total row
  const tot = metrics(rows);
  const totLift = tot.lift!=null ? tot.lift.toFixed(2)+'x' : '—';
  const totMix  = tot.origT>0 ? (tot.origN/tot.origT*100).toFixed(1)+'%' : '—';
  tbody += `<tr class="total-row">
    <td>TOTAL</td>
    <td>${{fmt(tot.off)}}</td>
    <td>${{fmt(tot.origN)}}</td><td>${{fmtPct(tot.cvrN)}}</td><td>${{fmtK(tot.usdN)}}</td>
    <td>${{fmt(tot.origO)}}</td><td>${{fmtPct(tot.cvrO)}}</td><td>${{fmtK(tot.usdO)}}</td>
    <td>${{totLift}}</td><td>${{totMix}}</td>
  </tr>`;
  document.getElementById('detailTable').innerHTML = tbody + '</tbody>';
}}

render();
</script>
</body>
</html>"""

with open('C:/Users/criva/newold.html', 'w', encoding='utf-8') as f:
    f.write(html_newold)
print(f'[{datetime.now().strftime("%H:%M:%S")}] HTML generado: C:/Users/criva/newold.html')

# ── 4. Publicar en GitHub Pages ─────────────────────────────────────────────
import subprocess, shutil
repo_dir = 'C:/Users/criva/dashboard-repo'
shutil.copy('C:/Users/criva/dashboard.html', repo_dir + '/index.html')
shutil.copy('C:/Users/criva/originations.html', repo_dir + '/originations.html')
shutil.copy('C:/Users/criva/dashboard_v2.html', repo_dir + '/v2.html')
shutil.copy('C:/Users/criva/newold.html', repo_dir + '/newold.html')
shutil.copy('C:/Users/criva/dashboard_v3.html', repo_dir + '/v3.html')
subprocess.run(['git', '-C', repo_dir, 'add', 'index.html', 'originations.html', 'v2.html', 'v3.html', 'newold.html'], check=True)
subprocess.run(['git', '-C', repo_dir, 'commit', '-m', f'Update {updated_at}'], check=True)
subprocess.run(['git', '-C', repo_dir, 'push'], check=True)
print(f'[{datetime.now().strftime("%H:%M:%S")}] Publicado en GitHub Pages: https://candelariva-coder.github.io/card-summary-dashboard/')

# ── 5. Publicar nueva versión en Grid ────────────────────────────────────────
GRID_DOC_ID = '01KNS2RGY44JBB2X546193YKBR'
try:
    _r = subprocess.run([
        'curl', '-s', '-X', 'POST', 'https://grid.melioffice.com/api/v1/engine/run',
        '-F', f'config={{"skill_version":"3.6.0","doc_id":"{GRID_DOC_ID}","file_new_version":true}}',
        '-F', 'file=@C:/Users/criva/dashboard_v3.html',
    ], capture_output=True, text=True, timeout=120)
    import json as _json
    _res = _json.loads(_r.stdout)
    if _res.get('ok'):
        print(f'[{datetime.now().strftime("%H:%M:%S")}] Publicado en Grid v{_res.get("version")}: {_res.get("view_url")}')
    else:
        print(f'[{datetime.now().strftime("%H:%M:%S")}] Grid error: {_r.stdout[:300]}')
except Exception as _e:
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Grid upload fallido: {_e}')
