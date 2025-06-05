import pybadges


def generate_badge(score: float, level: str, output: str):
    svg = pybadges.badge(
        left_text="DevOps Maturity", right_text=level, right_color="green"
    )
    with open(output, "w") as f:
        f.write(svg)
