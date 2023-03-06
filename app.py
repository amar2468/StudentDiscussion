import os
from datetime import date, datetime
from flask import Flask, render_template, request, redirect, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from bson.objectid import ObjectId
from flask_share import Share
import db

share = Share()

app = Flask(__name__)
app.secret_key = '32892938832jfdjjkd2993nd'
app.config["SESSION_TYPE"] = "filesystem"

share.init_app(app)

# Route for homepage which also checks whether the user is logged in or not

@app.route('/')
def home():
	subforum_info = db.subforum_database.SubforumList.find()
	notifications_info = db.notifications_database.NotificationsList.find()
	number_of_notifications = db.notifications_database.NotificationsList.count_documents({'username': session.get("name"), 'seen': False})
	
	return render_template("home.html", subforum_info=subforum_info, notifications_info=notifications_info,number_of_notifications=number_of_notifications)

@app.route('/visit_subforum/<subforum_name>')
def visit_subforum(subforum_name):
	collection_info = db.forum_database.ForumPostCollection.find().sort('time_stamp_when_post_created', -1)

	date_and_time_post_created = datetime.now()
		
	formatted_date_and_time_post_created = date_and_time_post_created.strftime("%d/%m/%Y %H:%M:%S")

	notifications_info = db.notifications_database.NotificationsList.find()
	number_of_notifications = db.notifications_database.NotificationsList.count_documents({'username': session.get("name"), 'seen': False})
	
	return render_template("subforum.html", subforum_name=subforum_name ,formatted_date_and_time_post_created=formatted_date_and_time_post_created, collection_info=collection_info,notifications_info=notifications_info,number_of_notifications=number_of_notifications)


# Route for register account which allows the user to register

@app.route('/register_account', methods =["GET", "POST"])
def register_account():
	if not session.get("name"):
		if request.method == "POST":
			fname = request.form.get("first_name")
			lname = request.form.get("last_name")
			email = request.form.get("email_address_for_register")
			passwd = request.form.get("user_password_for_register")
			profile_pic = request.files['profile_picture_for_register']

			if db.register_login_database.RegLoginCollection.find_one({"email": {"$eq": email}}):
				return redirect("/register_account")
			else:
				encrypted_password = generate_password_hash(passwd)

				saving_profile_picture = secure_filename(profile_pic.filename)

				if profile_pic.filename == "":
					saving_profile_picture = secure_filename('360_F_346839683_6nAPzbhpSkIpb8pmAwufkC7c5eD7wYws.jpg')
				else:
					profile_pic.save(os.path.join("static/", saving_profile_picture))

				date_registered = date.today()

				date_registered = date_registered.strftime("%d/%m/%Y")

				db.register_login_database.RegLoginCollection.insert_one({"first_name": fname, "last_name":lname, "email":email, "password": encrypted_password, "profile_picture_link": saving_profile_picture,'user_registered': date_registered, "list_of_followers": [], "number_of_followers":0, "list_of_following": [], "number_of_following":0})
				
				session["name"] = request.form.get("email_address_for_register")

				session.permanent = True
				
				return redirect("/student_profile")
		else:
			return render_template("RegisterAccount.html")
	else:
		return 'You are already logged in'

# Route for login account which allows the user to log in

@app.route('/login_account', methods =["GET", "POST"])
def login_account():
	if not session.get("name"):
		if request.method == "POST":
			email_for_login = request.form.get("email_address_for_login")
			password_for_login = request.form.get("user_password_for_login")

			for document in db.register_login_database.RegLoginCollection.find():
				if email_for_login == document["email"]:
					if check_password_hash(document["password"],password_for_login):
						session["name"] = request.form.get("email_address_for_login")
						session.permanent = True
						return redirect("/student_profile")
			return redirect("/login_account")
		else:
			return render_template("Login.html")
	else:
		return "You are already logged in"

# Route created so that the user can logout when they want to

@app.route('/logout')
def logout():
	if session.get("name"):
		session["name"] = None
		return redirect("/login_account")
	else:
		return 'Cannot logout when you are not logged in'

# Route created for student profile

