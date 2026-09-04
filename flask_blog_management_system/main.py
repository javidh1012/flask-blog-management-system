from datetime import date
from dotenv import load_dotenv
from flask import Flask, abort, render_template, redirect, url_for, flash, request
from functools import wraps
import os
import hashlib
import pandas as pd
from matplotlib.figure import Figure
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_login import login_user, LoginManager, current_user, logout_user, UserMixin
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_KEY', 'temporary_local_secret_key')

# ---------------- MONGODB SETUP ---------------- #
client = MongoClient("localhost", 27017)
post_db = client.flask_database

blogpost_collection = post_db.blogposts
user_collection = post_db.users
comment_collection = post_db.comments

# ---------------- EXTENSIONS & FILTERS ---------------- #
ckeditor = CKEditor(app)
Bootstrap5(app)


@app.context_processor
def inject_gravatar():
    def gravatar_url(email, size=100, rating='g', default='retro'):
        if not email:
            email = "anonymous@example.com"
        email_encoded = email.strip().lower().encode('utf-8')
        email_hash = hashlib.md5(email_encoded).hexdigest()
        return f"https://www.gravatar.com/avatar/{email_hash}?s={size}&r={rating}&d={default}"

    return dict(gravatar=gravatar_url)


login_manager = LoginManager()
login_manager.init_app(app)


class User(UserMixin):
    def __init__(self, user_doc):
        self.doc = user_doc
        self.id = str(user_doc["_id"])
        self.email = user_doc.get("email")
        self.name = user_doc.get("name")
        self.is_admin = user_doc.get("is_admin", False)
        self.is_moderator = user_doc.get("is_moderator", False)
        self.can_post = user_doc.get("can_post", False)


@login_manager.user_loader
def load_user(user_id):
    try:
        user_doc = user_collection.find_one({"_id": ObjectId(user_id)})
        return User(user_doc) if user_doc else None
    except Exception:
        return None


# ---------------- DECORATORS ---------------- #
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not getattr(current_user, 'is_admin', False):
            return abort(403)
        return f(*args, **kwargs)

    return decorated_function


def moderator_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return abort(403)
        if not (current_user.is_admin or current_user.is_moderator):
            return abort(403)
        return f(*args, **kwargs)

    return decorated_function


def post_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):

        if not current_user.is_authenticated:
            return abort(403)

        if not (current_user.is_admin or current_user.can_post):
            return abort(403)

        return f(*args, **kwargs)

    return decorated_function

# ---------------- ROUTES ---------------- #

@app.route('/')
def get_all_posts():
    posts = list(blogpost_collection.find())
    return render_template("index.html", all_posts=posts, current_user=current_user)


@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        existing_user = user_collection.find_one({"email": form.email.data})
        if existing_user:
            flash("Email already exists! Please login instead.")
            return redirect(url_for('login'))

        new_user = {
            "email": form.email.data,
            "name": form.name.data,
            "password": generate_password_hash(form.password.data, method='pbkdf2:sha256'),
            "is_admin": False,
            "is_moderator": False,
            "can_post": False
        }
        result = user_collection.insert_one(new_user)
        new_user["_id"] = result.inserted_id

        login_user(User(new_user))
        return redirect(url_for('get_all_posts'))
    return render_template("register.html", form=form, current_user=current_user)


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user_doc = user_collection.find_one({"email": form.email.data})
        if not user_doc or not check_password_hash(user_doc['password'], form.password.data):
            flash("Invalid email or password.")
            return redirect(url_for('login'))

        login_user(User(user_doc))
        return redirect(url_for('get_all_posts'))
    return render_template("login.html", form=form, current_user=current_user)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<post_id>", methods=["GET", "POST"])
