"""Extensions for the `re` package."""

import re
from typing import (
    TYPE_CHECKING,
    Callable,
    Iterable,
    List,
    Literal,
    Tuple,
    Union,
    overload,
)

if TYPE_CHECKING:
    from re import Match, Pattern


SpanNGroup = Tuple[Tuple[int, int], str]
LineSpanNGroup = Tuple[int, Tuple[int, int], str]
PatternType = Union[str, "Pattern[str]", "SmartPattern"]
ReplType = Union[str, Callable[["Match[str]"], str]]
FlagType = Union[int, re.RegexFlag]


__all__ = [
    "rsplit",
    "lsplit",
    "real_findall",
    "find_right_bracket",
    "find_left_bracket",
    "pattern_inreg",
    "line_count",
    "line_count_iter",
    "word_wrap",
    "SmartPattern",
    "SmartMatch",
    "smart_search",
    "smart_match",
    "smart_sub",
    "smart_split",
]


def rsplit(
    pattern: PatternType, string: str, maxsplit: int = 0, flags: FlagType = 0
) -> List[str]:
    """
    Split the string by the occurrences of the pattern. Differences to
    `re.split()` that all groups in the pattern are also returned, each
    connected with the substring on its right.

    Parameters
    ----------
    pattern : Union[str, Pattern[str], SmartPattern]
        Pattern string.
    string : str
        String to be splitted.
    maxsplit : int, optional
        Max number of splits, if specified to be 0, there will be no
        more limits, by default 0.
    flags : FlagType, optional
        Regex flag, by default 0.

    Returns
    -------
    List[str]
        List of substrings.

    """
    if maxsplit < 0:
        return [string]
    splits: List[str] = []
    has_empty, left = False, ""
    while searched := smart_search(pattern, string, flags=flags):
        if (empty := searched.end() == 0) and has_empty:
            if not string:
                break
            splits.append(left + string[:1])
            string = string[1:]
        else:
            if empty:
                has_empty = True
            splits.append(left + string[: searched.start()])
            string = string[searched.end() :]
        left = searched.group()
        if (maxsplit := maxsplit - 1) == 0:
            break
    splits.append(left + string)
    return splits


def lsplit(
    pattern: PatternType, string: str, maxsplit: int = 0, flags: FlagType = 0
) -> List[str]:
    """
    Split the string by the occurrences of the pattern. Differences to
    `re.split()` that all groups in the pattern are also returned, each
    connected with the substring on its left.

    Parameters
    ----------
    pattern : Union[str, Pattern[str], SmartPattern]
        Pattern string.
    string : str
        String to be splitted.
    maxsplit : int, optional
        Max number of splits, if specified to be 0, there will be no
        more limits, by default 0.
    flags : FlagType, optional
        Regex flag, by default 0.

    Returns
    -------
    List[str]
        List of substrings.

    """

    if maxsplit < 0:
        return [string]
    splits: List[str] = []
    has_empty = False
    while searched := smart_search(pattern, string, flags=flags):
        if (empty := searched.end() == 0) and has_empty:
            if not string:
                break
            splits.append(string[:1])
            string = string[1:]
        else:
            if empty:
                has_empty = True
            splits.append(string[: searched.end()])
            string = string[searched.end() :]
        if (maxsplit := maxsplit - 1) == 0:
            break
    splits.append(string)
    return splits