@app.route('/student_profile')
def student_profile():
	for document in db.register_login_database.RegLoginCollection.find():
		if document["email"] == session["name"]:
			notifications_info = db.notifications_database.NotificationsList.find()
			number_of_notifications = db.notifications_database.NotificationsList.count_documents({'username': session.get("name"), 'seen': False})
			return render_template("student_profile.html", document = document, notifications_info=notifications_info, number_of_notifications=number_of_notifications)
# Route created for student profile

@app.route('/viewing_profile/<student_profile_email>')
def viewing_profile(student_profile_email):
	for document in db.register_login_database.RegLoginCollection.find():
		if document["email"] == student_profile_email:
			notifications_info = db.notifications_database.NotificationsList.find()
			number_of_notifications = db.notifications_database.NotificationsList.count_documents({'username': session.get("name"), 'seen': False})
			return render_template("student_profile.html", document = document, notifications_info=notifications_info, number_of_notifications=number_of_notifications)

# Route created for changing profile picture

@app.route('/changing_profile_picture', methods =["GET", "POST"])
def changing_profile_picture():

	profile_picture = request.files['change_profile_picture_file_upload']
	changing_profile_picture = secure_filename(profile_picture.filename)
	profile_picture.save(os.path.join("static/", changing_profile_picture))
	
	db.register_login_database.RegLoginCollection.update_one(
		{ 'email': session.get("name") },
		{ "$set": { 'profile_picture_link': changing_profile_picture } }
	)

	return redirect("/student_profile")


# Route created to render the forgot password html template

@app.route('/render_forgot_password_template', methods =["GET", "POST"])
def render_forgot_password_template():
	notifications_info = db.notifications_database.NotificationsList.find()
	number_of_notifications = db.notifications_database.NotificationsList.count_documents({'username': session.get("name"), 'seen': False})
	return render_template("forgot_password.html", notifications_info=notifications_info, number_of_notifications=number_of_notifications)

# Route created for forgot password

@app.route('/forgot_password', methods =["GET", "POST"])
def forgot_password():
	pwd_reset = request.form.get("password_reset")
	confirm_pwd_reset = request.form.get("confirm_password_reset")

	encrypted_pwd = generate_password_hash(pwd_reset)

	if pwd_reset == confirm_pwd_reset:
		db.register_login_database.RegLoginCollection.update_one(
			{ 'email': session.get("name") },
			{ "$set": { 'password': encrypted_pwd } }
		)
	return redirect("/student_profile")

# Route for forum post render

@app.route('/render_forum_post/<subforum_name>', methods =["GET", "POST"])
def render_forum_post(subforum_name):
	if session.get("name"):
		notifications_info = db.notifications_database.NotificationsList.find()
		number_of_notifications = db.notifications_database.NotificationsList.count_documents({'username': session.get("name"), 'seen': False})
		return render_template("forum_post.html", subforum_name=subforum_name,notifications_info=notifications_info, number_of_notifications=number_of_notifications)
	elif not session.get("name"):
		collection_info = db.forum_database.ForumPostCollection.find()
		return render_template("subforum.html", collection_info=collection_info)

# Route for viewing topic

@app.route('/view_topic/<_id>')
def view_topic(_id):
	user_info = db.register_login_database.RegLoginCollection.find()

	for document in db.forum_database.ForumPostCollection.find():
		if str(document["_id"]) == _id:
			post_title = document['title_of_post']
			content_post = document['content_of_post']
			collection_info = list(db.forum_database.ForumPostCollection.find())

			for user in user_info:
				if user['email'] == document['author_of_post']:
					registration_date_user = user['user_registered']
					break
			notifications_info = db.notifications_database.NotificationsList.find()
			number_of_notifications = db.notifications_database.NotificationsList.count_documents({'username': session.get("name"), 'seen': False})
			return render_template("view_forum_post.html", _id=_id ,registration_date_user=registration_date_user, user_info=user_info, post_title=post_title ,content_post = content_post, collection_info=collection_info,notifications_info=notifications_info, number_of_notifications=number_of_notifications)
	collection_info = list(db.forum_database.ForumPostCollection.find())

	notifications_info = db.notifications_database.NotificationsList.find()
	number_of_notifications = db.notifications_database.NotificationsList.count_documents({'username': session.get("name"), 'seen': False})
	return render_template("view_forum_post.html", _id=_id, user_info=user_info, post_title = post_title, content_post = content_post, collection_info=collection_info, notifications_info=notifications_info, number_of_notifications=number_of_notifications)


