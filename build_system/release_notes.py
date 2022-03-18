# -*- coding: utf-8 -*-
# @Author: lnorb.com
# @Date:   2022-01-14 06:37:53
# @Last Modified by:   lnorb.com
# @Last Modified time: 2022-03-18 08:42:02

import os

from invoke import task
from textwrap import wrap


@task
def create(c, env=dict(PATH=os.environ["PATH"])):
    cmd = lambda x: c.run(x, env=env, hide=True).stdout
    tags = (
        [
            x.split("/")[-1]
            for x in cmd(
                "git for-each-ref --sort=creatordate  refs/tags | cut -f 2"
            ).split("\n")
            if x
        ]
        + ["HEAD"]
    )[::-1]
    current_version = open("VERSION").read().strip()
    notes = ""
    for prev_tag, tag in zip(tags, tags[1:]):
        print(prev_tag, tag)
        notes += f"{(prev_tag, current_version)[prev_tag == 'HEAD']:}\n{'-'*len(prev_tag)}\n\n"
        tag_commits = cmd(f"git log {tag}..{prev_tag} --oneline")
        notes += (
            "\n".join(
                "\n".join(wrap(x[8:], width=70, subsequent_indent="    "))
                for x in tag_commits.split("\n")
            )
            + "\n\n"
        )
    open("orb/dialogs/help_dialog/release_notes/release_notes.txt", "w").write(notes)