def show_post(post_id):
    post = blogpost_collection.find_one({"_id": ObjectId(post_id)})
    if not post:
        return abort(404)

    form = CommentForm()
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("Login required to post comments.")
            return redirect(url_for('login'))

        new_comment = {
            "text": form.comment_text.data,
            "author_id": ObjectId(current_user.id),
            "author_name": current_user.name,
            "author_email": current_user.email,
            "post_id": ObjectId(post_id)
        }
        comment_collection.insert_one(new_comment)
        return redirect(url_for('show_post', post_id=post_id))

    post_comments = list(comment_collection.find({"post_id": ObjectId(post_id)}))
    return render_template("post.html", post=post, form=form, comments=post_comments, current_user=current_user)


@app.route("/new-post", methods=["GET", "POST"])
@post_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        post = {
            "title": form.title.data,
            "subtitle": form.subtitle.data,
            "body": form.body.data,
            "img_url": form.img_url.data,
            "author": current_user.name,
            "author_id": ObjectId(current_user.id),
            "date": date.today().strftime("%B %d, %Y")
        }
        blogpost_collection.insert_one(post)
        return redirect(url_for('get_all_posts'))
    return render_template("make-post.html", form=form, current_user=current_user)


@app.route("/edit-post/<post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    post = blogpost_collection.find_one({"_id": ObjectId(post_id)})
    if not post:
        return abort(404)

    form = CreatePostForm(
        title=post.get("title"),
        subtitle=post.get("subtitle"),
        body=post.get("body"),
        img_url=post.get("img_url")
    )

    if form.validate_on_submit():
        blogpost_collection.update_one(
            {"_id": ObjectId(post_id)},
            {
                "$set": {
                    "title": form.title.data,
                    "subtitle": form.subtitle.data,
                    "body": form.body.data,
                    "img_url": form.img_url.data
                }
            }
        )
        return redirect(url_for('show_post', post_id=post_id))
    return render_template("make-post.html", form=form, is_edit=True, current_user=current_user)


@app.route("/delete-post/<post_id>")
@admin_only
def delete_post(post_id):
    post = blogpost_collection.find_one({"_id": ObjectId(post_id)})
    if not post:
        return abort(404)

    # Cascade delete associated comments
    comment_collection.delete_many({"post_id": ObjectId(post_id)})
    blogpost_collection.delete_one({"_id": ObjectId(post_id)})
    flash("Post and its comments deleted successfully!")
    return redirect(url_for('get_all_posts'))


@app.route("/delete-comment/<comment_id>")
@moderator_only
def delete_comment(comment_id):
    comment = comment_collection.find_one({"_id": ObjectId(comment_id)})
    if not comment:
        return abort(404)

    post_id = str(comment["post_id"])
    comment_collection.delete_one({"_id": ObjectId(comment_id)})
    flash("Comment deleted successfully!")
    return redirect(url_for("show_post", post_id=post_id))


@app.route("/edit-comment/<comment_id>", methods=["GET", "POST"])
@moderator_only
def edit_comment(comment_id):
    comment = comment_collection.find_one({"_id": ObjectId(comment_id)})
    if not comment:
        return abort(404)

    form = CommentForm()
    if request.method == "GET":
        form.comment_text.data = comment["text"]

    if form.validate_on_submit():
        comment_collection.update_one(
            {"_id": ObjectId(comment_id)},
            {"$set": {"text": form.comment_text.data}}
        )
        flash("Comment updated successfully!")
        return redirect(url_for("show_post", post_id=str(comment["post_id"])))

    return render_template("edit-comment.html", form=form, current_user=current_user)


@app.route("/dashboard")
def dashboard():
    os.makedirs("static", exist_ok=True)

    users_list = list(user_collection.find())
    posts_list = list(blogpost_collection.find())
    comments_list = list(comment_collection.find())

    users = pd.DataFrame(users_list) if users_list else pd.DataFrame(columns=["_id", "name", "email"])
    posts = pd.DataFrame(posts_list) if posts_list else pd.DataFrame(columns=["_id", "title", "date"])
    comments = pd.DataFrame(comments_list) if comments_list else pd.DataFrame(
        columns=["_id", "text", "author_id", "post_id"])

    provider_count = {}
    chart_path = None
    if not users.empty and "email" in users.columns:
        users["provider"] = users["email"].str.split("@").str[1]
        provider_count = users["provider"].value_counts().to_dict()

        fig = Figure(figsize=(5, 3))
        ax = fig.subplots()
        ax.bar(provider_count.keys(), provider_count.values())
        ax.set_title("Email Providers")
        fig.tight_layout()

        chart_path = "static/provider_chart.png"
        fig.savefig(chart_path)

    register_user = users[["name", "email"]].to_dict(orient="records") if not users.empty else []

    # --- 2. Top Comment Author Logic ---
    # --- 2. Most Commented Author Logic ---
    top_commend_author = "No Comments"
    total_author_count = 0

    if not comments.empty and not posts.empty and not users.empty:

        # Convert IDs to strings for merging
        comments['post_id_str'] = comments['post_id'].astype(str)
        posts['id_str'] = posts['_id'].astype(str)

        # Connect comments with the posts they belong to
        comment_post_merge = comments.merge(
            posts,
            left_on="post_id_str",
            right_on="id_str"
        )

        if not comment_post_merge.empty:

            # Convert post author IDs and user IDs to strings
            comment_post_merge['post_author_id_str'] = (
                comment_post_merge['author_id_y'].astype(str)
            )

            users['user_id_str'] = users['_id'].astype(str)

            # Connect posts with their authors
            final_merge = comment_post_merge.merge(
                users,
                left_on="post_author_id_str",
                right_on="user_id_str"
            )

            if not final_merge.empty:
                # Count total comments received by each author
                author_count = final_merge.groupby("name")["text"].count()

                top_commend_author = author_count.idxmax()
                total_author_count = int(author_count.max())

    # --- 3. Most Commented Post Logic ---
    max_post_comment_title = "No Posts"
    max_post_comment_count = 0
    if not comments.empty and not posts.empty:
        comments['post_id_str'] = comments['post_id'].astype(str)
        posts['id_str'] = posts['_id'].astype(str)
        post_merge = comments.merge(posts, left_on="post_id_str", right_on="id_str")
        if not post_merge.empty:
            post_comments_count = post_merge.groupby("title")["text"].count()
            max_post_comment_title = post_comments_count.idxmax()
            max_post_comment_count = int(post_comments_count.max())

    # --- 4. Trends Logic (Thread-safe plot generation) ---
    trends_path = None
    if not posts.empty and "date" in posts.columns:
        posts["parsed_date"] = pd.to_datetime(posts["date"], errors="coerce")
        posts_clean = posts.dropna(subset=["parsed_date"]).copy()  # explicit copy avoids copy warnings
        if not posts_clean.empty:
            posts_clean["year"] = posts_clean["parsed_date"].dt.year
            yearly_posts = posts_clean.groupby("year").size()

            # Thread-safe explicit Figure object initialization
            fig2 = Figure(figsize=(8, 3))
            ax2 = fig2.subplots()
            ax2.plot(yearly_posts.index, yearly_posts.values, marker="o")
            ax2.set_title("Blog Post Trend Over Years")
            ax2.set_xlabel("Year")
            ax2.set_ylabel("Number of Posts")
            ax2.set_xticks(yearly_posts.index)
            fig2.tight_layout()

            trends_path = "static/trends_path.png"
            fig2.savefig(trends_path)

    return render_template(
        "dashboard.html",
        users=users,
        posts=posts,
        comments=comments,
        total_users=len(users),
        total_comments=len(comments),
        total_posts=len(posts),
        provider_count=provider_count,
        register_user=register_user,
        plot=chart_path,
        top_commend_author=top_commend_author,
        total_author_count=total_author_count,
        max_post_comment_title=max_post_comment_title,
        max_post_comment_count=max_post_comment_count,
        trends_path=trends_path
    )


@app.route("/about")
def about():
    return render_template("about.html", current_user=current_user)


@app.route("/contact")
def contact():
    return render_template("contact.html", current_user=current_user)


if __name__ == "__main__":
    app.run(debug=True, port=5001)
