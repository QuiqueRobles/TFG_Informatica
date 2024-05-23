from website import create_app
from ascii import ascii_art


app = create_app()
print(ascii_art)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000,debug=True,ssl_context=('cert.pem', 'key.pem'))
