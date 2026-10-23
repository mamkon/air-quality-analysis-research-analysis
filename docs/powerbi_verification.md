# Native Power BI verification

- Generated a native `.pbip` project with PBIR report definitions and a TMSL import model.
- Seven editable pages, 23 tables, six relationships and 40 DAX measures.
- All 88 schema-bearing native files pass Microsoft's official JSON schemas.
- The full Python test suite passes 96 tests. New tests verify native project references,
  all page definitions, unavailable AQHI handling and scenario prediction limits against
  statsmodels OLS for Toronto, Ottawa and Kenora.
- No machine-specific file path or credentials are embedded in the native semantic model.
  Imported rows are a portable, dated snapshot with separate CSV evidence.

## Desktop verification limit

The installed Power BI Desktop remained on its blank Untitled workspace when opening
the `.pbip` and the report's `definition.pbir`. No usable report canvas or import result
could be confirmed in this environment. Schema validation and arithmetic tests do not
replace a native rendering check. A standalone `.pbix` has therefore not been produced
or claimed as verified. Open the project in a working current Power BI Desktop, select
Refresh to import the embedded snapshot, verify its pages, and save as `.pbix` if needed.

This record does not attribute the blank workspace to a specific Windows or Power BI
fault because no diagnostic message establishing a cause was observed.
