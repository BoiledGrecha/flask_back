from flask import Flask, request, render_template, session, redirect, url_for
from sqlalchemy import create_engine

app = Flask(__name__)
hashed = "XXXXXXXXXxx"
DATABASE_URI = 'sqlite:///test.db'
engine = create_engine(DATABASE_URI)
app.config['SECRET_KEY'] = "XXXXXXXXXXXX"

@app.route('/', methods=['POST', 'GET'])
def hello():
    if "submit" in request.form and request.form["submit"]=="send":
        if request.form["passwd"] == hashed:
            session["passwd"] = hashed
    if "passwd" in session and session["passwd"] == hashed:
        with open("quest_stat.txt", "r") as fd:
            string = fd.read()
            string = string.split(" ")
            return render_template("start.html",
                total1 = str(engine.execute("SELECT COUNT(id) as COUNT FROM saves").first()["COUNT"]),
                total2 = str(engine.execute("SELECT COUNT(mail) as COUNT FROM saves").first()["COUNT"]),
                total3 = str(engine.execute("SELECT COUNT(bonus_mail) as COUNT FROM saves").first()["COUNT"]),
                total4 = str(engine.execute("SELECT COUNT(bonus_mail) as COUNT FROM saves WHERE bonus_confirm != \"0\";").first()["COUNT"]),
                quest1 = string[0],
                quest2 = string[1],
                quest3 = string[2])
    else:
        return render_template("nopass.html")

@app.route("/search_mail", methods=["POST", "GET"])
def search_mail():
    if "passwd" in session and session["passwd"] == hashed:
        if "submit" in request.form and request.form["submit"]=="search":
            a = engine.execute("SELECT * FROM saves WHERE mail LIKE '%{}%'".format(request.form["pattern"]))
            return render_template("search.html", object = a)
        else:
            return render_template("search.html")
    else:
        return redirect("XXX.XXX.XXX.XXX:XXXX")

@app.route("/search_id", methods=["POST", "GET"])
def search_id():
    if "passwd" in session and session["passwd"] == hashed:
        if "submit" in request.form and request.form["submit"]=="search":
            a = engine.execute("SELECT * FROM saves WHERE id = \"{}\"".format(request.form["pattern"]))
            return render_template("search_id.html", object = a)
        else:
            return render_template("search_id.html")
    else:
        return redirect("XXX.XXX.XXX.XXX:XXXX")


if __name__ == "__main__":
    app.run(host='XXX.XXX.XXX.XXX', port=0000)
