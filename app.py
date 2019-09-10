from flask import Flask, request, jsonify, redirect
from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
import json
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Mail, Message
from logging import FileHandler, WARNING
from datetime import datetime

app = Flask(__name__)

file_handler = FileHandler("errors_flask.txt")
file_handler.setLevel(WARNING)

app.logger.addHandler(file_handler)

DATABASE_URI = 'sqlite:///test.db'
engine = create_engine(DATABASE_URI)

app.config['MAIL_SERVER'] = 'email-smtp.us-east-1.amazonaws.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'XXXXXXXXXXXXXXXXXXX'
app.config['MAIL_PASSWORD'] = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

@app.after_request
def after(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS, PUT, PATCH, DELETE'
    response.headers['Access-Control-Allow-Headers'] = 'X-Requested-With,content-type'
    response.headers['Access-Control-Allow-Credentials'] = True
    return response

@app.route('/', methods=['POST'])
def first():
    form = json.loads(request.data.decode())
    if "command" in form:
        if form["command"] == "create":
            try:
                if engine.execute("SELECT * FROM saves WHERE id = \"{}\"".format(form["uid"])).first():
                    return "I need new UID", 500
                engine.execute("INSERT INTO saves(id, mail, save, created) VALUES (\"{}\", NULL,NULL,\"{}\")".format(form["uid"], str(datetime.now())))
                if "url" in form:
                    engine.execute("UPDATE saves SET sender=\'{}\' WHERE id = \'{}\'".format(form['url'],form['uid']))
                return "Created", 200
            except:
                return "Something doesnt work in CREATE", 500
        elif form["command"] == "save":
            try:
                if not engine.execute("SELECT * FROM saves WHERE id = \"{}\"".format(form["uid"])).first():
                    return "User doesnt exist", 500
                engine.execute("UPDATE saves SET save = \"{}\" WHERE id = \"{}\"".format(form["saves"], form["uid"]))
                return "UPDATED", 200
            except:
                return "Something doesnt work in SAVE", 500
        elif form["command"] == "load":
            try:
                a = engine.execute("SELECT * FROM saves WHERE id = \"{}\"".format(form["uid"])).first()
                engine.execute("UPDATE saves SET last_login = \"{}\" WHERE id = \"{}\"".format(str(datetime.now()), form["uid"]))
                if a:
                    return str(a["save"]), 200
            except:
                return "Something doesnt work in LOAD", 500
        elif form["command"] == "link":
            engine.execute("UPDATE saves SET trash_mail = \"{}\" WHERE id = \"{}\"".format(form["email"], form["uid"]))
            if engine.execute("SELECT * FROM saves WHERE mail = \"{}\"".format(form["email"])).first() != None:
                return "Mail already registred", 200
            serializer = URLSafeTimedSerializer("XXXXXXXXXXXXXXXXXXX", salt="XXXXXXXXXXXXXXXXXXX")
            msg = Message(subject="Defentures Confirmation", sender="noreply@defentures.com")
            msg.body = "This is the confirmation link\n\n https://link.defentures.com/confirmation/" + serializer.dumps(form["uid"]+'\\'+form["email"])
            msg.add_recipient(form["email"])
            with app.app_context():
                mail.send(msg)
            return "Sent", 200
        elif form["command"] == "check_link":
            if (engine.execute("SELECT \"mail\" FROM saves WHERE id = \"{}\"".format(form["uid"])).first()["mail"]) == None:
                # print((engine.execute("SELECT * FROM saves WHERE id = \"{}\"".format(form["uid"])).first()["mail"]))
                return "0" , 200
            return "1" , 200
        elif form["command"] == "load_by_email":
            # key и email высылаю ссылку с токеном из ключа, потом когда нажмёт я его разверну и запишу в бд
            if engine.execute("SELECT * FROM saves WHERE mail = \"{}\"".format(form["email"])).first() == None:
                return "Mail not in base", 200
            serializer = URLSafeTimedSerializer("XXXXXXXXXXXXXXXXXXX", salt="XXXXXXXXXXXXXXXXXXX")
            msg = Message(subject="Defentures Confirmation", sender="noreply@defentures.com")
            msg.body = "This is the confirmation link.\n\n https://link.defentures.com/import_saves/" + serializer.dumps(form["key"] + '\\' + form["email"])
            msg.add_recipient(form["email"])
            with app.app_context():
                mail.send(msg)
            return "Sent", 200
        elif form["command"] == "enter_by_email":
            line = engine.execute("SELECT * FROM saves WHERE mail = \"{}\"".format(form["email"])).first()
            if line["session_key"] == form["key"]:
                return line["id"], 200
            else:
                return "Fail", 500
        elif form["command"] == "bonus":
            engine.execute("UPDATE saves SET bonus_mail = \"{}\" WHERE id = \"{}\"".format(form["email"], form["uid"]))
            serializer = URLSafeTimedSerializer("XXXXXXXXXXXXXXXXXXX", salt="XXXXXXXXXXXXXXXXXXX")
            try:
                msg = Message(subject="Defentures Confirmation", sender="noreply@defentures.com")
                msg.body = "This is the confirmation link\n\n https://link.defentures.com/bonus_confirmation/" + serializer.dumps(form['uid'] + '\\' + form["email"])
                msg.add_recipient(form["email"])
                with app.app_context():
                    mail.send(msg)
                return "Sent", 200
            except:
                return "Incorrect mail", 200
        elif form["command"] == "bonus_confirmation":
            return engine.execute("SELECT \"bonus_confirm\" FROM saves WHERE id  = \"{}\"".format(form["uid"])).first()[0], 200
        else:
            return "NU KAK TAK 1"
    else:
        return "NU KAK TAK 2"


@app.route('/confirmation/<token>')
def check_tocken(token):
    serializer = URLSafeTimedSerializer("XXXXXXXXXXXXXXXXXXX")
    try:
       token = serializer.loads(token, salt="XXXXXXXXXXXXXXXXXXX")
       uid, mail = token[:token.rindex("\\")], token[token.rindex("\\") + 1:]
       engine.execute("UPDATE saves SET mail = \"{}\" WHERE id = \"{}\"".format(mail, uid))
       return redirect( "http://defentures.com/success")
    except:
        return redirect( "http://defentures.com/fail")

@app.route('/bonus_confirmation/<token>')
def check_tocken3(token):
    serializer = URLSafeTimedSerializer("XXXXXXXXXXXXXXXXXXX")
    try:
        token = serializer.loads(token, salt="XXXXXXXXXXXXXXXXXXX")
        uid, mail = token[:token.rindex("\\")], token[token.rindex("\\") + 1:]
        engine.execute("UPDATE saves SET bonus_confirm = \"1\" WHERE bonus_mail = \"{}\"".format(mail))
        return redirect( "http://defentures.com/success")
    except:
        return redirect("http://defentures.com/fail")


@app.route('/import_saves/<token>')
def check_tocken2(token):
    serializer = URLSafeTimedSerializer("XXXXXXXXXXXXXXXXXXX")
    try:
       token = serializer.loads(token, salt="XXXXXXXXXXXXXXXXXXX")
       session_key, mail = token[:token.rindex("\\")], token[token.rindex("\\") + 1:]
       engine.execute("UPDATE saves SET session_key = \"{}\" WHERE mail = \"{}\"".format(session_key, mail))
       return redirect("http://defentures.com/success")
    except:
        return redirect("http://defentures.com/fail")


@app.route('/')
def hello():
    return redirect("http://defentures.com")

@app.route('/check')
def trying():
    return "Check Check"

if __name__ == "__main__":
    app.run(host='XXXX.XXXXX.XXXXX.XXXXX', port=8080)