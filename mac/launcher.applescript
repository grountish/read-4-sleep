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
		do shell script "cd " & quoted form of appDir & " && RFS_AUTOCLOSE=1 /usr/bin/nohup /usr/bin/arch -arm64 " & quoted form of pyBin & " app.py > /tmp/read-for-sleep.log 2>&1 &"

		-- Wait for Flask to answer (imports take a few seconds; model loads later)
		repeat 120 times
			delay 0.5
			set code to do shell script "/usr/bin/curl -s -o /dev/null -w '%{http_code}' " & serverURL & " || true"
			if code is "200" then exit repeat
		end repeat
	end if

	-- Only open a real, answering server — never a blank "can't connect" window.
	if code is "200" then
		do shell script "/usr/bin/open " & serverURL
	else
		display alert "Read for Sleep" message "The server did not start. See /tmp/read-for-sleep.log for details."
	end if
end run
