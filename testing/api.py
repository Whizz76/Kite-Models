from flask import Flask, jsonify
import random

app = Flask(__name__)

@app.route('/random_number', methods=['GET'])
def get_random_number():
    random_num = random.randint(100, 300)
    return jsonify({'random_number': random_num})

if __name__ == '__main__':
    app.run(debug=True)