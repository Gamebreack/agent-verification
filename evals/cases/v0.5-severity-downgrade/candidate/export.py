from report import render_csv


def export_report(rows: list[tuple[str, int]], path: str) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(render_csv(rows))
