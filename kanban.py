"""

Single-file Kanban board tool.

"""

# Copyright (c) 2017, Ben Zimmer
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the kanban.py nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import os
from os import path
import re
from string import Template
import sys
import time

import attr


BOOTSTRAP_CSS = "https://maxcdn.bootstrapcdn.com/bootstrap/3.3.5/css/bootstrap.min.css"
BOOTSTRAP_JS = "https://maxcdn.bootstrapcdn.com/bootstrap/3.3.5/js/bootstrap.min.js"
JQUERY_JS = "https://ajax.googleapis.com/ajax/libs/jquery/1.11.2/jquery.min.js"
STYLES_CSS = "https://maxcdn.bootstrapcdn.com/bootstrap/3.3.5/css/bootstrap-theme.min.css"
FONTS_CSS = ""
POPOVER_SCRIPT = """
  $(function(){
      // Enables popover
      $("[data-toggle=popover]").popover();
  });
"""


@attr.s(frozen=True)
class Tag(object):
    name = attr.ib()
    value = attr.ib()
    attributes = attr.ib()


@attr.s(frozen=True)
class Phase(object):
    name = attr.ib()
    wiplimit = attr.ib()


@attr.s(frozen=True)
class Person(object):
    name = attr.ib()
    image = attr.ib()


@attr.s(frozen=True)
class Category(object):
    name = attr.ib()
    color = attr.ib()


@attr.s(frozen=True)
class Task(object):
    phase = attr.ib()
    description = attr.ib()
    phase_dates = attr.ib()
    person = attr.ib()
    priority = attr.ib()
    category = attr.ib()


def read_file(input_filename):
    with open(input_filename, "r") as input_file:
        lines = input_file.readlines()

    tags = [parse_tag(re.sub("^[\\s\\*]+", "", x).strip()) for x in lines if ":" in x]

    title = [x.value for x in tags if x.name == "title"]

    if len(title) < 1:
        print "No title specified"
        sys.exit()
    else:
        title = title[0]

    phases = [parse_phase(x) for x in tags if x.name == "phase"]
    phases = [x for x in phases if x is not None]

    people = [parse_person(x) for x in tags if x.name == "person"]

    categories = [parse_category(x) for x in tags if x.name == "category"]

    phase_names = [x.name for x in phases]
    tasks = [parse_task(x, phases, people, categories) for x in tags if x.name in phase_names]

    return title, phases, people, categories, tasks


def parse_tag(line):
    split = line.split(":")
    name = split[0]
    rem = split[1].split("|")
    value = rem[0].strip()
    attributes = dict([x.strip().split("=") for x in rem[1:]])
    return Tag(name, value, attributes)


def parse_phase(tag):
    wiplimit = safe_int(tag.attributes.get("wiplimit"), 0)
    return Phase(tag.value, wiplimit)


def parse_person(tag):
    return Person(tag.value, tag.attributes.get("image"))


def parse_category(tag):
    return Category(tag.value, tag.attributes.get("color"))


def parse_task(tag, phases, people, categories):
    phase = [phase for phase in phases if tag.name == phase.name]
    if len(phase) == 0:
        print "invalid phase '" + tag.name + "'"
        sys.exit()
    phase = phase[0]

    phase_dates = dict([(x.name, tag.attributes.get(x.name)) for x in phases])

    person = [x for x in people if x.name == tag.attributes.get("person")]
    person = person[0] if len(person) > 0 else None

    category = [x for x in categories if x.name == tag.attributes.get("category")]
    category = category[0] if len(category) > 0 else None

    return Task(
        phase,
        tag.value,
        phase_dates,
        person,
        safe_int(tag.attributes.get("priority"), 10),
        category)


def safe_int(str, default):
    if str is None:
        return default
    try:
        return int(str)
    except ValueError:
        return default


def page(title, styles, body):

    page_text_template = Template("""
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="description" content="">
    <meta name="author" content="">

    <title>${title}</title>

    <!-- Fonts -->
    <link href="${fonts_css}" rel="stylesheet">

    <!-- Bootstrap core CSS -->
    <link href="${bootstrap_css}" rel="stylesheet">
    <!-- Custom styles -->
    <link href="${styles_css}" rel="stylesheet">

    <!-- HTML5 shim and Respond.js for IE8 support of HTML5 elements and media queries -->
    <!--[if lt IE 9]>
      <script src="https://oss.maxcdn.com/html5shiv/3.7.2/html5shiv.min.js"></script>
      <script src="https://oss.maxcdn.com/respond/1.4.2/respond.min.js"></script>
    <![endif]-->

    <!-- Bootstrap core JavaScript -->
    <!-- (Originally placed at the end of the document so the pages load faster) -->
    <script src="${jquery_js}"></script>
    <script src="${bootstrap_js}"></script>
    <script>${extra_scripts}</script>

    <!-- Additional styles -->
    <style>
      ${styles}
    </style>
  </head>
  <body>
    ${body}
  </body>
</html>
""")

    page_text = page_text_template.substitute(
        title=title,
        fonts_css=FONTS_CSS,
        bootstrap_css=BOOTSTRAP_CSS,
        styles_css=STYLES_CSS,
        jquery_js=JQUERY_JS,
        bootstrap_js=BOOTSTRAP_JS,
        extra_scripts=POPOVER_SCRIPT,
        styles=styles,
        body=body)

    return page_text


