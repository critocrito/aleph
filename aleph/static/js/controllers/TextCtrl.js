
aleph.controller('TextCtrl', ['$scope', '$location', '$http', 'metadata', 'Authz', 'Document', 'Title', 'data', 'pages',
    function($scope, $location, $http, metadata, Authz, Document, Title, data, pages) {

  $scope.doc = data.doc;
  $scope.pageText = data.page.text;
  $scope.pages = pages;

  $scope.loading = true;
  $scope.viewText = $location.search().view == 'text';
  $scope.pageNum = $location.search().page || 1;
  $scope.textQuery = $location.search().dq;
  $scope.reportLoading(true);
  $scope.pdfUrl = '/api/1/documents/' + data.doc.id + '/pdf';

  Title.set(data.doc.title + " (Page " + $scope.pageNum + ")");

  $scope.onError = function(error) {
    $scope.reportError("Could not load document.");
  }

  $scope.onLoad = function() {
    $scope.loading = false;
    $scope.reportLoading(false);
  }

  $scope.toggleViewText = function() {
    $scope.viewText = !$scope.viewText;
    var q = $location.search();
    q.view = $scope.viewText ? 'text' : null;
    $location.search(q);
  }

  $scope.$watch('pageNum', function(pg) {
    var q = $location.search();
    q.page = pg;
    $location.search(q);
    Document.getPage(data.doc.id, pg).then(function(page) {
      $scope.pageText = page.text;
    });
  });

  $scope.setPage = function(pageNum) {
    $scope.pageNum = pageNum;
  };

  $scope.backToSearch = function() {
    var query = alephUrlUnBlob($location.search().ctx);
    $location.path('/search');
    $location.search(query);
  };

  $scope.updateTextQuery = function() {
    var q = $location.search();
    q.dq = $scope.textQuery;
    $location.search(q); 
  };

  $scope.$on('$locationChangeStart', function() {
    var query = $location.search();
    $scope.pageNum = query.page || 1;
    $scope.textQuery = query.dq;
    Title.set(data.doc.title + ", Page " + $scope.pageNum);
    Document.queryPages(data.doc.id, query).then(function(pages) {
      $scope.pages = pages;  
    });
  });

}]);
