"""Consistent accessible Plotly figures with explicit measurement units."""
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
from statsmodels.regression.linear_model import RegressionResultsWrapper

from src.config import TIERS


def theme(fig: go.Figure, title: str, x: str, y: str) -> go.Figure:
    """Apply shared typography, contrast, titles and axes."""
    fig.update_layout(template="plotly_white", title=title, xaxis_title=x, yaxis_title=y,
                      font=dict(family="Arial", color="#183447"), height=430,
                      colorway=["#0072B2", "#D55E00", "#009E73"],
                      margin=dict(l=30, r=30, t=65, b=45), legend=dict(orientation="h"))
    return fig


def forecast(frame: pd.DataFrame) -> go.Figure:
    """Prediction band and labelled illustrative risk bands."""
    fig = go.Figure()
    lower = 0
    for upper, label, color in TIERS:
        top = upper if np.isfinite(upper) else max(100, frame.upper.max())
        fig.add_hrect(y0=lower, y1=top, fillcolor=color, opacity=0.08,
                      line_width=0, annotation_text=label, annotation_position="top left")
        lower = upper
    fig.add_scatter(x=frame.index, y=frame.upper, mode="lines", line=dict(width=0), showlegend=False)
    fig.add_scatter(x=frame.index, y=frame.lower, fill="tonexty",
                    mode="lines", fillcolor="rgba(0,114,178,0.16)", line=dict(width=0), name="95% prediction interval")
    fig.add_scatter(x=frame.index, y=frame.predicted, mode="lines+markers", line=dict(color="#0072B2"), name="OLS prediction")
    return theme(fig, "Afternoon ozone · weather-based outlook", "Selected location local date", "Ozone (ppb)")


def lines(frame: pd.DataFrame, columns: list[str], title: str, y: str) -> go.Figure:
    """Time-series comparison with unified hover."""
    fig = px.line(frame, x=frame.index, y=columns)
    fig.update_layout(hovermode="x unified")
    return theme(fig, title, "Selected location local date", y)


def residual(model: RegressionResultsWrapper) -> go.Figure:
    """Residuals versus fitted response with zero reference."""
    fig = px.scatter(x=model.fittedvalues, y=model.resid)
    fig.add_hline(y=0, line_dash="dash")
    return theme(fig, "Residual diagnostics", "Fitted ozone (response units)", "Residual (response units)")


def histogram(series: pd.Series, unit: str) -> go.Figure:
    """Distribution histogram."""
    return theme(px.histogram(x=series, nbins=20), f"Distribution · {series.name}", unit, "Count")


def qq(series: pd.Series, unit: str) -> go.Figure:
    """Normal Q–Q plot with fitted reference line."""
    (x, y), (slope, intercept, _) = stats.probplot(series.dropna())
    fig = go.Figure(go.Scatter(x=x, y=y, mode="markers", name="Sample"))
    fig.add_scatter(x=x, y=intercept + slope * x, mode="lines", name="Normal reference")
    return theme(fig, f"Normal Q–Q · {series.name}", "Theoretical normal quantile", unit)


def heatmap(frame: pd.DataFrame, method: str) -> go.Figure:
    """Labelled correlation heatmap with fixed comparable bounds."""
    fig = px.imshow(frame.corr(method=method), zmin=-1, zmax=1, text_auto=".2f",
                    color_continuous_scale="RdBu_r")
    return theme(fig, f"{method.title()} correlation", "Variable", "Variable")
