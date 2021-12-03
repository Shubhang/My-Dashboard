from flask import render_template, request, flash, redirect, url_for, session
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from app.models import User, Dashboard, Group
from app import app, db
from app.backend.company import Company
from app.backend.summary.compliance import getCompliance
from app.forms import LoginForm, RegistrationForm, EditProfileForm, ResetPasswordRequestForm, ResetPasswordForm, CreateGroupForm
from app.email import send_password_reset_email
from app.dashboard import dashboard as make_dashboard
from collections import Counter
import pandas as pd
import pickle


@app.route('/')
@app.route('/home')
@app.route('/index')
def home():
    company_counts = None
    if current_user.is_authenticated:
        dashboards = list(Dashboard.query.filter_by(user_id=current_user.id).all())
        if len(dashboards) > 0:
            company_counts = dict(Counter([dash.company_name for dash in dashboards]).most_common(5))
            company_names = dict([(k, Company(k).displayName) for k,v in company_counts.items()])
        else:
            company_names = {}
    else:
        company_names = {}
    return render_template("home.html", title='Home Page', company_names=company_names)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if 'dashboard' in str(next_page):  # User tries to search withouth being logged in
            next_page = url_for('home')
        if not next_page or url_parse(next_page).netloc != '': # protection from malicious absolute site redirects
            next_page = url_for('home')    # where the user gets redirected after login
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@login_required
@app.route('/create_group', methods=['GET', 'POST'])
def create_group():
    if current_user.is_authenticated:
        form = CreateGroupForm()
        if form.validate_on_submit():
            group = Group(
                name=form.name.data, 
                description=form.description.data,
                creator=current_user
                )
            db.session.add(group)
            db.session.commit()
            print(f'Group {group} created')
            return redirect(url_for('groups', group_id=group.id))
        return render_template('create_group.html', title='Create Group', form=form)
    else:
        return redirect(url_for('login'))

@app.route('/remove_group/<group_id>', methods=['POST'])
def remove_group(group_id):
    group = Group.query.filter_by(id=group_id).first()
    db.session.delete(group)
    db.session.commit()
    print(f'group {group} removed')
    return redirect(url_for('home'))

@app.route('/groups/<group_id>', methods=['GET', 'POST'])
def groups(group_id):

    if request.method == 'POST':

        group = Group.query.filter_by(id=group_id).first()
        group_companies = pickle.loads(group.companies)

        if 'new-company' in request.form:
            # add company
            new_company = request.form['new-company']
            print('adding to group:', group)
            print('new company:', new_company)
            if new_company not in group_companies:
                group_companies.append(new_company)
                group.companies = pickle.dumps(group_companies)
                db.session.commit()
            else:
                print(f'{new_company} already in group')

        elif 'delete-company' in request.form:
            # delete company
            company_to_delete = request.form['delete-company']
            print('removing from group:', group)
            print('company to delete:', company_to_delete)
            group_companies.remove(company_to_delete)
            group.companies = pickle.dumps(group_companies)
            db.session.commit()
    
    # get companies in group
    group = Group.query.filter_by(id=group_id).first()
    print('getting group:', group)
    group_companies = pickle.loads(group.companies) 

    return render_template('group.html', 
    title=group.name, 
    group=group,
    group_companies=group_companies,
    in_production=app.config['IN_PRODUCTION']
    )


@app.route('/loading', methods=['POST'])
def loading():
    return render_template('loading.html')

@app.route('/dashboard', methods=['POST', 'GET'])
@login_required
def dashboard():

    session['companyName'] = request.form['company']

    # try:
    return make_dashboard(session['companyName'])
    # except:
    #     return render_template('companyNotFound.html', title='Company Not Found', companyName=companyName)


