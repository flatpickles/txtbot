// reference to Firebase root
var root = new Firebase('https://gamma.firebase.com/overheard');

// trigger update when an entry is added to Firebase tree
root.on('child_added', function (snapshot) {
	// remove loading element if present
	$('#loading').remove();
	
	// add message element
	var elID = snapshot.name();
	var message = snapshot.child('body').val();
	var time = Date(snapshot.child('time').val());
	jQuery('<div/>', {
		id: elID,
		text: message
	}).addClass('msg').hide().appendTo('#list').fadeIn();
});