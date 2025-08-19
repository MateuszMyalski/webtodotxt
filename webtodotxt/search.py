from flask import render_template, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField


class SearchForm(FlaskForm):
    search_box = StringField(
        "Search box",
    )
    submit = SubmitField("Search")


def search_post():
    form = SearchForm()

    if not form.validate_on_submit():
        return render_template(
            "search.html", form=form, infos=[("error", "Not validated")]
        )

    query = form.search_box.data
    return redirect(url_for("main.index", filter=query))


def search_get():
    form = SearchForm()

    return render_template("search.html", form=form)
