"""Chapter 08 exercise: a list the agent can choose from, and a check on what it chose.

Grade it with `make exercise N=08`. The tests pass in accounts as dicts, so no model is needed.
When it passes, `make lesson N=08 ARGS=--mine` traces the trail from your list.
"""

from __future__ import annotations


def listing(accounts: list[dict[str, str]], lengths: dict[str, int], described: bool = True
            ) -> tuple[str, dict[str, str]]:
    """The file list as the agent sees it, and the map from the names shown to the real files.

    Each account is a dict with file, holder, account_no and bank. `lengths` maps a file to
    its number of lines. The text starts with the line "Statements on file:".

    Described, one line a file:
        - corvane-trading.csv: Corvane Trading Ltd, SC-0071-5530, Sabran Commercial Bank, 37 lines.
    Bare, the files are shown as stmt-01.csv, stmt-02.csv, ... in the order given:
        - stmt-01.csv
    The second value maps every name shown to the real file name.
    """
    # TODO 1: the described lines, where the name shown is the real name.
    # TODO 2: the bare lines, numbered from 01, and the map back to the real names.
    raise NotImplementedError("write listing")


def unopened(payees: list[str], accounts: list[dict[str, str]], opened: list[str]) -> list[str]:
    """Payees that have a statement on file which was not opened, each once, in order.

    `opened` holds real file names. A payee with no statement on file is nobody's to open.
    Match holders whatever the case of the name.
    """
    # TODO 3: holder (lower case) -> file. Then walk the payees.
    raise NotImplementedError("write unopened")
