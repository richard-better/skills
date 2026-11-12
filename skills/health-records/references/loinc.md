# Finding a LOINC code

The merge fills LOINC from `analytes.csv` when the unit matches. For a test it does not know,
search by analyte name only:

```
https://clinicaltables.nlm.nih.gov/api/loinc_items/v3/search?terms=<analyte>&df=LOINC_NUM,LONG_COMMON_NAME
```

Pick the code whose property matches the unit (Moles/volume for mmol/L, Mass/volume for mg/dL)
and whose method matches the report, and pass it in the row's `loinc` column. Leave it empty when
unsure: the analyte table does the same where the code depends on the method, such as eGFR.
