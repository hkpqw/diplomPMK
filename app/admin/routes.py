from flask import render_template, flash, redirect, url_for, request, Blueprint, current_app
from app import db
from app.forms import ServiceForm, NewsForm
from app.models import Service, Application, News, User
from flask_login import login_required, current_user
import os
from werkzeug.utils import secure_filename  # Импортируем secure_filename

bp = Blueprint('admin', __name__, url_prefix='/admin')


@bp.before_request
@login_required
def before_request():
    # Проверка, является ли пользователь администратором
    if not current_user.is_authenticated or current_user.username != 'admin':  # Пример проверки
        flash('У вас нет прав доступа к этой странице.', 'danger')
        return redirect(url_for('main.index'))

@bp.route('/dashboard')
def dashboard():
    applications_count = Application.query.count()
    services_count = Service.query.count()
    news_count = News.query.count()
    return render_template('admin/dashboard.html', applications_count=applications_count,
                           services_count=services_count, news_count=news_count)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/services', methods=['GET', 'POST'])
def manage_services():
    form = ServiceForm()
    if form.validate_on_submit():
        print("Форма отправлена") #  Добавлено
        # Проверяем, был ли загружен файл
        if 'image' in request.files:
            print("Поле image есть в request.files") # Добавлено
            image = request.files['image']
            # Если файл был загружен и он разрешенного типа
            if image and allowed_file(image.filename):
                print("Файл загружен и имеет допустимое расширение") # Добавлено
                filename = secure_filename(image.filename)  # Безопасное имя файла
                # Создаем папку uploads, если ее нет
                upload_folder = current_app.config['UPLOAD_FOLDER']
                os.makedirs(upload_folder, exist_ok=True)  # Создаем папку, если она не существует
                image.save(os.path.join(upload_folder, filename))  # Сохраняем файл

                service = Service(name=form.name.data, description=form.description.data,
                                  price=form.price.data, image_filename=filename)  # Сохраняем имя файла
                db.session.add(service)
                db.session.commit()
                flash('Услуга добавлена!', 'success')
                return redirect(url_for('admin.manage_services'))
            else:
                flash('Недопустимый тип файла', 'danger')  # Сообщение об ошибке
        else:
            flash('Изображение не выбрано', 'warning') # Сообщение об ошибке, если файл не был выбран

    services = Service.query.all()
    return render_template('admin/manage_services.html', form=form, services=services)

@bp.route('/services/edit/<int:service_id>', methods=['GET', 'POST'])
def edit_service(service_id):
    service = Service.query.get_or_404(service_id)
    form = ServiceForm(obj=service)
    if form.validate_on_submit():
         # Проверяем, был ли загружен файл
        if 'image' in request.files:
            image = request.files['image']
            # Если файл был загружен и он разрешенного типа
            if image and allowed_file(image.filename):
                filename = secure_filename(image.filename)  # Безопасное имя файла
                # Создаем папку uploads, если ее нет
                upload_folder = current_app.config['UPLOAD_FOLDER']
                os.makedirs(upload_folder, exist_ok=True)  # Создаем папку, если она не существует
                image.save(os.path.join(upload_folder, filename))  # Сохраняем файл
                # Удаляем старое изображение, если оно есть
                if service.image_filename:
                    old_image_path = os.path.join(upload_folder, service.image_filename)
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)
                service.image_filename = filename
        service.name = form.name.data
        service.description = form.description.data
        service.price = form.price.data
        db.session.commit()
        flash('Услуга обновлена!', 'success')
        return redirect(url_for('admin.manage_services'))
    return render_template('admin/edit_service.html', form=form, service=service)


@bp.route('/services/delete/<int:service_id>', methods=['POST'])
def delete_service(service_id):
    service = Service.query.get_or_404(service_id)
    db.session.delete(service)
    db.session.commit()
    flash('Услуга удалена!', 'success')
    return redirect(url_for('admin.manage_services'))

@bp.route('/applications')
def manage_applications():
    applications = Application.query.all()
    return render_template('admin/manage_applications.html', applications=applications)

@bp.route('/applications/status/<int:application_id>/<string:new_status>')
def update_application_status(application_id, new_status):
    application = Application.query.get_or_404(application_id)
    application.status = new_status
    db.session.commit()
    flash(f'Статус заявки изменен на {new_status}', 'success')
    return redirect(url_for('admin.manage_applications'))

@bp.route('/news', methods=['GET', 'POST'])
def manage_news():
    form = NewsForm()
    if form.validate_on_submit():
        news = News(title=form.title.data, content=form.content.data)
        db.session.add(news)
        db.session.commit()
        flash('Новость добавлена!', 'success')
        return redirect(url_for('admin.manage_news'))
    news = News.query.all()
    return render_template('admin/manage_news.html', form=form, news=news)

@bp.route('/news/edit/<int:news_id>', methods=['GET', 'POST'])
def edit_news(news_id):
     news = News.query.get_or_404(news_id)
     form = NewsForm(obj=news)
     if form.validate_on_submit():
          news.title = form.title.data
          news.content = form.content.data
          db.session.commit()
          flash('Новость обновлена', 'success')
          return redirect(url_for('admin.manage_news'))
     return render_template('admin/edit_news.html', form=form, news=news)


@bp.route('/news/delete/<int:news_id>', methods=['POST'])
def delete_news(news_id):
    news = News.query.get_or_404(news_id)
    db.session.delete(news)
    db.session.commit()
    flash('Новость удалена!', 'success')
    return redirect(url_for('admin.manage_news'))