@app.route('/summaries', methods=['POST', 'GET'])
@login_required
def summaries():

    if request.method =='POST':
        sources_list = request.form.getlist('summaries-sources[]') # list of checked sources
        sectors_list = request.form.getlist('summaries-sectors[]') # list of checked sectors
        multiplier = request.form['summaries-multiplier']
        print('new summaries values:', sources_list, sectors_list, multiplier)
        current_user.summaries_sources = pickle.dumps(sources_list)
        current_user.summaries_sectors = pickle.dumps(sectors_list)
        current_user.summaries_multiplier = multiplier
        db.session.commit()
        print('user dashboard settings updated!')

    print('getting summaries...')
    multiplier = current_user.summaries_multiplier
    all_summaries = []
    sources = pickle.loads(current_user.summaries_sources)
    custom_sectors = pickle.loads(current_user.summaries_sectors)
    for source in sources:
        override_sectors = []
        if source == 'nat_law_review':
            if custom_sectors != []:
                override_sectors = [[s.split('_')[1], s.split('_')[2]] for s in custom_sectors if s.split('_')[0] == 'National Law Review'] # source_sector_url
            source_display = 'National Law Review'
            link = 'https://www.natlawreview.com/'
        elif source == 'jdsupra':
            if custom_sectors != []:
                override_sectors = [[s.split('_')[1], s.split('_')[2]] for s in custom_sectors if s.split('_')[0] == 'JD Supra'] # source_sector_url
            source_display = 'JD Supra'
            link = 'https://www.jdsupra.com/law-news/'

        summaries = getCompliance(Company(session['companyName']), source, multiplier=multiplier, custom_sectors=override_sectors) # update later when we add preferences
        all_summaries.append({
            'summaries': summaries,
            'source': source_display,
            'link': link
        })

    # fake summaries (3) for fast testing
    # source_display = 'National Law Review'
    # summaries = [{'date':'01/05/2020', 'sector': 'Consumer Cyclical', 'score': 0.00, 'text': 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Egestas sed tempus urna et pharetra pharetra. Nulla facilisi nullam vehicula ipsum a arcu cursus vitae. Nunc consequat interdum varius sit amet mattis. Tincidunt eget nullam non nisi est sit amet facilisis magna. Varius duis at consectetur lorem. Consequat ac felis donec et odio. Ultricies tristique nulla aliquet enim tortor at. Maecenas pharetra convallis posuere morbi. Lorem mollis aliquam ut porttitor leo a diam sollicitudin tempor. Lacus luctus accumsan tortor posuere ac ut. Augue lacus viverra vitae congue. Purus semper eget duis at tellus at urna.Vitae congue eu consequat ac felis donec et. Lectus nulla at volutpat diam ut venenatis. Eu sem integer vitae justo eget magna fermentum iaculis eu. Auctor augue mauris augue neque gravida in fermentum et. Eget nulla facilisi etiam dignissim. Sit amet commodo nulla facilisi nullam vehicula. Enim sed faucibus turpis in. Dis parturient montes nascetur ridiculus mus mauris vitae ultricies leo. Purus in mollis nunc sed id semper risus. Auctor neque vitae tempus quam pellentesque nec nam aliquam. At volutpat diam ut venenatis tellus in. Aenean sed adipiscing diam donec adipiscing tristique risus. Pretium fusce id velit ut tortor pretium. Turpis tincidunt id aliquet risus feugiat in ante. At volutpat diam ut venenatis tellus in metus vulputate.Enim diam vulputate ut pharetra sit amet aliquam. Est ante in nibh mauris cursus. Sed enim ut sem viverra aliquet eget sit. In nibh mauris cursus mattis molestie a iaculis. Nisi lacus sed viverra tellus in hac habitasse platea. Id velit ut tortor pretium viverra. Diam vel quam elementum pulvinar etiam non quam. Dignissim suspendisse in est ante in nibh mauris cursus mattis. Interdum velit euismod in pellentesque massa. Lectus proin nibh nisl condimentum id. Id neque aliquam vestibulum morbi blandit. Arcu dictum varius duis at. Lacus suspendisse faucibus interdum posuere lorem ipsum. Aliquet porttitor lacus luctus accumsan tortor posuere ac. Integer enim neque volutpat ac. Pellentesque adipiscing commodo elit at imperdiet dui accumsan. Sit amet massa vitae tortor condimentum lacinia quis vel eros.In iaculis nunc sed augue lacus. Eget sit amet tellus cras adipiscing enim. Fermentum posuere urna nec tincidunt praesent semper. Elementum sagittis vitae et leo duis ut diam. Pharetra magna ac placerat vestibulum lectus mauris. Magna sit amet purus gravida quis blandit turpis. Orci eu lobortis elementum nibh tellus molestie nunc non. Orci porta non pulvinar neque laoreet suspendisse interdum consectetur. Adipiscing elit pellentesque habitant morbi tristique senectus. Ac odio tempor orci dapibus ultrices in iaculis. Id semper risus in hendrerit gravida rutrum. Massa id neque aliquam vestibulum morbi blandit cursus. Nunc sed augue lacus viverra.Nisi est sit amet facilisis magna etiam tempor orci. Ut eu sem integer vitae justo eget. Turpis egestas pretium aenean pharetra magna ac placerat vestibulum. Leo urna molestie at elementum. Est ullamcorper eget nulla facilisi. Ipsum dolor sit amet consectetur adipiscing elit. Phasellus egestas tellus rutrum tellus pellentesque eu tincidunt. Phasellus faucibus scelerisque eleifend donec pretium vulputate sapien nec sagittis. Amet cursus sit amet dictum sit amet. Amet venenatis urna cursus eget nunc. Nulla aliquet porttitor lacus luctus accumsan tortor. Lectus proin nibh nisl condimentum id venenatis a condimentum vitae.'}]*3
    # link = 'https://www.natlawreview.com/'
    # all_summaries.append({
    #         'summaries': summaries,
    #         'source': source_display,
    #         'link': link
    #     })

    return render_template('summaries.html',
        all_summaries=all_summaries)
    

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    return render_template('profile.html', current_user=current_user)

@app.route('/delete_profile', methods=['GET'])
def delete_profile():
    to_delete = current_user
    db.session.delete(current_user)
    db.session.commit()
    print(f'{to_delete} deleted')
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
    return render_template('edit_profile.html', title='Edit Profile',
            form=form)

@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
            title='Reset Password', form=form)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)