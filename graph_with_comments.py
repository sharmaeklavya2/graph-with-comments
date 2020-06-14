#!/usr/bin/env python3

import os
from os.path import join as pjoin
import argparse
import json
import subprocess

from jinja2 import Template


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOT_TEMPLATE_PATH = pjoin(BASE_DIR, 'graph.dot.jinja2')
HTML_TEMPLATE_PATH = pjoin(BASE_DIR, 'page.html.jinja2')
CSS_PATH = pjoin(BASE_DIR, 'style.css')


def read_file(fpath):
    with open(fpath) as fp:
        return fp.read()


def write_file(fpath, s):
    with open(fpath, 'w') as fp:
        fp.write(s)


def process_vertices(context):
    inferred_linking = False
    vertices, link_vertices = context['vertices'], context.get('link_vertices')
    # link_vertices can be True, False or None
    for vid, vinfo in vertices.items():
        vinfo['id'] = vid
        if link_vertices is None:
            vinfo['link'] = (vinfo.get(context['vertex_list_label']) is not None
                or vinfo.get('text') is not None)  # noqa
            if vinfo['link']:
                inferred_linking = True
        else:
            vinfo['link'] = link_vertices
        if vinfo.get('name') is None:
            vinfo['name'] = vinfo['id']
    return inferred_linking


def process_edges(context):
    vertices, edges, link_edges = context['vertices'], context['edges'], context.get('link_edges')
    inferred_linking = False
    for i, edge in enumerate(edges):
        edge['id'] = i + 1
        edge['from'] = vertices[edge['from']]
        edge['to'] = vertices[edge['to']]
        if link_edges is None:
            edge['link'] = context['vertex_edge_label'] != 'id' or edge.get('text') is not None
            if edge['link']:
                inferred_linking = True
        else:
            edge['link'] = link_edges
    return inferred_linking


def process_context(context):
    context['vertex_graph_label'] = context.get('vertex_graph_label', 'id')
    context['vertex_list_label'] = context.get('vertex_list_label', 'name')
    context['vertex_edge_label'] = context.get('vertex_edge_label', 'id')

    link_vertices = process_vertices(context)
    if context.get('link_vertices') is None:
        context['link_vertices'] = link_vertices
    link_edges = process_edges(context)
    if context.get('link_edges') is None:
        context['link_edges'] = link_edges
    return context


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input_path', help='path to JSON input file')
    parser.add_argument('-o', '--out-html-file', required=True, dest='out_html_path')
    parser.add_argument('--out-dot-path')
    parser.add_argument('--out-svg-path')
    parser.add_argument('--out-proc-context-path')
    args = parser.parse_args()

    context = process_context(json.loads(read_file(args.input_path)))
    if args.out_proc_context_path is not None:
        write_file(args.out_proc_context_path, json.dumps(context, indent=4))

    # Generate dot file
    dot_template = Template(read_file(DOT_TEMPLATE_PATH))
    dot_graph = dot_template.render(context)
    if args.out_dot_path is not None:
        write_file(args.out_dot_path, dot_graph)

    # Generate svg
    run_result = subprocess.run(['dot', '-Tsvg'], input=dot_graph, stdout=subprocess.PIPE,
        text=True, check=True)
    context['svg'] = run_result.stdout
    if args.out_svg_path is not None:
        write_file(args.out_svg_path, context['svg'])

    # Generate html
    css = read_file(CSS_PATH)
    context['css'] = css
    html_template = Template(read_file(HTML_TEMPLATE_PATH), trim_blocks=True, lstrip_blocks=True)
    html = html_template.render(context)
    write_file(args.out_html_path, html)


if __name__ == '__main__':
    main()
