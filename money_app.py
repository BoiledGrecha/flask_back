from flask import Flask, request
from sqlalchemy import create_engine
import json
from datetime import datetime
app = Flask(__name__)
#_________________
from logging import FileHandler, WARNING
file_handler = FileHandler("money_errors.txt")
file_handler.setLevel(WARNING)
app.logger.addHandler(file_handler)
#___________________________

DATABASE_URI = 'sqlite:///test.db'
engine = create_engine(DATABASE_URI)

def bonus_count(a):
    rankPrices = [400, 1200 ,2400, 4400, 6600, 9900, 14000, 20000, 40000, 699999]
    for i in range(len(rankPrices)):
        if a < rankPrices[i]:
            break
    if i > 0:
        a -= rankPrices[i - 1]
    percent = a / rankPrices[i]
    rank = i
    if rank == 0 :
        bonus1, bonus2, bonus3, bonus4 = 0, 0, 0, 0
    else:
        bonus1 = int(300 * (rank + 0)/100)
        bonus2 = int(1000 * (rank + 1)/100)
        bonus3 = int(3000 * (rank + 2)/100)
        bonus4 = int(15000 * (rank + 3)/100)
    return {"small_pack" : bonus1, "normal_pack" : bonus2, "big_pack" : bonus3, "huge_pack" : bonus4, "rank" : i, "percent" : percent}

def logwork (id, all_value, operation_name, value):
    line = engine.execute("SELECT log FROM money WHERE id = \"{}\"".format(id)).first()
    if line == None:
        engine.execute("INSERT INTO money (id) VALUES (\"{}\")".format(id))
        string = ""
    else:
        string = line["log"]
    new_log = "\n" + str(all_value) + " " + operation_name + " " + str(value) + " " + str(datetime.now()).split(".")[0]
    engine.execute("UPDATE money SET log = \"{}\" WHERE id = \"{}\"".format(string + new_log, id))


@app.after_request
def after(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS, PUT, PATCH, DELETE'
    response.headers['Access-Control-Allow-Headers'] = 'X-Requested-With,content-type'
    response.headers['Access-Control-Allow-Credentials'] = True
    return response

@app.route('/money', methods=['POST'])
def first():
    try:
        form = json.loads(request.data.decode())
    except Exception as error:
        with open("money_error.txt", "a+") as file:
            file.write("_____________________\n" + str(request.data) + "\n********************\n" + str(error) + "\n__________________\n")
    if "command" in form:
        if form["command"] == "set_crystal":
            try:
                line = engine.execute("SELECT command_number, crystal_value FROM saves WHERE id = \"{}\"".format(form["uid"])).first()
                if line["command_number"] == None:
                    engine.execute("UPDATE saves SET command_number = {},  crystal_value  = {} WHERE id = \"{}\"".format(form["command_number"], form["crystal_value"], form["uid"]))
                    if "operation_name" in form:
                        logwork(form["uid"], line["crystal_value"], form["operation_name"], form["crystal_value"])
                    return "{\"crystalValue\": \"" + form["crystal_value"] + "\", \"commandNumber\": \"" + form["command_number"] + "\", \"specialMessage\": \"OK\"}", 200
                if line["command_number"] < int(form["command_number"]):
                    engine.execute("UPDATE saves SET command_number = {},  crystal_value  = {} WHERE id = \"{}\"".format(form["command_number"], line["crystal_value"] + int(form["crystal_value"]), form["uid"]))
                    if "operation_name" in form:
                        logwork(form["uid"], line["crystal_value"], form["operation_name"], form["crystal_value"])
                    return "{\"crystalValue\": \"" + str(line["crystal_value"] + int(form["crystal_value"])) + "\", \"commandNumber\": \"" + form["command_number"] + "\", \"specialMessage\": \"OK\"}", 200
                else:
                    return "{\"crystalValue\": \"\", \"commandNumber\": \"\", \"specialMessage\": \"ABUSE\"}", 200
            except Exception as error:
                with open("money_error.txt", "a+") as file:
                    file.write("_____________________set_crystal\n" + str(datetime.now()) + "\n                    \n"
                            + str(error) + "\n********************\n" + form["uid"] + "\n_________________________\n")
                return "Trouble with crystals"
        elif form["command"] == "get_crystal":
            try:
                line = engine.execute("SELECT command_number, crystal_value, allBoughtCrystals FROM saves WHERE id = \"{}\"".format(form["uid"])).first()
                bonus = bonus_count(line["allBoughtCrystals"])
                bonus1 = bonus["small_pack"]
                bonus2 = bonus["normal_pack"]
                bonus3 = bonus["big_pack"]
                bonus4 = bonus["huge_pack"]
                i = bonus["rank"]
                percent = bonus["percent"]
                return ("{\"crystalValue\": \"" + str(line["crystal_value"]) + "\", \"commandNumber\": \""
                        + str(line["command_number"]) + "\", \"specialMessage\": \"OK\", \"rank\" : \""
                        + str(i) + "\", \"percent\" : \"" + str(percent) + "\", \"bonus1\" : \"" + str(bonus1)
                        + "\", \"bonus2\" : \"" + str(bonus2) + "\", \"bonus3\" : \"" + str(bonus3) + "\", \"bonus4\" : \"" + str(bonus4)+ "\"}", 200)
            except Exception as error:
                with open("money_error.txt", "a+") as file:
                    file.write("_____________________get_crystal\n" + str(datetime.now()) + "\n                    \n"
                            + str(error) + "\n********************\n" + form["uid"] + "\n_________________________\n")
                return "Trouble with crystals"
        else:
            return "COMMAND DIDNT RECOGNISE"
    elif "event" in form and form["event"] == "buy-item":
        base = {"small_pack" : 300, "normal_pack" : 1000, "big_pack" : 3000, "huge_pack" : 15000}
        line = engine.execute("SELECT id, crystal_value, allBoughtCrystals FROM saves WHERE local_id = \"{}\"".format(form["user_token"])).first()
        bonus = bonus_count(line["allBoughtCrystals"])[form["event_payload"]["items"][0]["uid"]]
        plus = line["crystal_value"]
        plus2 = base[form["event_payload"]["items"][0]["uid"]]
        if plus == None:
            plus = 0
        engine.execute("UPDATE saves SET crystal_value  = {}, allBoughtCrystals = {} WHERE local_id = \"{}\"".format(plus + plus2 + bonus, line["allBoughtCrystals"] + plus2, form["user_token"]))
        logwork(line["id"], line["crystal_value"], "purchase", plus2)
        return "OK", 200        
    else:
        return "NU KAK TAK "

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8800)
