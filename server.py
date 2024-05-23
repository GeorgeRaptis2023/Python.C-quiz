from flask import Flask,redirect, url_for,request, session, json
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import datetime,re,os,random
total_questions = 6
allQuiz = {}
class Quiz:
    def __init__(self, id, question, replies, correct):
        self.id = id
        self.question = question
        self.replies = replies
        self.correct = correct
        allQuiz[id] = self
def load_quiz():
    id = None
    code = False
    replies = {}
    question = ""
    for line in open(os.path.join("", "questions.txt"), "r", encoding="utf-8"):
        if not line.strip(): continue
        if line.startswith("Q") or line.startswith("T"): 
            if id: Quiz(id, question, replies, correct)
            id = line.strip().strip(".")
            question = ""
            replies = {}
        elif re.findall("^[1-9]+?\.", line):
            reply_number = int(line.split()[0].strip("."))
            if line.strip().endswith("***"):
                correct = reply_number
                line = line.strip().rstrip("***")
            reply_body = " ".join(line.split()[1:])
            replies[reply_number] = reply_body.strip()
        else:question += line
def draw_questions():
    all_quiz_keys = list(allQuiz.keys())
    random.shuffle(all_quiz_keys)
    return all_quiz_keys[:total_questions]
def show_question(id):
    if id in allQuiz.keys():
        return {"id": allQuiz[id].id,"question": allQuiz[id].question,
        "replies": {**allQuiz[id].replies, **{len(allQuiz[id].replies)+1: "Δεν γνωρίζω"}},"correct": allQuiz[id].correct}


load_quiz() 
app = Flask(__name__)
app.config['SECRET_KEY'] = "a-very-secret-key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

db = SQLAlchemy(app)

class User(db.Model):
    username = db.Column(db.String(80), primary_key=True)
    password = db.Column(db.String(250), nullable=False)
    def __repr__(self):
        return f'<User {self.username}>'

class Game(db.Model):
    name = db.Column(db.String(80), db.ForeignKey('user.username'), primary_key=True)
    when = db.Column(db.String(80), primary_key=True)
    score = db.Column(db.Float(), nullable=False)

    def __repr__(self):#!
        return f'<Game {self.name}-{self.when}>'

@app.route ("/")
def root():
    return redirect(url_for("login"))

@app.route("/login", methods=['POST'])
def login():
    def send_quiz():
        session["username"] = name
        print("session is ", session)
        return json.jsonify([show_question(q) for q in draw_questions()])
    print("Login in")
    name = request.json["name"]
    password_hash = generate_password_hash(request.json["passw"])
    user_existing = User.query.filter_by(username=name).first()
    if user_existing: 
        check_password = check_password_hash(user_existing.password, request.json["passw"])
        if check_password:return send_quiz()
        else:return json.jsonify({"error": "wrong password"})
    else:
        password_hash = generate_password_hash(request.json["passw"])
        new_user = User(username=name, password=password_hash)
        db.session.add(new_user)
        db.session.commit()
        return send_quiz()
@app.route("/end", methods=["POST"])
def end():
    print("Closing")
    print("session is ", session)
    name = session.get("username", None)
    score = request.json["score"]
    when =  datetime.datetime.now().strftime('%d-%m-%y %a %H:%M:%S')
    new_game = Game(name=name, when=when, score=score)
    try:
        db.session.add(new_game)
        db.session.commit()
        print(f'{name}s test is stored')
    except Exception as error:print(f'error: {error}')
    print(name, score)
    return json.jsonify({"ok": "saved game", "name": name})

@app.route("/newgame", methods=["POST"])
def newgame():
    print("Starting new game\nsession is ",session)
    return json.jsonify([show_question(q) for q in draw_questions()])
with app.app_context():db.create_all()
app.run()