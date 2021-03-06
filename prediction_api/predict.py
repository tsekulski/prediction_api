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

from sklearn.preprocessing import Imputer, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.externals import joblib


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
        mean_radius = float(request.form['mean_radius'])
        mean_texture = float(request.form['mean_texture'])
        mean_perimeter = float(request.form['mean_perimeter'])
        mean_area = float(request.form['mean_area'])
        mean_smoothness = float(request.form['mean_smoothness'])
        error = None

        if not (mean_radius and mean_texture and mean_perimeter and mean_area and mean_smoothness):
            error = 'all "variable" fields are required.'

        if error is not None:
            flash(error)
        else:
            col_names = ['mean_radius', 'mean_texture', 'mean_perimeter', 'mean_area', 'mean_smoothness']
            input_variables =  [[mean_radius], [mean_texture], [mean_perimeter], [mean_area], [mean_smoothness]]
            zipped = list(zip(col_names, input_variables))
            prediction_data = dict(zipped)

            server_response = requests.post(url_for('predict.predict_from_json', _external=True), json=prediction_data)
            # _external=True keyword needed to generate absolute URL which is needed by requests module

            predicted_value = server_response.json()[0] # taking first value from json response list

            db = get_db()
            db.execute(
                'INSERT INTO predictions (prediction_value, prediction_input, user_id)'
                'VALUES (?, ?, ?)',
                #(predicted_value, ' '.join(str(e) for e in input_variables), g.user['id'])
                (predicted_value, json.dumps(prediction_data), g.user['id'])
                # input_variables must be converted to string before inserting into db, json.dumps achieves that
            )
            db.commit()

            return redirect(url_for('predict.index'))

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
     json_ = request.json  # this loads json data into a dict called json_
     model = joblib.load('wisconsin_model.pkl')
     #model_columns = joblib.load('wisconsin_col_names.pkl')

     #joblib.dump(json_, 'test_dump.pkl')

     query_df = pd.DataFrame(json_, columns=json_.keys())
     # !!! the above makes sure column order is kept. mixing up row order needs to be tested as well !!!

     #prediction = query_df.sum(axis=1).values
     prediction = model.predict_proba(query_df)[:,1]
     #prediction = query_df.to_dict()

     #query_df = pd.DataFrame(json_)
     #query = pd.get_dummies(query_df)
     #prediction = clf.predict(query)
     #return jsonify({'prediction': list(prediction)})

     return jsonify(prediction.tolist())
     #return jsonify(prediction)