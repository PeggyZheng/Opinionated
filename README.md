# Opinionated

Opinionated is social networking web app where users can post a question or a decision they need to make and let other users help through voting. Afte the users log in, they can post a question with text descriptions, choices, and images (stored on Amazon S3), as well as a tag associated with the question. Other users will be able to vote on the question and see a visual representation of the voting result instantly. Users could also leave comments and follow other users to engage with each other. 
Built by <a href="https://www.linkedin.com/in/peggyzheng">Peggy Zheng</a> as part of her Hackbright Final Project

###Technology Stack
#####Backend
Python, Flask, Jinja, SQLite3, SQLAlchemy, Amazon S3 API/Boto, Facebook graph API
#####Frontend
Google charts, Javascript, jQuery, typeahead.js, tagmanager, Bootstrap, HTML5, CSS3

###Facebook login and graph API
Users will login with their Facebook account and gives the app the permission to access the public information on their facebook profile, such as user name, age, gender, location, profile picture, and friend list, as well as writing to their wall, which is needed for sharing posts to their facebook page. The user will folllow their facebook friends who are also registered with the app automatically when they first log in, and the app will update the following list every time they sign in with facebook credentials. 
Users will be able to share their posts or votes on Facebook by clicking on the share button on each post detail page. But this function is only enabled with the use of [ngrok] (https://ngrok.com/) or when the app is deployed. 
Once the users log out, they will be logged out of both the app and their Facebook account. 


![Alt Text](http://g.recordit.co/ZZL9a09qJL.gif)<br><br>
I copied the Jcrop div onto an HTML5 canvas, base64-encoded the canvas, and sent the selection to the server. Then, I decoded and sharpened the image, processed it using Python-Tesseract, verified it was a decimal value, and returned it on a charge form.

Some images were too large too be previewed and Jcropped on all devices (especially mobile), so I used the following Javascript to resize the image and the Jcrop utility (note: "preview2" is hidden using CSS):
<br>
```javascript
$(document).on('change','#new-receipt', function(){
    displayImage(this);
});
function displayImage(input) {
    if (input.files && input.files[0]){
        var readImage = new FileReader();
        readImage.readAsDataURL(input.files[0]);
        readImage.onloadend = function(e) {
            var imgdisplay = new Image();
            imgdisplay.src = e.target.result;
            imgdisplay.onload = function(c) {
                var orig_h = this.height;
                var orig_w = this.width;
                var canvas = document.getElementById("preview2");
                var context = canvas.getContext('2d');
                canvas.width=300;
                canvas.height=300*(orig_h/orig_w);
                context.drawImage(imgdisplay,0,0,300,300*(orig_h/orig_w));
                transformed = canvas.toDataURL("image/jpeg",1.0);
                $('#receipt-display').attr('src', transformed);
            }     
        }
    }
 };
```

Recommendation: If taking a picture of a receipt using an iPhone, make sure it is a landscape picture. See <b>Next Steps</b>.

###Charge Entry and Organization
####Groups
Users can organize charges by adding Groups (using the "GROUP" button). Groups expand to show basic information about charges. Groups can be deleted by clicking on the "x" on the far right hand side of the panel. Deleting a group does <i>not</i> delete the charges in the group.

![image](static/readme_imgs/chargeboard.png)

####Charges
Users can add and edit charges to Break It Up. Users can specify the amount paid and how it should be split between the two individuals; the total amount, percent split, and total split input fields update each other using jQuery. Any images that may be good to track (e.g. receipts, photos) can be uploaded and saved on Amazon S3 (using a hashed name). 

Charges may also be tagged with any of the Groups that have been created (including multiple). Users must proactively create groups with which they want to tag their charges. This feature uses <a href="https://maxfavilli.com/jquery-tag-manager">Tag Manager</a> and <a href="http://twitter.github.io/typeahead.js/">Typeahead</a>.

![image](static/readme_imgs/chargeform.png)

###Payments
Users can pay one another back using Venmo, Square, or in person (cash/check). After verifying the transaction, the payment is logged in the "All Charges" group. 
####Venmo
Users can authorize Break It Up to make payments using Venmo. After authorizing Break It Up, the page redirects back to the Chargeboard. The "VENMO" button now shows up instead of the "Authorize Venmo" button. The Venmo modal pulls in the user's partner's email address in the system as well as the amount entered, which are used to send the payment via Venmo. The user can change/add the email address, amount, and (private) note in the modal. If the payment is successfully completed, a green NotifyBar pops up at the bottom of the screen, and a payment is logged in "All Charges" (including the payment ID).

![image](static/readme_imgs/venmo.png)
 
####Square
The Square Connect API is only for merchants, so Break It Up uses <a href="https://squareup.com/help/us/en/article/5372-square-cash-with-email">Square Cash</a> with Email. When a user selects the "SQUARE" button, a mailto link opens in a new tab (requiring a user to be signed into their email), and a modal verifies that the user sent the Square email. This payment is logged in "All Charges."

###c3.js Visualizations
These c3 gauges make it easy to see what percentage of the time and how much out of the total the user pays. The gauges change color depending on how far the numbers stray from ~50%.
![image](static/readme_imgs/c3.png)

###Linking Accounts
Users must link accounts in order to use the application to track expenses and payments. Both users must input each other's email addresses to start tracking expenses. See <b>Next Steps</b>.
![image](static/readme_imgs/acctsettings.png)

###Mixpanel Integration
Break It Up tracks how often users click on different payment methods and submit the respective modals. 

###Setup
* Clone or fork this repo:
```
https://github.com/bpownow/BreakItUp.git
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

* Set up a <kbd>.env</kbd> file. You will need [Venmo] (https://developer.venmo.com/) and [AWS S3] (http://aws.amazon.com/s3/) developer accounts.
```
SECRET_KEY=YOUR_SECRET_ID_HERE
SQLALCHEMY_DATABASE_URI=postgresql+psycopg2://YOUR_USER_NAME@localhost/YOUR_FILE_DIRECTORY
CONSUMER_SECRET=YOUR_VENMO_CONSUMER_SECRET
CONSUMER_ID=YOUR_VENMO_CONSUMER_ID
AWS_ACCESS_KEY=YOUR_AMAZON_S3_ACCESS_KEY
AWS_SECRET_KEY=YOUR_AMAZON_S3_SECRET_KEY
AWS_BUCKET=YOUR_AMAZON_S3_BUCKET
```

* Set up [Foreman] (http://ddollar.github.io/foreman/) to [source .env] (http://mauricio.github.io/2014/02/09/foreman-and-environment-variables.html).

* Run Postgres server in a separate shell window. If you don't have Postgres, check out [Postgres.app] (http://postgresapp.com/).

* Create the database in Postgres
```
CREATE DATABASE biu;
```

* Back in your virtual environment, run the following to set up the tables in your Postgres database:
```
foreman run python -i model.py
db.create_all()
```

* Run the app:
```
foreman run python server.py
```

* Navigate to `localhost:5000` on your browser.

* If you want to test out the mobile version, download and unzip [ngrok] (https://ngrok.com/). For example, when I downloaded ngrok, it went to my Downloads folder. I used the following to unzip it:
```
unzip ../../Downloads/ngrok_2.0.17_darwin_amd64.zip
```

* To start ngrok, use `./ngrok http 5000`. Visit the Forwarding link on your phone's browser.

###Next Steps
1. Use <a href="https://openexchangerates.org/">Open Exchange Rates API</a> to add point-in-time currency conversion based on transaction date. May use <a href="https://github.com/ashokfernandez/PyExchangeRates">PyExchangeRates</a> wrapper.
2. Add a charge-specific chat or notes feature to discuss charges.
3. Find correct image orientation when displaying receipt images on non-desktop devices. See <a href="http://stackoverflow.com/questions/9353629/images-turning-sideways-upside-down-after-being-uploaded-via-phonegap-ios">this</a>.
4. Allow users to link to multiple other users and groups (many-to-many).
5. Include more Mixpanel events.

Technology Stack

Backend

Python, Flask, Jinja, PostgreSQL, SQLAlchemy, AJAX, Amazon S3 API/Boto, Venmo API, Tesseract-OCR/PyTesseract, Pillow (fork of Python Imaging Library), Mixpanel

Frontend

Javascript, jQuery, C3.js, Bootstrap, HTML5, CSS3
