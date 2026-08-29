--- run_bot.py
+++ run_bot.py
@@ -9,6 +9,14 @@
 OFFSET = 0
 
 def tg(method, **kw):
+    """
+    Send a request to the Telegram Bot API.
+    
+    Args:
+        method (str): The API method to call.
+        **kw: Additional keyword arguments for the API request.
+    
+    Returns: JSON response from the API.
+    """
     with httpx.Client(timeout=15) as c:
         return c.post(f"https://api.telegram.org/bot{TOKEN}/{method}", json=kw).json()
 
@@ -13,6 +21,14 @@
 def send(cid, text):
+    """
+    Send a message to a specific chat.
+    
+    Args:
+        cid (int): Chat ID to send the message to.
+        text (str): The message text to send.
+    
+    Returns: JSON response from the sendMessage API.
+    """
     return tg("sendMessage", chat_id=cid, text=text, parse_mode="HTML")
 
 def gh_post(url, body):
@@ -16,6 +32,14 @@
 def gh_post(url, body):
+    """
+    Send a POST request to a GitHub API endpoint.
+    
+    Args:
+        url (str): The GitHub API URL.
+        body (dict): The JSON body to send with the request.
+    
+    Returns: HTTP status code from the response.
+    """
     with httpx.Client(timeout=10) as c:
         return c.post(url, json=body, headers={"Authorization": f"token {GH_PAT}", "Accept": "application/vnd.github.v3+json"}).status_code
 
@@ -20,6 +44,14 @@
 def gh_get(url):
+    """
+    Send a GET request to a GitHub API endpoint.
+    
+    Args:
+        url (str): The GitHub API URL.
+    
+    Returns: JSON response from the API.
+    """
     with httpx.Client(timeout=10) as c:
         return c.get(url, headers={"Authorization": f"token {GH_PAT}", "Accept": "application/vnd.github.v3+json"}).json()
 
@@ -24,6 +56,14 @@
 def handle(cmd, args, cid):
+    """
+    Handle incoming commands and execute corresponding actions.
+    
+    Args:
+        cmd (str): The command to handle.
+        args (str): Additional arguments for the command.
+        cid (int): Chat ID where the command was received.
+    """
     cmd = cmd.lower()
     if cmd in ("/start", "/help"):
         return send(cid, "FORGEMIND online. I forge myself.\n\n/status — metrics\n/run — improve cycle\n/build — APK build\n/apk — latest APK\n/report <text> — bug or idea")
@@ -44,6 +84,14 @@
     return send(cid, "Unknown. /help")
 
 def main():
+    """
+    Main loop for the Telegram bot, handling updates and commands.
+    """
     global OFFSET
     print("FORGEMIND bot started")
     tg("deleteWebhook")
