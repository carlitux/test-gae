angular.module('TestExample', ['ngRoute'])
  .config(function($interpolateProvider) {
    $interpolateProvider.startSymbol('{$');
    $interpolateProvider.endSymbol('$}');
  })

 .controller('MainController', function($scope, $route, $routeParams, $location) {
    console.log(arguments);
     $scope.$route = $route;
     $scope.$location = $location;
     $scope.$routeParams = $routeParams;
 })

 .controller('RegistrationController', function($scope, $routeParams) {
     $scope.name = "BookController";
     $scope.params = $routeParams;
 })

 .controller('LoginController', function($scope, $routeParams) {
     $scope.name = "ControllerController";
     $scope.params = $routeParams;
 })

.config(function($routeProvider, $locationProvider) {
  $routeProvider
   .when('/', {
    templateUrl: 'templates/signup.html',
    controller: 'MainController',
    resolve: {
      console.log('test')
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
     // I will cause a 1 second delay
     delay: function($q, $timeout) {
       var delay = $q.defer();
       $timeout(delay.resolve, 1000);
       return delay.promise;
     }
   }
 })
  .when('/Book/:bookId/ch/:chapterId', {
    templateUrl: 'chapter.html',
    controller: 'ChapterController'
  });

  // configure html5 to get links working on jsfiddle
  $locationProvider.html5Mode(true);
});
