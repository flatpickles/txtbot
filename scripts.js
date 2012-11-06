var most_recent = 0;
var slide_in = false;

$(document).ready(function() {
	initialize(15);
	setInterval(check_for_new, 5000);
	
	$('#subheader').hover(function() {
		$('#number').html("859-898-2682");
	}, function() {
		$('#number').html("859-TXTBOT2");
	});
});


function check_for_new() {
	$.getJSON("http://mattnichols.net:6288/entries?callback=?", {
		'n': 10,
		'after': most_recent
	}, function(data) {
		$('#loading').remove();
		$.each(data, load_handler);
		update_stats();
	});
};

function initialize(n) {
	update_stats();
	
	// load first n texts
	$.getJSON("http://mattnichols.net:6288/entries?callback=?", {
		'n': n
	}, function(data) {
		$('#loading').remove();
		$.each(data, load_handler);
		
		// set to animate in the future
		slide_in = true;
	});
	
};

function update_stats() {
	// load number of texts
	$.getJSON("http://mattnichols.net:6288/count?callback=?", function(data) {
		$('#num_texts').html(data['count']);
	});
	// and number of numbers
};

function load_handler(key, value) {
	var e = jQuery('<div/>', {
		id: key,
		text: value['text']
	}).addClass('msg');
	e.css('border', '3px solid ' + value['color']);
	e.css('background', brighten_color(value['color'].substring(1), .77));
	insert_sorted(e, '.msg', '#list');
	most_recent = Math.max(most_recent, parseInt(key));
};

function insert_sorted(el, class_type, container) {
	var all = $(class_type);
	var curr = 0;
	
	while (curr < all.length && parseInt(el.attr('id')) < parseInt($(all[curr]).attr('id'))) {
		curr++;
	}
	
	if (slide_in) el.hide();
	
	if (all.length) {
		if (all[curr]) el.insertBefore(all[curr]);
		else el.insertAfter(all[all.length - 1]);
	} else {
		el.prependTo(container);
	}
	
	if (slide_in) el.slideDown();
	
	jQuery('<div/>', {
		class: '.breaker'
	}).insertAfter(el);	
};

function brighten_color(hex, l) {
	var rgb = "#";
	var c, i;  
	for (i = 0; i < 3; i++) {  
		c = parseInt(hex.substr(i*2,2), 16);  
		c = Math.round(c + (255 - c) * l).toString(16);  
		rgb += ("00"+c).substr(c.length);  
	}  
	return rgb;  
}