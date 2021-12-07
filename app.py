from flask import Flask, render_template, redirect, url_for, request, jsonify
from sqlalchemy.engine import create_engine
import joblib
import psycopg2
from flask_cors import CORS
import os

app = Flask(__name__)

CORS(app)

PASSWORD = os.getenv('PASSWORD')

DATABASE_URI = f"postgresql+psycopg2://henorakrtnepye:{PASSWORD}@ec2-34-233-214-228.compute-1.amazonaws.com:5432/dfq5ifardm38b6"
engine = create_engine(DATABASE_URI)


# landing page
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/training_data")
def training_data():
    result = engine.execute("select * from survival")
    rows = result.fetchall()
    result_list = []
    for r in rows:
        result_list.append(dict(r))
    return jsonify(result_list)


@app.route("/api/clinical_raw")
def clinical_raw():
    result = engine.execute("select * from clinical_raw")
    rows = result.fetchall()
    result_list = []
    for r in rows:
        result_list.append(dict(r))
    return jsonify(result_list)


@app.route("/api/new_data")
def new_data():
    result = engine.execute("select * from input_data")
    rows = result.fetchall()
    result_list = []
    for r in rows:
       result_list.append(r)

    return render_template('new_data.html', new_data_list = result_list)


loaded_model = joblib.load('static/models/randomForest_model.pkl')
loaded_scaler = joblib.load('static/models/scaler.pkl')

@app.route("/predict", methods=['POST', 'GET'])

def predict():
    if request.method == "POST":

        input_data = []

        for i in range (1,20):
            element_num = f"f{i}"
            requests = request.form[element_num]
            input_data.append(requests)
        
        predict_data = [input_data]
        scaled_data = loaded_scaler.transform(predict_data)
        result = (loaded_model.predict(scaled_data)).tolist()

        insert_data = input_data
        insert_data.append(result[0])

        conn = psycopg2.connect(database='dfq5ifardm38b6', user='henorakrtnepye', password=PASSWORD, host='ec2-34-233-214-228.compute-1.amazonaws.com', port= '5432')
        cur = conn.cursor()
        cur.execute("INSERT INTO input_data(age_at_diagnosis,chemotherapy,neoplasm_histologic_grade,hormone_therapy,lymph_nodes_examined_positive,mutation_count,radio_therapy,tumor_size,tumor_stage,encoded_type_of_breast_surgery,encoded_cancer_type_detailed,encoded_cellularity,encoded_pam50,encoded_er_status,encoded_her2_status,encoded_tumor_other_histologic_subtype,encoded_inferred_menopausal_state,encoded_integrative_cluster,encoded_pr_status,prediction) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s ,%s, %s, %s, %s, %s, %s)", insert_data)
        cur.close()
        conn.commit()
        conn.close()
        return render_template('predict.html', outcome=result[0], values = input_data)
        
    else:   
        return render_template("predict.html")


if __name__ == '__main__':
    app.run(debug=True)