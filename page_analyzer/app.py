import os
from flask import Flask, render_template, request, redirect, flash, url_for
from page_analyzer.db import get_connection
from urllib.parse import urlparse
import validators
import requests
from bs4 import BeautifulSoup
import psycopg2
from datetime import datetime
import psycopg2.extras

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/urls', methods=['POST'])
def add_url():
    url = request.form.get('url', '').strip()
    
    # Валидация URL
    if not url:
        flash('URL обязателен', 'danger')
        return render_template('index.html')
    
    if not validators.url(url):
        flash('Некорректный URL', 'danger')
        return render_template('index.html', url=url)
    
    if len(url) > 255:
        flash('URL превышает 255 символов', 'danger')
        return render_template('index.html', url=url)

    # Нормализация URL
    parsed_url = urlparse(url)
    normalized_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Проверяем, существует ли уже такой URL
                cur.execute("SELECT id FROM urls WHERE name = %s", (normalized_url,))
                row = cur.fetchone()
                
                if row:
                    flash('Страница уже существует', 'info')
                    return redirect(url_for('url_show', id=row[0]))
                
                # Добавляем новый URL
                cur.execute(
                    "INSERT INTO urls (name, created_at) VALUES (%s, %s) RETURNING id", 
                    (normalized_url, datetime.now())
                )
                new_id = cur.fetchone()[0]
                conn.commit()
                
        flash('Страница успешно добавлена', 'success')
        return redirect(url_for('url_show', id=new_id))
        
    except Exception as e:
        flash('Произошла ошибка при добавлении страницы', 'danger')
        return render_template('index.html', url=url)

@app.route('/urls/<int:id>')
def url_show(id):
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # Получаем информацию о URL
                cur.execute('SELECT * FROM urls WHERE id = %s', (id,))
                url = cur.fetchone()
                
                if not url:
                    flash('Страница не найдена', 'danger')
                    return redirect(url_for('urls'))
                
                # Получаем все проверки для этого URL
                cur.execute(
                    'SELECT * FROM url_checks WHERE url_id = %s ORDER BY created_at DESC', 
                    (id,)
                )
                checks = cur.fetchall()
                
        return render_template('url.html', url=url, checks=checks)
        
    except Exception as e:
        flash('Произошла ошибка при загрузке страницы', 'danger')
        return redirect(url_for('urls'))

@app.route('/urls')
def urls():
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute('''
                    SELECT 
                        urls.id,
                        urls.name,
                        urls.created_at,
                        MAX(url_checks.created_at) AS last_check,
                        (SELECT status_code FROM url_checks 
                         WHERE url_id = urls.id 
                         ORDER BY created_at DESC LIMIT 1) AS last_status_code
                    FROM urls
                    LEFT JOIN url_checks ON urls.id = url_checks.url_id
                    GROUP BY urls.id, urls.name, urls.created_at
                    ORDER BY urls.created_at DESC
                ''')
                urls_data = cur.fetchall()
                
        return render_template('urls.html', urls=urls_data)
        
    except Exception as e:
        flash('Произошла ошибка при загрузке списка сайтов', 'danger')
        return render_template('urls.html', urls=[])

@app.route('/urls/<int:id>/checks', methods=['POST'])
def url_check(id):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Получаем URL по ID
                cur.execute('SELECT name FROM urls WHERE id = %s', (id,))
                row = cur.fetchone()
                
                if not row:
                    flash('Сайт не найден', 'danger')
                    return redirect(url_for('urls'))

                url = row[0]

                # Выполняем HTTP-запрос
                try:
                    response = requests.get(url, timeout=10)
                    status_code = response.status_code
                    
                    # Парсим HTML только если запрос успешен
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Извлекаем h1
                        h1_tag = soup.find('h1')
                        h1 = h1_tag.get_text(strip=True) if h1_tag else ''
                        
                        # Извлекаем title
                        title_tag = soup.find('title')
                        title = title_tag.get_text(strip=True) if title_tag else ''
                        
                        # Извлекаем description
                        meta_desc = soup.find('meta', attrs={'name': 'description'})
                        description = meta_desc.get('content', '').strip() if meta_desc else ''
                    else:
                        h1 = title = description = ''
                        
                except requests.RequestException as e:
                    flash('Произошла ошибка при проверке сайта', 'danger')
                    return redirect(url_for('url_show', id=id))

                # Сохраняем результаты проверки
                cur.execute('''
                    INSERT INTO url_checks (url_id, status_code, h1, title, description, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (id, status_code, h1[:255], title[:255], description[:255], datetime.now()))
                
                conn.commit()
                flash('Страница успешно проверена', 'success')
                
    except Exception as e:
        flash('Произошла ошибка при проверке', 'danger')
    
    return redirect(url_for('url_show', id=id))

if __name__ == '__main__':
    app.run(debug=True)