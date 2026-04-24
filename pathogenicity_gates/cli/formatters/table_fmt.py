"""Table formatter (Unicode box drawing)."""


def _row(values, widths):
    return '| ' + ' | '.join(f"{str(v):<{widths[i]}}" for i, v in enumerate(values)) + ' |'


def _hline(widths, fill='-', mid='+', left='+', right='+'):
    return left + mid.join(fill * (w + 2) for w in widths) + right


def format_single(result: dict) -> str:
    """Format single prediction as a 2-column table."""
    protein = result.get('protein', '?')
    variant = result.get('variant') or f"{result['wt']}{result['pos']}{result['mt']}"
    pred = result['prediction']
    marker = '* ' if pred == 'Pathogenic' else '  '

    header_pairs = [
        ('Variant', variant),
        ('Protein', protein),
        ('Prediction', f"{marker}{pred}"),
        ('n_closed', str(result['n_closed'])),
        ('Regime', result.get('regime', '-')),
    ]
    channels = result.get('channels', {})
    channel_pairs = [(k, v) for k, v in sorted(channels.items())]

    all_pairs = header_pairs + channel_pairs
    w_l = max(len(k) for k, _ in all_pairs)
    w_r = max(len(str(v)) for _, v in all_pairs)
    w_l = max(w_l, 12)
    w_r = max(w_r, 10)

    lines = []
    lines.append(_hline([w_l, w_r]))
    for k, v in header_pairs:
        lines.append(_row([k, v], [w_l, w_r]))
    lines.append(_hline([w_l, w_r]))
    for k, v in channel_pairs:
        lines.append(_row([k, v], [w_l, w_r]))
    lines.append(_hline([w_l, w_r]))
    return '\n'.join(lines)


def format_batch(results: list) -> str:
    """Format batch results as a summary table."""
    if not results:
        return '(no results)'

    headers = ['Variant', 'Protein', 'Prediction', 'n_closed']
    rows = []
    for r in results:
        variant = r.get('variant') or f"{r['wt']}{r['pos']}{r['mt']}"
        pred = r['prediction']
        marker = '* ' if pred == 'Pathogenic' else '  '
        rows.append([variant, r.get('protein', '?'), f"{marker}{pred}", str(r['n_closed'])])

    widths = [max(len(str(row[i])) for row in rows + [headers]) for i in range(4)]

    lines = [
        _hline(widths),
        _row(headers, widths),
        _hline(widths),
    ]
    for row in rows:
        lines.append(_row(row, widths))
    lines.append(_hline(widths))

    n_path = sum(1 for r in results if r['prediction'] == 'Pathogenic')
    lines.append('')
    pct = 100 * n_path / len(results)
    lines.append(f"Total: {len(results)} variants, {n_path} pathogenic ({pct:.1f}%)")
    return '\n'.join(lines)


def format_list_proteins(proteins: list, annotations: dict) -> str:
    """Format list-proteins output as a readable table."""
    lines = []
    lines.append("Bundled proteins in pathogenicity-gates:")
    lines.append("")
    for name in proteins:
        ann = annotations.get(name)
        if ann is None:
            lines.append(f"  {name}")
            continue
        lines.append(f"  {name:8s} {ann.uniprot or '?'}")
        desc = getattr(ann, 'description', None)
        if desc:
            lines.append(f"           {desc}")
        lines.append("")
    lines.append("Use: pathogenicity-gates predict --protein <name> --mutation <variant>")
    return '\n'.join(lines)
