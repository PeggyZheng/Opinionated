//Facebook initialize.

function collectUserDetails(accessToken) {
    //make a FB api call and return an object of user details.
    FB.api('/me',
        {fields: ['last_name', 'first_name', 'email', 'id']},
        function (response) {

            var userDetails = {
                fname: response.first_name,
                lname: response.last_name,
                email: response.email,
                fbUserId: response.id
            };
            collectUserFriends(accessToken, userDetails);
        });

}

function collectUserFriends(accessToken, userDetails) {
    FB.api('/me/friends',
      function (response) {
        // if (response && !response.error) {
        //   friendsids = []
        //   for (var i = 0; i < response.data.length; i++) {
        //     friendsids.push(response.id)
        //   }
          console.log("In the get my friends function");
          console.log(response.data);
          var this_response = response;
          submitInfoToServer(accessToken, userDetails, this_response);
        })

      
      }


function submitInfoToServer(accessToken, userDetails, this_response) {
      //takes the access token, and a userdetails list as input, submits a form to the server.
      //userDetails is an object with fname, lname, email and fbUserId

      console.log('SUBMIT INFO TO SERVER');
      console.log('response from friends call');
      console.log(this_response.data);

      //create form elements
      var form = document.createElement('form');
      var userIdElement = document.createElement('input');
      var userFnameElement = document.createElement('input');
      var userLnameElement = document.createElement('input');
      var userEmailElement = document.createElement('input');
      var userFriendsElement = document.createElement('input');
      var currentAccessToken = document.createElement('input');

      //put everything all together

      var fbUserId = userDetails.fbUserId;
      var fname = userDetails.fname;
      var lname = userDetails.lname;
      var email = userDetails.email;
      var accessToken = accessToken;
      var userfriends = userDetails.friends;

      form.method = "POST";
      form.action = "/facebook-login-portal";


      //set element values
      userIdElement.value = fbUserId;
      userFnameElement.value = fname;
      userLnameElement.value = lname;
      userEmailElement.value = email;
      currentAccessToken.value = accessToken;

      //set element names
      userIdElement.name = 'fbUserId';
      userFnameElement.name = 'fbFname';
      userLnameElement.name = 'fbLname';
      userEmailElement.name = 'fbEmail';
      currentAccessToken.name = 'accessToken';

      form.appendChild(userIdElement);
      form.appendChild(userFnameElement);
      form.appendChild(userLnameElement);
      form.appendChild(userEmailElement);
      form.appendChild(currentAccessToken);

      document.body.appendChild(form);
      debugger;
      alert('STOP');
      form.submit();
  }

function statusChangeCallback(response) {
    console.log('statusChangeCallback');
    console.log(response);
    // The response object is returned with a status field that lets the
    // app know the current login status of the person.
    if (response.status === 'connected') {
    	//User is connected to both MLM and FB.
    	//Collect the access token.
    	var accessToken = response.authResponse.accessToken;

    	collectUserDetails(accessToken);

    } else if (response.status === 'not_authorized') {
      // User is connected to FB, but not MLM
      document.getElementById('status').innerHTML = 'Please log into Make Less Mush.';
    } else {
      // The person is not logged into Facebook, so we're not sure if
      // they are logged into MLM or not.
      document.getElementById('status').innerHTML = 'Please log into Facebook.';
    }
  }

function checkLoginState() {
    console.log("check login state");
	FB.getLoginStatus(function(response) {
	  statusChangeCallback(response);
	});
}


window.fbAsyncInit = function() {
  FB.init({
    appId      : '141368599534524', //Opinionated appId
    cookie     : true,  // enable cookies to allow the server to access the session
    xfbml      : true,  // parse social plugins on this page
    version    : 'v2.2' // use version 2.2
  });

  // 	//Now check to see which of the three login statuses is present for the user
    FB.getLoginStatus(function(response) {
    statusChangeCallback(response);
  });
};

// Load the SDK asynchronously
  (function(d, s, id) {
    var js, fjs = d.getElementsByTagName(s)[0];
    if (d.getElementById(id)) return;
    js = d.createElement(s); js.id = id;
    js.src = "//connect.facebook.net/en_US/sdk.js";
    fjs.parentNode.insertBefore(js, fjs);
  }(document, 'script', 'facebook-jssdk'));
