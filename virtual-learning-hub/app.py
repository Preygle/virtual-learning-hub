from flask import Flask, render_template

app = Flask(__name__)

# Route for the main HTML file
@app.route('/')
def home():
    return render_template('studysphere.html')

# Route for additional pages (assuming they are in the templates folder)
@app.route('/<page>')
def render_page(page):
    return render_template(page)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
