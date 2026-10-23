"""Generate and execute a compact baseline notebook using saved canonical data."""
import contextlib
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import ROOT  # noqa: E402


def main() -> None:
    """Execute reproducible cells and capture their real printed results."""
    sources = [
        "from pathlib import Path\nimport sys\nroot = Path.cwd()\nif root.name == 'notebooks':\n    root = root.parent\nsys.path.insert(0, str(root))\nfrom src.api_clients import baseline\nfrom src.modeling import baseline_frame, fit, metrics, missing_comparison, normality, vif\nimport pandas as pd\nraw = baseline_frame(baseline(True))\nclean = raw.dropna()\nprint(missing_comparison(raw).to_string(index=False))",
        "print(normality(clean).to_string(index=False))\nprint('Pearson correlation')\nprint(clean.corr().round(3).to_string())\nprint('Spearman correlation')\nprint(clean.corr(method='spearman').round(3).to_string())",
        "simple = fit(clean, ['temp'])\nmultiple = fit(clean)\nlog_model = fit(clean, log=True)\ncomparison = pd.DataFrame([metrics(m) for m in [simple, multiple, log_model]], index=['Simple', 'Multiple', 'Log response'])\nprint(comparison.to_string())\nprint(pd.DataFrame({'coefficient': multiple.params, 'p': multiple.pvalues}).to_string())\nprint(vif(clean).to_string(index=False))",
        "from src import viz\n# Interactive figures display when re-running in Jupyter.\nfigures = [viz.histogram(clean.ozone, 'Ozone (ppb)'), viz.qq(clean.ozone, 'Ozone (ppb)'), viz.heatmap(clean, 'pearson'), viz.residual(multiple)]\nfor figure in figures:\n    print(figure.layout.title.text)\n# Uncomment to view in an interactive notebook:\n# for figure in figures: figure.show()",
    ]
    cells = [{"cell_type": "markdown", "metadata": {}, "source": [
        "# Historical ozone analysis\n1973 NYC data, used to demonstrate method only.\n",
        "Run from the repository root or notebooks directory. Source: canonical R airquality via statsmodels / saved CSV.\n",
        "Complete cases are primary; missing-data approaches are descriptive sensitivity analyses.\n",
        "Log-response statistics use log(ppb), so do not rank its AIC/BIC or RMSE against raw-response models.\n"]}]
    sources.insert(1, "from src.modeling import baseline_sensitivity\nsensitivity = baseline_sensitivity(raw)\nprint(sensitivity.to_string(index=False))\nprint('Imputed responses are descriptive sensitivity analysis only, never live validation targets.')\nprint('Training R² differs across changed samples; this is not evidence of comparative predictive skill.')")
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
    notebook = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                                            "language_info": {"name": "python", "version": "3.11"}}, "nbformat": 4, "nbformat_minor": 5}
    (ROOT / "notebooks").mkdir(exist_ok=True)
    (ROOT / "notebooks" / "analysis.ipynb").write_text(json.dumps(notebook, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
