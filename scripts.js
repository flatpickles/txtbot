// constants
var LOAD_NUMBER = 20;
var FADEIN_DELAY = 100;
var FADEOUT_DELAY = 200;
var CHECK_DELAY = 10000;

// globals
var most_recent = 0;
var lowest_id = 99999999;
var slide_in = false;
var loading = true;

// best
var BEST = [
	[110, 118],
	[32, 37]
];

$(document).ready(function() {
	$(".body").hide();
	
	// check for IE
	if ($.browser.msie) {
		$('#nav').hide();
		return;		
	}

	// set things up
	initialize();
	
	// update number on hover over subheader
	$('#subheader').hover(function() {
		$('#number').html("859-898-2682");
	}, function() {
		$('#number').html("859-TXTBOT2");
	});
	
	$('#load_more').click(function() {
		if (loading) return;
		load_more();
	});
	
	// navigation
	$(".nav").click(function() {
		if ($(this).hasClass('selected')) return;
		// nav manipulation
		$(".nav").removeClass('selected');
		$(this).addClass('selected');
		// body manipulation
		var n = $(this).attr('id');
		n = n.substr(0, n.length - 4);
		var c = 0;
		$('.body').fadeOut(FADEOUT_DELAY, function() {
			if (++c > 2) { // once everything's faded out...
				$('#' + n).fadeIn(FADEIN_DELAY);
			}
		});
	});
	
	var i, j, k;
	for (i = 0; i < BEST.length; i++) {
		var low = BEST[i][0];
		var up = BEST[i][1];
		// load first n texts
		$.getJSON("http://mattnichols.net:6288/entries?callback=?", {
			'after': low - 1,
			'before': up + 1
		}, function(data) {
			// find min + max of keys
			var l, u;
			var keys = Object.keys(data);
			for (k = 0; k < keys.length; k++) {
				if (!l || parseInt(keys[k]) < l) l = keys[k];
				if (!u || parseInt(keys[k]) > u) u = keys[k];
			}
			// add all elements in list
			var last;
			for (j = l; j <= u; j++) {
				if (!data[j]) continue;
				var e = jQuery('<div/>', {
					id: j.toString() + '_best',
					text: data[j]['text']
				}).addClass('msg');
				e.css('border', '3px solid ' + data[j]['color']);
				e.css('background', brighten_color(data[j]['color'].substring(1), .77));
				e.appendTo('#best');
				jQuery('<div/>', {
					class: '.breaker'
				}).insertAfter(e);
				// insert tag at top
				if (j == l) {
					var d = new Date(data[j]['time'] * 1000);
					var div = get_divider(d.getMonth() + "/" + d.getDate() + "/" + d.getFullYear().toString().substr(2, 4));
					div.insertBefore(e);
					if (!div.is(':first-child')) div.css('margin-top', '30px');
				}
			}
		});
	}
	
});

function get_divider(contents) {
	var c = jQuery('<div/>').addClass('divider');
	jQuery('<span/>').addClass('divider_label').html(contents).appendTo(c);
	return c;
};

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
		
		$('#recent').fadeIn(FADEIN_DELAY);
		loading = false;
	});
	
	setInterval(check_for_new, CHECK_DELAY);
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
	insert_sorted(e, '.msg', '#recent');
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
};