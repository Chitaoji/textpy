"""
Contains css styles.

NOTE: this module is private. All functions and objects are available in the main
`textpy` namespace - use that instead.

"""

__all__ = []

TREE_CSS_STYLE = """<style type="text/css">
.{0},
.{0} ul.m,
.{0} li.m {{
    margin: 0;
    padding: 0;
    position: relative;
}}
.{0} {{
    margin: 0 0 1em;
    text-align: center;
}}
.{0},
.{0} ul.m {{
    display: table;
}}
.{0} ul.m {{
    width: 100%;
}}
.{0} li.m {{
    display: table-cell;
    padding: .5em 0;
    vertical-align: top;
}}
.{0} ul.s,
.{0} li.s {{
    text-align: left;
}}
.{0} li.m:before {{
    outline: solid 1px #666;
    content: "";
    left: 0;
    position: absolute;
    right: 0;
    top: 0;
}}
.{0} li.m:first-child:before {{
    left: 50%;
}}
.{0} li.m:last-child:before {{
    right: 50%;
}}
.{0} li.m>details>summary,
.{0} li.m>span {{
    border: solid .1em #666;
    border-radius: .2em;
    display: inline-block;
    margin: 0 .2em .5em;
    padding: .2em .5em;
    position: relative;
}}
.{0} li>details>summary {{ 
    white-space: nowrap;
}}
.{0} li.m>details>summary {{
    cursor: pointer;
}}
.{0} li.m>details>summary>span.open,
.{0} li.m>details[open]>summary>span.closed {{
    display: none;
}}
.{0} li.m>details[open]>summary>span.open {{
    display: inline;
}}
.{0} ul.m:before,
.{0} li.m>details>summary:before,
.{0} li.m>span:before {{
    outline: solid 1px #666;
    content: "";
    height: .5em;
    left: 50%;
    position: absolute;
}}
.{0} ul.m:before {{
    top: -.5em;
}}
.{0} li.m>details>summary:before,
.{0} li.m>span:before {{
    top: -.56em;
    height: .45em;
}}
.{0}>li.m {{
    margin-top: 0;
}}
.{0}>li.m:before,
.{0}>li.m:after,
.{0}>li.m>details>summary:before,
.{0}>li.m>span:before {{
    outline: none;
}}
</style>
"""

TABLE_CSS_STYLE = """<style type="text/css">
.{0} th {{
  text-align: center;
}}
.{0} td {{
  text-align: left;
}}
</style>
"""
