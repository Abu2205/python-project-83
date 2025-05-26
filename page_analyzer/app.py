import os
from flask import Flask, render_template, request, redirect, flash, url_for
from page_analyzer.db import get_connection
from urllib.parse import urlparse
import validators

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/urls', methods=['POST'])
def add_url():
    url = request.form.get('url')
    if not validators.url(url) or len(url) > 255:
        flash('Некорректный URL', 'danger')
        return render_template('index.html', url=url)

    parsed_url = urlparse(url)
    normalized_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM urls WHERE name = %s", (normalized_url,))
            row = cur.fetchone()
            if row:
                flash('Страница уже существует', 'info')
                return redirect(url_for('show_url', id=row[0]))
            cur.execute("INSERT INTO urls (name) VALUES (%s) RETURNING id", (normalized_url,))
            new_id = cur.fetchone()[0]
            conn.commit()
    flash('Страница успешно добавлена', 'success')
    return redirect(url_for('show_url', id=new_id))

@app.route('/urls/<int:id>')
def url_show(id):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute('SELECT * FROM urls WHERE id = %s;', (id,))
    url = cur.fetchone()

    cur.execute('SELECT * FROM url_checks WHERE url_id = %s ORDER BY id DESC;', (id,))
    checks = cur.fetchall()

    return render_template('url.html', url=url, checks=checks)

@app.route('/urls')
def urls():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM urls ORDER BY id DESC")
            urls = cur.fetchall()
    return render_template('urls.html', urls=urls)

@app.post('/urls/<int:id>/checks')
def url_check(id):
    conn = get_connection()
    with conn:
        conn.execute(
            'INSERT INTO url_checks (url_id) VALUES (%s)', (id,)
        )
    flash('Страница успешно проверена', 'success')
    return redirect(url_for('show_url', id=id))