from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from prediction_api.auth import login_required
from prediction_api.db import get_db

bp = Blueprint('predict', __name__)

@bp.route('/')
def index():
    db = get_db()
    predictions = db.execute(
        'SELECT p.id, prediction_value, prediction_input, created, user_id, username'
        ' FROM predictions p JOIN users u ON p.user_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()
    return render_template('predict/index.html', predictions=predictions)


@bp.route('/generate', methods=('GET', 'POST'))
@login_required
def generate():
    if request.method == 'POST':
        var_1 = request.form['var_1']
        var_2 = request.form['var_2']
        error = None

        if not (var_1 and var_2):
            error = 'all "variable" fields are required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO predictions (prediction_value, prediction_input, user_id)'
                ' VALUES (?, ?, ?)',
                (var_1, var_2, g.user['id'])
            )
            db.commit()
            return redirect(url_for('predict.index'))

    return render_template('predict/generate.html')
