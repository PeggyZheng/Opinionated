///**
// * Created by peggyzheng on 8/12/15.
// */
//window.fbAsyncInit = function() {
//    FB.init({
//        appId      : '141368599534524',
//        xfbml      : true,
//        cookie     : false,
//        version    : 'v2.4'
//    });
//    // place code here that I want to run as soon as the page is loaded
//
//    //share something on facebook
//    // FB.ui(
//    //    {
//    //     method: 'share_open_graph',
//    //     action_type: 'og.likes',
//    //     action_properties: JSON.stringify({
//    //       object:'http://014877ee.ngrok.io'
//    //     })
//    //   }, function(response){
//    //     console.log(response);
//    //       if (response && !response.error_code) {
//    //           alert('Posting completed.');
//    //       } else {
//    //           alert('Error while posting.');}
//    //   });
//
//    FB.ui(
//        {
//            method: 'feed',
//            href: 'http://014877ee.ngrok.io/home/post/{{ post.post_id }}',
//        }, function(response){});
//
//};  //close the fbAsyncInit function
//
//(function(d, s, id){
//        var js, fjs = d.getElementsByTagName(s)[0];
//        if (d.getElementById(id)) {return;}
//        js = d.createElement(s); js.id = id;
//        js.src = "//connect.facebook.net/en_US/sdk.js";
//        fjs.parentNode.insertBefore(js, fjs);
//    }(document, 'script', 'facebook-jssdk'));
//
////function myFacebookLogin() {
////      FB.login(function(){}, {scope: 'user_location'});
////    }
//
////myFacebookLogout is never used atm.
//function myFacebookLogout() {
//  FB.logout(function(response) {
//  // user is now logged out
//  });
//}