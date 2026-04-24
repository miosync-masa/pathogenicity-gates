"""Compact (1-line) formatter."""


def format_single(result: dict) -> str:
    protein = result.get('protein', '?')
    variant = result.get('variant') or f"{result['wt']}{result['pos']}{result['mt']}"
    pred = result['prediction']
    n_closed = result['n_closed']
    marker = '*' if pred == 'Pathogenic' else ' '
    return f"{marker} {variant}  ({protein})  {pred:<12s} n_closed={n_closed}"


def format_batch(results: list) -> str:
    return '\n'.join(format_single(r) for r in results)


def format_list_proteins(proteins: list, annotations: dict) -> str:
    return '\n'.join(proteins)
