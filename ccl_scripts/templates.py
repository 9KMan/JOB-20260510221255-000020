"""CCL script templates for HHSC EHR migration."""

HL7_ORDER_TEMPLATE = """
/******************************************************************************
 * CCL Script: extract_orders_psd
 * Schema: PSD
 * Purpose: Extract ORDER_PROC and SPECIMEN records for HL7 outbound
 ******************************************************************************/

SELECT o.ORDER_ID,
       o.PATIENT_ID,
       o.ORDER_TYPE_CD,
       o.ORDER_STATUS_CD,
       o.ORDERING_PROVIDER_ID,
       o.ORDER_START_DT_TM,
       o.ORDER_END_DT_TM,
       o.RESULT_STATUS_CD,
       s.SPECIMEN_ID,
       s.SPECIMEN_TYPE_CD,
       s.COLLECT_DT_TM,
       s.RECEIVE_DT_TM
FROM ORDER_PROC o
LEFT JOIN SPECIMEN s ON o.ORDER_ID = s.ORDER_ID
WHERE o.ORDER_START_DT_TM >= :start_date
  AND o.ORDER_START_DT_TM < :end_date
ORDER BY o.ORDER_START_DT_TM;
"""

HL7_RESPIRATORY_TEMPLATE = """
/******************************************************************************
 * CCL Script: extract_respiratory_results
 * Schema: PSD
 * Purpose: Extract RESPIRATORY results for clinical reporting
 ******************************************************************************/

SELECT r.RESULT_ID,
       r.PATIENT_ID,
       r.ORDER_ID,
       r.RESULT_TYPE_CD,
       r.RESULT_DT_TM,
       r.VALUE,
       r.UNITS,
       r.NORMAL_RANGE,
       r.ABNORMAL_IND
FROM RESPIRATORY r
WHERE r.RESULT_DT_TM >= :start_date
  AND r.RESULT_DT_TM < :end_date
ORDER BY r.RESULT_DT_TM;
"""

CDO_ORG_HIERARCHY_TEMPLATE = """
/******************************************************************************
 * CCL Script: extract_organizational_hierarchy
 * Schema: CDO
 * Purpose: Extract organizational structure for facility mapping
 ******************************************************************************/

SELECT ser.SER_ID,
       ser.SER_NAME,
       ser.SER_TYPE_CD,
       dep.DEP_ID,
       dep.DEP_NAME,
       dep.DEP_TYPE_CD,
       emp.EMP_ID,
       emp.EMP_NAME,
       emp.EMP_TYPE_CD
FROM CLARITY_SER ser
LEFT JOIN CLARITY_DEP dep ON ser.SER_ID = dep.SER_ID
LEFT JOIN CLARITY_EMP emp ON dep.DEP_ID = emp.DEP_ID
WHERE ser.SER_ID >= :start_ser_id
ORDER BY ser.SER_ID, dep.DEP_ID;
"""

HSD_VISIT_ENCOUNTER_TEMPLATE = """
/******************************************************************************
 * CCL Script: extract_visit_encounters
 * Schema: HSD
 * Purpose: Extract visit and encounter data for care continuity
 ******************************************************************************/

SELECT v.VISIT_ID,
       v.PATIENT_ID,
       v.ADMIT_DT_TM,
       v.DISCH_DT_TM,
       v.VISIT_TYPE_CD,
       v.ACCOMMODATION_CD,
       r.ORDER_ID,
       r.ORDER_STATUS_CD,
       m.ORDER_MISC_ID,
       m.MISC_TYPE_CD
FROM PATIENT_VISIT v
LEFT JOIN ORDER_REC r ON v.VISIT_ID = r.VISIT_ID
LEFT JOIN ORDER_MISC m ON v.VISIT_ID = m.VISIT_ID
WHERE v.ADMIT_DT_TM >= :start_date
  AND v.ADMIT_DT_TM < :end_date
ORDER BY v.ADMIT_DT_TM;
"""

ARK_PATIENT_DEMOGRAPHICS_TEMPLATE = """
/******************************************************************************
 * CCL Script: extract_patient_demographics
 * Schema: ARK
 * Purpose: Extract patient demographics, allergies, and diagnoses
 ******************************************************************************/

SELECT p.PATIENT_ID,
       p.FIRST_NAME,
       p.LAST_NAME,
       p.DOB,
       p.SEX_CD,
       p.MARITAL_STATUS_CD,
       p.ADDRESS_LINE_1,
       p.CITY,
       p.STATE_CD,
       p.ZIP_CD,
       a.ALLERGY_ID,
       a.ALLERGY_TYPE_CD,
       a.ALLERGY_CD,
       a.SEVERITY_CD,
       d.DIAGNOSIS_ID,
       d.DIAGNOSIS_CD,
       d.DIAGNOSIS_TYPE_CD,
       d.ONSET_DT_TM
FROM PATIENT p
LEFT JOIN PATIENT_ALLERGY a ON p.PATIENT_ID = a.PATIENT_ID
LEFT JOIN PATIENT_DIAGNOSIS d ON p.PATIENT_ID = d.PATIENT_ID
WHERE p.PATIENT_ID >= :start_patient_id
ORDER BY p.PATIENT_ID;
"""

FIN_BILLING_ACCOUNTS_TEMPLATE = """
/******************************************************************************
 * CCL Script: extract_billing_accounts
 * Schema: FIN
 * Purpose: Extract billing accounts and payments for AR reconciliation
 ******************************************************************************/

SELECT a.ACCOUNT_ID,
       a.PATIENT_ID,
       a.ACCOUNT_TYPE_CD,
       a.ACCOUNT_STATUS_CD,
       a.BALANCE_AMT,
       a.CREATE_DT_TM,
       ar.AR_ID,
       ar.AR_TYPE_CD,
       ar.AMOUNT,
       py.PAYMENT_ID,
       py.PAYMENT_DT_TM,
       py.PAYMENT_AMT,
       py.PAYMENT_METHOD_CD
FROM ACCOUNT a
LEFT JOIN PB_AR ar ON a.ACCOUNT_ID = ar.ACCOUNT_ID
LEFT JOIN GB_PAYMENT py ON a.ACCOUNT_ID = py.ACCOUNT_ID
WHERE a.CREATE_DT_TM >= :start_date
  AND a.CREATE_DT_TM < :end_date
ORDER BY a.CREATE_DT_TM;
"""

CCL_SCRIPT_BODIES = {
    "extract_orders_psd": HL7_ORDER_TEMPLATE,
    "extract_respiratory_results": HL7_RESPIRATORY_TEMPLATE,
    "extract_organizational_hierarchy": CDO_ORG_HIERARCHY_TEMPLATE,
    "extract_visit_encounters": HSD_VISIT_ENCOUNTER_TEMPLATE,
    "extract_patient_demographics": ARK_PATIENT_DEMOGRAPHICS_TEMPLATE,
    "extract_billing_accounts": FIN_BILLING_ACCOUNTS_TEMPLATE,
}
