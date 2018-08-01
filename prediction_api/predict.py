from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
)
from werkzeug.exceptions import abort

from prediction_api.auth import login_required
from prediction_api.db import get_db

import json
import requests
import pandas as pd
import numpy as np

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
        var_1 = float(request.form['var_1'])
        var_2 = float(request.form['var_2'])
        var_3 = float(request.form['var_3'])
        error = None

        if not (var_1 and var_2 and var_3):
            error = 'all "variable" fields are required.'

        if error is not None:
            flash(error)
        else:
           # input_variables = [var_1, var_2, var_3]
            #predicted_value = generate_prediction(input_variables)
            #db = get_db()
            #db.execute(
            #    'INSERT INTO predictions (prediction_value, prediction_input, user_id)'
            #    ' VALUES (?, ?, ?)',
            #    (predicted_value, ' '.join(str(e) for e in input_variables), g.user['id'])
            #    # input_variables must be converted to string before inserting into db
            #)
            #db.commit()

            col_names = ['var_1', 'var_2', 'var_3']
            input_variables =  [[var_1], [var_2], [var_3]]
            zipped = list(zip(col_names, input_variables))
            prediction_data = dict(zipped)

            #return redirect(url_for('predict.predict_from_json'))

            res = requests.post('http://127.0.0.1:5000/predict_from_json', json=prediction_data)
            return(res.json)

            #return redirect(url_for('predict.index'))

    return render_template('predict/generate.html')


def get_prediction(id, check_user=True):
    prediction = get_db().execute(
        'SELECT p.id, prediction_value, prediction_input, created, user_id, username'
        ' FROM predictions p JOIN users u ON p.user_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if prediction is None:
        abort(404, "Prediction id {0} doesn't exist.".format(id))

    if check_user and prediction['user_id'] != g.user['id']:
        abort(403)

    return prediction


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_prediction(id)
    db = get_db()
    db.execute('DELETE FROM predictions WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('predict.index'))


def generate_prediction(input_variables):
    predicted_value = 0

    for variable in input_variables:
        predicted_value += variable

    return predicted_value


@bp.route('/predict_from_json', methods=['POST'])
#@login_required
def predict_from_json():
     json_ = request.json

     #loaded_dict = json.loads(json_)

     query_df = pd.DataFrame(json_, columns=json_.keys())

     prediction = query_df.sum(axis=1).values
     #prediction = np.array([2, 3])

     #query_df = pd.DataFrame(json_)
     #query = pd.get_dummies(query_df)
     #prediction = clf.predict(query)
     #return jsonify({'prediction': list(prediction)})

     return jsonify(prediction.tolist())