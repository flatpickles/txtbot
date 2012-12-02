drop table if exists entries;
create table entries (
	id integer primary key autoincrement,
	text string not null,
	origin string not null,
	time long not null
);
create table best (
  id integer primary key autoincrement,
  first integer not null,
  last integer not null
);
create table blocked (
  id integer primary key autoincrement,
  num string not null
);