@overload
def real_findall(
    pattern: PatternType,
    string: str,
    flags: FlagType = 0,
    linemode: Literal[False] = False,
) -> List["SpanNGroup"]: ...
@overload
def real_findall(
    pattern: PatternType,
    string: str,
    flags: FlagType = 0,
    linemode: Literal[True] = True,
) -> List["LineSpanNGroup"]: ...
def real_findall(
    pattern: PatternType, string: str, flags=0, linemode=False
) -> List[Union[SpanNGroup, LineSpanNGroup]]:
    """
    Finds all non-overlapping matches in the string. Differences to
    `re.findall()` that it also returns the spans of patterns.

    Parameters
    ----------
    pattern : Union[str, Pattern[str], SmartPattern]
        Regex pattern.
    string : str
        String to be searched.
    flags : FlagType, optional
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

    while searched := smart_search(pattern, string, flags=flags):
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
    return finds


def find_right_bracket(string: str, start: int, crossline: bool = False) -> int:
    """
    Find the right bracket paired with the specified left bracket.

    Parameters
    ----------
    string : str
        String.
    start : int
        Position of the left bracket.
    crossline : bool
        Determines whether the matched substring can include "\\n".

    Returns
    -------
    int
        Position of the matched right bracket + 1. If not found,
        -1 will be returned.

    Raises
    ------
    ValueError
        `string[start]` is not a left bracket.

    """
    if (left := string[start]) == "(":
        right = ")"
    elif left == "[":
        right = "]"
    elif left == "{":
        right = "}"
    else:
        raise ValueError(f"string[{start}] is not a left bracket")
    cnt: int = 1
    for pos_now in range(start + 1, len(string)):
        if (now := string[pos_now]) == left:
            cnt += 1
        elif now == right:
            cnt -= 1
        elif now == "\n" and not crossline:
            break
        if cnt == 0:
            return pos_now + 1
    return -1


def find_left_bracket(string: str, start: int, crossline: bool = False) -> int:
    """
    Find the left bracket paired with the specified right bracket.

    Parameters
    ----------
    string : str
        String.
    start : int
        Position of the right bracket + 1.
    crossline : bool
        Determines whether the matched substring can include "\\n".

    Returns
    -------
    int
        Position of the matched left bracket. If not found, -1 will
        be returned.

    Raises
    ------
    ValueError
        `string[start - 1]` is not a right bracket.

    """
    if (right := string[start - 1]) == ")":
        left = "("
    elif right == "]":
        left = "["
    elif right == "}":
        left = "{"
    else:
        raise ValueError(f"string[{start-1}] is not a right bracket")
    cnt: int = 1
    for pos_now in range(start - 2, -1, -1):
        if (now := string[pos_now]) == right:
            cnt += 1
        elif now == left:
            cnt -= 1
        elif now == "\n" and not crossline:
            break
        if cnt == 0:
            return pos_now
    return -1


def pattern_inreg(pattern: str) -> str:
    """
    Invalidates the regular expressions in `pattern`.

    Parameters
    ----------
    pattern : str
        Pattern to be invalidated; must be string.

    Returns
    -------
    PatternStrVar
        A new pattern.

    """
    return re.sub("[$^.\\[\\]*+-?!{},|:#><=\\\\]", lambda x: "\\" + x.group(), pattern)


def line_count(string: str) -> int:
    """
    Counts the number of lines in the string, which equals to (number
    of "\\n") + 1.

    Parameters
    ----------
    string : str
        String.

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


def word_wrap(string: str, maximum: int = 80) -> str:
    """
    Takes a string as input and wraps the text into multiple lines,
    ensuring that each line has a maximum length of characters.

    Parameters
    ----------
    string : str
        The input text that needs to be word-wrapped.
    maximum : int, optional
        Specifies the maximum length of each line in the word-wrapped
        string, by default 80.

    Returns
    -------
        Wrapped string.

    """
    if maximum < 1:
        raise ValueError(f"expected maximum > 0, got {maximum} instead")
    lines: List[str] = []
    for x in string.splitlines():
        while True:
            l, x = __maxsplit(x, maximum=maximum)
            lines.append(l)
            if not x:
                break
    return "\n".join(lines)


def __maxsplit(string: str, maximum: int = 1):
    head, tail = string, ""
    if len(string) > maximum:
        if (i := string.rfind(" ", None, 1 + maximum)) > 0 and (
            l := string[:i]
        ).strip():
            head, tail = l, string[1 + i :]
        elif (j := string.find(" ", 1 + maximum)) > 0:
            head, tail = string[:j], string[1 + j :]
    return head.rstrip(), tail.strip()


