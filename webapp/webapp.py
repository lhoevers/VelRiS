from flask import Flask, render_template
import config #import the config of the app

app = Flask(__name__)

buffer = [] #create empty buffer

@app.route('/')
def home():
    title = "Systeem"
    config_load = config.config_read()

    return render_template("systeem_status.html", title= title, config_load = config_load)

@app.route("/invoerendoorkomst")
def invoerendoorkomst():
    title = "Doorkomst"
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
