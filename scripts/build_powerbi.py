"""Build a portable native Power BI project from the reproducible Python analysis.

The Power BI report is a dated research snapshot, not an unattended live service.
Embedded import partitions avoid machine-specific paths and credentials. Rebuild
after refreshing API snapshots to update the native model and its CSV evidence.
"""
import base64
import json
import sys
import uuid
import zlib
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.api_clients import baseline  # noqa: E402
from src.config import LOCATION_DETAILS, LOCATIONS  # noqa: E402
from src.context import aqhi_table, load  # noqa: E402
from src.decisions import matrix, risk  # noqa: E402
from src.modeling import (  # noqa: E402
    baseline_frame,
    baseline_sensitivity,
    fit,
    metrics,
    missing_comparison,
    normality,
    predict,
    vif,
)

OUT = ROOT / "powerbi"
NAME = "AIR QUALITY ANALYSIS RESEARCH ANALYSIS"
REPORT = OUT / f"{NAME}.Report"
MODEL = OUT / f"{NAME}.SemanticModel"
SCHEMA = "https://developer.microsoft.com/json-schemas/fabric"
MEASURES = "LocationSummary"
TABLES: dict[str, pd.DataFrame] = {}


def write_json(path: Path, value: dict) -> None:
    """Write deterministic UTF-8 JSON with no nonstandard NaN values."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")


def prepare_data() -> None:
    """Export all locations, real validation predictions and model uncertainty inputs."""
    summaries, histories, validations, forecasts, parameters, sources = [], [], [], [], [], []
    for city in LOCATIONS:
        ctx = load(city, True)
        model, past, validation = ctx["model"], ctx["past"], ctx["evaluation"]
        future = predict(model, ctx["future"]) if len(ctx["future"]) else pd.DataFrame()
        ozone = ctx["ozone_hourly"].loc[lambda f: f.index <= ctx["now"]].dropna()
        aqhi = aqhi_table(ctx["sources"]["Local AQHI observations"])
        latest = aqhi.sort_values("observation_datetime").iloc[-1] if len(aqhi) else {}
        value = float(future.predicted.iloc[0]) if len(future) else None
        summaries.append({"Location": city, "LatestOzone": float(ozone.ozone.iloc[-1] / 1.96) if len(ozone) else None,
            "LatestOzoneTime": ozone.index[-1].isoformat() if len(ozone) else "Unavailable",
            "ForecastOzone": value, "ForecastDate": str(future.index[0].date()) if len(future) else "Unavailable",
            "RiskTier": risk(value) if value is not None else "Unavailable", "AQHI": latest.get("aqhi"),
            "AQHITime": latest.get("observation_datetime", "Unavailable"), "AdjustedR2": model.rsquared_adj,
            "R2": model.rsquared, "HeldoutRMSE": float(np.sqrt(np.mean(validation.residual**2))),
            "TrainingDays": len(past), "HeldoutDays": len(validation),
            "TrainingStart": str(past.index.min().date()), "TrainingEnd": str(past.index.max().date()),
            "MaxVIF": vif(past).VIF.max(), "ResidualShapiroP": stats.shapiro(model.resid).pvalue})
        for day, row in past.join(predict(model, past)).iterrows():
            histories.append({"Location": city, "Date": str(day.date()), "ActualOzone": row.ozone,
                "FittedOzone": row.predicted, "Temperature": row.temp, "Wind": row.wind,
                "SolarEnergy": row.solar})
        for day, row in validation.iterrows():
            validations.append({"Location": city, "Date": str(day.date()), "ActualOzone": row.ozone,
                "PredictedOzone": row.predicted, "Lower95": row.lower, "Upper95": row.upper,
                "Residual": row.residual, "RollingRMSE": row.rolling_rmse})
        for day, row in future.iterrows():
            forecasts.append({"Location": city, "Date": str(day.date()), "PredictedOzone": row.predicted,
                              "Lower95": row.lower, "Upper95": row.upper})
        # model exog order is const, temp, wind, solar. Store the exact inverse
        # information matrix so native DAX can compute scenario prediction limits.
        inverse = np.asarray(model.normalized_cov_params)
        record = {"Location": city, "Intercept": model.params["const"], "TempCoef": model.params["temp"],
            "WindCoef": model.params["wind"], "SolarCoef": model.params["solar"],
            "ResidualSigma": np.sqrt(model.mse_resid), "TCritical": stats.t.ppf(0.975, model.df_resid),
            "MinTemp": past.temp.min(), "MaxTemp": past.temp.max(), "MinWind": past.wind.min(),
            "MaxWind": past.wind.max(), "MinSolar": past.solar.min(), "MaxSolar": past.solar.max()}
        record.update({f"Inv{i}{j}": inverse[i, j] for i in range(4) for j in range(i, 4)})
        parameters.append(record)
        for source, envelope in ctx["sources"].items():
            sources.append({"Location": city, "Source": source, "RetrievedUTC": envelope["retrieved_at"] or "Not configured",
                            "URL": envelope["source"]})
    TABLES["Locations"] = pd.DataFrame([{"Location": city, "Region": p["region"], "Latitude": p["latitude"],
        "Longitude": p["longitude"], "TimeZone": p["timezone"], "AQHIArea": p["aqhi_id"] or "Not configured"}
        for city, p in LOCATION_DETAILS.items()])
    for name, rows in [("LocationSummary", summaries), ("History", histories), ("Validation", validations),
                       ("Forecast", forecasts), ("ModelParameters", parameters), ("Provenance", sources)]:
        TABLES[name] = pd.DataFrame(rows)
    raw = baseline_frame(baseline(True))
    clean = raw.dropna()
    base_model = fit(clean)
    TABLES["Baseline"] = clean.assign(Index=np.arange(1, len(clean) + 1),
                                     Fitted=base_model.fittedvalues, Residual=base_model.resid).reset_index(drop=True)
    TABLES["BaselineModels"] = pd.DataFrame([{"Model": label, "ResponseScale": scale, **metrics(model)}
        for label, scale, model in [("Simple OLS", "ppb", fit(clean, ["temp"])),
                                   ("Multiple OLS", "ppb", base_model), ("Log response OLS", "log(ppb)", fit(clean, log=True))]])
    TABLES["MissingData"] = missing_comparison(raw)
    TABLES["BaselineSensitivity"] = baseline_sensitivity(raw)
    TABLES["Normality"] = normality(clean)
    TABLES["BaselineVIF"] = vif(clean)
    TABLES["BaselineCoefficients"] = pd.DataFrame({"Term": base_model.params.index,
        "Coefficient": base_model.params.values, "PValue": base_model.pvalues.values})
    correlations = []
    for method in ["pearson", "spearman"]:
        corr = clean.corr(method=method)
        for x in clean:
            for y in clean:
                correlations.append({"Method": method.title(), "VariableX": x, "VariableY": y, "Correlation": corr.loc[x, y]})
    TABLES["Correlations"] = pd.DataFrame(correlations)
    TABLES["Decisions"] = matrix()
    TABLES["Threshold"] = pd.DataFrame({"Value": range(20, 101)})
    TABLES["ScenarioTemperature"] = pd.DataFrame({"Value": range(-15, 46)})
    TABLES["ScenarioWind"] = pd.DataFrame({"Value": range(0, 61)})
    TABLES["ScenarioSolar"] = pd.DataFrame({"Value": range(0, 451, 10)})
    TABLES["ScenarioPresets"] = pd.DataFrame([
        {"Scenario": "Hot, calm, sunny", "Temperature": 33, "Wind": 5, "Solar": 300},
        {"Scenario": "Cool and windy", "Temperature": 17, "Wind": 25, "Solar": 140},
        {"Scenario": "Typical summer day", "Temperature": 26, "Wind": 13, "Solar": 230}])
    TABLES["ConfusionLabels"] = pd.DataFrame([
        {"Actual": "Event", "Predicted": "Alert", "Outcome": "TP"},
        {"Actual": "Event", "Predicted": "No alert", "Outcome": "FN"},
        {"Actual": "Non-event", "Predicted": "Alert", "Outcome": "FP"},
        {"Actual": "Non-event", "Predicted": "No alert", "Outcome": "TN"}])
    TABLES["Audience"] = pd.DataFrame([
        ["Public health", "Advisory preparation", "Public Health Ontario; Ontario health units", "Health data analyst", "Decision Framework"],
        ["Hospitals", "Respiratory capacity planning", "UHN; The Ottawa Hospital; London Health Sciences Centre", "Clinical / BI analyst", "Ontario Model"],
        ["Government / environment", "Monitoring and exposure planning", "ECCC; Ontario MECP", "Environmental analyst", "Overview"],
        ["ESG consulting", "Environmental reporting", "WSP; Deloitte", "Sustainability analyst", "Historical Method"],
        ["Insurance", "Environmental risk screening", "Intact; Manulife", "Risk analyst", "Limitations"],
        ["Energy / utilities", "Weather-linked operations", "Hydro One; Ontario utilities", "Operations analyst", "What-If Simulator"],
        ["Planning / transit", "Outdoor exposure planning", "Ontario municipalities; Metrolinx", "Planning analyst", "Decision Framework"],
        ["Pharmacy", "Demand preparedness", "Ontario pharmacy networks", "Supply-chain analyst", "Overview"]],
        columns=["Industry", "Decision", "IllustrativeEmployers", "JobTitles", "EvidencePage"])
    for name, frame in TABLES.items():
        path = OUT / "data" / f"{name}.csv"
        path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(path, index=False)
    write_json(OUT / "data" / "manifest.json", {"generatedUTC": datetime.now(timezone.utc).isoformat(),
        "mode": "Dated embedded research snapshot; not unattended live data", "locations": len(LOCATIONS),
        "tables": {name: len(frame) for name, frame in TABLES.items()},
        "source": "Real timestamped API snapshots in data/sample; Python OLS from src/modeling.py"})


def dax_measures() -> list[dict]:
    """Native DAX supports location filtering, alert trade-offs and scenario limits."""
    expressions = {
        "Selected Location": "SELECTEDVALUE(Locations[Location], \"Select one Ontario location\")",
        "Snapshot Forecast Date": 'SELECTEDVALUE(LocationSummary[ForecastDate], "Select one location")',
        "Latest Ozone ppb": "IF(HASONEVALUE(Locations[Location]), MAX(LocationSummary[LatestOzone]))",
        "Forecast Ozone ppb": "IF(HASONEVALUE(Locations[Location]), MAX(LocationSummary[ForecastOzone]))",
        "Illustrative Risk Tier": 'SELECTEDVALUE(LocationSummary[RiskTier], "Select one location")',
        "Official AQHI": "IF(HASONEVALUE(Locations[Location]), MAX(LocationSummary[AQHI]))",
        "Model Adjusted R2": "IF(HASONEVALUE(Locations[Location]), MAX(LocationSummary[AdjustedR2]))",
        "Heldout RMSE ppb": "IF(HASONEVALUE(Locations[Location]), MAX(LocationSummary[HeldoutRMSE]))",
        "Training Days": "IF(HASONEVALUE(Locations[Location]), MAX(LocationSummary[TrainingDays]))",
        "Validation Days": "COUNTROWS(Validation)",
        "Forecast Mean": "IF(HASONEVALUE(Locations[Location]), AVERAGE(Forecast[PredictedOzone]))",
        "Forecast Lower 95": "IF(HASONEVALUE(Locations[Location]), AVERAGE(Forecast[Lower95]))",
        "Forecast Upper 95": "IF(HASONEVALUE(Locations[Location]), AVERAGE(Forecast[Upper95]))",
        "Reference Ozone": "IF(HASONEVALUE(Locations[Location]), AVERAGE(Validation[ActualOzone]))",
        "Heldout Prediction": "IF(HASONEVALUE(Locations[Location]), AVERAGE(Validation[PredictedOzone]))",
        "Rolling RMSE": "IF(HASONEVALUE(Locations[Location]), AVERAGE(Validation[RollingRMSE]))",
        "Residual ppb": "AVERAGE(Validation[Residual])",
        "High Cutoff ppb": "SELECTEDVALUE(Threshold[Value], 60)",
        "True Positives": "COUNTROWS(FILTER(Validation, Validation[ActualOzone] >= [High Cutoff ppb] && Validation[PredictedOzone] >= [High Cutoff ppb]))",
        "False Positives": "COUNTROWS(FILTER(Validation, Validation[ActualOzone] < [High Cutoff ppb] && Validation[PredictedOzone] >= [High Cutoff ppb]))",
        "False Negatives": "COUNTROWS(FILTER(Validation, Validation[ActualOzone] >= [High Cutoff ppb] && Validation[PredictedOzone] < [High Cutoff ppb]))",
        "True Negatives": "COUNTROWS(FILTER(Validation, Validation[ActualOzone] < [High Cutoff ppb] && Validation[PredictedOzone] < [High Cutoff ppb]))",
        "Precision": "DIVIDE([True Positives], [True Positives] + [False Positives])",
        "Recall": "DIVIDE([True Positives], [True Positives] + [False Negatives])",
        "False Alarm Rate": "DIVIDE([False Positives], [False Positives] + [True Negatives])",
        "Missed Event Rate": "DIVIDE([False Negatives], [False Negatives] + [True Positives])",
        "Event Support": "[True Positives] + [False Negatives]",
        "Confusion Count": 'SWITCH(SELECTEDVALUE(ConfusionLabels[Outcome]), "TP", [True Positives], "FP", [False Positives], "FN", [False Negatives], "TN", [True Negatives])',
        "Scenario Temp C": "SELECTEDVALUE(ScenarioTemperature[Value], SELECTEDVALUE(ScenarioPresets[Temperature], 26))",
        "Scenario Wind kmh": "SELECTEDVALUE(ScenarioWind[Value], SELECTEDVALUE(ScenarioPresets[Wind], 13))",
        "Scenario Solar Wm2": "SELECTEDVALUE(ScenarioSolar[Value], SELECTEDVALUE(ScenarioPresets[Solar], 230))",
        "Scenario Prediction ppb": "IF(HASONEVALUE(Locations[Location]), MAX(ModelParameters[Intercept]) + MAX(ModelParameters[TempCoef])*[Scenario Temp C] + MAX(ModelParameters[WindCoef])*[Scenario Wind kmh] + MAX(ModelParameters[SolarCoef])*[Scenario Solar Wm2]*0.0864)",
        "Scenario Half Width": "VAR t = [Scenario Temp C] VAR w = [Scenario Wind kmh] VAR s = [Scenario Solar Wm2]*0.0864 VAR h = MAX(ModelParameters[Inv00]) + 2*t*MAX(ModelParameters[Inv01]) + 2*w*MAX(ModelParameters[Inv02]) + 2*s*MAX(ModelParameters[Inv03]) + t*t*MAX(ModelParameters[Inv11]) + 2*t*w*MAX(ModelParameters[Inv12]) + 2*t*s*MAX(ModelParameters[Inv13]) + w*w*MAX(ModelParameters[Inv22]) + 2*w*s*MAX(ModelParameters[Inv23]) + s*s*MAX(ModelParameters[Inv33]) RETURN IF(HASONEVALUE(Locations[Location]), MAX(ModelParameters[TCritical])*MAX(ModelParameters[ResidualSigma])*SQRT(MAX(0,1+h)))",
        "Scenario Lower 95": "[Scenario Prediction ppb] - [Scenario Half Width]",
        "Scenario Upper 95": "[Scenario Prediction ppb] + [Scenario Half Width]",
        "Scenario Tier": 'VAR p = [Scenario Prediction ppb] RETURN IF(ISBLANK(p), "Select one location", SWITCH(TRUE(), p<0, "Unavailable", p<50, "Good", p<60, "Moderate", p<70, "High", "Very High"))',
        "Scenario Extrapolation": 'IF([Scenario Temp C]<MAX(ModelParameters[MinTemp]) || [Scenario Temp C]>MAX(ModelParameters[MaxTemp]) || [Scenario Wind kmh]<MAX(ModelParameters[MinWind]) || [Scenario Wind kmh]>MAX(ModelParameters[MaxWind]) || [Scenario Solar Wm2]*0.0864<MAX(ModelParameters[MinSolar]) || [Scenario Solar Wm2]*0.0864>MAX(ModelParameters[MaxSolar]), "Outside training range", "Within marginal training ranges")',
        "Baseline Mean Ozone": "AVERAGE(Baseline[ozone])",
        "Baseline Mean Temperature": "AVERAGE(Baseline[temp])",
        "Baseline Residual": "AVERAGE(Baseline[Residual])",
    }
    percent = {"Precision", "Recall", "False Alarm Rate", "Missed Event Rate"}
    for name in ("True Positives", "True Negatives", "False Positives", "False Negatives"):
        expressions[name] = "COALESCE(" + expressions[name] + ", 0)"
    integer = {"Training Days", "Validation Days", "Event Support", "True Positives", "True Negatives", "False Positives", "False Negatives", "Confusion Count"}
    text = {"Selected Location", "Snapshot Forecast Date", "Illustrative Risk Tier", "Scenario Tier", "Scenario Extrapolation"}
    return [{"name": name, "expression": value, **({} if name in text else {"formatString": "0.0%" if name in percent else "0" if name in integer else "0.00"})}
            for name, value in expressions.items()]


def build_model() -> None:
    """Create TMSL import partitions with portable embedded, compressed source rows."""
    tables = []
    for name, frame in TABLES.items():
        numeric = {column for column in frame if pd.api.types.is_numeric_dtype(frame[column])}
        rows = json.loads(frame.to_json(orient="values", double_precision=14))
        compressor = zlib.compressobj(level=9, wbits=-15)
        compressed = compressor.compress(json.dumps(rows, separators=(",", ":")).encode()) + compressor.flush()
        encoded = base64.b64encode(compressed).decode()
        columns = [{"name": column, "dataType": "double" if column in numeric else "string",
                    "sourceColumn": column, "summarizeBy": "none"} for column in frame]
        for column in columns:
            if column["name"] in {"p", "P Value", "BP p", "JB p", "PValue"}:
                column["formatString"] = "0.00E+00"
        header = "{" + ",".join(json.dumps(c, ensure_ascii=False) for c in frame.columns) + "}"
        typing = "{" + ",".join("{" + json.dumps(c, ensure_ascii=False) + ", " + ("type number" if c in numeric else "type text") + "}" for c in frame.columns) + "}"
        expression = ["let", f'    Rows = Json.Document(Binary.Decompress(Binary.FromText("{encoded}", BinaryEncoding.Base64), Compression.Deflate)),',
                      f"    Source = Table.FromRows(Rows, {header}),", f"    Typed = Table.TransformColumnTypes(Source, {typing}, \"en-US\")", "in", "    Typed"]
        table = {"name": name, "columns": columns, "partitions": [{"name": name, "mode": "import", "source": {"type": "m", "expression": expression}}]}
        if name == MEASURES:
            table["measures"] = dax_measures()
        tables.append(table)
    relationships = [{"name": str(uuid.uuid5(uuid.NAMESPACE_URL, "ontario/" + name)), "fromTable": name,
        "fromColumn": "Location", "toTable": "Locations", "toColumn": "Location",
        "crossFilteringBehavior": "oneDirection"} for name in ["LocationSummary", "History", "Validation", "Forecast", "ModelParameters", "Provenance"]]
    write_json(MODEL / "definition.pbism", {"$schema": f"{SCHEMA}/item/semanticModel/definitionProperties/1.0.0/schema.json", "version": "1.0", "settings": {}})
    write_json(MODEL / "model.bim", {"name": NAME, "compatibilityLevel": 1567,
        "model": {"culture": "en-US", "defaultPowerBIDataSourceVersion": "powerBI_V3",
                  "tables": tables, "relationships": relationships,
                  "annotations": [{"name": "PBI_QueryOrder", "value": json.dumps(list(TABLES))}]}})
    (OUT / "measures.dax").write_text("\n\n".join(f"// {m['name']}\n{m['name']} = {m['expression']}" for m in dax_measures()), encoding="utf-8")


def literal(value: str | bool | int) -> dict:
    """Power BI formatting expression literal."""
    text = str(value).lower() if isinstance(value, bool) else str(value) + "D" if isinstance(value, int) else "'" + value.replace("'", "''") + "'"
    return {"expr": {"Literal": {"Value": text}}}


def field(table: str, column: str, measure: bool = False) -> dict:
    """Create a semantic field reference and stable query name."""
    return {"field": {"Measure" if measure else "Column": {"Expression": {"SourceRef": {"Entity": table}}, "Property": column}},
            "queryRef": table + "." + column, "nativeQueryRef": column}


def visual(page: str, name: str, kind: str, x: int, y: int, width: int, height: int,
           title: str = "", roles: dict | None = None, objects: dict | None = None, selected: tuple | None = None) -> None:
    """Write a native PBIR visual with explicit query roles and accessible title."""
    title = " ".join(word if word in {"and", "or", "in"} else word[:1].upper() + word[1:] for word in title.split(" "))
    config = {"visualType": kind, "drillFilterOtherVisuals": True}
    if roles:
        config["query"] = {"queryState": {role: {"projections": projections} for role, projections in roles.items()}}
    config["visualContainerObjects"] = {
        "title": [{"properties": {"show": literal(bool(title)), "text": literal(title), "fontSize": literal(12),
                                     "fontColor": {"solid": {"color": literal("#15394B")}}}}],
        "background": [{"properties": {"show": literal(True), "color": {"solid": {"color": literal("#FFFFFF")}}, "transparency": literal(0)}}],
        "border": [{"properties": {"show": literal(True), "color": {"solid": {"color": literal("#DCE6EB")}}, "radius": literal(8)}}]}
    if objects:
        config["objects"] = objects
    content = {"$schema": f"{SCHEMA}/item/report/definition/visualContainer/2.5.0/schema.json", "name": name,
               "position": {"x": x, "y": y, "z": 0, "width": width, "height": height, "tabOrder": y * 10 + x}, "visual": config}
    if selected:
        table, column, value = selected
        source = {"Column": {"Expression": {"SourceRef": {"Source": "s"}}, "Property": column}}
        selection_filter = {"Version": 2, "From": [{"Name": "s", "Entity": table, "Type": 0}],
            "Where": [{"Condition": {"In": {"Expressions": [source], "Values": [[{"Literal": {"Value": "'" + str(value) + "'" if isinstance(value, str) else str(value) + "L"}}]]}}}]}
        config.setdefault("objects", {})["general"] = [{"properties": {"filter": {"filter": selection_filter}}}]
    write_json(REPORT / "definition" / "pages" / page / "visuals" / name / "visual.json", content)


def textbox(page: str, name: str, text: str, x: int, y: int, width: int, height: int, size: int = 12) -> None:
    """Native editable text, not a screenshot of the Streamlit application."""
    paragraphs = [{"textRuns": [{"value": line, "textStyle": {"fontSize": f"{size}pt", "fontFamily": "Segoe UI", "color": "#15394B"}}]} for line in text.split("\n")]
    visual(page, name, "textbox", x, y, width, height, objects={"general": [{"properties": {"paragraphs": paragraphs}}]})


def slicer(page: str, name: str, table: str, column: str, x: int, y: int, width: int, title: str, default: str | int | None = None) -> None:
    """Single-select native slicer; clear selection allows preset defaults."""
    visual(page, name, "slicer", x, y, width, 76, title, {"Values": [field(table, column)]},
           {"data": [{"properties": {"mode": literal("Dropdown")}}],
            "selection": [{"properties": {"singleSelect": literal(True), "strictSingleSelect": literal(False)}}]},
           (table, column, default) if default is not None else None)


def card(page: str, name: str, measure: str, x: int, y: int, width: int, title: str) -> None:
    """Native DAX-bound KPI card."""
    visual(page, name, "card", x, y, width, 100, title, {"Values": [field(MEASURES, measure, True)]})


def table_visual(page: str, name: str, table: str, columns: list[str], x: int, y: int, width: int, height: int, title: str) -> None:
    """Native table with selectable semantic columns."""
    visual(page, name, "tableEx", x, y, width, height, title, {"Values": [field(table, c) for c in columns]})


def page_frame(code: str, title: str, subtitle: str, location: bool = False) -> None:
    """Set page dimensions, source context and optional Ontario selectors."""
    write_json(REPORT / "definition" / "pages" / code / "page.json", {
        "$schema": f"{SCHEMA}/item/report/definition/page/2.0.0/schema.json", "name": code,
        "displayName": {"Overview": "Overview", "HistoricalMethod": "Historical Method", "OntarioModel": "Ontario Model", "DecisionFramework": "Decision Framework", "WhatIfSimulator": "What-If Simulator", "WhoUsesThis": "Who Uses This", "Limitations": "Limitations"}[code], "displayOption": "FitToPage", "height": 900, "width": 1280,
        "objects": {"background": [{"properties": {"color": {"solid": {"color": literal("#F2F6F9")}}, "transparency": literal(0)}}]}})
    textbox(code, "Heading", title, 24, 14, 1232, 58, 25)
    textbox(code, "Subtitle", subtitle, 24, 74, 1232, 54, 11)
    textbox(code, "Footer", "Mercy Mamkon Oyeleke | Data Analytics & Business Intelligence Consultant\nResearch snapshot from timestamped Open-Meteo / CAMS and ECCC sources. Illustrative planning; not a health advisory.", 24, 836, 1232, 60, 9)
    if location:
        slicer(code, "RegionSelector", "Locations", "Region", 24, 140, 330, "Ontario region")
        slicer(code, "LocationSelector", "Locations", "Location", 370, 140, 330, "Ontario location", "Toronto")


def build_report() -> None:
    """Create seven editable native report pages, including DAX what-if controls."""
    codes = ["Overview", "HistoricalMethod", "OntarioModel", "DecisionFramework", "WhatIfSimulator", "WhoUsesThis", "Limitations"]
    write_json(OUT / f"{NAME}.pbip", {"$schema": f"{SCHEMA}/pbip/pbipProperties/1.0.0/schema.json", "version": "1.0",
        "artifacts": [{"report": {"path": REPORT.name}}], "settings": {"enableAutoRecovery": True}})
    write_json(REPORT / "definition.pbir", {"$schema": f"{SCHEMA}/item/report/definitionProperties/2.0.0/schema.json",
        "version": "4.0", "datasetReference": {"byPath": {"path": "../" + MODEL.name}}})
    write_json(REPORT / "definition" / "version.json", {"$schema": f"{SCHEMA}/item/report/definition/versionMetadata/1.0.0/schema.json", "version": "2.0.0"})
    write_json(REPORT / "definition" / "pages" / "pages.json", {"$schema": f"{SCHEMA}/item/report/definition/pagesMetadata/1.0.0/schema.json", "pageOrder": codes, "activePageName": "Overview"})
    write_json(REPORT / "definition" / "report.json", {"$schema":"https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.2.0/schema.json","themeCollection":{"baseTheme":{"name":"CY26SU04","reportVersionAtImport":{"visual":"2.8.0","report":"3.2.0","page":"2.3.1"},"type":"SharedResources"}},"objects":{"section":[{"properties":{"verticalAlignment":{"expr":{"Literal":{"Value":"'Top'"}}}}}]},"resourcePackages":[{"name":"SharedResources","type":"SharedResources","items":[{"name":"CY26SU04","path":"BaseThemes/CY26SU04.json","type":"BaseTheme"}]}],"settings":{"useStylableVisualContainerHeader":True,"exportDataMode":"AllowSummarized","defaultDrillFilterOtherVisuals":True,"allowChangeFilterTypes":True,"useEnhancedTooltips":True,"useDefaultAggregateDisplayName":True}})
    page_frame("Overview", "Ontario Air Quality | Research Overview", "47 Ontario locations • Select one location • Forecast and source dates remain visible • Native Power BI / DAX", True)
    card("Overview", "ForecastDate", "Snapshot Forecast Date", 720, 140, 536, "Forecast date (dated snapshot)")
    for i, (measure, title) in enumerate([("Latest Ozone ppb", "Latest reference ozone (ppb)"), ("Forecast Ozone ppb", "Forecast afternoon ozone (ppb)"), ("Illustrative Risk Tier", "Illustrative ozone tier"), ("Official AQHI", "Local ECCC AQHI"), ("Model Adjusted R2", "Model adjusted R²")]):
        card("Overview", "KPI" + str(i), measure, 24 + i * 248, 250, 240, title)
    visual("Overview", "ForecastChart", "lineChart", 24, 374, 850, 380, "Weather-based afternoon ozone outlook (ppb) with 95% bounds",
           {"Category": [field("Forecast", "Date")], "Y": [field(MEASURES, m, True) for m in ["Forecast Mean", "Forecast Lower 95", "Forecast Upper 95"]]})
    table_visual("Overview", "SourceStatus", "LocationSummary", ["Location", "LatestOzoneTime", "AQHITime", "TrainingEnd"], 894, 374, 362, 380, "Source age and training window")
    textbox("Overview", "Takeaway", "Takeaway: read prediction bounds alongside the source dates. Blank AQHI means no configured official local area, never a substitute city's value.", 24, 770, 1232, 56)
    page_frame("HistoricalMethod", "Historical Method | NYC 1973", "1973 data, used to demonstrate method only. Original °F / mph / narrow-band Langleys units. This model never scores modern Ontario inputs.")
    table_visual("HistoricalMethod", "MissingComparison", "MissingData", list(TABLES["MissingData"]), 24, 145, 600, 190, "Missing-data sensitivity: ozone variability and correlation")
    table_visual("HistoricalMethod", "ModelComparison", "BaselineModels", list(TABLES["BaselineModels"]), 648, 145, 608, 190, "Simple, multiple and log-response OLS (scales differ)")
    visual("HistoricalMethod", "BaselineScatter", "scatterChart", 24, 355, 600, 280, "Temperature (°F) versus ozone (ppb), complete cases",
           {"Category": [field("Baseline", "Index")], "X": [field(MEASURES, "Baseline Mean Temperature", True)], "Y": [field(MEASURES, "Baseline Mean Ozone", True)]})
    table_visual("HistoricalMethod", "Correlation", "Correlations", ["Method", "VariableX", "VariableY", "Correlation"], 648, 355, 608, 280, "Pearson linear and Spearman rank associations")
    table_visual("HistoricalMethod", "Coefficients", "BaselineCoefficients", list(TABLES["BaselineCoefficients"]), 24, 652, 600, 150, "Multiple OLS coefficients: associations, not causal effects")
    table_visual("HistoricalMethod", "Normality", "Normality", list(TABLES["Normality"]), 648, 652, 608, 150, "Shapiro–Wilk: a large p-value does not prove normality")
    page_frame("OntarioModel", "Ontario Model | Chronological Validation", "Each Ontario location is fitted separately. Latest quarter held out chronologically; CAMS is modelled reference ozone, not station observations.", True)
    card("OntarioModel", "RMSE", "Heldout RMSE ppb", 720, 140, 250, "Held-out RMSE (ppb)")
    card("OntarioModel", "Support", "Training Days", 990, 140, 266, "Complete training days")
    visual("OntarioModel", "ValidationChart", "lineChart", 24, 260, 780, 330, "Held-out reference versus prediction (ppb)",
           {"Category": [field("Validation", "Date")], "Y": [field(MEASURES, m, True) for m in ["Reference Ozone", "Heldout Prediction"]]})
    visual("OntarioModel", "ResidualChart", "scatterChart", 826, 260, 430, 330, "Residual (ppb) versus prediction (ppb)",
           {"Category": [field("Validation", "Date")], "X": [field(MEASURES, "Heldout Prediction", True)], "Y": [field(MEASURES, "Residual ppb", True)]})
    visual("OntarioModel", "RollingError", "lineChart", 24, 612, 1232, 190, "Rolling seven-day held-out RMSE (ppb)",
           {"Category": [field("Validation", "Date")], "Y": [field(MEASURES, "Rolling RMSE", True)]})
    page_frame("DecisionFramework", "Decision Framework | Alert Trade-offs", "Illustrative afternoon-mean tiers are not eight-hour compliance standards. CAAQS 2025: 60 ppb; EPA: 70 ppb, with multi-year measurement rules.", True)
    slicer("DecisionFramework", "ThresholdSelector", "Threshold", "Value", 720, 140, 250, "Alert cutoff (ppb)", 60)
    card("DecisionFramework", "EventSupport", "Event Support", 990, 140, 266, "Held-out event days")
    for i, (measure, title) in enumerate([("Precision", "Precision"), ("Recall", "Recall"), ("False Alarm Rate", "False-alarm rate: FP/(FP+TN)"), ("Missed Event Rate", "Missed-event rate")]):
        card("DecisionFramework", "AlertMetric" + str(i), measure, 24 + i * 310, 254, 302, title)
    visual("DecisionFramework", "ConfusionMatrix", "pivotTable", 24, 378, 470, 300, "Held-out confusion matrix (counts)",
           {"Rows": [field("ConfusionLabels", "Actual")], "Columns": [field("ConfusionLabels", "Predicted")], "Values": [field(MEASURES, "Confusion Count", True)]})
    table_visual("DecisionFramework", "DecisionMatrix", "Decisions", list(TABLES["Decisions"]), 518, 378, 738, 300, "Accountable actions and success measures")
    textbox("DecisionFramework", "Tradeoff", "Favour recall during screening design: missed events can harm vulnerable groups. Balance this with alert fatigue and operational costs. Undefined recall means no event support, not a safe model. Explore thresholds here; validate policy choices independently with public-health partners.", 24, 702, 1232, 100)
    page_frame("WhatIfSimulator", "What-If Simulator | Weather Scenarios", "Illustrative, not a health advisory. Native DAX uses the selected modern model and its OLS prediction interval. Radiation is a full-day mean W/m².", True)
    slicer("WhatIfSimulator", "Preset", "ScenarioPresets", "Scenario", 720, 140, 536, "Preset scenario", "Typical summer day")
    for i, (table, title) in enumerate([("ScenarioTemperature", "Override max temperature (°C)"), ("ScenarioWind", "Override daily mean wind (km/h)"), ("ScenarioSolar", "Override full-day mean solar (W/m²)")]):
        slicer("WhatIfSimulator", "ScenarioControl" + str(i), table, "Value", 24 + i * 414, 258, 404, title)
    for i, (measure, title) in enumerate([("Scenario Prediction ppb", "Predicted ozone (ppb)"), ("Scenario Lower 95", "95% prediction lower (ppb)"), ("Scenario Upper 95", "95% prediction upper (ppb)"), ("Scenario Tier", "Illustrative tier")]):
        card("WhatIfSimulator", "ScenarioResult" + str(i), measure, 24 + i * 310, 382, 302, title)
    for i, (measure, title) in enumerate([("Scenario Temp C", "Effective temperature (°C)"), ("Scenario Wind kmh", "Effective wind (km/h)"), ("Scenario Solar Wm2", "Effective full-day solar (W/m²)")]):
        card("WhatIfSimulator", "ScenarioInput" + str(i), measure, 24 + i * 414, 522, 404, title)
    card("WhatIfSimulator", "Extrapolation", "Scenario Extrapolation", 24, 660, 1232, "Training-range check")
    textbox("WhatIfSimulator", "ScenarioExplanation", "Clear a manual override to use the preset value. Radiation is integrated by ×0.0864 into MJ/m²/day. Intervals remain raw, including negative lower bounds; weather forecast and model-reference uncertainty are excluded.", 24, 770, 1232, 56)
    page_frame("WhoUsesThis", "Who Uses This | Evidence of Analytical Skills", "Public health and hospitals lead the use cases. Employers are illustrative examples, not endorsements or advertised vacancies.")
    table_visual("WhoUsesThis", "AudienceTable", "Audience", list(TABLES["Audience"]), 24, 150, 1232, 570, "Industries, decisions, job titles and portfolio evidence")
    textbox("WhoUsesThis", "AudienceTakeaway", "Takeaway: the portfolio demonstrates data preparation, interpretable modelling, uncertainty communication, operational decision design and native Power BI / DAX authoring.", 24, 742, 1232, 76)
    page_frame("Limitations", "Limitations | Source Transparency & Next Steps", "Research illustration. Official ECCC AQHI and local public-health guidance take precedence over this exploratory model.")
    limitations = "Association is not causation; emissions, traffic, humidity and transport are omitted.\nCAMS ozone is modelled reference data, not station-level observed truth.\nShort seasonal windows and retrospective reanalysis do not establish year-round forecast skill.\nOzone conversion assumes 25°C and 1 atm; afternoon mean is not an eight-hour maximum.\nOLS prediction bounds rely on model assumptions and omit weather/CAMS uncertainty.\nAQHI is unavailable for six additional northern communities; no proxy city is substituted.\nPower BI contains an embedded dated snapshot. Refresh Python sources, rebuild this project and reopen it to update data.\nNext: ECCC station validation, rolling-origin forecasts, governed ER-outcome linkage, SARIMAX and gradient boosting."
    textbox("Limitations", "LimitationsText", limitations, 24, 145, 1232, 340, 13)
    table_visual("Limitations", "ProvenanceTable", "Provenance", ["Location", "Source", "RetrievedUTC", "URL"], 24, 510, 1232, 292, "Original source timestamps and attribution by location")


def main() -> None:
    """Build all data exports, semantic model, DAX measures and seven report pages."""
    OUT.mkdir(exist_ok=True)
    prepare_data()
    build_model()
    build_report()
    print(f"Built {NAME}.pbip: {len(TABLES)} native tables, {len(dax_measures())} measures, seven pages.")


if __name__ == "__main__":
    main()
