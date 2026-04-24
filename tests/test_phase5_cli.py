"""
Phase 5 CLI integration tests.

Runs the CLI via `python -m pathogenicity_gates.cli` subprocess and
verifies end-to-end behavior (predict/predict-batch/explain/list-proteins).
"""
import json
import os
import subprocess
import sys
import tempfile
import pytest


CLI_MODULE = "pathogenicity_gates.cli"


def run_cli(args, stdin_input=None, expect_success=True):
    cmd = [sys.executable, "-m", CLI_MODULE] + args
    result = subprocess.run(
        cmd,
        input=stdin_input,
        capture_output=True,
        text=True,
        timeout=180,
    )
    if expect_success:
        assert result.returncode == 0, (
            f"CLI failed with code {result.returncode}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
    return result.stdout, result.stderr, result.returncode


# ═══════════════════════════════════════════════════════════════
# Basic invocation
# ═══════════════════════════════════════════════════════════════
def test_cli_version():
    out, _, _ = run_cli(['--version'])
    assert 'pathogenicity-gates' in out


def test_cli_help():
    out, _, _ = run_cli(['--help'])
    assert 'predict' in out
    assert 'predict-batch' in out
    assert 'explain' in out
    assert 'list-proteins' in out


def test_cli_no_subcommand():
    _, _, rc = run_cli([], expect_success=False)
    assert rc != 0


# ═══════════════════════════════════════════════════════════════
# list-proteins
# ═══════════════════════════════════════════════════════════════
def test_list_proteins_table():
    out, _, _ = run_cli(['list-proteins'])
    for p in ['p53', 'kras', 'tdp43', 'brca1']:
        assert p in out


def test_list_proteins_json():
    out, _, _ = run_cli(['list-proteins', '--format', 'json'])
    data = json.loads(out)
    names = {d['name'] for d in data}
    assert names >= {'p53', 'kras', 'tdp43', 'brca1'}


def test_list_proteins_compact():
    out, _, _ = run_cli(['list-proteins', '--format', 'compact'])
    lines = out.strip().split('\n')
    assert 'p53' in lines


# ═══════════════════════════════════════════════════════════════
# predict
# ═══════════════════════════════════════════════════════════════
def test_predict_r175h_compact():
    out, _, _ = run_cli(['predict', '--protein', 'p53', '--mutation', 'R175H'])
    assert 'R175H' in out
    assert 'Pathogenic' in out


def test_predict_r175h_json():
    out, _, _ = run_cli(['predict', '--protein', 'p53',
                         '--mutation', 'R175H', '--format', 'json'])
    data = json.loads(out)
    assert data['variant'] == 'R175H'
    assert data['prediction'] == 'Pathogenic'
    assert data['n_closed'] >= 1
    assert 'Ch03_Core' in data['channels']


def test_predict_r175h_table():
    out, _, _ = run_cli(['predict', '--protein', 'p53',
                         '--mutation', 'R175H', '--format', 'table'])
    assert 'R175H' in out
    assert 'Pathogenic' in out
    assert 'Ch03_Core' in out


def test_predict_split_format():
    """'--mutation 175 R H' (3 args) must work."""
    out, _, _ = run_cli(['predict', '--protein', 'p53',
                         '--mutation', '175', 'R', 'H'])
    assert 'Pathogenic' in out


def test_predict_kras():
    out, _, _ = run_cli(['predict', '--protein', 'kras', '--mutation', 'K117N'])
    assert 'K117N' in out
    assert 'Pathogenic' in out


def test_predict_tdp43_idr():
    out, _, _ = run_cli(['predict', '--protein', 'tdp43',
                         '--mutation', 'G348C', '--format', 'json'])
    data = json.loads(out)
    assert data['prediction'] == 'Pathogenic'
    assert data.get('regime') == 'idr'


def test_predict_invalid_mutation():
    _, err, rc = run_cli(['predict', '--protein', 'p53', '--mutation', 'XYZ'],
                         expect_success=False)
    assert rc != 0
    assert 'Invalid' in err or 'ERROR' in err


def test_predict_nonexistent_protein():
    _, _, rc = run_cli(['predict', '--protein', 'nonexistent',
                        '--mutation', 'R175H'], expect_success=False)
    assert rc != 0


def test_predict_requires_protein_or_annotation():
    _, _, rc = run_cli(['predict', '--mutation', 'R175H'], expect_success=False)
    assert rc != 0


# ═══════════════════════════════════════════════════════════════
# predict-batch
# ═══════════════════════════════════════════════════════════════
def test_predict_batch_csv():
    with tempfile.NamedTemporaryFile('w', suffix='.csv', delete=False) as f:
        f.write("position,wt,mt\n175,R,H\n248,R,W\n273,R,H\n")
        csv_path = f.name
    try:
        out, _, _ = run_cli(['predict-batch', '--protein', 'p53',
                             '--input', csv_path, '--format', 'json'])
        data = json.loads(out)
        assert len(data) == 3
        assert all(r['prediction'] == 'Pathogenic' for r in data)
    finally:
        os.unlink(csv_path)


def test_predict_batch_json_input():
    with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as f:
        json.dump([
            {'position': 175, 'wt': 'R', 'mt': 'H'},
            {'position': 248, 'wt': 'R', 'mt': 'W'},
        ], f)
        json_path = f.name
    try:
        out, _, _ = run_cli(['predict-batch', '--protein', 'p53',
                             '--input', json_path])
        data = json.loads(out)
        assert len(data) == 2
    finally:
        os.unlink(json_path)


def test_predict_batch_stdin():
    csv_input = "position,wt,mt\n175,R,H\n248,R,W\n"
    out, _, _ = run_cli(['predict-batch', '--protein', 'p53', '--input', '-'],
                        stdin_input=csv_input)
    data = json.loads(out)
    assert len(data) == 2


def test_predict_batch_csv_output():
    with tempfile.NamedTemporaryFile('w', suffix='.csv', delete=False) as fi:
        fi.write("position,wt,mt\n175,R,H\n")
        in_path = fi.name
    out_path = tempfile.mktemp(suffix='.csv')
    try:
        run_cli(['predict-batch', '--protein', 'p53',
                 '--input', in_path, '--output', out_path,
                 '--format', 'csv'])
        with open(out_path) as f:
            content = f.read()
        assert 'R175H' in content
        assert 'Pathogenic' in content
    finally:
        os.unlink(in_path)
        if os.path.exists(out_path):
            os.unlink(out_path)


# ═══════════════════════════════════════════════════════════════
# explain
# ═══════════════════════════════════════════════════════════════
def test_explain_r175h():
    out, _, _ = run_cli(['explain', '--protein', 'p53', '--mutation', 'R175H'])
    assert 'R175H' in out
    assert 'Pathogenic' in out
    assert 'Ch03_Core' in out
    assert 'structural' in out


def test_explain_idr_variant():
    out, _, _ = run_cli(['explain', '--protein', 'tdp43', '--mutation', 'G348C'])
    assert 'G348C' in out
    assert 'idr' in out.lower() or 'IDR' in out


def test_explain_channels_only():
    out, _, _ = run_cli(['explain', '--protein', 'p53',
                         '--mutation', 'R175H', '--channels-only'])
    assert 'Ch03_Core' in out
    assert 'Residue Context' not in out


def test_explain_verbose():
    out, _, _ = run_cli(['explain', '--protein', 'p53',
                         '--mutation', 'R175H', '--verbose'])
    assert 'Full residue context' in out


# ═══════════════════════════════════════════════════════════════
# API parity
# ═══════════════════════════════════════════════════════════════
def test_cli_matches_api():
    """CLI output must match direct Predictor API call (bit-for-bit channels)."""
    from pathogenicity_gates import Predictor

    pred = Predictor.from_protein('p53')
    api = pred.predict(175, 'R', 'H', mode='channels')

    out, _, _ = run_cli(['predict', '--protein', 'p53',
                         '--mutation', 'R175H', '--format', 'json'])
    cli = json.loads(out)

    assert cli['n_closed'] == api['n_closed']
    assert cli['prediction'] == api['prediction']
    for ch, state in api['channels'].items():
        assert cli['channels'].get(ch) == state
