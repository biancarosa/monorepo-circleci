#!/usr/bin/env python3

import os
import subprocess

import jinja2


def _render_file(filename, **variables) -> str:
    dirname = os.path.dirname(filename)
    loader = jinja2.FileSystemLoader(dirname)
    relpath = os.path.relpath(filename, dirname)
    return _render(relpath, loader, variables)


def _render(template_name, loader, variables) -> str:
    env = jinja2.Environment(loader=loader, undefined=jinja2.Undefined)

    template = env.get_template(template_name)
    output = template.render(variables)

    # jinja2 cuts the last newline
    source, _, _ = loader.get_source(env, template_name)
    if source.split("\n")[-1] == "" and output.split("\n")[-1] != "":
        output += "\n"

    return output


def checkout(revision) -> None:
    """
    Helper function for checking out a branch

    :param revision: The revision to checkout
    :type revision: str
    """
    subprocess.run(["git", "checkout", revision], check=True)


def is_pull_request() -> bool:
    print(os.environ.get("CIRCLE_PULL_REQUEST"))
    return True if os.environ.get("CIRCLE_PULL_REQUEST") else False


def check_diff_between_branch_and_base() -> []:
    changes = []
    try:
        head = os.environ.get("CIRCLE_SHA1")
        base_revision = "main"
        checkout(
            base_revision
        )  # Checkout base revision to make sure it is available for comparison
        checkout(head)  # return to head commit

        base = (
            subprocess.run(
                ["git", "merge-base", base_revision, head], check=True, capture_output=True
            )
            .stdout.decode("utf-8")
            .strip()
        )

        if head == base:
            try:
                # If building on the same branch as BASE_REVISION, we will get the
                # current commit as merge base. In that case try to go back to the
                # first parent, i.e. the last state of this branch before the
                # merge, and use that as the base.
                base = (
                    subprocess.run(
                        [
                            "git",
                            "rev-parse",
                            "HEAD~1",
                        ],  # FIXME this breaks on the first commit, fallback to something
                        check=True,
                        capture_output=True,
                    )
                    .stdout.decode("utf-8")
                    .strip()
                )
            except Exception:
                # This can fail if this is the first commit of the repo, so that
                # HEAD~1 actually doesn't resolve. In this case we can compare
                # against this magic SHA below, which is the empty tree. The diff
                # to that is just the first commit as patch.
                base = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
        print("Comparing {}...{}".format(base, head))
        changes = (
            subprocess.run(
                ["git", "diff", "--name-only", base, head], check=True, capture_output=True
            )
            .stdout.decode("utf-8")
            .splitlines()
        )
    except Exception:
        print("No changes found")

    return changes


def generate_output(changes=[]) -> bytes:
    variables ={
        'backend/api' : {
            'filename': 'build/api.yml',
            'executor' : 'python/default',
            'working_dir': ' ~/backend/api',
            'jobname': 'backend-api'
        },
        'backend/consumer' : {
            'filename': 'build/consumer.yml',
            'executor' : 'python/default',
            'working_dir': ' ~/backend/consumer',
            'jobname': 'backend-consumer'
        },
        'frontend' : {
            'filename': 'build/frontend.yml',
            'executor' : 'node/default',
            'working_dir': ' ~/frontend',
            'jobname': 'frontend'
        }
    }
    print(changes)
    builds = {}
    for k in variables:
        for c in changes:
            if k in c:
                builds[k] = variables[k]
    if len(builds) == 0:
        print("Building all...")
        builds = variables
    output = _render_file("./.circleci/ci-template.yml", builds=builds)
    return output


def main() -> None:
    if is_pull_request():
        print("It is a PR")
        changes = check_diff_between_branch_and_base()
        content = generate_output(changes)
    else:
        print("It is not a PR")
        content = generate_output()
    print(content)
    output_filename = "generated_config.yml"
    with open(output_filename, "wb") as f:
        f.write(content.encode("utf-8"))


if __name__ == "__main__":
    main()
