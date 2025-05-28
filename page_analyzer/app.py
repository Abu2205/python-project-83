from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
)
from dotenv import load_dotenv
import os
from urllib.parse import urlparse
import validators
import requests
from bs4 import BeautifulSoup
from page_analyzer.db import (
    add_url,
    get_url_by_id,
    get_url_by_name,
    get_all_urls,
    add_url_check,
    get_checks_by_url_id,
    update_check_status,
    get_connection,
)

load_dotenv()
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/urls", methods=["GET"])
def urls_list():
    urls = get_all_urls()
    print(f"Retrieved URLs: {urls}")
    return render_template("urls.html", urls=urls)


@app.route("/urls/<int:id>")
def url_detail(id):
    url = get_url_by_id(id)
    if not url:
        flash("URL не найден", "danger")
        return redirect(url_for("urls_list"))
    checks = get_checks_by_url_id(id)
    print(
        f"URL {id} details: {url}, Checks: {checks}"
    )
    return render_template(
        "url.html", url=url, checks=checks
    )


@app.route("/urls", methods=["POST"])
def add_url_handler():
    url = request.form.get("url", "").strip()

    if not url:
        flash("URL обязателен", "danger")
        return (
            render_template(
                "index.html", url=url
            ),
            422,
        )
    if len(url) > 255:
        flash(
            "URL превышает 255 символов", "danger"
        )
        return (
            render_template(
                "index.html", url=url
            ),
            422,
        )
    if not validators.url(url):
        flash("Некорректный URL", "danger")
        return (
            render_template(
                "index.html", url=url
            ),
            422,
        )

    parsed_url = urlparse(url)
    normalized_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

    existing_url = get_url_by_name(normalized_url)
    if existing_url:
        flash("Страница уже существует", "info")
        return redirect(
            url_for(
                "url_detail", id=existing_url[0]
            )
        )

    url_id, created = add_url(normalized_url)
    if created:
        flash(
            "Страница успешно добавлена",
            "success",
        )
    return redirect(
        url_for("url_detail", id=url_id)
    )


@app.route(
    "/urls/<int:id>/checks", methods=["POST"]
)
def run_check(id):
    url = get_url_by_id(id)
    if not url:
        flash("URL не найден", "danger")
        return redirect(url_for("urls_list"))

    check_id = add_url_check(id)
    try:
        response = requests.get(
            url[1], timeout=10
        )
        response.raise_for_status()
        status_code = response.status_code

        soup = BeautifulSoup(
            response.text, "html.parser"
        )
        h1 = (
            soup.find("h1").text.strip()
            if soup.find("h1")
            else None
        )
        title = (
            soup.title.string.strip()
            if soup.title
            else None
        )
        description = next(
            (
                meta["content"].strip()
                for meta in soup.find_all("meta")
                if meta.get("name")
                == "description"
            ),
            None,
        )

        update_check_status(
            check_id,
            status_code,
            h1,
            title,
            description,
        )
        flash(
            "Страница успешно проверена",
            "success",
        )
    except requests.RequestException as e:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM url_checks WHERE id = %s",
                    (check_id,),
                )
                conn.commit()
        flash(
            "Произошла ошибка при проверке: "
            + str(e),
            "danger",
        )
        print(f"Error during check: {e}")

    return redirect(url_for("url_detail", id=id))