# Route for rendering template that allows the user to re-enter the information that they want to update

@app.route('/edit_topic/<id_edit>')
def edit_topic(id_edit):
	for document in db.forum_database.ForumPostCollection.find():
		if str(document["_id"]) == id_edit:
			notifications_info = db.notifications_database.NotificationsList.find()
			number_of_notifications = db.notifications_database.NotificationsList.count_documents({'username': session.get("name"), 'seen': False})
			return render_template("update_post.html", document=document ,id_edit=id_edit, notifications_info=notifications_info, number_of_notifications=number_of_notifications)

# Route for edit topic
@app.route('/edit_forum_topic/<id_edit>', methods =["GET", "POST"])
def edit_forum_topic(id_edit):

	topic_title = request.form.get("title_of_post")
	topic_content = request.form.get("post_content")

	db.forum_database.ForumPostCollection.update_one(
		{ '_id':  ObjectId(id_edit) },
		{ "$set": { 'title_of_post': topic_title } }
	)

	db.forum_database.ForumPostCollection.update_one(
		{ '_id':  ObjectId(id_edit) },
		{ "$set": { 'content_of_post': topic_content } }
	)

	return redirect("/")

# Route for deleting a topic

@app.route('/delete_topic/<id_delete>')
def delete_topic(id_delete):
	db.forum_database.ForumPostCollection.delete_one( {"_id": ObjectId(id_delete)})

	return redirect("/")

# Route for like post functionality

@app.route('/like_post/<like_post_id>')
def like_post(like_post_id):

	for document in db.forum_database.ForumPostCollection.find():
		if str(document["_id"]) == like_post_id:
			if session.get("name") == document["author_of_post"]:

				subforum_name = document["subforum"]

				if document["user_liked_own_post"] == False:

					db.forum_database.ForumPostCollection.update_one(
						{ '_id':  ObjectId(like_post_id) },
						{ "$set": { 'user_liked_own_post':  True} }
					)

					db.forum_database.ForumPostCollection.update_one(
						{ '_id':  ObjectId(like_post_id) },
						{ "$inc": { 'number_of_likes':  1} }
					)

					db.forum_database.ForumPostCollection.update_one(
						{ '_id':  ObjectId(like_post_id) },
						{ "$push": { 'all_users_who_liked_post': session.get("name") } }
					)
				return redirect("/visit_subforum/" + subforum_name)
			
			else:
				if session.get("name") not in document["all_users_who_liked_post"] and session.get("name") != None:

					subforum_name = document["subforum"]

					db.forum_database.ForumPostCollection.update_one(
						{ '_id':  ObjectId(like_post_id) },
						{ "$inc": { 'number_of_likes':  1} }
					)

					db.forum_database.ForumPostCollection.update_one(
						{ '_id':  ObjectId(like_post_id) },
						{ "$push": { 'all_users_who_liked_post': session.get("name") } }
					)

					notification_content = session.get("name") + " liked your post : " + document["title_of_post"]
					db.notifications_database.NotificationsList.insert_one({"notification_type":'like' ,"forum_post_id":like_post_id,"username":document["author_of_post"],"username_of_follower":session.get("name"),"content":notification_content,"seen":False })
					return redirect("/visit_subforum/" + subforum_name)
	return redirect("/login_account")


# Route for dislike post functionality

@app.route('/dislike_post/<dislike_post_id>')
def dislike_post(dislike_post_id):

	for document in db.forum_database.ForumPostCollection.find():
		if str(document["_id"]) == dislike_post_id:

			if session.get("name") == document["author_of_post"]:

				subforum_name = document["subforum"]

				if document["user_disliked_own_post"] == False:

					db.forum_database.ForumPostCollection.update_one(
						{ '_id':  ObjectId(dislike_post_id) },
						{ "$set": { 'user_disliked_own_post':  True} }
					)

					db.forum_database.ForumPostCollection.update_one(
						{ '_id':  ObjectId(dislike_post_id) },
						{ "$inc": { 'number_of_dislikes':  1} }
					)

					db.forum_database.ForumPostCollection.update_one(
						{ '_id':  ObjectId(dislike_post_id) },
						{ "$push": { 'all_users_who_disliked_post': session.get("name") } }
					)
				return redirect("/visit_subforum/" + subforum_name)
			
			else:
				if session.get("name") not in document["all_users_who_disliked_post"] and session.get("name") != None:

					subforum_name = document["subforum"]

					db.forum_database.ForumPostCollection.update_one(
						{ '_id':  ObjectId(dislike_post_id) },
						{ "$inc": { 'number_of_dislikes':  1} }
					)

					db.forum_database.ForumPostCollection.update_one(
						{ '_id':  ObjectId(dislike_post_id) },
						{ "$push": { 'all_users_who_disliked_post': session.get("name") } }
					)
					
					return redirect("/visit_subforum/" + subforum_name)


	return redirect("/login_account")