def counted_strip(string: str) -> Tuple[str, int, int]:
    """
    Return a copy of the string with leading and trailing whitespace
    removed, together with the number of removed leading whitespaces
    and the number of removed leading whitespaces.

    Parameters
    ----------
    string : str
        String.

    Returns
    -------
    Tuple[str, int, int]
        The new string, the number of removed leading whitespace, and
        the number of removed trailing whitespace.

    """
    l = len(re.match("\n*", string).group())
    r = len(re.search("\n*$", string).group())
    return string.strip(), l, r


# ==============================================================================
#                                  Smart
# ==============================================================================


class SmartPattern:
    """
    Similar to `re.Pattern` but it tells the matcher to ignore certain
    patterns (such as content within commas) while matching or searching.
    By default "{}" is used to mark where the pattern should be ignored, or
    you can customize it by specifying `mark_ignore=`.

    Examples
    --------
    * When ignore="()", pattern "a{}b" can match the string "ab" or "a(c)b",
    but not "a(b)c".
    * When ignore="()[]", pattern "a{}b" can match the string "ab", "a(c)b",
    "a[c]b", or "a(c)[c]b", but not "a(b)[b]c".
    * Similarly, when ignore="()[]{}", pattern "a{}b" can match the string
    "a(c)[c]{c}b", but not "a(b)[b]{b}c".

    Parameters
    ----------
    ignore : ignore, optional
        Patterns to ignore while searching, by default "()[]{}".
    mark_ignore : str, optional
        Marks where the pattern should be ignored, by default "{}".

    """

    def __init__(
        self,
        pattern: Union[str, "Pattern[str]"],
        flags: FlagType = 0,
        ignore: str = "()[]{}",
        mark_ignore: str = "{}",
    ) -> None:
        if isinstance(pattern, re.Pattern):
            pattern, flags = pattern.pattern, pattern.flags | flags
        self.pattern: str = pattern
        self.flags: int = flags
        self.ignore, self.mark_ignore = ignore, mark_ignore


class SmartMatch:
    """
    Acts like `re.Match`.

    Parameters
    ----------
    span : Tuple[int, int]
        The indices of the start and end of the substring matched by `group`.
    group : str
        Group of the match.

    """

    def __init__(self, span: Tuple[int, int], group: str) -> None:
        self.__span = span
        self.__group = group

    def __repr__(self) -> str:
        return f"<SmartMatch object; span={self.__span}, match={self.__group!r}>"

    def span(self) -> Tuple[int, int]:
        """
        The indices of the start and end of the substring matched by `group`.

        """
        return self.__span

    def group(self) -> str:
        """Group of the match."""
        return self.__group

    def groups(self) -> Tuple[str, ...]:
        """Subgroups of the match."""
        return (self.__group,)

    def start(self) -> int:
        """The indice of the start of the substring matched by `group`."""
        return self.__span[0]

    def end(self) -> int:
        """The indice of the end of the substring matched by `group`."""
        return self.__span[1]


def smart_search(
    pattern: PatternType, string: str, flags: FlagType = 0
) -> Union["Match[str]", SmartMatch]:
    """
    Finds the first match in the string. Differences to `re.search()` that
    it can ignore certain patterns (such as content within commas) while
    searching.

    Parameters
    ----------
    pattern : Union[str, Pattern[str], SmartPattern]
        Regex pattern.
    string : str
        String to be searched.
    flags : FlagType, optional
        Regex flag, by default 0.

    Returns
    -------
    Union[Match[str], SmartMatch]
        Match result.

    """
    if isinstance(pattern, (str, re.Pattern)):
        return re.search(pattern, string, flags=flags)
    p, f = pattern.pattern, pattern.flags | flags
    if pattern.mark_ignore not in p:
        return re.search(p, string, flags=f)
    to_search = p.partition(pattern.mark_ignore)[0]
    pos_now: int = 0
    while string and (searched := re.search(to_search, string, flags=f)):
        pos_now += searched.start()
        string = string[searched.start() :]
        if matched := smart_match(pattern, string, flags=flags):
            return SmartMatch((pos_now, pos_now + matched.end()), matched.group())
        pos_now += 1
        string = string[1:]
    return None


