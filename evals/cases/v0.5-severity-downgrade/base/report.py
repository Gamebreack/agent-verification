def render_csv(rows: list[tuple[str, int]]) -> str:
    lines = ["name,amount"]
    lines += [f"{name},{amount}" for name, amount in rows]
    return "\n".join(lines) + "\n"
