from website import create_app
from ascii import ascii_art


app = create_app()
print(ascii_art)
if __name__ == '__main__':
    app.run(debug=True)