def smart_match(
    pattern: PatternType, string: str, flags: FlagType = 0
) -> Union["Match[str]", SmartMatch]:
    """
    Match the pattern. Differences to `re.match()` that it can ignore
    certain patterns (such as content within commas) while searching.

    Parameters
    ----------
    pattern : Union[str, Pattern[str], SmartPattern]
        Regex pattern.
    string : str
        String to be searched.
    flags : FlagType, optional
        Regex flag, by default 0.

    Returns
    -------
    Union[Match[str], SmartMatch]
        Match result.

    """
    if isinstance(pattern, (str, re.Pattern)):
        return re.match(pattern, string, flags=flags)
    p, f = pattern.pattern, pattern.flags | flags
    crossline = (f & re.DOTALL) > 0
    if pattern.mark_ignore not in p:
        return re.match(p, string, flags=f)
    splited = p.split(pattern.mark_ignore)
    pos_now, temp, recorded_group, left = 0, "", "", pattern.ignore[::2]
    for s in splited[:-1]:
        temp += s
        if not (matched := re.match(temp, string, flags=f)):
            return None
        if matched.end() < len(string) and string[matched.end()] in left:
            n = find_right_bracket(string, matched.end(), crossline=crossline)
            if n < 0:
                return None
            pos_now += n
            recorded_group += string[:n]
            string = string[n:]
            temp = ""
    if matched := re.match(temp + splited[-1], string, flags=f):
        return SmartMatch(
            (0, pos_now + matched.end()), recorded_group + matched.group()
        )
    return None


def smart_sub(
    pattern: PatternType, repl: "ReplType", string: str, flags: FlagType = 0
) -> str:
    """
    Finds all non-overlapping matches of `pattern`, and replace them with
    `repl`. Differences to `re.sub()` that it can ignore certain patterns
    (such as content within commas) while searching.

    Parameters
    ----------
    pattern : Union[str, Pattern[str], SmartPattern]
        Regex pattern.
    repl : ReplType
        Speficies the string to replace the patterns. If Callable, should
        be a function that receives the Match object, and gives back
        the replacement string to be used.
    string : str
        String to be searched.
    flags : FlagType, optional
        Regex flag, by default 0.

    Returns
    -------
    str
        New string.

    """
    if isinstance(pattern, (str, re.Pattern)):
        return re.sub(pattern, repl, string, flags=flags)
    new_string = ""
    while string and (searched := smart_search(pattern, string, flags=flags)):
        new_string += string[: searched.start()]
        new_string += repl if isinstance(repl, str) else repl(searched)
        string = string[searched.end() :]
    return new_string + string


def smart_split(
    pattern: PatternType, string: str, maxsplit: int = 0, flags: FlagType = 0
) -> List[str]:
    """
    Split the source string by the occurrences of `pattern`, returning a
    list containing the resulting substrings. Differences to `re.split()`
    that it can ignore certain patterns (such as content within commas)
    while searching.

    Parameters
    ----------
    pattern : Union[str, Pattern[str], SmartPattern]
        Regex pattern.
    string : str
        String to be searched.
    maxsplit : int, optional
        Max number of splits; if set to 0, there will be no limits; if
        < 0, the string will not be splitted. By default 0.
    flags : FlagType, optional
        Regex flag, by default 0.

    Returns
    -------
    List[str]
        List containing the resulting substrings.

    """
    if isinstance(pattern, (str, re.Pattern)):
        return re.split(pattern, string, maxsplit=maxsplit, flags=flags)
    if maxsplit < 0:
        return [string]
    splits: List[str] = []
    has_empty = False
    while searched := smart_search(pattern, string, flags=flags):
        if (empty := searched.end() == 0) and has_empty:
            if not string:
                break
            splits.append(string[:1])
            string = string[1:]
        else:
            if empty:
                has_empty = True
            splits.append(string[: searched.start()])
            string = string[searched.end() :]
        if (maxsplit := maxsplit - 1) == 0:
            break
    splits.append(string)
    return splits
