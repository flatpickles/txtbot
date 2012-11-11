var LOAD_NUMBER = 15;

var most_recent = 0;
var lowest_id = 99999999;
var slide_in = false;
var loading = true;

$(document).ready(function() {
	// set things up
	initialize();
	
	// update number on hover over subheader
	$('#subheader').hover(function() {
		$('#number').html("859-898-2682");
	}, function() {
		$('#number').html("859-TXTBOT2");
	});
	
	$('#load_more').click(function() {
		if (loading) return false;
		load_more();
		return false;
	});
	
	// navigation
	$(".nav").click(function() {
		$(".nav").removeClass('selected');
		$(this).addClass('selected');
	});
	
});

function initialize() {
	update_stats();
	
	// load first n texts
	$.getJSON("http://mattnichols.net:6288/entries?callback=?", {
		'n': LOAD_NUMBER
	}, function(data) {
		$('#loading').remove();
		$.each(data, load_handler);
		
		// set to animate in the future
		slide_in = true;
		
		$('#load_more').fadeIn().css('display', 'inline-block');
		loading = false;
	});
	
	setInterval(check_for_new, 300000);
};

function load_more() {
	slide_in = false;
	// load first n texts
	loading = true;
	$.getJSON("http://mattnichols.net:6288/entries?callback=?", {
		'n': LOAD_NUMBER,
		'before': lowest_id
	}, function(data) {
		$('#loading').remove();
		$.each(data, load_handler);
		
		// set to animate in the future
		slide_in = true;
		
		loading = false;
	});
};


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

function update_stats() {
	// load number of texts
	$.getJSON("http://mattnichols.net:6288/text_count?callback=?", function(data) {
		$('#num_texts').html(data['count']);
	});
	// and number of numbers
	$.getJSON("http://mattnichols.net:6288/number_count?callback=?", function(data) {
		$('#num_numbers').html(data['count']);
	});
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
	lowest_id = Math.min(lowest_id, parseInt(key));
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
		else $(all[all.length - 1]).next().after(el);
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