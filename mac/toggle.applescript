-- Read for Sleep — toggle launcher
-- If server is down: start it, wait, open browser.
-- If server is up:   stop it.

on run
	set appDir to "/Users/mcmilton/Documents/code/read-for-sleep"
	set pyBin to appDir & "/venv/bin/python"
	set serverURL to "http://127.0.0.1:5050"

	set code to do shell script "/usr/bin/curl -s -o /dev/null -w '%{http_code}' " & serverURL & " || true"

	if code is "200" then
		-- running -> stop
		do shell script "/usr/bin/pkill -f 'read-for-sleep/app.py' || true"
		display notification "Server stopped." with title "Read for Sleep"
	else
		-- down -> start
		do shell script "cd " & quoted form of appDir & " && /usr/bin/nohup " & quoted form of pyBin & " app.py > /tmp/read-for-sleep.log 2>&1 &"
		repeat 60 times
			delay 0.5
			set code to do shell script "/usr/bin/curl -s -o /dev/null -w '%{http_code}' " & serverURL & " || true"
			if code is "200" then exit repeat
		end repeat
		do shell script "/usr/bin/open " & serverURL
	end if
end run
