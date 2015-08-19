//Facebook initialize.

function collectUserDetails(accessToken) {
    //make a FB api call and return an object of user details.
    FB.api('/me',
        // {fields: 'id'},
        function (response) {

            var userDetails = {
                user_id: response.id,
                accessToken: accessToken
            };

            console.log(userDetails);
            $.post('/facebook-login-portal', userDetails, function(result){
                location.href="/home";})

        });
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
        console.log(accessToken);

        collectUserDetails(accessToken);

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
    version    : 'v2.4' // use version 2.2
  });

  // 	//Now check to see which of the three login statuses is present for the user
    FB.getLoginStatus(function(response) {
    statusChangeCallback(response);
  });
};

function myFacebookLogout() {
  FB.logout(function(response) {
  // user is now logged out
  });
}