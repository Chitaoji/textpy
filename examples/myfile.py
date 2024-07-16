#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Optional


class MyBook:
    """
    A book that records a story.

    Parameters
    ----------
    story : str, optional
        Story to record, by default None.

    """

    def __init__(self, story: Optional[str] = None) -> None:
        if story is None:
            self.content = "This book is empty."
        self.content = story


def print_my_book(book: MyBook) -> None:
    """
    Print a book.

    Parameters
    ----------
    book : MyBook
        A book.

    """
    print(book.content)
