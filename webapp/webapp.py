from flask import Flask, render_template, request
import config #import the config of the app
import datetime

app = Flask(__name__)

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
        
        print(datetime_current, " ", team)

    return render_template("invoeren_doorkomst.html", title= title)

@app.route("/wijzigingen")
def wijzigingen():
    title = "Wijzigingen"
    return render_template("wijzigingen.html", title= title)

@app.route("/instellingen")
def instellingen():
    title = "Instellingen"
    return render_template("instellingen.html", title= title)

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug = True)