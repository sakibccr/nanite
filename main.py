from datetime import datetime
from pathlib import Path
from distutils.dir_util import copy_tree
from jinja2 import Environment, FileSystemLoader, select_autoescape, TemplateNotFound
import markdown
from settings import THEME_NAME, CONTENT_DIR_NAME, OUTPUT_DIR_NAME, SITE_VARIABLES


def read_header(text, sep="---"):
    """
    Splits the text by the separator.
    Then the first item is disintegrated into a dictionary.
    That dictionary is the variables from the header part of a page.
    I call them header variables.
    """
    headers = text.split(sep)[0].strip().split("\n")

    post_vars = {
        k.strip(): v.strip() for k, v in [header.split(":", 1) for header in headers]
    }

    if "draft" in post_vars and post_vars["draft"].lower() == "true":
        post_vars["draft"] = True
    else:
        post_vars["draft"] = False

    if "created" in post_vars:
        post_vars["created"] = datetime.fromisoformat(post_vars["created"])
    else:
        post_vars["created"] = datetime.now()

    return post_vars


def read_posts(directory):
    """
    Reads all the files in a directory and converts them into a list of dictionary.
    One dict contains everything about one file.
    """
    posts = []
    for child in directory.iterdir():
        if child.is_file() and child.name.endswith(".md"):
            text = child.read_text()
            post = {
                "content": markdown.markdown(text.split("---")[-1].strip()),
                "file": child,
            }
            post.update(read_header(text))

            if not post["draft"]:
                posts.append(post)
    return posts


def get_template(env, data):
    """
    Returns the appropriate type of template determined from data
    """
    if isinstance(data, list):
        return env.get_template("list.html")

    try:
        return env.get_template(data["file"].name.replace(".md", ".html"))
    except TemplateNotFound:
        pass

    return env.get_template("single.html")


def write_posts(env, output_dir, posts):
    for idx, post in enumerate(posts):
        template = get_template(env, post)
        html = template.render(post=post, **SITE_VARIABLES)
        filename = output_dir / post["file"].name.replace(".md", ".html")
        filename.write_text(html)
        posts[idx]["path"] = filename.name
    return posts


def write_list(env, output_dir, posts):
    template = get_template(env, posts)
    html = template.render(posts=posts, **SITE_VARIABLES)
    list_file = output_dir / "index.html"
    list_file.write_text(html)
    return list_file


def copy_staticfiles(templates_dir, output_dir):
    copy_tree(str(templates_dir / "static"), str(output_dir / "static"))


def main():
    BASE_DIR = Path(__file__).parent.absolute()
    content_dir = BASE_DIR / CONTENT_DIR_NAME
    output_dir = BASE_DIR / OUTPUT_DIR_NAME
    templates_dir = BASE_DIR / "themes" / THEME_NAME

    # create a new output directory even if one exists
    output_dir.mkdir(parents=True, exist_ok=True)

    posts = read_posts(content_dir)

    env = Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=select_autoescape(),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    posts = write_posts(env, output_dir, posts)
    write_list(env, output_dir, posts)
    copy_staticfiles(templates_dir, output_dir)


main()
