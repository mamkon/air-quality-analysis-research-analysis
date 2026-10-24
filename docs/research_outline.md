# Aim Objectives and Outline

**Researcher: Mercy Mamkon Oyeleke**  
**AIR QUALITY ANALYSIS RESEARCH ANALYSIS**

## Research Background and Goals

This research studies the relationship between weather and ground-level ozone. It focuses on Ontario so that the dashboard is relevant to communities across the province. Comparing selected locations makes local differences visible rather than using one result for the whole province.

Ozone was selected because its formation and movement are linked to weather. Temperature, wind speed and sunlight provide a clear starting point for investigating these patterns. These data are available through documented sources and can be updated. They do not describe all the factors that affect ozone.

This research demonstrates my ability to prepare data, explain analytical choices, check predictions and present useful findings. Its purpose is to support understanding and planning, while making uncertainty clear.

## Research Aim

This research examines how temperature, wind speed and sunlight relate to ground-level ozone, and whether these relationships can help estimate afternoon ozone in selected Ontario locations.

## Research Objectives

1. **Understand the data:** describe its sources, dates, units, coverage and missing values so the analysis is based on clearly defined information.
2. **Choose a data preparation approach:** compare complete cases, mean filling and median filling in the historical demonstration, and explain their limitations. Keep filled ozone responses out of modern prediction checks.
3. **Explore relationships:** use charts and Pearson and Spearman correlations to understand how weather and ozone vary together, without assuming cause and effect.
4. **Compare methods:** examine temperature-only, multiple regression and log-transformed models in the historical analysis. Explain why an easier-to-interpret model is a useful starting point, without declaring a winner before suitable testing.
5. **Check predictions:** evaluate the Ontario model on later days kept out of training, report errors in ozone units and show uncertainty. Keep training results separate from results on unseen days.
6. **Explain practical uses:** present findings in a dashboard and describe possible uses for public health, healthcare, schools, outdoor employers and environmental teams, including what extra evidence each use needs.

## Research Questions

- How do temperature, wind and sunlight relate to afternoon ozone?
- How do missing-data choices change the historical analysis?
- Does using several weather inputs describe the historical data better than temperature alone?
- How closely does the Ontario model estimate source ozone values on later days kept out of training?
- How could the information support planning, and where are its limits?

## Research Workflow Pipeline

![Process flow showing separate historical analysis and Ontario data collection, preparation, prediction checks, forecasting and dashboard steps](workflow_pipeline.png)

The image shows how this research moves from source data to estimates and planning information. The historical method is separate from the Ontario prediction model.

## Research Outline

| Section | What it explains | Why it matters |
|---|---|---|
| 1. Summary | The question, approach and main findings | Gives the reader a clear starting point |
| 2. Background, aim and objectives | Why this research was undertaken and what it investigates | Keeps the work focused |
| 3. Data sources and understanding | Locations, dates, units and missing values | Shows what the evidence represents |
| 4. Data preparation | Missing-data choices and time alignment | Makes analytical decisions transparent |
| 5. Charts and relationships | Distributions and correlations | Reveals patterns and possible problems |
| 6. Historical model comparison | Simple, multiple and log-transformed regression | Explains the methods using the 1973 data |
| 7. Ontario prediction checks | Later-day evaluation, errors and uncertainty | Separates model fitting from prediction evidence |
| 8. Dashboard and industry applications | How readers explore results and possible uses | Connects analysis with practical questions |
| 9. Limitations and next steps | What the research cannot establish and what to test next | Prevents conclusions that go beyond the evidence |

## Boundaries Of The Research

The 1973 New York dataset is a separate method demonstration, not the source of today's Ontario predictions. The Ontario model uses recent data for each selected location. Modern training ozone comes from CAMS through Open-Meteo and represents model estimates, not independent station measurements.

The historical raw and log models may be compared using errors on the same original ozone scale, but errors calculated on training rows do not prove future forecasting performance. Raw-response and log-response R-squared, AIC and BIC cannot simply be ranked as if they describe the same response scale. Non-significant diagnostic tests do not prove that every model assumption is satisfied.

Complete-case analysis avoids inserting invented response values but can still introduce bias if the missing rows differ systematically. Low VIF values reduce concern about overlapping predictors; they do not prove that every source of model instability is absent.

The research does not establish cause and effect, predict hospital visits, validate health alerts or demonstrate compliance with official air-quality standards. Its afternoon ozone tiers are illustrative and differ from official AQHI and eight-hour regulatory measures. Independent station validation and testing across seasons are important next steps.

## Corrections Made After Reviewing The Draft

The reviewed notebook reruns the analysis from the saved canonical data instead of copying the draft's headline figures. Its raw multiple-regression training RMSE is about 20.80 ppb, and the exponentiated log-model training RMSE is about 19.53 ppb. The draft's 17.91 ppb result was not reproduced. These figures describe fit to training rows, not future forecasting accuracy.

The rerun also does not support the draft's claim that the log model resolves both residual normality and unequal error variance. The notebook reports the calculated diagnostic results directly. No historical model is labelled a validated forecasting winner.