def render_board(phases, people, categories, tasks):

    # split tasks by phase
    def extract_tasks(phase):
        pts = [x for x in tasks if x.phase.name == phase.name]
        pts_sorted = sorted(pts, key=lambda x: (x.priority, x.category))
        return pts_sorted
    tasks_by_phase = [extract_tasks(x) for x in phases]

    def column_text(pts, phase):
        if len(pts) > phase.wiplimit:
            wip_style = "text-center text-danger"
        else:
            wip_style = "text-center"
        return (
            h3_center(phase.name) + br() +
            p(b(str(len(pts)) + " / " + str(phase.wiplimit)), wip_style) +
            "".join([task_text(x) for x in pts]))

    def task_text(task):
        return panel(
            task.description,
            b("Person: ") + ("None" if task.person is None else task.person.name) + br() +
            b("Priority: ") + ("None" if task.priority is None else str(task.priority)) + br() +
            b("Category: ") + ("None" if task.category is None else  task.category.name),
            None if task.category is None else "background:" + task.category.color + ";")

    columns_text = [column_text(pts, phase)
                    for pts, phase in zip(tasks_by_phase, phases)]

    return container(row("".join([col(x) for x in columns_text])))


def b(text):
    """bold tag"""
    return "<b>" + text + "</b>"


def p(text, css_class):
    """paragraph tag"""
    return "<p class=\"" + css_class + "\">" + text + "</p>\n"


def h3_center(text):
    return """<h3 class="text-center">""" + text + "</h3>\n"


def br():
    """break tag"""
    return "<br />"


def container(text):
    """bootstrap container"""
    return Template("""
<div class="container">
  ${text}
</div>""").substitute(text=text)


def row(text):
    """bootstrap row"""
    return Template("""
<div class="row">
  ${text}
</div>""").substitute(text=text)


def col(text):
    """bootstrap column"""
    return Template("""
<div class="col-md-3 col-sm-4 col-lg">
  ${text}
</div>""").substitute(text=text)


def panel(text, popover_content, style):
    """bootstrap panel"""
    style_string = "" if style is None else "style=\"" + style + "\""
    panel_template = Template("""
<div class="panel panel-default" data-toggle="popover" data-trigger="hover click" data-html="true" data-placement="bottom" data-content="${popover_content}">
  <!-- <div class="panel-heading">Panel Heading</div> -->
  <div class="panel-body"  ${style_string}>${text}</div>
</div>""")
    return panel_template.substitute(
        popover_content=popover_content,
        text=text,
        style_string=style_string)


def print_board(phases, people, categories, tasks):
    """Print the board."""
    for phase in phases:
        phase_tasks = [x for x in tasks if x.phase.name == phase.name]
        phase_tasks = sorted(phase_tasks, key=lambda x: x.priority)

        title_string = (phase.name.upper() + " - " +
                        str(len(phase_tasks)) + " / " + str(phase.wiplimit))
        print title_string
        print "-" * len(title_string)

        for task in phase_tasks:
            print "-", task.description
            if task.person is not None:
                print "  - person:", task.person.name
            if task.priority is not None:
                print "  - priority:", task.priority
            if task.category is not None:
                print "  - category:", task.category.name
        print
    print


def main(argv):
    """Main program."""

    start_time = time.time()
    if len(argv) < 2 or len(argv) > 3:
        print "usage: python -m kanban input_file output_dir"
        sys.exit(1)

    input_filename = argv[1]
    output_dirname = argv[2]

    print "input file:", input_filename
    print "output dir:", output_dirname
    print

    title, phases, people, categories, tasks = read_file(input_filename)

    print_board(phases, people, categories, tasks)

    if not path.exists(output_dirname):
        os.makedirs(output_dirname)

    board_text = render_board(phases, people, categories, tasks)

    page_text = page("test", "", board_text)

    index_filename = path.join(output_dirname, "index.html")
    with open(index_filename, "w") as output_file:
        output_file.write(page_text)

    os.system(index_filename)

    end_time = time.time()
    print "total time:", end_time - start_time


if __name__ == "__main__":
    main(sys.argv)
