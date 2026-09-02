-- Read for Sleep launcher
-- Starts the Flask server (if not already running) and opens the browser.
-- Build and install the .app with mac/build.sh

on run
	set appDir to "/Users/mcmilton/Documents/code/read-for-sleep"
	set pyBin to appDir & "/venv/bin/python"
	set serverURL to "http://127.0.0.1:5050"
	set logFile to "/tmp/read-for-sleep.log"
	set probe to "/usr/bin/curl -s -m 2 -o /dev/null -w '%{http_code}' " & serverURL & " || true"

	-- Is the server already up?
	set code to do shell script probe

	if code is not "200" then
		-- Launch detached. `do shell script` only returns once every process
		-- holding its output pipe has closed it. A plain
		--   cd X && nohup ... > log 2>&1 &
		-- backgrounds the whole AND-list in a subshell whose own stdout/stderr
		-- still point at that pipe, so the applet hangs here for the server's
		-- entire lifetime and never opens the browser. Redirect the whole
		-- subshell instead, and `exec` so no extra sh lingers.
		do shell script "( cd " & quoted form of appDir & " && exec /usr/bin/env PATH=\"/opt/homebrew/bin:/usr/local/bin:$PATH\" RFS_AUTOCLOSE=1 /usr/bin/nohup /usr/bin/arch -arm64 " & quoted form of pyBin & " app.py ) > " & logFile & " 2>&1 < /dev/null &"

		-- Wait for Flask to answer. Imports take a few seconds warm but can
		-- take a minute or more on a cold start (torch), so allow two minutes.
		repeat 240 times
			delay 0.5
			set code to do shell script probe
			if code is "200" then exit repeat
		end repeat
	end if

	-- Only open a real, answering server, never a blank "can't connect" window.
	if code is "200" then
		do shell script "/usr/bin/open " & serverURL
	else
		display alert "Read for Sleep" message "The server did not start. See " & logFile & " for details."
	end if
end run
