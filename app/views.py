# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, send_from_directory

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/static/<path:path>')
def static_files():
    return send_from_directory('static', path)
