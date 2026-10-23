"""OLS diagnostics and chronological validation without target leakage."""
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.regression.linear_model import OLS, RegressionResultsWrapper
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.tools.tools import add_constant

from src.config import FEATURES


def fit(frame: pd.DataFrame, features: list[str] = FEATURES, log: bool = False) -> RegressionResultsWrapper:
    """Fit complete cases; never impute a validation target."""
    clean = frame.dropna(subset=["ozone", *features])
    if log:
        clean = clean.loc[clean.ozone > 0]
    if len(clean) < len(features) + 6:
        raise ValueError("Too few complete days to fit a reliable model")
    y = np.log(clean.ozone) if log else clean.ozone
    return OLS(y, add_constant(clean[features], has_constant="add")).fit()


def predict(model: RegressionResultsWrapper, frame: pd.DataFrame) -> pd.DataFrame:
    """Raw OLS predictions and 95% individual prediction intervals, untruncated."""
    names = [x for x in model.model.exog_names if x != "const"]
    result = model.get_prediction(add_constant(frame[names], has_constant="add"))
    return result.summary_frame().rename(columns={"mean": "predicted",
        "obs_ci_lower": "lower", "obs_ci_upper": "upper"})[["predicted", "lower", "upper"]]


def metrics(model: RegressionResultsWrapper) -> dict:
    """Training fit statistics; RMSE uses the response scale of this model."""
    return {"n": int(model.nobs), "R²": model.rsquared, "Adjusted R²": model.rsquared_adj,
            "AIC": model.aic, "BIC": model.bic,
            "RMSE": float(np.sqrt(np.mean(model.resid**2))),
            "Residual Shapiro p": stats.shapiro(model.resid).pvalue}


def validate(frame: pd.DataFrame) -> tuple:
    """Hold out the latest 25%; train final deployment model on all past days."""
    clean = frame.dropna().sort_index()
    split = int(len(clean) * 0.75)
    train, test = clean.iloc[:split], clean.iloc[split:]
    training_model = fit(train)
    evaluation = test.join(predict(training_model, test))
    evaluation["residual"] = evaluation.ozone - evaluation.predicted
    evaluation["rolling_rmse"] = evaluation.residual.pow(2).rolling(7).mean().pow(0.5)
    return fit(clean), evaluation, training_model


def vif(frame: pd.DataFrame) -> pd.DataFrame:
    """Variance inflation factors include an intercept in auxiliary regressions."""
    x = add_constant(frame[FEATURES].dropna(), has_constant="add")
    return pd.DataFrame({"Feature": FEATURES, "VIF": [
        variance_inflation_factor(x.to_numpy(), i + 1) for i in range(len(FEATURES))]})


def baseline_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Rename baseline columns; retain original °F, mph and Langleys units."""
    return frame.rename(columns={"Ozone": "ozone", "Temp": "temp", "Wind": "wind",
                                  "Solar.R": "solar"})[["ozone", *FEATURES]]


def missing_comparison(frame: pd.DataFrame) -> pd.DataFrame:
    """Compare complete cases to descriptive mean/median imputation."""
    rows = []
    for name in ["Complete case", "Mean", "Median"]:
        sample = frame.dropna() if name == "Complete case" else frame.fillna(
            frame.mean() if name == "Mean" else frame.median())
        rows.append({"Method": name, "n": len(sample), "Ozone SD": sample.ozone.std(),
                     "Pearson r with Temp": sample.ozone.corr(sample.temp)})
    return pd.DataFrame(rows)


def baseline_sensitivity(frame: pd.DataFrame) -> pd.DataFrame:
    """Reproduce baseline OLS under complete-case, mean and median handling.

    Imputed responses are permitted only for this descriptive historical
    sensitivity analysis. They must never become live validation targets.
    """
    rows = []
    for name in ["Complete case", "Mean", "Median"]:
        sample = frame.dropna() if name == "Complete case" else frame.fillna(
            frame.mean() if name == "Mean" else frame.median())
        model = fit(sample)
        rows.append({"Method": name, **metrics(model),
                     "Imputed ozone targets": 0 if name == "Complete case" else int(frame.ozone.isna().sum()),
                     "Intercept": model.params["const"],
                     "Temperature coefficient (ppb/°F)": model.params["temp"],
                     "Wind coefficient (ppb/mph)": model.params["wind"],
                     "Solar coefficient (ppb/Langley)": model.params["solar"]})
    return pd.DataFrame(rows)


def normality(frame: pd.DataFrame) -> pd.DataFrame:
    """Shapiro–Wilk tests are descriptive, not a gate for using OLS."""
    return pd.DataFrame([{"Variable": col, "W": stats.shapiro(frame[col].dropna()).statistic,
                          "p": stats.shapiro(frame[col].dropna()).pvalue} for col in frame])
