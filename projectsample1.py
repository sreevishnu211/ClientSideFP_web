from flask import Flask, render_template, jsonify, redirect, request
import face_recognition
from flask_pymongo import PyMongo
from numpy import array

app = Flask(__name__)

app.config['MONGO_DBNAME'] = 'admin'
app.config['MONGO_URI'] = 'mongodb://admin:1234@localhost:27017/admin'
mongo = PyMongo(app)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def detect_faces_in_image(file_stream):
    known_face_encoding = [-0.1649552, 0.13401355, 0.05516857, -0.01164937, -0.00166567,
                           -0.0509211, 0.01381511, 0.01031353, 0.13141859, 0.02188031,
                           0.24959894, 0.0155438, -0.16957857, -0.17130299, -0.00856864,
                           0.12352721, -0.06003122, -0.13988888, -0.10035978, -0.09299699,
                           0.04236951, 0.00703817, -0.03020944, 0.01856286, -0.15346573,
                           -0.35141581, -0.06282666, -0.13314885, -0.00290594, -0.09133524,
                           0.03331999, 0.03044619, -0.20005885, -0.0686389, 0.00597119,
                           0.11690811, 0.04024971, -0.03331555, 0.17072728, -0.04288237,
                           -0.10720912, -0.02524333, 0.09641182, 0.26672766, 0.15032755,
                           -0.02915591, 0.03510844, 0.02454352, 0.09962389, -0.26585963,
                           0.0859708, 0.07615338, 0.09336157, 0.08913936, 0.13320528,
                           -0.13085134, 0.0134411, 0.11807568, -0.25288349, -0.00662292,
                           -0.0876106, 0.01576828, -0.1386525, -0.0711746, 0.23227528,
                           0.19955763, -0.10880195, -0.1404044, 0.14619486, -0.13927692,
                           0.04595419, 0.10092922, -0.08155489, -0.14100173, -0.26284462,
                           0.14437926, 0.44835603, 0.13620703, -0.18057272, 0.1008053,
                           -0.10218421, -0.05700202, 0.048289, -0.06231377, -0.07752553,
                           0.06646018, -0.09250712, 0.0761778, 0.16689818, 0.06489497,
                           -0.05985761, 0.14182988, -0.03928234, 0.06337542, 0.04528295,
                           0.00769243, -0.02698882, -0.00691607, -0.08820476, 0.01932585,
                           0.0719667, -0.0920478, -0.02015581, 0.0266807, -0.14656655,
                           0.07644067, 0.0573869, 0.03349284, -0.02575551, 0.06660458,
                           -0.11182937, 0.00670396, 0.13173267, -0.29141042, 0.25009516,
                           0.07165, -0.0929575, 0.15322635, 0.07546778, 0.04296182,
                           0.00631781, -0.06807842, -0.11759381, -0.04145756, 0.06039871,
                           -0.04791883, 0.07702737, 0.04080973]
    img = face_recognition.load_image_file(file_stream)
    unknown_face_encoding = face_recognition.face_encodings(img)
    face_found = False
    is_person = False

    if len(unknown_face_encoding) > 0:
        face_found = True
        match_results = face_recognition.compare_faces([known_face_encoding], unknown_face_encoding[0])
        if match_results[0]:
            is_person = True

    result = {
        "face_found_in_image": face_found,
        "is_picture_of_the_person_i_needed": is_person
    }
    return jsonify(result)


def encodeandstore(name, file_stream):
    img = face_recognition.load_image_file(file_stream)
    img_encoding = face_recognition.face_encodings(img)
    image_data = mongo.db.image_data
    image_id = image_data.insert({'name': name, 'imgenc': img_encoding[0].tolist()})
    return 'all OK'


# Gives wrong output
def custom_detect_faces_in_image(file_stream):
    img = face_recognition.load_image_file(file_stream)
    img_encoding = face_recognition.face_encodings(img)
    image_data = mongo.db.image_data
    present_in_pic = []
    for d in image_data.find():
        if face_recognition.compare_faces([array(d['imgenc'])], img_encoding)[0] and d['name'] not in present_in_pic:
            present_in_pic.append(d['name'])

    return jsonify(present_in_pic)


# Gives slightly wrong output like naming 4 people when 3 people are present and wrong matching
def custom_detect_faces_in_image_two(file_stream):
    img = face_recognition.load_image_file(file_stream)
    img_encoding = face_recognition.face_encodings(img)
    image_data = mongo.db.image_data
    present_in_pic = []
    for u in img_encoding:
        for d in image_data.find():
            if face_recognition.compare_faces([array(d['imgenc'])], u)[0] and d['name'] not in present_in_pic:
                present_in_pic.append(d['name'])

    return jsonify(present_in_pic)


# didnt see much difference but the code looks great
def custom_detect_faces_in_image_three(file_stream):
    img = face_recognition.load_image_file(file_stream)
    img_encoding = face_recognition.face_encodings(img)
    image_data = mongo.db.image_data
    present_in_pic = []
    all_names = []
    known_enc = []
    for d in image_data.find():
        known_enc.append(array(d['imgenc']))
        all_names.append(d['name'])

    for u in img_encoding:
        a = face_recognition.compare_faces(known_enc, u)
        for y, z in zip(all_names, a):
            if z and y not in present_in_pic:
                present_in_pic.append(y)

    return jsonify(present_in_pic)


@app.route('/', methods=['GET', 'POST'])
def hello_world():
    if request.method == "POST":
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']

        if file.filename == '':
            return redirect(request.url)

        if file and allowed_file(file.filename):
            return custom_detect_faces_in_image_three(file)

    return render_template("index.html")




@app.route('/encodeimage', methods=['GET', 'POST'])
def encodeimage():
    if request.method == "POST":
        if 'file' not in request.files or 'name' not in request.form:
            return redirect(request.url)
        file = request.files['file']
        name = request.form['name']

        if file.filename == '':
            return redirect(request.url)

        if file and allowed_file(file.filename):
            return encodeandstore(name, file)

    return render_template("encodeimage.html")


	




if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=True)
