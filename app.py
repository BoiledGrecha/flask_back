from flask import Flask, request, jsonify, redirect
from sqlalchemy import create_engine
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

app.config['MAIL_SERVER'] = 'XXXXXXXXXXXXXXXXXXXXX.com'
app.config['MAIL_PORT'] = 000
app.config['MAIL_USERNAME'] = 'XXXXXXXXXXXXXXXXXXXXXXXXXXX'
app.config['MAIL_PASSWORD'] = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
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
    try:
        form = json.loads(request.data.decode())
    except Exception as error:
        with open("byte_error.txt", "a+") as file:
            file.write("_____________________\n" + str(request.data) + "\n********************\n" + str(error))
        #return "Decode problems", 500
    if "command" in form:  # заменить на проверку есть ли поле ключа и равен ли хэш ключа нашему хэшу
        if form["command"] == "create":
            try:
                file = open("byte_error.txt", "a+")
                file.write("_______________\n1")
                if engine.execute("SELECT * FROM saves WHERE id = \"{}\"".format(form["uid"])).first():
                    file.write("2")
                    return "I need new UID", 500
                engine.execute("INSERT INTO saves(id, mail, save, created) VALUES (\"{}\", NULL,NULL,\"{}\")".format(form["uid"], str(datetime.now())))
                file.write("3")
                if "local_id" in form and form["local_id"]:
                    file.write("4")
                    engine.execute("UPDATE saves SET local_id = \"{}\" WHERE id = \"{}\"".format(form["local_id"], form["uid"]))
                    file.write("5")
                if "url" in form:
                    file.write("6")
                    engine.execute("UPDATE saves SET sender=\'{}\' WHERE id = \'{}\'".format(form['url'],form['uid']))
                file.write("Created\n")
                file.close()
                return "Created", 200
            except:
                file.write(" body: " + str(request.data) + " Brocken\n")
                file.close()
                return "Something doesnt work in CREATE", 500
        elif form["command"] == "save2":
            try:
                a = engine.execute("SELECT * FROM saves WHERE id = \"{}\"".format(form["uid"])).first()
                if not a:
                    return "User doesnt exist", 500
                if form["save_id"] == a["save_id"]:
                    engine.execute("UPDATE saves SET save = \"{}\" WHERE id = \"{}\"".format(form["saves"], form["uid"]))
                    return "UPDATED", 200
                elif not a["save_id"]:
                    engine.execute("UPDATE saves SET save = \"{}\", save_id = \"{}\" WHERE id = \"{}\"".format(form["saves"], form["save_id"], form["uid"]))
                    return "REWRITED", 200
                else:
                    engine.execute("UPDATE saves SET save_second = \"{}\" WHERE id = \"{}\"".format(form["saves"], form["uid"]))
                    return "WRONG", 200
            except:
                return "Something doesnt work in SAVE", 500
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
                if "local_id" in form and form["local_id"]:
                    engine.execute("UPDATE saves SET local_id = \'{}\' WHERE id = \"{}\"".format(form["local_id"], form["uid"]))
                if a:
                    if not a["save"]:
                        return "ERROR", 500
                    return str(a["save"]), 200
                return "SOMETHING WRONG IN LOAD", 500
            except:
                return "Something doesnt work in LOAD", 500
        elif form["command"] == "link":
            engine.execute("UPDATE saves SET trash_mail = \"{}\" WHERE id = \"{}\"".format(form["email"], form["uid"]))
            if engine.execute("SELECT * FROM saves WHERE mail = \"{}\"".format(form["email"])).first() != None:
                return "Mail already registred", 200
            serializer = URLSafeTimedSerializer("XXXXXXXX", salt="XXXXXXXXXXXXX")
            msg = Message(subject="Defentures Confirmation", sender="noreply@defentures.com")
            msg.body = "This is the confirmation link\n\n https://link.defentures.com/confirmation/" + serializer.dumps(form["uid"]+'\\'+form["email"])
            msg.add_recipient(form["email"])
            with app.app_context():
                mail.send(msg)
            return "Sent", 200
        elif form["command"] == "check_link":
            if (engine.execute("SELECT \"mail\" FROM saves WHERE id = \"{}\"".format(form["uid"])).first()["mail"]) == None:
                return "0" , 200
            return "1" , 200
        elif form["command"] == "load_by_email":
            # key и email высылаю ссылку с токеном из ключа, потом когда нажмёт я его разверну и запишу в бд
            if engine.execute("SELECT * FROM saves WHERE mail = \"{}\"".format(form["email"])).first() == None and \
                    engine.execute("SELECT * FROM saves WHERE bonus_mail = \"{}\"".format(form["email"])).first() == None:
                return "Mail not in base", 200
            serializer = URLSafeTimedSerializer("XXXXXXXXX", salt="XXXXXXXXXXXXX")
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
            serializer = URLSafeTimedSerializer("XXXXXXXXX", salt="XXXXXXXX")
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
        elif form["command"] == "get_achievment":
            with open("quests.txt") as fd:
                string = fd.read()
            names = string.split("\n")
            names.pop(-1)
            if form["achievment_name"] not in names:
                return redirect("http://defentures.com/questErrorNoLogin")
            a = engine.execute("SELECT save FROM saves WHERE mail = \"{}\"".format(form["email"])).first()
            if a == None:
                return redirect("http://defentures.com/questErrorNoLogin")
            a = a[0].replace("\'", "\"")
            a = json.loads(a)
            for i in a["tokens"]:
                if i["name"] == form["achievment_name"]:
                    i["dRecord"]["Value"] = "1"
                    break
            else:
                a["tokens"].append({'name': form["achievment_name"], 'dRecord': {'Value': '1'}})
            engine.execute("UPDATE saves SET save = \'{}\' WHERE mail = \"{}\"".format(json.dumps(a), form["email"]))
            return "OK", 200
        else:
            return "NU KAK TAK 1"
    else:
        return "NU KAK TAK 2"


@app.route('/confirmation/<token>')
def check_tocken(token):
    serializer = URLSafeTimedSerializer("XXXXXXXX")
    try:
       token = serializer.loads(token, salt="XXXXXXX")
       uid, mail = token[:token.rindex("\\")], token[token.rindex("\\") + 1:]
       engine.execute("UPDATE saves SET mail = \"{}\" WHERE id = \"{}\"".format(mail, uid))
       return redirect( "http://defentures.com/success")
    except:
        return redirect( "http://defentures.com/fail")

@app.route('/bonus_confirmation/<token>')
def check_tocken3(token):
    serializer = URLSafeTimedSerializer("XXXXXXX")
    try:
        token = serializer.loads(token, salt="XXXXXXX")
        uid, mail = token[:token.rindex("\\")], token[token.rindex("\\") + 1:]
        engine.execute("UPDATE saves SET bonus_confirm = \"1\" WHERE bonus_mail = \"{}\"".format(mail))
        return redirect( "http://defentures.com/success")
    except:
        return redirect("http://defentures.com/fail")


@app.route('/import_saves/<token>')
def check_tocken2(token):
    serializer = URLSafeTimedSerializer("XXXXXXXXX")
    try:
       token = serializer.loads(token, salt="XXXXXXXX")
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
    app.run(host='127.0.0.1', port=8000)
