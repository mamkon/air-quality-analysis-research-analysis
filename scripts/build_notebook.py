"""Generate and execute a compact baseline notebook using saved canonical data."""
import contextlib
import io
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import ROOT  # noqa: E402


def main() -> None:
    """Execute reproducible cells and capture their real printed results."""
    sources = [
        "import sys\nfrom pathlib import Path\n\nroot = Path.cwd()\nif root.name == 'notebooks':\n    root = root.parent\nsys.path.insert(0, str(root))\nimport pandas as pd\n\nfrom src.api_clients import baseline\nfrom src.modeling import baseline_frame, fit, metrics, missing_comparison, normality, vif\n\nraw = baseline_frame(baseline(True))\nclean = raw.dropna()\nprint(missing_comparison(raw).to_string(index=False))",
        "print(normality(clean).to_string(index=False))\nprint('Pearson correlation')\nprint(clean.corr().round(3).to_string())\nprint('Spearman correlation')\nprint(clean.corr(method='spearman').round(3).to_string())",
        "simple = fit(clean, ['temp'])\nmultiple = fit(clean)\nlog_model = fit(clean, log=True)\ncomparison = pd.DataFrame([metrics(m) for m in [simple, multiple, log_model]], index=['Simple', 'Multiple', 'Log response'])\nprint(comparison.to_string())\nprint(pd.DataFrame({'coefficient': multiple.params, 'p': multiple.pvalues}).to_string())\nprint(vif(clean).to_string(index=False))",
        "from src import viz\n\n# Interactive figures display when re-running in Jupyter.\nfigures = [viz.histogram(clean.ozone, 'Ozone (ppb)'), viz.qq(clean.ozone, 'Ozone (ppb)'), viz.heatmap(clean, 'pearson'), viz.residual(multiple)]\nfor figure in figures:\n    print(figure.layout.title.text)\n# Uncomment to view in an interactive notebook:\n# for figure in figures: figure.show()",
    ]
    cells = [{"cell_type": "markdown", "metadata": {}, "source": [
        "# Historical ozone analysis\n1973 NYC data, used to demonstrate method only.\n",
        "Run from the repository root or notebooks directory. Source: canonical R airquality via statsmodels / saved CSV.\n",
        "Complete cases are primary; missing-data approaches are descriptive sensitivity analyses.\n",
        "Log-response statistics use log(ppb), so do not rank its AIC/BIC or RMSE against raw-response models.\n"]}]
    sources.insert(1, "from src.modeling import baseline_sensitivity\n\nsensitivity = baseline_sensitivity(raw)\nprint(sensitivity.to_string(index=False))\nprint('Imputed responses are descriptive sensitivity analysis only, never live validation targets.')\nprint('Training RÂ² differs across changed samples; this is not evidence of comparative predictive skill.')")
    sources.append("import numpy as np\nfrom statsmodels.stats.diagnostic import het_breuschpagan\nfrom statsmodels.stats.stattools import durbin_watson, jarque_bera\n\nrows = []\nfor name, model in [('Raw multiple regression', multiple), ('Log response, exp prediction', log_model)]:\n    fitted = np.exp(model.fittedvalues) if model is log_model else model.fittedvalues\n    rows.append({'Model': name, 'Training RMSE (ppb)': float(np.sqrt(np.mean((clean.ozone-fitted)**2))), 'Breusch-Pagan p': het_breuschpagan(model.resid, model.model.exog)[1], 'Jarque-Bera p': jarque_bera(model.resid)[1], 'Durbin-Watson': durbin_watson(model.resid)})\nprint(pd.DataFrame(rows).to_string(index=False))\nprint('These errors use training rows. They do not establish future forecast accuracy.')\nprint('Exp(log prediction) estimates the conditional median under the log model assumptions, not a bias-corrected mean.')\nprint('A non-significant diagnostic test does not prove that all assumptions hold.')\n")
    namespace = {}
    previous = Path.cwd()
    import os
    os.chdir(ROOT)
    try:
        for count, source in enumerate(sources, 1):
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                exec(compile(source, f"notebook-cell-{count}", "exec"), namespace)
            cells.append({"cell_type": "code", "metadata": {}, "execution_count": count,
                          "source": source.splitlines(keepends=True), "outputs": [
                              {"output_type": "stream", "name": "stdout", "text": buffer.getvalue().splitlines(keepends=True)}]})
    finally:
        os.chdir(previous)
    historical_rows = namespace["rows"]
    summary = ("# Research summary\n\n"
               "This research explores how weather relates to afternoon ozone. "
               "The historical notebook explains the methods; the Ontario dashboard uses separate recent location models. "
               "The results support further investigation rather than validated health alerts.\n\n"
               f"Historical complete cases: {len(namespace['clean'])}. "
               f"Raw multiple-regression training RMSE: {historical_rows[0]['Training RMSE (ppb)']:.2f} ppb. "
               f"Log-model training RMSE after exponentiation: {historical_rows[1]['Training RMSE (ppb)']:.2f} ppb. "
               "These are training errors, not unseen-day forecasting results.\n\n"
               "The rerun does not reproduce the supplied draft's 17.91 ppb log-model error or its claim that the log model resolves both diagnostic problems. "
               "The diagnostic table below contains the actual results from this run; a model winner is not declared from those draft claims.\n")
    cells.insert(0, {"cell_type": "markdown", "metadata": {},
                     "source": summary.splitlines(keepends=True)})
    overview = (ROOT / "docs" / "research_outline.md").read_text(encoding="utf-8")
    cells.insert(0, {"cell_type": "markdown", "metadata": {},
                     "source": overview.replace("(workflow_pipeline.png)", "(../docs/workflow_pipeline.png)").splitlines(keepends=True)})
    labels = ["1. Data sources and missing values", "2. Missing-data choices",
              "3. Distributions and weather relationships", "4. Historical model comparison",
              "5. Analytical charts", "6. Historical errors and diagnostic checks"]
    organised = []
    code_index = 0
    for cell in cells:
        if cell["cell_type"] == "code":
            organised.append({"cell_type": "markdown", "metadata": {},
                              "source": ["## " + labels[code_index] + "\n"]})
            code_index += 1
        organised.append(cell)
    cells = organised
    cells.append({"cell_type": "markdown", "metadata": {}, "source": [
        "## 7. Ontario application and practical uses\n",
        "The calculations above describe historical New York data only. The Ontario dashboard fits separate recent location models and checks them on later days kept out of training.\n",
        "Ontario source ozone is modelled CAMS data, not independent station readings. See ../docs/plain_language_guide.md for industry examples and ../docs/research_outline.md for objectives and boundaries.\n",
        "The native Power BI report is still awaiting a successful display check; no verified PBIX is claimed.\n"]})
    # Apply the researcher's heading style to all generated Markdown cells.
    for cell in cells:
        if cell["cell_type"] == "markdown":
            lines = []
            for line in "".join(cell["source"]).splitlines(keepends=True):
                if re.match(r"^#{1,6} ", line):
                    line = re.sub(r"[A-Za-z]+(?:[-'][A-Za-z]+)*",
                                  lambda match: match[0].lower() if match[0].lower() in {"and", "or", "in"}
                                  else (match[0] if match[0].isupper() else match[0][0].upper() + match[0][1:]), line)
                lines.append(line)
            cell["source"] = lines
    notebook = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                                            "language_info": {"name": "python", "version": "3.11"}}, "nbformat": 4, "nbformat_minor": 5}
    (ROOT / "notebooks").mkdir(exist_ok=True)
    (ROOT / "notebooks" / "analysis.ipynb").write_text(json.dumps(notebook, indent=2), encoding="utf-8")
    (ROOT / "notebooks" / "research_reviewed.ipynb").write_text(json.dumps(notebook, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
