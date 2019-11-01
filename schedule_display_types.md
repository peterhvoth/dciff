[time]
	<start_time> - <end_time>: 

[film_info]
	<title_with_link> (<ctry> / <len> / <year> / <category> / <premiere_status>>) by <director_list>

[location]
	(<location_name_map_link>, <location_address>)


film
	[time] [film_info] [location]. <comment>

film + short
	[time] [film_info]; [film_info] [location]. <comment>

film block
	[time] <block_name> [location]
	[film_info]

event
	[time] <event_type>: <title_with_link> - <comment> [location]
