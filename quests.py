from flask import Flask, request, redirect
import json

app = Flask(__name__)

@app.after_request
def after(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS, PUT, PATCH, DELETE'
    response.headers['Access-Control-Allow-Headers'] = 'X-Requested-With,content-type'
    response.headers['Access-Control-Allow-Credentials'] = True
    return response

@app.route('/quests', methods=['POST'])
def first():
    form = json.loads(request.data.decode())
    if "command" in form:
        #передается комманд и place в плэйс запишем номер который надо обновить, 0 - start, 1 - finish, 2 - mail
        if form["command"] == "update":
            with open("quest_stat.txt", "r") as fd:
                a = fd.read()
                a = a.split(" ")
                a[int(form["place"])] = str(int(a[int(form["place"])]) + 1)
                a = a[0] + ' ' + a[1] + ' ' + a[2]
            with open("quest_stat.txt", "w") as fd:
                fd.write(a)
            return ("OK")
        return ("NE OK")
            

@app.route('/quests')
def hello():
    return redirect("http://defentures.com")

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8888)
