"""JSON formatter."""
import json


def format_single(result: dict) -> str:
    return json.dumps(result, indent=2, ensure_ascii=False)


def format_batch(results: list) -> str:
    return json.dumps(results, indent=2, ensure_ascii=False)


def format_list_proteins(proteins: list, annotations: dict) -> str:
    data = []
    for name in proteins:
        ann = annotations.get(name)
        data.append({
            'name': name,
            'uniprot': ann.uniprot if ann else None,
            'description': getattr(ann, 'description', None) if ann else None,
        })
    return json.dumps(data, indent=2, ensure_ascii=False)
