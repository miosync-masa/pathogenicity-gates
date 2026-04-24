"""CLI subcommands."""
from . import predict, predict_batch, explain, list_proteins


def register_all(subparsers):
    predict.add_subparser(subparsers)
    predict_batch.add_subparser(subparsers)
    explain.add_subparser(subparsers)
    list_proteins.add_subparser(subparsers)
