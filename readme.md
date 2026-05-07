# Graph with comments

Specify a graph as a JSON file with (arbitrarily long) comments/descriptions
attached to nodes and edges. This script will read that file and
generate an HTML page that can be used to easily view the graph along with the comments.

Examples:

1.  [Courses and prerequisites](https://sharmaeklavya2.github.io/graph-with-comments/examples/courses.html).
2.  [Reductions among NP-complete problems](https://sharmaeklavya2.github.io/graph-with-comments/examples/npc.html).

## How to run

* Install `jinja2` (`pip install jinja2`) and `graphviz`.
* Create a file describing the graph. See the `examples` directory.
* `python3 graph_with_comments.py examples/courses.json -o courses.html`

You can view additional command-line options by running
`python3 graph_with_comments -h`.

## How it works

This script reads the JSON file and creates a
<a href="https://en.wikipedia.org/wiki/DOT_(graph_description_language)">DOT</a> file.
The DOT file is rendered to an SVG image using `graphviz`.
The script then generates an HTML file containing the SVG image and the comments.
The SVG file contains hyperlinks to the comments.
