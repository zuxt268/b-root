console.log("main.js")

document.getElementById("facebook_login").addEventListener("click", (event) =>{
  FB.login(function(response){
      let accessToken = response.authResponse.accessToken;

      let form = document.createElement('form');
      form.setAttribute('method', 'post');
      form.setAttribute('action', '/facebook/auth');
      form.setAttribute('facebook_access_token', response.authResponse.accessToken);

      let accessTokenField = document.createElement('input');
      accessTokenField.setAttribute('type', 'hidden');
      accessTokenField.setAttribute('name', 'accessToken'); // 'name'属性を使用
      accessTokenField.setAttribute('value', accessToken); // accessTokenの値を設定

      form.appendChild(accessTokenField);
      document.body.appendChild(form);
      form.submit();
  }, {scope: 'public_profile,email,pages_show_list,instagram_basic,pages_read_engagement'});
})