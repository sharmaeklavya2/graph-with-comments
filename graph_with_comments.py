#!/usr/bin/env python3

import os
from os.path import join as pjoin
import argparse
import json
import subprocess

from collections.abc import Mapping, Sequence
from typing import Any, Literal, NotRequired, Required, TypedDict
from jinja2 import DictLoader, Environment


BASE_DIR = os.path.dirname(os.path.realpath(__file__))
DEFAULT_DOT_TEMPLATE_PATH = pjoin(BASE_DIR, 'graph.dot.jinja2')
DEFAULT_HTML_TEMPLATE_PATH = pjoin(BASE_DIR, 'page.html.jinja2')
CSS_PATH = pjoin(BASE_DIR, 'style.css')


def read_file(fpath: str) -> str:
    with open(fpath) as fp:
        return fp.read()


def write_file(fpath: str, s: str) -> None:
    with open(fpath, 'w') as fp:
        fp.write(s)


class VertexInfo(TypedDict, total=False):
    id: str
    name: str
    text: str
    url: str

EdgeInfo = TypedDict('EdgeInfo', {
    'id': str,
    'from': Required[str],
    'to': Required[str],
    'fromV': VertexInfo,
    'toV': VertexInfo,
    'bidir': bool,
    'text': str,
    'url': str,
    'type': str,
    }, total=False)

class Labels(TypedDict, total=False):
    title: str
    vertices: str
    edges: str

class Config(TypedDict, total=False):
    rankdir: Literal['LR'] | Literal['TB'] | None
    showVertices: bool
    showEdges: bool

class Graph(TypedDict):
    labels: NotRequired[Labels]
    config: NotRequired[Config]
    vertices: Mapping[str, VertexInfo]
    edges: Sequence[EdgeInfo]
    css: NotRequired[str]
    svg: NotRequired[str]

def processVertices(graph: Graph) -> None:
    vertices = graph['vertices']
    for vid, vinfo in vertices.items():
        vinfo['id'] = vid
        if vinfo.get('name') is None:
            vinfo['name'] = vinfo['id']

def processEdges(graph: Graph) -> None:
    vertices, edges = graph['vertices'], graph['edges']
    for i, edge in enumerate(edges):
        edge['id'] = str(i+1)
        edge['fromV'] = vertices[edge['from']]
        edge['toV'] = vertices[edge['to']]


def processGraph(graph: Graph) -> None:
    processVertices(graph)
    processEdges(graph)

    labels = graph.get('labels', {})
    labels.setdefault('vertices', 'Vertices')
    labels.setdefault('edges', 'Edges')
    graph['labels'] = labels

    config = graph.get('config', {})
    config.setdefault('showVertices', True)
    config.setdefault('showEdges', True)
    config.setdefault('rankdir', None)
    graph['config'] = config


def loadTemplate(custom_path: str | None, default_path: str, **options: Any) -> Any:
    default_contents = read_file(default_path)
    if custom_path is not None:
        custom_contents = read_file(custom_path)
    else:
        custom_contents = '{% extends "base" %}'
    loader = DictLoader({'base': default_contents, 'custom': custom_contents})
    env = Environment(loader=loader, **options)
    return env.get_template('custom')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input_path', help='path to JSON input file')
    parser.add_argument('-o', '--out-html-path', required=True)
    parser.add_argument('--out-dot-path')
    parser.add_argument('--out-svg-path')
    parser.add_argument('--out-proc-context-path')
    parser.add_argument('--dot-template-path',
        help='path to template that overrides/extends base dot template')
    parser.add_argument('--html-template-path',
        help='path to template that overrides/extends base html template')
    args = parser.parse_args()

    graph = json.loads(read_file(args.input_path))
    processGraph(graph)
    if args.out_proc_context_path is not None:
        write_file(args.out_proc_context_path, json.dumps(graph, indent=4))

    # Generate dot file
    dotTemplate = loadTemplate(args.dot_template_path, DEFAULT_DOT_TEMPLATE_PATH)
    dotGraph = dotTemplate.render(graph)
    if args.out_dot_path is not None:
        write_file(args.out_dot_path, dotGraph)

    # Generate svg
    runResult = subprocess.run(['dot', '-Tsvg_inline'], input=dotGraph, stdout=subprocess.PIPE,
        text=True, check=True)
    graph['svg'] = runResult.stdout
    if args.out_svg_path is not None:
        write_file(args.out_svg_path, graph['svg'])

    # Generate html
    css = read_file(CSS_PATH)
    graph['css'] = css
    htmlTemplate = loadTemplate(args.html_template_path, DEFAULT_HTML_TEMPLATE_PATH,
        trim_blocks=True, lstrip_blocks=True)
    html = htmlTemplate.render(graph)
    write_file(args.out_html_path, html)


if __name__ == '__main__':
    main()
