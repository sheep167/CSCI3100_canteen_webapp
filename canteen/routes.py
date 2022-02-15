from canteen import app
from flask import render_template


@app.route('/', methods=['GET'])
def home_page():
    return render_template('home_page.html')
