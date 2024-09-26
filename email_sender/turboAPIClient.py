import urllib.parse
import urllib.request


class TurboAPIClient:

    def sendMail(self, username, password, serverUrl, mail):
        dataToSend = {
            'authuser': username,
            'authpass': password,
            'from': mail.getFrom(),
            'to': mail.getTo(),
            'subject': mail.getSubject(),
            'content': mail.getContent(),
            'html_content': mail.getHtmlContent(),
            'custom_headers': mail.getCustomHeaders(),
            'mime_raw': mail.getMimeRaw()
        }
        try:
            # Encode the data to be sent
            encodedDataToSend = urllib.parse.urlencode(dataToSend).encode("utf-8")
            # Create the request object
            req = urllib.request.Request(serverUrl, data=encodedDataToSend)
            # Open the URL and read the response
            with urllib.request.urlopen(req) as response:
                return response.read().decode("utf-8")
        except Exception as e:
            raise e