# Route for liking a reply

@app.route('/like_a_reply/<reply_id>', methods =["GET", "POST"])
def like_a_reply(reply_id):

	reply_id = int(reply_id)

	db.forum_database.ForumPostCollection.update_one(
		{ "comments.id": reply_id, "comments.list_of_users_who_liked": { "$nin": [session.get("name")] } },
		{ "$push": { "comments.$.list_of_users_who_liked": session.get("name") }, "$inc": { "comments.$.number_of_likes_for_reply": 1 } }
	)

	return redirect("/")

# Route for disliking a reply

@app.route('/dislike_a_reply/<reply_id>', methods =["GET", "POST"])
def dislike_a_reply(reply_id):

	reply_id = int(reply_id)

	db.forum_database.ForumPostCollection.update_one(
		{ "comments.id": reply_id, "comments.list_of_users_who_disliked": { "$nin": [session.get("name")] } },
		{ "$push": { "comments.$.list_of_users_who_disliked": session.get("name") }, "$inc": { "comments.$.number_of_dislikes_for_reply": 1 } }
	)

	return redirect("/")

# Route for dealing with forum post form

@app.route('/forum_post', methods =["GET", "POST"])
def forum_post():
	if session.get("name"):
		subforum_name = request.form.get("name_of_subforum")
		title = request.form.get("title_of_post")
		content = request.form.get("post_content")
		date_and_time_post_created = datetime.now()
		
		formatted_date_and_time_post_created = date_and_time_post_created.strftime("%d/%m/%Y %H:%M:%S")

		db.forum_database.ForumPostCollection.insert_one({"subforum":subforum_name, "author_of_post":session.get("name"), "title_of_post": title, "content_of_post": content, "number_of_likes": 0, "number_of_dislikes": 0, "user_liked_own_post": False, "user_disliked_own_post": False, "all_users_who_liked_post": [], "all_users_who_disliked_post": [], "time_stamp_when_post_created": formatted_date_and_time_post_created, "comments":[]})

		return redirect('/visit_subforum/' + subforum_name)
	elif not session.get("name"):
		return redirect('/visit_subforum/' + subforum_name)

# Route for dealing with following user

@app.route('/follow_user/<student_profile_email>', methods =["GET", "POST"])
def follow_user(student_profile_email):
	if session.get("name"):
		follow_button = request.form.get("follow_button");
		
		if follow_button == "Follow":
			db.register_login_database.RegLoginCollection.update_one(
				{ 'email': student_profile_email },
				{ "$push": { 'list_of_followers': session.get("name") } }
			)

			user_collection = db.register_login_database.RegLoginCollection.find_one({ 'email': student_profile_email })
			number_of_followers = len(user_collection["list_of_followers"])

			db.register_login_database.RegLoginCollection.update_one(
				{ 'email': student_profile_email },
				{ "$set": { 'number_of_followers':  number_of_followers } }
			)

			db.register_login_database.RegLoginCollection.update_one(
				{ 'email': session.get("name") },
				{ "$push": { 'list_of_following': student_profile_email } }
			)

			user_collection = db.register_login_database.RegLoginCollection.find_one({ 'email': session.get("name") })
			number_of_following = len(user_collection["list_of_following"])

			db.register_login_database.RegLoginCollection.update_one(
				{ 'email': session.get("name") },
				{ "$set": { 'number_of_following':  number_of_following } }
			)

			# Add in notifications database
			notification_content = session.get("name") + " followed you"
			db.notifications_database.NotificationsList.insert_one({"notification_type":'follow',"username":student_profile_email,"username_of_follower":session.get("name"),"content":notification_content,"seen":False })

		elif follow_button == "Following":
			db.register_login_database.RegLoginCollection.update_one(
				{ 'email': student_profile_email },
				{ "$pull": { 'list_of_followers': session.get("name") } }
			)

			user_collection = db.register_login_database.RegLoginCollection.find_one({ 'email': student_profile_email })
			number_of_followers = len(user_collection["list_of_followers"])

			db.register_login_database.RegLoginCollection.update_one(
				{ 'email': student_profile_email },
				{ "$set": { 'number_of_followers':  number_of_followers } }
			)

			db.register_login_database.RegLoginCollection.update_one(
				{ 'email': session.get("name") },
				{ "$pull": { 'list_of_following': student_profile_email } }
			)

			user_collection = db.register_login_database.RegLoginCollection.find_one({ 'email': session.get("name") })
			number_of_following = len(user_collection["list_of_following"])

			db.register_login_database.RegLoginCollection.update_one(
				{ 'email': session.get("name") },
				{ "$set": { 'number_of_following':  number_of_following } }
			)

		return redirect('/student_profile')
	elif not session.get("name"):
		return redirect('/login_account')


