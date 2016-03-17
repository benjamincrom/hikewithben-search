'''
app.py -- Flask web interface for module lib.search_query
'''
from flask import Flask, request, render_template

from lib import search_query

JSON_RESPONSE_HEADER = 'application/json'

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def search():
    '''
    Peform search of redis datastore based on temperature, date, and distance
    parameters.
    '''
    if request.args:
        request_dict = {key: value
                        for key, value in request.args.iteritems()
                        if value}

        search_instance = search_query.SearchQuery()
        recarea_list = search_instance.search(request_dict)
        recarea_list = sorted(recarea_list,
                              key=lambda k: k['distance_from_home'])
    else:
        recarea_list = []
        request_dict = {}

    return render_template('index.html',
                           recarea_list=recarea_list,
                           request_dict=request_dict)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
