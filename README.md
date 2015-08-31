# Opinionated

Opinionated is social networking web app where users can post a question or a decision they need to make and let other users help through voting. Afte the users log in, they can post a question with text descriptions, choices, and images (stored on Amazon S3), as well as a tag associated with the question. Other users will be able to vote on the question and see a visual representation of the voting result instantly. Users could also leave comments and follow other users to engage with each other. 
Built by <a href="https://www.linkedin.com/in/peggyzheng">Peggy Zheng</a> as part of her Hackbright Final Project

###Technology Stack
#####Backend
Python, Flask, Jinja, SQLite3, SQLAlchemy, Amazon S3 API/Boto, Facebook graph API
#####Frontend
Google charts, Javascript, jQuery, typeahead.js, tagmanager, Bootstrap, HTML5, CSS3

###Facebook login and graph API
Users will login with their Facebook account and gives the app the permission to access the public information on their facebook profile, such as user name, age, gender, location, profile picture, and friend list, as well as writing to their wall, which is needed for sharing posts to their facebook page. 

The user will folllow their facebook friends who are also registered with the app automatically when they first log in, and the app will update the following list every time they sign in with facebook credentials. 
Users will be able to share their posts or votes on Facebook by clicking on the share button on each post detail page. But this function is only enabled with the use of [ngrok] (https://ngrok.com/) or when the app is deployed. 
Once the users log out, they will be logged out of both the app and their Facebook account. 

This feature is implemented through Facebook open graph API in conjunction with the library <a href="https://facebook-sdk.readthedocs.org/en/latest/">Facebook SDK for Python</a>. The login popup window and authentication are implemented in javascript with Facebook API and the fetching of user information is done in the controller for ease of storing and manipulating the data. 


###Posting a question
A user needs to log in to post a question. If they are not logged in, they will be redirected to the home page for logging in. 
![Alt Text](http://g.recordit.co/kWzPNEfs0K.gif)<br><br>
####File types
Users could upload files in these formats: 'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif' for clearer representation of their questions and options. They will see a preview of the image once they attach the files. All images are saved on Amazon S3 (using a hashed name).

####Tags
Users can add tags to their posts so it is searchable. The typeahead function is enabled, so as the users are typing, all existing tags with word or letter matched will show up for suggestions. This feature uses <a href="https://maxfavilli.com/jquery-tag-manager">Tag Manager</a> and <a href="http://twitter.github.io/typeahead.js/">Typeahead</a>.

####Deleting a post
Users can also delete their posts if they want to. But modification on the post details is not allowed once a post is created for the purpose of maintaining the voting integrity. 


###Voting on a post
Users can view their own and other users' posts and vote on them or leaving comments in the post details page. Each user can only cast one valid vote, but they are allowed to change vote as many times as they want. 
When the user first arrives on a new post that he/she has not voted on, the voting result will be hidden so the viewer can vote unbiasedly. Once they vote, the result will show up in chart format. 

A user can view any posts and comments without having to log in. But in order to vote and see the vote results, he/she will need to log in. 
![Alt Text](http://g.recordit.co/4tBbzbrkEI.gif)<br><br>
####Google Charts
The voting results are displayed in interactive charts based on different attributes. 4 types of charts(donut chart, bar chart, geochart, and column chart) are utilized to better demonstrate how the votes are broken down on certain user characterists, such as gender, geographic location and age group. The information are gathered through Facebook. Users can also hover over the chart to see the details on how many poeple voted on which choice.
This feature is implemented with Google charts. 

####Commenting
Users can interact with the author or other users through the commenting area. They can leave comments and delete comments anytime. 

####Sharing to Facebook
The users are able to share a particular post to their Facebook wall by clicking on the share button. So it provides a link back to the post page for their facebook friends who are interested in checking it out.


###Follow other users
A following system is in place, where users can follow other users whom they want to keep up to date with all their posts. Just click on the follow button on a particular user's profile page and you are now following her/him. Unfollowing a person is equally easy, by just clicking the unfollow button. You could see a list of your followers and people you followed as well as since when the follow starts. 
On the home page you could filter to see only the posts from the people you follow instead of every single post. 

###Tags
####Search by tags
Tags are great place to start with your exploration of the whole site. On the login page, you could see 6 tiles showing the current most popular tags and links to the posts associated with the tag. Choose the ones that interest you and get started

A search box in placed on the navigation bar that allows you to search posts by tags, whichever page you are on. 

###Test
####Unittest
The unittesting covers most of the methods in the model and is implemented throughout the development process.
A test suite that consists of a setup of test database and teardown is in place to facilitate refactoring and testing corner cases. 

###Setup
* Clone or fork this repo:
```
https://github.com/PeggyZheng/Opinionated.git
```

* Create and activate a virtual environment inside your project directory: 
```
virtualenv env
source env/bin/activate
```

* Install requirements.txt:
```
pip install -r requirements.txt
```

* Set up a <kbd>.env</kbd> file. You will need [Facebook] (https://developers.facebook.com/) and [AWS S3] (http://aws.amazon.com/s3/) developer accounts.
```
SECRET_KEY=YOUR_SECRET_ID_HERE
SQLALCHEMY_DATABASE_URI=postgresql+psycopg2://YOUR_USER_NAME@localhost/YOUR_FILE_DIRECTORY
FB_APP_ID=YOUR_FACEBOOK_APP_ID
FB_APP_NAME=YOUR_FACEBOOK_APP_NAME
FB_APP_SECRET=YOUR_FACEBOOK_APP_SECRET
AWS_ACCESS_KEY=YOUR_AMAZON_S3_ACCESS_KEY
AWS_SECRET_KEY=YOUR_AMAZON_S3_SECRET_KEY
AWS_BUCKET=YOUR_AMAZON_S3_BUCKET
```

* In your virtual environment, run the following to set up the tables in your database:
```
python -i models.py
db.create_all()
```

* Run the app:
```
python server.py
```

* Navigate to `localhost:5000` on your browser.

* If you need to test the Facebook share function, download <a href="https://ngrok.com/To start ngrok">ngrok</a>.
* 
* To start ngrok, use `./ngrok http 5000`, and copy the url it generates to the browser.

###Next Steps
1. Add the anonymous posting capibilities, so the user can choose to be anonymous for posting questions
2. Enable infite scroll on the post list page, which is more desirable in a moden web app. 
3. Migrate to Postgres or MySql to allow flexible query and managing bigger size of users and posts.
4. Allow uploading of other file types, audio and video, for easier describing of the questions and options. 
5. Work on image compression, so it is compressed to certain size for faster uploading speed and consistency in displaying. 


