var most_recent = 0;

$(document).ready(function() {
	initialize(15);
	setInterval(check_for_new, 5000);
});

function check_for_new() {
	$.getJSON("http://mattnichols.net:6288/entries?callback=?", {
		'n': 10,
		'after': most_recent
	}, function(data) {
		$('#loading').remove();
		$.each(data, load_handler);
	});
}

function initialize(n) {
	$.getJSON("http://mattnichols.net:6288/entries?callback=?", {
		'n': n
	}, function(data) {
		$('#loading').remove();
		$.each(data, load_handler);
	});
};

function load_handler(key, value) {
	var e = jQuery('<div/>', {
		id: key,
		text: value['text']
	}).addClass('msg');
	insert_sorted(e, '.msg', '#list');
	most_recent = Math.max(most_recent, parseInt(value['time']));
};

function insert_sorted(el, class_type, container) {
	var all = $(class_type);
	var curr = 0;
	
	while (curr < all.length && parseInt(el.attr('id')) < parseInt($(all[curr]).attr('id'))) {
		curr++;
	}
	
	if (all.length) {
		if (all[curr]) el.insertBefore(all[curr]);
		else el.insertAfter(all[all.length - 1]);
	} else {
		el.prependTo(container);
	}
};