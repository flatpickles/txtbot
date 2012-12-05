// constants
var LOAD_NUMBER = 20;
var BEST_LOAD_NUMBER = 5;
var FADEIN_DELAY = 100;
var FADEOUT_DELAY = 200;
var CHECK_DELAY = 10000;

// globals
var most_recent = 0;
var oldest_best = Infinity;
var lowest_id = Infinity;
var slide_in = false;
var loading = true;

$(document).ready(function() {
	$("#content").css('display', 'block');
	$(".body").hide();

	// check for IE
	if ($.browser.msie) {
		$('#nav').hide();
		$('#loading').hide();
		$('#ie_msg').show();
		update_stats();
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

	$('#load_more_best').click(function() {
		if (loading) return;
		load_best();
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

	// load best
	load_best(true);
});

function load_best(is_first) {
	$.getJSON("http://mattnichols.net:6288/best?callback=?", {
		'n': BEST_LOAD_NUMBER,
		'before': is_first ? -1 : oldest_best
	}, function(data) {
		// call add_best_entry for each result returned
		$.each(data, function(k, v) {
			add_best_entry(v['first'], v['last'], k);
		});
	});
};

function add_best_entry(low, high, id) {
	// for future inserts...
	oldest_best = Math.min(parseInt(id), oldest_best);
	// make div
	var best_el = jQuery('<div/>', {
		id: 'best_' + id,
		class: 'best',
	});
	// insert sorted among other best entries
	insert_sorted(best_el, ".best", "#best", "best_", true)
	// load in best texts
	$.getJSON("http://mattnichols.net:6288/entries?callback=?", {
		'after': low - 1,
		'before': high + 1
	}, function(data) {
		var j, k;
		// add all elements in list
		var last;
		for (j = low; j <= high; j++) {
			if (!data[j]) continue;
			var e = jQuery('<div/>', {
				id: j.toString() + '_best',
				class: 'msg',
				text: data[j]['text']
			});
			e.css('border', '3px solid ' + data[j]['color']);
			e.css('background', brighten_color(data[j]['color'].substring(1), .77));
			e.appendTo(best_el);
			jQuery('<div/>', {
				class: 'breaker'
			}).insertAfter(e);
			// insert tag at top, do it here so we have the date
			if (j == low) {
				var d = new Date(data[j]['time'] * 1000);
				var div = get_divider((d.getMonth() + 1) + "/" + d.getDate() + "/" + d.getFullYear().toString().substr(2, 4));
				div.insertBefore(e);
			}
		}
	});
}

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
		// finish loading (animation, state)
		$('#recent').fadeIn(FADEIN_DELAY);
		loading = false;
	});

	setInterval(check_for_new, CHECK_DELAY);
};

function load_more() {
	slide_in = false;
	// load n texts before last displayed
	loading = true;
	$.getJSON("http://mattnichols.net:6288/entries?callback=?", {
		'n': LOAD_NUMBER,
		'before': lowest_id
	}, function(data) {
		$('#loading').remove();
		$.each(data, load_handler);
		// set to animate in the future, remove loading property
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
	// create an element for the new message
	var e = jQuery('<div/>', {
		id: key,
		class: 'msg',
		text: value['text']
	});
	// add dynamic CSS properties
	e.css('border', '3px solid ' + value['color']);
	e.css('background', brighten_color(value['color'].substring(1), .77));
	// insert and adjust globals
	insert_sorted(e, '.msg', '#recent', '', false);
	most_recent = Math.max(most_recent, parseInt(key));
	lowest_id = Math.min(lowest_id, parseInt(key));
};

function insert_sorted(el, class_type, container, id_prepend, no_slide) {
	var all = $(class_type);
	var curr = 0;

	// find the element to insert el before (by id, w/out prepend)
	while (curr < all.length && parseInt(el.attr('id').substr(id_prepend.length)) < parseInt($(all[curr]).attr('id').substr(id_prepend.length))) {
		curr++;
	}

	if (slide_in && !no_slide) el.hide();

	// add it (to beginning, if appropriate)
	if (all.length) {
		if (all[curr]) el.insertBefore(all[curr]);
		else $(all[all.length - 1]).next().after(el);
	} else {
		el.prependTo(container);
	}

	if (slide_in && !no_slide) el.slideDown();

	// add a breaking element
	jQuery('<div/>', {
		class: 'breaker'
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