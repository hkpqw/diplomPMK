from app import create_app, db
from app.models import User, Service, Application, News, Review

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Service': Service, 'Application': Application, 'News': News, 'Review': Review}

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0') #  Для доступа извне, если в Docker
    #app.run(debug=True) #  Для локальной разработки