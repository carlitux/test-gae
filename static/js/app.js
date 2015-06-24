// Is not the best code, many validation are not done!

angular.module('testExample', ['ngRoute', 'ngResource'])
  .config(function($interpolateProvider) {
    $interpolateProvider.startSymbol('{$');
    $interpolateProvider.endSymbol('$}');
  })

 .controller('MainController', function($scope, $route, $routeParams, $location) {
     $scope.$route = $route;
     $scope.$location = $location;
     $scope.$routeParams = $routeParams;
     $scope.message = ""
 })

 .controller('RegistrationController', function($scope, $routeParams, $resource, $location) {
     $scope.fullName = '';
     $scope.email = '';
     $scope.password = '';
     $scope.errors = {};

     $scope.doSignup = function (event) {
       var User = $resource('/api/users');
       var user = new User({full_name: $scope.fullName, email: $scope.email, password: $scope.password})
       $scope.errors = {};
       user.$save(function(user) {
         angular.element('#main-container').scope().message =  "Login into your new account";
         $location.path( "/login" );
       }, function(response){
         for (key in response.data) {
           if (response.data[key].join)
             $scope.errors[key] = response.data[key].join(', ');
           else
              $scope.errors[key] = response.data[key];
         }
       });
     }
 })
 
 .controller('LoginController', function($scope, $routeParams, $resource, $location) {
     $scope.email = '';
     $scope.password = '';
     $scope.errors = {};

     $scope.doLogin = function (event) {
       var Login = $resource('/api/login');

       var user = new Login({email: $scope.email, password: $scope.password});
       $scope.errors = {};
       user.$save(function(user) {
          window.location.href = '/';
       }, function(response){
         for (key in response.data) {
           if (response.data[key].join)
             $scope.errors[key] = response.data[key].join(', ');
           else
              $scope.errors[key] = response.data[key];
         }
       });
     }
 })

 .controller('LogoutController', function($scope, $routeParams, $resource, $location) {
       var Logout = $resource('/api/logout');
       var rootScope = angular.element('#main-container').scope();
       rootScope.message = "You will be logged out soon."
       Logout.get(function(data){
          console.log(data);
          window.location.href = '/';
       });
 })
 
 .controller('MessageSendController', function($scope, $routeParams, $resource, $location) {
     $scope.sender = '';
     $scope.recipient = $routeParams.email;
     $scope.body = '';
     $scope.errors = {};

     $scope.doSubmit = function (event) {
       var Message = $resource('/api/messages');
       var message = new Message({sender: $scope.sender, recipient: $scope.recipient, body: $scope.body})
       $scope.errors = {};
       message.$save(function(user) {
         angular.element('#main-container').scope().message =  "Your message was sent successfully";
         window.location.href = "/messages";
       }, function(response){
         for (key in response.data) {
           if (response.data[key].join)
             $scope.errors[key] = response.data[key].join(', ');
           else
             $scope.errors[key] = response.data[key];
         }
       });
     }
 })

 .controller('MessagesController', function($scope, $routeParams, $resource, $location) {
     var Message = $resource('/api/messages');
     var rootScope = angular.element('#main-container').scope();

     Message.query(function(data){
       $scope.messages = data;
     }, function(){ console.log(arguments); });
 })

 .controller('HomeController', function($scope, $routeParams, $resource, $location) {
     $scope.name = "HomeController";
     $scope.params = $routeParams;

     var User = $resource('/api/users');
     var rootScope = angular.element('#main-container').scope();

     User.query(function(data){
       $scope.users = data;
     }, function(){ console.log(arguments); });
 })

.config(function($routeProvider, $locationProvider) {
  $routeProvider
  .when('/', {
   templateUrl: 'templates/home.html',
   controller: 'HomeController',
   resolve: {
     // I will cause a 1 second delay
       delay: function($q, $timeout) {
         var delay = $q.defer();
         $timeout(delay.resolve, 1000);
         return delay.promise;
       }
     }
   })
   
  .when('/signup', {
     templateUrl: 'templates/signup.html',
     controller: 'RegistrationController',
     resolve: {
       delay: function($q, $timeout) {

       }
    }
   })
   
  .when('/login', {
    templateUrl: 'templates/login.html',
    controller: 'LoginController'
  })
  
  .when('/message/:email', {
    templateUrl: 'templates/message_form.html',
    controller: 'MessageSendController'
  })
  
  .when('/messages', {
    templateUrl: 'templates/messages.html',
    controller: 'MessagesController'
  })

  .when('/logout', {
    templateUrl: 'templates/logout.html',
    controller: 'LogoutController'
  });
  
  // configure html5 to get links working on jsfiddle
  $locationProvider.html5Mode(true);
});
