from flask import render_template, flash, redirect, url_for, request, Blueprint
from app import db
from app.forms import ApplicationForm, LoginForm, RegistrationForm, ReviewForm
from app.models import Service, Application, News, User, Review
from flask_login import current_user, login_user, logout_user, login_required

bp = Blueprint('main', __name__)

@bp.route('/')
@bp.route('/index')
def index():
    news = News.query.order_by(News.date_posted.desc()).limit(3).all()
    reviews = Review.query.order_by(Review.date_posted.desc()).limit(3).all()
    return render_template('index.html', news=news, reviews=reviews)

@bp.route('/services')
def services():
    services = Service.query.all()
    service_counts = {}
    for service in services:
        service_counts[service.id] = Application.query.filter_by(service_id=service.id).count()
    return render_template('services.html', services=services, service_counts=service_counts)

@bp.route('/service/<int:service_id>', methods=['GET', 'POST'])
def service_detail(service_id):
    service = Service.query.get_or_404(service_id)
    form = ApplicationForm()

    if current_user.is_authenticated:
        if form.validate_on_submit():
            application = Application(message=form.message.data, service=service, author=current_user)
            db.session.add(application)
            db.session.commit()
            flash('Ваша заявка успешно отправлена!', 'success')
            return redirect(url_for('main.index'))

        return render_template('service_detail.html', service=service, form=form)
    else:
        return render_template('service_detail_login_required.html', service=service)

@bp.route('/profile')
@login_required
def profile():
    applications = Application.query.filter_by(author=current_user).order_by(Application.timestamp.desc()).all()
    return render_template('profile.html', applications=applications)

@bp.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ApplicationForm()
    if form.validate_on_submit():
        application = Application(message=form.message.data, author=current_user)
        db.session.add(application)
        db.session.commit()
        flash('Ваше сообщение отправлено!', 'success')
        return redirect(url_for('main.index'))

    return render_template('contact.html', form=form)

@bp.route('/news')
def news_list():
    news = News.query.order_by(News.date_posted.desc()).all()
    return render_template('news_list.html', news=news)

@bp.route('/reviews', methods=['GET', 'POST'])
def reviews():
    form = ReviewForm()
    if form.validate_on_submit():
        review = Review(name=form.name.data, text=form.text.data, rating=form.rating.data)
        db.session.add(review)
        db.session.commit()
        flash('Спасибо за ваш отзыв!', 'success')
        return redirect(url_for('main.reviews'))

    reviews = Review.query.order_by(Review.date_posted.desc()).all()
    return render_template('reviews.html', form=form, reviews=reviews)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data,
                    full_name=form.full_name.data, phone_number=form.phone_number.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Поздравляем, вы зарегистрированы!', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html', title='Регистрация', form=form)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Неверный email или пароль', 'danger')
            return redirect(url_for('main.login'))
        login_user(user, remember=form.remember.data)
        next_page = request.args.get('next')
        if not next_page or next_page == url_for('main.login'):
            next_page = url_for('main.index')
        return redirect(next_page)
    return render_template('login.html', title='Войти', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))