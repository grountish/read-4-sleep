-- Stop Read for Sleep
-- Kills the running Flask server.

on run
	do shell script "/usr/bin/pkill -f 'Python app.py' || true"
	display notification "Server stopped." with title "Read for Sleep"
end run
