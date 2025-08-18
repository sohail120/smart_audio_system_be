from flask import Blueprint, render_template

ui_bp = Blueprint('ui', __name__)

@ui_bp.route('/')
def home():
    return render_template('index.html')

@ui_bp.route('/result-page/<string:file_id>')
def result(file_id):
    return render_template('result.html', file_id=file_id)
