"""Extensions to the `re` package."""
import re
from typing import Iterable, List, Literal, Tuple, TypeVar, Union, overload

SpanNGroup = Tuple[Tuple[int, int], str]
LineSpanNGroup = Tuple[int, Tuple[int, int], str]
StrPattern = TypeVar("StrPattern", str, re.Pattern)

__all__ = [
    "rsplit",
    "lsplit",
    "real_findall",
    "pattern_inreg",
    "line_count",
    "line_count_iter",
]


def rsplit(
    pattern: Union[str, re.Pattern],
    string: str,
    maxsplit: int = 0,
    flags: Union[int, re.RegexFlag] = 0,
) -> List[str]:
    """
    Split the string by the occurrences of the pattern. Differences to
    `re.split()` that all groups in the pattern are also returned, each
    connected with the substring on its right.

    Parameters
    ----------
    pattern : Union[str, re.Pattern]
        Pattern string.
    string : str
        String to be splitted.
    maxsplit : int, optional
        Max number of splits, if specified to be 0, there will be no
        more limits, by default 0.
    flags : Union[int, re.RegexFlag], optional
        Regex flag, by default 0.

    Returns
    -------
    List[str]
        List of substrings.

    """
    splits: List[str] = []
    searched = re.search(pattern, string, flags=flags)
    left: str = ""
    while searched:
        span = searched.span()
        splits.append(left + string[: span[0]])
        left = searched.group()
        string = string[span[1] :]
        if len(splits) >= maxsplit > 0:
            break
        searched = re.search(pattern, string, flags=flags)
    splits.append(left + string)
    return splits


def lsplit(
    pattern: Union[str, re.Pattern],
    string: str,
    maxsplit: int = 0,
    flags: Union[int, re.RegexFlag] = 0,
) -> List[str]:
    """
    Split the string by the occurrences of the pattern. Differences to
    `re.split()` that all groups in the pattern are also returned, each
    connected with the substring on its left.

    Parameters
    ----------
    pattern : Union[str, re.Pattern]
        Pattern string.
    string : str
        String to be splitted.
    maxsplit : int, optional
        Max number of splits, if specified to be 0, there will be no
        more limits, by default 0.
    flags : Union[int, re.RegexFlag], optional
        Regex flag, by default 0.

    Returns
    -------
    List[str]
        List of substrings.

    """
    splits: List[str] = []
    searched = re.search(pattern, string, flags=flags)
    while searched:
        span = searched.span()
        splits.append(string[: span[1]])
        string = string[span[1] :]
        if len(splits) >= maxsplit > 0:
            break
        searched = re.search(pattern, string, flags=flags)
    splits.append(string)
    return splits


@overload
def real_findall(
    pattern: Union[str, re.Pattern],
    string: str,
    flags: Union[int, re.RegexFlag] = 0,
    linemode: Literal[False] = False,
) -> List[SpanNGroup]:
    ...


@overload
def real_findall(
    pattern: Union[str, re.Pattern],
    string: str,
    flags: Union[int, re.RegexFlag] = 0,
    linemode: Literal[True] = True,
) -> List[LineSpanNGroup]:
    ...


def real_findall(
    pattern: Union[str, re.Pattern],
    string: str,
    flags: Union[int, re.RegexFlag] = 0,
    linemode: bool = False,
) -> List[Union[SpanNGroup, LineSpanNGroup]]:
    """
    Finds all non-overlapping matches in the string. Differences to
    `re.findall` that it also returns the spans of patterns.

    Parameters
    ----------
    pattern : Union[str, re.Pattern]
        Regex pattern.
    string : str
        String to be searched.
    flags : Union[int, re.RegexFlag], optional
        Regex flag, by default 0.
    linemode : bool, optional
        Determines whether to match the pattern on each line of the
        string, by default False.

    Returns
    -------
    List[Union[SpanNGroup, LineSpanNGroup]]
        List of finding result. If `linemode` is False, each list
        element consists of the span and the group of the pattern. If
        `linemode` is True, each list element consists of the line
        number, the span (within the line), and the group of the
        pattern instead.

    """
    finds: List[SpanNGroup] = []
    nline: int = 1
    total_pos: int = 0
    inline_pos: int = 0
    searched = re.search(pattern, string, flags=flags)
    while searched:
        span, group = searched.span(), searched.group()
        if linemode:
            left = string[: span[0]]
            lc_left = line_count(left) - 1
            nline += lc_left
            if lc_left > 0:
                inline_pos = 0
            lastline_pos = len(left) - 1 - left.rfind("\n")
            finds.append(
                (
                    nline,
                    (
                        inline_pos + lastline_pos,
                        inline_pos + lastline_pos + span[1] - span[0],
                    ),
                    group,
                )
            )
            nline += line_count(group) - 1
            if "\n" in group:
                inline_pos = len(group) - 1 - group.rfind("\n")
            else:
                inline_pos += max(lastline_pos + span[1] - span[0], 1)
        else:
            finds.append(((span[0] + total_pos, span[1] + total_pos), group))
            total_pos += max(span[1], 1)
        if len(string) == 0:
            break
        if span[1] == 0:
            nline += 1 if string[0] == "\n" else 0
            string = string[1:]
        else:
            string = string[span[1] :]
        searched = re.search(pattern, string, flags=flags)  # search again
    return finds


def pattern_inreg(pattern: StrPattern) -> StrPattern:
    """
    Invalidates the regular expressions in `pattern`.

    Parameters
    ----------
    pattern : StrPattern
        Pattern to be invalidated.

    Returns
    -------
    StrPattern
        A new pattern.

    """
    flags: int = -1
    if isinstance(pattern, re.Pattern):
        pattern, flags = str(pattern.pattern), pattern.flags
    pattern = re.sub(
        "[$^.\\[\\]*+-?!{},|:#><=\\\\]", lambda x: "\\" + x.group(), pattern
    )
    if flags == -1:
        return pattern
    return re.compile(pattern, flags=flags)


def line_count(string: str) -> int:
    """
    Counts the number of lines in the string.

    Parameters
    ----------
    string : str
        A string.

    Returns
    -------
    int
        Total number of lines.

    """
    return 1 + len(re.findall("\n", string))


def line_count_iter(iterstr: Iterable[str]) -> Iterable[Tuple[int, str]]:
    """
    Counts the number of lines in each string, and returns the cumsumed
    values.

    Parameters
    ----------
    iter : Iterable[str]
        An iterable of strings.

    Yields
    ------
    Tuple[int, str]
        Each time, yields the cumsumed number of lines til now together
        with a string found in `iter`, until `iter` is traversed.

    """
    cnt: int = 1
    for s in iterstr:
        yield cnt, s
        cnt += len(re.findall("\n", s))
