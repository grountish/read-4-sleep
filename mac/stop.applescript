-- Stop Read for Sleep
-- Kills the running Flask server.

on run
	do shell script "/usr/bin/pkill -f 'read-for-sleep/app.py' || /usr/bin/pkill -f 'venv/bin/python app.py' || true"
	display notification "Server stopped." with title "Read for Sleep"
end run