# Route to redirect to the list of followers page

@app.route('/list_of_followers/<student_email>', methods =["GET", "POST"])
def list_of_followers(student_email):
	if session.get("name"):
		registration_info = db.register_login_database.RegLoginCollection.find()
		notifications_info = db.notifications_database.NotificationsList.find()
		number_of_notifications = db.notifications_database.NotificationsList.count_documents({'username': session.get("name"), 'seen': False})
		
		return render_template("list_of_followers.html", student_email=student_email, registration_info=registration_info, notifications_info=notifications_info, number_of_notifications=number_of_notifications)
	elif not session.get("name"):
		return redirect('/')

# Route to redirect to the list of following page

@app.route('/list_of_following/<student_email>', methods =["GET", "POST"])
def list_of_following(student_email):
	if session.get("name"):
		registration_info = db.register_login_database.RegLoginCollection.find()
		db.notifications_database.NotificationsList.update_many({'username': session.get("name")}, {'$set': {'seen': True}})
		notifications_info = db.notifications_database.NotificationsList.find()
		number_of_notifications = db.notifications_database.NotificationsList.count_documents({'username': session.get("name"), 'seen': False})
		return render_template("list_of_following.html", student_email=student_email, registration_info=registration_info, notifications_info=notifications_info, number_of_notifications=number_of_notifications)
	elif not session.get("name"):
		return redirect('/')

@app.route('/reply_to_the_post/<post_id>', methods =["GET", "POST"])
def reply_to_the_post(post_id):
	if request.method == "POST":
		reply_content = request.form.get("reply_content")

	date_and_time_of_reply = datetime.now()
		
	date_and_time_of_reply_formatted = date_and_time_of_reply.strftime("%d/%m/%Y %H:%M:%S")

	db.forum_database.ForumPostCollection.update_one(
		{ '_id': ObjectId(post_id) },
		{ "$push": { 'comments': ({"author_of_post":session.get("name"), "content_of_post": reply_content, "timestamp_for_reply":date_and_time_of_reply_formatted, "number_of_likes_for_reply":0, "number_of_dislikes_for_reply":0 }) } }
	)

	student = db.forum_database.ForumPostCollection.find_one({ '_id': ObjectId(post_id) })
	student_profile_email = student["author_of_post"]
	forum_post_title = student["title_of_post"]

	# Add in notifications database
	notification_content = session.get("name") + " has replied to your post : " + forum_post_title
	db.notifications_database.NotificationsList.insert_one({"notification_type":'reply',"forum_post_id":post_id,"username":student_profile_email,"username_of_follower":session.get("name"),"content":notification_content,"seen":False})

	return redirect('/')

@app.route('/update_notification_count', methods =["GET", "POST"])
def update_notification_count():
	if request.method == "POST":
		db.notifications_database.NotificationsList.update_many({'username': session.get("name")}, {'$set': {'seen': True}})
		number_of_notifications = db.notifications_database.NotificationsList.count_documents({'username': session.get("name"), 'seen': False})
		return jsonify(number_of_notifications=number_of_notifications)

if __name__ == '__main__':
	app.run(debug=True)