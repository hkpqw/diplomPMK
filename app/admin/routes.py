from flask import render_template, flash, redirect, url_for, request, Blueprint, current_app, send_file
from app import db
from app.forms import ServiceForm, NewsForm
from app.models import Service, Application, News, User
from flask_login import login_required, current_user
import os
from werkzeug.utils import secure_filename
from datetime import datetime, date
from io import BytesIO
from reportlab.pdfgen import canvas  # Import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors

bp = Blueprint('admin', __name__, url_prefix='/admin')

# Register the Times New Roman fonts
try:
    pdfmetrics.registerFont(TTFont('Times-Roman', 'app/static/fonts/times.ttf'))
    pdfmetrics.registerFont(TTFont('Times-Bold', 'app/static/fonts/timesbd.ttf'))
    FONT_REGISTERED_SUCCESSFULLY = True
except Exception as e:
    print(f"Error registering Times New Roman fonts: {e}")
    print("Please ensure times.ttf and timesbd.ttf are in app/static/fonts/")
    FONT_REGISTERED_SUCCESSFULLY = False

@bp.before_request
@login_required
def before_request():
    if not current_user.is_authenticated or current_user.username != 'admin':
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
        if 'image' in request.files:
            image = request.files['image']
            if image and allowed_file(image.filename):
                filename = secure_filename(image.filename)
                upload_folder = current_app.config['UPLOAD_FOLDER']
                os.makedirs(upload_folder, exist_ok=True)
                image.save(os.path.join(upload_folder, filename))

                service = Service(name=form.name.data, description=form.description.data,
                                  price=form.price.data, image_filename=filename)
                db.session.add(service)
                db.session.commit()
                flash('Услуга добавлена!', 'success')
                return redirect(url_for('admin.manage_services'))
            else:
                flash('Недопустимый тип файла', 'danger')
        else:
            flash('Изображение не выбрано', 'warning')

    services = Service.query.all()
    # Retrieve application counts for each service
    service_counts = {}
    for service in services:
        service_counts[service.id] = Application.query.filter_by(service_id=service.id).count()

    return render_template('admin/manage_services.html', form=form, services=services, service_counts=service_counts)

@bp.route('/services/edit/<int:service_id>', methods=['GET', 'POST'])
def edit_service(service_id):
    service = Service.query.get_or_404(service_id)
    form = ServiceForm(obj=service)
    if form.validate_on_submit():
        if 'image' in request.files:
            image = request.files['image']
            if image and allowed_file(image.filename):
                filename = secure_filename(image.filename)
                upload_folder = current_app.config['UPLOAD_FOLDER']
                os.makedirs(upload_folder, exist_ok=True)
                image.save(os.path.join(upload_folder, filename))
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

@bp.route('/reports', methods=['GET', 'POST'])
def reports():
    report_data = None
    start_date = None
    end_date = None  # Initialize end_date

    if request.method == 'POST':
        if request.form.get('current_month'):
            now = datetime.now()
            start_date = date(now.year, now.month, 1)
            end_date = date(now.year, now.month, now.day)  # Correct end date for current month
        else:
            start_date_str = request.form.get('start_date')
            end_date_str = request.form.get('end_date')

            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else None
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None
            except ValueError:
                flash('Неверный формат даты. Используйте YYYY-MM-DD.', 'danger')
                return render_template('admin/reports.html', report_data=report_data)

            if not start_date or not end_date:
                flash('Необходимо указать начальную и конечную даты.', 'danger')
                return render_template('admin/reports.html', report_data=report_data)

        applications = Application.query.filter(Application.timestamp.between(start_date, end_date)).all()

        # Prepare the report data for display on the page
        report_data = []
        for app_index, app in enumerate(applications):
            user = User.query.get(app.user_id)
            service = Service.query.get(app.service_id)
            report_data.append({
                'index': app_index + 1,
                'app_id': app.id,
                'user_full_name': user.full_name if user else "Пользователь не найден",
                'user_phone_number': user.phone_number if user else "",
                'user_email': user.email if user else "",  # added email
                'service_name': service.name if service else "Услуга не найдена",
                'service_price': service.price if service else "",
                'message': app.message,
                'timestamp': app.timestamp.strftime('%d.%m.%Y %H:%M'),
                'status': app.status
            })

        if request.form.get('action') == 'download':  # Check if the download button was clicked
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=letter)  # Create a canvas

            # Set font
            if FONT_REGISTERED_SUCCESSFULLY:
                 c.setFont('Times-Roman', 10)
            else:
                 c.setFont('Helvetica', 10)  # Fallback if Times New Roman is not available

            # Header
            c.drawString(inch, 10.5 * inch, f"Отчет по заявкам с {start_date.strftime('%d.%m.%Y')} по {end_date.strftime('%d.%m.%Y')}")

            y = 10 * inch
            for item in report_data:
                c.drawString(inch, y, f"{item['index']}. Заявка ID: {item['app_id']}")
                y -= 0.25 * inch
                c.drawString(1.2 * inch, y, f"От: {item['user_full_name']} ({item['user_email']})")
                y -= 0.25 * inch
                c.drawString(1.2 * inch, y, f"Услуга: {item['service_name']} ({item['service_price']} руб)")
                y -= 0.25 * inch
                c.drawString(1.2 * inch, y, f"Сообщение: {item['message'][:100]}...") # Truncate for brevity
                y -= 0.25 * inch
                c.drawString(1.2 * inch, y, f"Дата: {item['timestamp']}, Статус: {item['status']}")
                y -= 0.5 * inch  # Space between entries

                if y < inch: # New page if needed
                    c.showPage()
                    if FONT_REGISTERED_SUCCESSFULLY:
                        c.setFont('Times-Roman', 10)
                    else:
                        c.setFont('Helvetica', 10)
                    y = 10 * inch

            # Footer
            c.drawString(inch, 0.75 * inch, "Васильков О. В.    Директор     __________(поодпись)")

            c.save()  # Save the PDF

            buffer.seek(0)
            return send_file(
                buffer,
                as_attachment=True,
                download_name=f"report_applications_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.pdf",
                mimetype='application/pdf'
            )

        return render_template('admin/reports.html', report_data=report_data, start_date=start_date, end_date=end_date)  # Pass dates
    else:
        return render_template('admin/reports.html', report_data=None, start_date=None, end_date=None)  # Pass dates even when no report generated