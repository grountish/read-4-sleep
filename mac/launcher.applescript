-- Read for Sleep launcher
-- Starts the Flask server (if not already running) and opens the browser.

on run
	set appDir to "/Users/mcmilton/Documents/code/read-for-sleep"
	set pyBin to appDir & "/venv/bin/python"
	set serverURL to "http://127.0.0.1:5050"

	-- Is the server already up?
	set code to do shell script "/usr/bin/curl -s -o /dev/null -w '%{http_code}' " & serverURL & " || true"

	if code is not "200" then
		-- Launch detached so it survives this script quitting
		do shell script "cd " & quoted form of appDir & " && /usr/bin/nohup " & quoted form of pyBin & " app.py > /tmp/read-for-sleep.log 2>&1 &"

		-- Wait for Flask to answer (up to ~30s; model loads lazily later)
		repeat 60 times
			delay 0.5
			set code to do shell script "/usr/bin/curl -s -o /dev/null -w '%{http_code}' " & serverURL & " || true"
			if code is "200" then exit repeat
		end repeat
	end if

	do shell script "/usr/bin/open " & serverURL
end run
