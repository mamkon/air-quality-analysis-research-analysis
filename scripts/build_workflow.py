"""Draw the research workflow as a portable PNG process-flow image."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs' / 'workflow_pipeline.png'
INK = '#172D46'
TEAL = '#087E8B'
MUTED = '#486075'
FONT = Path('C:/Windows/Fonts/arial.ttf')
BOLD = Path('C:/Windows/Fonts/arialbd.ttf')


def main() -> None:
    """Render reviewed steps, with independent historical and Ontario paths."""
    canvas = Image.new('RGB', (1600, 1710), '#F4F7FB')
    draw = ImageDraw.Draw(canvas)

    def text(x: int, y: int, value: str, size: int = 26, bold: bool = False, color: str = INK) -> None:
        font = ImageFont.truetype(str(BOLD if bold else FONT), size)
        draw.multiline_text((x, y), value, font=font, fill=color, spacing=10)

    def title_text(value: str) -> str:
        return ' '.join(word.lower() if word.lower() in {'and', 'or', 'in'} else (word if word.isupper() else word[0].upper()+word[1:]) for word in value.split())

    def box(x: int, y: int, w: int, h: int, title: str, body: str, accent: str = TEAL, fill: str = '#E0F3F2') -> None:
        draw.rounded_rectangle((x, y, x+w, y+h), radius=22, fill=fill, outline=accent, width=3)
        draw.rounded_rectangle((x, y, x+7, y+h), radius=3, fill=accent)
        text(x+25, y+18, title_text(title), 29, True, accent)
        text(x+25, y+61, body, 25)

    def arrow(x: int, y1: int, y2: int) -> None:
        draw.line((x, y1, x, y2-10), fill=TEAL, width=4)
        draw.polygon([(x, y2), (x-9, y2-14), (x+9, y2-14)], fill=TEAL)

    text(60, 40, 'Research Workflow Pipeline', 50, True)
    text(60, 112, 'From Source Data To Ozone Estimates and Planning Information', 28, color=MUTED)
    text(60, 188, 'Historical Method', 25, True, MUTED)
    text(530, 188, 'Ontario Prediction Workflow', 25, True, TEAL)
    box(60, 242, 410, 160, '1973 New York data', 'Explain the analysis method.\nKeep original historical units.', MUTED)
    arrow(265, 407, 456)
    box(60, 462, 410, 195, 'Explore and compare', 'Missing-data choices, charts,\ncorrelations and regression.\nCheck errors and assumptions.', MUTED)
    arrow(265, 662, 712)
    box(60, 718, 410, 192, 'Explain the evidence', 'Report historical results.\nTraining fit is different from\nfuture prediction accuracy.', MUTED)
    text(75, 950, 'Separate method demonstration.\nIts equation does not generate\nOntario predictions.', 25, True, MUTED)
    steps = [
        ('1  Collect source data', 'Weather: Open-Meteo. Ozone: CAMS via Open-Meteo.\nKeep source dates; saved snapshots provide a fallback.'),
        ('2  Prepare local daily data', 'Align dates, time zones and units; check missing hours.\nMatch weather with afternoon ozone for each location.'),
        ('3  Keep later days aside', 'Split the latest complete past days in time order.\nUse earlier days for training; reserve the latest quarter for checking.'),
        ('4  Train and check predictions', 'Fit regression on earlier days and predict the reserved days.\nCompare with source ozone values; report errors and uncertainty.'),
        ('5  Fit the model for future estimates', 'Refit on the available past training window for that location.\nEnter forecast weather to estimate future afternoon ozone.'),
        ('6  Present the results', 'Streamlit: API data, estimates and source timestamps.\nPower BI: dated snapshot; report display verification pending.'),
        ('7  Support understanding and planning', 'Explore possible uses for health, schools and outdoor work.\nShow official local AQHI separately; it is not this model\'s output.'),
    ]
    palette = [('#096B70', '#DAF2EF'), ('#2253A3', '#E1EDFF'), ('#7041A5', '#EEE4FC'),
               ('#885808', '#FFF0CD'), ('#096782', '#DCF3FA'), ('#A33262', '#FBE3EE'), ('#286B37', '#E1F3DF')]
    draw.ellipse((780, 237, 1290, 312), fill='#172D46', outline='#172D46', width=3)
    text(920, 256, 'Research Start', 29, True, 'white')
    arrow(1035, 314, 345)
    for i, (title, body) in enumerate(steps):
        y = 350+i*150
        box(530, y, 1010, 125, title, body, *palette[i])
        if i < len(steps)-1:
            arrow(1035, y+127, y+148)
    arrow(1035, 1377, 1420)
    draw.ellipse((730, 1425, 1340, 1500), fill='#286B37', outline='#286B37', width=3)
    text(850, 1445, 'Review and Next Steps', 29, True, 'white')
    draw.rounded_rectangle((60, 1540, 1540, 1670), radius=18, fill='#E4EEF4')
    text(85, 1557, 'What The Evidence Means', 27, True)
    text(85, 1600, 'CAMS ozone is modelled, not independent station readings. This research does not validate health alerts.\nResearch by Mercy Mamkon Oyeleke | Air Quality Analysis Research Analysis', 24, color=MUTED)
    canvas.save(OUT, optimize=True)
    print(OUT)


if __name__ == '__main__':
    main()
