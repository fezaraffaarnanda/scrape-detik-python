from flask import Flask, render_template, request, Response
import requests as req
from bs4 import BeautifulSoup as bs
import csv
import io
import json

app = Flask(__name__)

hades = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36'}

def scrape_detik(query, hal):
    for page in range(1, hal + 1):
        url = f'https://www.detik.com/search/searchnews?query={query}&sortby=time&page={page}'
        ge = req.get(url, headers=hades).text
        sop = bs(ge, 'lxml')
        li = sop.find('div', class_='list-content')
        if li:
            lin = li.find_all('article', class_='list-content__item')
            for x in lin:
                link = x.find('a')['href']
                date = x.find('span', title=True).get('title')
                headline = x.find("a", {"class": "media__link"}).get('dtr-ttl')
                ge_ = req.get(link, headers=hades).text
                sop_ = bs(ge_, 'lxml')
                content = sop_.find_all('div', class_='detail__body-text itp_bodycontent')
                for x in content:
                    x = x.find_all('p')
                    y = [y.text for y in x]
                    content_ = ''.join(y).replace('\n', '').replace('ADVERTISEMENT', '').replace('SCROLL TO RESUME CONTENT', '')
                    yield [headline, date, link, content_]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scrape')
def scrape():
    query = request.args.get('query')
    hal = int(request.args.get('page'))

    def generate():
        for result in scrape_detik(query, hal):
            yield f"data: {json.dumps(result)}\n\n"
        yield "data: DONE\n\n"

    return Response(generate(), mimetype='text/event-stream')

@app.route('/download', methods=['POST'])
def download():
    results = request.form.getlist('results[]')
    query = request.form.get('query', 'unknown')
    pages = request.form.get('pages', '0')
    
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['Headline', 'Date', 'Link', 'Content'])
    cw.writerows([result.split('|') for result in results])
    output = si.getvalue()
    
    filename = f"{query}_{pages}_pages.csv"
    
    return Response(
        output,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )

if __name__ == '__main__':
    app.run(debug=True)