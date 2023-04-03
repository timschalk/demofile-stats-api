from awpy.parser import DemoParser
from awpy.analytics.stats import player_stats
from flask import Flask, jsonify, request
import os
import urllib.request
import bz2

app = Flask(__name__)

def extract_bz2_file(url):
    # Herunterladen der bz2-Datei von der URL
    response = urllib.request.urlopen(url)
    compressed_file = response.read()

    # Extrahieren des Dateinamens aus der URL
    filename = os.path.basename(url)

    # Speichern der bz2-Datei im aktuellen Verzeichnis
    with open("download/" + filename, 'wb') as f:
        f.write(compressed_file)

    # Entpacken der Datei und Speichern im Ordner "demofiles"
    with bz2.BZ2File("download/" + filename) as f_in, open(os.path.join('demofiles', os.path.splitext(filename)[0]), 'wb') as f_out:
        for data in iter(lambda : f_in.read(100 * 1024), b''):
            f_out.write(data)

    # Löschen der bz2-Datei
    os.remove("download/" + filename)

    # Rückgabe des Dateinamens der entpackten Datei
    return os.path.splitext(filename)[0]

@app.route('/get-stats', methods=['GET'])
def get_stats():

    demofile_url = request.args.get('url')
    demofile = extract_bz2_file(demofile_url)

    # Create the parser object.
    parser = DemoParser(
        demofile="demofiles/" + demofile,
        demo_id=demofile.replace(".dem", ""),
        outpath="output",
        parse_frames=False,
    )
    # Parse the demofile, output results to a dictionary of dataframes.
    data = parser.parse()
    
    result_obj = {
        "matchID": data["matchID"],
        "match" : {
            "map": data["mapName"],
            "tickRate": data["tickRate"],
            "clientName": data["clientName"],
            "maxRounds": data["serverVars"]["maxRounds"]
        },
        "teamA": {
            "score": data["gameRounds"][-1]["endTScore"],
            "player": data["gameRounds"][0]["ctSide"]["players"]
        },
        "teamB": {
            "score": data["gameRounds"][-1]["endCTScore"],
            "player": data["gameRounds"][0]["tSide"]["players"]
        },
        "player_stats" : player_stats(data["gameRounds"])
    }

    return jsonify(result_obj)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)