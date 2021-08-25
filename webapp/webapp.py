from flask import Flask, render_template, request
from flask.config import Config 
import config #import the config of the app
import datetime


app = Flask(__name__)

class webserver:
    buffer = []
    def __init___(self):
        pass            

@app.route('/')
def home():
    title = "Systeem"
    config_load = config.config_read()

    return render_template("systeem_status.html", title = title, config_load = config_load)

@app.route("/invoerendoorkomst", methods = ['POST', 'GET'])
def invoerendoorkomst():
    title = "Doorkomst"

    if request.method == 'POST':
        team = request.form['team_insert']
        datetime_current = datetime.datetime.now().astimezone().replace(microsecond=0).isoformat() #current system datetime

        buffer_temp = (datetime_current, team) #combine al data into a single variable

        webserver().buffer.append(buffer_temp) 

#        print(datetime_current, " ", team)
#        print(webserver().buffer)


    return render_template("invoeren_doorkomst.html", title= title)

@app.route("/wijzigingen")
def wijzigingen():
    title = "Wijzigingen"
    return render_template("wijzigingen.html", title= title)

@app.route("/instellingen", methods = ['POST', 'GET'])
def instellingen():
    title = "Instellingen"
    config_load = config.config_read()

    if request.method == 'POST':
        
        config_load["competition"]["checkpointteam"] = request.form['checkpointteam']
        config_load["competition"]["checkpoint"] = request.form['checkpoint']
        
        config.config_write(config_load)

        
    return render_template("instellingen.html", title= title, config_load = config_load)


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug = True)