# Import the flask class and create an instance of it
from flask import Flask, render_template

app = Flask(__name__)

# Define a route and view function
@app.route('/')
def home():
    return render_template('index.html')

# Run the app in debug mode
if __name__ == '__main__':
    app.run(debug=True)